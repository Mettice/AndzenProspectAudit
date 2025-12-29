"""
Campaign performance data preparer.
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


async def prepare_campaign_performance_data(
    campaign_raw: Dict[str, Any],
    benchmarks: Dict[str, Any],
    client_name: str = "the client",
    account_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Prepare campaign performance data with benchmark comparisons and LLM-generated insights."""
    if not campaign_raw:
        return {}
    
    # Get account context
    account_context = account_context or {}
    currency = account_context.get("currency", "USD")
    
    campaign_benchmarks = benchmarks.get("campaigns", {})
    summary = campaign_raw.get("summary", {})
    
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
        
        # Format data for LLM
        formatted_data = LLMDataFormatter.format_for_campaign_analysis(
            campaign_data={"summary": summary},
            client_context={
                "client_name": client_name,
                "industry": industry,
                "currency": currency
            },
            benchmarks=benchmarks  # Pass benchmarks as separate parameter
        )
        
        # Generate insights using LLM
        strategic_insights = await llm_service.generate_insights(
            section="campaign_performance",
            data=formatted_data,
            context=formatted_data.get("context", {})
        )
        
        # Extract primary - handle raw JSON strings
        primary_text = strategic_insights.get("primary", "")
        if isinstance(primary_text, str):
            # If it looks like raw JSON, don't use it
            if primary_text.strip().startswith('{') or (primary_text.strip().startswith('"') and '"primary"' in primary_text[:100]):
                logger.warning("Primary text appears to be JSON string, JSON parsing may have failed")
                primary_text = ""
        
        # Format as HTML paragraphs
        if primary_text:
            paragraphs = [p.strip() for p in primary_text.split('\n\n') if p.strip()]
            narrative = '\n'.join([f'<p>{p}</p>' for p in paragraphs])
        else:
            narrative = ""
        
        # Extract secondary - handle raw JSON strings
        secondary_text = strategic_insights.get("secondary", "")
        if isinstance(secondary_text, str):
            if secondary_text.strip().startswith('{') or (secondary_text.strip().startswith('"') and '"secondary"' in secondary_text[:100]):
                logger.warning("Secondary text appears to be JSON string, JSON parsing may have failed")
                secondary_text = ""
        
        if secondary_text:
            paragraphs = [p.strip() for p in secondary_text.split('\n\n') if p.strip()]
            secondary_narrative = '\n'.join([f'<p>{p}</p>' for p in paragraphs])
        else:
            secondary_narrative = ""
        
        performance_status = strategic_insights.get("performance_status", "needs_improvement")
        
        # Get recommendations from LLM response (can be list of strings or list of dicts)
        recommendations = strategic_insights.get("recommendations", [])
        # If recommendations is a string, try to parse it
        if isinstance(recommendations, str):
            recommendations = [r.strip() for r in recommendations.split('\n') if r.strip() and len(r.strip()) > 20]
        # Ensure it's a list
        if not isinstance(recommendations, list):
            recommendations = []
        
        # Get areas of opportunity from LLM response
        areas_of_opportunity = strategic_insights.get("areas_of_opportunity", [])
        # Ensure it's a list
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
        # Fallback - log error but still try to provide minimal analysis
        logger.error(f"LLM service unavailable for campaign analysis: {e}", exc_info=True)
        # Provide minimal data-driven fallback instead of empty
        avg_open = summary.get("avg_open_rate", 0)
        avg_click = summary.get("avg_click_rate", 0)
        narrative = f"<p>Over the past 3 months, your campaign metrics show {avg_open:.1f}% open rate and {avg_click:.1f}% click rate. Review the metrics above to identify optimization opportunities.</p>"
        secondary_narrative = ""
        performance_status = "needs_improvement"
        recommendations = []
        areas_of_opportunity = []
        root_cause_analysis = {}
        risk_flags = []
        quick_wins = []
    
    # Determine status vs benchmark
    def get_status(metric_val, benchmark_avg):
        if metric_val >= benchmark_avg * 1.1:
            return "exceeds"
        elif metric_val >= benchmark_avg * 0.9:
            return "meets"
        else:
            return "below"
    
    return {
        "summary": summary,
        "benchmark": campaign_raw.get("benchmark", {
            "industry": "Apparel and Accessories",
            "open_rate": campaign_benchmarks.get("open_rate", {}).get("average", 44.50),
            "click_rate": campaign_benchmarks.get("click_rate", {}).get("average", 1.66),
            "conversion_rate": campaign_benchmarks.get("conversion_rate", {}).get("average", 0.07),
            "revenue_per_recipient": campaign_benchmarks.get("revenue_per_recipient", {}).get("average", 0.09)
        }),
        "vs_benchmark": {
            "open_rate": get_status(
                summary.get("avg_open_rate", 0),
                campaign_benchmarks.get("open_rate", {}).get("average", 44.50)
            ),
            "click_rate": get_status(
                summary.get("avg_click_rate", 0),
                campaign_benchmarks.get("click_rate", {}).get("average", 1.66)
            ),
            "conversion_rate": get_status(
                summary.get("avg_placed_order_rate", 0),
                campaign_benchmarks.get("conversion_rate", {}).get("average", 0.07)
            )
        },
        "analysis": campaign_raw.get("analysis", {}),
        "recommendations": recommendations,  # LLM-generated recommendations
        "areas_of_opportunity": areas_of_opportunity,  # LLM-generated areas of opportunity table
        "narrative": narrative,  # LLM-generated narrative
        "secondary_narrative": secondary_narrative,  # LLM-generated secondary insights
        "performance_status": performance_status,  # LLM-determined status
        "root_cause_analysis": root_cause_analysis,  # LLM-generated root cause analysis
        "risk_flags": risk_flags,  # LLM-generated risk flags
        "quick_wins": quick_wins  # LLM-generated quick wins
    }

