"""
Chat interface for interacting with generated audit reports.
Allows users to ask questions and make edits via conversational interface.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import logging
import json
from ..database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit", tags=["chat"])


class ChatMessage(BaseModel):
    """Chat message model."""
    message: str
    section_id: Optional[str] = None  # If user clicked on a specific section
    report_id: int


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    suggested_edits: Optional[List[Dict[str, Any]]] = None
    section_references: Optional[List[str]] = None
    navigation_actions: Optional[List[Dict[str, Any]]] = None


class EditRequest(BaseModel):
    """Edit request model."""
    report_id: int
    section_id: str
    new_content: str
    edit_source: str = "manual"  # "manual" or "chat"
    chat_message_id: Optional[int] = None


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
        # Get report from database
        from ..models.report import Report
        report = db.query(Report).filter(Report.id == report_id).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Get chat history
        from ..models.chat import ChatMessage as ChatMessageModel
        chat_history = db.query(ChatMessageModel).filter(
            ChatMessageModel.report_id == report_id
        ).order_by(ChatMessageModel.created_at.asc()).all()
        
        # Format chat history for LLM
        formatted_history = []
        for msg in chat_history:
            formatted_history.append({
                "role": msg.role,
                "content": msg.message
            })
        
        # Get HTML content (handle None case)
        html_content = report.html_content or ""
        if not html_content and report.file_path_html:
            # Try to load from file if not in database
            try:
                from pathlib import Path
                reports_dir = Path(__file__).parent.parent.parent / "data" / "reports"
                html_filename = Path(report.file_path_html).name
                html_file_path = reports_dir / html_filename
                if html_file_path.exists():
                    with open(html_file_path, "r", encoding="utf-8") as f:
                        html_content = f.read()
            except Exception as e:
                logger.warning(f"Could not load HTML from file: {e}")
        
        # Get section context if provided
        section_context = None
        if message.section_id and html_content:
            # Extract section content from report HTML
            import re
            section_match = re.search(
                f'<section[^>]*data-section="{message.section_id}"[^>]*>(.*?)</section>',
                html_content,
                re.DOTALL
            )
            if section_match:
                section_context = section_match.group(1)[:2000]  # Limit context
        
        # Call LLM service for chat
        from ..services.llm import LLMService
        
        # Initialize LLM service (use report's LLM config if available)
        llm_config = {}
        if hasattr(report, 'llm_config') and report.llm_config:
            # If llm_config is stored as JSON string (SQLite), parse it
            if isinstance(report.llm_config, str):
                import json
                try:
                    llm_config = json.loads(report.llm_config)
                except (json.JSONDecodeError, TypeError):
                    llm_config = {}
            else:
                llm_config = report.llm_config or {}
        
        # Log what we're using
        logger.info(f"Chat LLM config: provider={llm_config.get('provider')}, has_anthropic_key={bool(llm_config.get('anthropic_api_key'))}, has_openai_key={bool(llm_config.get('openai_api_key'))}, has_gemini_key={bool(llm_config.get('gemini_api_key'))}")
        
        # Fallback to environment variables if no config or missing API key
        import os
        provider = llm_config.get("provider", "claude")
        
        # Ensure we have an API key for the selected provider
        if provider == "claude" and not llm_config.get("anthropic_api_key"):
            llm_config["anthropic_api_key"] = os.getenv("ANTHROPIC_API_KEY")
        elif provider == "openai" and not llm_config.get("openai_api_key"):
            llm_config["openai_api_key"] = os.getenv("OPENAI_API_KEY")
        elif provider == "gemini" and not llm_config.get("gemini_api_key"):
            llm_config["gemini_api_key"] = os.getenv("GOOGLE_API_KEY")
        
        # Ensure provider is set
        if not llm_config.get("provider"):
            llm_config["provider"] = "claude"
        
        # Validate we have an API key
        if provider == "claude" and not llm_config.get("anthropic_api_key"):
            raise HTTPException(status_code=400, detail="Anthropic API key not found. Please ensure the API key was provided during audit generation.")
        elif provider == "openai" and not llm_config.get("openai_api_key"):
            raise HTTPException(status_code=400, detail="OpenAI API key not found. Please ensure the API key was provided during audit generation.")
        elif provider == "gemini" and not llm_config.get("gemini_api_key"):
            raise HTTPException(status_code=400, detail="Gemini API key not found. Please ensure the API key was provided during audit generation.")
        
        llm_service = LLMService(
            default_provider=llm_config.get("provider", "claude"),
            anthropic_api_key=llm_config.get("anthropic_api_key"),
            openai_api_key=llm_config.get("openai_api_key"),
            gemini_api_key=llm_config.get("gemini_api_key"),
            claude_model=llm_config.get("claude_model"),
            openai_model=llm_config.get("openai_model"),
            gemini_model=llm_config.get("gemini_model")
        )
        
        # Extract section list for better navigation
        section_list = []
        if html_content:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            sections = soup.find_all(['section', 'div'], {'data-section': True}) or \
                      soup.find_all('section', {'id': True})
            for sec in sections[:20]:  # Limit to first 20 sections
                section_id = sec.get('data-section') or sec.get('id')
                section_title = sec.find(['h1', 'h2', 'h3', 'h4'])
                if section_title:
                    section_list.append(f"- {section_id}: {section_title.get_text().strip()[:50]}")
        
        # Build prompt with report context
        # Use smarter context extraction - prioritize sections mentioned in chat history
        report_context = ""
        if html_content:
            # If user mentioned specific sections in history, prioritize those
            mentioned_sections = []
            for msg in formatted_history[-5:]:  # Check last 5 messages
                if isinstance(msg, dict) and 'content' in msg:
                    import re
                    # Look for section mentions (e.g., "executive summary", "KAV analysis")
                    section_patterns = [
                        r'executive\s+summary', r'kav\s+analysis', r'campaign\s+performance',
                        r'flow\s+performance', r'data\s+capture', r'segmentation',
                        r'list\s+growth', r'automation', r'strategic\s+recommendations'
                    ]
                    for pattern in section_patterns:
                        if re.search(pattern, msg['content'], re.IGNORECASE):
                            mentioned_sections.append(pattern.replace(r'\s+', '_'))
            
            # Extract full report context (limit to 50k chars)
            if len(html_content) <= 50000:
                report_context = html_content
            else:
                # If too large, extract key sections first
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Priority sections to always include
                priority_sections = ['executive_summary', 'kav_analysis', 'strategic_recommendations']
                context_parts = []
                
                for section_id in priority_sections:
                    section = soup.find('section', {'data-section': section_id}) or \
                             soup.find('div', {'id': section_id})
                    if section:
                        context_parts.append(str(section)[:10000])  # 10k per priority section
                
                # Add remaining content up to limit
                remaining = 50000 - sum(len(p) for p in context_parts)
                if remaining > 0:
                    # Get text content (strip HTML tags for more text)
                    text_content = soup.get_text()[:remaining]
                    context_parts.append(text_content)
                
                report_context = '\n\n'.join(context_parts)
        else:
            report_context = "Report content not available. Please ask general questions about Klaviyo audits."
        
        prompt = f"""You are an expert email marketing consultant reviewing an audit report for a client.

