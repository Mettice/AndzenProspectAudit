"""
Campaign performance prompt templates.
Simplified to use narrative format with embedded strategic elements.
"""
from typing import Dict, Any
from .base import get_currency_symbol


def get_campaign_prompt(data: Dict[str, Any], context: Dict[str, Any]) -> str:
    """Generate prompt for campaign performance analysis."""
    client_name = context.get("client_name", "the client")
    industry = context.get("industry", "retail")
    currency = context.get("currency", "USD")
    
    currency_symbol = get_currency_symbol(currency)
    
    metrics = data.get("metrics", {})
    open_rate = metrics.get("open_rate", 0)
    click_rate = metrics.get("click_rate", 0)
    conversion_rate = metrics.get("conversion_rate", 0)
    revenue = metrics.get("revenue", 0)
    sent = metrics.get("sent", 0)
    
    # Benchmark data
    benchmark = data.get("benchmark", {})
    benchmark_open = benchmark.get("open_rate", 44.5)  # Industry average
    benchmark_click = benchmark.get("click_rate", 1.7)
    benchmark_conv = benchmark.get("conversion_rate", 0.07)
    
    # Get strategic analysis from context (added in Phase 1-4)
    # Context is passed as separate parameter, but also check data.context for backward compatibility
    pattern_diagnosis = context.get("pattern_diagnosis", data.get("context", {}).get("pattern_diagnosis", {}))
    deliverability_analysis = context.get("deliverability_analysis", data.get("context", {}).get("deliverability_analysis", {}))
    segmentation_recommendation = context.get("segmentation_recommendation", data.get("context", {}).get("segmentation_recommendation", {}))
    
    # Extract deliverability metrics if available
    bounce_rate = metrics.get("bounce_rate", 0)
    unsubscribe_rate = metrics.get("unsubscribe_rate", 0)
    spam_complaint_rate = metrics.get("spam_complaint_rate", 0)
    
    prompt = f"""You are an expert email marketing strategist analyzing campaign performance data. Provide clear narrative insights with embedded strategic elements.

CLIENT CONTEXT:
- Client: {client_name}
- Industry: {industry}
- Currency: {currency} ({currency_symbol})

CAMPAIGN PERFORMANCE METRICS:
- Open Rate: {open_rate:.2f}% (Benchmark: {benchmark_open:.2f}%)
- Click Rate: {click_rate:.2f}% (Benchmark: {benchmark_click:.2f}%)
- Conversion Rate: {conversion_rate:.2f}% (Benchmark: {benchmark_conv:.2f}%)
- Total Revenue: {currency_symbol}{revenue:,.2f}
- Total Sent: {sent:,}
- Bounce Rate: {bounce_rate:.3f}%
- Unsubscribe Rate: {unsubscribe_rate:.3f}%
- Spam Complaint Rate: {spam_complaint_rate:.3f}%

STRATEGIC ANALYSIS:
- Campaign Pattern: {pattern_diagnosis.get("pattern", "N/A")} - {pattern_diagnosis.get("diagnosis", "No pattern identified")}
- Root Cause: {pattern_diagnosis.get("root_cause", "N/A")}
- Deliverability Status: {deliverability_analysis.get("overall_status", "N/A")}
- Deliverability Issues: {len(deliverability_analysis.get("issues", []))} issue(s) identified
- Segmentation Needed: {"Yes" if segmentation_recommendation.get("needed", False) else "No"}
- Segmentation Reason: {segmentation_recommendation.get("reason", "N/A") if segmentation_recommendation.get("needed", False) else "Not required"}

PROVIDE INSIGHTS IN SIMPLE JSON FORMAT:

{{
    "primary": "Campaign performance analysis: Campaigns showing {open_rate:.1f}% open rate vs {benchmark_open:.1f}% industry benchmark and {click_rate:.1f}% click rate vs {benchmark_click:.1f}% benchmark. Generated {currency_symbol}{revenue:,.0f} in total revenue from {sent:,} emails sent. **Performance Status:** [Assess as Excellent/Good/Needs Improvement/Poor based on benchmarks]. **Quick Wins:** [List 2-3 immediate campaign optimization opportunities with effort/impact estimates]. **Risk Flags:** [Any critical campaign issues requiring urgent attention].",
    "secondary": "Strategic campaign recommendations: **Top Priorities:** [Rank 3 campaign optimization areas by impact]. **Subject Line Optimization:** [Specific recommendations for improving open rates]. **Send Time & Frequency:** [Optimization opportunities for better engagement]. **Segmentation Strategy:** [How to improve targeting and relevance]. Include specific next steps and expected results."
}}

GUIDELINES:
- Include specific numbers and benchmark comparisons
- Embed strategic elements within narrative text using **bold headers**
- Professional consultant tone with actionable insights
- Focus on subject lines, send timing, frequency, and segmentation
- Estimate impact where possible
- Return only the JSON object"""

    return prompt