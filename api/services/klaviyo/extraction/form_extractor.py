"""
Form performance data extraction module.
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class FormExtractor:
    """Extracts form performance data from Klaviyo."""
    
    def __init__(self, forms):
        """
        Initialize form extractor.
        
        Args:
            forms: FormsService instance
        """
        self.forms = forms
    
    async def extract(
        self,
        days_for_analysis: int,
        verbose: bool = True,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Extract form performance data.
        
        Args:
            days_for_analysis: Number of days for analysis period
            verbose: Whether to print progress messages
            date_range: Optional explicit date range with 'start' and 'end' ISO strings
            
        Returns:
            Dict with form performance data
        """
        period_label = f"{days_for_analysis} Days" if days_for_analysis < 365 else f"{days_for_analysis // 30} Months" if days_for_analysis < 730 else "Year to Date"
        if verbose:
            print(f"\n📝 SECTION 6: Form Performance ({period_label})")
            print("-" * 40)
        
        try:
            form_data = await self.forms.get_form_performance(days=days_for_analysis, date_range=date_range)
            
            if verbose:
                forms = form_data.get("forms", [])
                print(f"  ✓ Found {len(forms)} forms")
                for form in forms[:5]:
                    print(f"    - {form.get('name', 'Unknown')}: {form.get('submit_rate', 0):.2f}% ({form.get('standing', 'N/A')})")
            
            return form_data
        except Exception as e:
            if verbose:
                print(f"  ✗ Error fetching form data: {e}")
            logger.error(f"Error fetching form data: {e}", exc_info=True)
            return {"forms": []}

