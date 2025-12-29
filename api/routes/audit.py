"""
Audit API routes.
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional
from sqlalchemy.orm import Session
from httpx import HTTPStatusError
from api.models.schemas import AuditRequest, AuditResponse, ReportStatusResponse
from api.models.report import Report, ReportStatus
from api.services.klaviyo import KlaviyoService
from api.services.analysis import AgenticAnalysisFramework
from api.services.report import EnhancedReportService
from api.services.benchmark import BenchmarkService
from api.database import SessionLocal
# Auth imports removed temporarily for testing
# from api.services.auth import get_current_user, require_user_or_admin  
# from api.database import get_db
# from api.models.user import User
import hashlib
import os
import json

router = APIRouter()

# In-memory store for report HTML content (for async jobs)
# In production, use Redis or database
_report_cache = {}


async def _process_audit_background(
    report_id: int,
    request_data: dict,
    llm_config: dict
):
    """Background task to process audit generation."""
    db = SessionLocal()
    try:
        # Get report
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            print(f"❌ Report {report_id} not found")
            return
        
        try:
            print(f"🚀 Starting background audit generation for report {report_id}...")
            
            # Initialize progress tracking with start time (preserve if already exists)
            from datetime import datetime
            if report_id not in _report_cache:
                start_time = datetime.now()
                _report_cache[report_id] = {
                    "progress": 0.0, 
                    "step": "Initializing...",
                    "start_time": start_time.isoformat()
                }
            else:
                # Preserve existing start_time if cache already initialized
                existing_cache = _report_cache[report_id]
                if "start_time" not in existing_cache:
                    existing_cache["start_time"] = datetime.now().isoformat()
            
            # Initialize services
            klaviyo_service = KlaviyoService(api_key=request_data["api_key"])
            benchmark_service = BenchmarkService()
            
            # Get LLM API key
            anthropic_api_key = llm_config.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY")
            if not anthropic_api_key:
                raise Exception("Anthropic API key required")
            
            analysis_framework = AgenticAnalysisFramework(anthropic_api_key=anthropic_api_key)
            report_service = EnhancedReportService()
            
            # Step 1: Extract data from Klaviyo (0-20%)
            print("📊 Extracting data from Klaviyo...")
            # Preserve start_time from initialization
            existing_cache = _report_cache.get(report_id, {})
            existing_start_time = existing_cache.get("start_time", datetime.now().isoformat())
            _report_cache[report_id].update({
                "progress": 5.0, 
                "step": "Extracting data from Klaviyo...",
                "start_time": existing_start_time  # Preserve original start time
            })
            date_range_dict = request_data.get("date_range")
            
            # Update progress during extraction (continuous progress simulation)
            import asyncio
            extraction_done = asyncio.Event()
            extraction_start = datetime.now()
            
            async def simulate_extraction_progress():
                steps = [
                    (8.0, "Fetching revenue data..."),
                    (11.0, "Fetching campaign data..."),
                    (14.0, "Fetching flow data..."),
                    (17.0, "Fetching list growth data..."),
                ]
                step_index = 0
                last_update = datetime.now()
                
                while not extraction_done.is_set():
                    elapsed = (datetime.now() - extraction_start).total_seconds()
                    
                    if step_index < len(steps):
                        progress, step = steps[step_index]
                        _report_cache[report_id].update({"progress": progress, "step": step})
                        step_index += 1
                        # Wait before next step or until extraction completes
                        try:
                            await asyncio.wait_for(extraction_done.wait(), timeout=8.0)
                            break
                        except asyncio.TimeoutError:
                            continue  # Continue to next step
                    else:
                        # All steps done, but extraction still running - gradually increase progress
                        # Calculate progress based on elapsed time (assume extraction takes 2-5 minutes)
                        # Progress from 17% to 19% over time
                        time_based_progress = min(19.0, 17.0 + (elapsed / 120.0) * 2.0)  # 2 minutes to go from 17% to 19%
                        if (datetime.now() - last_update).total_seconds() >= 3.0:  # Update every 3 seconds
                            _report_cache[report_id].update({
                                "progress": time_based_progress, 
                                "step": "Finalizing data extraction..."
                            })
                            last_update = datetime.now()
                        # Check every 2 seconds
                        try:
                            await asyncio.wait_for(extraction_done.wait(), timeout=2.0)
                            break
                        except asyncio.TimeoutError:
                            continue
            
            # Start progress simulation as background task
            progress_task = asyncio.create_task(simulate_extraction_progress())
            
            try:
                # Run extraction
                klaviyo_data = await klaviyo_service.extract_all_data(date_range=date_range_dict)
            finally:
                # Signal extraction is done and cancel progress task
                extraction_done.set()
                progress_task.cancel()
                try:
                    await progress_task
                except asyncio.CancelledError:
                    pass
            
            _report_cache[report_id].update({"progress": 20.0, "step": "Data extraction complete"})
            
            # Step 2: Load benchmarks (20-25%)
            print("📊 Loading benchmarks...")
            _report_cache[report_id].update({"progress": 22.0, "step": "Loading benchmarks..."})
            benchmarks = benchmark_service.get_all_benchmarks()
            _report_cache[report_id].update({"progress": 25.0, "step": "Benchmarks loaded"})
            
            # Step 3: Run comprehensive agentic analysis (25-60%)
            print("🤖 Running comprehensive analysis...")
            _report_cache[report_id].update({"progress": 30.0, "step": "Running AI analysis..."})
            
            # Simulate progress during AI analysis (continuous until done)
            analysis_done = asyncio.Event()
            analysis_start = datetime.now()
            
            async def simulate_ai_progress():
                steps = [
                    (35.0, "Analyzing revenue data..."),
                    (40.0, "Analyzing campaign performance..."),
                    (45.0, "Analyzing flow performance..."),
                    (50.0, "Generating insights..."),
                    (55.0, "Finalizing analysis..."),
                ]
                step_index = 0
                last_update = datetime.now()
                
                while not analysis_done.is_set():
                    elapsed = (datetime.now() - analysis_start).total_seconds()
                    
                    if step_index < len(steps):
                        progress, step = steps[step_index]
                        _report_cache[report_id].update({"progress": progress, "step": step})
                        step_index += 1
                        # Wait before next step or until analysis completes
                        try:
                            await asyncio.wait_for(analysis_done.wait(), timeout=12.0)
                            break
                        except asyncio.TimeoutError:
                            continue  # Continue to next step
                    else:
                        # All steps done, but analysis still running - gradually increase progress
                        # Calculate progress based on elapsed time (assume analysis takes 3-8 minutes)
                        # Progress from 55% to 59% over time
                        time_based_progress = min(59.0, 55.0 + (elapsed / 180.0) * 4.0)  # 3 minutes to go from 55% to 59%
                        if (datetime.now() - last_update).total_seconds() >= 3.0:  # Update every 3 seconds
                            _report_cache[report_id].update({
                                "progress": time_based_progress, 
                                "step": "Finalizing AI analysis..."
                            })
                            last_update = datetime.now()
                        # Check every 3 seconds
                        try:
                            await asyncio.wait_for(analysis_done.wait(), timeout=3.0)
                            break
                        except asyncio.TimeoutError:
                            continue
            
            # Start progress simulation as background task
            progress_task = asyncio.create_task(simulate_ai_progress())
            
            try:
                # Run analysis
                analysis_results = await analysis_framework.run_comprehensive_analysis(
                    klaviyo_data=klaviyo_data,
                    benchmarks=benchmarks,
                    client_name=request_data["client_name"]
                )
            finally:
                # Signal analysis is done and cancel progress task
                analysis_done.set()
                progress_task.cancel()
                try:
                    await progress_task
                except asyncio.CancelledError:
                    pass
            
            _report_cache[report_id].update({"progress": 60.0, "step": "AI analysis complete"})
            
            # Step 4: Convert analysis results to audit data format (60-80%)
            print("🔄 Converting analysis results to audit data format...")
            _report_cache[report_id].update({"progress": 65.0, "step": "Formatting audit data..."})
            audit_data = await klaviyo_service.format_audit_data(
                date_range=date_range_dict,
                verbose=False
            )
            _report_cache[report_id].update({"progress": 80.0, "step": "Data formatting complete"})
            
            # Step 5: Generate audit report (80-100%)
            print("📝 Generating audit report...")
            _report_cache[report_id].update({"progress": 85.0, "step": "Generating report..."})
            
            # Simulate progress during report generation
            report_done = asyncio.Event()
            
            async def simulate_report_progress():
                steps = [
                    (88.0, "Rendering templates..."),
                    (92.0, "Generating PDF..."),
                    (96.0, "Finalizing report..."),
                ]
                step_index = 0
                while not report_done.is_set() and step_index < len(steps):
                    progress, step = steps[step_index]
                    _report_cache[report_id].update({"progress": progress, "step": step})
                    step_index += 1
                    try:
                        await asyncio.wait_for(report_done.wait(), timeout=20.0)
                        break
                    except asyncio.TimeoutError:
                        continue
            
            progress_task = asyncio.create_task(simulate_report_progress())
            
            try:
                generated_report = await report_service.generate_audit(
                    audit_data=audit_data,
                    client_name=request_data["client_name"],
                    auditor_name=request_data.get("auditor_name"),
                    client_code=request_data.get("client_code"),
                    industry=request_data.get("industry"),
                    llm_config=llm_config
                )
            finally:
                report_done.set()
                progress_task.cancel()
                try:
                    await progress_task
                except asyncio.CancelledError:
                    pass
            
            # Update report with results
            report.filename = generated_report.get("filename", report.filename)
            report.file_path_html = generated_report.get("html_url")
            report.file_path_pdf = generated_report.get("pdf_url")
            report.file_path_word = generated_report.get("word_url")
            report.status = ReportStatus.COMPLETED
            
            # Store HTML content in cache and set final progress
            _report_cache[report_id] = {
                "progress": 100.0,
                "step": "Report generation complete",
                "html_content": generated_report.get("html_content"),
                "report_data": {
                    "filename": generated_report.get("filename"),
                    "html_url": generated_report.get("html_url"),
                    "pdf_url": generated_report.get("pdf_url"),
                    "word_url": generated_report.get("word_url"),
                    "pages": generated_report.get("pages"),
                    "sections": generated_report.get("sections", [])
                }
            }
            
            db.commit()
            print(f"✅ Audit report {report_id} completed successfully")
            
        except Exception as e:
            import traceback
            error_msg = str(e)
            print(f"❌ ERROR in background audit generation for report {report_id}: {error_msg}")
            print(f"Traceback: {traceback.format_exc()}")
            
            # Update report status to failed
            report.status = ReportStatus.FAILED
            _report_cache[report_id] = {"error": error_msg}
            db.commit()
            
    finally:
        db.close()


@router.post("/generate", response_model=AuditResponse)
async def generate_audit(request: AuditRequest, background_tasks: BackgroundTasks):
    """
    Generate a complete comprehensive audit report for a Klaviyo account (async).
    
    Returns immediately with a report_id. Use /status/{report_id} to poll for completion.
    Uses the enhanced agentic analysis framework and comprehensive report template.
    """
    try:
        print(f"🚀 Starting async audit generation for {request.client_name}...")
        
        # Get LLM API key from request (prioritize request over env vars)
        anthropic_api_key = request.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            raise HTTPException(
                status_code=400,
                detail="Anthropic API key required. Please provide 'anthropic_api_key' in the request or set ANTHROPIC_API_KEY environment variable."
            )
        
        # Convert DateRange model to dict if provided
        date_range_dict = None
        if request.date_range:
            date_range_dict = {
                "start": request.date_range.start,
                "end": request.date_range.end
            }
        elif request.days:
            # Fallback: convert days to date_range if date_range not provided
            from datetime import datetime, timedelta, timezone
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=request.days)
            date_range_dict = {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        
        # Build LLM config from request
        llm_config = {
            "provider": request.llm_provider or "claude",
            "anthropic_api_key": request.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY"),
            "claude_model": request.claude_model or os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5"),
            "openai_api_key": request.openai_api_key or os.getenv("OPENAI_API_KEY"),
            "openai_model": request.openai_model or os.getenv("OPENAI_MODEL", "gpt-4o"),
            "gemini_api_key": request.gemini_api_key or os.getenv("GOOGLE_API_KEY"),
            "gemini_model": request.gemini_model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        }
        
        # Prepare request data for background task
        request_data = {
            "api_key": request.api_key,
            "client_name": request.client_name,
            "auditor_name": request.auditor_name,
            "client_code": getattr(request, 'client_code', None),
            "industry": request.industry,
            "date_range": date_range_dict
        }
        
        # Create report record with PROCESSING status
        db = SessionLocal()
        try:
            api_key_hash = hashlib.sha256(request.api_key.encode()).hexdigest() if request.api_key else None
            
            # Try to create report with created_by_id=None
            # If it fails due to NOT NULL constraint, try to run migration automatically
            try:
                db_report = Report(
                    filename=f"audit_{request.client_name}_pending",
                    client_name=request.client_name,
                    auditor_name=request.auditor_name,
                    client_code=getattr(request, 'client_code', None),
                    industry=request.industry,
                    analysis_period_days=request.days,
                    status=ReportStatus.PROCESSING,
                    klaviyo_api_key_hash=api_key_hash,
                    llm_provider=request.llm_provider,
                    llm_model=request.claude_model or request.openai_model or request.gemini_model,
                    created_by_id=None
                )
                db.add(db_report)
                db.commit()
                db.refresh(db_report)
                report_id = db_report.id
                print(f"✓ Created report record with ID: {report_id}")
            except Exception as db_error:
                error_str = str(db_error)
                if "created_by_id" in error_str and "not-null" in error_str.lower():
                    # Database still has NOT NULL constraint - try to fix it
                    print("⚠️  Database schema needs migration. Attempting automatic migration...")
                    try:
                        from sqlalchemy import text
                        # Use raw connection for DDL operations
                        with db.connection() as conn:
                            conn.execute(text("ALTER TABLE reports ALTER COLUMN created_by_id DROP NOT NULL;"))
                            conn.commit()
                        print("✓ Migration applied. Retrying report creation...")
                        
                        # Retry creating the report
                        db_report = Report(
                            filename=f"audit_{request.client_name}_pending",
                            client_name=request.client_name,
                            auditor_name=request.auditor_name,
                            client_code=getattr(request, 'client_code', None),
                            industry=request.industry,
                            analysis_period_days=request.days,
                            status=ReportStatus.PROCESSING,
                            klaviyo_api_key_hash=api_key_hash,
                            llm_provider=request.llm_provider,
                            llm_model=request.claude_model or request.openai_model or request.gemini_model,
                            created_by_id=None
                        )
                        db.add(db_report)
                        db.commit()
                        db.refresh(db_report)
                        report_id = db_report.id
                        print(f"✓ Created report record with ID: {report_id}")
                    except Exception as migrate_error:
                        db.rollback()
                        raise HTTPException(
                            status_code=500,
                            detail=f"Database migration required. Please run: python scripts/migrate_reports_created_by_id.py. Error: {str(migrate_error)}"
                        )
                else:
                    # Re-raise if it's a different error
                    raise
        finally:
            db.close()
        
        # Initialize cache immediately so status endpoint has initial values
        from datetime import datetime
        start_time = datetime.now()
        _report_cache[report_id] = {
            "progress": 0.0,
            "step": "Initializing...",
            "start_time": start_time.isoformat()
        }
        
        # Add background task
        background_tasks.add_task(
            _process_audit_background,
            report_id=report_id,
            request_data=request_data,
            llm_config=llm_config
        )
        
        # Return immediately with report_id
        return AuditResponse(
            success=True,
            report_id=report_id,
            status="processing",
            report_url=None,
            html_content=None,
            report_data={"report_id": report_id, "status": "processing"}
        )
        
    except Exception as e:
        import traceback
        print(f"❌ ERROR in audit generation: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Audit generation failed: {str(e)}")


@router.get("/status/{report_id}", response_model=ReportStatusResponse)
async def get_report_status(report_id: int):
    """Get the status of an audit report generation."""
    db = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Get cached content if available
        cached = _report_cache.get(report_id, {})
        
        if report.status == ReportStatus.COMPLETED:
            return ReportStatusResponse(
                report_id=report.id,
                status="completed",
                progress=100.0,
                report_url=report.file_path_html,
                html_content=cached.get("html_content"),
                report_data=cached.get("report_data", {
                    "filename": report.filename,
                    "html_url": report.file_path_html,
                    "pdf_url": report.file_path_pdf,
                    "word_url": report.file_path_word
                })
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
            cached_progress = cached.get("progress", 0.0)  # Default to 0% if not set (not started yet)
            cached_step = cached.get("step", "Initializing...")
            start_time = cached.get("start_time")
            
            # Calculate estimated time remaining based on progress
            # Use stage-based estimates since progress is not linear
            estimated_remaining = None
            if start_time and cached_progress > 1:
                from datetime import datetime
                try:
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    elapsed = (datetime.now(start_dt.tzinfo) - start_dt).total_seconds()
                    elapsed_minutes = elapsed / 60
                    
                    # Stage-based time estimates (based on typical durations)
                    # Extraction: 0-20% (typically 2-5 min)
                    # Benchmarks: 20-25% (typically < 1 min)
                    # AI Analysis: 25-60% (typically 10-20 min - the longest)
                    # Formatting: 60-80% (typically 1-2 min)
                    # Report Gen: 80-100% (typically 2-5 min)
                    
                    if cached_progress < 20:
                        # Extraction phase: estimate based on typical 3-4 min for extraction, then add remaining stages
                        # If we're at X% of extraction, estimate: (20-X)/20 * 4 min + 15 min (AI) + 3 min (rest)
                        extraction_remaining = ((20 - cached_progress) / 20) * 4  # minutes
                        remaining_phases = 15 + 3  # AI analysis + formatting + report gen
                        estimated_remaining = int(extraction_remaining + remaining_phases)
                    elif cached_progress < 25:
                        # Benchmarks phase: almost done, just add remaining
                        estimated_remaining = int(15 + 3)  # AI + rest
                    elif cached_progress < 60:
                        # AI Analysis phase: the longest part
                        # If we're at X% of AI phase (25-60%), estimate remaining
                        ai_progress = (cached_progress - 25) / 35  # 0-1 progress through AI phase
                        ai_remaining = (1 - ai_progress) * 15  # typical 15 min for AI
                        remaining_phases = 3  # formatting + report gen
                        estimated_remaining = int(ai_remaining + remaining_phases)
                    elif cached_progress < 80:
                        # Formatting phase: estimate remaining
                        formatting_progress = (cached_progress - 60) / 20  # 0-1 progress through formatting
                        formatting_remaining = (1 - formatting_progress) * 1.5  # typical 1.5 min
                        report_gen = 3  # typical 3 min for report gen
                        estimated_remaining = int(formatting_remaining + report_gen)
                    else:
                        # Report generation phase: estimate based on actual progress rate
                        if elapsed > 10:
                            rate = cached_progress / elapsed  # % per second
                            remaining_seconds = (100 - cached_progress) / rate if rate > 0 else 0
                            estimated_remaining = max(1, int(remaining_seconds / 60))
                        else:
                            estimated_remaining = 3  # default for report gen
                    
                    # Ensure reasonable bounds
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


@router.post("/generate-pro", response_model=AuditResponse)
async def generate_audit_pro(request: AuditRequest):
    """
    Generate a professional comprehensive audit report.
    
    This endpoint uses the new modular template system to create
    comprehensive audits matching the quality of manual consultant audits.
    """
    try:
        print(f"🚀 Starting audit generation for {request.client_name}...")
        
        # Initialize services
        klaviyo_service = KlaviyoService(api_key=request.api_key)
        report_service = EnhancedReportService()
        
        # Step 1: Extract audit data
        # Use date_range if provided (for YTD or custom ranges), otherwise use days
        industry = getattr(request, 'industry', None) or "apparel_accessories"
        
        # Convert date_range to dict format if provided
        date_range_dict = None
        if request.date_range:
            date_range_dict = {
                "start": request.date_range.start,
                "end": request.date_range.end
            }
            print(f"📊 Extracting audit data (date range: {date_range_dict['start']} to {date_range_dict['end']}, industry: {industry})...")
        else:
            # Use days parameter if provided, otherwise default to 90 days
            days = request.days or 90
            print(f"📊 Extracting audit data ({days} days, industry: {industry})...")
        
        # Extract data using date_range if available, otherwise use days
        if date_range_dict:
            # Use date_range for YTD or custom ranges
            audit_data = await klaviyo_service.format_audit_data(
                days=0,  # Will be calculated from date_range
                industry=industry,
                verbose=True,
                date_range=date_range_dict
            )
        else:
            # Use days parameter for standard periods
            audit_data = await klaviyo_service.extract_audit_data(days=days, industry=industry)
        
        # Step 2: Generate audit report
        print("📝 Generating comprehensive audit report...")
        
        # Prepare LLM configuration from request
        llm_config = {}
        if request.llm_provider:
            llm_config["provider"] = request.llm_provider
        if request.anthropic_api_key:
            llm_config["anthropic_api_key"] = request.anthropic_api_key
        if request.claude_model:
            llm_config["claude_model"] = request.claude_model
        if request.openai_api_key:
            llm_config["openai_api_key"] = request.openai_api_key
        if request.openai_model:
            llm_config["openai_model"] = request.openai_model
        if request.gemini_api_key:
            llm_config["gemini_api_key"] = request.gemini_api_key
        if request.gemini_model:
            llm_config["gemini_model"] = request.gemini_model
        
        report = await report_service.generate_audit(
            audit_data=audit_data,
            client_name=request.client_name,
            auditor_name=request.auditor_name,
            client_code=getattr(request, 'client_code', None),
            industry=getattr(request, 'industry', None),
            llm_config=llm_config if llm_config else None
        )
        
        print(f"✅ Audit report generated: {report.get('html_url')}")
        if report.get('pdf_url'):
            print(f"✅ PDF report generated: {report.get('pdf_url')}")
        if report.get('word_url'):
            print(f"✅ Word report generated: {report.get('word_url')}")
        
        # Convert file paths to relative HTTP download URLs
        report_filename = report.get("filename", "")
        
        def get_download_url_from_filename(filename):
            """Create relative download URL from filename."""
            if not filename:
                return None
            # Extract just the filename if it's a full path
            from pathlib import Path
            clean_filename = Path(filename).name
            return f"/api/audit/download-file?path={clean_filename}"
        
        html_download_url = None
        pdf_download_url = None
        word_download_url = None
        
        if report_filename:
            html_download_url = get_download_url_from_filename(report_filename)
            pdf_download_url = get_download_url_from_filename(report_filename.replace('.html', '.pdf'))
            word_download_url = get_download_url_from_filename(report_filename.replace('.html', '.docx'))
        
        # Save report to database
        try:
            # Hash API key for storage (don't store plain text)
            api_key_hash = hashlib.sha256(request.api_key.encode()).hexdigest() if request.api_key else None
            
            db_report = Report(
                filename=report.get("filename", "unknown"),
                client_name=request.client_name,
                auditor_name=request.auditor_name,
                client_code=getattr(request, 'client_code', None),
                industry=getattr(request, 'industry', None),
                analysis_period_days=request.days,
                file_path_html=report.get("html_url"),
                file_path_pdf=report.get("pdf_url"),
                file_path_word=report.get("word_url"),
                status=ReportStatus.COMPLETED,
                klaviyo_api_key_hash=api_key_hash,
                llm_provider=request.llm_provider,
                llm_model=request.claude_model or request.openai_model or request.gemini_model,
                created_by_id=None  # No user auth required for now
            )
            db.add(db_report)
            db.commit()
            db.refresh(db_report)
            print(f"✓ Report saved to database with ID: {db_report.id}")
        except Exception as e:
            print(f"⚠ Warning: Could not save report to database: {e}")
            # Continue even if DB save fails
        
        return AuditResponse(
            success=True,
            report_url=html_download_url,
            report_data={
                "filename": report.get("filename"),
                "pages": report.get("pages"),
                "sections": report.get("sections"),
                "pdf_url": pdf_download_url,
                "word_url": word_download_url,
                "report_id": db_report.id if 'db_report' in locals() else None
            },
            html_content=report.get("html_content")  # Include HTML for inline display
        )
        
    except Exception as e:
        import traceback
        print(f"❌ ERROR in audit generation: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Audit generation failed: {str(e)}")


@router.get("/download-file")
async def download_file(path: str):
    """
    Download a report file by filename.
    Serves files from the reports directory.
    """
    from fastapi.responses import FileResponse
    from pathlib import Path
    import os
    
    # Security: Only allow files from reports directory
    reports_dir = Path(__file__).parent.parent.parent / "data" / "reports"
    file_path = reports_dir / path
    
    # Prevent directory traversal
    try:
        file_path.resolve().relative_to(reports_dir.resolve())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid file path"
        )
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )
    
    # Determine media type from extension
    ext = file_path.suffix.lower()
    media_types = {
        '.html': 'text/html',
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.doc': 'application/msword'
    }
    
    return FileResponse(
        path=str(file_path),
        filename=path,
        media_type=media_types.get(ext, 'application/octet-stream')
    )


@router.get("/test-connection")
async def test_connection(api_key: str):
    """
    Test Klaviyo API connection.
    """
    if not api_key or not api_key.strip():
        raise HTTPException(status_code=400, detail="API key is required")
    
    # Validate API key format (Klaviyo keys start with pk_ or sk_)
    if not (api_key.startswith("pk_") or api_key.startswith("sk_")):
        raise HTTPException(
            status_code=400, 
            detail="Invalid API key format. Klaviyo API keys should start with 'pk_' or 'sk_'"
        )
    
    try:
        klaviyo_service = KlaviyoService(api_key=api_key)
        result = await klaviyo_service.test_connection()
        
        if result:
            return {"success": True, "message": "Connection successful"}
        else:
            # If test_connection returns False, it means the connection failed
            # but no exception was raised. This could be a 401/403 error.
            return {"success": False, "message": "Connection failed: Invalid API key or insufficient permissions. Please check your API key."}
    except HTTPStatusError as e:
        # Handle HTTP status errors with detailed messages
        status_code = e.response.status_code if hasattr(e, 'response') and e.response else 400
        error_msg = "Connection failed"
        
        try:
            # Try to extract error details from response
            if hasattr(e, 'response') and e.response:
                error_data = e.response.json()
                errors = error_data.get("errors", [])
                if errors:
                    error_detail = errors[0].get("detail", "")
                    if error_detail:
                        error_msg = error_detail
        except Exception:
            pass
        
        # Map status codes to user-friendly messages
        if status_code == 401:
            error_msg = "Invalid API key. Please check your Klaviyo API key."
        elif status_code == 403:
            error_msg = "API key does not have sufficient permissions."
        elif status_code == 404:
            error_msg = "API endpoint not found. Please check Klaviyo API version."
        elif status_code == 429:
            error_msg = "Rate limit exceeded. Please try again in a moment."
        elif status_code == 400:
            error_msg = error_msg or "Bad request. Please check your API key format."
        
        return {"success": False, "message": error_msg}
    except Exception as e:
        # Provide more detailed error information for other exceptions
        error_msg = str(e)
        
        # Check for common error patterns
        if "401" in error_msg or "Unauthorized" in error_msg:
            error_msg = "Invalid API key. Please check your Klaviyo API key."
        elif "403" in error_msg or "Forbidden" in error_msg:
            error_msg = "API key does not have sufficient permissions."
        elif "404" in error_msg or "Not Found" in error_msg:
            error_msg = "API endpoint not found. Please check Klaviyo API version."
        elif "429" in error_msg or "Too Many Requests" in error_msg:
            error_msg = "Rate limit exceeded. Please try again in a moment."
        elif "timeout" in error_msg.lower():
            error_msg = "Connection timeout. Please check your internet connection."
        else:
            error_msg = f"Connection failed: {error_msg}"
        
        return {"success": False, "message": error_msg}


@router.post("/test-llm")
async def test_llm(
    provider: str,
    api_key: str,
    model: Optional[str] = None
):
    """
    Test LLM API connection (Claude, OpenAI, or Gemini).
    
    Query Parameters:
        provider: LLM provider ("claude", "openai", or "gemini")
        api_key: API key for the provider
        model: Optional model name (uses default if not provided)
    """
    try:
        from api.services.llm import LLMService
        
        # Create LLM service with the provided API key
        llm_config = {
            "provider": provider,
            f"{provider}_api_key": api_key
        }
        
        if provider == "claude":
            llm_config["anthropic_api_key"] = api_key
            if model:
                llm_config["claude_model"] = model
        elif provider == "openai":
            llm_config["openai_api_key"] = api_key
            if model:
                llm_config["openai_model"] = model
        elif provider == "gemini":
            llm_config["gemini_api_key"] = api_key
            if model:
                llm_config["gemini_model"] = model
        else:
            raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
        
        llm_service = LLMService(
            default_provider=provider,
            llm_config=llm_config
        )
        
        # Test by generating a simple response
        test_data = {"test": "This is a test connection"}
        test_context = {"client_name": "Test Client"}
        
        try:
            response = await llm_service.generate_insights(
                section="test",
                data=test_data,
                context=test_context,
                provider=provider
            )
            
            # If we get a response (even if it's a fallback), the connection worked
            if response and response.get("primary"):
                return {
                    "success": True,
                    "message": f"{provider.capitalize()} API connection successful",
                    "provider": provider
                }
            else:
                return {
                    "success": False,
                    "message": f"{provider.capitalize()} API connection failed - no response",
                    "provider": provider
                }
        except Exception as e:
            error_msg = str(e)
            # Check for common API key errors
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
                return {
                    "success": False,
                    "message": f"Invalid {provider.capitalize()} API key",
                    "provider": provider,
                    "error": error_msg
                }
            else:
                return {
                    "success": False,
                    "message": f"{provider.capitalize()} API error: {error_msg}",
                    "provider": provider,
                    "error": error_msg
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing {provider} API: {str(e)}")

