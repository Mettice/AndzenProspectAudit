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
        Uses batched API calls to reduce rate limiting issues.
        
        Args:
            days: Number of days for analysis
            limit_flows: Maximum number of flows to query (default 10 to avoid rate limits)
            
        Returns:
            Dict mapping flow types to their performance data
        """
        import asyncio
        
        flows = await self.flows.get_flows()
        
        core_flows = {}
        
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
        
        # Limit to max flows
        if len(identified_flows) > limit_flows:
            # Prioritize live flows
            live_flows = {k: v for k, v in identified_flows.items() if v["flow_status"] == "live"}
            other_flows = {k: v for k, v in identified_flows.items() if v["flow_status"] != "live"}
            identified_flows = dict(list(live_flows.items())[:limit_flows] + list(other_flows.items())[:limit_flows - len(live_flows)])
        
        if not identified_flows:
            # Mark all flows as missing
            for flow_type in self.FLOW_PATTERNS.keys():
                core_flows[flow_type] = {
                    "name": flow_type.replace("_", " ").title(),
                    "status": "missing",
                    "email_count": 0,
                    "performance": {},
                    "found": False
                }
            return core_flows
        
        # Map days to timeframe string for API
        timeframe_map = {
            7: "last_7_days",
            30: "last_30_days",
            90: "last_90_days",
            365: "last_365_days"
        }
        timeframe = timeframe_map.get(days, "last_90_days")
        if days > 365:
            timeframe = "last_365_days"
        
        # OPTIMIZATION: Batch all flow statistics in ONE API call instead of individual calls
        flow_ids = [flow_info["flow_id"] for flow_info in identified_flows.values()]
        
        # Get flow details and actions in parallel (these are lightweight)
        flow_details_tasks = []
        flow_actions_tasks = []
        for flow_type, flow_info in identified_flows.items():
            flow_id = flow_info["flow_id"]
            flow_details_tasks.append((flow_type, self.flows.get_flow(flow_id)))
            flow_actions_tasks.append((flow_type, self.flows.get_flow_actions(flow_id)))
        
        # Fetch flow details and actions in parallel
        flow_details_results = {}
        flow_actions_results = {}
        
        for flow_type, task in flow_details_tasks:
            try:
                flow_details_results[flow_type] = await task
            except Exception as e:
                logger.warning(f"Error fetching flow details for {flow_type}: {e}")
                flow_details_results[flow_type] = None
        
        # Small delay before fetching actions
        await asyncio.sleep(0.5)
        
        for flow_type, task in flow_actions_tasks:
            try:
                flow_actions_results[flow_type] = await task
            except Exception as e:
                logger.warning(f"Error fetching flow actions for {flow_type}: {e}")
                flow_actions_results[flow_type] = []
        
        # CRITICAL FIX: Batch statistics call for ALL flows at once
        # This reduces 7-10 individual API calls to just 1 call
        try:
            batched_stats_response = await self.stats.get_statistics(
                flow_ids=flow_ids,
                statistics=[
                    "recipients",
                    "opens", 
                    "open_rate",
                    "clicks",
                    "click_rate",
                    "conversions",
                    "conversion_rate", 
                    "conversion_value",
                    "conversion_uniques"
                ],
                timeframe=timeframe
            )
            
            # Parse batched results into a dict keyed by flow_id
            # Statistics are grouped by flow_message_id, so we need to aggregate by flow_id
            batched_stats_by_flow_id = {}
            if batched_stats_response and "data" in batched_stats_response:
                results = batched_stats_response.get("data", {}).get("attributes", {}).get("results", [])
                logger.info(f"Parsing {len(results)} flow statistics results")
                
                # Helper function to aggregate statistics
                def aggregate_stats(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
                    """Aggregate statistics from multiple messages in the same flow."""
                    if not existing:
                        return new.copy()
                    
                    aggregated = {
                        "recipients": existing.get("recipients", 0) + new.get("recipients", 0),
                        "opens": existing.get("opens", 0) + new.get("opens", 0),
                        "clicks": existing.get("clicks", 0) + new.get("clicks", 0),
                        "conversions": existing.get("conversions", 0) + new.get("conversions", 0),
                        "conversion_uniques": existing.get("conversion_uniques", 0) + new.get("conversion_uniques", 0),
                        "revenue": existing.get("revenue", 0) + new.get("revenue", 0),
                        "conversion_value": existing.get("conversion_value", 0) + new.get("conversion_value", 0)
                    }
                    
                    # Recalculate rates after aggregation
                    recipients = aggregated["recipients"]
                    if recipients > 0:
                        aggregated["open_rate"] = (aggregated["opens"] / recipients) * 100
                        aggregated["click_rate"] = (aggregated["clicks"] / recipients) * 100
                        aggregated["conversion_rate"] = (aggregated["conversions"] / recipients) * 100
                    else:
                        aggregated["open_rate"] = 0
                        aggregated["click_rate"] = 0
                        aggregated["conversion_rate"] = 0
                    
                    return aggregated
                
                for result in results:
                    # Extract flow_id from groupings (not from result.id)
                    groupings = result.get("groupings", {})
                    flow_id = groupings.get("flow_id")
                    
                    if flow_id:
                        from ..parsers import extract_statistics
                        stats = extract_statistics({"data": {"attributes": {"results": [result]}}})
                        if stats:
                            # Aggregate statistics for this flow_id (sum across all messages)
                            if flow_id in batched_stats_by_flow_id:
                                batched_stats_by_flow_id[flow_id] = aggregate_stats(
                                    batched_stats_by_flow_id[flow_id], 
                                    stats
                                )
                            else:
                                batched_stats_by_flow_id[flow_id] = stats
                            
                            # Log aggregated totals after adding this message's stats
                            total_recipients = batched_stats_by_flow_id[flow_id].get("recipients", 0)
                            total_revenue = batched_stats_by_flow_id[flow_id].get("revenue", 0)
                            logger.debug(f"Added stats for flow {flow_id} message: recipients={stats.get('recipients', 0)}, revenue={stats.get('revenue', 0)} | Flow totals: recipients={total_recipients}, revenue={total_revenue}")
                        else:
                            logger.warning(f"No statistics extracted for flow {flow_id} - result statistics may be empty")
                    else:
                        logger.warning(f"Flow result missing flow_id in groupings: {result}")
                
                # Log summary of aggregated statistics
                if batched_stats_by_flow_id:
                    logger.info(f"Aggregated statistics for {len(batched_stats_by_flow_id)} flows:")
                    for fid, agg_stats in batched_stats_by_flow_id.items():
                        logger.info(f"  Flow {fid}: recipients={agg_stats.get('recipients', 0)}, revenue=${agg_stats.get('revenue', 0):.2f}, open_rate={agg_stats.get('open_rate', 0):.2f}%")
            else:
                logger.warning(f"Batched stats response missing data: {batched_stats_response}")
        except Exception as e:
            logger.error(f"Error fetching batched flow statistics: {e}", exc_info=True)
            batched_stats_by_flow_id = {}
        
        # Combine all data for each flow
        for flow_type, flow_info in identified_flows.items():
            flow_id = flow_info["flow_id"]
            flow = flow_info["flow"]
            
            # Get flow details
            flow_detail = flow_details_results.get(flow_type) or flow
            flow_attrs = flow_detail.get("attributes", {}) if flow_detail else {}
            flow_name = flow_attrs.get("name", flow.get("attributes", {}).get("name", "Unknown"))
            flow_status = flow_info["flow_status"]
            
            # Get email count from actions
            actions = flow_actions_results.get(flow_type, [])
            email_count = len([
                a for a in actions 
                if a.get("attributes", {}).get("action_type") == "EMAIL"
            ])
            
            # Get statistics from batched response
            stats = batched_stats_by_flow_id.get(flow_id, {})
            if not stats:
                logger.warning(f"No statistics found for flow {flow_id} ({flow_name}) - flow may have no deliveries or statistics API returned no data")
            
            # Calculate revenue per recipient
            recipients = stats.get("recipients", 0)
            revenue = stats.get("revenue", 0) or stats.get("conversion_value", 0)
            if recipients > 0 and revenue > 0:
                stats["revenue_per_recipient"] = revenue / recipients
            else:
                stats["revenue_per_recipient"] = 0
            
            # Ensure basic structure - only set defaults if stats is completely empty
            if not stats:
                stats = {
                    "recipients": 0,
                    "opens": 0,
                    "open_rate": 0,
                    "clicks": 0,
                    "click_rate": 0,
                    "conversions": 0,
                    "conversion_rate": 0,
                    "revenue": 0,
                    "revenue_per_recipient": 0
                }
            else:
                # Ensure all required keys exist (in case extract_statistics returned partial data)
                stats.setdefault("recipients", 0)
                stats.setdefault("opens", 0)
                stats.setdefault("open_rate", 0)
                stats.setdefault("clicks", 0)
                stats.setdefault("click_rate", 0)
                stats.setdefault("conversions", 0)
                stats.setdefault("conversion_rate", 0)
                stats.setdefault("revenue", 0)
                stats.setdefault("revenue_per_recipient", 0)
            
            core_flows[flow_type] = {
                "flow_id": flow_id,
                "name": flow_name,
                "status": flow_status,
                "email_count": email_count,
                "performance": stats,
                "found": True
            }
        
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

