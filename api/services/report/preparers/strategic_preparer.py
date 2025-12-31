"""
Strategic recommendations preparer using LLM.
"""
from typing import Dict, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)


async def generate_strategic_thesis(
    all_audit_data: Dict[str, Any],
    llm_service: Optional[Any] = None,
    prepared_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Strategist approach:
    - Connect KAV split → Automation opportunity
    - Connect campaign patterns → Segmentation need
    - Connect list growth → Data capture opportunity
    - Create prioritized recommendations based on gaps
    
    Args:
        all_audit_data: Complete audit data dictionary with all sections
        llm_service: Optional LLM service instance (will create if not provided)
    
    Returns:
        Strategic thesis string (HTML formatted)
    """
    # Extract key findings from all sections
    kav_data = all_audit_data.get("kav_data", {})
    campaign_data = all_audit_data.get("campaign_performance_data", {})
    list_growth_data = all_audit_data.get("list_growth_data", {})
    data_capture_data = all_audit_data.get("data_capture_data", {})
    automation_data = all_audit_data.get("automation_overview_data", {})  # Fixed: was "automation_data"
    
    kav_interpretation = kav_data.get("kav_interpretation", {})
    campaign_pattern = campaign_data.get("pattern_diagnosis", {})
    list_correlation = list_growth_data.get("list_correlation", {})
    form_categories = data_capture_data.get("categorized_forms", {})
    flow_issues = automation_data.get("flow_issues", {})
    
    # Build synthesis prompt for LLM - structured for better LLM understanding
    client_name = prepared_context.get("client_name", "the client") if prepared_context else all_audit_data.get("client_name", "the client")
    
    synthesis_prompt = f"""You are an expert email marketing strategist creating a strategic thesis for a comprehensive Klaviyo audit report.

CLIENT: {client_name}

AUDIT FINDINGS SUMMARY:

KAV (Klaviyo Attributed Value) Analysis:
- Strategic Thesis: {kav_interpretation.get("thesis", "N/A")}
- Opportunity: {kav_interpretation.get("opportunity", "N/A")}
- KAV Status: {kav_interpretation.get("kav_status", "N/A")}

Campaign Performance:
- Pattern Identified: {campaign_pattern.get("pattern", "N/A")}
- Diagnosis: {campaign_pattern.get("diagnosis", "N/A")}
- Root Cause: {campaign_pattern.get("root_cause", "N/A")}
- Priority Level: {campaign_pattern.get("priority", "N/A")}

List Growth & Revenue Correlation:
- Connection: {list_correlation.get("connection", "N/A")}
- Revenue Impact: {list_correlation.get("revenue_impact", "N/A")}
- Opportunity: {list_correlation.get("opportunity", "N/A")}

Data Capture Performance:
- Underperforming Forms: {len(form_categories.get("underperformers", []))}
- Inactive Forms: {len(form_categories.get("inactive", []))}
- High-Performing Forms: {len(form_categories.get("high_performers", []))}

Flow Issues & Opportunities:
- Missing Flows: {len(flow_issues.get("missing", []))}
- Duplicate Flows: {len(flow_issues.get("duplicates", []))}
- Zero-Delivery Flows: {len(flow_issues.get("zero_deliveries", []))}

YOUR TASK:
Create a comprehensive 2-3 paragraph strategic thesis that synthesizes all the findings above. The thesis should:

1. Identify the Core Opportunity: What is the single most important opportunity for improvement? (e.g., automation underinvestment, segmentation gaps, data capture optimization)

2. Connect Findings Across Sections: Show how different findings relate to each other (e.g., "Low KAV percentage combined with high campaign open rates but low click rates suggests...")

3. Prioritize Recommendations: Based on the priority levels and impact identified, what should be addressed first?

4. Provide Clear Next Steps: What are the immediate actionable next steps?

REQUIREMENTS:
- Write in a professional, consultant-style tone
- Be specific and actionable - reference actual findings from the audit
- Use numbers and percentages where available
- Connect insights across different sections
- Focus on business impact and revenue opportunities
- Write 2-3 well-structured paragraphs (each 4-6 sentences)
- DO NOT use generic phrases like "Contact Andzen" or "schedule consultation" - you ARE the strategist

Provide your strategic thesis in the following JSON format:

{{
    "primary": "Your complete 2-3 paragraph strategic thesis here. This should synthesize all findings, identify the core opportunity, connect insights across sections, prioritize recommendations, and provide clear next steps. Write in professional consultant tone with specific numbers and actionable insights."
}}

Return only the JSON object, no additional text."""
    
    # Use provided LLM service or create one
    if not llm_service:
        account_context = all_audit_data.get("account_context", {})
        llm_config = account_context.get("llm_config", {}) if account_context else {}
        from ...llm import LLMService
        
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
    
    try:
        # Log the prompt for debugging
        logger.debug(f"Strategic thesis prompt length: {len(synthesis_prompt)} characters")
        logger.debug(f"Key findings in prompt: KAV={kav_interpretation.get('thesis', 'N/A')[:50]}..., Pattern={campaign_pattern.get('pattern', 'N/A')}")
        
        thesis_response = await llm_service.generate_insights(
            section="strategic_synthesis",
            data={"prompt": synthesis_prompt},
            context={}
        )
        
        # Extract thesis text (could be in primary field or as direct response)
        thesis_text = thesis_response.get("primary", "") or thesis_response.get("thesis", "") or str(thesis_response)
        
        # Check if we got a fallback error message
        if "Unable to provide" in thesis_text or "no specific performance data" in thesis_text:
            logger.warning("LLM returned fallback error message for strategic thesis. Using fallback thesis generator.")
            return _generate_fallback_thesis(
                kav_interpretation,
                campaign_pattern,
                list_correlation,
                form_categories,
                flow_issues
            )
        
        # Format as HTML paragraphs
        if thesis_text:
            paragraphs = [p.strip() for p in thesis_text.split('\n\n') if p.strip()]
            thesis_html = '\n'.join([f'<p>{p}</p>' for p in paragraphs])
            logger.info(f"Strategic thesis generated successfully ({len(thesis_html)} characters)")
        else:
            logger.warning("Strategic thesis text is empty, using fallback")
            return _generate_fallback_thesis(
                kav_interpretation,
                campaign_pattern,
                list_correlation,
                form_categories,
                flow_issues
            )
        
        return thesis_html
        
    except Exception as e:
        logger.error(f"Error generating strategic thesis: {e}")
        # Fallback: Create a simple thesis from key findings
        return _generate_fallback_thesis(
            kav_interpretation,
            campaign_pattern,
            list_correlation,
            form_categories,
            flow_issues
        )


def identify_integration_opportunities(audit_data: Dict[str, Any]) -> list:
    """
    Strategist approach:
    - Missing review flows → Okendo Reviews
    - Wishlist behavior → Wishlist Plus
    - UGC needs → Okendo
    
    Args:
        audit_data: Complete audit data dictionary
    
    Returns:
        List of integration opportunity dictionaries
    """
    opportunities = []
    
    # Check for review flow
    reviews_data = audit_data.get("reviews_data", {})
    post_purchase_data = audit_data.get("post_purchase_data", {})
    
    # Check if review flow exists in post-purchase flows
    has_review_flow = False
    if post_purchase_data:
        # Check if any post-purchase flow mentions reviews
        flows = post_purchase_data.get("flows", [])
        for flow in flows:
            flow_name = flow.get("flow_name", "").lower() if flow.get("flow_name") else ""
            if "review" in flow_name or "rating" in flow_name:
                has_review_flow = True
                break
    
    # Also check reviews_data directly
    if reviews_data:
        has_review_flow = reviews_data.get("has_review_flow", False) or \
                         reviews_data.get("review_flow_exists", False)
    
    if not has_review_flow:
        opportunities.append({
            "integration": "Okendo Reviews",
            "capabilities": [
                "Review request flows",
                "Dynamic review content blocks",
                "UGC galleries",
                "Sentiment-based automation triggers"
            ],
            "priority": "MEDIUM",
            "reason": "No review request flow detected in post-purchase automation"
        })
    
    # Check for wishlist data
    wishlist_data = audit_data.get("wishlist_data", {})
    has_wishlist_behavior = False
    
    if wishlist_data:
        # Check if wishlist data indicates active wishlist usage
        has_wishlist_behavior = wishlist_data.get("has_wishlist_behavior", False) or \
                               wishlist_data.get("wishlist_items_count", 0) > 0 or \
                               wishlist_data.get("wishlist_flows_exist", False)
    
    # Also check flows for wishlist-related automation
    automation_data = audit_data.get("automation_data", {})
    if automation_data:
        flows = automation_data.get("flows", [])
        for flow in flows:
            flow_name = flow.get("name", "").lower() if flow.get("name") else ""
            if "wishlist" in flow_name:
                has_wishlist_behavior = True
                break
    
    if has_wishlist_behavior:
        opportunities.append({
            "integration": "Wishlist Plus",
            "capabilities": [
                "Low stock alerts",
                "Price drop notifications",
                "Back in stock triggers",
                "Wishlist abandonment flows"
            ],
            "priority": "LOW",
            "reason": "Wishlist behavior detected - integration could enhance automation"
        })
    
    # Check for UGC needs (if reviews are present but no UGC gallery)
    if has_review_flow and not reviews_data.get("ugc_gallery_exists", False):
        opportunities.append({
            "integration": "Okendo UGC",
            "capabilities": [
                "User-generated content galleries",
                "Social proof widgets",
                "UGC in email campaigns",
                "Visual content blocks"
            ],
            "priority": "LOW",
            "reason": "Review flow exists but UGC gallery not detected"
        })
    
    return opportunities


def _generate_fallback_thesis(
    kav_interpretation: Dict[str, Any],
    campaign_pattern: Dict[str, Any],
    list_correlation: Dict[str, Any],
    form_categories: Dict[str, Any],
    flow_issues: Dict[str, Any]
) -> str:
    """Generate fallback strategic thesis from key findings."""
    thesis_parts = []
    
    # KAV analysis
    if kav_interpretation.get("thesis"):
        thesis_parts.append(kav_interpretation.get("thesis"))
    
    # Campaign pattern
    if campaign_pattern.get("diagnosis"):
        thesis_parts.append(campaign_pattern.get("diagnosis"))
    
    # List correlation
    if list_correlation.get("connection"):
        thesis_parts.append(list_correlation.get("connection"))
    
    # Flow issues
    missing_count = len(flow_issues.get("missing", []))
    if missing_count > 0:
        thesis_parts.append(f"Missing {missing_count} critical automation flows represents a significant revenue opportunity.")
    
    # Combine into paragraphs
    if thesis_parts:
        thesis_text = " ".join(thesis_parts)
        paragraphs = [p.strip() for p in thesis_text.split('. ') if p.strip()]
        return '\n'.join([f'<p>{p}.</p>' for p in paragraphs if p])
    else:
        return '<p>Strategic analysis indicates opportunities for optimization across automation, segmentation, and data capture strategies.</p>'


async def prepare_strategic_recommendations(audit_data: Dict[str, Any], prepared_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Prepare strategic recommendations using LLM service.
    
    This synthesizes all audit findings into high-level strategic recommendations.
    
    Args:
        audit_data: Raw audit data dictionary
        prepared_context: Optional prepared context dictionary with processed data (kav_interpretation, pattern_diagnosis, etc.)
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
        
        # Step 1: Generate strategic thesis (synthesizes all findings)
        logger.info("Generating strategic thesis...")
        strategic_thesis = await generate_strategic_thesis(audit_data, llm_service, prepared_context)
        
        # Add strategic thesis to context for recommendations
        context["strategic_thesis"] = strategic_thesis
        
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
    
    # Generate strategic thesis (even if LLM failed for recommendations)
    # Use prepared_context if available (has prepared data with kav_interpretation, pattern_diagnosis, etc.)
    # Otherwise fall back to raw audit_data
    thesis_data_source = prepared_context if prepared_context else audit_data
    try:
        strategic_thesis = await generate_strategic_thesis(thesis_data_source, None)
    except Exception as e:
        logger.warning(f"Failed to generate strategic thesis: {e}")
        strategic_thesis = _generate_fallback_thesis(
            thesis_data_source.get("kav_data", {}).get("kav_interpretation", {}),
            thesis_data_source.get("campaign_performance_data", {}).get("pattern_diagnosis", {}),
            thesis_data_source.get("list_growth_data", {}).get("list_correlation", {}),
            thesis_data_source.get("data_capture_data", {}).get("categorized_forms", {}),
            thesis_data_source.get("automation_overview_data", {}).get("flow_issues", {})
        )
    
    # Step 2: Identify integration opportunities
    integration_opportunities = identify_integration_opportunities(audit_data)
    
    if integration_opportunities:
        logger.info(f"Identified {len(integration_opportunities)} integration opportunities")
    
    return {
        "strategic_recommendations": strategic_recommendations,
        "strategic_thesis": strategic_thesis,  # Strategic synthesis thesis
        "integration_opportunities": integration_opportunities,  # Third-party integration recommendations
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
