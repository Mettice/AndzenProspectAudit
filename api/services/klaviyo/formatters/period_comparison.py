"""
Period-over-period comparison formatter.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PeriodComparisonFormatter:
    """Formats period-over-period comparison data."""
    
    def __init__(self, revenue):
        """
        Initialize period comparison formatter.
        
        Args:
            revenue: RevenueTimeSeriesService instance
        """
        self.revenue = revenue
    
    async def calculate_comparison(
        self,
        current_totals: Dict[str, Any],
        current_period: Dict[str, Any],
        days: int,
        account_timezone: str,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate period-over-period comparison.
        
        Args:
            current_totals: Current period totals dict
            current_period: Current period dict with start_date/end_date
            days: Number of days in current period
            account_timezone: Account timezone
            verbose: Whether to log progress
            
        Returns:
            Dict with vs_previous_period, attributed_vs_previous, and previous_period_data
        """
        vs_previous_period = 0
        attributed_vs_previous = 0
        previous_period_data = None
        
        try:
            from ..utils.date_helpers import parse_iso_date, get_previous_period_range, get_klaviyo_compatible_range
            
            # Parse current period dates
            current_start_str = current_period.get("start_date", "")
            current_end_str = current_period.get("end_date", "")
            
            # Try to parse dates (format: "September 28, 2025")
            if current_start_str and current_end_str:
                try:
                    from dateutil import parser
                    current_start_dt = parser.parse(current_start_str)
                    current_end_dt = parser.parse(current_end_str)
                    
                    # Calculate previous period range
                    previous_range = get_previous_period_range(current_start_dt, current_end_dt, days)
                    
                    # Fetch previous period revenue data
                    if verbose:
                        logger.info(f"Fetching previous period data: {previous_range['start'].isoformat()} to {previous_range['end'].isoformat()}")
                    
                    # Get previous period date range in Klaviyo format
                    previous_days = (previous_range["end"] - previous_range["start"]).days + 1
                    previous_date_range = get_klaviyo_compatible_range(previous_days, account_timezone)
                    
                    # Fetch previous period revenue (simplified - just get totals)
                    previous_kav_data = await self.revenue.get_revenue_time_series(
                        days=previous_days,
                        interval="day",
                        account_timezone=account_timezone
                    )
                    
                    previous_totals = previous_kav_data.get("totals", {})
                    previous_total_revenue = previous_totals.get("total_revenue", 0)
                    previous_attributed_revenue = previous_totals.get("attributed_revenue", 0)
                    
                    # Calculate period-over-period changes
                    current_total = current_totals.get("total_revenue", 0)
                    current_attributed = current_totals.get("attributed_revenue", 0)
                    
                    if previous_total_revenue > 0:
                        vs_previous_period = ((current_total - previous_total_revenue) / previous_total_revenue) * 100
                    
                    if previous_attributed_revenue > 0:
                        attributed_vs_previous = ((current_attributed - previous_attributed_revenue) / previous_attributed_revenue) * 100
                    
                    previous_period_data = {
                        "total_revenue": previous_total_revenue,
                        "attributed_revenue": previous_attributed_revenue,
                        "period": previous_kav_data.get("period", {})
                    }
                    
                    if verbose:
                        logger.info(f"Previous period: ${previous_total_revenue:,.2f} total, ${previous_attributed_revenue:,.2f} attributed")
                        logger.info(f"Period-over-period: {vs_previous_period:+.1f}% total, {attributed_vs_previous:+.1f}% attributed")
                        
                except Exception as e:
                    logger.warning(f"Could not calculate previous period comparison: {e}")
        except Exception as e:
            logger.warning(f"Error calculating previous period: {e}", exc_info=True)
        
        return {
            "vs_previous_period": round(vs_previous_period, 1),
            "attributed_vs_previous": round(attributed_vs_previous, 1),
            "previous_period_data": previous_period_data
        }

