"""
Audit API routes.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from sqlalchemy.orm import Session
from api.models.schemas import AuditRequest, AuditResponse
from api.models.report import Report, ReportStatus
from api.services.klaviyo import KlaviyoService
from api.services.analysis import AgenticAnalysisFramework
from api.services.report import EnhancedReportService
from api.services.benchmark import BenchmarkService
from api.services.auth import get_current_user, require_user_or_admin
from api.database import get_db
from api.models.user import User
import hashlib

router = APIRouter()


@router.post("/generate", response_model=AuditResponse)
async def generate_audit(request: AuditRequest):
    """
    Generate a complete comprehensive audit report for a Klaviyo account.
    
    Uses the enhanced agentic analysis framework and comprehensive report template.
    """
    try:
        print(f"🚀 Starting audit generation for {request.client_name}...")
        
        # DEBUG: Log request parameters
        print(f"🔍 DEBUG: Request parameters:")
        print(f"  days: {request.days}")
        print(f"  date_range: {request.date_range}")
        if request.date_range:
            print(f"  date_range.start: {request.date_range.start}")
            print(f"  date_range.end: {request.date_range.end}")
        
        # Initialize services
        klaviyo_service = KlaviyoService(api_key=request.api_key)
        benchmark_service = BenchmarkService()
        analysis_framework = AgenticAnalysisFramework()
        report_service = EnhancedReportService()
        
        # Step 1: Extract data from Klaviyo
        print("📊 Extracting data from Klaviyo...")
        # Convert DateRange model to dict if provided
        date_range_dict = None
        if request.date_range:
            date_range_dict = {
                "start": request.date_range.start,
                "end": request.date_range.end
            }
            print(f"✅ Using date_range: {date_range_dict['start']} to {date_range_dict['end']}")
        elif request.days:
            # Fallback: convert days to date_range if date_range not provided
            from datetime import datetime, timedelta, timezone
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=request.days)
            date_range_dict = {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
            print(f"⚠️  No date_range provided, converting days={request.days} to date_range: {date_range_dict['start']} to {date_range_dict['end']}")
        else:
            print("⚠️  No date_range or days provided, will use default (365 days)")
        
        klaviyo_data = await klaviyo_service.extract_all_data(
            date_range=date_range_dict
        )
        
        # DEBUG: Show extracted data structure
        print("🔍 DEBUG: Klaviyo data structure:")
        print(f"  Keys: {list(klaviyo_data.keys())}")
        print(f"  Revenue data type: {type(klaviyo_data.get('revenue'))}")
        print(f"  Campaigns count: {len(klaviyo_data.get('campaigns', []))}")
        print(f"  Flows count: {len(klaviyo_data.get('flows', []))}")
        if klaviyo_data.get('revenue'):
            print(f"  Revenue sample: {str(klaviyo_data.get('revenue'))[:200]}...")
        if klaviyo_data.get('campaigns') and len(klaviyo_data['campaigns']) > 0:
            print(f"  Campaign sample: {str(klaviyo_data['campaigns'][0])[:200]}...")
        
        # Step 2: Load benchmarks
        benchmarks = benchmark_service.get_all_benchmarks()
        
        # Step 3: Run comprehensive agentic analysis
        print("🤖 Running comprehensive analysis...")
        analysis_results = await analysis_framework.run_comprehensive_analysis(
            klaviyo_data=klaviyo_data,
            benchmarks=benchmarks,
            client_name=request.client_name
        )
        
        # Step 4: Convert analysis results to audit data format
        print("🔄 Converting analysis results to audit data format...")
        audit_data = await klaviyo_service.format_audit_data(
            date_range=date_range_dict,
            verbose=False
        )
        
        # Step 5: Generate audit report  
        print("📝 Generating audit report...")
        report = await report_service.generate_audit(
            audit_data=audit_data,
            client_name=request.client_name,
            auditor_name=request.auditor_name,
            client_code=getattr(request, 'client_code', None)
        )
        
        print(f"✅ Audit report generated: {report.get('html_url')}")
        print(f"   HTML content length: {len(report.get('html_content', ''))} characters")
        
        return AuditResponse(
            success=True,
            report_url=report.get("html_url"),  # Changed from "url" to "html_url"
            html_content=report.get("html_content"),  # Include HTML content for inline display
            report_data={
                "filename": report.get("filename"),
                "html_url": report.get("html_url"),
                "pdf_url": report.get("pdf_url"),
                "word_url": report.get("word_url"),
                "pages": report.get("pages"),
                "sections": report.get("sections", [])
            }
        )
        
    except Exception as e:
        import traceback
        print(f"❌ ERROR in audit generation: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Audit generation failed: {str(e)}")


@router.post("/generate", response_model=AuditResponse)
async def generate_audit(
    request: AuditRequest,
    current_user: User = Depends(require_user_or_admin),
    db: Session = Depends(get_db)
):
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
                created_by_id=current_user.id
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
async def download_file(
    path: str,
    current_user: User = Depends(require_user_or_admin)
):
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
    try:
        klaviyo_service = KlaviyoService(api_key=api_key)
        result = await klaviyo_service.test_connection()
        return {"success": result, "message": "Connection successful"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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

