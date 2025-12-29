"""
Flow performance prompt templates (Welcome, Abandoned Cart, Browse Abandonment, Post Purchase).
Simplified to use narrative format with embedded strategic elements.
"""
from typing import Dict, Any
from .base import get_currency_symbol, get_strategic_value_instructions


def get_flow_prompt(data: Dict[str, Any], context: Dict[str, Any]) -> str:
    """Generate prompt for flow performance analysis (Welcome, Abandoned Cart, Browse Abandonment, Post Purchase)."""
    flow_name = data.get("flow_name", "Unknown Flow")
    metrics = data.get("metrics", {})
    client_name = context.get("client_name", "the client")
    industry = context.get("industry", "retail")
    currency = context.get("currency", "USD")
    
    currency_symbol = get_currency_symbol(currency)
    
    open_rate = metrics.get("open_rate", 0)
    click_rate = metrics.get("click_rate", 0)
    conversion_rate = metrics.get("conversion_rate", 0)
    revenue = metrics.get("revenue", 0)
    revenue_per_recipient = metrics.get("revenue_per_recipient", 0)
    conversions = metrics.get("conversions", 0)
    recipients = metrics.get("recipients", 0)
    
    # Get benchmark data if available
    benchmark = data.get("benchmark", {})
    benchmark_open = benchmark.get("open_rate", 0)
    benchmark_click = benchmark.get("click_rate", 0)
    benchmark_conv = benchmark.get("conversion_rate", 0)
    benchmark_revenue = benchmark.get("revenue_per_recipient", 0)
    
    # Calculate revenue opportunity
    revenue_opportunity = max(0, (benchmark_revenue - revenue_per_recipient) * recipients) if benchmark_revenue > 0 else 0
    
    prompt = f"""You are an expert email marketing strategist analyzing flow performance data. Provide clear narrative insights with embedded strategic elements.

CLIENT CONTEXT:
- Client: {client_name}
- Industry: {industry}
- Flow: {flow_name}
- Currency: {currency} ({currency_symbol})

FLOW PERFORMANCE METRICS:
- Open Rate: {open_rate:.2f}% (Benchmark: {benchmark_open:.2f}%)
- Click Rate: {click_rate:.2f}% (Benchmark: {benchmark_click:.2f}%)
- Conversion Rate: {conversion_rate:.2f}% (Benchmark: {benchmark_conv:.2f}%)
- Revenue: {currency_symbol}{revenue:,.2f}
- Revenue per Recipient: {currency_symbol}{revenue_per_recipient:.2f}
- Recipients: {recipients:,}
- Conversions: {conversions:,}

REVENUE OPPORTUNITY:
- Current Revenue: {currency_symbol}{revenue:,.2f}
- Revenue Opportunity: {currency_symbol}{revenue_opportunity:,.2f} if flow reaches benchmark

PROVIDE INSIGHTS IN SIMPLE JSON FORMAT:

{{
    "primary": "Flow performance analysis: {flow_name} showing {open_rate:.1f}% open rate vs {benchmark_open:.1f}% benchmark and {click_rate:.1f}% click rate vs {benchmark_click:.1f}% benchmark. Generated {currency_symbol}{revenue:,.0f} in revenue from {recipients:,} recipients. **Performance Status:** [Assess as Excellent/Good/Needs Improvement/Poor based on benchmarks]. **Quick Wins:** [List 2-3 immediate optimization opportunities with effort estimates like '2 hours to fix subject lines' and impact like '$5K potential']. **Risk Flags:** [Any critical issues like broken flows or zero conversions with severity levels].",
    "secondary": "Strategic recommendations with implementation guidance: **Top Priorities:** [Rank 3 optimization areas by ROI potential]. **Revenue Impact:** Optimizing to benchmark performance could generate additional {currency_symbol}{revenue_opportunity:,.0f}. **Next Steps:** [Specific actionable recommendations with timelines and expected results]. Include email timing, content optimization, segmentation opportunities, or flow expansion recommendations."
}}

GUIDELINES:
- Include specific numbers and benchmark comparisons
- Embed strategic elements (Quick Wins, Risk Flags, Top Priorities) within narrative text using **bold headers**
- Professional consultant tone with actionable insights
- Estimate revenue impact and implementation effort where relevant
- Focus on the biggest opportunities first
- Return only the JSON object"""

    return prompt


def get_browse_abandonment_prompt(data: Dict[str, Any], context: Dict[str, Any]) -> str:
    """Generate prompt for Browse Abandonment flow analysis."""
    return get_flow_prompt(data, context)  # Reuse main flow prompt


def get_post_purchase_prompt(data: Dict[str, Any], context: Dict[str, Any]) -> str:
    """Generate prompt for Post Purchase flow analysis."""
    return get_flow_prompt(data, context)  # Reuse main flow prompt