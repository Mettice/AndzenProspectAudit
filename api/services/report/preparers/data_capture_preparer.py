"""
Data capture/forms data preparer.
"""
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


def generate_form_recommendations(form: Dict[str, Any]) -> List[str]:
    """
    Strategist's tactical recommendations:
    - Trigger timing analysis (12s → 20s)
    - CTA visibility
    - Form complexity (two-step forms)
    - Field reduction
    
    Args:
        form: Form data dictionary
    
    Returns:
        List of recommendation strings
    """
    recommendations = []
    submit_rate = form.get("submit_rate", 0)
    form_type = form.get("type", "").lower() if form.get("type") else ""
    
    # Check if popup and low submit rate
    if "popup" in form_type and submit_rate < 1:
        recommendations.append("Consider implementing exit-intent triggering to capture abandoning visitors")
        recommendations.append("Review form fields - each additional field reduces conversion by ~5-10%")
    
    if submit_rate < 2:
        recommendations.append("Test offering a stronger incentive (15% vs 10% discount)")
        recommendations.append("Ensure CTA button is prominent and above the fold")
    
    # Trigger timing analysis (if we have this data)
    trigger_delay = form.get("trigger_delay")
    if trigger_delay is not None and trigger_delay < 20:
        recommendations.append(f"Current trigger timing ({trigger_delay}s) may be too early. Test 20+ seconds for better conversion.")
    
    # Form complexity recommendations
    if submit_rate < 3:
        recommendations.append("Consider implementing a two-step form to reduce friction")
        recommendations.append("Test reducing the number of form fields to improve conversion")
    
    return recommendations


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
            # Generate form-specific recommendations
            recommendations = generate_form_recommendations(form)
            categorized["underperformers"].append({
                **form,
                "problem": f"Despite {impressions} impressions, only achieving {submit_rate:.1f}% conversion",
                "recommendations": recommendations
            })
    
    return categorized


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
        
        # Format analysis text as HTML paragraphs - filter out raw JSON strings
        primary_text = strategic_insights.get("primary", "")
        if isinstance(primary_text, str) and (primary_text.strip().startswith('{') or (primary_text.strip().startswith('"') and '"primary"' in primary_text[:100])):
            logger.warning("Primary text appears to be JSON string, JSON parsing may have failed")
            primary_text = ""
        
        if primary_text:
            # Split into paragraphs and wrap in <p> tags
            paragraphs = [p.strip() for p in primary_text.split('\n\n') if p.strip()]
            analysis_text = '\n'.join([f'<p>{p}</p>' for p in paragraphs])
        else:
            analysis_text = ""
        
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
        "recommendations": recommendations,
        "areas_of_opportunity": areas_of_opportunity if isinstance(areas_of_opportunity, list) else [],
        "root_cause_analysis": root_cause_analysis,  # LLM-generated root cause analysis
        "risk_flags": risk_flags,  # LLM-generated risk flags
        "quick_wins": quick_wins,  # LLM-generated quick wins
        "analysis": forms_raw.get("analysis", {
            "popup_timing": "12 seconds",
            "recommended_timing": "20 seconds"
        }),
        "advanced_targeting": forms_raw.get("advanced_targeting", [
            "Exit Intent",
            "Returning Customer Form",
            "Engaged With Form But Not Submitted",
            "Idle Cart",
            "Page Views",
            "Product Viewed"
        ]),
        "progressive_profiling": forms_raw.get("progressive_profiling", {"enabled": True}),
        "flyout_forms": forms_raw.get("flyout_forms", {"enabled": True})
    }

