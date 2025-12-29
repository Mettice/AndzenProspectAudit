"""Metric aggregates query service."""
from typing import Dict, List, Optional, Any
import logging

from ..client import KlaviyoClient
from ..filters import build_metric_filter
from ..parsers import parse_aggregate_data, parse_metric_value

logger = logging.getLogger(__name__)


class MetricAggregatesService:
    """Service for querying metric aggregates."""
    
    def __init__(self, client: KlaviyoClient):
        """
        Initialize metric aggregates service.
        
        Args:
            client: KlaviyoClient instance
        """
        self.client = client
    
    async def query(
        self,
        metric_id: str,
        start_date: str,
        end_date: str,
        measurements: Optional[List[str]] = None,
        interval: str = "day",
        by: Optional[List[str]] = None,
        filter_conditions: Optional[List[str]] = None,
        timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """
        Query metric aggregates using POST /metric-aggregates/.
        
        This is the CORRECT endpoint per Klaviyo documentation.
        It requires POST with JSON body, not GET with params.
        
        Reference: https://developers.klaviyo.com/en/reference/query_metric_aggregates
        
        Args:
            metric_id: The metric ID to query
            start_date: Start datetime in ISO format (e.g., "2025-11-17T00:00:00Z")
            end_date: End datetime in ISO format
            measurements: List of measurements (e.g., ["count", "sum_value", "unique"])
            interval: Time interval (day, week, month)
            by: List of dimensions to group by (e.g., ["$message", "$flow"])
            filter_conditions: Additional filter conditions beyond datetime
            timezone: Timezone for processing (e.g., "Australia/Sydney", "UTC")
        
        Returns:
            Dict with metric aggregate data
        """
        if measurements is None:
            measurements = ["count", "sum_value", "unique"]
        
        # Build filter array - datetime filters are required
        filters = build_metric_filter(start_date, end_date, filter_conditions)
        
        payload = {
            "data": {
                "type": "metric-aggregate",
                "attributes": {
                    "metric_id": metric_id,
                    "measurements": measurements,
                    "interval": interval,
                    "filter": filters,
                    "timezone": timezone
                }
            }
        }
        
        # Add grouping if specified
        if by:
            payload["data"]["attributes"]["by"] = by
        
        # Log payload for debugging (especially for subscription metrics)
        if "Subscribed" in metric_id or "Unsubscribed" in metric_id or interval == "month":
            logger.debug(f"Metric aggregates payload for {metric_id}: {payload}")
        
        try:
            # Client already doesn't retry 400 errors, so this will fail fast
            response = await self.client.request("POST", "/metric-aggregates/", data=payload)
            # Log successful response for debugging
            if response:
                logger.debug(f"Successfully queried metric {metric_id}, got response with keys: {list(response.keys())}")
            return response
        except Exception as e:
            # Some metrics (like "Subscribed to List", "Unsubscribed") may not support aggregation
            # Log as warning instead of error to reduce noise
            error_msg = str(e)
            if "400 Bad Request" in error_msg or "400" in error_msg:
                logger.warning(f"Metric {metric_id} returned 400 Bad Request. Skipping this metric (no retries).")
                logger.warning(f"Date range: {start_date} to {end_date}, Interval: {interval}")
                # Don't log full payload for 400s to reduce noise
            else:
                logger.warning(f"Error querying metric aggregates for {metric_id}: {e}")
            return {}
    
    def parse_response(self, response: Dict[str, Any]) -> Dict[str, List]:
        """
        Parse metric aggregates response into structured format.
        
        Args:
            response: Raw API response
            
        Returns:
            Dict with 'dates' and 'values' lists
        """
        dates, values = parse_aggregate_data(response)
        
        # Parse values based on structure
        parsed_values = []
        for val in values:
            parsed_values.append(parse_metric_value(val))
        
        return {
            "dates": dates,
            "values": parsed_values
        }

