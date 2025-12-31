"""
Campaign data extraction module.
"""
import asyncio
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class CampaignExtractor:
    """Extracts campaign data from Klaviyo."""
    
    def __init__(self, campaigns, campaign_stats):
        """
        Initialize campaign extractor.
        
        Args:
            campaigns: CampaignsService instance
            campaign_stats: CampaignStatisticsService instance
        """
        self.campaigns = campaigns
        self.campaign_stats = campaign_stats
    
    async def extract(
        self,
        start: str,
        end: str,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Extract campaign data and statistics for all channels (Email, SMS, Push).
        
        Args:
            start: Start date (ISO format with Z suffix)
            end: End date (ISO format with Z suffix)
            verbose: Whether to print progress messages
            
        Returns:
            Dict with 'campaigns', 'campaign_statistics', and channel breakdown
        """
        if verbose:
            print("\n📧 SECTION 2: Campaign Data")
            print("-" * 40)
        
        # Fetch campaigns for all channels
        all_campaigns = []
        email_campaigns = await self.campaigns.get_campaigns(start, end, "email")
        all_campaigns.extend(email_campaigns)
        if verbose:
            print(f"  ✓ Fetched {len(email_campaigns)} email campaigns")
        
        sms_campaigns = await self.campaigns.get_campaigns(start, end, "sms")
        all_campaigns.extend(sms_campaigns)
        if verbose:
            print(f"  ✓ Fetched {len(sms_campaigns)} SMS campaigns")
        
        # Push campaigns: Klaviyo API doesn't support push channel filter
        # The campaigns endpoint returns 400 Bad Request for push channel
        # Push campaigns may need to be fetched differently or aren't available via this endpoint
        push_campaigns = []
        try:
            push_campaigns = await self.campaigns.get_campaigns(start, end, "push")
            all_campaigns.extend(push_campaigns)
            if verbose:
                print(f"  ✓ Fetched {len(push_campaigns)} push campaigns")
        except Exception as e:
            # Push campaigns not supported via campaigns endpoint (API limitation)
            # This is expected - Klaviyo API doesn't support push channel filter
            if verbose:
                logger.debug(f"Push campaigns not available via campaigns endpoint (API limitation): {e}")
                print(f"  ⚠ Push campaigns not available (Klaviyo API limitation - push channel not supported)")
            push_campaigns = []
        
        # Get statistics for all campaigns
        campaign_statistics = {}
        if all_campaigns:
            # Batch campaigns to reduce API load
            all_campaign_ids = [c["id"] for c in all_campaigns[:50]]
            batch_size = 15  # Process 15 campaigns at a time to reduce rate limiting
            
            if verbose:
                print(f"  Fetching statistics for {len(all_campaign_ids)} campaigns in batches of {batch_size}...")
            
            # Resolve conversion_metric_id once before processing batches
            # This prevents repeated lookups and warnings
            conversion_metric_id = None
            if hasattr(self.campaign_stats, '_cached_conversion_metric_id') and self.campaign_stats._cached_conversion_metric_id:
                conversion_metric_id = self.campaign_stats._cached_conversion_metric_id
            else:
                # Trigger resolution on first batch (will cache it)
                # We'll get it from the cache after first call
                pass
            
            # Process campaigns in batches with delays
            for i in range(0, len(all_campaign_ids), batch_size):
                batch_ids = all_campaign_ids[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(all_campaign_ids) + batch_size - 1) // batch_size
                
                if verbose and total_batches > 1:
                    print(f"    Processing batch {batch_num}/{total_batches} ({len(batch_ids)} campaigns)...")
                
                try:
                    # Use cached conversion_metric_id if available (after first batch)
                    if conversion_metric_id is None and hasattr(self.campaign_stats, '_cached_conversion_metric_id'):
                        conversion_metric_id = self.campaign_stats._cached_conversion_metric_id
                    
                    batch_stats = await self.campaign_stats.get_statistics(
                        campaign_ids=batch_ids,
                        timeframe="last_365_days",
                        conversion_metric_id=conversion_metric_id  # Pass it explicitly to avoid repeated lookups
                    )
                    
                    # After first batch, get the cached value for subsequent batches
                    if conversion_metric_id is None and hasattr(self.campaign_stats, '_cached_conversion_metric_id'):
                        conversion_metric_id = self.campaign_stats._cached_conversion_metric_id
                    
                    # Merge batch results
                    if batch_stats:
                        if not campaign_statistics:
                            campaign_statistics = batch_stats
                        else:
                            # Merge results if multiple batches
                            batch_results = batch_stats.get("data", {}).get("attributes", {}).get("results", [])
                            if batch_results and "data" in campaign_statistics:
                                existing_results = campaign_statistics["data"]["attributes"].get("results", [])
                                existing_results.extend(batch_results)
                    
                    # Add delay between batches to avoid rate limiting
                    if i + batch_size < len(all_campaign_ids):
                        await asyncio.sleep(1.5)  # 1.5 second delay between batches
                        
                except Exception as e:
                    if verbose:
                        print(f"    ⚠️ Batch {batch_num} failed: {e}")
                    continue
            
            if campaign_statistics and verbose:
                total_results = 0
                if "data" in campaign_statistics and "attributes" in campaign_statistics["data"]:
                    total_results = len(campaign_statistics["data"]["attributes"].get("results", []))
                print(f"  ✓ Campaign statistics extracted for {total_results} campaigns")
        
        return {
            "campaigns": all_campaigns,
            "campaign_statistics": campaign_statistics,
            "email_campaigns": email_campaigns,
            "sms_campaigns": sms_campaigns,
            "push_campaigns": push_campaigns
        }

