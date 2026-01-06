"""
Status and download endpoints for audit reports.
"""
from typing import Optional
from datetime import datetime
from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import FileResponse, Response

from api.models.schemas import ReportStatusResponse
from api.models.report import Report, ReportStatus
from api.database import SessionLocal
from .shared_state import get_report_cache, get_running_tasks


async def get_report_status(report_id: int):
    """Get the status of an audit report generation."""
    _report_cache = get_report_cache()
    
    db = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Get cached content if available
        cached = _report_cache.get(report_id, {})
        
        if report.status == ReportStatus.COMPLETED:
            # Use cached report_data if available (has proper download URLs)
            # Otherwise construct URLs from filenames
            report_data = cached.get("report_data")
            if not report_data:
                # Fallback: construct URLs from stored filenames
                report_data = {
                    "filename": report.filename,
                    "html_url": f"/api/audit/download-file?path={report.file_path_html}" if report.file_path_html else None,
                    "pdf_url": f"/api/audit/download-file?path={report.file_path_pdf}" if report.file_path_pdf else None,
                    "word_url": f"/api/audit/download-file?path={report.file_path_word}" if report.file_path_word else None
                }
            
            # Get HTML content - ALWAYS prefer original file over database
            # Database may contain edited/processed HTML, but we need the original for viewer
            # Priority: 1. Cache (if original), 2. File on disk (original), 3. Database (fallback)
            html_content = None
            
            # First, try to load from file (original HTML with styles and semantic IDs)
            if report.file_path_html:
                try:
                    reports_dir = Path(__file__).parent.parent.parent.parent / "data" / "reports"
                    html_filename = Path(report.file_path_html).name
                    html_file_path = reports_dir / html_filename
                    if html_file_path.exists():
                        with open(html_file_path, "r", encoding="utf-8") as f:
                            html_content = f.read()
                        
                        # Verify it's the original HTML (has styles and semantic IDs)
                        is_original = '<style>' in html_content and 'data-section=' in html_content
                        if is_original:
                            # Store in cache for future requests
                            if report_id not in _report_cache:
                                _report_cache[report_id] = {}
                            _report_cache[report_id]["html_content"] = html_content
                            # Update database with original HTML if it's missing or was overwritten
                            if not report.html_content or not ('<style>' in report.html_content):
                                report.html_content = html_content
                                db.commit()
                            print(f"✓ Loaded ORIGINAL HTML from file for report {report_id} ({len(html_content)} chars, has styles: {is_original})")
                        else:
                            print(f"⚠ File HTML appears to be processed (no styles), will try database...")
                            html_content = None  # Try database instead
                    else:
                        print(f"⚠ HTML file not found: {html_file_path}")
                except Exception as e:
                    print(f"⚠ Could not read HTML content from file: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Fallback to cache if file didn't work
            if not html_content:
                html_content = cached.get("html_content")
                if html_content and '<style>' in html_content:
                    print(f"✓ Using cached original HTML ({len(html_content)} chars)")
                elif html_content:
                    print(f"⚠ Cached HTML appears processed, trying database...")
                    html_content = None
            
            # Fallback to database (may contain edited HTML, but better than nothing)
            if not html_content:
                try:
                    db.refresh(report)  # Refresh to get latest data from DB
                    if report.html_content:
                        html_content = report.html_content
                        # Check if it's original or processed
                        is_original = '<style>' in html_content and 'data-section=' in html_content
                        if is_original:
                            # Store in cache
                            if report_id not in _report_cache:
                                _report_cache[report_id] = {}
                            _report_cache[report_id]["html_content"] = html_content
                            print(f"✓ Loaded HTML from database (original: {is_original}, {len(html_content)} chars)")
                        else:
                            print(f"⚠ Database HTML appears processed - missing styles/semantic IDs")
                except Exception as e:
                    print(f"⚠ Error reading html_content from database: {e}")
                    import traceback
                    traceback.print_exc()
            
            if not html_content:
                print(f"⚠ No HTML content available for report {report_id} (checked cache, database, and file)")
                # Last resort: try to load from download endpoint if file exists
                if report.file_path_html:
                    try:
                        from .download_endpoints import download_file
                        reports_dir = Path(__file__).parent.parent.parent.parent / "data" / "reports"
                        html_filename = Path(report.file_path_html).name
                        html_file_path = reports_dir / html_filename
                        if html_file_path.exists():
                            # Read directly
                            with open(html_file_path, "r", encoding="utf-8") as f:
                                html_content = f.read()
                            # Save to database for next time
                            report.html_content = html_content
                            db.commit()
                            print(f"✓ Loaded HTML from file and saved to database for report {report_id}")
                    except Exception as e:
                        print(f"⚠ Final fallback failed: {e}")
            
            return ReportStatusResponse(
                report_id=report.id,
                status="completed",
                progress=100.0,
                report_url=report_data.get("html_url") or (f"/api/audit/download-file?path={report.file_path_html}" if report.file_path_html else None),
                html_content=html_content,
                report_data=report_data
            )
        elif report.status == ReportStatus.FAILED:
            return ReportStatusResponse(
                report_id=report.id,
                status="failed",
                progress=0.0,
                error=cached.get("error", "Unknown error occurred")
            )
        else:
            # Still processing - get progress from cache
            cached_progress = cached.get("progress", 0.0)
            cached_step = cached.get("step", "Initializing...")
            start_time = cached.get("start_time")
            
            # Calculate estimated time remaining based on progress
            estimated_remaining = None
            if start_time and cached_progress > 1:
                try:
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    elapsed = (datetime.now(start_dt.tzinfo) - start_dt).total_seconds()
                    
                    # Stage-based time estimates
                    if cached_progress < 20:
                        extraction_remaining = ((20 - cached_progress) / 20) * 4
                        remaining_phases = 15 + 3
                        estimated_remaining = int(extraction_remaining + remaining_phases)
                    elif cached_progress < 25:
                        estimated_remaining = int(15 + 3)
                    elif cached_progress < 30:
                        estimated_remaining = int(15 + 3)
                    elif cached_progress < 60:
                        ai_progress = (cached_progress - 30) / 30
                        ai_remaining = (1 - ai_progress) * 15
                        remaining_phases = 3
                        estimated_remaining = int(ai_remaining + remaining_phases)
                    elif cached_progress < 80:
                        formatting_progress = (cached_progress - 60) / 20
                        formatting_remaining = (1 - formatting_progress) * 1.5
                        report_gen = 3
                        estimated_remaining = int(formatting_remaining + report_gen)
                    else:
                        if elapsed > 10:
                            rate = cached_progress / elapsed
                            remaining_seconds = (100 - cached_progress) / rate if rate > 0 else 0
                            estimated_remaining = max(1, int(remaining_seconds / 60))
                        else:
                            estimated_remaining = 3
                    
                    estimated_remaining = max(1, min(30, estimated_remaining))
                except:
                    pass
            
            return ReportStatusResponse(
                report_id=report.id,
                status="processing",
                progress=cached_progress,
                report_data={
                    "step": cached_step, 
                    "progress": cached_progress,
                    "estimated_remaining_minutes": estimated_remaining,
                    "start_time": start_time
                }
            )
    finally:
        db.close()


async def cancel_audit(report_id: int):
    """
    Cancel a running audit generation.
    
    This will mark the report as failed and stop the background task.
    """
    _report_cache = get_report_cache()
    _running_tasks = get_running_tasks()
    
    try:
        # Mark report as failed in cache
        _report_cache[report_id] = {
            "error": "Audit generation cancelled by user",
            "progress": 0.0,
            "step": "Cancelled"
        }
        
        # Remove from running tasks
        if report_id in _running_tasks:
            task = _running_tasks.pop(report_id)
        
        # Update database
        db = SessionLocal()
        try:
            report = db.query(Report).filter(Report.id == report_id).first()
            if report:
                report.status = ReportStatus.FAILED
                db.commit()
                print(f"✓ Report {report_id} marked as cancelled")
        finally:
            db.close()
        
        return {"success": True, "message": f"Report {report_id} cancelled"}
    except Exception as e:
        print(f"❌ Error cancelling report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel report: {str(e)}")


async def download_file(path: str, report_id: Optional[int] = None):
    """
    Download a report file by filename or report_id.
    Queries the database to verify the report exists and get the correct file path.
    Serves files from the reports directory.
    """
    _report_cache = get_report_cache()
    
    db = SessionLocal()
    try:
        # Query database to get the report record
        report = None
        if report_id:
            report = db.query(Report).filter(Report.id == report_id).first()
        else:
            filename = Path(path).name
            report = db.query(Report).filter(Report.filename == filename).first()
        
        if not report:
            raise HTTPException(
                status_code=404,
                detail=f"Report not found in database: {path}"
            )
        
        # Determine which file type to serve (html, pdf, or word)
        file_type = None
        stored_path = None
        
        path_lower = path.lower()
        if path_lower.endswith('.pdf'):
            file_type = 'pdf'
            stored_path = report.file_path_pdf
        elif path_lower.endswith('.docx') or path_lower.endswith('.doc'):
            file_type = 'word'
            stored_path = report.file_path_word
        else:
            file_type = 'html'
            stored_path = report.file_path_html
        
        # If no stored path, try to construct from filename
        if not stored_path:
            stored_path = report.filename
            if file_type == 'pdf':
                stored_path = stored_path.replace('.html', '.pdf')
            elif file_type == 'word':
                stored_path = stored_path.replace('.html', '.docx')
        
        # Extract just the filename (in case full path was stored)
        filename = Path(stored_path).name if stored_path else Path(path).name
        
        # Security: Only allow files from reports directory
        reports_dir = Path(__file__).parent.parent.parent.parent / "data" / "reports"
        file_path = reports_dir / filename
        
        # Prevent directory traversal
        try:
            resolved_file = file_path.resolve()
            resolved_reports = reports_dir.resolve()
            resolved_file.relative_to(resolved_reports)
        except (ValueError, OSError):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file path: {path}"
            )
        
        # Check if file exists on disk
        if file_path.exists():
            ext = file_path.suffix.lower()
            media_types = {
                '.html': 'text/html',
                '.pdf': 'application/pdf',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.doc': 'application/msword'
            }
            
            return FileResponse(
                path=str(file_path),
                filename=file_path.name,
                media_type=media_types.get(ext, 'application/octet-stream')
            )
        else:
            # File doesn't exist on disk - check if we have HTML content in cache
            if file_type == 'html':
                cached = _report_cache.get(report.id, {})
                html_content = cached.get("html_content")
                
                if html_content:
                    return Response(
                        content=html_content,
                        media_type='text/html',
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
                    )
            
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {filename}. The file may have been deleted or the server was restarted. Report ID: {report.id}"
            )
    
    finally:
        db.close()

