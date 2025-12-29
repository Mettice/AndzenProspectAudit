"""
Data preparation utilities for report sections.

This module serves as a facade, importing all prepare functions from individual preparer modules.
All _prepare_* methods have been extracted to dedicated preparer modules for better organization.
"""
# Import all prepare functions from preparer modules
from .preparers import (
    prepare_kav_data,
    prepare_list_growth_data,
    prepare_data_capture_data,
    prepare_automation_data,
    prepare_flow_data,
    prepare_browse_abandonment_data,
    prepare_post_purchase_data,
    prepare_abandoned_cart_data,
    prepare_campaign_performance_data,
    prepare_strategic_recommendations
)

# Re-export for backward compatibility
__all__ = [
    "prepare_kav_data",
    "prepare_list_growth_data",
    "prepare_data_capture_data",
    "prepare_automation_data",
    "prepare_flow_data",
    "prepare_browse_abandonment_data",
    "prepare_post_purchase_data",
    "prepare_abandoned_cart_data",
    "prepare_campaign_performance_data",
    "prepare_strategic_recommendations",
]
