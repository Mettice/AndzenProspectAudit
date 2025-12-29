"""
Revenue data extraction module.
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class RevenueExtractor:
    """Extracts revenue data from Klaviyo."""
    
    def __init__(self, metrics, metric_aggregates):
        """
        Initialize revenue extractor.
        
        Args:
            metrics: MetricsService instance
            metric_aggregates: MetricAggregatesService instance
        """
        self.metrics = metrics
        self.metric_aggregates = metric_aggregates
    
    async def extract(
        self,
        start: str,
        end: str,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Extract revenue data.
        
        Args:
            start: Start date (ISO format with Z suffix)
            end: End date (ISO format with Z suffix)
            verbose: Whether to print progress messages
            
        Returns:
            Dict with revenue data
        """
        if verbose:
            print("📊 SECTION 1: Revenue Data")
            print("-" * 40)
        
        revenue_data: Dict[str, Any] = {}
        try:
            # Use Ordered Product metric for comprehensive revenue (matches dashboard)
            revenue_metric = await self.metrics.get_metric_by_name("Ordered Product")
            if not revenue_metric:
                # Fallback to Placed Order if Ordered Product not available
                revenue_metric = await self.metrics.get_metric_by_name("Placed Order")
            
            if revenue_metric:
                metric_id = revenue_metric.get("id")
                metric_name = revenue_metric.get("attributes", {}).get("name", "Unknown")
                if verbose:
                    print(f"  Found {metric_name} metric: {metric_id}")
                if metric_id:
                    revenue_data = await self.metric_aggregates.query(
                        metric_id=metric_id,
                        start_date=start,
                        end_date=end,
                        measurements=["count", "sum_value", "unique"]
                    )
                    if verbose:
                        print(f"  ✓ Revenue data extracted")
        except Exception as e:
            if verbose:
                print(f"  ✗ Error fetching revenue metric aggregates: {e}")
            logger.error(f"Error fetching revenue metric aggregates: {e}", exc_info=True)
        
        return revenue_data

