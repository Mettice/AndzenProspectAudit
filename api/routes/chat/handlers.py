"""
Chat handlers - main business logic for chat endpoints.
"""
import logging
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session

from ...database import get_db
from ...utils.security import sanitize_prompt_input
from ...services.llm import LLMService
from ...models.report import Report
from ...models.chat import ChatMessage as ChatMessageModel
from .models import ChatMessage, ChatResponse, ChatAction
from .context_builder import extract_frontend_context, build_context_from_frontend, build_context_from_html
from .prompt_builder import build_system_prompt, build_chat_prompt
from .response_parser import parse_llm_response

logger = logging.getLogger(__name__)


def load_html_content(report: Report) -> str:
    """Load HTML content from report, trying multiple locations."""
    html_content = report.html_content or ""
    
    if not html_content and report.file_path_html:
        try:
            # Try the direct file path first
            if os.path.exists(report.file_path_html):
                logger.info(f"Loading HTML from direct path: {report.file_path_html}")
                with open(report.file_path_html, "r", encoding="utf-8") as f:
                    html_content = f.read()
                logger.info(f"✓ Loaded HTML from direct path: {len(html_content)} chars")
            else:
                # Try the relative path from API folder
                reports_dir = Path(__file__).parent.parent.parent.parent / "api" / "data" / "reports"
                html_filename = Path(report.file_path_html).name
                html_file_path = reports_dir / html_filename
                logger.info(f"Attempting to load HTML from API path: {html_file_path}")
                
                if html_file_path.exists():
                    with open(html_file_path, "r", encoding="utf-8") as f:
                        html_content = f.read()
                    logger.info(f"✓ Loaded HTML from API path: {len(html_content)} chars")
                else:
                    # Try root data/reports path
                    reports_dir = Path(__file__).parent.parent.parent.parent / "data" / "reports"
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
    
    return html_content


def get_section_context(message: ChatMessage, html_content: str) -> Optional[str]:
    """Extract section context if user clicked on a specific section."""
    if not message.section_id or not html_content:
        return None
    
    import re
    section_match = re.search(
        f'<section[^>]*data-section="{message.section_id}"[^>]*>(.*?)</section>',
        html_content,
        re.DOTALL
    )
    if section_match:
        return section_match.group(1)[:2000]  # Limit context
    return None


def get_chat_history(report_id: int, db: Session) -> list[Dict[str, Any]]:
    """Get and format chat history for LLM."""
    chat_history = db.query(ChatMessageModel).filter(
        ChatMessageModel.report_id == report_id
    ).order_by(ChatMessageModel.created_at.asc()).all()
    
    formatted_history = []
    for msg in chat_history:
        content = msg.message
        if msg.role == "user":
            content = sanitize_prompt_input(content, max_length=2000)
        formatted_history.append({
            "role": msg.role,
            "content": content
        })
    
    return formatted_history


def get_section_list(html_content: str) -> list[str]:
    """Extract section list from HTML for navigation."""
    if not html_content:
        return []
    
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        sections = soup.find_all(['section', 'div'], {'data-section': True}) or \
                  soup.find_all('section', {'id': True})
        
        section_list = []
        for sec in sections[:20]:  # Limit to first 20 sections
            section_id = sec.get('data-section') or sec.get('id')
            section_title = sec.find(['h1', 'h2', 'h3', 'h4'])
            if section_title:
                section_list.append(f"- {section_id}: {section_title.get_text().strip()[:50]}")
        return section_list
    except Exception as e:
        logger.error(f"Error extracting section list: {e}")
        return []


def initialize_llm_service(report: Report) -> LLMService:
    """Initialize LLM service with report's configuration."""
    llm_config = {}
    if hasattr(report, 'llm_config') and report.llm_config:
        # If llm_config is stored as JSON string (SQLite), parse it
        if isinstance(report.llm_config, str):
            try:
                llm_config = json.loads(report.llm_config)
            except (json.JSONDecodeError, TypeError):
                llm_config = {}
        else:
            llm_config = report.llm_config or {}
    
    # Log what we're using
    logger.info(f"Chat LLM config: provider={llm_config.get('provider')}, has_anthropic_key={bool(llm_config.get('anthropic_api_key'))}, has_openai_key={bool(llm_config.get('openai_api_key'))}, has_gemini_key={bool(llm_config.get('gemini_api_key'))}")
    
    # Fallback to environment variables if no config or missing API key
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
    
    return LLMService(
        default_provider=llm_config.get("provider", "claude"),
        anthropic_api_key=llm_config.get("anthropic_api_key"),
        openai_api_key=llm_config.get("openai_api_key"),
        gemini_api_key=llm_config.get("gemini_api_key"),
        claude_model=claude_model,
        openai_model=llm_config.get("openai_model"),
        gemini_model=llm_config.get("gemini_model")
    )


