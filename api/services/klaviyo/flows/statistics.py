"""Flow statistics service using Reporting API."""
from typing import Dict, List, Optional, Any
import logging

from ..client import KlaviyoClient
from ..filters import build_reporting_filter
from ..parsers import extract_statistics
from ..metrics.service import MetricsService
from .service import FlowsService

logger = logging.getLogger(__name__)


class FlowStatisticsService:
    """Service for fetching flow statistics using Reporting API."""
    
    def __init__(self, client: KlaviyoClient):
        """
        Initialize flow statistics service.
        
        Args:
            client: KlaviyoClient instance
        """
        self.client = client
        self.metrics = MetricsService(client)
        self.flows = FlowsService(client)
        # Cache conversion_metric_id to avoid multiple lookups
        self._cached_conversion_metric_id = None
        # Cache for flow statistics to avoid duplicate API calls
        # Key: (tuple(sorted(flow_ids)), timeframe, tuple(sorted(statistics)))
        # Value: cached response
        self._stats_cache = {}
    
    async def _resolve_conversion_metric_id(self, conversion_metric_id: Optional[str] = None) -> Optional[str]:
        """Resolve conversion metric ID with multiple fallback options."""
        if conversion_metric_id:
            # Cache it for future use
            self._cached_conversion_metric_id = conversion_metric_id
            return conversion_metric_id
        
        # Use cached value if available
        if self._cached_conversion_metric_id:
            logger.debug(f"Using cached conversion_metric_id: {self._cached_conversion_metric_id}")
            return self._cached_conversion_metric_id
        
        logger.warning(
            "conversion_metric_id is required for flow statistics. "
            "Attempting to resolve conversion metric with fallback options..."
        )
        
        # Try multiple metric names in order of preference
        metric_names = [
            "Ordered Product",   # Shopify integration - often the primary metric
            "Placed Order",      # Standard Klaviyo metric
            "Purchase",          # Alternative common name
            "Completed Order",   # Another alternative
            "Order",             # Simple variant
            "Checkout"           # Fallback for checkout events
        ]
        
        for metric_name in metric_names:
            try:
                # First try with Shopify integration preference
                logger.debug(f"Trying to resolve metric: {metric_name} (Shopify integration preferred)")
                metric = await self.metrics.get_metric_by_name(metric_name, prefer_integration="shopify")
                
                if not metric:
                    # Fallback to any integration
                    logger.debug(f"Trying to resolve metric: {metric_name} (any integration)")
                    metric = await self.metrics.get_metric_by_name(metric_name)
                
                if metric and metric.get("id"):
                    metric_id = metric.get("id")
                    # Cache the resolved metric ID
                    self._cached_conversion_metric_id = metric_id
                    integration = metric.get("attributes", {}).get("integration", {})
                    integration_name = integration.get("name", "Unknown") if integration else "None"
                    logger.info(f"Successfully resolved conversion metric: {metric_name} (ID: {metric_id}, Integration: {integration_name})")
                    return metric_id
                    
            except Exception as e:
                logger.warning(f"Failed to fetch {metric_name} metric: {e}")
                continue
        
        logger.error("Could not resolve any conversion metric ID from available options")
        return None
    
    async def _get_basic_statistics(self, flow_id: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Get basic flow statistics without requiring conversion metrics."""
        try:
            # Try to use Flow Message API for recipient counts as alternative
            # This approach doesn't require conversion metrics
            logger.debug(f"Attempting to fetch basic statistics for flow {flow_id} via alternative method")
            
            # Get flow messages to estimate recipient counts
            flow_messages = await self.flows.get_flow_messages(flow_id)
            
            if not flow_messages:
                logger.warning(f"No flow messages found for flow {flow_id}")
                return None
                
            # For now, return None to fall back to main statistics method
            # This is a placeholder for future implementation of alternative data sources
            return None
            
        except Exception as e:
            logger.debug(f"Alternative basic statistics method failed for flow {flow_id}: {e}")
            return None
    
    async def get_statistics(
        self,
        flow_ids: List[str],
        statistics: Optional[List[str]] = None,
        timeframe: str = "last_30_days",
        conversion_metric_id: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get flow statistics using Reporting API.
        
        This endpoint provides 1:1 matches with Klaviyo UI data.
        Reference: https://developers.klaviyo.com/en/reference/query_flow_values
        
        IMPORTANT: conversion_metric_id is REQUIRED by the API.
        Filter syntax: use equals() for single ID or contains-any() for multiple
        
        Args:
            flow_ids: List of flow IDs
            statistics: List of statistics to fetch
            timeframe: Time period
            conversion_metric_id: Metric ID for conversion tracking (REQUIRED)
            use_cache: Whether to use cached results if available (default True)
            
        Returns:
            Dict with flow statistics
        """
        if statistics is None:
            # Only use VALID statistics per API documentation
            statistics = [
                "opens",
                "open_rate",
                "clicks",
                "click_rate",
                "bounce_rate",
                "recipients",
                "delivery_rate",
                "unsubscribe_rate"
            ]
        
        # conversion_metric_id is REQUIRED
        if not conversion_metric_id:
            conversion_metric_id = await self._resolve_conversion_metric_id()
            if not conversion_metric_id:
                logger.error(
                    "Could not resolve any conversion metric ID and no conversion_metric_id provided"
                )
                return {}
        
        # Check cache first to avoid duplicate API calls
        if use_cache:
            cache_key = (
                tuple(sorted(flow_ids)),
                timeframe,
                tuple(sorted(statistics)),
                conversion_metric_id
            )
            if cache_key in self._stats_cache:
                logger.debug(f"Using cached flow statistics for {len(flow_ids)} flows")
                return self._stats_cache[cache_key]
        
        # Build filter - same syntax as campaigns
        filter_string = build_reporting_filter(flow_ids, "flow_id")
        
        payload = {
            "data": {
                "type": "flow-values-report",
                "attributes": {
                    "statistics": statistics,
                    "timeframe": {"key": timeframe},
                    "filter": filter_string,
                    "conversion_metric_id": conversion_metric_id
                }
            }
        }
        
        try:
            response = await self.client.request(
                "POST",
                "/flow-values-reports/",
                data=payload,
                retry_on_429=True,
                max_retries=3
            )
            
            # Cache the response
            if use_cache and response:
                cache_key = (
                    tuple(sorted(flow_ids)),
                    timeframe,
                    tuple(sorted(statistics)),
                    conversion_metric_id
                )
                self._stats_cache[cache_key] = response
                # Limit cache size to prevent memory issues (keep last 50 entries)
                if len(self._stats_cache) > 50:
                    # Remove oldest entry (simple FIFO)
                    oldest_key = next(iter(self._stats_cache))
                    del self._stats_cache[oldest_key]
            
            return response
        except Exception as e:
            logger.error(f"Error fetching flow statistics: {e}", exc_info=True)
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                try:
                    logger.debug(f"Response: {e.response.text}")
                except Exception:
                    pass
            return {}
    
    async def get_individual_stats(
        self,
        flow_id: str,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        Get detailed statistics for a single flow.
        
        Args:
            flow_id: The flow ID to get stats for
            days: Number of days to look back
            
        Returns:
            Dict with detailed flow performance metrics
        """
        # Get flow details
        flow = await self.flows.get_flow(flow_id)
        if not flow:
            return {"error": f"Flow {flow_id} not found"}
        
        flow_attrs = flow.get("attributes", {})
        flow_name = flow_attrs.get("name", "Unknown")
        flow_status = flow_attrs.get("status", "unknown")
        
        # Get flow actions (emails)
        actions = await self.flows.get_flow_actions(flow_id)
        email_count = len([
            a for a in actions 
            if a.get("attributes", {}).get("action_type") == "EMAIL"
        ])
        
        # Get conversion metric using enhanced resolution
        conversion_metric_id = await self._resolve_conversion_metric_id()
        
        # Get flow statistics
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
        
        stats = {}
        
        # Try to get basic statistics first (without conversion metrics)
        try:
            basic_stats_response = await self._get_basic_statistics(flow_id, timeframe)
            if basic_stats_response:
                basic_stats = extract_statistics(basic_stats_response)
                stats.update(basic_stats)
                logger.debug(f"Retrieved basic statistics for flow {flow_id}: {basic_stats}")
        except Exception as e:
            logger.warning(f"Failed to get basic statistics for flow {flow_id}: {e}")
        
        # Try to get conversion statistics if we have a metric ID
        if conversion_metric_id:
            try:
                stats_response = await self.get_statistics(
                    flow_ids=[flow_id],
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
                    timeframe=timeframe,
                    conversion_metric_id=conversion_metric_id
                )
                
                # Extract stats from response and merge with basic stats
                if stats_response:
                    conversion_stats = extract_statistics(stats_response)
                    stats.update(conversion_stats)
                    logger.debug(f"Retrieved conversion statistics for flow {flow_id}: {conversion_stats}")
                    
            except Exception as e:
                logger.warning(f"Failed to get conversion statistics for flow {flow_id}: {e}")
        else:
            logger.warning(f"No conversion metric available for flow {flow_id}, skipping conversion statistics")
        
        # Calculate revenue per recipient if we have both values
        recipients = stats.get("recipients", 0)
        revenue = stats.get("revenue", 0)
        if recipients > 0 and revenue > 0:
            stats["revenue_per_recipient"] = revenue / recipients
        else:
            stats["revenue_per_recipient"] = 0
        
        # Ensure basic structure even if API calls fail
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
        
        return {
            "flow_id": flow_id,
            "flow_name": flow_name,
            "status": flow_status,
            "email_count": email_count,
            "performance": stats,
            "actions": [
                {
                    "id": a.get("id"),
                    "type": a.get("attributes", {}).get("action_type"),
                    "name": a.get("attributes", {}).get("name", "")
                }
                for a in actions
            ]
        }

