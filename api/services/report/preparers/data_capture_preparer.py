"""
Data capture/forms data preparer.
"""
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


def generate_form_recommendations(
    form: Dict[str, Any], 
    all_forms_data: Optional[List[Dict[str, Any]]] = None,
    account_context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Generate form-specific recommendations with context, effort estimates, and expected impact.
    
    Args:
        form: Form data dictionary
        all_forms_data: Optional list of all forms for comparison context
    
    Returns:
        List of recommendation dictionaries with:
        - recommendation: str (specific recommendation text)
        - effort: str (time estimate)
        - expected_impact: str (potential lift/benefit)
        - priority: str (high/medium/low)
    """
    recommendations = []
    submit_rate = form.get("submit_rate", 0)
    impressions = form.get("impressions", 0)
    form_name = form.get("name", "Unknown Form")
    form_name_display = form_name  # Keep original for display
    form_name_lower = form_name.lower()
    form_type = form.get("type", "").lower() if form.get("type") else ""
    
    # Calculate context metrics
    high_performers = []
    avg_submit_rate = 0
    performance_gap_pct = 0
    
    if all_forms_data:
        other_forms = [f for f in all_forms_data if f.get("name") != form.get("name")]
        if other_forms:
            avg_submit_rate = sum(f.get("submit_rate", 0) for f in other_forms) / len(other_forms)
            high_performers = [f for f in other_forms if f.get("submit_rate", 0) >= 5]
            if avg_submit_rate > 0:
                performance_gap_pct = ((avg_submit_rate - submit_rate) / avg_submit_rate * 100) if avg_submit_rate > 0 else 0
    
    # Build context string
    context_parts = []
    if impressions > 10000:
        context_parts.append(f"High traffic ({impressions:,} impressions)")
    elif impressions > 1000:
        context_parts.append(f"Moderate traffic ({impressions:,} impressions)")
    
    if performance_gap_pct > 50 and avg_submit_rate > 0:
        context_parts.append(f"{performance_gap_pct:.0f}% below your other forms")
    elif performance_gap_pct > 30 and avg_submit_rate > 0:
        context_parts.append(f"{performance_gap_pct:.0f}% below average")
    
    context_str = " | ".join(context_parts) if context_parts else "Standard performance"
    
    # Determine form category for specific recommendations
    is_exit_intent = "exit" in form_name_lower or "exit-intent" in form_name_lower
    is_popup = "popup" in form_type or "pop-up" in form_name_lower
    is_product_page = "product" in form_name_lower
    is_sms = "sms" in form_name_lower
    
    # RECOMMENDATION 1: Exit Intent Specific (if applicable)
    if is_exit_intent and submit_rate < 3:
        # Calculate potential impact
        target_rate = 4.5 if high_performers else 3.5  # Aim for high performer level or benchmark
        potential_lift = target_rate - submit_rate
        additional_emails = int((impressions * potential_lift / 100))
        
        recommendations.append({
            "recommendation": f"Test stronger exit intent offer - your high-performing forms convert at 5-12%, likely due to better incentives. Try: 'Wait! Get 20% off your first order' instead of generic 'Join our list'",
            "effort": "1 hour",
            "expected_impact": f"+{potential_lift:.1f}% submit rate = +{additional_emails:,} emails/month",
            "priority": "high"
        })
        
        if is_product_page:
            recommendations.append({
                "recommendation": f"Add cart value context - since this is product page exit intent, reference the specific product they're viewing. Example: 'Love the [product name]? Get 15% off when you sign up'",
                "effort": "2 hours (requires dynamic insertion)",
                "expected_impact": f"+1-2% = +{int(impressions * 0.015):,}-{int(impressions * 0.02):,} emails/month",
                "priority": "medium"
            })
    
    # RECOMMENDATION 2: A/B Test Messaging (for underperformers)
    if submit_rate < 3 and impressions > 1000:
        test_variants = []
        if is_exit_intent:
            test_variants.append("'Last chance! 20% off expires in 10 minutes' (urgency)")
            test_variants.append("'Join 50K+ happy customers - get exclusive deals' (social proof)")
        else:
            test_variants.append("Percentage discount (e.g., '20% off')")
            test_variants.append("Dollar amount (e.g., '$10 off $50+')")
            test_variants.append("Free shipping threshold")
        
        potential_lift = 1.0  # Conservative 1% lift estimate
        additional_emails = int(impressions * potential_lift / 100)
        
        recommendations.append({
            "recommendation": f"A/B test urgency vs. value messaging. Test A: {test_variants[0] if test_variants else 'Urgency-focused'}. Test B: {test_variants[1] if len(test_variants) > 1 else 'Value-focused'}",
            "effort": "30 mins setup",
            "expected_impact": f"+{potential_lift:.1f}% = +{additional_emails:,} emails/month",
            "priority": "medium"
        })
    
    # RECOMMENDATION 3: Compare to High Performers
    if high_performers and submit_rate < avg_submit_rate * 0.7:
        top_performer = high_performers[0]
        top_name = top_performer.get("name", "high-performing form")
        top_rate = top_performer.get("submit_rate", 0)
        
        recommendations.append({
            "recommendation": f"This form performs {performance_gap_pct:.0f}% below your other forms - investigate what makes '{top_name}' successful (currently {top_rate:.1f}% submit rate). Analyze: messaging, offer type, placement, trigger timing",
            "effort": "2 hours (analysis + implementation)",
            "expected_impact": f"Closing {performance_gap_pct:.0f}% gap could add +{int(impressions * performance_gap_pct / 100):,} emails/month",
            "priority": "high"
        })
    
    # RECOMMENDATION 4: Form Type Specific
    if is_popup and submit_rate < 2:
        if not is_exit_intent:
            recommendations.append({
                "recommendation": f"For popup '{form_name_display}', consider implementing exit-intent triggering instead of time-based to capture abandoning visitors more effectively",
                "effort": "1 hour",
                "expected_impact": "+0.5-1% submit rate = +" + f"{int(impressions * 0.0075):,}-{int(impressions * 0.01):,} emails/month" if impressions > 0 else "moderate lift",
                "priority": "medium"
            })
        
        trigger_delay = form.get("trigger_delay")
        if trigger_delay is not None and trigger_delay < 20:
            recommendations.append({
                "recommendation": f"Current trigger timing ({trigger_delay}s) may be too early. Test 20+ seconds for better conversion and less interruption",
                "effort": "15 mins",
                "expected_impact": "+0.3-0.5% submit rate",
                "priority": "low"
            })
    
    # RECOMMENDATION 5: Incentive Strength
    if submit_rate < 3 and impressions > 500:
        recommendations.append({
            "recommendation": f"For '{form_name_display}', test offering a stronger incentive (e.g., 15% vs 10% discount) to boost conversions. Ensure the offer is clearly stated in form copy",
            "effort": "1 hour",
            "expected_impact": f"+0.5-1% submit rate = +{int(impressions * 0.0075):,}-{int(impressions * 0.01):,} emails/month",
            "priority": "medium"
        })
    
    # RECOMMENDATION 6: Two-Step Form (for high traffic, low conversion)
    if impressions > 5000 and submit_rate < 1.5:
        recommendations.append({
            "recommendation": f"Consider implementing a two-step form for '{form_name_display}' to reduce initial friction and capture more leads. Step 1: Email only. Step 2: Preferences",
            "effort": "2-3 hours",
            "expected_impact": f"+1-2% submit rate = +{int(impressions * 0.015):,}-{int(impressions * 0.02):,} emails/month",
            "priority": "medium"
        })
    
    # RECOMMENDATION 7: Field Reduction
    if submit_rate < 2 and impressions > 1000:
        recommendations.append({
            "recommendation": f"Test reducing the number of form fields in '{form_name_display}' - each additional field can reduce conversion by ~5-10%",
            "effort": "1 hour",
            "expected_impact": f"+0.3-0.7% submit rate = +{int(impressions * 0.005):,}-{int(impressions * 0.007):,} emails/month",
            "priority": "low"
        })
    
    # RECOMMENDATION 8: CTA Optimization
    if submit_rate < 2 and not any("cta" in rec.get("recommendation", "").lower() or "button" in rec.get("recommendation", "").lower() for rec in recommendations):
        recommendations.append({
            "recommendation": f"Ensure the Call-to-Action (CTA) button for '{form_name_display}' is prominent, clear, and above the fold. Test button color, size, and copy",
            "effort": "1 hour",
            "expected_impact": "+0.2-0.5% submit rate",
            "priority": "low"
        })
    
    # Calculate expected revenue impact based on actual subscriber value
    if recommendations and impressions > 0:
        # Estimate: moving from current rate to target rate
        target_rate = min(5.0, avg_submit_rate * 1.2) if avg_submit_rate > 0 else 4.0
        if submit_rate < target_rate:
            potential_lift = target_rate - submit_rate
            additional_subscribers = int(impressions * potential_lift / 100)
            
            # Calculate email LTV from actual account data (KAV revenue / subscriber count)
            # This gives us the actual value per subscriber for THIS client
            subscriber_ltv = 50  # Fallback conservative estimate
            if account_context:
                kav_data = account_context.get("kav_data", {})
                list_data = account_context.get("list_growth_data", {})
                if kav_data and list_data:
                    attributed_revenue = kav_data.get("attributed_revenue", 0)
                    total_subscribers = list_data.get("current_total", 0)
                    if attributed_revenue > 0 and total_subscribers > 0:
                        # Annualized LTV per subscriber from actual data
                        subscriber_ltv = int((attributed_revenue / total_subscribers) * 4)  # Quarterly * 4 = annual
                        subscriber_ltv = max(subscriber_ltv, 25)  # Minimum $25 floor
            
            # Calculate revenue range: conservative (80% of LTV) to optimistic (120% of LTV)
            revenue_low = int(additional_subscribers * subscriber_ltv * 0.8)
            revenue_high = int(additional_subscribers * subscriber_ltv * 1.2)
            
            # Add summary recommendation with calculated impact
            recommendations.insert(0, {
                "recommendation": f"EXPECTED IMPACT: Moving '{form_name_display}' from {submit_rate:.2f}% to {target_rate:.1f}% (matching high performers) = +{additional_subscribers:,} additional subscribers monthly = ~${revenue_low:,}-${revenue_high:,} additional revenue based on your account's subscriber value",
                "effort": "Combined effort from recommendations below",
                "expected_impact": f"+{potential_lift:.1f}% submit rate = +{additional_subscribers:,} subscribers/month",
                "priority": "high"
            })
    
    # Remove duplicates and limit to top 5-6 most relevant
    seen = set()
    unique_recommendations = []
    for rec in recommendations:
        rec_key = rec.get("recommendation", "").lower()[:100]  # First 100 chars as key
        if rec_key not in seen:
            seen.add(rec_key)
            unique_recommendations.append(rec)
    
    return unique_recommendations[:6]  # Return top 6 (including summary)


def categorize_forms(forms_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Strategist approach:
    - High performers: ≥5% submit rate
    - Underperformers: <3% with >100 impressions
    - Inactive: 0 impressions
    
    Args:
        forms_data: List of form dictionaries
    
    Returns:
        Dict with categorized forms (high_performers, underperformers, inactive)
    """
    categorized = {
        "high_performers": [],
        "underperformers": [],
        "inactive": []
    }
    
    for form in forms_data:
        submit_rate = form.get("submit_rate", 0)
        impressions = form.get("impressions", 0)
        
        if impressions == 0:
            categorized["inactive"].append({
                **form,
                "issue": "No impressions recorded",
                "recommendation": "Either activate this form or remove it to reduce clutter"
            })
        elif submit_rate >= 5:
            categorized["high_performers"].append({
                **form,
                "achievement": f"{submit_rate:.1f}% submit rate exceeds industry standard of 3-5%"
            })
        elif submit_rate < 3 and impressions > 100:
            # Generate form-specific recommendations with context from all forms
            recommendations = generate_form_recommendations(form, forms_data, None)
            # Calculate performance gap for context
            other_forms = [f for f in forms_data if f.get("name") != form.get("name")]
            avg_rate = sum(f.get("submit_rate", 0) for f in other_forms) / len(other_forms) if other_forms else 0
            gap_pct = ((avg_rate - submit_rate) / avg_rate * 100) if avg_rate > 0 else 0
            
            context_msg = f"High traffic ({impressions:,} impressions)" if impressions > 10000 else f"{impressions:,} impressions"
            if gap_pct > 50:
                context_msg += f" but {gap_pct:.0f}% below your other forms"
            
            categorized["underperformers"].append({
                **form,
                "problem": f"Despite {context_msg}, only achieving {submit_rate:.1f}% conversion",
                "recommendations": recommendations  # Now returns list of dicts with effort/impact
            })
    
    return categorized


def _analyze_advanced_targeting(forms: List[Dict[str, Any]], client_name: str = "the client") -> List[str]:
    """
    Analyze forms to detect which advanced targeting features are being used.
    Returns specific, contextual recommendations based on actual form data.
    
    Args:
        forms: List of form dictionaries
        client_name: Client name for context
    
    Returns:
        List of detected/available advanced targeting features with context
    """
    if not forms:
        return []
    
    detected_features = []
    form_names_lower = [f.get("name", "").lower() for f in forms]
    form_types = [f.get("type", "").lower() for f in forms]
    
    # Detect Exit Intent
    exit_intent_keywords = ["exit", "exit-intent", "exit intent", "leaving", "abandon"]
    has_exit_intent = any(any(keyword in name for keyword in exit_intent_keywords) for name in form_names_lower)
    if has_exit_intent:
        # Find the exit intent form(s)
        exit_forms = [f for f in forms if any(keyword in f.get("name", "").lower() for keyword in exit_intent_keywords)]
        if exit_forms:
            best_exit = max(exit_forms, key=lambda x: x.get("impressions", 0))
            submit_rate = best_exit.get("submit_rate", 0)
            if submit_rate < 3:
                detected_features.append(f"Exit Intent (detected in '{best_exit.get('name')}' - {submit_rate:.1f}% submit rate, optimization opportunity)")
            else:
                detected_features.append(f"Exit Intent (detected in '{best_exit.get('name')}' - performing well at {submit_rate:.1f}%)")
    else:
        # Recommend exit intent if they have high-traffic popups
        high_traffic_popups = [f for f in forms if f.get("type", "").lower() == "popup" and f.get("impressions", 0) > 5000]
        if high_traffic_popups:
            detected_features.append("Exit Intent (not detected - recommended for high-traffic popups)")
    
    # Detect Returning Customer targeting
    returning_keywords = ["returning", "existing", "customer", "repeat", "loyal"]
    has_returning = any(any(keyword in name for keyword in returning_keywords) for name in form_names_lower)
    if has_returning:
        detected_features.append("Returning Customer Targeting (detected in form names)")
    else:
        # Check if they have multiple forms that could benefit from segmentation
        if len(forms) > 3:
            detected_features.append("Returning Customer Targeting (not detected - opportunity to segment by customer lifecycle)")
    
    # Detect Product Page targeting
    product_keywords = ["product", "pdp", "product page", "item"]
    has_product_targeting = any(any(keyword in name for keyword in product_keywords) for name in form_names_lower)
    if has_product_targeting:
        product_forms = [f for f in forms if any(keyword in f.get("name", "").lower() for keyword in product_keywords)]
        if product_forms:
            detected_features.append(f"Product Page Targeting (detected in {len(product_forms)} form(s))")
    else:
        # Recommend if they have ecommerce
        detected_features.append("Product Page Targeting (not detected - consider adding for product pages)")
    
    # Detect Cart/Checkout targeting
    cart_keywords = ["cart", "checkout", "basket", "abandon"]
    has_cart_targeting = any(any(keyword in name for keyword in cart_keywords) for name in form_names_lower)
    if has_cart_targeting:
        detected_features.append("Cart/Checkout Targeting (detected in form names)")
    else:
        detected_features.append("Cart/Checkout Targeting (not detected - opportunity to capture abandoning shoppers)")
    
    # Detect Engagement-based targeting (forms with high views but low submissions)
    underperforming_forms = [f for f in forms if f.get("impressions", 0) > 1000 and f.get("submit_rate", 0) < 2]
    if underperforming_forms:
        detected_features.append(f"Engagement-Based Retargeting (recommended for {len(underperforming_forms)} underperforming form(s) with high traffic)")
    
    # Detect Page View targeting
    if len(forms) > 5:
        detected_features.append("Page View Targeting (multiple forms suggest page-level targeting in use)")
    else:
        detected_features.append("Page View Targeting (not detected - consider triggering forms after X page views)")
    
    # If no specific features detected, provide generic recommendations
    if len(detected_features) == 0:
        detected_features = [
            "Exit Intent (not detected - high-impact opportunity)",
            "Returning Customer Segmentation (not detected - opportunity to personalize)",
            "Product Page Targeting (not detected - consider for product pages)",
            "Cart Abandonment Targeting (not detected - opportunity to recover sales)"
        ]
    
    return detected_features


def _analyze_progressive_profiling(forms: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze forms to determine if progressive profiling is being used.
    
    Args:
        forms: List of form dictionaries
    
    Returns:
        Dict with enabled status and recommendations
    """
    if not forms:
        return {"enabled": False, "recommendation": "No forms available to analyze"}
    
    # Check for multi-step forms (indicator of progressive profiling)
    multi_step_keywords = ["step", "multi", "progressive", "stage"]
    form_names_lower = [f.get("name", "").lower() for f in forms]
    has_multi_step = any(any(keyword in name for keyword in multi_step_keywords) for name in form_names_lower)
    
    # Check if forms have varying complexity (suggests progressive profiling)
    form_submit_rates = [f.get("submit_rate", 0) for f in forms if f.get("impressions", 0) > 100]
    has_varying_complexity = False
    if len(form_submit_rates) > 2:
        rate_variance = max(form_submit_rates) - min(form_submit_rates)
        # High variance might indicate different form complexities
        has_varying_complexity = rate_variance > 3
    
    # Analyze form performance to infer progressive profiling
    high_performers = [f for f in forms if f.get("submit_rate", 0) >= 5]
    low_performers = [f for f in forms if f.get("submit_rate", 0) < 2 and f.get("impressions", 0) > 500]
    
    if has_multi_step or (has_varying_complexity and len(high_performers) > 0):
        return {
            "enabled": True,
            "evidence": "Multi-step forms or varying form complexity detected",
            "recommendation": "Consider expanding progressive profiling to more forms"
        }
    elif low_performers and not high_performers:
        return {
            "enabled": False,
            "recommendation": f"Progressive profiling recommended - {len(low_performers)} form(s) underperforming could benefit from reduced initial friction"
        }
    else:
        return {
            "enabled": False,
            "recommendation": "Progressive profiling not detected - consider implementing to reduce form abandonment"
        }


def _analyze_flyout_forms(forms: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze forms to determine if flyout forms are being used.
    
    Args:
        forms: List of form dictionaries
    
    Returns:
        Dict with enabled status and recommendations
    """
    if not forms:
        return {"enabled": False, "recommendation": "No forms available to analyze"}
    
    # Check for flyout form type
    flyout_forms = [f for f in forms if f.get("type", "").lower() == "flyout"]
    
    if flyout_forms:
        avg_submit_rate = sum(f.get("submit_rate", 0) for f in flyout_forms) / len(flyout_forms) if flyout_forms else 0
        return {
            "enabled": True,
            "count": len(flyout_forms),
            "avg_submit_rate": round(avg_submit_rate, 2),
            "recommendation": f"Flyout forms detected ({len(flyout_forms)} form(s), avg {avg_submit_rate:.1f}% submit rate)"
        }
    else:
        # Check if they have popups that could be converted to flyouts
        popup_forms = [f for f in forms if f.get("type", "").lower() == "popup"]
        if popup_forms:
            return {
                "enabled": False,
                "recommendation": f"Flyout forms not detected - consider testing flyouts vs popups ({len(popup_forms)} popup form(s) found)"
            }
        else:
            return {
                "enabled": False,
                "recommendation": "Flyout forms not detected - consider testing flyout format for less intrusive capture"
            }


async def prepare_data_capture_data(
    forms_raw: Dict[str, Any],
    client_name: str = "the client",
    account_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Prepare data capture/forms data for template with LLM-generated insights."""
    if not forms_raw:
        return {"forms": []}
    
    # Format forms data - filter out zero impressions, deduplicate, and format submit rates
    forms = []
    seen_form_ids = set()
    seen_form_names = set()
    
    for form in forms_raw.get("forms", []):
        form_id = form.get("id")
        form_name = form.get("name", "Unknown")
        
        # Deduplicate by ID first (most reliable)
        if form_id and form_id in seen_form_ids:
            logger.debug(f"Skipping duplicate form by ID: {form_name} (ID: {form_id})")
            continue
        
        # Also check for duplicate names (in case ID is missing)
        if form_name in seen_form_names:
            logger.debug(f"Skipping duplicate form by name: {form_name}")
            continue
        
        # Only include forms with impressions > 0
        if form.get("impressions", 0) > 0:
            # Format submit rate to match sample audit (0.9% not 0.90%, 0.10% not 0.1%)
            submit_rate = form.get("submit_rate", 0)
            if submit_rate >= 1:
                submit_rate_fmt = f"{submit_rate:.1f}%"
            else:
                # For < 1%, use 2 decimals but remove trailing zero if .X0
                rate_str = f"{submit_rate:.2f}"
                if rate_str.endswith("0"):
                    submit_rate_fmt = f"{rate_str.rstrip('0').rstrip('.')}%"
                else:
                    submit_rate_fmt = f"{rate_str}%"
            
            forms.append({
                **form,
                "submit_rate_fmt": submit_rate_fmt
            })
            
            # Track seen forms
            if form_id:
                seen_form_ids.add(form_id)
            seen_form_names.add(form_name)
    
    # Step 1: Categorize forms (before LLM call)
    categorized_forms = categorize_forms(forms)
    
    logger.info(
        f"Forms categorized: {len(categorized_forms.get('high_performers', []))} high performers, "
        f"{len(categorized_forms.get('underperformers', []))} underperformers, "
        f"{len(categorized_forms.get('inactive', []))} inactive"
    )
    
    # Try to use LLM service for insights
    analysis_text = ""
    recommendations = []
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
        
        # Get industry from account_context
        industry = account_context.get("industry", "retail") if account_context else "retail"
        
        # Format data for LLM (include categorized forms for context)
        formatted_data = LLMDataFormatter.format_for_generic_analysis(
            section="data_capture",
            data={
                "forms": forms,
                "period_days": forms_raw.get("period_days", 90),
                "total_forms": len(forms),
                "total_impressions": sum(f.get("impressions", 0) for f in forms),
                "total_submissions": sum(f.get("submitted", 0) for f in forms),
                "avg_submit_rate": sum(f.get("submit_rate", 0) for f in forms) / len(forms) if forms else 0
            },
            client_context={
                "client_name": client_name,
                "industry": industry,
                "currency": account_context.get("currency", "USD") if account_context else "USD"
            }
        )
        
        # Add categorized forms to context for LLM
        if "context" not in formatted_data:
            formatted_data["context"] = {}
        formatted_data["context"]["categorized_forms"] = categorized_forms
        
        # Generate insights using LLM
        strategic_insights = await llm_service.generate_insights(
            section="data_capture",
            data=formatted_data,
            context=formatted_data.get("context", {})
        )
        
        # Extract comprehensive subsections (new enhanced format)
        from ..html_formatter import format_llm_output
        
        form_performance_overview = strategic_insights.get("form_performance_overview", "")
        high_performers_analysis = strategic_insights.get("high_performers_analysis", "")
        optimization_opportunities = strategic_insights.get("optimization_opportunities", "")
        
        # Format analysis text as HTML paragraphs - filter out raw JSON strings
        primary_text = strategic_insights.get("primary", "")
        if isinstance(primary_text, str) and (primary_text.strip().startswith('{') or (primary_text.strip().startswith('"') and '"primary"' in primary_text[:100])):
            logger.warning("Primary text appears to be JSON string, JSON parsing may have failed")
            primary_text = ""
        
        if primary_text:
            # Use format_llm_output for consistent formatting
            analysis_text = format_llm_output(primary_text)
        else:
            analysis_text = ""
        
        # Format all subsections
        form_performance_overview = format_llm_output(form_performance_overview) if form_performance_overview else ""
        high_performers_analysis = format_llm_output(high_performers_analysis) if high_performers_analysis else ""
        optimization_opportunities = format_llm_output(optimization_opportunities) if optimization_opportunities else ""
        
        recommendations = strategic_insights.get("recommendations", [])
        if not isinstance(recommendations, list):
            recommendations = []
        
        areas_of_opportunity = strategic_insights.get("areas_of_opportunity", [])
        if not isinstance(areas_of_opportunity, list):
            areas_of_opportunity = []
        
        # Extract enhanced strategic value elements
        root_cause_analysis = strategic_insights.get("root_cause_analysis", {})
        if not isinstance(root_cause_analysis, dict):
            root_cause_analysis = {}
        
        risk_flags = strategic_insights.get("risk_flags", [])
        if not isinstance(risk_flags, list):
            risk_flags = []
        
        quick_wins = strategic_insights.get("quick_wins", [])
        if not isinstance(quick_wins, list):
            quick_wins = []
        
    except Exception as e:
        # Fallback if LLM fails
        logger.warning(f"LLM service unavailable for data capture analysis, using fallback: {e}")
        form_performance_overview = ""
        high_performers_analysis = ""
        optimization_opportunities = ""
        analysis_text = ""
        recommendations = []
        areas_of_opportunity = []
        root_cause_analysis = {}
        risk_flags = []
        quick_wins = []
    
    return {
        "forms": forms,
        "categorized_forms": categorized_forms,  # Form categorization (high_performers, underperformers, inactive)
        "analysis_text": analysis_text,
        # Comprehensive subsections (new enhanced format)
        "form_performance_overview": form_performance_overview if 'form_performance_overview' in locals() else "",
        "high_performers_analysis": high_performers_analysis if 'high_performers_analysis' in locals() else "",
        "optimization_opportunities": optimization_opportunities if 'optimization_opportunities' in locals() else "",
        "recommendations": recommendations,
        "areas_of_opportunity": areas_of_opportunity if isinstance(areas_of_opportunity, list) else [],
        "root_cause_analysis": root_cause_analysis,  # LLM-generated root cause analysis
        "risk_flags": risk_flags,  # LLM-generated risk flags
        "quick_wins": quick_wins,  # LLM-generated quick wins
        "analysis": forms_raw.get("analysis", {
            "popup_timing": "12 seconds",
            "recommended_timing": "20 seconds"
        }),
        "advanced_targeting": _analyze_advanced_targeting(forms, client_name),
        "progressive_profiling": _analyze_progressive_profiling(forms),
        "flyout_forms": _analyze_flyout_forms(forms)
    }

