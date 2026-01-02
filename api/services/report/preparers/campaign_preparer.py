"""
Campaign performance data preparer.
"""
from typing import Dict, Any, Optional
import logging
from ..html_formatter import format_llm_output

logger = logging.getLogger(__name__)


def recommend_segmentation(
    campaign_pattern: Dict[str, Any],
    deliverability_analysis: Dict[str, Any],
    benchmarks: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Strategist approach:
    - High spam complaints → Segmentation needed
    - Low open + high click → Segmentation needed
    - Batch and blast pattern → Segmentation needed
    
    Args:
        campaign_pattern: Campaign pattern diagnosis dictionary
        deliverability_analysis: Deliverability analysis dictionary
        benchmarks: Optional benchmarks dictionary (for 5-track model)
    
    Returns:
        Dict with needed flag, reason, priority, and tracks
    """
    recommendation = {
        "needed": False,
        "reason": "",
        "priority": "",
        "tracks": []
    }
    
    # Check if segmentation is needed based on deliverability or campaign patterns
    requires_segmentation = deliverability_analysis.get("requires_segmentation", False)
    pattern = campaign_pattern.get("pattern", "")
    
    if requires_segmentation or pattern in ["high_open_low_click", "low_open_high_click"]:
        recommendation["needed"] = True
        recommendation["reason"] = "Campaign performance and deliverability metrics indicate engagement-based segmentation is required"
        recommendation["priority"] = "HIGH"
        
        # Get 5-track model from benchmarks
        if benchmarks:
            segmentation_benchmarks = benchmarks.get("segmentation", {})
            tracks = segmentation_benchmarks.get("tracks", [])
            if tracks:
                recommendation["tracks"] = tracks
            else:
                # Fallback to default 5-track model
                recommendation["tracks"] = _get_default_5_track_model()
        else:
            # Fallback to default 5-track model
            recommendation["tracks"] = _get_default_5_track_model()
    
    return recommendation


def _get_default_5_track_model() -> list:
    """Get default 5-track segmentation model."""
    return [
        {
            "name": "Track A: Highly Engaged",
            "criteria": "Opened or clicked in last 30 days",
            "recommended_cadence": "Daily",
            "typical_percentage": 15
        },
        {
            "name": "Track B: Moderately Engaged",
            "criteria": "Opened or clicked in last 60 days (not in Track A)",
            "recommended_cadence": "2-3x/week",
            "typical_percentage": 25
        },
        {
            "name": "Track C: Broad Engaged",
            "criteria": "Opened or clicked in last 90 days (not in A or B)",
            "recommended_cadence": "1x/week",
            "typical_percentage": 20
        },
        {
            "name": "Track D: Unengaged",
            "criteria": "No engagement in 90+ days",
            "recommended_cadence": "Goes through Sunset Flow then suppressed if remains unengaged in a few days",
            "typical_percentage": 30
        },
        {
            "name": "Track E: For Suppression",
            "criteria": "Hard bounces, spam complaints, unsubscribes",
            "recommended_cadence": "Do not send. Needs to be suppressed",
            "typical_percentage": 10
        }
    ]


def analyze_deliverability(
    bounce_rate: float,
    spam_complaint_rate: float,
    unsubscribe_rate: float,
    benchmarks: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Strategist approach:
    - Spam complaint > 0.02% = Poor (sending frequency/content issues)
    - Unsubscribe > 0.15% = Poor (list quality or relevance)
    - Bounce > 0.50% = Poor (list hygiene needed)
    
    Args:
        bounce_rate: Campaign bounce rate percentage
        spam_complaint_rate: Campaign spam complaint rate percentage
        unsubscribe_rate: Campaign unsubscribe rate percentage
        benchmarks: Benchmarks dictionary with deliverability metrics
    
    Returns:
        Dict with overall_status, issues list, and requires_segmentation flag
    """
    issues = []
    campaign_benchmarks = benchmarks.get("campaigns", {})
    
    # Get benchmark values (defaults from strategist thresholds)
    spam_benchmark = campaign_benchmarks.get("spam_complaint_rate", {}).get("average", 0.02)
    unsubscribe_benchmark = campaign_benchmarks.get("unsubscribe_rate", {}).get("average", 0.15)
    bounce_benchmark = campaign_benchmarks.get("bounce_rate", {}).get("average", 0.50)
    
    if spam_complaint_rate > spam_benchmark:
        issues.append({
            "metric": "spam_complaint_rate",
            "value": spam_complaint_rate,
            "benchmark": spam_benchmark,
            "severity": "Poor",
            "diagnosis": "High spam complaints indicate sending frequency or content relevance issues. Likely combining engaged and unengaged segments.",
            "recommendation": "Implement engagement-based segmentation immediately"
        })
    
    if unsubscribe_rate > unsubscribe_benchmark:
        issues.append({
            "metric": "unsubscribe_rate",
            "value": unsubscribe_rate,
            "benchmark": unsubscribe_benchmark,
            "severity": "Poor",
            "diagnosis": "High unsubscribe rate suggests list quality issues or over-sending.",
            "recommendation": "Review sending frequency and segment unengaged subscribers"
        })
    
    if bounce_rate > bounce_benchmark:
        issues.append({
            "metric": "bounce_rate",
            "value": bounce_rate,
            "benchmark": bounce_benchmark,
            "severity": "Poor",
            "diagnosis": "High bounce rate indicates list hygiene problems.",
            "recommendation": "Run list hygiene audit and sunset flow"
        })
    
    return {
        "overall_status": "Poor" if issues else "Good",
        "issues": issues,
        "requires_segmentation": len(issues) > 0
    }


def diagnose_campaign_pattern(open_rate: float, click_rate: float, benchmark_open: float, benchmark_click: float) -> Dict[str, Any]:
    """
    Pattern recognition based on strategist approach:
    - High open + Low click = Unengaged list (batch and blast)
    - Low open + High click = Engaged but fatigued
    - Low open + Low click = Fundamental issues
    
    Args:
        open_rate: Campaign open rate percentage
        click_rate: Campaign click rate percentage
        benchmark_open: Industry benchmark open rate percentage
        benchmark_click: Industry benchmark click rate percentage
    
    Returns:
        Dict with pattern name, diagnosis, root_cause, and priority
    """
    patterns = {
        "high_open_low_click": {
            "condition": open_rate >= benchmark_open * 0.9 and click_rate < benchmark_click * 0.7,
            "diagnosis": "Strong subject lines but content not resonating. Likely batch-and-blast to unengaged list.",
            "root_cause": "Missing engagement-based segmentation",
            "priority": "HIGH"
        },
        "low_open_high_click": {
            "condition": open_rate < benchmark_open * 0.8 and click_rate >= benchmark_click * 0.9,
            "diagnosis": "Engaged subscribers are highly engaged, but list contains too many unengaged dragging down open rates.",
            "root_cause": "Over-sending to disengaged subscribers",
            "priority": "HIGH"
        },
        "underperforming_overall": {
            "condition": open_rate < benchmark_open * 0.8 and click_rate < benchmark_click * 0.7,
            "diagnosis": "Fundamental issues: list quality, deliverability, or content relevance.",
            "root_cause": "Multiple issues requiring audit",
            "priority": "CRITICAL"
        }
    }
    
    for pattern_name, pattern_data in patterns.items():
        if pattern_data["condition"]:
            return {
                "pattern": pattern_name,
                "diagnosis": pattern_data["diagnosis"],
                "root_cause": pattern_data["root_cause"],
                "priority": pattern_data["priority"]
            }
    
    return {
        "pattern": "performing_well",
        "diagnosis": "Campaign performance meets or exceeds benchmarks.",
        "root_cause": "No significant issues identified",
        "priority": "LOW"
    }


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
    
    # Step 1: Diagnose campaign pattern (before LLM call)
    avg_open_rate = summary.get("avg_open_rate", 0)
    avg_click_rate = summary.get("avg_click_rate", 0)
    benchmark_open = campaign_benchmarks.get("open_rate", {}).get("average", 44.50)
    benchmark_click = campaign_benchmarks.get("click_rate", {}).get("average", 1.66)
    
    pattern_diagnosis = diagnose_campaign_pattern(
        open_rate=avg_open_rate,
        click_rate=avg_click_rate,
        benchmark_open=benchmark_open,
        benchmark_click=benchmark_click
    )
    
    logger.info(
        f"Campaign pattern diagnosed: {pattern_diagnosis.get('pattern')} "
        f"(Priority: {pattern_diagnosis.get('priority')}) - {pattern_diagnosis.get('diagnosis')}"
    )
    logger.debug(f"Pattern diagnosis data structure: {pattern_diagnosis}")
    
    # Step 2: Analyze deliverability (before LLM call)
    bounce_rate = summary.get("avg_bounce_rate", 0)
    unsubscribe_rate = summary.get("avg_unsubscribe_rate", 0)
    spam_complaint_rate = summary.get("avg_spam_complaint_rate", 0)
    
    deliverability_analysis = analyze_deliverability(
        bounce_rate=bounce_rate,
        spam_complaint_rate=spam_complaint_rate,
        unsubscribe_rate=unsubscribe_rate,
        benchmarks=benchmarks
    )
    
    if deliverability_analysis.get("issues"):
        logger.info(
            f"Deliverability issues found: {len(deliverability_analysis.get('issues', []))} issues "
            f"(Status: {deliverability_analysis.get('overall_status')})"
        )
    else:
        logger.info(
            f"Deliverability analysis: No issues found (Status: {deliverability_analysis.get('overall_status')})"
        )
    logger.debug(f"Deliverability analysis data structure: {deliverability_analysis}")
    
    # Step 3: Recommend segmentation (before LLM call)
    segmentation_recommendation = recommend_segmentation(
        campaign_pattern=pattern_diagnosis,
        deliverability_analysis=deliverability_analysis,
        benchmarks=benchmarks
    )
    
    if segmentation_recommendation.get("needed"):
        logger.info(
            f"Segmentation recommended: {segmentation_recommendation.get('reason')} "
            f"(Priority: {segmentation_recommendation.get('priority')})"
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
        
        # Format data for LLM (include pattern diagnosis for context)
        formatted_data = LLMDataFormatter.format_for_campaign_analysis(
            campaign_data={"summary": summary},
            client_context={
                "client_name": client_name,
                "industry": industry,
                "currency": currency
            },
            benchmarks=benchmarks  # Pass benchmarks as separate parameter
        )
        
        # Add pattern diagnosis, deliverability analysis, and segmentation recommendation to formatted data for LLM context
        if "context" not in formatted_data:
            formatted_data["context"] = {}
        formatted_data["context"]["pattern_diagnosis"] = pattern_diagnosis
        formatted_data["context"]["deliverability_analysis"] = deliverability_analysis
        formatted_data["context"]["segmentation_recommendation"] = segmentation_recommendation
        
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
        
        # Format as HTML with markdown conversion
        if primary_text:
            narrative = format_llm_output(primary_text)
        else:
            narrative = ""
        
        # Extract secondary - handle raw JSON strings
        secondary_text = strategic_insights.get("secondary", "")
        if isinstance(secondary_text, str):
            if secondary_text.strip().startswith('{') or (secondary_text.strip().startswith('"') and '"secondary"' in secondary_text[:100]):
                logger.warning("Secondary text appears to be JSON string, JSON parsing may have failed")
                secondary_text = ""
        
        if secondary_text:
            secondary_narrative = format_llm_output(secondary_text)
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
        "pattern_diagnosis": pattern_diagnosis,  # Campaign pattern recognition
        "deliverability_analysis": deliverability_analysis,  # Deliverability analysis
        "segmentation_recommendation": segmentation_recommendation,  # Segmentation recommendation
        "recommendations": recommendations,  # LLM-generated recommendations
        "areas_of_opportunity": areas_of_opportunity,  # LLM-generated areas of opportunity table
        "narrative": narrative,  # LLM-generated narrative
        "secondary_narrative": secondary_narrative,  # LLM-generated secondary insights
        "performance_status": performance_status,  # LLM-determined status
        "root_cause_analysis": root_cause_analysis,  # LLM-generated root cause analysis
        "risk_flags": risk_flags,  # LLM-generated risk flags
        "quick_wins": quick_wins  # LLM-generated quick wins
    }

