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
from ..utils.security import sanitize_prompt_input

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit", tags=["chat"])


class ChatMessage(BaseModel):
    """Chat message model."""
    message: str
    section_id: Optional[str] = None  # If user clicked on a specific section
    report_id: int
    full_context: Optional[Dict[str, Any]] = None  # Frontend-provided full context
    available_sections: Optional[List[str]] = None  # Frontend-provided section list
    system_context: Optional[Dict[str, Any]] = None  # Frontend-provided system context
    context_type: Optional[str] = None  # Type of context being sent


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


@router.delete("/{report_id}/chat/history")
async def clear_chat_history(
    report_id: int,
    db: Session = Depends(get_db)
):
    """Clear chat history for a report."""
    try:
        from ..models.chat import ChatMessage as ChatMessageModel
        deleted = db.query(ChatMessageModel).filter(
            ChatMessageModel.report_id == report_id
        ).delete()
        db.commit()
        
        return {"message": f"Cleared {deleted} chat messages for report {report_id}"}
    except Exception as e:
        logger.error(f"Failed to clear chat history: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear chat history")


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
        
        # Sanitize user message to prevent prompt injection
        sanitized_message = sanitize_prompt_input(message.message, max_length=2000)
        logger.info(f"Chat message sanitized: original_length={len(message.message)}, sanitized_length={len(sanitized_message)}")
        
        # Get chat history
        from ..models.chat import ChatMessage as ChatMessageModel
        chat_history = db.query(ChatMessageModel).filter(
            ChatMessageModel.report_id == report_id
        ).order_by(ChatMessageModel.created_at.asc()).all()
        
        # Format chat history for LLM (sanitize user messages)
        formatted_history = []
        for msg in chat_history:
            content = msg.message
            if msg.role == "user":
                content = sanitize_prompt_input(content, max_length=2000)
            formatted_history.append({
                "role": msg.role,
                "content": content
            })
        
        # Get HTML content (handle None case)
        html_content = report.html_content or ""
        logger.info(f"Chat request for report {report_id}: html_content length={len(html_content) if html_content else 0}, file_path_html={report.file_path_html}")
        
        # Extract key metrics from report model  
        report_metrics = {
            'client_name': report.client_name,
            'total_revenue': report.total_revenue,
            'attributed_revenue': report.attributed_revenue,
            'industry': report.industry,
            'analysis_period_days': report.analysis_period_days
        }
        logger.info(f"Report metrics: {report_metrics}")
        
        if not html_content and report.file_path_html:
            # Try to load from file if not in database
            try:
                from pathlib import Path
                import os
                
                # Try the direct file path first
                if os.path.exists(report.file_path_html):
                    logger.info(f"Loading HTML from direct path: {report.file_path_html}")
                    with open(report.file_path_html, "r", encoding="utf-8") as f:
                        html_content = f.read()
                    logger.info(f"✓ Loaded HTML from direct path: {len(html_content)} chars")
                else:
                    # Try the relative path from API folder
                    reports_dir = Path(__file__).parent.parent.parent / "api" / "data" / "reports"
                    html_filename = Path(report.file_path_html).name
                    html_file_path = reports_dir / html_filename
                    logger.info(f"Attempting to load HTML from API path: {html_file_path}")
                    
                    if html_file_path.exists():
                        with open(html_file_path, "r", encoding="utf-8") as f:
                            html_content = f.read()
                        logger.info(f"✓ Loaded HTML from API path: {len(html_content)} chars")
                    else:
                        # Try root data/reports path
                        reports_dir = Path(__file__).parent.parent.parent / "data" / "reports"  
                        html_file_path = reports_dir / html_filename
                        logger.info(f"Attempting to load HTML from root path: {html_file_path}")
                        
                        if html_file_path.exists():
                            with open(html_file_path, "r", encoding="utf-8") as f:
                                html_content = f.read()
                            logger.info(f"✓ Loaded HTML from root path: {len(html_content)} chars")
                        else:
                            logger.warning(f"HTML file not found in any expected location")
                            
            except Exception as e:
                logger.error(f"Could not load HTML from file: {e}", exc_info=True)
        
        if not html_content:
            logger.warning(f"No HTML content available for report {report_id}. Chat will have limited context.")
        
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
        
        # Check if frontend provided full context (preferred over HTML parsing)
        frontend_context = None
        if hasattr(message, 'full_context') and message.full_context:
            frontend_context = message.full_context
            logger.info(f"Using frontend-provided context: {len(frontend_context.get('report_summary', []))} sections")
        
        # Check if frontend provided available sections mapping
        frontend_sections = None
        if hasattr(message, 'available_sections') and message.available_sections:
            frontend_sections = message.available_sections
            logger.info(f"Using frontend-provided section mapping: {len(frontend_sections)} sections")
        
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
        
        # Update outdated Claude models to current version
        claude_model = llm_config.get("claude_model")
        if claude_model and "claude-3-" in claude_model:
            logger.warning(f"Updating outdated Claude model {claude_model} to current version")
            claude_model = "claude-sonnet-4-20250514"  # Use current default
        
        llm_service = LLMService(
            default_provider=llm_config.get("provider", "claude"),
            anthropic_api_key=llm_config.get("anthropic_api_key"),
            openai_api_key=llm_config.get("openai_api_key"),
            gemini_api_key=llm_config.get("gemini_api_key"),
            claude_model=claude_model,
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
        # Prefer frontend-provided context if available (more accurate)
        report_context = ""
        
        if frontend_context:
            # Use frontend-provided context (already parsed and structured)
            context_parts = []
            
            # Prefer full_content if available (most comprehensive)
            if frontend_context.get('full_content'):
                for page in frontend_context['full_content'][:30]:  # First 30 pages
                    if isinstance(page, dict):
                        section_id = page.get('sectionId', page.get('section', 'unknown'))
                        title = page.get('title', 'Untitled')
                        content = page.get('content', '')
                        if content:
                            context_parts.append(f"{title} ({section_id}):\n{content[:3000]}\n")
                logger.info(f"✓ Using frontend full_content: {len(frontend_context['full_content'])} pages")
            
            # Fallback to report summary
            elif frontend_context.get('report_summary'):
                for item in frontend_context['report_summary'][:20]:  # Limit to 20 sections
                    section_id = item.get('section', 'unknown')
                    title = item.get('title', 'Untitled')
                    preview = item.get('preview', '')
                    context_parts.append(f"{title} ({section_id}):\n{preview}\n")
            
            # Fallback to content preview
            elif frontend_context.get('content_preview'):
                for page in frontend_context['content_preview'][:15]:  # First 15 pages
                    if isinstance(page, dict):
                        section = page.get('section', 'unknown')
                        content = page.get('content', '')
                        if content:
                            context_parts.append(f"Section {section}:\n{content[:2000]}\n")
            
            if context_parts:
                report_context = '\n'.join(context_parts)
                if len(report_context) > 40000:
                    report_context = report_context[:40000] + "\n[... content truncated ...]"
                
                logger.info(f"✓ Using frontend-provided context: {len(report_context)} chars from {len(context_parts)} sections")
        
        # Fallback to HTML parsing if frontend context not available
        elif html_content:
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract key metrics and data from tables and sections
                context_parts = []
                
                # Try multiple ways to find sections
                def find_section(section_id):
                    """Try multiple ways to find a section."""
                    # Try data-section attribute
                    section = soup.find('section', {'data-section': section_id})
                    if section:
                        return section
                    # Try id attribute
                    section = soup.find('section', {'id': section_id})
                    if section:
                        return section
                    # Try div with id
                    section = soup.find('div', {'id': section_id})
                    if section:
                        return section
                    # Try case-insensitive search
                    section = soup.find('section', {'data-section': lambda x: x and x.lower() == section_id.lower()})
                    if section:
                        return section
                    return None
                
                def find_section_by_title(title_keywords):
                    """Find section by title content."""
                    for section in soup.find_all('section'):
                        h1 = section.find('h1')
                        if h1 and any(keyword.lower() in h1.get_text().lower() for keyword in title_keywords):
                            return section
                    return None
                
                # Extract KAV metrics - try multiple approaches
                kav_section = find_section('kav_analysis') or find_section_by_title(['KAV', 'KLAVIYO', 'REVENUE'])
                if kav_section:
                    kav_text = kav_section.get_text(separator='\n', strip=True)
                    
                    # Extract key KAV metrics from the section
                    kav_metrics = []
                    
                    # Look for stat values in kav-stat elements
                    kav_stats = kav_section.find_all('div', class_='kav-stat')
                    for stat in kav_stats:
                        value = stat.find('span', class_='stat-value')
                        label = stat.find('span', class_='stat-label')
                        percent = stat.find('span', class_='stat-percent')
                        if value and label:
                            metric_text = f"{label.get_text(strip=True)}: {value.get_text(strip=True)}"
                            if percent:
                                metric_text += f" ({percent.get_text(strip=True)})"
                            kav_metrics.append(metric_text)
                    
                    # Look for kav-amount (total revenue)
                    kav_amount = kav_section.find('span', class_='kav-amount')
                    if kav_amount:
                        kav_metrics.append(f"Total Revenue: {kav_amount.get_text(strip=True)}")
                    
                    # Extract key numbers from tables if present
                    kav_tables = kav_section.find_all('table')
                    for table in kav_tables:
                        rows = table.find_all('tr')
                        for row in rows:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 2:
                                label = cells[0].get_text(strip=True)
                                value = cells[1].get_text(strip=True)
                                if label and value and not label.startswith('Month'):
                                    kav_metrics.append(f"{label}: {value}")
                    
                    if kav_metrics:
                        context_parts.append("KAV (Klaviyo Attributed Value) Metrics:\n" + "\n".join(kav_metrics[:15]) + "\n")
                    if kav_text:
                        context_parts.append(f"KAV Analysis Summary:\n{kav_text[:3000]}\n")
                    logger.info(f"✓ Extracted KAV section: {len(kav_text)} chars, {len(kav_metrics)} metrics")
                else:
                    logger.warning("KAV section not found in HTML")
                
                # Extract Executive Summary
                exec_section = find_section('executive_summary')
                if exec_section:
                    exec_text = exec_section.get_text(separator='\n', strip=True)
                    if exec_text:
                        context_parts.append(f"Executive Summary:\n{exec_text[:2000]}\n")
                        logger.info(f"✓ Extracted Executive Summary: {len(exec_text)} chars")
                else:
                    logger.warning("Executive Summary section not found")
                
                # Extract Strategic Recommendations
                strategic_section = find_section('strategic_recommendations')
                if strategic_section:
                    strategic_text = strategic_section.get_text(separator='\n', strip=True)
                    if strategic_text:
                        context_parts.append(f"Strategic Recommendations:\n{strategic_text[:3000]}\n")
                        logger.info(f"✓ Extracted Strategic Recommendations: {len(strategic_text)} chars")
                else:
                    logger.warning("Strategic Recommendations section not found")
                
                # Extract flow performance data - try multiple patterns
                flow_patterns = ['welcome', 'abandoned', 'browse', 'post_purchase', 'post-purchase']
                for pattern in flow_patterns:
                    flow_section = soup.find('section', {'data-section': lambda x: x and pattern in x.lower()})
                    if not flow_section:
                        flow_section = soup.find('section', {'id': lambda x: x and pattern in x.lower()})
                    if flow_section:
                        flow_name = flow_section.get('data-section') or flow_section.get('id', 'Unknown Flow')
                        flow_tables = flow_section.find_all('table')
                        flow_metrics = []
                        for table in flow_tables:
                            rows = table.find_all('tr')
                            for row in rows:
                                cells = row.find_all(['td', 'th'])
                                if len(cells) >= 2:
                                    label = cells[0].get_text(strip=True)
                                    value = cells[1].get_text(strip=True)
                                    if label and value:
                                        flow_metrics.append(f"{label}: {value}")
                        if flow_metrics:
                            context_parts.append(f"{flow_name} Performance:\n" + "\n".join(flow_metrics[:10]) + "\n")
                
                # Extract campaign performance
                campaign_section = find_section('campaign_performance')
                if campaign_section:
                    campaign_text = campaign_section.get_text(separator='\n', strip=True)
                    if campaign_text:
                        context_parts.append(f"Campaign Performance:\n{campaign_text[:2000]}\n")
                
                # Extract list growth data
                list_section = find_section('list_growth')
                if list_section:
                    list_text = list_section.get_text(separator='\n', strip=True)
                    if list_text:
                        context_parts.append(f"List Growth:\n{list_text[:1500]}\n")
                
                # If we didn't find structured sections, extract all text content as fallback
                if not context_parts:
                    logger.warning("No structured sections found, extracting all text content")
                    all_text = soup.get_text(separator='\n', strip=True)
                    if all_text:
                        context_parts.append(f"Full Report Content:\n{all_text[:20000]}\n")
                
                # Combine all context - prioritize critical sections
                report_context = '\n'.join(context_parts)
                
                # Add real report metrics to context
                if report_metrics:
                    summary_lines = []
                    
                    # Add basic report info
                    if report_metrics['client_name']:
                        summary_lines.append(f"Client: {report_metrics['client_name']}")
                    if report_metrics['industry']:
                        summary_lines.append(f"Industry: {report_metrics['industry']}")
                    if report_metrics['analysis_period_days']:
                        summary_lines.append(f"Analysis Period: {report_metrics['analysis_period_days']} days")
                    
                    # Add revenue metrics if available
                    if report_metrics['total_revenue'] and report_metrics['attributed_revenue']:
                        summary_lines.append(f"Revenue Overview: {report_metrics['attributed_revenue']} attributed out of {report_metrics['total_revenue']} total")
                    
                    if summary_lines:
                        report_context = "REPORT OVERVIEW:\n" + "\n".join(summary_lines) + "\n\n" + report_context
                
                # Increase context limit for comprehensive analysis (100k chars)
                if len(report_context) > 100000:
                    # Prioritize: keep structured summary + first 50k + last 45k
                    lines = report_context.split('\n')
                    if len(lines) > 100:
                        middle_cut = len(lines) // 2
                        kept_lines = lines[:middle_cut//2] + ["[... middle content truncated for length ...]"] + lines[-middle_cut//2:]
                        report_context = '\n'.join(kept_lines)
                    else:
                        report_context = report_context[:100000] + "\n[... content truncated ...]"
                
                logger.info(f"✓ Extracted comprehensive report context: {len(report_context)} chars from {len(context_parts)} sections")
                
            except Exception as e:
                logger.error(f"Error extracting context from HTML: {e}", exc_info=True)
                # Fallback: use raw text
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')
                    report_context = soup.get_text(separator='\n', strip=True)[:20000]
                    logger.info(f"✓ Using fallback text extraction: {len(report_context)} chars")
                except:
                    report_context = "Report content available but could not be parsed. Please ask general questions about Klaviyo audits."
        else:
            report_context = "Report content not available. Please ask general questions about Klaviyo audits."
            logger.warning("No HTML content available for context extraction")
        
        # Log context summary for debugging
        context_summary = f"Context length: {len(report_context)} chars"
        if report_context:
            context_preview = report_context[:200].replace('\n', ' ')
            context_summary += f", Preview: {context_preview}..."
        logger.info(f"Report context for chat: {context_summary}")
        
        # Build system context from frontend if provided
        system_prompt = ""
        if message.system_context:
            role = message.system_context.get('role', 'expert email marketing consultant')
            capabilities = message.system_context.get('capabilities', [])
            guidelines = message.system_context.get('guidelines', [])
            
            system_prompt = f"{role}\n\n"
            if capabilities:
                system_prompt += "Capabilities:\n" + "\n".join([f"- {cap}" for cap in capabilities]) + "\n\n"
            if guidelines:
                system_prompt += "Guidelines:\n" + "\n".join([f"- {guideline}" for guideline in guidelines]) + "\n\n"
        else:
            system_prompt = f"""You are an intelligent Klaviyo email marketing consultant assistant that can both ANALYZE and MODIFY audit reports for {report.client_name}.

CORE CAPABILITIES:
1. **Analysis**: Deep dive into email marketing performance data
2. **Actions**: Suggest specific improvements and edits to the report
3. **Content Generation**: Create new sections or regenerate existing ones with better insights
4. **Real-time Editing**: Modify report content based on user requests

IMPORTANT CONTEXT: This is about EMAIL MARKETING performance analysis, NOT chat support. You have access to:
- Complete audit report content and structured data
- Ability to regenerate sections with improved analysis
- Power to edit and enhance existing content
- Capability to add new insights and recommendations

KEY DEFINITIONS:
- KAV (Klaviyo Attributed Value) = Email marketing revenue attribution (Good: 25-30%, Average: 15-25%)
- You can suggest ACTIONS to improve low-performing areas
- You can REGENERATE sections with deeper insights
- You can EDIT content to be more actionable and specific

AVAILABLE ACTIONS:
- "regenerate_section": Recreate a section with better analysis
- "edit_content": Modify existing content for clarity/impact  
- "add_recommendations": Insert specific improvement strategies
- "analyze_deeper": Provide more detailed analysis of specific metrics
- "create_action_plan": Generate step-by-step improvement plans

When the user asks about performance issues, don't just explain - SUGGEST ACTIONS to fix them."""
        
        # Build available sections list (prefer frontend-provided)
        available_sections_text = ""
        if frontend_sections:
            available_sections_text = "\n".join([f"- {sec}" for sec in frontend_sections[:30]])
        elif section_list:
            available_sections_text = "\n".join(section_list)
        else:
            available_sections_text = "No sections identified"
        
        prompt = f"""{system_prompt}

AUDIT REPORT CONTEXT:
{report_context if report_context else "No report context available. The user is asking about a Klaviyo audit report, but the report content could not be loaded. Please provide general guidance about Klaviyo audits."}

AVAILABLE SECTIONS IN REPORT:
{available_sections_text}

CHAT HISTORY (last 10 messages):
{chr(10).join([f"{msg.get('role', 'unknown')}: {msg.get('content', msg.get('message', ''))}" for msg in formatted_history[-10:]])}

CURRENT USER MESSAGE:
{sanitized_message}

{"SECTION CONTEXT (user clicked on this section):" if section_context else ""}
{section_context if section_context else ""}

INSTRUCTIONS:
You are an intelligent assistant. Analyze the ACTUAL report data above and:

1. **Extract real metrics** - Find the actual KAV %, revenue numbers, open rates, etc. from the context
2. **Intelligent analysis** - Compare real performance to industry standards and identify gaps  
3. **Actionable insights** - Suggest specific improvements based on what the data reveals
4. **Dynamic responses** - Don't use templates, respond based on what you actually find
5. **Offer to help** - Suggest regenerating sections, adding analysis, or improving content when relevant
6. **Navigate smartly** - Reference specific sections when it makes sense for the conversation

If the user wants to improve something, offer to:
- Regenerate sections with deeper analysis
- Add specific recommendations  
- Edit content for better clarity/impact
- Create action plans with timelines

IMPORTANT: You MUST respond with valid JSON only. Do not include any text before or after the JSON object.

RESPOND IN THIS EXACT JSON FORMAT (no markdown, no code blocks, just raw JSON):
{{
    "response": "Your intelligent analysis with specific insights from the actual data",
    "suggested_actions": [
        {{
            "action_type": "regenerate_section|edit_content|add_recommendations|analyze_deeper",
            "target_section": "section_name_from_actual_data",
            "description": "What this will accomplish for this client",
            "confidence": 0.8
        }}
    ],
    "section_references": ["relevant_sections_you_found"],
    "navigation_actions": [{{"action": "scroll_to", "section_id": "section_from_context"}}]
}}

BE INTELLIGENT: 
- Extract ACTUAL metrics from the report context above (don't use placeholder numbers)
- Analyze what those real numbers mean compared to industry benchmarks  
- Suggest specific, actionable improvements based on what you find
- If you can't find specific data, say so - don't make up numbers"""
        
        # Call LLM
        llm_response = await llm_service.generate_insights(
            section="chat",
            data={"prompt": prompt},
            context={}
        )
        
        # Parse response (should be JSON)
        try:
            response_text = ""
            suggested_actions = []
            suggested_edits = []
            section_references = []
            navigation_actions = []
            
            if isinstance(llm_response, str):
                raw_response = llm_response.strip()
                
                # Try to extract JSON from response
                if raw_response.startswith('{'):
                    # Clean up common issues
                    cleaned = raw_response
                    # Remove markdown code blocks if present
                    if '```json' in cleaned:
                        cleaned = cleaned.split('```json')[1].split('```')[0].strip()
                    elif '```' in cleaned:
                        cleaned = cleaned.split('```')[1].split('```')[0].strip()
                    
                    try:
                        parsed = json.loads(cleaned)
                        response_text = parsed.get("response", "")
                        suggested_actions = parsed.get("suggested_actions", [])
                        suggested_edits = parsed.get("suggested_edits", [])
                        section_references = parsed.get("section_references", [])
                        navigation_actions = parsed.get("navigation_actions", [])
                    except json.JSONDecodeError:
                        # Try to extract just the response field
                        import re
                        response_match = re.search(r'"response"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', cleaned, re.DOTALL)
                        if response_match:
                            response_text = response_match.group(1).replace('\\"', '"').replace('\\n', '\n')
                        else:
                            response_text = raw_response
                else:
                    # Check for Python dict-like syntax: ['primary': '...', 'secondary': '...']
                    if "'primary':" in raw_response or "primary:" in raw_response:
                        # Extract text between quotes after 'primary':
                        import re
                        primary_match = re.search(r"['\"]?primary['\"]?\s*:\s*['\"](.+?)['\"](?:,\s*['\"]?secondary|$)", raw_response, re.DOTALL)
                        secondary_match = re.search(r"['\"]?secondary['\"]?\s*:\s*['\"](.+?)['\"](?:}|\]|$)", raw_response, re.DOTALL)
                        
                        parts = []
                        if primary_match:
                            parts.append(primary_match.group(1).strip())
                        if secondary_match:
                            parts.append(secondary_match.group(1).strip())
                        
                        if parts:
                            response_text = '\n\n'.join(parts)
                        else:
                            response_text = raw_response
                    else:
                        # Just use the raw response as text
                        response_text = raw_response
            else:
                # llm_response is already a dict
                parsed = llm_response if isinstance(llm_response, dict) else {"response": str(llm_response)}
                response_text = parsed.get("response", str(llm_response))
                suggested_actions = parsed.get("suggested_actions", [])
                suggested_edits = parsed.get("suggested_edits", [])
                section_references = parsed.get("section_references", [])
                navigation_actions = parsed.get("navigation_actions", [])
            
            # Final cleanup - remove any remaining JSON artifacts
            if response_text:
                response_text = response_text.strip()
                # Remove leading/trailing quotes or brackets
                if response_text.startswith('"') and response_text.endswith('"'):
                    response_text = response_text[1:-1]
                # Clean up escaped characters
                response_text = response_text.replace('\\n', '\n').replace('\\"', '"')
                
        except Exception as parse_error:
            logger.warning(f"Error parsing LLM response: {parse_error}")
            # Fallback: treat entire response as text
            response_text = str(llm_response) if llm_response else "I'm sorry, I couldn't generate a proper response."
            suggested_actions = []
            suggested_edits = []
            section_references = []
            navigation_actions = []
        
        # Save chat messages to database (store original message, but use sanitized for LLM)
        user_msg = ChatMessageModel(
            report_id=report_id,
            role="user",
            message=message.message,  # Store original for display
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
            suggested_actions=[ChatAction(**action) for action in suggested_actions] if suggested_actions else None,
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
    """
    Save edited report content.
    
    NOTE: This saves the edited HTML, but the original HTML is preserved in the file.
    The viewer should always load from the original file to get styles and semantic IDs.
    """
    try:
        from ..models.report import Report
        report = db.query(Report).filter(Report.id == report_id).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Save edited HTML to a separate field or file
        # For now, we'll save it but the status endpoint will prefer the original file
        # TODO: Consider adding an edited_html_content column or separate edited file
        
        # Check if this is processed HTML (missing styles) - if so, don't overwrite original
        is_processed = '<style>' not in save_request.html_content or 'data-section-id="section-' in save_request.html_content
        
        if is_processed:
            logger.warning(f"Attempted to save processed HTML for report {report_id} - preserving original")
            # Don't overwrite - the original HTML should be in the file
            return {
                "success": True,
                "message": "Edits saved (original HTML preserved in file)",
                "note": "The original HTML with styles is preserved. Edits are tracked separately."
            }
        
        # Only save if it looks like original HTML
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
        
        # Update outdated Claude models to current version
        claude_model = llm_config.get("claude_model")
        if claude_model and "claude-3-" in claude_model:
            logger.warning(f"Updating outdated Claude model {claude_model} to current version")
            claude_model = "claude-sonnet-4-20250514"  # Use current default
        
        llm_service = LLMService(
            default_provider=llm_config.get("provider", "claude"),
            anthropic_api_key=llm_config.get("anthropic_api_key"),
            openai_api_key=llm_config.get("openai_api_key"),
            gemini_api_key=llm_config.get("gemini_api_key"),
            claude_model=claude_model,
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

