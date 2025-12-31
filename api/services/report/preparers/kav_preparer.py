"""
KAV data preparer.
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def interpret_kav_split(
    flow_percentage: float,
    campaign_percentage: float,
    kav_percentage: float,
    benchmarks: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Strategist approach:
    - Campaigns > Flows = Automation underinvestment
    - Flows > Campaigns = Healthy automation, potential campaign opportunity
    - KAV < 30% = Below benchmark, room to grow
    - KAV > 30% = Healthy, optimize to maintain
    
    Args:
        flow_percentage: Percentage of revenue from flows
        campaign_percentage: Percentage of revenue from campaigns
        kav_percentage: Total KAV percentage
        benchmarks: Optional benchmarks dictionary
    
    Returns:
        Dict with thesis, opportunity, priority, kav_status, and kav_opportunity
    """
    interpretation = {
        "thesis": "",
        "opportunity": "",
        "priority": ""
    }
    
    # Flow vs Campaign analysis
    if campaign_percentage > flow_percentage * 1.2:  # Campaigns 20%+ more than flows
        interpretation["thesis"] = "Campaign-heavy revenue indicates automation underinvestment"
        interpretation["opportunity"] = "Adding flows (Welcome, Abandoned Cart, Post Purchase) could increase automation revenue"
        interpretation["priority"] = "HIGH"
    elif flow_percentage > campaign_percentage * 1.2:  # Flows 20%+ more than campaigns
        interpretation["thesis"] = "Healthy automation foundation with potential campaign opportunity"
        interpretation["opportunity"] = "Regular campaign sends could complement strong automation performance"
        interpretation["priority"] = "MEDIUM"
    else:
        interpretation["thesis"] = "Balanced approach between campaigns and flows"
        interpretation["opportunity"] = "Optimize both channels for maximum impact"
        interpretation["priority"] = "LOW"
    
    # KAV percentage analysis (industry benchmark is typically 30%)
    kav_benchmark = 30.0
    if benchmarks and isinstance(benchmarks, dict):
        # Try to get KAV benchmark from benchmarks if available
        kav_benchmark = benchmarks.get("kav_benchmark", 30.0)
    
    if kav_percentage < 25:
        interpretation["kav_status"] = "Below industry benchmark (30%)"
        interpretation["kav_opportunity"] = f"Reaching 30% KAV could generate additional revenue"
    elif kav_percentage < 30:
        interpretation["kav_status"] = "Approaching industry benchmark"
        interpretation["kav_opportunity"] = "Small optimizations could reach benchmark"
    else:
        interpretation["kav_status"] = "Exceeds industry benchmark"
        interpretation["kav_opportunity"] = "Maintain position and optimize further"
    
    return interpretation


