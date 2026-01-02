"""
List growth data preparer.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
from ..chart_generator import get_chart_generator

logger = logging.getLogger(__name__)


def correlate_list_to_revenue(
    list_data: Dict[str, Any],
    revenue_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Strategist approach:
    - "52.9% increase in campaign recipients = revenue increase"
    - Connect list growth to revenue opportunity
    
    Args:
        list_data: List growth data dictionary
        revenue_data: Optional revenue data dictionary (from KAV or campaign data)
    
    Returns:
        Dict with connection, revenue_impact, and opportunity
    """
    correlation = {
        "connection": "",
        "revenue_impact": "",
        "opportunity": ""
    }
    
    # Calculate list growth percentage
    current_total = list_data.get("current_total", 0)
    net_change = list_data.get("net_change", 0)
    period_months = list_data.get("period_months", 6)
    
    # Calculate growth percentage (approximate based on net change)
    # If we have previous period data, use it; otherwise estimate
    previous_total = current_total - net_change if current_total > 0 else 0
    list_growth_pct = 0
    if previous_total > 0:
        list_growth_pct = (net_change / previous_total) * 100
    
    # Get revenue growth from revenue_data if available
    revenue_growth_pct = 0
    if revenue_data:
        # Try different possible fields for revenue growth
        revenue_growth_pct = revenue_data.get("revenue_growth", 0) or \
                           revenue_data.get("vs_previous_period", 0) or \
                           revenue_data.get("attributed_vs_previous", 0)
    
    if list_growth_pct > 0 and revenue_growth_pct > 0:
        correlation["connection"] = f"{list_growth_pct:.1f}% list growth correlates with revenue performance"
        correlation["revenue_impact"] = "Data capture investment has direct revenue implications"
        correlation["opportunity"] = "Further list growth optimization could drive additional revenue"
    elif list_growth_pct > 0 and revenue_growth_pct <= 0:
        correlation["connection"] = f"{list_growth_pct:.1f}% list growth not yet translating to revenue"
        correlation["revenue_impact"] = "Focus on engagement and conversion of new subscribers"
        correlation["opportunity"] = "Improve welcome series and onboarding to convert new subscribers"
    elif list_growth_pct <= 0:
        correlation["connection"] = "List growth is stagnant or declining"
        correlation["revenue_impact"] = "Stagnant list growth limits revenue potential"
        correlation["opportunity"] = "Prioritize data capture optimization to grow subscriber base"
    else:
        correlation["connection"] = "List growth data available, revenue correlation analysis pending"
        correlation["revenue_impact"] = "Monitor list growth impact on revenue over time"
        correlation["opportunity"] = "Optimize data capture to maximize list growth"
    
    return correlation


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
    
    # Step 1: Correlate list growth to revenue (before LLM call)
    # Get revenue data from account_context if available (passed from orchestrator)
    revenue_data = account_context.get("revenue_data", {}) if account_context else {}
    list_correlation = correlate_list_to_revenue(
        list_data=list_raw,
        revenue_data=revenue_data
    )
    
    logger.info(
        f"List-revenue correlation: {list_correlation.get('connection')} - "
        f"{list_correlation.get('opportunity')}"
    )
    
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
        
        # Add list-revenue correlation to context for LLM
        if "context" not in formatted_data:
            formatted_data["context"] = {}
        formatted_data["context"]["list_correlation"] = list_correlation
        
        # Generate insights using LLM
        strategic_insights = await llm_service.generate_insights(
            section="list_growth",
            data=formatted_data,
            context=formatted_data.get("context", {})
        )
        
        # Extract comprehensive subsections (new enhanced format)
        from ..html_formatter import format_llm_output
        
        list_growth_overview = strategic_insights.get("list_growth_overview", "")
        growth_drivers = strategic_insights.get("growth_drivers", "")
        attrition_sources = strategic_insights.get("attrition_sources", "")
        
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
                # Use format_llm_output for consistent formatting
                analysis_text = format_llm_output(primary_str) if primary_str else ""
        else:
            # Convert to string and format
            analysis_text = format_llm_output(str(primary_raw)) if primary_raw else ""
        
        # Format all subsections
        list_growth_overview = format_llm_output(list_growth_overview) if list_growth_overview else ""
        growth_drivers = format_llm_output(growth_drivers) if growth_drivers else ""
        attrition_sources = format_llm_output(attrition_sources) if attrition_sources else ""
        
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
        
        list_growth_overview = ""
        growth_drivers = ""
        attrition_sources = ""
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
        # Comprehensive subsections (new enhanced format)
        "list_growth_overview": list_growth_overview if 'list_growth_overview' in locals() else "",
        "growth_drivers": growth_drivers if 'growth_drivers' in locals() else "",
        "attrition_sources": attrition_sources if 'attrition_sources' in locals() else "",
        "recommendations": recommendations if isinstance(recommendations, list) else [],
        "areas_of_opportunity": areas_of_opportunity if isinstance(areas_of_opportunity, list) else [],
        "root_cause_analysis": root_cause_analysis,  # LLM-generated root cause analysis
        "risk_flags": risk_flags,  # LLM-generated risk flags
        "quick_wins": quick_wins,  # LLM-generated quick wins
        "list_correlation": list_correlation  # List-revenue correlation analysis
    }

