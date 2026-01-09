"""
Pydantic models for chat API.
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ChatMessage(BaseModel):
    """Chat message model."""
    message: str
    section_id: Optional[str] = None  # If user clicked on a specific section
    report_id: Optional[int] = None  # Optional - can be in URL path instead
    full_context: Optional[Dict[str, Any]] = None  # Frontend-provided full context
    available_sections: Optional[List[str]] = None  # Frontend-provided section list
    system_context: Optional[Dict[str, Any]] = None  # Frontend-provided system context
    context_type: Optional[str] = None  # Type of context being sent
    
    class Config:
        # Allow extra fields to be ignored (for backward compatibility)
        extra = "ignore"


class ChatAction(BaseModel):
    """Represents an action the chat can perform."""
    action_type: str  # "regenerate_section", "edit_content", "add_content", "analyze_deeper"
    target_section: Optional[str] = None
    description: str
    parameters: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None  # How confident the AI is this will help


class ChatResponse(BaseModel):
    """Enhanced chat response model with actions."""
    response: str
    suggested_actions: Optional[List[ChatAction]] = None
    suggested_edits: Optional[List[Dict[str, Any]]] = None
    section_references: Optional[List[str]] = None
    navigation_actions: Optional[List[Dict[str, Any]]] = None
    data_insights: Optional[Dict[str, Any]] = None  # Key metrics/insights extracted


class EditRequest(BaseModel):
    """Edit request model."""
    report_id: int
    section_id: str
    new_content: str
    edit_source: str = "manual"  # "manual" or "chat"
    chat_message_id: Optional[int] = None


class SaveRequest(BaseModel):
    """Save request model."""
    html_content: str


class ExportRequest(BaseModel):
    """Export request model."""
    html_content: str
    format: str = "html"  # html, pdf, word


class QuoteRequest(BaseModel):
    """Quote generation request model."""
    priorities: Optional[List[str]] = None  # List of priority items
    custom_message: Optional[str] = None  # Custom instructions
