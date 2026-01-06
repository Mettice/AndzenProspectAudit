"""
Request handlers for audit generation endpoints.
"""
import hashlib
import os
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.models.schemas import AuditRequest, AuditResponse
from api.models.report import Report, ReportStatus
from api.services.klaviyo import KlaviyoService
from api.services.report import EnhancedReportService
from api.database import SessionLocal, IS_POSTGRES
from api.utils.security import validate_prompt_data
from .shared_state import get_report_cache, get_running_tasks
from .background_tasks import process_audit_background


async def handle_generate_audit(request: AuditRequest, background_tasks: BackgroundTasks):
    """
    Generate a complete comprehensive audit report for a Klaviyo account (async).
    
    Returns immediately with a report_id. Use /status/{report_id} to poll for completion.
    Uses the enhanced agentic analysis framework and comprehensive report template.
    """
    _report_cache = get_report_cache()
    _running_tasks = get_running_tasks()
    
    try:
        # Sanitize and validate user inputs to prevent injection attacks
        try:
            sanitized_data = validate_prompt_data({
                "client_name": request.client_name,
                "auditor_name": getattr(request, 'auditor_name', None),
                "industry": getattr(request, 'industry', None),
                "client_code": getattr(request, 'client_code', None)
            })
            # Update request with sanitized values
            request.client_name = sanitized_data.get("client_name", request.client_name)
            if hasattr(request, 'auditor_name') and sanitized_data.get("auditor_name"):
                request.auditor_name = sanitized_data["auditor_name"]
            if hasattr(request, 'industry') and sanitized_data.get("industry"):
                request.industry = sanitized_data["industry"]
            if hasattr(request, 'client_code') and sanitized_data.get("client_code"):
                request.client_code = sanitized_data["client_code"]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
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
            # If it fails due to missing column, try to run migration automatically
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
                    llm_config=llm_config,  # Save LLM config immediately so chat can use it
                    created_by_id=None
                )
                db.add(db_report)
                db.commit()
                db.refresh(db_report)
                report_id = db_report.id
                print(f"✓ Created report record with ID: {report_id}")
                print(f"✓ Saved LLM config: provider={llm_config.get('provider')}, has_api_key={bool(llm_config.get('anthropic_api_key') or llm_config.get('openai_api_key') or llm_config.get('gemini_api_key'))}")
            except Exception as db_error:
                error_str = str(db_error)
                # Check for missing columns
                if "html_content" in error_str or "llm_config" in error_str:
                    # Missing columns - try to add them automatically
                    print("⚠️  Database schema needs migration. Attempting automatic migration for html_content/llm_config...")
                    try:
                        # Use raw connection for DDL operations
                        with db.connection() as conn:
                            # Check if columns exist and add if missing
                            if IS_POSTGRES:
                                # PostgreSQL - check and add html_content
                                check_html = conn.execute(text("""
                                    SELECT column_name 
                                    FROM information_schema.columns 
                                    WHERE table_name='reports' AND column_name='html_content'
                                """))
                                if not check_html.fetchone():
                                    conn.execute(text("ALTER TABLE reports ADD COLUMN html_content TEXT;"))
                                    print("✓ Added html_content column")
                                
                                # Check and add llm_config
                                check_llm = conn.execute(text("""
                                    SELECT column_name 
                                    FROM information_schema.columns 
                                    WHERE table_name='reports' AND column_name='llm_config'
                                """))
                                if not check_llm.fetchone():
                                    conn.execute(text("ALTER TABLE reports ADD COLUMN llm_config JSONB;"))
                                    print("✓ Added llm_config column")
                            else:
                                # SQLite - check and add columns
                                pragma = conn.execute(text("PRAGMA table_info(reports)"))
                                columns = [row[1] for row in pragma.fetchall()]
                                
                                if 'html_content' not in columns:
                                    conn.execute(text("ALTER TABLE reports ADD COLUMN html_content TEXT;"))
                                    print("✓ Added html_content column")
                                
                                if 'llm_config' not in columns:
                                    conn.execute(text("ALTER TABLE reports ADD COLUMN llm_config TEXT;"))
                                    print("✓ Added llm_config column")
                            
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
                            llm_config=llm_config,  # Save LLM config immediately so chat can use it
                            created_by_id=None
                        )
                        db.add(db_report)
                        db.commit()
                        db.refresh(db_report)
                        report_id = db_report.id
                        print(f"✓ Created report record with ID: {report_id}")
                        print(f"✓ Saved LLM config: provider={llm_config.get('provider')}, has_api_key={bool(llm_config.get('anthropic_api_key') or llm_config.get('openai_api_key') or llm_config.get('gemini_api_key'))}")
                    except Exception as migrate_error:
                        db.rollback()
                        raise HTTPException(
                            status_code=500,
                            detail=f"Database migration required. Please run: python scripts/migrate_add_html_content.py. Error: {str(migrate_error)}"
                        )
                elif "created_by_id" in error_str and "not-null" in error_str.lower():
                    # Database still has NOT NULL constraint - try to fix it
                    print("⚠️  Database schema needs migration. Attempting automatic migration for created_by_id...")
                    try:
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
                            llm_config=llm_config,  # Save LLM config immediately so chat can use it
                            created_by_id=None
                        )
                        db.add(db_report)
                        db.commit()
                        db.refresh(db_report)
                        report_id = db_report.id
                        print(f"✓ Created report record with ID: {report_id}")
                        print(f"✓ Saved LLM config: provider={llm_config.get('provider')}, has_api_key={bool(llm_config.get('anthropic_api_key') or llm_config.get('openai_api_key') or llm_config.get('gemini_api_key'))}")
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
        start_time = datetime.now()
        _report_cache[report_id] = {
            "progress": 0.0,
            "step": "Initializing...",
            "start_time": start_time.isoformat()
        }
        
        # Add background task and track it
        task = background_tasks.add_task(
            process_audit_background,
            report_id=report_id,
            request_data=request_data,
            llm_config=llm_config
        )
        _running_tasks[report_id] = task
        
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


async def handle_generate_audit_pro(request: AuditRequest):
    """
    Generate a professional comprehensive audit report (synchronous).
    
    This endpoint uses the new modular template system to create
    comprehensive audits matching the quality of manual consultant audits.
    """
    try:
        print(f"🚀 Starting audit generation for {request.client_name}...")
        
        # Initialize services
        klaviyo_service = KlaviyoService(api_key=request.api_key)
        report_service = EnhancedReportService()
        
        # Step 1: Extract audit data
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
            days = request.days or 90
            print(f"📊 Extracting audit data ({days} days, industry: {industry})...")
        
        # Extract data using date_range if available, otherwise use days
        if date_range_dict:
            audit_data = await klaviyo_service.format_audit_data(
                days=0,
                industry=industry,
                verbose=True,
                date_range=date_range_dict
            )
        else:
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
        db = SessionLocal()
        try:
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
                created_by_id=None
            )
            db.add(db_report)
            db.commit()
            db.refresh(db_report)
            print(f"✓ Report saved to database with ID: {db_report.id}")
        except Exception as e:
            print(f"⚠ Warning: Could not save report to database: {e}")
        finally:
            db.close()
        
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
            html_content=report.get("html_content")
        )
        
    except Exception as e:
        import traceback
        print(f"❌ ERROR in audit generation: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Audit generation failed: {str(e)}")