async def handle_chat_message(
    report_id: int,
    message: ChatMessage,
    db: Session
) -> ChatResponse:
    """Handle a chat message - main handler function."""
    # Debug: Log the incoming message structure
    print(f"\n{'='*80}")
    print(f"🔵 CHAT REQUEST RECEIVED - report_id: {report_id}")
    print(f"{'='*80}")
    logger.info(f"Chat request received - report_id: {report_id}, message type: {type(message)}")
    if hasattr(message, 'dict'):
        msg_dict = message.dict()
        print(f"📦 Message dict keys: {list(msg_dict.keys())}")
        print(f"📦 Has full_context: {bool(msg_dict.get('full_context'))}")
        print(f"📦 Has available_sections: {bool(msg_dict.get('available_sections'))}")
        print(f"📦 Has system_context: {bool(msg_dict.get('system_context'))}")
        logger.info(f"Message dict keys: {list(msg_dict.keys())}")
        logger.info(f"Has full_context: {bool(msg_dict.get('full_context'))}")
        logger.info(f"Has available_sections: {bool(msg_dict.get('available_sections'))}")
        logger.info(f"Has system_context: {bool(msg_dict.get('system_context'))}")
        
        # Check full_context structure
        if msg_dict.get('full_context'):
            fc = msg_dict['full_context']
            print(f"📦 full_context type: {type(fc)}")
            print(f"📦 full_context keys: {list(fc.keys()) if isinstance(fc, dict) else 'not a dict'}")
            if isinstance(fc, dict) and fc.get('full_content'):
                print(f"📦 full_content pages: {len(fc.get('full_content', []))}")
                # Check if KAV is in any page
                for i, page in enumerate(fc.get('full_content', [])[:5]):
                    if isinstance(page, dict):
                        section_id = page.get('sectionId', page.get('section', 'unknown'))
                        if 'kav' in section_id.lower():
                            print(f"📦 ✓ Found KAV in page {i}: {section_id}")
    
    # Get report from database
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Sanitize user message
    sanitized_message = sanitize_prompt_input(message.message, max_length=2000)
    logger.info(f"Chat message sanitized: original_length={len(message.message)}, sanitized_length={len(sanitized_message)}")
    
    # Get chat history
    formatted_history = get_chat_history(report_id, db)
    
    # Get HTML content
    html_content = load_html_content(report)
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
    
    if not html_content:
        logger.warning(f"No HTML content available for report {report_id}. Chat will have limited context.")
    
    # Get section context if provided
    section_context = get_section_context(message, html_content)
    
    # Extract frontend context
    print(f"🔍 Extracting frontend context from message...")
    logger.info(f"🔍 Extracting frontend context from message...")
    frontend_context, frontend_sections, frontend_system_context = extract_frontend_context(message)
    print(f"🔍 Frontend context extracted: has_context={bool(frontend_context)}, has_sections={bool(frontend_sections)}, has_system={bool(frontend_system_context)}")
    logger.info(f"🔍 Frontend context extracted: has_context={bool(frontend_context)}, has_sections={bool(frontend_sections)}, has_system={bool(frontend_system_context)}")
    
    # Build report context (prefer frontend, fallback to HTML)
    report_context = ""
    if frontend_context:
        print(f"🔍 Building context from frontend...")
        logger.info(f"🔍 Building context from frontend...")
        report_context = build_context_from_frontend(frontend_context)
        print(f"🔍 Context built: {len(report_context)} chars")
        logger.info(f"🔍 Context built: {len(report_context)} chars")
    elif html_content:
        report_context = build_context_from_html(html_content, report_metrics)
    else:
        report_context = "Report content not available. Please ask general questions about Klaviyo audits."
        logger.warning("No HTML content available for context extraction")
    
    # Log context summary
    context_summary = f"Context length: {len(report_context)} chars"
    if report_context:
        context_preview = report_context[:200].replace('\n', ' ')
        context_summary += f", Preview: {context_preview}..."
    logger.info(f"Report context for chat: {context_summary}")
    
    # Build system prompt
    system_prompt = build_system_prompt(frontend_system_context, report.client_name)
    
    # Get section list for navigation
    section_list = get_section_list(html_content)
    available_sections = frontend_sections or [s.split(':')[0].strip('- ') for s in section_list]
    
    # Build chat prompt
    prompt = build_chat_prompt(
        system_prompt=system_prompt,
        report_context=report_context,
        available_sections=available_sections,
        chat_history=formatted_history,
        user_message=sanitized_message,
        section_context=section_context
    )
    
    # Log prompt for debugging
    print(f"\n{'='*80}")
    print(f"📤 Sending prompt to LLM: {len(prompt)} chars, context: {len(report_context)} chars")
    logger.info(f"📤 Sending prompt to LLM: {len(prompt)} chars, context: {len(report_context)} chars")
    
    # Generic check: Verify that context contains relevant information for the user's question
    user_message_lower = sanitized_message.lower()
    context_lower = report_context.lower()
    
    # Extract key terms from user message (section names, metrics, etc.)
    important_topics = ['kav', 'executive', 'summary', 'growth', 'campaign', 'flow', 'automation', 'recommendation', 'segmentation', 'data capture', 'list']
    found_topics = []
    missing_topics = []
    
    for topic in important_topics:
        if topic in user_message_lower:
            if topic in context_lower:
                found_topics.append(topic)
                print(f"✅ '{topic.upper()}' content found in context")
                logger.info(f"✅ '{topic.upper()}' content found in context")
            else:
                missing_topics.append(topic)
                print(f"⚠️ '{topic.upper()}' mentioned in question but NOT found in context")
                logger.warning(f"⚠️ '{topic.upper()}' mentioned in question but NOT found in context")
    
    if found_topics:
        print(f"📊 Context contains relevant data for: {', '.join(found_topics)}")
        logger.info(f"📊 Context contains relevant data for: {', '.join(found_topics)}")
    if missing_topics:
        print(f"⚠️ Context missing data for: {', '.join(missing_topics)} - LLM may give generic answer")
        logger.warning(f"⚠️ Context missing data for: {', '.join(missing_topics)} - LLM may give generic answer")
    print(f"{'='*80}\n")
    # Check if user asked about specific topic
    user_message_lower = sanitized_message.lower()
    important_topics = ['kav', 'executive', 'summary', 'growth', 'campaign', 'flow', 'automation', 'recommendation']
    for topic in important_topics:
        if topic in user_message_lower:
            if topic in report_context.lower():
                logger.info(f"✅ {topic.upper()} content IS in context - LLM should be able to answer")
                # For KAV specifically, log more details
                if topic == 'kav':
                    kav_pos = report_context.lower().find('kav')
                    if kav_pos >= 0:
                        kav_snippet = report_context[max(0, kav_pos-50):min(len(report_context), kav_pos+200)]
                        logger.info(f"✅ KAV snippet in context: ...{kav_snippet}...")
            else:
                logger.warning(f"❌ {topic.upper()} content NOT in context - LLM may give generic answer")
            break
    
    # Special check for KAV - warn if LLM might confuse it with chat
    if 'kav' in user_message_lower:
        logger.info(f"🔍 User asked about KAV - ensuring LLM understands this is REVENUE, not chat widget")
        if 'kav' not in report_context.lower():
            logger.error(f"❌ CRITICAL: KAV content NOT found in context! LLM will give generic/wrong answer")
    
    # Initialize LLM service
    llm_service = initialize_llm_service(report)
    
    # Call LLM - use the prompt directly instead of template
    print(f"📞 Calling LLM service with custom prompt...")
    # Bypass the template system and call the LLM directly with our custom prompt
    provider = llm_service.default_provider
    client = llm_service._get_client(provider) if hasattr(llm_service, '_get_client') else None
    
    if client:
        try:
            # Call the LLM directly with our prompt
            response = await client.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Try to parse as JSON first
            import json
            try:
                if content.strip().startswith('{'):
                    llm_response = json.loads(content)
                else:
                    # Not JSON, wrap in dict format
                    llm_response = {"response": content}
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                if '```json' in content:
                    json_part = content.split('```json')[1].split('```')[0].strip()
                    llm_response = json.loads(json_part)
                elif '```' in content:
                    json_part = content.split('```')[1].split('```')[0].strip()
                    try:
                        llm_response = json.loads(json_part)
                    except:
                        llm_response = {"response": content}
                else:
                    llm_response = {"response": content}
        except Exception as e:
            print(f"❌ Error calling LLM directly: {e}")
            logger.error(f"Error calling LLM directly: {e}", exc_info=True)
            # Fallback to template system
            llm_response = await llm_service.generate_insights(
                section="chat",
                data={"prompt": prompt},
                context={}
            )
    else:
        # Fallback to template system
        llm_response = await llm_service.generate_insights(
            section="chat",
            data={"prompt": prompt},
            context={}
        )
    
    print(f"📥 Received LLM response: {type(llm_response)}, length: {len(str(llm_response)) if llm_response else 0}")
    logger.info(f"📥 Received LLM response: {type(llm_response)}, length: {len(str(llm_response)) if llm_response else 0}")
    
    # Log first 500 chars of response for debugging
    if llm_response:
        response_preview = str(llm_response)[:500]
        print(f"📥 Response preview: {response_preview}...")
        logger.info(f"📥 Response preview: {response_preview}...")
        
        # Generic check: Warn if response seems to be about wrong topic
        # This catches cases where LLM confuses terms (e.g., KAV vs chat, flow vs campaign)
        response_str_lower = str(llm_response).lower()
        # Check for common term confusions
        term_confusions = [
            ('kav', 'chat'),  # KAV (revenue) vs chat (widget)
            ('flow', 'campaign'),  # Flow (automation) vs campaign (one-time)
            ('segmentation', 'list'),  # Segmentation (targeting) vs list (subscribers)
        ]
        for correct_term, wrong_term in term_confusions:
            if correct_term in user_message_lower and wrong_term in response_str_lower and correct_term not in response_str_lower[:300]:
                print(f"⚠️ WARNING: User asked about '{correct_term}' but response mentions '{wrong_term}' - possible confusion!")
                logger.warning(f"⚠️ WARNING: User asked about '{correct_term}' but response mentions '{wrong_term}' - possible confusion!")
    
    # Parse response
    response_text, suggested_actions, suggested_edits, section_references, navigation_actions = parse_llm_response(llm_response)
    
    # Generic validation: Check if response actually uses the provided context
    # If the response is too generic or doesn't reference the context, it might be ignoring it
    response_lower = response_text.lower()
    context_lower = report_context.lower()
    
    # Extract key terms from user message (section names, metrics, etc.)
    import re
    # Find section names mentioned in user message
    user_sections = []
    if message.available_sections:
        for section in message.available_sections:
            if section.replace('_', ' ') in user_message_lower or section in user_message_lower:
                user_sections.append(section)
    
    # Check if response references the context
    context_used = False
    if user_sections:
        # Check if any mentioned section appears in the response
        for section in user_sections:
            section_keywords = section.replace('_', ' ').split()
            if any(keyword in response_lower for keyword in section_keywords if len(keyword) > 3):
                context_used = True
                break
    
    # Also check for common metrics/terms that should appear if context is used
    if not context_used and len(report_context) > 1000:
        # Look for numbers, percentages, or specific terms from context
        context_indicators = re.findall(r'\d+\.?\d*%|\$[\d,]+|klaviyo|attributed|revenue|growth|campaign|flow|automation', context_lower[:5000])
        response_indicators = re.findall(r'\d+\.?\d*%|\$[\d,]+|klaviyo|attributed|revenue|growth|campaign|flow|automation', response_lower)
        
        # If context has specific data but response doesn't, it's likely generic
        if len(context_indicators) > 5 and len(response_indicators) < 2:
            print(f"⚠️ Response appears generic - context has {len(context_indicators)} indicators but response has {len(response_indicators)}")
            logger.warning(f"Response may not be using context - context indicators: {len(context_indicators)}, response indicators: {len(response_indicators)}")
    
    # If response is clearly wrong (e.g., talks about "chat widget" when asked about report sections)
    # This is a generic check, not KAV-specific
    if len(report_context) > 5000 and len(response_text) > 100:
        # Check if response mentions generic terms that shouldn't be there
        generic_wrong_terms = ['chat widget', 'chatbot', 'live chat', 'customer service chat']
        user_mentions_sections = any(section in user_message_lower for section in ['kav', 'executive', 'summary', 'growth', 'campaign', 'flow', 'automation', 'recommendation'])
        
        if user_mentions_sections and any(term in response_lower for term in generic_wrong_terms):
            print(f"❌ Response contains wrong generic terms - likely not using context properly")
            logger.error(f"Response contains wrong generic terms: {[term for term in generic_wrong_terms if term in response_lower]}")
            # Don't override, but log the issue - the prompt improvements should prevent this
    
    # Save chat messages to database
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

