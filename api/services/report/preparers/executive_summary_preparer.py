"""
Executive Summary data preparer.
Creates a comprehensive 1-page executive summary that synthesizes all audit findings.
"""
from typing import Dict, Any, Optional, List
import logging
from ..html_formatter import format_llm_output

logger = logging.getLogger(__name__)


async def prepare_executive_summary_data(
    all_audit_data: Dict[str, Any],
    client_name: str = "the client",
    account_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Prepare comprehensive executive summary data from all audit sections.
    
    This function synthesizes all audit findings into a 1-page executive summary
    that provides key metrics, top priorities, and strategic overview.
    
    Args:
        all_audit_data: Complete audit data from all sections
        client_name: Name of the client
        account_context: Account context including industry, currency, etc.
    
    Returns:
        Dict with executive summary data for template
    """
    
    # Extract key data from all sections
    kav_data = all_audit_data.get("kav_data", {})
    list_growth_data = all_audit_data.get("list_growth_data", {})
    campaign_data = all_audit_data.get("campaign_performance_data", {})
    automation_data = all_audit_data.get("automation_overview_data", {})
    data_capture_data = all_audit_data.get("data_capture_data", {})
    strategic_data = all_audit_data.get("strategic_recommendations_data", {})
    
    # Key metrics for executive summary
    kav_percentage = kav_data.get("revenue", {}).get("attributed_percentage", 0)
    attributed_revenue = kav_data.get("revenue", {}).get("attributed", 0)
    total_revenue = kav_data.get("revenue", {}).get("total_website", 0)
    
    # List health metrics
    current_list_size = list_growth_data.get("current_total", 0)
    list_growth = list_growth_data.get("net_change", 0)
    churn_rate = list_growth_data.get("churn_rate", 0)
    engagement_threshold = list_growth_data.get("engagement_threshold", {})
    
    # Automation health
    automation_summary = automation_data.get("automation_summary", {})
    flows_active = automation_summary.get("flows_active", 0)
    flows_total = automation_summary.get("flows_total", 0)
    
    # Campaign performance
    campaign_summary = campaign_data.get("summary", {})
    avg_open_rate = campaign_summary.get("average_open_rate", 0)
    avg_click_rate = campaign_summary.get("average_click_rate", 0)
    
    # Data capture health
    form_summary = data_capture_data.get("form_summary", {})
    total_forms = form_summary.get("total_forms", 0)
    conversion_rate = form_summary.get("overall_conversion_rate", 0)
    
    # Generate top 3 priorities based on audit findings
    top_priorities = _generate_top_priorities(
        all_audit_data, 
        kav_percentage, 
        engagement_threshold, 
        flows_active, 
        flows_total
    )
    
    # Calculate total opportunity value
    total_opportunity = _calculate_total_opportunity(
        all_audit_data, 
        attributed_revenue, 
        total_revenue
    )
    
    # Generate key insights using LLM if available
    executive_insights = await _generate_executive_insights(
        all_audit_data,
        client_name,
        account_context
    )
    
    # Assess overall health score
    health_score = _calculate_health_score(
        kav_percentage,
        engagement_threshold,
        flows_active,
        flows_total,
        churn_rate
    )
    
    return {
        # Key metrics for display
        "kav_percentage": round(kav_percentage, 1),
        "attributed_revenue": attributed_revenue,
        "total_revenue": total_revenue,
        "kav_benchmark_status": _get_kav_status(kav_percentage),
        
        # List health summary
        "list_size": current_list_size,
        "list_growth": list_growth,
        "list_engagement_percentage": engagement_threshold.get("engaged_percentage", 100),
        "engagement_warning": engagement_threshold.get("warning_threshold", False),
        
        # Automation summary
        "flows_active": flows_active,
        "flows_total": flows_total,
        "automation_health": "healthy" if flows_active >= 4 else "needs_attention",
        
        # Campaign summary
        "avg_open_rate": round(avg_open_rate, 1),
        "avg_click_rate": round(avg_click_rate, 1),
        
        # Data capture summary
        "total_forms": total_forms,
        "form_conversion_rate": round(conversion_rate, 2),
        
        # Strategic elements
        "top_priorities": top_priorities,
        "total_opportunity": total_opportunity,
        "health_score": health_score,
        "executive_insights": executive_insights,
        
        # Period information
        "analysis_period": account_context.get("analysis_period", "Last 6 months") if account_context else "Last 6 months",
        "currency": account_context.get("currency", "USD") if account_context else "USD",
        
        # Risk flags
        "critical_issues": _identify_critical_issues(all_audit_data),
        "quick_wins": _identify_quick_wins(all_audit_data)
    }


def _generate_top_priorities(
    audit_data: Dict[str, Any], 
    kav_percentage: float, 
    engagement_threshold: Dict[str, Any], 
    flows_active: int, 
    flows_total: int
) -> List[Dict[str, Any]]:
    """Generate top 3 priorities based on audit findings."""
    
    priorities = []
    
    # Priority 1: KAV improvement if below threshold
    if kav_percentage < 25:
        priorities.append({
            "title": "Increase Klaviyo Attribution (KAV)",
            "description": f"Current KAV is {kav_percentage:.1f}%, below industry benchmark of 30%. Focus on email capture optimization and flow activation.",
            "impact": f"Could increase attributed revenue by ${(25-kav_percentage) * 1000:,.0f}+ monthly",
            "timeline": "30-60 days"
        })
    
    # Priority 2: Engagement threshold warning
    if engagement_threshold.get("warning_threshold", False):
        unengaged_pct = engagement_threshold.get("unengaged_percentage", 0)
        priorities.append({
            "title": "Address List Engagement Issues",
            "description": f"{unengaged_pct:.1f}% of your list is unengaged (above 20% warning threshold). This impacts deliverability and sender reputation.",
            "impact": "Improve deliverability and email performance",
            "timeline": "14-30 days"
        })
    
    # Priority 3: Missing automation flows
    missing_flows = flows_total - flows_active
    if missing_flows > 0:
        priorities.append({
            "title": "Activate Missing Automation Flows",
            "description": f"{missing_flows} critical automation flows are missing or inactive. These are essential for revenue generation.",
            "impact": f"Could generate ${missing_flows * 2000:,.0f}+ additional monthly revenue",
            "timeline": "30-45 days"
        })
    
    # Priority 4: Data capture optimization (if others are healthy)
    data_capture = audit_data.get("data_capture_data", {})
    form_summary = data_capture.get("form_summary", {})
    if len(priorities) < 3 and form_summary.get("overall_conversion_rate", 0) < 2:
        priorities.append({
            "title": "Optimize Email Capture Forms",
            "description": f"Form conversion rate is {form_summary.get('overall_conversion_rate', 0):.1f}%, below industry average of 2-3%.",
            "impact": "Increase list growth rate and revenue potential",
            "timeline": "15-30 days"
        })
    
    # Priority 5: Campaign optimization (fallback)
    campaign_data = audit_data.get("campaign_performance_data", {})
    campaign_summary = campaign_data.get("summary", {})
    if len(priorities) < 3 and campaign_summary.get("average_open_rate", 0) < 20:
        priorities.append({
            "title": "Improve Campaign Performance",
            "description": f"Campaign open rates averaging {campaign_summary.get('average_open_rate', 0):.1f}% are below industry benchmarks.",
            "impact": "Increase campaign revenue and engagement",
            "timeline": "15-30 days"
        })
    
    # Return top 3 priorities
    return priorities[:3]


def _calculate_total_opportunity(
    audit_data: Dict[str, Any], 
    current_attributed: float, 
    total_revenue: float
) -> Dict[str, Any]:
    """Calculate total revenue opportunity from implementing recommendations."""
    
    # Conservative estimates based on industry improvements
    kav_data = audit_data.get("kav_data", {})
    current_kav = kav_data.get("revenue", {}).get("attributed_percentage", 0)
    
    # Opportunity from KAV improvement
    kav_opportunity = 0
    if current_kav < 30:
        # Conservative: 5-10% improvement possible
        potential_kav_increase = min(10, 30 - current_kav)
        kav_opportunity = (potential_kav_increase / 100) * total_revenue
    
    # Opportunity from list engagement improvement
    engagement_opportunity = 0
    list_data = audit_data.get("list_growth_data", {})
    engagement_threshold = list_data.get("engagement_threshold", {})
    if engagement_threshold.get("warning_threshold", False):
        # Improving engagement typically increases revenue by 15-25%
        engagement_opportunity = current_attributed * 0.15
    
    # Opportunity from missing flows
    automation_opportunity = 0
    automation_data = audit_data.get("automation_overview_data", {})
    automation_summary = automation_data.get("automation_summary", {})
    flows_active = automation_summary.get("flows_active", 0)
    if flows_active < 4:  # Missing critical flows
        missing_flows = 4 - flows_active
        # Each critical flow typically generates 5-10% of total email revenue
        automation_opportunity = current_attributed * (missing_flows * 0.07)
    
    total_annual_opportunity = (kav_opportunity + engagement_opportunity + automation_opportunity)
    
    return {
        "annual_revenue": round(total_annual_opportunity, 0),
        "monthly_revenue": round(total_annual_opportunity / 12, 0),
        "kav_component": round(kav_opportunity, 0),
        "engagement_component": round(engagement_opportunity, 0),
        "automation_component": round(automation_opportunity, 0),
        "confidence": "conservative" if total_annual_opportunity > 0 else "low"
    }


async def _generate_executive_insights(
    audit_data: Dict[str, Any],
    client_name: str,
    account_context: Optional[Dict[str, Any]]
) -> str:
    """Generate executive insights using LLM if available."""
    
    try:
        from ...llm import LLMService
        from ...llm.formatter import LLMDataFormatter
        
        # Initialize LLM service
        llm_config = account_context.get("llm_config", {}) if account_context else {}
        llm_service = LLMService(
            default_provider=llm_config.get("provider", "claude"),
            anthropic_api_key=llm_config.get("anthropic_api_key"),
            openai_api_key=llm_config.get("openai_api_key"),
            gemini_api_key=llm_config.get("gemini_api_key"),
            claude_model=llm_config.get("claude_model"),
            openai_model=llm_config.get("openai_model"),
            gemini_model=llm_config.get("gemini_model"),
            llm_config=llm_config if llm_config else None
        )
        
        # Format audit data for LLM
        formatted_data = LLMDataFormatter.format_for_generic_analysis(
            section="executive_summary",
            data=audit_data,
            client_context={
                "client_name": client_name,
                "industry": account_context.get("industry", "retail") if account_context else "retail",
                "currency": account_context.get("currency", "USD") if account_context else "USD"
            }
        )
        
        # Generate executive summary insights
        insights = await llm_service.generate_insights(
            section="executive_summary",
            data=formatted_data,
            context=formatted_data.get("context", {})
        )
        
        # Extract and format the primary executive insight
        primary_insight = insights.get("primary", "")
        if isinstance(primary_insight, str):
            return format_llm_output(primary_insight) if primary_insight else ""
        else:
            return format_llm_output(str(primary_insight)) if primary_insight else ""
            
    except Exception as e:
        logger.warning(f"LLM service unavailable for executive insights, using fallback: {e}")
        
        # Create fallback insight based on data
        kav_data = audit_data.get("kav_data", {})
        kav_percentage = kav_data.get("revenue", {}).get("attributed_percentage", 0)
        
        if kav_percentage < 20:
            return f"<p><strong>{client_name}</strong> has significant opportunity to improve email marketing attribution. With KAV at {kav_percentage:.1f}%, there's potential to capture more revenue through better email capture, segmentation, and automation flow optimization.</p>"
        elif kav_percentage >= 30:
            return f"<p><strong>{client_name}</strong> shows strong email marketing performance with {kav_percentage:.1f}% KAV. Focus should be on optimization and scaling current successful strategies while addressing any engagement or deliverability issues.</p>"
        else:
            return f"<p><strong>{client_name}</strong> has a solid email marketing foundation with {kav_percentage:.1f}% KAV. Key opportunities exist in automation, list growth, and campaign optimization to reach industry-leading performance levels.</p>"


def _calculate_health_score(
    kav_percentage: float,
    engagement_threshold: Dict[str, Any],
    flows_active: int,
    flows_total: int,
    churn_rate: float
) -> Dict[str, Any]:
    """Calculate overall email marketing health score."""
    
    score = 0
    max_score = 100
    
    # KAV component (30 points)
    if kav_percentage >= 30:
        score += 30
    elif kav_percentage >= 25:
        score += 25
    elif kav_percentage >= 20:
        score += 20
    elif kav_percentage >= 15:
        score += 15
    elif kav_percentage >= 10:
        score += 10
    
    # Engagement component (25 points)
    if not engagement_threshold.get("warning_threshold", False):
        score += 25
    elif engagement_threshold.get("unengaged_percentage", 0) < 25:
        score += 15
    elif engagement_threshold.get("unengaged_percentage", 0) < 30:
        score += 10
    
    # Automation component (25 points)
    if flows_active >= 4:
        score += 25
    elif flows_active >= 3:
        score += 20
    elif flows_active >= 2:
        score += 15
    elif flows_active >= 1:
        score += 10
    
    # Churn component (20 points)
    if churn_rate < 10:
        score += 20
    elif churn_rate < 15:
        score += 15
    elif churn_rate < 20:
        score += 10
    elif churn_rate < 25:
        score += 5
    
    # Determine health status
    if score >= 80:
        status = "excellent"
    elif score >= 60:
        status = "good"
    elif score >= 40:
        status = "fair"
    else:
        status = "needs_improvement"
    
    return {
        "score": score,
        "max_score": max_score,
        "percentage": round((score / max_score) * 100, 0),
        "status": status,
        "grade": _get_letter_grade(score)
    }


def _get_kav_status(kav_percentage: float) -> str:
    """Get KAV benchmark status."""
    if kav_percentage >= 30:
        return "excellent"
    elif kav_percentage >= 25:
        return "good"
    elif kav_percentage >= 20:
        return "fair"
    else:
        return "needs_improvement"


def _get_letter_grade(score: int) -> str:
    """Convert numeric score to letter grade."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def _identify_critical_issues(audit_data: Dict[str, Any]) -> List[str]:
    """Identify critical issues that need immediate attention."""
    
    issues = []
    
    # Critical KAV issues
    kav_data = audit_data.get("kav_data", {})
    kav_percentage = kav_data.get("revenue", {}).get("attributed_percentage", 0)
    if kav_percentage < 15:
        issues.append("Critically low KAV - email attribution below 15%")
    
    # Critical engagement issues
    list_data = audit_data.get("list_growth_data", {})
    engagement_threshold = list_data.get("engagement_threshold", {})
    if engagement_threshold.get("unengaged_percentage", 0) > 30:
        issues.append("Severe list engagement issues - over 30% unengaged")
    
    # Critical automation issues
    automation_data = audit_data.get("automation_overview_data", {})
    automation_summary = automation_data.get("automation_summary", {})
    flows_active = automation_summary.get("flows_active", 0)
    if flows_active < 2:
        issues.append("Critical automation gaps - fewer than 2 active flows")
    
    # Critical deliverability issues
    if list_data.get("spam_percentage", 0) > 2:
        issues.append("Deliverability risk - spam complaint rate above 2%")
    
    return issues


def _identify_quick_wins(audit_data: Dict[str, Any]) -> List[str]:
    """Identify quick wins that can be implemented immediately."""
    
    quick_wins = []
    
    # Form optimization quick wins
    data_capture = audit_data.get("data_capture_data", {})
    form_summary = data_capture.get("form_summary", {})
    if form_summary.get("total_forms", 0) < 3:
        quick_wins.append("Add email capture forms to high-traffic pages")
    
    # Campaign frequency optimization
    campaign_data = audit_data.get("campaign_performance_data", {})
    if campaign_data.get("send_frequency_analysis", {}).get("recommendation"):
        quick_wins.append("Optimize email send frequency based on engagement data")
    
    # Missing flow activation
    automation_data = audit_data.get("automation_overview_data", {})
    flow_issues = automation_data.get("flow_issues", [])
    for issue in flow_issues[:2]:  # Top 2 flow issues
        if "missing" in issue.get("issue", "").lower():
            quick_wins.append(f"Activate {issue.get('flow_name', 'critical')} automation flow")
    
    # List hygiene
    list_data = audit_data.get("list_growth_data", {})
    engagement_threshold = list_data.get("engagement_threshold", {})
    if engagement_threshold.get("warning_threshold", False):
        quick_wins.append("Implement re-engagement campaign for unengaged subscribers")
    
    return quick_wins[:3]  # Top 3 quick wins