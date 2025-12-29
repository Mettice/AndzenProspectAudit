"""Metrics service for fetching Klaviyo metrics."""
from typing import Dict, List, Optional, Any
import logging

from ..client import KlaviyoClient

logger = logging.getLogger(__name__)


class MetricsService:
    """Service for interacting with Klaviyo metrics."""
    
    def __init__(self, client: KlaviyoClient):
        """
        Initialize metrics service.
        
        Args:
            client: KlaviyoClient instance
        """
        self.client = client
    
    async def get_metrics(self) -> List[Dict[str, Any]]:
        """
        Get all metrics from Klaviyo account.
        
        Returns:
            List of metric objects
        """
        try:
            response = await self.client.request("GET", "/metrics/")
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Error fetching metrics: {e}", exc_info=True)
            return []
    
    async def get_metric_by_name(
        self, 
        metric_name: str, 
        prefer_integration: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a metric by its name.
        
        Args:
            metric_name: Name of the metric (e.g., "Placed Order")
            prefer_integration: If multiple metrics match, prefer this integration
                              (e.g., "shopify", "api"). Integration key is checked.
            
        Returns:
            Metric object if found, None otherwise
        """
        metrics = await self.get_metrics()
        matches = []
        
        for metric in metrics:
            if metric.get("attributes", {}).get("name") == metric_name:
                matches.append(metric)
        
        if not matches:
            logger.warning(f"Metric '{metric_name}' not found in {len(metrics)} available metrics")
            return None
        
        # If only one match, return it
        if len(matches) == 1:
            return matches[0]
        
        # If multiple matches and prefer_integration specified, find the preferred one
        if prefer_integration:
            for metric in matches:
                integration = metric.get("attributes", {}).get("integration", {})
                integration_key = integration.get("key", "").lower()
                if integration_key == prefer_integration.lower():
                    logger.info(
                        f"Found {len(matches)} metrics named '{metric_name}', "
                        f"using {prefer_integration} integration: {metric.get('id')}"
                    )
                    return metric
        
        # If no preference or preference not found, return first match with warning
        logger.warning(
            f"Found {len(matches)} metrics named '{metric_name}', "
            f"returning first match: {matches[0].get('id')}. "
            f"Consider using prefer_integration parameter."
        )
        return matches[0]
    
    async def get_metric_by_id(self, metric_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a metric by its ID.
        
        Args:
            metric_id: Metric ID
            
        Returns:
            Metric object if found, None otherwise
        """
        try:
            response = await self.client.request("GET", f"/metrics/{metric_id}/")
            return response.get("data")
        except Exception as e:
            logger.error(f"Error fetching metric {metric_id}: {e}", exc_info=True)
            return None

