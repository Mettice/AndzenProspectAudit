"""
Campaign performance formatting module.
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class CampaignFormatter:
    """Formats campaign performance data."""
    
    def calculate_summary(
        self,
        campaign_statistics: Dict[str, Any],
        campaign_revenue: float,
        campaigns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate campaign performance summary from statistics.
        
        Args:
            campaign_statistics: Raw campaign statistics from API
            campaign_revenue: Total campaign revenue from KAV data
            campaigns: List of campaign objects
            
        Returns:
            Formatted campaign performance data
        """
        # Extract statistics from API response
        results = campaign_statistics.get("data", {}).get("attributes", {}).get("results", [])
        
        if not results:
            # Return default structure if no data
            return {
                "summary": {
                    "avg_open_rate": 0,
                    "avg_click_rate": 0,
                    "avg_placed_order_rate": 0,
                    "total_revenue": campaign_revenue,  # Use revenue from KAV data
                    "total_sent": 0  # Add missing total_sent field
                },
                "benchmark": {
                    "industry": "Apparel and Accessories",
                    "open_rate": 44.50,
                    "click_rate": 1.66,
                    "conversion_rate": 0.07,
                    "revenue_per_recipient": 0.09
                },
                "vs_benchmark": {
                    "open_rate": "meets",
                    "click_rate": "meets",
                    "conversion_rate": "meets"
                },
                "analysis": {
                    "campaigns_per_month": len(campaigns) // 3 if campaigns else 0,
                    "primary_list": "",
                    "segmentation_used": False,
                    "issues_identified": []
                },
                "recommendations": []
            }
        
        # Calculate averages from all campaign results
        total_opens = 0
        total_clicks = 0
        total_conversions = 0
        total_recipients = 0
        campaign_count = 0
        
        for result in results:
            stats = result.get("statistics", {})
            recipients = stats.get("recipients", 0)
            
            if recipients > 0:  # Only count campaigns with recipients
                conversions = stats.get("conversions", 0)
                total_opens += stats.get("opens", 0)
                total_clicks += stats.get("clicks", 0)
                total_conversions += conversions
                total_recipients += recipients
                campaign_count += 1
                
                # Log if conversions are missing
                if conversions == 0 and stats.get("clicks", 0) > 0:
                    logger.debug(f"Campaign {result.get('campaign_id', 'unknown')}: {recipients} recipients, {stats.get('clicks', 0)} clicks, but 0 conversions")
        
        logger.info(f"Campaign summary: {campaign_count} campaigns, {total_recipients} recipients, {total_conversions} conversions, {total_opens} opens, {total_clicks} clicks")
        
        # Calculate average rates
        avg_open_rate = (total_opens / total_recipients * 100) if total_recipients > 0 else 0
        avg_click_rate = (total_clicks / total_recipients * 100) if total_recipients > 0 else 0
        avg_placed_order_rate = (total_conversions / total_recipients * 100) if total_recipients > 0 else 0
        
        # Determine status vs benchmark
        def get_status(metric_val, benchmark_avg):
            if metric_val >= benchmark_avg * 1.1:
                return "exceeds"
            elif metric_val >= benchmark_avg * 0.9:
                return "meets"
            else:
                return "below"
        
        return {
            "summary": {
                "avg_open_rate": round(avg_open_rate, 2),
                "avg_click_rate": round(avg_click_rate, 2),
                "avg_placed_order_rate": round(avg_placed_order_rate, 2),
                "total_revenue": campaign_revenue,  # Use revenue from KAV data
                "total_sent": total_recipients  # Add missing total_sent field
            },
            "benchmark": {
                "industry": "Apparel and Accessories",
                "open_rate": 44.50,
                "click_rate": 1.66,
                "conversion_rate": 0.07,
                "revenue_per_recipient": 0.09
            },
            "vs_benchmark": {
                "open_rate": get_status(avg_open_rate, 44.50),
                "click_rate": get_status(avg_click_rate, 1.66),
                "conversion_rate": get_status(avg_placed_order_rate, 0.07)
            },
            "analysis": {
                "campaigns_per_month": len(campaigns) // 3 if campaigns else 0,
                "primary_list": "",
                "segmentation_used": False,
                "issues_identified": []
            },
            "recommendations": []
        }

