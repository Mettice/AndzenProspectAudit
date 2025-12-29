"""
Flow data formatting module.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class FlowFormatter:
    """Formats flow data for audit templates."""
    
    def prepare_browse_abandonment_data(self, core_flows: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare browse abandonment data - only include if flow exists and has performance data.
        
        Args:
            core_flows: Core flows data from get_core_flows_performance
            
        Returns:
            Browse abandonment data dict with flows array (empty if flow not found)
        """
        browse_flow = core_flows.get("browse_abandonment", {})
        flows = []
        
        # Only add flow if it exists and was found
        if browse_flow.get("found", False):
            performance = browse_flow.get("performance", {})
            # Only include if there's actual performance data (not all zeros)
            if (performance.get("open_rate", 0) > 0 or 
                performance.get("click_rate", 0) > 0 or 
                performance.get("revenue", 0) > 0):
                flows.append({
                    "name": browse_flow.get("name", "Browse Abandonment"),
                    "open_rate": performance.get("open_rate", 0),
                    "click_rate": performance.get("click_rate", 0),
                    "placed_order_rate": performance.get("conversion_rate", 0),
                    "revenue_per_recipient": performance.get("revenue_per_recipient", 0),
                    "revenue": performance.get("revenue", 0)
                })
        
        return {
            "flows": flows,  # Empty array if flow not found
            "benchmark": {
                "name": "Browse Abandonment",
                "open_rate": 45.20,
                "click_rate": 4.80,
                "conversion_rate": 1.85,
                "revenue_per_recipient": 2.10
            },
            "industry": "Apparel and Accessories",
            "recommendations": []
        }
    
    def prepare_abandoned_cart_data(self, core_flows: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare abandoned cart data - only include flows that were found.
        
        Args:
            core_flows: Core flows data from get_core_flows_performance
            
        Returns:
            Abandoned cart data dict with flows array (only includes found flows)
        """
        flows = []
        
        # Check for abandoned checkout flow
        checkout_flow = core_flows.get("abandoned_checkout", {})
        if checkout_flow.get("found", False):
            performance = checkout_flow.get("performance", {})
            flows.append({
                "name": checkout_flow.get("name", "Abandoned Checkout"),
                "open_rate": performance.get("open_rate", 0),
                "click_rate": performance.get("click_rate", 0),
                "placed_order_rate": performance.get("conversion_rate", 0),
                "revenue_per_recipient": performance.get("revenue_per_recipient", 0),
                "revenue": performance.get("revenue", 0)
            })
        
        # Check for abandoned cart flow
        cart_flow = core_flows.get("abandoned_cart", {})
        if cart_flow.get("found", False):
            performance = cart_flow.get("performance", {})
            flows.append({
                "name": cart_flow.get("name", "Abandoned Cart Reminder"),
                "open_rate": performance.get("open_rate", 0),
                "click_rate": performance.get("click_rate", 0),
                "placed_order_rate": performance.get("conversion_rate", 0),
                "revenue_per_recipient": performance.get("revenue_per_recipient", 0),
                "revenue": performance.get("revenue", 0)
            })
        
        return {
            "flows": flows,  # Only includes flows that were found
            "benchmark": {
                "name": "Abandoned Cart",
                "open_rate": 54.74,
                "click_rate": 6.25,
                "conversion_rate": 3.36,
                "revenue_per_recipient": 3.80
            },
            "industry": "Apparel and Accessories",
            "recommendations": []
        }