REPORT CONTEXT:
{report_context}

AVAILABLE SECTIONS IN REPORT:
{chr(10).join(section_list) if section_list else "No sections identified"}

CHAT HISTORY:
{formatted_history[-10:]}  # Last 10 messages

CURRENT USER MESSAGE:
{message.message}

{"SECTION CONTEXT (user clicked on this section):" if section_context else ""}
{section_context if section_context else ""}

INSTRUCTIONS:
1. Answer the user's question based on the audit report content
2. Reference specific sections and metrics when relevant - use the exact section_id from the list above
3. If the user asks to edit something, suggest the edit but don't apply it yet
4. Be conversational but professional
5. If asked about opportunities, reference the "Areas of Opportunity" tables
6. If asked about revenue, reference the KAV section
7. If the user asks to "go to" or "show" a section, include it in section_references so the UI can navigate there
8. You can suggest edits to any section - use the section_id from the available sections list
9. When suggesting edits, provide the full HTML content for that section (preserve structure)

RESPOND IN JSON FORMAT:
{{
    "response": "Your conversational response to the user",
    "suggested_edits": [  // Optional: if user requested edits
        {{
            "section_id": "executive_summary",  // Must match a section from the available sections list
            "reason": "User asked to make it more concise",
            "new_content": "<div>Updated HTML content...</div>"  // Full HTML for the section
        }}
    ],
    "section_references": ["executive_summary", "kav_analysis"],  // Sections you referenced - UI will scroll to these
    "navigation_actions": [  // Optional: if user wants to navigate
        {{
            "action": "scroll_to",  // or "highlight"
            "section_id": "kav_analysis"
        }}
    ]
}}"""
        
        # Call LLM
        llm_response = await llm_service.generate_insights(
            section="chat",
            data={"prompt": prompt},
            context={}
        )
        
        # Parse response (should be JSON)
        try:
            if isinstance(llm_response, str):
                # Try to extract JSON from response
                if llm_response.strip().startswith('{'):
                    parsed = json.loads(llm_response)
                else:
                    # If not JSON, wrap in response
                    parsed = {"response": llm_response}
            else:
                parsed = llm_response
            
            response_text = parsed.get("response", str(llm_response))
            suggested_edits = parsed.get("suggested_edits", [])
            section_references = parsed.get("section_references", [])
            navigation_actions = parsed.get("navigation_actions", [])
        except json.JSONDecodeError:
            # Fallback: treat entire response as text
            response_text = str(llm_response)
            suggested_edits = []
            section_references = []
            navigation_actions = []
        
        # Save chat messages to database
        user_msg = ChatMessageModel(
            report_id=report_id,
            role="user",
            message=message.message,
            section_id=message.section_id,
            section_references=section_references
        )
        db.add(user_msg)
        db.flush()  # Get ID
        
        assistant_msg = ChatMessageModel(
            report_id=report_id,
            role="assistant",
            message=response_text,
            suggested_edits=suggested_edits,
            section_references=section_references,
            parent_message_id=user_msg.id
        )
        db.add(assistant_msg)
        db.commit()
        
        return ChatResponse(
            response=response_text,
            suggested_edits=suggested_edits if suggested_edits else None,
            section_references=section_references if section_references else None,
            navigation_actions=navigation_actions if navigation_actions else None
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.post("/{report_id}/edit")
async def edit_report_section(
    report_id: int,
    edit_request: EditRequest,
    db: Session = Depends(get_db)
):
    """
    Edit a specific section of the report.
    Can be triggered manually or by chat.
    """
    try:
        from ..models.report import Report
        report = db.query(Report).filter(Report.id == report_id).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Parse HTML and update section
        import re
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(report.html_content, 'html.parser')
        
        # Find section by data-section attribute or ID
        section = soup.find('section', {'data-section': edit_request.section_id}) or \
                  soup.find('div', {'id': edit_request.section_id}) or \
                  soup.find('section', {'id': edit_request.section_id})
        
        if not section:
            raise HTTPException(
                status_code=404,
                detail=f"Section '{edit_request.section_id}' not found in report"
            )
        
        # Store old content for undo
        old_content = str(section)
        
        # Update section content
        # If new_content is HTML, parse and replace
        # If it's plain text, wrap in appropriate tags
        if edit_request.new_content.strip().startswith('<'):
            # HTML content
            new_soup = BeautifulSoup(edit_request.new_content, 'html.parser')
            section.clear()
            section.append(new_soup)
        else:
            # Plain text - wrap in paragraph
            section.clear()
            p_tag = soup.new_tag('p')
            p_tag.string = edit_request.new_content
            section.append(p_tag)
        
        # Update report HTML
        updated_html = str(soup)
        report.html_content = updated_html
        
        # Save edit history
        from ..models.chat import ReportEdit
        edit_record = ReportEdit(
            report_id=report_id,
            section_id=edit_request.section_id,
            old_content=old_content,
            new_content=str(section),
            edit_source=edit_request.edit_source,
            chat_message_id=edit_request.chat_message_id
        )
        db.add(edit_record)
        db.commit()
        
        return {
            "success": True,
            "updated_section": edit_request.section_id,
            "preview": str(section)[:500]  # Preview of updated section
        }
        
    except Exception as e:
        logger.error(f"Error editing report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Edit error: {str(e)}")


@router.get("/{report_id}/chat/history")
async def get_chat_history(
    report_id: int,
    db: Session = Depends(get_db)
):
    """Get chat history for a report."""
    try:
        from ..models.chat import ChatMessage as ChatMessageModel
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
                    "suggested_edits": msg.suggested_edits,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in messages
            ]
        }
    except Exception as e:
        logger.error(f"Error getting chat history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/{report_id}/edits/history")
async def get_edit_history(
    report_id: int,
    db: Session = Depends(get_db)
):
    """Get edit history for a report."""
    try:
        from ..models.chat import ReportEdit
        edits = db.query(ReportEdit).filter(
            ReportEdit.report_id == report_id
        ).order_by(ReportEdit.created_at.desc()).all()
        
        return {
            "edits": [
                {
                    "id": edit.id,
                    "section_id": edit.section_id,
                    "edit_source": edit.edit_source,
                    "created_at": edit.created_at.isoformat(),
                    "preview": edit.new_content[:200]
                }
                for edit in edits
            ]
        }
    except Exception as e:
        logger.error(f"Error getting edit history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


class SaveRequest(BaseModel):
    """Save request model."""
    html_content: str


@router.post("/{report_id}/save")
async def save_report(
    report_id: int,
    save_request: SaveRequest,
    db: Session = Depends(get_db)
):
    """Save edited report content."""
    try:
        from ..models.report import Report
        report = db.query(Report).filter(Report.id == report_id).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Update HTML content
        report.html_content = save_request.html_content
        db.commit()
        
        return {
            "success": True,
            "message": "Report saved successfully"
        }
    except Exception as e:
        logger.error(f"Error saving report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


class ExportRequest(BaseModel):
    """Export request model."""
    html_content: str
    format: str = "html"  # html, pdf, word


@router.post("/{report_id}/export")
async def export_report(
    report_id: int,
    export_request: ExportRequest,
    db: Session = Depends(get_db)
):
    """Export edited report."""
    try:
        from ..models.report import Report
        from pathlib import Path
        import os
        from datetime import datetime
        
        report = db.query(Report).filter(Report.id == report_id).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Save updated HTML content
        report.html_content = export_request.html_content
        db.commit()
        
        # Generate export file
        reports_dir = Path(__file__).parent.parent.parent / "data" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audit_{report.client_name.replace(' ', '_')}_edited_{timestamp}.html"
        file_path = reports_dir / filename
        
        # Write HTML file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(export_request.html_content)
        
        # Return download URL
        return {
            "success": True,
            "filename": filename,
            "download_url": f"/api/audit/download-file?path={filename}"
        }
    except Exception as e:
        logger.error(f"Error exporting report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


class QuoteRequest(BaseModel):
    """Quote generation request model."""
    priorities: Optional[List[str]] = None  # List of priority items
    custom_message: Optional[str] = None  # Custom instructions


@router.post("/{report_id}/quote")
async def generate_quote(
    report_id: int,
    quote_request: QuoteRequest,
    db: Session = Depends(get_db)
):
    """Generate a sales quote based on audit findings."""
    try:
        from ..models.report import Report
        from ..services.llm import LLMService
        
        report = db.query(Report).filter(Report.id == report_id).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Get chat history for context
        from ..models.chat import ChatMessage as ChatMessageModel
        chat_history = db.query(ChatMessageModel).filter(
            ChatMessageModel.report_id == report_id
        ).order_by(ChatMessageModel.created_at.desc()).limit(10).all()
        
        # Initialize LLM service
        llm_config = {}
        if hasattr(report, 'llm_config') and report.llm_config:
            llm_config = report.llm_config
        
        llm_service = LLMService(
            default_provider=llm_config.get("provider", "claude"),
            anthropic_api_key=llm_config.get("anthropic_api_key"),
            openai_api_key=llm_config.get("openai_api_key"),
            gemini_api_key=llm_config.get("gemini_api_key"),
            claude_model=llm_config.get("claude_model"),
            openai_model=llm_config.get("openai_model"),
            gemini_model=llm_config.get("gemini_model")
        )
        
        # Build quote generation prompt
        priorities_text = ""
        if quote_request.priorities:
            priorities_text = "\n".join([f"- {p}" for p in quote_request.priorities])
        
        prompt = f"""You are a sales consultant creating a professional quote for {report.client_name} based on their Klaviyo audit.

