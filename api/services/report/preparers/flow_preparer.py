"""
Flow data preparer.
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def analyze_flow_intent_level(flow_data: Dict[str, Any], flow_type: str) -> Dict[str, Any]:
    """
    Strategist approach:
    - "Added to Cart" = Lower intent, earlier funnel → Different timing/messaging
    - "Started Checkout" = Higher intent, closer to purchase → Urgent timing
    
    Args:
        flow_data: Flow data dictionary
        flow_type: Flow type string (e.g., "abandoned_cart", "abandoned_checkout")
    
    Returns:
        Dict with intent_level, recommended_timing, and messaging_strategy
    """
    flow_name = flow_data.get("flow_name", "").lower() if flow_data.get("flow_name") else ""
    flow_type_lower = flow_type.lower() if flow_type else ""
    
    intent_analysis = {
        "intent_level": None,
        "recommended_timing": None,
        "messaging_strategy": None
    }
    
    # Check for checkout abandonment (high intent)
    if "checkout" in flow_name or flow_type_lower == "abandoned_checkout":
        intent_analysis = {
            "intent_level": "high",
            "recommended_timing": "2 hours, 1 day, 3 days",
            "messaging_strategy": "Urgent, value-focused, minimal friction"
        }
    # Check for cart abandonment (medium intent)
    elif "cart" in flow_name or flow_type_lower == "abandoned_cart":
        intent_analysis = {
            "intent_level": "medium",
            "recommended_timing": "4 hours, 1 day, 3 days, 7 days",
            "messaging_strategy": "Product-focused, social proof, gentle urgency"
        }
    # Browse abandonment (lower intent)
    elif "browse" in flow_name or flow_type_lower == "browse_abandonment":
        intent_analysis = {
            "intent_level": "low",
            "recommended_timing": "1 day, 3 days, 7 days, 14 days",
            "messaging_strategy": "Educational, product discovery, brand awareness"
        }
    # Post-purchase (highest intent for retention)
    elif "post" in flow_name or "purchase" in flow_name or flow_type_lower == "post_purchase":
        intent_analysis = {
            "intent_level": "very_high",
            "recommended_timing": "Immediate, 1 day, 7 days",
            "messaging_strategy": "Thank you, cross-sell, upsell, reviews"
        }
    # Welcome series (medium-high intent for onboarding)
    elif "welcome" in flow_name or flow_type_lower == "welcome_series":
        intent_analysis = {
            "intent_level": "medium_high",
            "recommended_timing": "Immediate, 1 day, 3 days, 7 days",
            "messaging_strategy": "Onboarding, brand introduction, value proposition"
        }
    
    return intent_analysis


async def prepare_flow_data(
    flow_raw: Dict[str, Any],
    flow_type: str,
    benchmarks: Dict[str, Any],
    client_name: str = "the client",
    account_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Prepare individual flow data with benchmark comparisons and LLM-generated insights."""
    if not flow_raw:
        return {}
    
    # Get account context
    account_context = account_context or {}
    currency = account_context.get("currency", "USD")
    
    # Step 1: Analyze flow intent level (before LLM call)
    intent_analysis = analyze_flow_intent_level(flow_raw, flow_type)
    
    if intent_analysis.get("intent_level"):
        logger.info(
            f"Flow intent analysis: {intent_analysis.get('intent_level')} intent - "
            f"Timing: {intent_analysis.get('recommended_timing')}"
        )
    
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
        
        # Get industry from account_context
        industry = account_context.get("industry", "retail") if account_context else "retail"
        
        # Get benchmark for this flow type to include in LLM data
        flow_benchmarks = benchmarks.get("flows", {}).get(flow_type, {})
        benchmark = {
            "open_rate": flow_benchmarks.get("open_rate", {}).get("average", 0),
            "click_rate": flow_benchmarks.get("click_rate", {}).get("average", 0),
            "conversion_rate": flow_benchmarks.get("conversion_rate", {}).get("average", 0),
            "revenue_per_recipient": flow_benchmarks.get("revenue_per_recipient", {}).get("average", 0)
        }
        
        # Prepare flow data structure for LLM (match what format_for_flow_analysis expects)
        flow_perf = flow_raw.get("performance", {})
        flow_data_for_llm = {
            "flow_name": flow_raw.get("flow_name", flow_type.replace("_", " ").title()),
            "metrics": {
                "open_rate": flow_perf.get("open_rate", 0),
                "click_rate": flow_perf.get("click_rate", 0),
                "conversion_rate": flow_perf.get("conversion_rate", flow_perf.get("placed_order_rate", 0)),
                "revenue": flow_perf.get("revenue", 0),
                "revenue_per_recipient": flow_perf.get("revenue_per_recipient", 0),
                "conversions": flow_perf.get("conversions", 0)
            },
            "benchmark": benchmark
        }
        
        # Format data for LLM
        formatted_data = LLMDataFormatter.format_for_flow_analysis(
            flow_data=flow_data_for_llm,
            client_context={
                "client_name": client_name,
                "industry": industry,
                "currency": currency
            }
        )
        
        # Add intent analysis to context for LLM
        if "context" not in formatted_data:
            formatted_data["context"] = {}
        formatted_data["context"]["intent_analysis"] = intent_analysis
        
        # Generate insights using LLM
        strategic_insights = await llm_service.generate_insights(
            section="flow_performance",
            data=formatted_data,
            context=formatted_data.get("context", {})
        )
        
        narrative = strategic_insights.get("primary", "")
        secondary_narrative = strategic_insights.get("secondary", "")
        performance_status = strategic_insights.get("performance_status", "needs_improvement")
        areas_of_opportunity = strategic_insights.get("areas_of_opportunity", [])
        
    except Exception as e:
        # Fallback - log error but still try to provide minimal analysis
        logger.error(f"LLM service unavailable for flow analysis: {e}", exc_info=True)
        # Provide minimal data-driven fallback instead of empty
        flow_perf = flow_raw.get("performance", {})
        open_rate = flow_perf.get("open_rate", 0)
        click_rate = flow_perf.get("click_rate", 0)
        narrative = f"<p>Your {flow_raw.get('flow_name', 'flow')} flow demonstrates {open_rate:.1f}% open rate and {click_rate:.1f}% click rate. Review the metrics above to identify optimization opportunities.</p>"
        secondary_narrative = ""
        performance_status = "needs_improvement"
        areas_of_opportunity = []
    
    # Get benchmark for this flow type
    flow_benchmarks = benchmarks.get("flows", {}).get(flow_type, {})
    
    benchmark = {
        "open_rate": flow_benchmarks.get("open_rate", {}).get("average", 0),
        "click_rate": flow_benchmarks.get("click_rate", {}).get("average", 0),
        "conversion_rate": flow_benchmarks.get("conversion_rate", {}).get("average", 0),
        "revenue_per_recipient": flow_benchmarks.get("revenue_per_recipient", {}).get("average", 0)
    }
    
    return {
        "flow_name": flow_raw.get("flow_name", flow_type.replace("_", " ").title()),
        "status": flow_raw.get("status", "unknown"),
        "email_count": flow_raw.get("email_count", 0),
        "performance": flow_raw.get("performance", {}),
        "benchmark": flow_raw.get("benchmark", benchmark),
        "industry": flow_raw.get("industry", "Apparel and Accessories"),
        "analysis": flow_raw.get("analysis", {}),
        "intent_analysis": intent_analysis,  # Flow intent level analysis
        "narrative": narrative,  # LLM-generated narrative
        "secondary_narrative": secondary_narrative,  # LLM-generated secondary insights
        "performance_status": performance_status,  # LLM-determined status
        "areas_of_opportunity": areas_of_opportunity if isinstance(areas_of_opportunity, list) else []  # LLM-generated areas of opportunity table
    }

