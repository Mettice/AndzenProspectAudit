"""
KAV (Key Account Value) revenue time series extraction module.
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class KAVExtractor:
    """Extracts KAV revenue time series data from Klaviyo."""
    
    def __init__(self, revenue):
        """
        Initialize KAV extractor.
        
        Args:
            revenue: RevenueTimeSeriesService instance
        """
        self.revenue = revenue
    
    async def extract(
        self,
        days_for_analysis: int,
        account_timezone: str = "UTC",
        verbose: bool = True,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Extract KAV revenue time series data.
        
        Args:
            days_for_analysis: Number of days for analysis period
            account_timezone: Account timezone (default: UTC)
            verbose: Whether to print progress messages
            date_range: Optional custom date range (overrides days_for_analysis)
            
        Returns:
            Dict with KAV analysis data
        """
        # Determine period label
        if date_range and days_for_analysis >= 365:
            period_label = "Year to Date"
        elif days_for_analysis >= 365:
            period_label = "1 Year"
        elif days_for_analysis >= 180:
            period_label = f"{days_for_analysis // 30} Months"
        else:
            period_label = f"{days_for_analysis} Days"
            
        if verbose:
            print(f"\n💰 SECTION 4: KAV Revenue Time Series ({period_label})")
            print("-" * 40)
        
        try:
            # Use monthly interval for chart to match sample audit format
            # Sample shows monthly data (Nov, Dec, Jan, Feb) not daily
            kav_data = await self.revenue.get_revenue_time_series(
                days=days_for_analysis, 
                interval="month",  # Changed to monthly to match sample audit
                account_timezone=account_timezone,
                date_range=date_range
            )
            
            if verbose:
                totals = kav_data.get("totals", {})
                print(f"  ✓ Total Revenue: ${totals.get('total_revenue', 0):,.2f}")
                print(f"  ✓ Attributed Revenue: ${totals.get('attributed_revenue', 0):,.2f}")
                print(f"  ✓ KAV %: {totals.get('kav_percentage', 0):.1f}%")
                print(f"  ✓ Flow Revenue: ${totals.get('flow_revenue', 0):,.2f}")
                print(f"  ✓ Campaign Revenue: ${totals.get('campaign_revenue', 0):,.2f}")
            
            return kav_data
        except Exception as e:
            if verbose:
                print(f"  ✗ Error fetching KAV data: {e}")
            logger.error(f"Error fetching KAV data: {e}", exc_info=True)
            return {}

