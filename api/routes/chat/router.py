"""
Chat router - API route definitions for chat endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import logging

from ...database import get_db
from ...models.chat import ChatMessage as ChatMessageModel
from .models import ChatMessage, ChatResponse, EditRequest, SaveRequest, ExportRequest, QuoteRequest
from .handlers import handle_chat_message
from .edit_handlers import handle_edit_section, handle_save_report, handle_export_report, handle_get_edit_history
from .quote_handler import handle_generate_quote

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit", tags=["chat"])


@router.post("/{report_id}/chat", response_model=ChatResponse)
async def chat_about_report(
    report_id: int,
    message: ChatMessage,
    db: Session = Depends(get_db)
):
    """
    Chat with AI about a generated audit report.
    
    The AI has access to:
    - Full report content
    - Chat history
    - Section context (if user clicked on a section)
    """
    try:
        return await handle_chat_message(report_id, message, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.delete("/{report_id}/chat/history")
async def clear_chat_history(
    report_id: int,
    db: Session = Depends(get_db)
):
    """Clear chat history for a report."""
    try:
        deleted = db.query(ChatMessageModel).filter(
            ChatMessageModel.report_id == report_id
        ).delete()
        db.commit()
        
        return {"message": f"Cleared {deleted} chat messages for report {report_id}"}
    except Exception as e:
        logger.error(f"Failed to clear chat history: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear chat history")


@router.get("/{report_id}/chat/history")
async def get_chat_history(
    report_id: int,
    db: Session = Depends(get_db)
):
    """Get chat history for a report."""
    try:
        messages = db.query(ChatMessageModel).filter(
            ChatMessageModel.report_id == report_id
        ).order_by(ChatMessageModel.created_at.asc()).all()
        
        return {
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "message": msg.message,
                    "section_id": msg.section_id,
                    "section_references": msg.section_references,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None
                }
                for msg in messages
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat history")


@router.post("/{report_id}/edit")
async def edit_report_section(
    report_id: int,
    edit_request: EditRequest,
    db: Session = Depends(get_db)
):
    """Edit a specific section of the report."""
    try:
        return await handle_edit_section(report_id, edit_request, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error editing report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Edit error: {str(e)}")


@router.get("/{report_id}/edits/history")
async def get_edit_history(
    report_id: int,
    db: Session = Depends(get_db)
):
    """Get edit history for a report."""
    try:
        return await handle_get_edit_history(report_id, db)
    except Exception as e:
        logger.error(f"Error getting edit history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/{report_id}/save")
async def save_report(
    report_id: int,
    save_request: SaveRequest,
    db: Session = Depends(get_db)
):
    """Save edited report content."""
    try:
        return await handle_save_report(report_id, save_request, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/{report_id}/export")
async def export_report(
    report_id: int,
    export_request: ExportRequest,
    db: Session = Depends(get_db)
):
    """Export edited report."""
    try:
        return await handle_export_report(report_id, export_request, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/{report_id}/quote")
async def generate_quote(
    report_id: int,
    quote_request: QuoteRequest,
    db: Session = Depends(get_db)
):
    """Generate a sales quote based on audit findings."""
    try:
        return await handle_generate_quote(report_id, quote_request, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating quote: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

