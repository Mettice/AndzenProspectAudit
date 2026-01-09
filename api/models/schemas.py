"""
Pydantic models for API request/response schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class DateRange(BaseModel):
    """Date range for data extraction."""
    start: str = Field(..., description="Start date in ISO format")
    end: str = Field(..., description="End date in ISO format")


class AuditRequest(BaseModel):
    """Request model for audit generation."""
    api_key: str = Field(..., description="Klaviyo API key")
    client_name: str = Field(..., description="Client/company name")
    client_type: Optional[str] = Field("prospect", description="Client type: 'prospect' or 'existing'")
    industry: Optional[str] = Field("apparel_accessories", description="Industry for benchmark selection")
    days: Optional[int] = Field(None, description="Number of days for analysis period (90, 180, 365, etc.)")
    date_range: Optional[DateRange] = Field(None, description="Custom date range for analysis (alternative to days)")
    auditor_name: Optional[str] = Field(None, description="Name of auditor")
    client_code: Optional[str] = Field(None, description="Andzen client code")
    # LLM configuration (optional - uses env vars if not provided)
    llm_provider: Optional[str] = Field(None, description="LLM provider: 'claude', 'openai', or 'gemini'")
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic/Claude API key")
    claude_model: Optional[str] = Field(None, description="Claude model name (e.g., 'claude-sonnet-4-5')")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    openai_model: Optional[str] = Field(None, description="OpenAI model name (e.g., 'gpt-4o')")
    gemini_api_key: Optional[str] = Field(None, description="Google Gemini API key")
    gemini_model: Optional[str] = Field(None, description="Gemini model name (e.g., 'gemini-2.0-flash-exp')")


class AuditResponse(BaseModel):
    """Response model for audit generation."""
    success: bool = Field(..., description="Whether the audit was generated successfully")
    report_url: Optional[str] = Field(None, description="URL/path to generated report")
    report_data: Optional[Dict[str, Any]] = Field(None, description="Additional report metadata")
    html_content: Optional[str] = Field(None, description="HTML content of the report for inline display")
    report_id: Optional[int] = Field(None, description="Report ID for status polling (async mode)")
    status: Optional[str] = Field(None, description="Report status: processing, completed, failed")


class ReportStatusResponse(BaseModel):
    """Response model for report status polling."""
    report_id: int = Field(..., description="Report ID")
    status: str = Field(..., description="Status: processing, completed, failed")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    report_url: Optional[str] = Field(None, description="URL/path to generated report (when completed)")
    html_content: Optional[str] = Field(None, description="HTML content (when completed)")
    report_data: Optional[Dict[str, Any]] = Field(None, description="Report metadata (when completed)")
    error: Optional[str] = Field(None, description="Error message (if failed)")
    created_at: Optional[str] = Field(None, description="Report creation date")


class MetricData(BaseModel):
    """Metric data model."""
    metric_id: str
    value: float
    date: str


class CampaignData(BaseModel):
    """Campaign data model."""
    id: str
    name: str
    status: str
    created_at: str
    metrics: Optional[Dict[str, Any]] = None


class FlowData(BaseModel):
    """Flow data model."""
    id: str
    name: str
    status: str
    created_at: str
    messages: Optional[List[Dict[str, Any]]] = None


class KlaviyoData(BaseModel):
    """Complete Klaviyo data model."""
    revenue: Dict[str, Any]
    campaigns: List[CampaignData]
    flows: List[FlowData]
    date_range: DateRange


class AnalysisResult(BaseModel):
    """AI analysis result model."""
    strengths: List[str]
    opportunities: List[str]
    insights: str
    recommendations: List[str]


class BenchmarkComparison(BaseModel):
    """Benchmark comparison model."""
    metric: str
    value: float
    benchmark: Optional[float]
    benchmark_type: Optional[str]
    difference: Optional[float]
    percent_difference: Optional[float]
    percentile: Optional[float]
    status: Optional[str]

