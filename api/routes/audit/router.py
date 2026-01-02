"""
Main router for audit API endpoints.
Imports and registers all audit-related endpoints.
"""
from fastapi import APIRouter, BackgroundTasks
from typing import Optional

from api.models.schemas import AuditRequest, AuditResponse, ReportStatusResponse
from .request_handlers import handle_generate_audit, handle_generate_audit_pro
from .status_endpoints import get_report_status, cancel_audit, download_file
from .test_endpoints import test_klaviyo_connection, test_llm_connection

router = APIRouter()


@router.post("/generate", response_model=AuditResponse)
async def generate_audit(request: AuditRequest, background_tasks: BackgroundTasks):
    """
    Generate a complete comprehensive audit report for a Klaviyo account (async).
    
    Returns immediately with a report_id. Use /status/{report_id} to poll for completion.
    Uses the enhanced agentic analysis framework and comprehensive report template.
    """
    return await handle_generate_audit(request, background_tasks)


@router.post("/generate-pro", response_model=AuditResponse)
async def generate_audit_pro(request: AuditRequest):
    """
    Generate a professional comprehensive audit report (synchronous).
    
    This endpoint uses the new modular template system to create
    comprehensive audits matching the quality of manual consultant audits.
    """
    return await handle_generate_audit_pro(request)


@router.get("/status/{report_id}", response_model=ReportStatusResponse)
async def get_report_status_endpoint(report_id: int):
    """Get the status of an audit report generation."""
    return await get_report_status(report_id)


@router.post("/cancel/{report_id}")
async def cancel_audit_endpoint(report_id: int):
    """
    Cancel a running audit generation.
    
    This will mark the report as failed and stop the background task.
    """
    return await cancel_audit(report_id)


@router.get("/download-file")
async def download_file_endpoint(path: str, report_id: Optional[int] = None):
    """
    Download a report file by filename or report_id.
    Queries the database to verify the report exists and get the correct file path.
    Serves files from the reports directory.
    """
    return await download_file(path, report_id)


@router.get("/test-connection")
async def test_connection_endpoint(api_key: str):
    """
    Test Klaviyo API connection (GET with query parameter).
    """
    return await test_klaviyo_connection(api_key)


@router.post("/test-klaviyo")
async def test_klaviyo_post_endpoint(request: dict):
    """
    Test Klaviyo API connection (POST with JSON body).
    """
    api_key = request.get("api_key")
    if not api_key:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="API key is required in request body")
    return await test_klaviyo_connection(api_key)


@router.post("/test-llm")
async def test_llm_endpoint(request: dict):
    """
    Test LLM API connection (Claude, OpenAI, or Gemini).
    
    Request Body (JSON):
        provider: LLM provider ("claude", "openai", or "gemini")
        api_key: API key for the provider
        model: Optional model name (uses default if not provided)
    """
    return await test_llm_connection(request)

