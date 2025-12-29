"""
Data preparers for report sections.

Each preparer handles preparation of data for a specific report section.
"""

from .kav_preparer import prepare_kav_data
from .list_growth_preparer import prepare_list_growth_data
from .data_capture_preparer import prepare_data_capture_data
from .automation_preparer import prepare_automation_data
from .flow_preparer import prepare_flow_data
from .browse_abandonment_preparer import prepare_browse_abandonment_data
from .post_purchase_preparer import prepare_post_purchase_data
from .abandoned_cart_preparer import prepare_abandoned_cart_data
from .campaign_preparer import prepare_campaign_performance_data
from .strategic_preparer import prepare_strategic_recommendations

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

