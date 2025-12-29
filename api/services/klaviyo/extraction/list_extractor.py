"""
List growth data extraction module.
"""
import logging
from typing import Dict, Any

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
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Extract list growth data.
        
        Args:
            days_for_analysis: Number of days for analysis period
            verbose: Whether to print progress messages
            
        Returns:
            Dict with list growth data
        """
        # Convert days to months (approximate)
        months_for_analysis = max(1, days_for_analysis // 30)
        if verbose:
            print(f"\n📈 SECTION 5: List Growth Data ({months_for_analysis} Months)")
            print("-" * 40)
        
        try:
            list_growth = await self.lists.get_list_growth_data(months=months_for_analysis)
            
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

