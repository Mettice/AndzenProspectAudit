"""
Modular prompt templates for LLM-generated insights.

Based on the strategist's method: data + context + benchmarks → insights
Enhanced with strategic value elements: ROI, quick wins, risk flags, implementation roadmaps
"""
from typing import Dict, Any

from .base import format_data_for_prompt
from .kav_prompt import get_kav_prompt
from .flow_prompt import get_flow_prompt, get_browse_abandonment_prompt, get_post_purchase_prompt
from .campaign_prompt import get_campaign_prompt
from .strategic_prompt import get_strategic_recommendations_prompt
from .section_prompts import (
    get_list_growth_prompt,
    get_automation_prompt,
    get_data_capture_prompt,
    get_generic_prompt
)


def get_prompt_template(section: str, data: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Get prompt template for a specific section.
    
    Args:
        section: Section name (e.g., "kav", "flow_performance", "list_growth", "automation_overview")
        data: Formatted data for the section
        context: Additional context (industry, benchmarks, etc.)
    
    Returns:
        Formatted prompt string
    """
    if section == "kav":
        return get_kav_prompt(data, context)
    elif section == "flow_performance":
        return get_flow_prompt(data, context)
    elif section == "campaign_performance":
        return get_campaign_prompt(data, context)
    elif section == "list_growth":
        return get_list_growth_prompt(data, context)
    elif section == "automation_overview":
        return get_automation_prompt(data, context)
    elif section == "data_capture":
        return get_data_capture_prompt(data, context)
    elif section == "browse_abandonment":
        return get_browse_abandonment_prompt(data, context)
    elif section == "post_purchase":
        return get_post_purchase_prompt(data, context)
    elif section == "strategic_recommendations":
        return get_strategic_recommendations_prompt(data, context)
    else:
        return get_generic_prompt(section, data, context)

