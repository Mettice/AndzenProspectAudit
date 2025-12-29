"""
List growth data preparer.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging

logger = logging.getLogger(__name__)


async def prepare_list_growth_data(
    list_raw: Dict[str, Any],
    client_name: str = "the client",
    account_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Prepare list growth data for template with LLM-generated insights."""
    if not list_raw:
        return {}
    
    # Calculate date range for display
    period_months = list_raw.get("period_months", 6)
    end_date = datetime.now()
    start_date = end_date - relativedelta(months=period_months)
    
    # Format date range for display (e.g., "Sep 2025 - Dec 2025")
    date_range_str = f"{start_date.strftime('%b %Y')} - {end_date.strftime('%b %Y')}"
    
    # Try to use LLM service for insights
    analysis_text = ""
    try:
        from ...llm import LLMService
        from ...llm.formatter import LLMDataFormatter
        
        # Initialize LLM service with config from account_context if available
        llm_config = account_context.get("llm_config", {}) if account_context else {}
        default_provider = llm_config.get("provider", "claude")
        llm_service = LLMService(
            default_provider=default_provider,
            anthropic_api_key=llm_config.get("anthropic_api_key"),
            openai_api_key=llm_config.get("openai_api_key"),
            gemini_api_key=llm_config.get("gemini_api_key"),
            claude_model=llm_config.get("claude_model"),
            openai_model=llm_config.get("openai_model"),
            gemini_model=llm_config.get("gemini_model"),
            llm_config=llm_config if llm_config else None
        )
        
        # Format data for LLM
        # Get industry from account_context
        industry = account_context.get("industry", "retail") if account_context else "retail"
        
        formatted_data = LLMDataFormatter.format_for_generic_analysis(
            section="list_growth",
            data=list_raw,
            client_context={
                "client_name": client_name,
                "industry": industry,
                "currency": account_context.get("currency", "USD") if account_context else "USD"
            }
        )
        
        # Generate insights using LLM
        strategic_insights = await llm_service.generate_insights(
            section="list_growth",
            data=formatted_data,
            context=formatted_data.get("context", {})
        )
        
        # Extract primary narrative - handle both string and dict formats
        primary_raw = strategic_insights.get("primary", "")
        if isinstance(primary_raw, str):
            primary_str = primary_raw.strip()
            # If it's a string that looks like JSON, try to parse it
            if primary_str.startswith('{') or (primary_str.startswith('[') or (primary_str.startswith('"') and '"primary"' in primary_str[:100])):
                # This shouldn't happen if JSON parsing worked, but handle it
                logger.warning("Primary narrative appears to be JSON string, JSON parsing may have failed")
                analysis_text = ""  # Don't display raw JSON
            else:
                # Format as HTML paragraphs (split on double newlines or single newlines)
                if primary_str:
                    # Try splitting on double newlines first, then single newlines
                    if '\n\n' in primary_str:
                        paragraphs = [p.strip() for p in primary_str.split('\n\n') if p.strip()]
                    else:
                        # Split on single newlines and group into paragraphs
                        lines = [l.strip() for l in primary_str.split('\n') if l.strip()]
                        paragraphs = []
                        current_para = []
                        for line in lines:
                            if line.endswith('.') or line.endswith('!') or line.endswith('?'):
                                current_para.append(line)
                                paragraphs.append(' '.join(current_para))
                                current_para = []
                            else:
                                current_para.append(line)
                        if current_para:
                            paragraphs.append(' '.join(current_para))
                    
                    if paragraphs:
                        analysis_text = '\n'.join([f'<p>{p}</p>' for p in paragraphs])
                    else:
                        analysis_text = f'<p>{primary_str}</p>'  # Single paragraph
                else:
                    analysis_text = ""
        else:
            # Convert to string and format
            analysis_text = f'<p>{str(primary_raw)}</p>' if primary_raw else ""
        
        recommendations = strategic_insights.get("recommendations", [])
        if not isinstance(recommendations, list):
            recommendations = []
        
        areas_of_opportunity = strategic_insights.get("areas_of_opportunity", [])
        if not isinstance(areas_of_opportunity, list):
            areas_of_opportunity = []
        
        # Extract enhanced strategic value elements
        root_cause_analysis = strategic_insights.get("root_cause_analysis", {})
        if not isinstance(root_cause_analysis, dict):
            root_cause_analysis = {}
        
        risk_flags = strategic_insights.get("risk_flags", [])
        if not isinstance(risk_flags, list):
            risk_flags = []
        
        quick_wins = strategic_insights.get("quick_wins", [])
        if not isinstance(quick_wins, list):
            quick_wins = []
        
    except Exception as e:
        # Fallback if LLM fails
        logger.warning(f"LLM service unavailable for list growth analysis, using fallback: {e}")
        # Try to get fallback from list_raw, or create a simple one
        fallback_text = list_raw.get("analysis_text", "")
        if not fallback_text:
            # Create a simple fallback based on data
            current_total = list_raw.get("current_total", 0)
            net_change = list_raw.get("net_change", 0)
            period_months = list_raw.get("period_months", 6)
            if current_total > 0:
                fallback_text = f"Email List Growth Overview: {client_name} has {current_total:,} total subscribers as of the analysis period. Over the last {period_months} months, the list has shown a net change of {net_change:+,} subscribers."
            else:
                fallback_text = f"Email List Growth Overview: Analysis of list growth data for {client_name} over the last {period_months} months."
        
        # Format fallback as HTML paragraphs
        if fallback_text:
            paragraphs = [p.strip() for p in fallback_text.split('\n\n') if p.strip()]
            if paragraphs:
                analysis_text = '\n'.join([f'<p>{p}</p>' for p in paragraphs])
            else:
                analysis_text = f'<p>{fallback_text}</p>'
        else:
            analysis_text = ""
        
        recommendations = []
        areas_of_opportunity = []
        root_cause_analysis = {}
        risk_flags = []
        quick_wins = []
    
    return {
        "list_name": list_raw.get("list_name", "Primary List"),
        "period_months": period_months,
        "date_range": date_range_str,  # Add date range for template
        "current_total": list_raw.get("current_total", 0),
        "net_change": list_raw.get("net_change", 0),
        "growth_subscribers": list_raw.get("growth_subscribers", 0),
        "lost_subscribers": list_raw.get("lost_subscribers", 0),
        "churn_rate": list_raw.get("churn_rate", 0),
        "signup_sources": list_raw.get("signup_sources", {
            "popup_form": 0,
            "footer_form": 0,
            "other": 0
        }),
        "chart_data": list_raw.get("chart_data", {}),
        "net_change_chart_data": list_raw.get("net_change_chart_data", {}),
        "analysis_text": analysis_text,  # LLM-generated analysis
        "recommendations": recommendations if isinstance(recommendations, list) else [],
        "areas_of_opportunity": areas_of_opportunity if isinstance(areas_of_opportunity, list) else [],
        "root_cause_analysis": root_cause_analysis,  # LLM-generated root cause analysis
        "risk_flags": risk_flags,  # LLM-generated risk flags
        "quick_wins": quick_wins  # LLM-generated quick wins
    }

