"""Flow pattern matching for identifying core flows."""
from typing import Dict, List, Any
import logging

from .service import FlowsService
from .statistics import FlowStatisticsService

logger = logging.getLogger(__name__)


class FlowPatternMatcher:
    """Service for identifying flows by name patterns."""
    
    # Flow identification patterns (Enhanced 2025)
    FLOW_PATTERNS = {
        "welcome_series": ["welcome", "nurture", "onboard", "new customer", "first time", "ns-", "-ns-"],
        "browse_abandonment": ["browse", "abandon", "viewed", "product view", "ba-", "-ba-"],
        "abandoned_checkout": ["checkout", "abandon", "ac-", "-ac-", "started checkout"],  
        "abandoned_cart": ["abandon", "cart", "add to cart", "atc-", "-atc-"],
        "post_purchase": ["post", "purchase", "thank", "order confirm", "pp-", "-pp-", "fpf", "first-to-second"],
        "back_in_stock": ["back in stock", "restock", "back-in-stock", "bis-", "-bis-", "inventory"],
        "winback": ["winback", "win back", "lapsed", "re-engage", "lc-", "-lc-", "customer"]
    }
    
    def __init__(self, flows_service: FlowsService, stats_service: FlowStatisticsService):
        """
        Initialize flow pattern matcher.
        
        Args:
            flows_service: FlowsService instance
            stats_service: FlowStatisticsService instance
        """
        self.flows = flows_service
        self.stats = stats_service
    
    def identify_flow_type(self, flow_name: str) -> str:
        """
        Identify flow type by name pattern.
        
        Args:
            flow_name: Name of the flow
            
        Returns:
            Flow type key or None
        """
        flow_name_lower = flow_name.lower()
        
        # Check for browse abandonment first (more specific)
        if "browse" in flow_name_lower and "abandon" in flow_name_lower:
            return "browse_abandonment"
        
        # Check for abandoned checkout (more specific than cart)
        # Patterns: "checkout" + "abandon", "as-" + "abandon" (AS = Abandon Search/Checkout), "ac-" prefix
        if ("checkout" in flow_name_lower and "abandon" in flow_name_lower) or \
           (flow_name_lower.startswith("as-") and "abandon" in flow_name_lower) or \
           (flow_name_lower.startswith("ac-")) or \
           ("-as-" in flow_name_lower and "abandon" in flow_name_lower):
            return "abandoned_checkout"
        
        # Then check other patterns
        for flow_type, patterns in self.FLOW_PATTERNS.items():
            # Skip browse_abandonment and abandoned_checkout as we handled them above
            if flow_type in ["browse_abandonment", "abandoned_checkout"]:
                continue
                
            if any(pattern in flow_name_lower for pattern in patterns):
                return flow_type
        return None
    
    async def get_core_flows_performance(
        self,
        days: int = 90,
        limit_flows: int = 10
    ) -> Dict[str, Any]:
        """
        Get performance data for core flows (Welcome, AC, Browse, Post-Purchase).
        
        Identifies flows by name patterns and returns performance metrics.
        Limits the number of flows queried to avoid rate limiting.
        
        Args:
            days: Number of days for analysis
            limit_flows: Maximum number of flows to query (default 10 to avoid rate limits)
            
        Returns:
            Dict mapping flow types to their performance data
        """
        flows = await self.flows.get_flows()
        
        core_flows = {}
        flows_queried = 0
        
        # First pass: Identify flows by pattern (no API calls)
        identified_flows = {}
        for flow in flows:
            flow_name = flow.get("attributes", {}).get("name", "").lower()
            flow_id = flow.get("id")
            flow_status = flow.get("attributes", {}).get("status", "unknown")
            
            # Check each pattern
            flow_type = self.identify_flow_type(flow.get("attributes", {}).get("name", ""))
            if flow_type:
                # Only store if we haven't found this type yet, or this one is live
                if flow_type not in identified_flows or flow_status == "live":
                    identified_flows[flow_type] = {
                        "flow": flow,
                        "flow_id": flow_id,
                        "flow_status": flow_status
                    }
        
        # Second pass: Query statistics for identified flows (with rate limiting)
        for flow_type, flow_info in identified_flows.items():
            if flows_queried >= limit_flows:
                logger.warning(f"Reached flow query limit ({limit_flows}). Skipping remaining flows.")
                break
            
            flow_id = flow_info["flow_id"]
            flow = flow_info["flow"]
            
            # Get detailed stats for this flow (with rate limiting built-in)
            flow_stats = await self.stats.get_individual_stats(flow_id, days)
            flows_queried += 1
            
            core_flows[flow_type] = {
                "flow_id": flow_id,
                "name": flow.get("attributes", {}).get("name"),
                "status": flow_info["flow_status"],
                "email_count": flow_stats.get("email_count", 0),
                "performance": flow_stats.get("performance", {}),
                "found": True
            }
            
            # Small delay between flow queries
            if flows_queried < len(identified_flows):
                import asyncio
                await asyncio.sleep(0.2)
        
        # Mark missing flows
        for flow_type in self.FLOW_PATTERNS.keys():
            if flow_type not in core_flows:
                core_flows[flow_type] = {
                    "name": flow_type.replace("_", " ").title(),
                    "status": "missing",
                    "email_count": 0,
                    "performance": {},
                    "found": False
                }
        
        return core_flows

