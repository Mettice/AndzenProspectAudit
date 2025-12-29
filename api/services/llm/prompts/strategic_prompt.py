"""
Strategic recommendations prompt templates.
Enhanced with comprehensive strategic value elements: ROI, quick wins, risk flags, implementation roadmaps.
"""
from typing import Dict, Any
from .base import format_data_for_prompt, get_currency_symbol, get_strategic_value_instructions, get_json_output_instructions


def get_strategic_recommendations_prompt(data: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Generate prompt for strategic recommendations section.
    
    This synthesizes all audit findings into high-level strategic recommendations.
    Enhanced with comprehensive strategic value elements.
    """
    client_name = context.get("client_name", "the client")
    industry = context.get("industry", "retail")
    currency = context.get("currency", "USD")
    currency_symbol = get_currency_symbol(currency)
    
    # Extract key metrics from audit data
    kav_data = data.get("kav_data", {})
    campaign_data = data.get("campaign_performance_data", {})
    flow_data = data.get("automation_overview_data", {})
    list_growth = data.get("list_growth_data", {})
    
    # Get key metrics
    kav_percentage = kav_data.get("kav_percentage", 0) if kav_data else 0
    total_revenue = kav_data.get("total_revenue", 0) if kav_data else 0
    attributed_revenue = kav_data.get("attributed_revenue", 0) if kav_data else 0
    
    avg_open_rate = campaign_data.get("summary", {}).get("avg_open_rate", 0) if campaign_data else 0
    avg_click_rate = campaign_data.get("summary", {}).get("avg_click_rate", 0) if campaign_data else 0
    
    prompt = f"""You are an expert email marketing strategist providing high-level strategic recommendations for a comprehensive Klaviyo audit report.

CLIENT CONTEXT:
- Client: {client_name}
- Industry: {industry}
- Currency: {currency} ({currency_symbol})
- Analysis Period: Last 3 months (90 days)

KEY PERFORMANCE METRICS:
- KAV Percentage: {kav_percentage:.1f}% of total revenue
- Total Revenue: {currency_symbol}{total_revenue:,.2f}
- Attributed Revenue: {currency_symbol}{attributed_revenue:,.2f}
- Average Campaign Open Rate: {avg_open_rate:.2f}%
- Average Campaign Click Rate: {avg_click_rate:.2f}%

AUDIT FINDINGS SUMMARY:
{format_data_for_prompt(data)}

{get_strategic_value_instructions()}

YOUR TASK:
Based on the comprehensive audit findings above, provide strategic recommendations in the following JSON format. This should be a high-level synthesis of all findings, focusing on the most impactful opportunities for growth and optimization.

{{
    "executive_summary": "A comprehensive 8-12 sentence executive summary synthesizing all audit findings. Highlight the most critical insights, overall performance status, and the biggest opportunities for improvement. Be specific with numbers and percentages. Structure with: Overall Performance Assessment (2-3 sentences), Key Strengths (2-3 sentences), Critical Opportunities (2-3 sentences), and Strategic Direction (2-3 sentences). DO NOT truncate - provide complete analysis.",
    "quick_wins": [
        {{
            "title": "Quick Win Title (e.g., 'Optimize Email Send Times')",
            "description": "Detailed description of the quick win opportunity",
            "effort": "Time required (e.g., '2 hours', '1 week')",
            "impact": "Expected impact with revenue estimates (e.g., '15-20% increase in open rates', '$5K/month revenue recovery')",
            "roi": "ROI percentage (e.g., '2500%')",
            "timeline": "Implementation timeline (e.g., '1-2 weeks')",
            "steps": ["Step 1: Action", "Step 2: Action"]
        }}
    ],
    "risk_flags": [
        {{
            "severity": "critical|high|medium|low",
            "issue": "Specific risk or problem (e.g., 'Abandoned cart flow broken')",
            "impact": "Revenue impact if not fixed (e.g., 'Losing $5K/month')",
            "urgency": "Timeline for action (e.g., 'Fix within 7 days')",
            "recommended_action": "What to do to fix it"
        }}
    ],
    "recommendations": {{
        "tier_1_critical": [
            {{
                "title": "Critical Recommendation Title",
                "description": "Detailed description of the critical recommendation",
                "rationale": "Why this is critical based on the audit findings",
                "revenue_impact": "Expected revenue impact with specific numbers (e.g., '$25K/year', '$5K/month recovery')",
                "effort_hours": "Estimated hours required (e.g., 20)",
                "roi": "ROI percentage (e.g., '1250%')",
                "payback_period": "Time to see results (e.g., '1 month')",
                "implementation_steps": ["Step 1: Detailed action", "Step 2: Detailed action", "Step 3: Detailed action"],
                "dependencies": "What must be done first (if any)"
            }}
        ],
        "tier_2_high_impact": [
            {{
                "title": "High Impact Recommendation Title",
                "description": "Detailed description of the high-impact recommendation",
                "rationale": "Why this has high impact potential",
                "revenue_impact": "Expected revenue impact with specific numbers",
                "effort_hours": "Estimated hours required",
                "roi": "ROI percentage",
                "payback_period": "Time to see results",
                "implementation_steps": ["Step 1", "Step 2", "Step 3"],
                "dependencies": "What must be done first (if any)"
            }}
        ],
        "tier_3_strategic": [
            {{
                "title": "Strategic Recommendation Title",
                "description": "Detailed description of the strategic recommendation",
                "rationale": "Long-term strategic value",
                "revenue_impact": "Expected revenue impact with specific numbers",
                "effort_hours": "Estimated hours required",
                "roi": "ROI percentage",
                "payback_period": "Time to see results",
                "implementation_steps": ["Step 1", "Step 2", "Step 3"],
                "dependencies": "What must be done first (if any)"
            }}
        ]
    }},
    "total_revenue_impact": "Estimated total revenue impact in dollars (e.g., 500000) or 0 if not calculable",
    "implementation_roadmap": {{
        "phase_1_quick_wins": [
            {{
                "title": "Quick Win Title",
                "timeline": "1-2 weeks",
                "dependencies": "None"
            }}
        ],
        "phase_2_optimizations": [
            {{
                "title": "Optimization Title",
                "timeline": "1-3 months",
                "dependencies": "May require Phase 1 completion"
            }}
        ],
        "phase_3_strategic": [
            {{
                "title": "Strategic Initiative Title",
                "timeline": "3-6 months",
                "dependencies": "Requires foundation from Phase 1 & 2"
            }}
        ]
    }},
    "next_steps": [
        "Immediate next step 1 (e.g., 'Review and prioritize recommendations with team')",
        "Immediate next step 2 (e.g., 'Begin implementation of Tier 1 critical recommendations')",
        "Immediate next step 3 (e.g., 'Schedule follow-up audit in 90 days')"
    ]
}}

CRITICAL REQUIREMENTS:
1. DO NOT mention "Contact Andzen" or "schedule consultation" - you ARE the strategist
2. Provide specific, actionable recommendations based on the audit data
3. Include specific numbers and percentages from the audit findings
4. Structure recommendations by priority (critical, high impact, strategic)
5. Provide implementation steps for each recommendation
6. Estimate revenue impact where possible (use conservative estimates)
7. Match the professional, consultant-style tone of comprehensive audits
8. DO NOT truncate text - provide complete, full sentences
9. Focus on actionable insights, not generic advice
10. Synthesize findings from all sections (KAV, campaigns, flows, list growth, etc.)
11. For each recommendation, include: revenue impact, effort, ROI, payback period
12. Identify at least 2-3 quick wins (high impact, low effort)
13. Flag all critical risks requiring urgent attention
14. Provide a clear implementation roadmap with phases and dependencies
15. Calculate total revenue impact potential across all recommendations

{get_json_output_instructions()}

Provide your strategic recommendations as valid JSON now:"""
    
    return prompt

