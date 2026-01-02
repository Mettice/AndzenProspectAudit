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
        # Extract structured text content from HTML (not raw HTML)
        report_context = ""
        if html_content:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract key metrics and data from tables and sections
            context_parts = []
            
            # Extract KAV metrics
            kav_section = soup.find('section', {'data-section': 'kav_analysis'}) or \
                         soup.find('div', {'id': 'kav_analysis'})
            if kav_section:
                kav_text = kav_section.get_text(separator='\n', strip=True)
                # Extract key numbers
                kav_tables = kav_section.find_all('table')
                for table in kav_tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            context_parts.append(f"{cells[0].get_text(strip=True)}: {cells[1].get_text(strip=True)}")
                context_parts.append(f"\nKAV Analysis Summary:\n{kav_text[:3000]}\n")
            
            # Extract Executive Summary
            exec_section = soup.find('section', {'data-section': 'executive_summary'}) or \
                          soup.find('div', {'id': 'executive_summary'})
            if exec_section:
                exec_text = exec_section.get_text(separator='\n', strip=True)
                context_parts.append(f"\nExecutive Summary:\n{exec_text[:2000]}\n")
            
            # Extract Strategic Recommendations
            strategic_section = soup.find('section', {'data-section': 'strategic_recommendations'}) or \
                               soup.find('div', {'id': 'strategic_recommendations'})
            if strategic_section:
                strategic_text = strategic_section.get_text(separator='\n', strip=True)
                context_parts.append(f"\nStrategic Recommendations:\n{strategic_text[:3000]}\n")
            
            # Extract flow performance data
            flow_sections = soup.find_all('section', {'data-section': lambda x: x and ('flow' in x.lower() or 'welcome' in x.lower() or 'abandoned' in x.lower())})
            for flow_section in flow_sections[:5]:  # Limit to 5 flows
                flow_name = flow_section.get('data-section', 'Unknown Flow')
                flow_text = flow_section.get_text(separator='\n', strip=True)
                # Extract performance metrics from tables
                flow_tables = flow_section.find_all('table')
                flow_metrics = []
                for table in flow_tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            flow_metrics.append(f"{cells[0].get_text(strip=True)}: {cells[1].get_text(strip=True)}")
                if flow_metrics:
                    context_parts.append(f"\n{flow_name} Performance:\n" + "\n".join(flow_metrics[:10]) + "\n")
            
            # Extract campaign performance
            campaign_section = soup.find('section', {'data-section': 'campaign_performance'}) or \
                              soup.find('div', {'id': 'campaign_performance'})
            if campaign_section:
                campaign_text = campaign_section.get_text(separator='\n', strip=True)
                context_parts.append(f"\nCampaign Performance:\n{campaign_text[:2000]}\n")
            
            # Extract list growth data
            list_section = soup.find('section', {'data-section': 'list_growth'}) or \
                         soup.find('div', {'id': 'list_growth'})
            if list_section:
                list_text = list_section.get_text(separator='\n', strip=True)
                context_parts.append(f"\nList Growth:\n{list_text[:1500]}\n")
            
            # Combine all context (limit to 40k chars for safety)
            report_context = '\n'.join(context_parts)
            if len(report_context) > 40000:
                report_context = report_context[:40000] + "\n[... content truncated ...]"
        else:
            report_context = "Report content not available. Please ask general questions about Klaviyo audits."
        
        prompt = f"""You are an expert email marketing consultant reviewing a Klaviyo audit report for a client named {report.client_name}.

AUDIT REPORT CONTEXT:
{report_context}

AVAILABLE SECTIONS IN REPORT:
{chr(10).join(section_list) if section_list else "No sections identified"}

CHAT HISTORY (last 10 messages):
{chr(10).join([f"{msg.get('role', 'unknown')}: {msg.get('content', msg.get('message', ''))}" for msg in formatted_history[-10:]])}

CURRENT USER MESSAGE:
{message.message}

{"SECTION CONTEXT (user clicked on this section):" if section_context else ""}
{section_context if section_context else ""}

INSTRUCTIONS:
1. Answer the user's question based on the audit report content above
2. Reference specific sections and metrics when relevant - use the exact section_id from the available sections list
3. If the user asks about KAV, revenue, or performance metrics, reference the specific numbers from the report context
4. If asked about opportunities, reference the "Areas of Opportunity" or recommendations mentioned in the report
5. Be conversational but professional - write as if you're explaining the audit findings to the client
6. If the user asks to "go to" or "show" a section, include it in section_references so the UI can navigate there
7. If the user asks to edit something, suggest the edit but don't apply it yet - include it in suggested_edits
8. When suggesting edits, provide the full HTML content for that section (preserve structure)

IMPORTANT: You MUST respond with valid JSON only. Do not include any text before or after the JSON object.

RESPOND IN THIS EXACT JSON FORMAT (no markdown, no code blocks, just raw JSON):
{{
    "response": "Your conversational response to the user based on the audit report context",
    "suggested_edits": [],
    "section_references": [],
    "navigation_actions": []
}}

Example response for "why is the kav low?":
{{
    "response": "Based on the audit report, your KAV (Klaviyo Attributed Value) percentage is shown in the KAV Analysis section. This indicates that [explanation based on report context]. To improve this, I recommend [specific recommendations from the report].",
    "suggested_edits": [],
    "section_references": ["kav_analysis", "strategic_recommendations"],
    "navigation_actions": [{{"action": "scroll_to", "section_id": "kav_analysis"}}]
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
        
        # Extract key metrics and opportunities from report HTML
        from bs4 import BeautifulSoup
        key_metrics = {}
        opportunities = []
        
        if report.html_content:
            soup = BeautifulSoup(report.html_content, 'html.parser')
            
            # Extract KAV percentage and revenue
            kav_section = soup.find('section', {'data-section': 'kav_analysis'}) or \
                         soup.find('div', {'id': 'kav_analysis'})
            if kav_section:
                kav_tables = kav_section.find_all('table')
                for table in kav_tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            label = cells[0].get_text(strip=True).lower()
                            value = cells[1].get_text(strip=True)
                            if 'kav' in label or 'attributed' in label:
                                key_metrics['kav_percentage'] = value
                            if 'revenue' in label:
                                key_metrics['revenue'] = value
            
            # Extract strategic recommendations and opportunities
            strategic_section = soup.find('section', {'data-section': 'strategic_recommendations'}) or \
                               soup.find('div', {'id': 'strategic_recommendations'})
            if strategic_section:
                # Extract recommendation cards or lists
                recommendations = strategic_section.find_all(['div', 'li'], class_=lambda x: x and ('recommendation' in x.lower() or 'opportunity' in x.lower()))
                for rec in recommendations[:10]:  # Limit to 10
                    rec_text = rec.get_text(strip=True)
                    if rec_text and len(rec_text) > 20:
                        opportunities.append(rec_text)
            
            # Extract areas of opportunity from tables
            opp_tables = soup.find_all('table', class_=lambda x: x and 'opportunity' in str(x).lower())
            for table in opp_tables:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows[:5]:  # Limit to 5
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        opp_name = cells[0].get_text(strip=True)
                        opp_value = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                        if opp_name:
                            opportunities.append(f"{opp_name}: {opp_value}")
        
        # Build quote generation prompt
        priorities_text = ""
        if quote_request.priorities:
            priorities_text = "\n".join([f"- {p}" for p in quote_request.priorities])
        elif opportunities:
            priorities_text = "\n".join([f"- {opp}" for opp in opportunities[:5]])
        
        metrics_summary = "\n".join([f"{k}: {v}" for k, v in key_metrics.items()])
        
        prompt = f"""You are a sales consultant creating a professional quote for {report.client_name} based on their Klaviyo audit.

KEY METRICS FROM AUDIT:
{metrics_summary if metrics_summary else "See audit report for detailed metrics"}

KEY OPPORTUNITIES IDENTIFIED:
{priorities_text if priorities_text else "Top 3-5 recommendations from the audit"}

RECENT CHAT CONTEXT:
{chr(10).join([f"{msg.role}: {msg.message}" for msg in chat_history[:5]])}

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

