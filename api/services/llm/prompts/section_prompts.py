"""
Section-specific prompt templates (list growth, automation, data capture, generic).
Simplified to use narrative format with embedded strategic elements.
"""
from typing import Dict, Any
from .base import get_currency_symbol, get_strategic_value_instructions


def get_list_growth_prompt(data: Dict[str, Any], context: Dict[str, Any]) -> str:
    """Generate prompt for list growth analysis."""
    client_name = context.get("client_name", "the client")
    industry = context.get("industry", "retail")
    section_data = data.get("data", {})
    
    current_total = section_data.get("current_total", 0)
    growth_subscribers = section_data.get("growth_subscribers", 0) 
    lost_subscribers = section_data.get("lost_subscribers", 0)
    churn_rate = section_data.get("churn_rate", 0)
    period_months = section_data.get("period_months", 6)
    
    # Get list-revenue correlation from context (added in Phase 3)
    # Context is passed as separate parameter, but also check data.context for backward compatibility
    list_revenue_correlation = context.get("list_revenue_correlation", data.get("context", {}).get("list_revenue_correlation", {}))
    
    prompt = f"""You are an expert email marketing strategist analyzing list growth data. Provide clear narrative insights.

CLIENT CONTEXT:
- Client: {client_name}
- Industry: {industry}
- Analysis Period: {period_months} months

LIST GROWTH METRICS:
- Current Subscribers: {current_total:,}
- New Subscribers: {growth_subscribers:,}
- Lost Subscribers: {lost_subscribers:,}
- Churn Rate: {churn_rate:.2f}%

LIST-REVENUE CORRELATION:
- Connection: {list_revenue_correlation.get("connection", "N/A")}
- Revenue Impact: {list_revenue_correlation.get("revenue_impact", "N/A")}
- Opportunity: {list_revenue_correlation.get("opportunity", "N/A")}

PROVIDE COMPREHENSIVE ANALYSIS IN JSON FORMAT WITH MULTIPLE SUBSECTIONS:

{{
    "list_growth_overview": "A detailed 2-3 paragraph analysis of email list growth. Current subscriber count {current_total:,} with {growth_subscribers:,} new subscribers and {lost_subscribers:,} lost over {period_months} months. Explain what these numbers mean for {client_name}'s list health. Include specific growth rate calculations and period-over-period comparisons if available.",
    
    "growth_drivers": "A detailed 1-2 paragraph analysis of growth drivers. Where are new subscribers coming from? Break down signup sources (forms, campaigns, integrations, etc.) with specific numbers and percentages. Explain which sources are performing best.",
    
    "attrition_sources": "A detailed 1-2 paragraph analysis of attrition sources. Where are subscribers being lost? Break down churn sources (unsubscribes, manual suppressions, bounces, etc.) with specific numbers. Explain what the {churn_rate:.1f}% churn rate means and identify the biggest churn drivers.",
    
    "primary": "List growth overview: Current subscriber count {current_total:,} with {growth_subscribers:,} new subscribers and {lost_subscribers:,} lost over {period_months} months. Churn rate at {churn_rate:.1f}% indicates [assess list health]. **Performance Status:** [Healthy/Concerning/Critical based on growth vs churn]. **Quick Wins:** [2-3 immediate opportunities to reduce churn or increase acquisition]. **Risk Flags:** [Any critical list health issues].",
    
    "secondary": "Strategic list growth recommendations: **Growth Optimization:** [Specific strategies to increase acquisition]. **Churn Reduction:** [Tactics to improve retention]. **Expected Impact:** [Estimate subscriber and revenue impact of optimizations]."
}}

GUIDELINES:
- Each subsection should be 2-3 paragraphs (not just 1 sentence)
- Compare growth rate to industry standards 
- Assess churn rate health (ideal is <2% monthly)
- Be specific with numbers and percentages
- Identify key opportunities for improvement
- Write clear, consultant-style insights
- Return only the JSON object"""

    return prompt


def get_automation_prompt(data: Dict[str, Any], context: Dict[str, Any]) -> str:
    """Generate prompt for automation overview analysis."""
    client_name = context.get("client_name", "the client")
    industry = context.get("industry", "retail")
    currency_code = context.get("currency", "USD")
    currency_symbol = get_currency_symbol(currency_code)
    
    section_data = data.get("data", {})
    total_revenue = section_data.get("total_revenue", 0)
    total_recipients = section_data.get("total_recipients", 0)
    flows = section_data.get("flows", [])
    period_days = section_data.get("period_days", 90)
    
    # Get flow issues from context (added in Phase 2)
    # Context is passed as separate parameter, but also check data.context for backward compatibility
    flow_issues = context.get("flow_issues", data.get("context", {}).get("flow_issues", {}))
    missing_flows = flow_issues.get("missing", [])
    duplicate_flows = flow_issues.get("duplicates", [])
    zero_deliveries = flow_issues.get("zero_deliveries", [])
    
    prompt = f"""You are an expert email marketing strategist analyzing automation performance. Provide clear narrative insights.

CLIENT CONTEXT:
- Client: {client_name}
- Industry: {industry}
- Currency: {currency_code} ({currency_symbol})
- Analysis Period: {period_days} days
- Total Flow Revenue: {currency_symbol}{total_revenue:,.2f}
- Total Recipients: {total_recipients:,}
- Number of Flows: {len(flows)}

FLOW ISSUES DETECTED:
- Missing Flows: {len(missing_flows)} critical flow(s) not found
- Duplicate Flows: {len(duplicate_flows)} duplicate flow type(s) detected
- Zero Deliveries: {len(zero_deliveries)} live flow(s) with zero deliveries

PROVIDE INSIGHTS IN SIMPLE JSON FORMAT:

{{
    "primary": "Automation overview: Flow ecosystem generated {currency_symbol}{total_revenue:,.0f} in revenue from {total_recipients:,} recipients over {period_days} days. **Performance Highlights:** [Key performing flows and metrics]. **Quick Wins:** [2-3 immediate flow optimization opportunities]. **Missing Flows:** [Identify critical missing automation flows].",
    "secondary": "Strategic automation recommendations: **Flow Optimization:** [Specific improvements for existing flows]. **New Flow Opportunities:** [Recommended new automations to implement]. **Revenue Impact:** [Estimate potential revenue increase from optimizations]."
}}

GUIDELINES:
- Focus on overall flow ecosystem performance
- Identify missing critical flows (welcome, abandoned cart, etc.)
- Embed strategic recommendations within narrative text
- Return only the JSON object"""

    return prompt


