"""
Background tasks for audit generation.
Handles async audit report generation in the background.
"""
import asyncio
import os
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session

from api.database import SessionLocal
from api.models.report import Report, ReportStatus
from api.services.klaviyo import KlaviyoService
from api.services.analysis import AgenticAnalysisFramework
from api.services.report import EnhancedReportService
from api.services.benchmark import BenchmarkService
from .shared_state import get_report_cache, get_running_tasks


async def process_audit_background(
    report_id: int,
    request_data: dict,
    llm_config: dict
):
    """Background task to process audit generation."""
    db = SessionLocal()
    _report_cache = get_report_cache()
    
    try:
        # Get report
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            print(f"❌ Report {report_id} not found")
            return
        
        try:
            print(f"🚀 Starting background audit generation for report {report_id}...")
            
            # Initialize progress tracking with start time (preserve if already exists)
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
            
            # Immediately update progress to show we've started (fixes stuck at 0% issue)
            existing_cache = _report_cache.get(report_id, {})
            existing_start_time = existing_cache.get("start_time", datetime.now().isoformat())
            _report_cache[report_id].update({
                "progress": 1.0, 
                "step": "Starting audit generation...",
                "start_time": existing_start_time
            })
            print(f"✓ Progress updated to 1% for report {report_id}")
            
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
            _report_cache[report_id].update({
                "progress": 5.0, 
                "step": "Extracting data from Klaviyo...",
                "start_time": existing_start_time
            })
            print(f"✓ Progress updated to 5% for report {report_id}")
            date_range_dict = request_data.get("date_range")
            
            # Update progress during extraction (continuous progress simulation)
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
                        try:
                            await asyncio.wait_for(extraction_done.wait(), timeout=8.0)
                            break
                        except asyncio.TimeoutError:
                            continue
                    else:
                        time_based_progress = min(19.0, 17.0 + (elapsed / 120.0) * 2.0)
                        if (datetime.now() - last_update).total_seconds() >= 3.0:
                            _report_cache[report_id].update({
                                "progress": time_based_progress, 
                                "step": "Finalizing data extraction..."
                            })
                            last_update = datetime.now()
                        try:
                            await asyncio.wait_for(extraction_done.wait(), timeout=2.0)
                            break
                        except asyncio.TimeoutError:
                            continue
            
            progress_task = asyncio.create_task(simulate_extraction_progress())
            
            try:
                klaviyo_data = await klaviyo_service.extract_all_data(date_range=date_range_dict)
            finally:
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
            
            # Step 3: Run comprehensive agentic analysis (30-60%)
            print("🤖 Running comprehensive analysis...")
            _report_cache[report_id].update({"progress": 30.0, "step": "Running AI analysis..."})
            
            analysis_done = asyncio.Event()
            
            def update_analysis_progress(progress: float, step: str):
                """Update progress based on actual analysis stage."""
                _report_cache[report_id].update({
                    "progress": progress,
                    "step": step
                })
                print(f"✓ Progress updated to {progress:.1f}%: {step}")
            
            try:
                print(f"🤖 Starting AI analysis for report {report_id}...")
                analysis_results = await asyncio.wait_for(
                    analysis_framework.run_comprehensive_analysis(
                        klaviyo_data=klaviyo_data,
                        benchmarks=benchmarks,
                        client_name=request_data["client_name"],
                        progress_callback=update_analysis_progress
                    ),
                    timeout=1800.0  # 30 minutes max
                )
                print(f"✓ AI analysis completed for report {report_id}")
            except asyncio.TimeoutError:
                print(f"❌ AI analysis timed out after 30 minutes for report {report_id}")
                _report_cache[report_id].update({
                    "progress": 30.0,
                    "step": "AI analysis timed out - please try again"
                })
                raise Exception("AI analysis timed out after 30 minutes. Please try again.")
            finally:
                analysis_done.set()
            
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
            html_url = generated_report.get("html_url")
            pdf_url = generated_report.get("pdf_url")
            word_url = generated_report.get("word_url")
            html_content = generated_report.get("html_content")
            
            report.filename = generated_report.get("filename", report.filename)
            if html_url:
                report.file_path_html = Path(html_url).name if html_url else None
            if pdf_url:
                report.file_path_pdf = Path(pdf_url).name if pdf_url else None
            if word_url:
                report.file_path_word = Path(word_url).name if word_url else None
            if html_content:
                report.html_content = html_content
            if llm_config:
                report.llm_config = llm_config
            report.status = ReportStatus.COMPLETED
            
            html_filename = Path(html_url).name if html_url else None
            pdf_filename = Path(pdf_url).name if pdf_url else None
            word_filename = Path(word_url).name if word_url else None
            
            _report_cache[report_id] = {
                "progress": 100.0,
                "step": "Report generation complete",
                "html_content": generated_report.get("html_content"),
                "report_data": {
                    "filename": generated_report.get("filename"),
                    "html_url": f"/api/audit/download-file?path={html_filename}" if html_filename else None,
                    "pdf_url": f"/api/audit/download-file?path={pdf_filename}" if pdf_filename else None,
                    "word_url": f"/api/audit/download-file?path={word_filename}" if word_filename else None,
                    "pages": generated_report.get("pages"),
                    "sections": generated_report.get("sections", [])
                }
            }
            
            db.commit()
            print(f"✅ Audit report {report_id} completed successfully")
            
        except asyncio.CancelledError:
            print(f"⚠️ Report {report_id} was cancelled")
            _report_cache[report_id] = {"error": "Audit generation cancelled", "progress": 0.0}
            report.status = ReportStatus.FAILED
            db.commit()
            raise
        except Exception as e:
            import traceback
            error_msg = str(e)
            print(f"❌ ERROR in background audit generation for report {report_id}: {error_msg}")
            print(f"Traceback: {traceback.format_exc()}")
            
            report.status = ReportStatus.FAILED
            _report_cache[report_id] = {"error": error_msg}
            db.commit()
            
    finally:
        db.close()

