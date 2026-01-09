"""
Quote generation handler.
"""
import logging
import json
import os
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.report import Report
from ...models.chat import ChatMessage as ChatMessageModel
from ...services.llm import LLMService

logger = logging.getLogger(__name__)


async def handle_generate_quote(
    report_id: int,
    quote_request: Any,
    db: Session
) -> Dict[str, Any]:
    """Generate a sales quote based on audit findings."""
    # Extract priorities and custom_message from quote_request
    priorities = getattr(quote_request, 'priorities', None) if hasattr(quote_request, 'priorities') else None
    custom_message = getattr(quote_request, 'custom_message', None) if hasattr(quote_request, 'custom_message') else None
    
    report = db.query(Report).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Get chat history for context
    chat_history = db.query(ChatMessageModel).filter(
        ChatMessageModel.report_id == report_id
    ).order_by(ChatMessageModel.created_at.desc()).limit(10).all()
    
    # Initialize LLM service (use report's LLM config if available)
    llm_config = {}
    if hasattr(report, 'llm_config') and report.llm_config:
        if isinstance(report.llm_config, str):
            try:
                llm_config = json.loads(report.llm_config)
            except (json.JSONDecodeError, TypeError):
                llm_config = {}
        else:
            llm_config = report.llm_config or {}
    
    # Fallback to environment variables
    provider = llm_config.get("provider", "claude")
    
    if provider == "claude" and not llm_config.get("anthropic_api_key"):
        llm_config["anthropic_api_key"] = os.getenv("ANTHROPIC_API_KEY")
    elif provider == "openai" and not llm_config.get("openai_api_key"):
        llm_config["openai_api_key"] = os.getenv("OPENAI_API_KEY")
    elif provider == "gemini" and not llm_config.get("gemini_api_key"):
        llm_config["gemini_api_key"] = os.getenv("GOOGLE_API_KEY")
    
    if not llm_config.get("provider"):
        llm_config["provider"] = "claude"
    
    # Validate API key
    if provider == "claude" and not llm_config.get("anthropic_api_key"):
        raise HTTPException(status_code=400, detail="Anthropic API key not found.")
    elif provider == "openai" and not llm_config.get("openai_api_key"):
        raise HTTPException(status_code=400, detail="OpenAI API key not found.")
    elif provider == "gemini" and not llm_config.get("gemini_api_key"):
        raise HTTPException(status_code=400, detail="Gemini API key not found.")
    
    # Update outdated Claude models
    claude_model = llm_config.get("claude_model")
    if claude_model and "claude-3-" in claude_model:
        claude_model = "claude-sonnet-4-20250514"
    
    llm_service = LLMService(
        default_provider=llm_config.get("provider", "claude"),
        anthropic_api_key=llm_config.get("anthropic_api_key"),
        openai_api_key=llm_config.get("openai_api_key"),
        gemini_api_key=llm_config.get("gemini_api_key"),
        claude_model=claude_model,
        openai_model=llm_config.get("openai_model"),
        gemini_model=llm_config.get("gemini_model")
    )
    
    # Extract key metrics and opportunities from report HTML (like old implementation)
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
            recommendations = strategic_section.find_all(['div', 'li'], class_=lambda x: x and ('recommendation' in x.lower() or 'opportunity' in x.lower()))
            for rec in recommendations[:10]:
                rec_text = rec.get_text(strip=True)
                if rec_text and len(rec_text) > 20:
                    opportunities.append(rec_text)
        
        # Extract areas of opportunity from tables
        opp_tables = soup.find_all('table', class_=lambda x: x and 'opportunity' in str(x).lower())
        for table in opp_tables:
            rows = table.find_all('tr')[1:]  # Skip header
            for row in rows[:5]:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    opp_name = cells[0].get_text(strip=True)
                    opp_value = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                    if opp_name:
                        opportunities.append(f"{opp_name}: {opp_value}")
    
    # Build quote generation prompt
    priorities_text = ""
    if priorities:
        priorities_text = "\n".join([f"- {p}" for p in priorities])
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
{custom_message or "Create a comprehensive quote covering the main opportunities identified in the audit."}

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

    try:
        quote_response = await llm_service.generate_insights(
            section="quote",
            data={"prompt": prompt},
            context={}
        )
        
        # Parse response (similar to old implementation)
        import json
        try:
            if isinstance(quote_response, str):
                if quote_response.strip().startswith('{'):
                    quote_data = json.loads(quote_response)
                else:
                    # Fallback: wrap in basic structure
                    quote_data = {
                        "quote_title": f"Klaviyo Optimization Services for {report.client_name}",
                        "executive_summary": quote_response,
                        "services": [],
                        "total_investment": "Contact for pricing",
                        "next_steps": ["Schedule a call to discuss", "Review audit findings", "Customize proposal"]
                    }
            else:
                quote_data = quote_response
        except json.JSONDecodeError:
            quote_data = {
                "quote_title": f"Klaviyo Optimization Services for {report.client_name}",
                "executive_summary": str(quote_response),
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