async def prepare_kav_data(
    kav_raw: Dict[str, Any], 
    client_name: str = "the client",
    account_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Prepare KAV data for template consumption with LLM-generated strategic narratives."""
    if not kav_raw:
        return {}
    
    # Ensure all required fields are present
    period = kav_raw.get("period", {})
    revenue = kav_raw.get("revenue", {})
    totals = kav_raw.get("totals", {})
    
    # Get account context (currency, timezone)
    account_context = account_context or {}
    currency = account_context.get("currency", "USD")
    timezone = account_context.get("timezone", "UTC")
    
    # Calculate flow and campaign percentages early (needed for interpretation)
    flow_pct = revenue.get("flow_percentage", 0)
    campaign_pct = revenue.get("campaign_percentage", 0)
    kav_pct = revenue.get("attributed_percentage", 0) or totals.get("kav_percentage", 0)
    
    # If percentages not in revenue, calculate from totals
    if not flow_pct and totals:
        attributed = totals.get("attributed_revenue", 0)
        if attributed > 0:
            flow_pct = (totals.get("flow_revenue", 0) / attributed) * 100
            campaign_pct = (totals.get("campaign_revenue", 0) / attributed) * 100
    
    # Step 1: Interpret KAV split (before LLM call)
    # Get benchmarks from account_context if available
    benchmarks = account_context.get("benchmarks", {}) if account_context else {}
    kav_interpretation = interpret_kav_split(
        flow_percentage=flow_pct,
        campaign_percentage=campaign_pct,
        kav_percentage=kav_pct,
        benchmarks=benchmarks
    )
    
    logger.info(
        f"KAV interpretation: {kav_interpretation.get('thesis')} "
        f"(Priority: {kav_interpretation.get('priority')}) - {kav_interpretation.get('kav_status')}"
    )
    
    # Initialize variables for LLM response
    primary_narrative = ""
    secondary_narrative = ""
    strategic_focus = "optimization"
    recommendations = []
    areas_of_opportunity = []
    root_cause_analysis = {}
    risk_flags = []
    quick_wins = []
    
    # Try to use LLM service for insights
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
        
        # Get industry from account_context if available
        industry = account_context.get("industry", "retail") if account_context else "retail"
        
        # Format data for LLM
        formatted_data = LLMDataFormatter.format_for_kav_analysis(
            kav_data=kav_raw,
            client_context={
                "client_name": client_name,
                "industry": industry,
                "kav_benchmark": 30.0,  # Industry standard (will be overridden by benchmarks)
                "currency": currency,
                "timezone": timezone
            }
        )
        
        # Add KAV interpretation to context for LLM
        if "context" not in formatted_data:
            formatted_data["context"] = {}
        formatted_data["context"]["kav_interpretation"] = kav_interpretation
        
        # Generate insights using LLM
        strategic_narratives = await llm_service.generate_insights(
            section="kav",
            data=formatted_data,
            context=formatted_data.get("context", {})
        )
        
        # Extract narratives - ensure they're strings, not JSON, and format as HTML
        primary_raw = strategic_narratives.get("primary", "")
        if isinstance(primary_raw, str):
            # If it looks like raw JSON, don't use it
            if primary_raw.strip().startswith('{') or (primary_raw.strip().startswith('"') and '"primary"' in primary_raw[:100]):
                logger.warning("Primary narrative appears to be JSON string, JSON parsing may have failed")
                primary_narrative = ""
            else:
                # Format as HTML paragraphs (split on double newlines)
                if primary_raw:
                    paragraphs = [p.strip() for p in primary_raw.split('\n\n') if p.strip()]
                    primary_narrative = '\n'.join([f'<p>{p}</p>' for p in paragraphs])
                else:
                    primary_narrative = ""
        else:
            primary_narrative = str(primary_raw) if primary_raw else ""
        
        secondary_raw = strategic_narratives.get("secondary", "")
        if isinstance(secondary_raw, str):
            if secondary_raw.strip().startswith('{') or (secondary_raw.strip().startswith('"') and '"secondary"' in secondary_raw[:100]):
                logger.warning("Secondary narrative appears to be JSON string, JSON parsing may have failed")
                secondary_narrative = ""
            else:
                # Format as HTML paragraphs (split on double newlines)
                if secondary_raw:
                    paragraphs = [p.strip() for p in secondary_raw.split('\n\n') if p.strip()]
                    secondary_narrative = '\n'.join([f'<p>{p}</p>' for p in paragraphs])
                else:
                    secondary_narrative = ""
        else:
            secondary_narrative = str(secondary_raw) if secondary_raw else ""
        
        strategic_focus = strategic_narratives.get("strategic_focus", "optimization")
        
        # Extract recommendations (can be list of strings or list of dicts)
        recommendations = strategic_narratives.get("recommendations", [])
        if not isinstance(recommendations, list):
            recommendations = []
        
        # Extract areas of opportunity
        areas_of_opportunity = strategic_narratives.get("areas_of_opportunity", [])
        if not isinstance(areas_of_opportunity, list):
            areas_of_opportunity = []
        
        # Extract enhanced strategic value elements
        root_cause_analysis = strategic_narratives.get("root_cause_analysis", {})
        if not isinstance(root_cause_analysis, dict):
            root_cause_analysis = {}
        
        risk_flags = strategic_narratives.get("risk_flags", [])
        if not isinstance(risk_flags, list):
            risk_flags = []
        
        quick_wins = strategic_narratives.get("quick_wins", [])
        if not isinstance(quick_wins, list):
            quick_wins = []
        
    except Exception as e:
        # Fallback to original narrative if LLM fails
        logger.warning(f"LLM service unavailable, using fallback narrative: {e}")
        
        # Fallback to original data or simple narrative
        primary_narrative = kav_raw.get("narrative", "")
        secondary_narrative = kav_raw.get("secondary_narrative", "")
        strategic_focus = "optimization"
        recommendations = []
        areas_of_opportunity = []
        root_cause_analysis = {}
        risk_flags = []
        quick_wins = []
        
        # If no narrative exists, create a simple one
        if not primary_narrative:
            # Try to get KAV percentage from either structure
            kav_pct = revenue.get("attributed_percentage", 0) or totals.get("kav_percentage", 0)
            primary_narrative = f"Klaviyo Attributed Value (KAV) represents {kav_pct:.1f}% of total revenue, indicating the impact of email and SMS marketing efforts."
    
    # Calculate message type breakdown (Campaigns vs Flows)
    flow_revenue = revenue.get("flow_attributed", totals.get("flow_revenue", 0))
    campaign_revenue = revenue.get("campaign_attributed", totals.get("campaign_revenue", 0))
    attributed_revenue = revenue.get("attributed", totals.get("attributed_revenue", 0))
    
    # Get previous period data for growth calculation
    previous_period = kav_raw.get("previous_period", {})
    # Previous period structure: {total_revenue, attributed_revenue, period}
    # We don't have flow/campaign breakdown for previous period, so we'll estimate
    # based on current period percentages or set growth to 0
    if previous_period:
        previous_attributed_revenue = previous_period.get("attributed_revenue", 0)
        # Estimate previous flow/campaign revenue using current percentages
        # This is an approximation - ideally we'd fetch previous period breakdown
        if attributed_revenue > 0 and previous_attributed_revenue > 0:
            # Use current period percentages to estimate previous period breakdown
            previous_flow_revenue = previous_attributed_revenue * (flow_pct / 100) if flow_pct > 0 else 0
            previous_campaign_revenue = previous_attributed_revenue * (campaign_pct / 100) if campaign_pct > 0 else 0
        else:
            previous_flow_revenue = 0
            previous_campaign_revenue = 0
    else:
        previous_flow_revenue = 0
        previous_campaign_revenue = 0
        previous_attributed_revenue = 0
    
    # Calculate growth rates
    flow_growth = 0
    if previous_flow_revenue > 0:
        flow_growth = ((flow_revenue - previous_flow_revenue) / previous_flow_revenue) * 100
    
    campaign_growth = 0
    if previous_campaign_revenue > 0:
        campaign_growth = ((campaign_revenue - previous_campaign_revenue) / previous_campaign_revenue) * 100
    
    # Message type breakdown
    message_type_breakdown = {
        "campaigns": {
            "revenue": campaign_revenue,
            "percentage": campaign_pct,
            "growth": round(campaign_growth, 1)
        },
        "flows": {
            "revenue": flow_revenue,
            "percentage": flow_pct,
            "growth": round(flow_growth, 1)
        },
        "total_attributed": attributed_revenue
    }
    
    # Channel breakdown (Email, SMS, Push)
    # Get channel revenue from kav_raw if available (calculated in orchestrator)
    channel_revenue = kav_raw.get("channel_revenue", {})
    email_revenue = channel_revenue.get("email", 0)
    sms_revenue = channel_revenue.get("sms", 0)
    push_revenue = channel_revenue.get("push", 0)
    
    # If channel revenue not available, default to all Email (backward compatibility)
    if email_revenue == 0 and sms_revenue == 0 and push_revenue == 0:
        email_revenue = campaign_revenue  # Default: all campaign revenue is Email
        sms_revenue = 0
        push_revenue = 0
    
    # Calculate channel percentages
    total_channel_revenue = email_revenue + sms_revenue + push_revenue
    if total_channel_revenue > 0:
        email_pct = (email_revenue / total_channel_revenue) * 100
        sms_pct = (sms_revenue / total_channel_revenue) * 100
        push_pct = (push_revenue / total_channel_revenue) * 100
    else:
        # Fallback: if no channel revenue, assume all Email
        email_pct = 100.0 if attributed_revenue > 0 else 0
        sms_pct = 0
        push_pct = 0
    
    # Get previous period channel data (default to all Email)
    previous_email_revenue = previous_attributed_revenue if previous_period else 0
    previous_sms_revenue = 0
    previous_push_revenue = 0
    
    # Calculate channel growth rates
    email_growth = 0
    if previous_email_revenue > 0:
        email_growth = ((email_revenue - previous_email_revenue) / previous_email_revenue) * 100
    
    sms_growth = 0
    push_growth = 0
    
    channel_breakdown = {
        "email": {
            "revenue": email_revenue,
            "percentage": email_pct,
            "growth": round(email_growth, 1)
        },
        "sms": {
            "revenue": sms_revenue,
            "percentage": sms_pct,
            "growth": round(sms_growth, 1)
        },
        "push": {
            "revenue": push_revenue,
            "percentage": push_pct,
            "growth": round(push_growth, 1)
        },
        "total_attributed": attributed_revenue
    }
    
    return {
        "period": {
            "start_date": period.get("start_date", "N/A"),
            "end_date": period.get("end_date", "N/A"),
            "days": period.get("days", 90)
        },
        "revenue": {
            "total_website": revenue.get("total_website", totals.get("total_revenue", 0)),
            "total_website_formatted": revenue.get("total_website_formatted", f"${totals.get('total_revenue', 0):,.2f}"),
            "vs_previous_period": revenue.get("vs_previous_period", 0),
            "attributed": attributed_revenue,
            "attributed_percentage": revenue.get("attributed_percentage", totals.get("kav_percentage", 0)),
            "attributed_vs_previous": revenue.get("attributed_vs_previous", 0),
            "flow_attributed": flow_revenue,
            "campaign_attributed": campaign_revenue,
            "kav_percentage": revenue.get("kav_percentage", totals.get("kav_percentage", 0)),
            "flow_percentage": flow_pct,
            "campaign_percentage": campaign_pct
        },
        "message_type_breakdown": message_type_breakdown,
        "channel_breakdown": channel_breakdown,
        "chart_data": kav_raw.get("chart_data", {}),
        "narrative": primary_narrative,
        "secondary_narrative": secondary_narrative,
        "strategic_focus": strategic_focus,
        "recommendations": recommendations if isinstance(recommendations, list) else [],
        "areas_of_opportunity": areas_of_opportunity if isinstance(areas_of_opportunity, list) else [],
        "root_cause_analysis": root_cause_analysis,
        "risk_flags": risk_flags if isinstance(risk_flags, list) else [],
        "quick_wins": quick_wins if isinstance(quick_wins, list) else [],
        "kav_interpretation": kav_interpretation  # KAV strategic interpretation
    }

