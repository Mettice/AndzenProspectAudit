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

PROVIDE COMPREHENSIVE ANALYSIS IN JSON FORMAT WITH MULTIPLE SUBSECTIONS:

{{
    "growth_overview": "A detailed 2-3 paragraph analysis of KAV growth and performance trends. Include year-over-year or period-over-period comparisons if available. Explain what the current {kav_percentage:.1f}% KAV means in context of the industry benchmark ({kav_benchmark}%) and {client_name}'s business. Highlight key growth drivers and any concerning trends.",
    
    "campaigns_vs_flows": "A detailed 2-3 paragraph breakdown of the Campaign vs Flows revenue split ({campaign_percentage:.1f}% campaigns, {flow_percentage:.1f}% flows). Explain what this balance means for {client_name}'s marketing strategy. Is this optimal? What does the split indicate about automation maturity? Include specific revenue numbers: Campaign revenue {currency_symbol}{attributed_revenue * (campaign_percentage/100):,.2f}, Flow revenue {currency_symbol}{attributed_revenue * (flow_percentage/100):,.2f}.",
    
    "flow_performance_insights": "A dedicated 1-2 paragraph analysis specifically about flow performance. What do the flow metrics tell us about {client_name}'s automation effectiveness? Are flows performing well? What opportunities exist to expand or optimize flows?",
    
    "campaign_performance_insights": "A dedicated 1-2 paragraph analysis specifically about campaign performance. What do the campaign metrics tell us about {client_name}'s campaign strategy? Are campaigns performing well? What opportunities exist to improve campaign effectiveness?",
    
    "kav_implications": "A 2-3 bullet point analysis of 'What This Means for KAV Performance'. Connect the dots between the metrics and explain the strategic implications. What should {client_name} prioritize?",
    
    "growing_your_kav": {{
        "reignite_campaigns": {{
            "objective": "Clear objective statement for improving campaign performance",
            "actions": ["Action item 1 with specific details", "Action item 2 with specific details", "Action item 3 with specific details"]
        }},
        "strengthen_flows": "A 2-paragraph strategic recommendation for strengthening and expanding flow strategy. Include specific flow types to add or optimize.",
        "foundation_for_growth": "A detailed paragraph about setting the foundation for scalable growth. What foundational elements need to be in place?"
    }},
    
    "primary": "A comprehensive 2-3 paragraph KAV performance overview summarizing the key findings from all subsections above.",
    "secondary": "Strategic recommendations for improving KAV: Focus on the highest-impact optimizations that could move KAV closer to benchmark. Include specific next steps and estimated revenue impact."
}}

GUIDELINES:
- Write clear, consultant-style insights like you would after reviewing dashboard screenshots
- Each subsection should be 2-3 paragraphs (not just 1 sentence)
- Be specific with numbers and percentages  
- Compare to industry benchmarks
- Include year-over-year comparisons if data suggests trends
- Identify 3-5 key opportunities with revenue estimates
- Keep language professional but accessible
- Focus on actionable insights
- Return only the JSON object, no markdown formatting
- The "growing_your_kav" section should match the sample audit format with objectives and action items"""

    return prompt
