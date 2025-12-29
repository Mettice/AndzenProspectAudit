"""Campaigns service for fetching Klaviyo campaigns."""
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from ..client import KlaviyoClient
from ..filters import build_campaign_filter
from ..utils.date_helpers import parse_iso_date

logger = logging.getLogger(__name__)


class CampaignsService:
    """Service for interacting with Klaviyo campaigns."""
    
    def __init__(self, client: KlaviyoClient):
        """
        Initialize campaigns service.
        
        Args:
            client: KlaviyoClient instance
        """
        self.client = client
    
    async def get_campaigns(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        channel: str = "email"
    ) -> List[Dict[str, Any]]:
        """
        Get campaigns with proper filter syntax.
        
        FIXED: Multiple filters must be combined with and() operator.
        Reference: https://developers.klaviyo.com/en/reference/get_campaigns
        
        Note: Date filters on campaigns may not work with the API,
        so filtering is done in Python instead.
        
        Args:
            start_date: Start datetime in ISO format with Z suffix
            end_date: End datetime in ISO format with Z suffix
            channel: Channel type (email, sms, push)
            
        Returns:
            List of campaign objects
        """
        # Build filter string
        filter_string = build_campaign_filter(channel, start_date, end_date)
        
        params = {}
        if filter_string:
            params["filter"] = filter_string
        
        try:
            response = await self.client.request(
                "GET",
                "/campaigns/",
                params=params if params else None
            )
            campaigns = response.get("data", [])
            
            # Filter by date in Python if date range provided
            if start_date and end_date:
                try:
                    start_dt = parse_iso_date(start_date)
                    end_dt = parse_iso_date(end_date)
                    filtered_campaigns = []
                    for c in campaigns:
                        created_at = c.get("attributes", {}).get("created_at")
                        if created_at:
                            try:
                                created_dt = parse_iso_date(created_at)
                                if start_dt <= created_dt <= end_dt:
                                    filtered_campaigns.append(c)
                            except (ValueError, TypeError) as e:
                                logger.debug(f"Error parsing date for campaign {c.get('id')}: {e}")
                                continue
                    return filtered_campaigns
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing date range: {e}")
                    return campaigns
            
            return campaigns
            
        except Exception as e:
            # Check if this is a 400 error for push channel (not supported)
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                if e.response.status_code == 400 and channel == "push":
                    # Push campaigns may not be supported via campaigns endpoint
                    logger.warning(f"Push campaigns not supported via campaigns endpoint (this is expected)")
                    return []
            
            logger.error(f"Error fetching campaigns: {e}", exc_info=True)
            if hasattr(e, 'response'):
                logger.debug(f"Filter used: {filter_string}")
                if hasattr(e.response, 'text'):
                    logger.debug(f"Response: {e.response.text}")
            
            # Fallback: try without date filters (only for email/SMS, not push)
            if channel != "push":
                try:
                    logger.info("Trying without date filters...")
                    simple_params = {"filter": f"equals(messages.channel,'{channel}')"}
                    response = await self.client.request("GET", "/campaigns/", params=simple_params)
                    campaigns = response.get("data", [])
                    
                    # Filter by date in Python if needed
                    if start_date and end_date:
                        try:
                            start_dt = parse_iso_date(start_date)
                            end_dt = parse_iso_date(end_date)
                            campaigns = [
                                c for c in campaigns 
                                if 'created_at' in c.get("attributes", {})
                                and start_dt <= parse_iso_date(c["attributes"]["created_at"]) <= end_dt
                            ]
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Error parsing date range in fallback: {e}")
                    
                    return campaigns
                except Exception as e2:
                    logger.error(f"Fallback also failed: {e2}", exc_info=True)
                    return []
            else:
                # Push channel not supported, return empty
                logger.warning("Push campaigns not supported via campaigns endpoint")
                return []

