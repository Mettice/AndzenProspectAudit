"""
List growth data extraction module.
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ListExtractor:
    """Extracts list growth data from Klaviyo."""
    
    def __init__(self, lists):
        """
        Initialize list extractor.
        
        Args:
            lists: ListsService instance
        """
        self.lists = lists
    
    async def extract(
        self,
        days_for_analysis: int,
        date_range: Optional[Dict[str, str]] = None,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Extract list growth data.
        
        Args:
            days_for_analysis: Number of days for analysis period
            date_range: Optional explicit date range (for YTD or custom ranges)
            verbose: Whether to print progress messages
            
        Returns:
            Dict with list growth data
        """
        # Convert days to months (approximate), but cap at 6 months for API compatibility
        months_for_analysis = max(1, min(days_for_analysis // 30, 6))
        if verbose:
            print(f"\n📈 SECTION 5: List Growth Data ({months_for_analysis} Months)")
            print("-" * 40)
        
        try:
            # Pass date_range if provided to optimize API calls (reduces API calls for YTD)
            list_growth = await self.lists.get_list_growth_data(
                months=months_for_analysis,
                date_range=date_range
            )
            
            if verbose:
                print(f"  ✓ List: {list_growth.get('list_name', 'Unknown')}")
                print(f"  ✓ Current subscribers: {list_growth.get('current_total', 0):,}")
                print(f"  ✓ New subscribers: {list_growth.get('growth_subscribers', 0):,}")
                print(f"  ✓ Lost subscribers: {list_growth.get('lost_subscribers', 0):,}")
                print(f"  ✓ Churn rate: {list_growth.get('churn_rate', 0):.2f}%")
            
            return list_growth
        except Exception as e:
            if verbose:
                print(f"  ✗ Error fetching list growth data: {e}")
            logger.error(f"Error fetching list growth data: {e}", exc_info=True)
            return {}

