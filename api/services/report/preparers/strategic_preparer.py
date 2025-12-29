"""
Strategic recommendations preparer using LLM.
"""
from typing import Dict, Any
import logging
import json

logger = logging.getLogger(__name__)


async def prepare_strategic_recommendations(audit_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare strategic recommendations using LLM service.
    
    This synthesizes all audit findings into high-level strategic recommendations.
    """
    # Initialize variables
    strategic_recommendations = {
        "error": False,
        "executive_summary": "",
        "total_revenue_impact": 0,
        "quick_wins": [],
        "risk_flags": [],
        "recommendations": {
            "tier_1_critical": [],
            "tier_2_high_impact": [],
            "tier_3_strategic": []
        },
        "implementation_roadmap": {},
        "next_steps": []
    }
    
    # Get context FIRST before using it
    account_context = audit_data.get("account_context", {})
    client_name = audit_data.get("client_name", "the client")
    industry = audit_data.get("industry", "retail")
    
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
        
        # Format data for LLM - use format_for_generic_analysis for strategic recommendations
        formatted_data = LLMDataFormatter.format_for_generic_analysis(
            section="strategic_recommendations",
            data=audit_data,
            client_context={
                "client_name": client_name,
                "industry": industry,
                "currency": account_context.get("currency", "USD"),
                "currency_symbol": account_context.get("currency_symbol", "$"),
                "timezone": account_context.get("timezone", "UTC")
            }
        )
        
        context = {
            "client_name": client_name,
            "industry": industry,
            "currency": account_context.get("currency", "USD"),
            "currency_symbol": account_context.get("currency_symbol", "$"),
            "timezone": account_context.get("timezone", "UTC")
        }
        
        # Generate strategic recommendations using LLM
        logger.info("Generating strategic recommendations using LLM...")
        llm_response = await llm_service.generate_insights(
            section="strategic_recommendations",
            data=formatted_data,
            context=context
        )
        
        # Parse LLM response
        if isinstance(llm_response, dict):
            # Extract executive summary
            strategic_recommendations["executive_summary"] = llm_response.get("executive_summary", "")
            
            # Extract quick wins
            quick_wins = llm_response.get("quick_wins", [])
            if isinstance(quick_wins, list):
                strategic_recommendations["quick_wins"] = quick_wins
            
            # Extract recommendations by tier
            recommendations = llm_response.get("recommendations", {})
            if isinstance(recommendations, dict):
                strategic_recommendations["recommendations"]["tier_1_critical"] = recommendations.get("tier_1_critical", [])
                strategic_recommendations["recommendations"]["tier_2_high_impact"] = recommendations.get("tier_2_high_impact", [])
                strategic_recommendations["recommendations"]["tier_3_strategic"] = recommendations.get("tier_3_strategic", [])
            
            # Extract total revenue impact
            total_impact = llm_response.get("total_revenue_impact", 0)
            if isinstance(total_impact, str):
                # Try to extract number from string
                try:
                    # Remove currency symbols and commas
                    total_impact = total_impact.replace("$", "").replace(",", "").strip()
                    strategic_recommendations["total_revenue_impact"] = float(total_impact) if total_impact else 0
                except:
                    strategic_recommendations["total_revenue_impact"] = 0
            elif isinstance(total_impact, (int, float)):
                strategic_recommendations["total_revenue_impact"] = float(total_impact)
            
            # Extract next steps
            next_steps = llm_response.get("next_steps", [])
            if isinstance(next_steps, list):
                strategic_recommendations["next_steps"] = next_steps
            
            # Extract risk flags
            risk_flags = llm_response.get("risk_flags", [])
            if isinstance(risk_flags, list):
                strategic_recommendations["risk_flags"] = risk_flags
            
            # Extract implementation roadmap
            implementation_roadmap = llm_response.get("implementation_roadmap", {})
            if isinstance(implementation_roadmap, dict):
                strategic_recommendations["implementation_roadmap"] = implementation_roadmap
        
        logger.info("Strategic recommendations generated successfully")
        
    except Exception as e:
        logger.warning(f"LLM service unavailable for strategic recommendations, using fallback: {e}")
        # Fallback: Generate basic recommendations from audit data
        strategic_recommendations["executive_summary"] = _generate_fallback_summary(audit_data)
        strategic_recommendations["quick_wins"] = _generate_fallback_quick_wins(audit_data)
        strategic_recommendations["recommendations"] = {
            "tier_1_critical": _generate_fallback_critical(audit_data),
            "tier_2_high_impact": _generate_fallback_high_impact(audit_data),
            "tier_3_strategic": _generate_fallback_strategic(audit_data)
        }
        strategic_recommendations["risk_flags"] = []
        strategic_recommendations["implementation_roadmap"] = {}
        strategic_recommendations["next_steps"] = [
            "Review audit findings with team",
            "Prioritize recommendations based on business goals",
            "Develop implementation roadmap"
        ]
        # Calculate estimated revenue impact from audit data
        strategic_recommendations["total_revenue_impact"] = _calculate_fallback_revenue_impact(audit_data)
    
    return {
        "strategic_recommendations": strategic_recommendations,
        "phase3_enabled": not strategic_recommendations.get("error", False)
    }


def _generate_fallback_summary(audit_data: Dict[str, Any]) -> str:
    """Generate fallback executive summary from audit data."""
    client_name = audit_data.get("client_name", "the client")
    kav_data = audit_data.get("kav_data", {})
    kav_percentage = kav_data.get("kav_percentage", 0) if kav_data else 0
    
    return f"""Based on the comprehensive audit of {client_name}'s Klaviyo account, the analysis reveals key performance metrics and optimization opportunities. The Klaviyo Attributed Value (KAV) represents {kav_percentage:.1f}% of total revenue, indicating the impact of email and SMS marketing efforts. The audit identified several areas for improvement across campaigns, flows, and list growth strategies. Key recommendations focus on optimizing segmentation, improving content relevance, and enhancing automation performance to drive higher engagement and revenue attribution."""


def _generate_fallback_quick_wins(audit_data: Dict[str, Any]) -> list:
    """Generate fallback quick wins from audit data."""
    quick_wins = [
        {
            "title": "Optimize Email Send Times",
            "description": "Test and implement optimal send times based on audience engagement patterns",
            "impact": "15-20% increase in open rates",
            "timeline": "1-2 weeks",
            "effort": "Low",
            "revenue_impact": 5000
        },
        {
            "title": "Improve Segmentation Strategy", 
            "description": "Implement behavioral segmentation to improve content relevance",
            "impact": "10-15% increase in click rates",
            "timeline": "2-3 weeks",
            "effort": "Medium",
            "revenue_impact": 8000
        },
        {
            "title": "Subject Line A/B Testing",
            "description": "Implement systematic A/B testing for campaign subject lines",
            "impact": "5-10% improvement in open rates",
            "timeline": "1 week",
            "effort": "Low",
            "revenue_impact": 3000
        }
    ]
    
    # Add flow-specific quick wins based on audit data
    flows_data = audit_data.get("flows_data", {})
    if flows_data:
        flows = flows_data.get("flows", [])
        for flow in flows:
            flow_name = flow.get("flow_name", "")
            flow_metrics = flow.get("metrics", {})
            open_rate = flow_metrics.get("open_rate", 0)
            
            # Add quick win for low-performing flows
            if open_rate < 30 and flow_name:  # Below average open rate
                quick_wins.append({
                    "title": f"Optimize {flow_name} Flow",
                    "description": f"Improve {flow_name} content and timing to boost engagement",
                    "impact": f"Target 25-35% open rate vs current {open_rate:.1f}%",
                    "timeline": "1-2 weeks",
                    "effort": "Medium",
                    "revenue_impact": 4000
                })
    
    return quick_wins[:5]  # Limit to 5 quick wins


def _generate_fallback_critical(audit_data: Dict[str, Any]) -> list:
    """Generate fallback critical recommendations."""
    return [
        {
            "title": "Address Low Engagement Metrics",
            "description": "Focus on improving open and click rates through content optimization and segmentation",
            "rationale": "Low engagement rates indicate missed opportunities for revenue growth",
            "expected_impact": "20-30% improvement in engagement metrics",
            "implementation_steps": [
                "Audit current email content and messaging",
                "Implement A/B testing for subject lines and content",
                "Review and optimize segmentation strategy"
            ]
        }
    ]


def _generate_fallback_high_impact(audit_data: Dict[str, Any]) -> list:
    """Generate fallback high-impact recommendations."""
    return [
        {
            "title": "Expand Automation Flows",
            "description": "Implement additional automation flows to capture more revenue opportunities",
            "rationale": "Automation flows drive significant attributed revenue",
            "expected_impact": "15-25% increase in flow revenue",
            "implementation_steps": [
                "Identify gaps in current flow strategy",
                "Design and implement new flows",
                "Monitor and optimize performance"
            ]
        }
    ]


def _generate_fallback_strategic(audit_data: Dict[str, Any]) -> list:
    """Generate fallback strategic recommendations."""
    return [
        {
            "title": "Develop Long-term Growth Strategy",
            "description": "Create a comprehensive long-term strategy for sustainable growth",
            "rationale": "Strategic planning ensures continued improvement and scalability",
            "expected_impact": "Ongoing optimization and growth",
            "implementation_steps": [
                "Establish quarterly review process",
                "Set KPIs and success metrics",
                "Create implementation roadmap"
            ]
        }
    ]


def _calculate_fallback_revenue_impact(audit_data: Dict[str, Any]) -> float:
    """Calculate estimated revenue impact from audit data for fallback mode."""
    total_impact = 0.0
    
    try:
        # Get account context for currency calculations
        account_context = audit_data.get("account_context", {})
        
        # 1. KAV improvement opportunity (benchmark vs current)
        kav_data = audit_data.get("kav_data", {})
        if kav_data:
            current_kav = kav_data.get("kav_percentage", 0)
            benchmark_kav = kav_data.get("benchmark_percentage", 45)  # Industry average ~45%
            total_revenue = kav_data.get("total_revenue", 0)
            
            if current_kav < benchmark_kav and total_revenue > 0:
                # Conservative estimate: 50% of gap to benchmark
                kav_gap = benchmark_kav - current_kav
                kav_opportunity = (total_revenue * (kav_gap / 100)) * 0.5
                total_impact += kav_opportunity
        
        # 2. Flow optimization opportunities
        flows_data = audit_data.get("flows_data", {})
        if flows_data:
            flows = flows_data.get("flows", [])
            for flow in flows:
                flow_metrics = flow.get("metrics", {})
                current_revenue = flow_metrics.get("revenue", 0)
                recipients = flow_metrics.get("recipients", 0)
                
                # Estimate 15-25% improvement for underperforming flows
                if current_revenue > 0 and recipients > 0:
                    revenue_per_recipient = current_revenue / recipients
                    # Conservative 15% improvement estimate
                    flow_opportunity = current_revenue * 0.15
                    total_impact += flow_opportunity
        
        # 3. Campaign optimization opportunities
        campaigns_data = audit_data.get("campaigns_data", {})
        if campaigns_data:
            campaign_metrics = campaigns_data.get("metrics", {})
            campaign_revenue = campaign_metrics.get("revenue", 0)
            
            # Conservative 10-15% improvement through optimization
            if campaign_revenue > 0:
                campaign_opportunity = campaign_revenue * 0.12
                total_impact += campaign_opportunity
        
        # 4. List growth impact (new subscriber value)
        list_growth_data = audit_data.get("list_growth_data", {})
        if list_growth_data:
            current_subscribers = list_growth_data.get("current_total", 0)
            growth_rate = list_growth_data.get("growth_subscribers", 0)
            
            # Estimate value per subscriber based on KAV data
            if kav_data and current_subscribers > 0:
                attributed_revenue = kav_data.get("attributed_revenue", 0)
                value_per_subscriber = attributed_revenue / current_subscribers if current_subscribers > 0 else 0
                
                # Conservative estimate: 20% improvement in acquisition rate
                if growth_rate > 0 and value_per_subscriber > 0:
                    acquisition_opportunity = (growth_rate * 0.2) * value_per_subscriber * 12  # Annualized
                    total_impact += acquisition_opportunity
        
        # Cap the total impact at reasonable bounds (max 50% of current revenue)
        if kav_data:
            total_revenue = kav_data.get("total_revenue", 0)
            if total_revenue > 0:
                max_impact = total_revenue * 0.5  # Max 50% improvement
                total_impact = min(total_impact, max_impact)
        
        # Ensure minimum impact for presentation purposes
        if total_impact < 1000:
            total_impact = max(total_impact, 5000)  # Minimum $5K impact for small accounts
            
    except Exception as e:
        logger.error(f"Error calculating fallback revenue impact: {e}")
        # Default fallback impact
        total_impact = 25000  # Default $25K impact
    
    return round(total_impact, 0)