AUDIT REPORT SUMMARY:
{report.html_content[:10000]}  # First 10k chars for context

RECENT CHAT CONTEXT:
{chr(10).join([f"{msg.role}: {msg.message}" for msg in chat_history[:5]])}

PRIORITIES TO INCLUDE:
{priorities_text if priorities_text else "Top 3-5 recommendations from the audit"}

CUSTOM INSTRUCTIONS:
{quote_request.custom_message or "Create a comprehensive quote covering the main opportunities identified in the audit."}

GENERATE A PROFESSIONAL SALES QUOTE IN JSON FORMAT:
{{
    "quote_title": "Klaviyo Optimization Services for {report.client_name}",
    "executive_summary": "2-3 paragraph overview of the opportunity",
    "services": [
        {{
            "service_name": "Service name",
            "description": "Detailed description",
            "deliverables": ["Deliverable 1", "Deliverable 2"],
            "timeline": "X weeks/months",
            "investment": "$X,XXX"
        }}
    ],
    "total_investment": "$X,XXX",
    "payment_terms": "Payment terms",
    "next_steps": ["Step 1", "Step 2", "Step 3"],
    "expected_roi": "Expected ROI description",
    "quote_valid_until": "Date"
}}

GUIDELINES:
- Be specific with deliverables and timelines
- Base pricing on industry standards and scope
- Highlight expected ROI based on audit findings
- Make it professional and compelling
- Return only the JSON object"""
        
        # Call LLM
        llm_response = await llm_service.generate_insights(
            section="quote",
            data={"prompt": prompt},
            context={}
        )
        
        # Parse response
        import json
        try:
            if isinstance(llm_response, str):
                if llm_response.strip().startswith('{'):
                    quote_data = json.loads(llm_response)
                else:
                    # Fallback: wrap in basic structure
                    quote_data = {
                        "quote_title": f"Klaviyo Optimization Services for {report.client_name}",
                        "executive_summary": llm_response,
                        "services": [],
                        "total_investment": "Contact for pricing",
                        "next_steps": ["Schedule a call to discuss", "Review audit findings", "Customize proposal"]
                    }
            else:
                quote_data = llm_response
        except json.JSONDecodeError:
            quote_data = {
                "quote_title": f"Klaviyo Optimization Services for {report.client_name}",
                "executive_summary": str(llm_response),
                "services": [],
                "total_investment": "Contact for pricing",
                "next_steps": ["Schedule a call to discuss", "Review audit findings", "Customize proposal"]
            }
        
        return {
            "success": True,
            "quote": quote_data
        }
        
    except Exception as e:
        logger.error(f"Error generating quote: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating quote: {str(e)}")