def get_data_capture_prompt(data: Dict[str, Any], context: Dict[str, Any]) -> str:
    """Generate prompt for data capture/forms analysis."""
    client_name = context.get("client_name", "the client")
    industry = context.get("industry", "retail")
    
    # Get categorized forms from context (added in Phase 2)
    # Context is passed as separate parameter, but also check data.context for backward compatibility
    section_data = data.get("data", {})
    categorized_forms = context.get("categorized_forms", data.get("context", {}).get("categorized_forms", {}))
    high_performers = categorized_forms.get("high_performers", [])
    underperformers = categorized_forms.get("underperformers", [])
    inactive = categorized_forms.get("inactive", [])
    
    prompt = f"""You are an expert email marketing strategist analyzing form performance data. Provide clear narrative insights.

CLIENT CONTEXT:
- Client: {client_name}
- Industry: {industry}

FORM PERFORMANCE SUMMARY:
- Total Forms: {section_data.get("total_forms", 0)}
- Total Impressions: {section_data.get("total_impressions", 0):,}
- Total Submissions: {section_data.get("total_submissions", 0):,}
- Average Submit Rate: {section_data.get("avg_submit_rate", 0):.2f}%

FORM CATEGORIZATION:
- High Performers: {len(high_performers)} form(s) (≥5% submit rate)
- Underperformers: {len(underperformers)} form(s) (<3% submit rate with >100 impressions)
- Inactive Forms: {len(inactive)} form(s) (0 impressions)

PROVIDE COMPREHENSIVE ANALYSIS IN JSON FORMAT WITH MULTIPLE SUBSECTIONS:

{{
    "form_performance_overview": "A detailed 2-3 paragraph analysis of form performance. Total {section_data.get('total_forms', 0)} forms with {section_data.get('total_impressions', 0):,} impressions and {section_data.get('total_submissions', 0):,} submissions. Average submit rate {section_data.get('avg_submit_rate', 0):.2f}%. Explain what these numbers mean for {client_name}'s data capture effectiveness.",
    
    "high_performers_analysis": "A detailed 1-2 paragraph analysis of high-performing forms ({len(high_performers)} forms with ≥5% submit rate). What makes these forms successful? Identify common patterns, design elements, or targeting strategies that drive performance.",
    
    "optimization_opportunities": "A detailed 2-3 paragraph analysis of optimization opportunities. Focus on underperforming forms ({len(underperformers)} forms with <3% submit rate) and inactive forms ({len(inactive)} forms with 0 impressions). What specific improvements could be made?",
    
    "primary": "Form performance overview: Analyze form conversion rates, signup sources, and data capture effectiveness. **Performance Highlights:** [Top performing forms with conversion rates]. **Quick Wins:** [2-3 immediate form optimization opportunities]. **Issues:** [Any underperforming forms needing attention].",
    
    "secondary": "Strategic form recommendations: **Optimization Priorities:** [Rank form improvements by impact]. **New Opportunities:** [Additional forms or targeting strategies]. **Expected Impact:** [Estimate conversion and list growth improvements]."
}}

GUIDELINES:
- Each subsection should be 2-3 paragraphs (not just 1 sentence)
- Focus on form conversion rates and effectiveness
- Identify optimization opportunities
- Embed strategic recommendations within narrative text
- Return only the JSON object"""

    return prompt


def get_generic_prompt(section: str, data: Dict[str, Any], context: Dict[str, Any]) -> str:
    """Generate generic prompt for any section."""
    client_name = context.get("client_name", "the client") 
    
    prompt = f"""You are an expert email marketing strategist analyzing {section} performance data.

CLIENT CONTEXT:
- Client: {client_name}
- Section: {section}

PROVIDE INSIGHTS IN SIMPLE JSON FORMAT:

{{
    "primary": "{section.title()} analysis: Provide overview of performance and key findings. Include specific metrics and insights.",
    "secondary": "Strategic recommendations: Key optimization opportunities and next steps for {section}."
}}

GUIDELINES:
- Professional consultant tone
- Include specific metrics when available  
- Focus on actionable insights
- Return only the JSON object"""

    return prompt