"""
Automation overview data preparer.
"""
from typing import Dict, Any, Optional
import logging
from .helpers import generate_flow_strategic_summary, create_flow_implementation_roadmap

logger = logging.getLogger(__name__)


async def prepare_automation_data(
    automation_raw: Dict[str, Any],
    benchmarks: Dict[str, Any],
    client_name: str = "the client",
    account_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Prepare automation overview data with advanced flow intelligence and LLM-generated insights."""
    if not automation_raw:
        return {}
    
    # Get account context
    account_context = account_context or {}
    currency = account_context.get("currency", "USD")
    
    flows = automation_raw.get("flows", [])
    
    # Ensure all flows have recipients field and calculate performance tier/strategic focus
    from ...benchmark import BenchmarkService
    benchmark_service = BenchmarkService()
    
    for flow in flows:
        if "recipients" not in flow:
            # Try to calculate from revenue and revenue_per_recipient if available
            revenue = flow.get("revenue", 0)
            rev_per_recip = flow.get("revenue_per_recipient", 0)
            if rev_per_recip > 0:
                flow["recipients"] = int(revenue / rev_per_recip) if revenue > 0 else 0
            else:
                flow["recipients"] = 0
        
        # Calculate performance tier based on open rate, click rate, and conversion rate
        open_rate = flow.get("avg_open_rate", 0)
        click_rate = flow.get("avg_click_rate", 0)
        conversion_rate = flow.get("avg_placed_order_rate", 0)
        
        # Determine flow type for benchmark lookup
        flow_name_lower = flow.get("name", "").lower()
        flow_type = None
        if "welcome" in flow_name_lower or "nurture" in flow_name_lower:
            flow_type = "welcome_series"
        elif "abandon" in flow_name_lower and ("cart" in flow_name_lower or "checkout" in flow_name_lower):
            flow_type = "abandoned_cart"
        elif "browse" in flow_name_lower:
            flow_type = "browse_abandonment"
        elif "post" in flow_name_lower or "purchase" in flow_name_lower:
            flow_type = "post_purchase"
        
        # Get benchmarks - check nested structure first
        benchmarks = benchmark_service.get_all_benchmarks()
        
        # Try to get flow-specific benchmarks from nested structure
        flow_benchmarks = None
        if flow_type and "flows" in benchmarks and flow_type in benchmarks["flows"]:
            flow_benchmarks = benchmarks["flows"][flow_type]
        
        # Helper function to calculate tier from benchmark data
        def calculate_tier_from_benchmark(value: float, bench_data: Dict[str, Any]) -> Dict[str, Any]:
            """Calculate tier from benchmark data structure."""
            if not bench_data:
                return {"tier": "unknown", "percentile": 50.0}
            
            avg = bench_data.get("average", 0)
            top_10 = bench_data.get("top_10_percent", avg * 1.5)
            
            if avg == 0:
                return {"tier": "unknown", "percentile": 50.0}
            
            if value >= top_10:
                percentile = 90.0
                tier = "excellent"
            elif value >= avg:
                ratio = (value - avg) / (top_10 - avg) if top_10 > avg else 0.5
                percentile = 50.0 + (ratio * 40.0)
                tier = "good" if percentile >= 70 else "average"
            else:
                ratio = value / avg if avg > 0 else 0
                percentile = max(0.0, min(50.0, ratio * 50.0))
                tier = "average" if percentile >= 25 else "poor"
            
            return {"tier": tier, "percentile": percentile}
        
        # Calculate tiers using flow-specific or generic benchmarks
        if flow_benchmarks and "open_rate" in flow_benchmarks:
            open_tier = calculate_tier_from_benchmark(open_rate, flow_benchmarks["open_rate"])
        else:
            open_tier = benchmark_service.get_performance_tier("open_rate", open_rate)
        
        if flow_benchmarks and "click_rate" in flow_benchmarks:
            click_tier = calculate_tier_from_benchmark(click_rate, flow_benchmarks["click_rate"])
        else:
            click_tier = benchmark_service.get_performance_tier("click_rate", click_rate)
        
        if flow_benchmarks and "conversion_rate" in flow_benchmarks:
            conversion_tier = calculate_tier_from_benchmark(conversion_rate, flow_benchmarks["conversion_rate"])
        else:
            conversion_tier = benchmark_service.get_performance_tier("conversion_rate", conversion_rate)
        
        # Calculate overall performance tier (average of all tiers)
        tier_scores = {"excellent": 4, "good": 3, "average": 2, "poor": 1, "unknown": 1}
        avg_score = (
            tier_scores.get(open_tier.get("tier", "unknown"), 1) +
            tier_scores.get(click_tier.get("tier", "unknown"), 1) +
            tier_scores.get(conversion_tier.get("tier", "unknown"), 1)
        ) / 3
        
        if avg_score >= 3.5:
            performance_tier = "Excellent"
        elif avg_score >= 2.5:
            performance_tier = "Good"
        elif avg_score >= 1.5:
            performance_tier = "Average"
        else:
            performance_tier = "Poor"
        
        flow["performance_tier"] = performance_tier
        
        # Determine strategic focus based on which metric needs the most improvement
        gaps = {
            "open_rate": open_tier.get("percentile", 50),
            "click_rate": click_tier.get("percentile", 50),
            "conversion_rate": conversion_tier.get("percentile", 50)
        }
        
        # Find the metric with the lowest percentile (needs most improvement)
        min_metric = min(gaps.items(), key=lambda x: x[1])
        
        if min_metric[1] < 25:
            strategic_focus = "Critical Optimization"
        elif min_metric[1] < 50:
            strategic_focus = "Performance Enhancement"
        elif min_metric[1] < 75:
            strategic_focus = "Optimization Analysis"
        else:
            strategic_focus = "Maintenance"
        
        flow["strategic_focus"] = strategic_focus
    
    # Calculate totals
    total_revenue = sum(f.get("revenue", 0) for f in flows)
    total_recipients = sum(f.get("recipients", 0) for f in flows)
    
    # Import advanced analyzers
    try:
        from ...klaviyo.flows.lifecycle import FlowLifecycleAnalyzer
        from ...klaviyo.segmentation.analyzer import SegmentationAnalyzer
        
        # Initialize analyzers
        lifecycle_analyzer = FlowLifecycleAnalyzer()
        segmentation_analyzer = SegmentationAnalyzer()
        
        # Prepare flow data for analysis
        flows_for_analysis = {}
        individual_flow_analyses = {}
        
        for flow in flows:
            flow_name = flow.get("name", "").lower()
            flow_data = {
                "name": flow.get("name"),
                "open_rate": flow.get("avg_open_rate", 0),
                "click_rate": flow.get("avg_click_rate", 0), 
                "placed_order_rate": flow.get("avg_placed_order_rate", 0),
                "revenue": flow.get("revenue", 0),
                "recipients": flow.get("recipients", 0)
            }
            
            # Categorize flows for lifecycle analysis
            if "welcome" in flow_name:
                flows_for_analysis["welcome_series"] = flow_data
                individual_flow_analyses["welcome_series"] = lifecycle_analyzer.analyze_welcome_series(flow_data)
            elif "abandon" in flow_name and "cart" in flow_name:
                flows_for_analysis["abandoned_cart"] = flow_data
                individual_flow_analyses["abandoned_cart"] = lifecycle_analyzer.analyze_abandonment_flows(flow_data, None)["cart_abandonment"]
            elif "browse" in flow_name:
                flows_for_analysis["browse_abandonment"] = flow_data
                individual_flow_analyses["browse_abandonment"] = lifecycle_analyzer.analyze_browse_abandonment(flow_data)
            elif "post" in flow_name or "purchase" in flow_name:
                flows_for_analysis["post_purchase"] = flow_data
                individual_flow_analyses["post_purchase"] = lifecycle_analyzer.analyze_post_purchase_flows(flow_data)
        
        # Generate optimization priority matrix
        optimization_priority_matrix = lifecycle_analyzer.get_flow_optimization_priority_matrix(individual_flow_analyses)
        
        # Generate segmentation analysis
        segmentation_analysis = segmentation_analyzer.analyze_flow_segmentation(flows_for_analysis)
        
        # Combine analyses into strategic summary
        strategic_summary = generate_flow_strategic_summary(
            optimization_priority_matrix, segmentation_analysis
        )
        
        # Create implementation roadmap
        implementation_roadmap = create_flow_implementation_roadmap(
            optimization_priority_matrix, segmentation_analysis
        )
        
        flow_lifecycle_analysis = {
            "individual_flows": individual_flow_analyses,
            "optimization_priority_matrix": optimization_priority_matrix,
            "strategic_summary": strategic_summary,
            "implementation_roadmap": implementation_roadmap
        }
        
    except Exception as e:
        logger.warning(f"Advanced flow analysis failed: {e}")
        flow_lifecycle_analysis = None
        segmentation_analysis = None
    
    # Try to use LLM service for strategic narrative
    narrative = automation_raw.get("narrative", "")
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
            section="automation_overview",
            data={
                "total_revenue": total_revenue,
                "total_recipients": total_recipients,
                "flows": flows,
                "period_days": automation_raw.get("period_days", 90)
            },
            client_context={
                "client_name": client_name,
                "industry": industry,
                "currency": currency
            }
        )
        
        # Generate insights using LLM
        strategic_insights = await llm_service.generate_insights(
            section="automation_overview",
            data=formatted_data,
            context=formatted_data.get("context", {})
        )
        
        primary_text = strategic_insights.get("primary", narrative)
        # Format as HTML paragraphs
        if primary_text:
            paragraphs = [p.strip() for p in primary_text.split('\n\n') if p.strip()]
            narrative = '\n'.join([f'<p>{p}</p>' for p in paragraphs])
        else:
            narrative = narrative if narrative else ""
        
        analysis_text = strategic_insights.get("secondary", "")
        if analysis_text:
            paragraphs = [p.strip() for p in analysis_text.split('\n\n') if p.strip()]
            analysis_text = '\n'.join([f'<p>{p}</p>' for p in paragraphs])
        
        narrative_text = strategic_insights.get("narrative_text", "")
        if narrative_text:
            paragraphs = [p.strip() for p in narrative_text.split('\n\n') if p.strip()]
            narrative_text = '\n'.join([f'<p>{p}</p>' for p in paragraphs])
        
    except Exception as e:
        logger.warning(f"LLM service unavailable for automation overview, using fallback: {e}")
        # Format existing narrative as HTML if it exists
        if narrative:
            paragraphs = [p.strip() for p in narrative.split('\n\n') if p.strip()]
            narrative = '\n'.join([f'<p>{p}</p>' for p in paragraphs])
        analysis_text = ""
        narrative_text = ""
    
    return {
        "period_days": automation_raw.get("period_days", 90),
        "flows": flows,  # All flows should be included
        "summary": {
            "total_conversion_value": total_revenue,
            "vs_previous_period": automation_raw.get("summary", {}).get("vs_previous_period", 0),
            "total_recipients": total_recipients,
            "recipients_vs_previous": automation_raw.get("summary", {}).get("recipients_vs_previous", 0)
        },
        "chart_data": automation_raw.get("chart_data", {}),
        "narrative": narrative,  # LLM-generated narrative (HTML formatted)
        "analysis_text": analysis_text,  # LLM-generated analysis (HTML formatted)
        "narrative_text": narrative_text,  # LLM-generated narrative text (HTML formatted)
        # Advanced intelligence
        "flow_lifecycle_analysis": flow_lifecycle_analysis,
        "segmentation_analysis": segmentation_analysis
    }

