"""Campaign statistics service using Reporting API."""
from typing import Dict, List, Optional, Any
import logging

from ..client import KlaviyoClient
from ..filters import build_reporting_filter
from ..metrics.service import MetricsService

logger = logging.getLogger(__name__)


class CampaignStatisticsService:
    """Service for fetching campaign statistics using Reporting API."""
    
    def __init__(self, client: KlaviyoClient):
        """
        Initialize campaign statistics service.
        
        Args:
            client: KlaviyoClient instance
        """
        self.client = client
        self.metrics = MetricsService(client)
        # Cache conversion_metric_id to avoid multiple lookups
        self._cached_conversion_metric_id = None
    
    async def get_statistics(
        self,
        campaign_ids: List[str],
        statistics: Optional[List[str]] = None,
        timeframe: str = "last_30_days",
        conversion_metric_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get campaign statistics using Reporting API.
        
        This endpoint provides 1:1 matches with Klaviyo UI data.
        Reference: https://developers.klaviyo.com/en/reference/query_campaign_values
        
        IMPORTANT: conversion_metric_id is REQUIRED by the API.
        Filter syntax for Reporting API is different: use equals() or contains-any()
        
        Args:
            campaign_ids: List of campaign IDs
            statistics: List of statistics to fetch (opens, clicks, etc.)
            timeframe: Time period (last_30_days, last_365_days, etc.)
            conversion_metric_id: Metric ID for conversion tracking (REQUIRED)
            
        Returns:
            Dict with campaign statistics
        """
        if statistics is None:
            # Only use VALID statistics per API documentation
            # Note: "conversions" and "conversion_rate" are available when conversion_metric_id is provided
            statistics = [
                "opens",
                "open_rate",
                "clicks",
                "click_rate",
                "bounce_rate",
                "recipients",
                "delivery_rate",
                "unsubscribe_rate",
                "spam_complaint_rate",
                "conversions",  # Available when conversion_metric_id is provided
                "conversion_rate"  # Available when conversion_metric_id is provided
            ]
        
        # conversion_metric_id is REQUIRED
        if not conversion_metric_id:
            # Use cached value if available
            if self._cached_conversion_metric_id:
                logger.debug(f"Using cached conversion_metric_id: {self._cached_conversion_metric_id}")
                conversion_metric_id = self._cached_conversion_metric_id
            else:
                logger.warning(
                    "conversion_metric_id is required for campaign statistics. "
                    "Fetching Placed Order metric (preferring Shopify integration)..."
                )
                # Prefer Shopify integration to match dashboard
                placed_order = await self.metrics.get_metric_by_name("Placed Order", prefer_integration="shopify")
                if not placed_order:
                    placed_order = await self.metrics.get_metric_by_name("Placed Order")
                
                if placed_order:
                    conversion_metric_id = placed_order.get("id")
                    # Cache it for future use
                    self._cached_conversion_metric_id = conversion_metric_id
                    integration = placed_order.get("attributes", {}).get("integration", {})
                    logger.info(f"Using Placed Order metric: {conversion_metric_id} ({integration.get('name', 'Unknown')})")
                else:
                    logger.error(
                        "Could not find Placed Order metric and no conversion_metric_id provided"
                    )
                    return {}
        
        # Build filter using reporting API syntax
        filter_string = build_reporting_filter(campaign_ids, "campaign_id")
        
        payload = {
            "data": {
                "type": "campaign-values-report",
                "attributes": {
                    "statistics": statistics,
                    "timeframe": {"key": timeframe},
                    "filter": filter_string,
                    "conversion_metric_id": conversion_metric_id
                }
            }
        }
        
        try:
            return await self.client.request("POST", "/campaign-values-reports/", data=payload)
        except Exception as e:
            logger.error(f"Error fetching campaign statistics: {e}", exc_info=True)
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                logger.debug(f"Response: {e.response.text}")
            return {}

