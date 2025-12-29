"""
Abandoned cart flow data preparer.
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


async def prepare_abandoned_cart_data(
    cart_raw: Dict[str, Any],
    benchmarks: Dict[str, Any],
    client_name: str = "the client",
    account_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Prepare abandoned cart flow data with LLM-generated insights."""
    if not cart_raw:
        return {}
    
    # Get account context
    account_context = account_context or {}
    currency = account_context.get("currency", "USD")
    
    # Get benchmark
    cart_benchmarks = benchmarks.get("flows", {}).get("abandoned_cart", {})
    
    # Try to use LLM service for insights
    narrative = ""
    recommendations = []
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
        
        # Get industry from account_context
        industry = account_context.get("industry", "retail") if account_context else "retail"
        
        # Get actual flow data for accurate narrative
        flows_list = cart_raw.get("flows", [])
        if flows_list:
            # Calculate averages from actual flows
            avg_open = sum(f.get("open_rate", 0) for f in flows_list) / len(flows_list)
            avg_click = sum(f.get("click_rate", 0) for f in flows_list) / len(flows_list)
            avg_conv = sum(f.get("placed_order_rate", 0) for f in flows_list) / len(flows_list)
            total_rev = sum(f.get("revenue", 0) for f in flows_list)
        else:
            avg_open = avg_click = avg_conv = total_rev = 0
        
        # Format data for LLM - use flow_analysis format since abandoned cart is a flow type
        formatted_data = LLMDataFormatter.format_for_flow_analysis(
            flow_data={
                "flow_name": "Abandoned Cart",
                "flows": flows_list,
                "performance": {
                    "open_rate": avg_open,
                    "click_rate": avg_click,
                    "conversion_rate": avg_conv,
                    "revenue": total_rev
                }
            },
            client_context={
                "client_name": client_name,
                "industry": industry,
                "currency": currency
            }
        )
        
        # Generate insights using LLM
        strategic_insights = await llm_service.generate_insights(
            section="flow_performance",
            data=formatted_data,
            context=formatted_data.get("context", {})
        )
        
        # Extract narratives - filter out raw JSON strings and format as HTML paragraphs
        primary_raw = strategic_insights.get("primary", "")
        if isinstance(primary_raw, str):
            if primary_raw.strip().startswith('{') or (primary_raw.strip().startswith('[') or (primary_raw.strip().startswith('"') and '"primary"' in primary_raw[:100])):
                logger.warning("Primary narrative appears to be JSON string, JSON parsing may have failed")
                narrative = ""
            else:
                # Format as HTML paragraphs
                if primary_raw:
                    paragraphs = [p.strip() for p in primary_raw.split('\n\n') if p.strip()]
                    narrative = '\n'.join([f'<p>{p}</p>' for p in paragraphs]) if paragraphs else f'<p>{primary_raw}</p>'
                else:
                    narrative = ""
        else:
            narrative = f'<p>{str(primary_raw)}</p>' if primary_raw else ""
        
        secondary_raw = strategic_insights.get("secondary", "")
        if isinstance(secondary_raw, str):
            if secondary_raw.strip().startswith('{') or (secondary_raw.strip().startswith('[') or (secondary_raw.strip().startswith('"') and '"secondary"' in secondary_raw[:100])):
                logger.warning("Secondary narrative appears to be JSON string, JSON parsing may have failed")
                secondary_narrative = ""
            else:
                # Format as HTML paragraphs
                if secondary_raw:
                    paragraphs = [p.strip() for p in secondary_raw.split('\n\n') if p.strip()]
                    secondary_narrative = '\n'.join([f'<p>{p}</p>' for p in paragraphs]) if paragraphs else f'<p>{secondary_raw}</p>'
                else:
                    secondary_narrative = ""
        else:
            secondary_narrative = f'<p>{str(secondary_raw)}</p>' if secondary_raw else ""
        
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
        
        # Format as HTML paragraphs
        if narrative:
            paragraphs = [p.strip() for p in narrative.split('\n\n') if p.strip()]
            narrative = '\n'.join([f'<p>{p}</p>' for p in paragraphs])
        if secondary_narrative:
            paragraphs = [p.strip() for p in secondary_narrative.split('\n\n') if p.strip()]
            secondary_narrative = '\n'.join([f'<p>{p}</p>' for p in paragraphs])
        
    except Exception as e:
        # Fallback if LLM fails
        logger.error(f"LLM service unavailable for abandoned cart analysis: {e}", exc_info=True)
        narrative = ""
        secondary_narrative = ""
        recommendations = cart_raw.get("recommendations", [])
        areas_of_opportunity = []
        root_cause_analysis = {}
        risk_flags = []
        quick_wins = []
    
    return {
        "flows": cart_raw.get("flows", []),
        "benchmark": cart_raw.get("benchmark", {
            "name": "Abandoned Cart",
            "open_rate": cart_benchmarks.get("open_rate", {}).get("average", 54.74),
            "click_rate": cart_benchmarks.get("click_rate", {}).get("average", 6.25),
            "conversion_rate": cart_benchmarks.get("conversion_rate", {}).get("average", 3.36),
            "revenue_per_recipient": cart_benchmarks.get("revenue_per_recipient", {}).get("average", 3.80)
        }),
        "industry": cart_raw.get("industry", "Apparel and Accessories"),
        "segmentation": cart_raw.get("segmentation", {}),
        "narrative": narrative,  # LLM-generated narrative (HTML formatted)
        "secondary_narrative": secondary_narrative,  # LLM-generated secondary insights (HTML formatted)
        "recommendations": recommendations,  # LLM-generated recommendations
        "areas_of_opportunity": areas_of_opportunity if isinstance(areas_of_opportunity, list) else [],  # LLM-generated areas of opportunity table
        "root_cause_analysis": root_cause_analysis,  # LLM-generated root cause analysis
        "risk_flags": risk_flags,  # LLM-generated risk flags
        "quick_wins": quick_wins  # LLM-generated quick wins
    }

