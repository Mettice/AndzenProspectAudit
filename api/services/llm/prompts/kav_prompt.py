"""
KAV (Klaviyo Attributed Value) prompt templates.
Enhanced with strategic value elements: ROI, quick wins, risk flags, root cause analysis.
"""
from typing import Dict, Any
from .base import get_currency_symbol, get_strategic_value_instructions, get_json_output_instructions


def get_kav_prompt(data: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Generate prompt for KAV (Klaviyo Attributed Value) analysis.
    
    Enhanced with:
    - ROI & impact quantification
    - Quick wins identification
    - Risk flags
    - Root cause analysis
    """
    metrics = data.get("metrics", {})
    client_name = context.get("client_name", "the client")
    industry = context.get("industry", "retail")
    date_range = context.get("date_range", "the reporting period")
    currency = context.get("currency", "USD")
    timezone = context.get("timezone", "UTC")
    
    currency_symbol = get_currency_symbol(currency)
    
    # Extract key metrics
    total_revenue = metrics.get("total_revenue", 0)
    attributed_revenue = metrics.get("attributed_revenue", 0)
    kav_percentage = metrics.get("kav_percentage", 0)
    flow_percentage = metrics.get("flow_percentage", 0)
    campaign_percentage = metrics.get("campaign_percentage", 0)
    
    # Benchmarks
    kav_benchmark = context.get("kav_benchmark", 30.0)
    
    # Calculate potential revenue impact
    potential_kav = total_revenue * (kav_benchmark / 100)
    revenue_opportunity = potential_kav - attributed_revenue
    
    # Get KAV interpretation from context (added in Phase 3)
    # Context is passed as separate parameter, but also check data.context for backward compatibility
    kav_interpretation = context.get("kav_interpretation", data.get("context", {}).get("kav_interpretation", {}))
    
    prompt = f"""You are an expert email marketing strategist analyzing Klaviyo performance data. Provide clear narrative insights like the strategist would after reviewing dashboard screenshots.

CLIENT CONTEXT:
- Client: {client_name}
- Industry: {industry} 
- Date Range: {date_range}
- Currency: {currency} ({currency_symbol})

KLAVIYO ATTRIBUTED VALUE (KAV) METRICS:
- Total Revenue: {currency_symbol}{total_revenue:,.2f}
- Attributed Revenue (KAV): {currency_symbol}{attributed_revenue:,.2f}
- KAV Percentage: {kav_percentage:.1f}%
- Industry Benchmark: {kav_benchmark}%
- Flow Revenue: {currency_symbol}{attributed_revenue * (flow_percentage/100):,.2f} ({flow_percentage:.1f}% of attributed)
- Campaign Revenue: {currency_symbol}{attributed_revenue * (campaign_percentage/100):,.2f} ({campaign_percentage:.1f}% of attributed)
- Revenue Opportunity: {currency_symbol}{revenue_opportunity:,.2f} if KAV reaches benchmark

STRATEGIC INTERPRETATION:
- Thesis: {kav_interpretation.get("thesis", "N/A")}
- Opportunity: {kav_interpretation.get("opportunity", "N/A")}
- KAV Status: {kav_interpretation.get("kav_status", "N/A")}
- KAV Opportunity: {kav_interpretation.get("kav_opportunity", "N/A")}
- Priority: {kav_interpretation.get("priority", "N/A")}

PROVIDE INSIGHTS IN SIMPLE JSON FORMAT:

{{
    "primary": "A comprehensive KAV performance overview: Current performance at {kav_percentage:.1f}% KAV ({currency_symbol}{attributed_revenue:,.0f} attributed from {currency_symbol}{total_revenue:,.0f} total revenue) compared to {kav_benchmark}% industry benchmark. Flow vs Campaign split is {flow_percentage:.1f}% flows to {campaign_percentage:.1f}% campaigns. Analyze what this means for {client_name}'s email marketing effectiveness and identify the biggest opportunities for improvement. Include specific revenue impact estimates where possible.",
    "secondary": "Strategic recommendations for improving KAV: Focus on the highest-impact optimizations that could move KAV closer to benchmark. Include specific next steps and estimated revenue impact. Keep recommendations practical and prioritized."
}}

GUIDELINES:
- Write clear, consultant-style insights like you would after reviewing dashboard screenshots
- Be specific with numbers and percentages  
- Compare to industry benchmarks
- Identify 2-3 key opportunities with revenue estimates
- Keep language professional but accessible
- Focus on actionable insights
- Return only the JSON object, no markdown formatting"""

    return prompt
