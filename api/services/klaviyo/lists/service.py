"""Lists service for fetching Klaviyo lists and growth data."""
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from ..client import KlaviyoClient
from ..metrics.service import MetricsService
from ..metrics.aggregates import MetricAggregatesService
from ..parsers import parse_metric_value
from ..utils.date_helpers import get_date_range_months

logger = logging.getLogger(__name__)


class ListsService:
    """Service for interacting with Klaviyo lists and subscriber data."""
    
    def __init__(self, client: KlaviyoClient):
        """
        Initialize lists service.
        
        Args:
            client: KlaviyoClient instance
        """
        self.client = client
        self.metrics = MetricsService(client)
        self.aggregates = MetricAggregatesService(client)
    
    async def get_lists(self) -> List[Dict[str, Any]]:
        """
        Get all lists in the account (handles pagination).
        
        Returns:
            List of list objects
        """
        all_lists = []
        page_cursor = None
        
        try:
            page_cursor = None  # Start with no cursor (first page)
            
            while True:
                params = {}
                if page_cursor:
                    params["page[cursor]"] = page_cursor
                
                response = await self.client.request("GET", "/lists/", params=params)
                page_data = response.get("data", [])
                all_lists.extend(page_data)
                
                logger.debug(f"Fetched {len(page_data)} lists (total so far: {len(all_lists)})")
                
                # Check for next page - Klaviyo uses 'links.next' for pagination
                links = response.get("links", {})
                next_url = links.get("next")
                
                if next_url:
                    # Extract cursor from the next URL
                    # Format: https://a.klaviyo.com/api/lists/?page%5Bcursor%5D=bmV4dDo6aWQ6Ok43dW1iVw
                    from urllib.parse import urlparse, parse_qs
                    parsed = urlparse(next_url)
                    query_params = parse_qs(parsed.query)
                    
                    # Get the cursor value (parse_qs returns lists)
                    cursor_list = query_params.get("page[cursor]", [])
                    if cursor_list:
                        page_cursor = cursor_list[0]  # Get first value
                        logger.debug(f"Next page cursor: {page_cursor[:30]}...")
                    else:
                        logger.debug("No cursor found in pagination link, stopping")
                        break
                else:
                    logger.debug("No next page link, stopping pagination")
                    break  # No next page, we're done
            
            logger.info(f"Fetched {len(all_lists)} total lists (with pagination)")
            return all_lists
        except Exception as e:
            logger.error(f"Error fetching lists: {e}", exc_info=True)
            return all_lists if all_lists else []
    
    async def get_list_profiles_count(self, list_id: str) -> int:
        """
        Get the count of profiles in a specific list.
        
        Args:
            list_id: List ID
            
        Returns:
            Number of profiles in the list
        """
        try:
            # Method 1: Try using additional-fields parameter for profile_count
            try:
                response = await self.client.request(
                    "GET",
                    f"/lists/{list_id}",
                    params={"additional-fields[list]": "profile_count"}
                )
                count = response.get("data", {}).get("attributes", {}).get("profile_count")
                if count is not None:
                    logger.debug(f"Got profile count via additional-fields: {count}")
                    return count
            except Exception as e:
                logger.warning(f"additional-fields method failed: {e}")
            
            # Method 2: Fallback to profiles endpoint pagination count
            response = await self.client.request(
                "GET",
                f"/lists/{list_id}/profiles/",
                params={"page[size]": 1}  # Just get count, not all profiles
            )
            count = response.get("meta", {}).get("pagination", {}).get("total", 0)
            logger.debug(f"Got profile count via pagination: {count}")
            return count
            
        except Exception as e:
            logger.error(f"Error fetching list profile count: {e}", exc_info=True)
            return 0
    
    async def _calculate_engaged_profiles(self, list_id: str, total_count: int) -> Dict[str, Any]:
        """
        Calculate engaged vs unengaged profiles for list engagement analysis.
        
        Args:
            list_id: List ID to analyze
            total_count: Total number of profiles in the list
            
        Returns:
            Dict with engagement metrics and threshold warnings
        """
        try:
            # Try to get engagement metrics from recent email activity
            # Look for metrics like "Received Email", "Opened Email", "Clicked Email"
            received_email_metric = await self.metrics.get_metric_by_name("Received Email")
            opened_email_metric = await self.metrics.get_metric_by_name("Opened Email") 
            clicked_email_metric = await self.metrics.get_metric_by_name("Clicked Email")
            
            # Calculate engagement for the last 90 days (standard engagement window)
            from datetime import datetime, timedelta
            from ..utils.date_helpers import get_date_range_months
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            start_str = start_date.strftime("%Y-%m-%dT00:00:00Z")
            end_str = end_date.strftime("%Y-%m-%dT23:59:59Z")
            
            # Get metrics for engagement calculation
            received_total = 0
            opened_total = 0
            clicked_total = 0
            
            if received_email_metric:
                try:
                    received_data = await self.aggregates.query(
                        metric_id=received_email_metric.get("id"),
                        start_date=start_str,
                        end_date=end_str,
                        measurements=["count"],
                        interval="month",
                        timezone="UTC"
                    )
                    if received_data:
                        attrs = received_data.get("data", {}).get("attributes", {})
                        data_list = attrs.get("data", [])
                        if data_list and isinstance(data_list[0], dict):
                            measurements = data_list[0].get("measurements", {})
                            values = measurements.get("count", [])
                            received_total = sum(self._parse_metric_value(v) for v in values)
                except Exception as e:
                    logger.debug(f"Could not get received email metrics: {e}")
            
            if opened_email_metric:
                try:
                    opened_data = await self.aggregates.query(
                        metric_id=opened_email_metric.get("id"),
                        start_date=start_str,
                        end_date=end_str,
                        measurements=["count"],
                        interval="month",
                        timezone="UTC"
                    )
                    if opened_data:
                        attrs = opened_data.get("data", {}).get("attributes", {})
                        data_list = attrs.get("data", [])
                        if data_list and isinstance(data_list[0], dict):
                            measurements = data_list[0].get("measurements", {})
                            values = measurements.get("count", [])
                            opened_total = sum(self._parse_metric_value(v) for v in values)
                except Exception as e:
                    logger.debug(f"Could not get opened email metrics: {e}")
            
            # Estimate engagement based on available data
            if received_total > 0 and opened_total > 0:
                # Calculate engagement rate based on opens vs receives
                engagement_rate = (opened_total / received_total) * 100
                
                # Estimate engaged vs unengaged profiles
                # This is an approximation since we can't get exact profile-level data
                estimated_engaged_profiles = int((engagement_rate / 100) * total_count)
                estimated_unengaged_profiles = total_count - estimated_engaged_profiles
                
                engaged_percentage = (estimated_engaged_profiles / total_count) * 100
                unengaged_percentage = (estimated_unengaged_profiles / total_count) * 100
                
                # Check if we exceed the 20% unengaged threshold (Jason's warning criteria)
                warning_threshold = unengaged_percentage >= 20.0
                
                # Estimate "received no emails" (profiles that weren't sent any emails)
                # This would be profiles in the list but not in the "received email" count
                received_no_emails = max(0, total_count - int(received_total * 0.1))  # Rough estimate
                received_no_emails_percentage = (received_no_emails / total_count) * 100 if total_count > 0 else 0
                
                # Calculate estimated wasted spend (industry averages)
                # Klaviyo pricing: ~$0.0005-0.002 per email depending on plan
                # Industry average: ~$0.001 per email for mid-tier accounts
                estimated_cost_per_email = 0.001
                estimated_emails_per_month = 8  # Average email frequency
                monthly_wasted_cost = received_no_emails * estimated_cost_per_email * estimated_emails_per_month
                annual_wasted_cost = monthly_wasted_cost * 12
                
                logger.info(f"Engagement analysis: {engaged_percentage:.1f}% engaged, {unengaged_percentage:.1f}% unengaged, warning: {warning_threshold}")
                
                return {
                    "engaged_count": estimated_engaged_profiles,
                    "unengaged_count": estimated_unengaged_profiles,
                    "engaged_percentage": round(engaged_percentage, 2),
                    "unengaged_percentage": round(unengaged_percentage, 2),
                    "warning_threshold": warning_threshold,
                    "received_no_emails": received_no_emails,
                    "received_no_emails_percentage": round(received_no_emails_percentage, 2),
                    "engagement_rate": round(engagement_rate, 2),
                    "calculation_method": "estimated_from_metrics",
                    "wasted_spend": {
                        "monthly_cost": round(monthly_wasted_cost, 2),
                        "annual_cost": round(annual_wasted_cost, 2),
                        "cost_per_email": estimated_cost_per_email,
                        "calculation_note": "Estimated using industry averages"
                    }
                }
            else:
                # Fallback: Assume moderate engagement if no data available
                logger.warning("No engagement metrics available, using fallback estimates")
                estimated_unengaged = int(total_count * 0.15)  # Assume 15% unengaged as moderate
                estimated_engaged = total_count - estimated_unengaged
                
                return {
                    "engaged_count": estimated_engaged,
                    "unengaged_count": estimated_unengaged,
                    "engaged_percentage": 85.0,
                    "unengaged_percentage": 15.0,
                    "warning_threshold": False,  # Below 20% threshold
                    "received_no_emails": 0,
                    "received_no_emails_percentage": 0.0,
                    "engagement_rate": 85.0,
                    "calculation_method": "fallback_estimate",
                    "wasted_spend": {
                        "monthly_cost": 0.0,
                        "annual_cost": 0.0,
                        "cost_per_email": 0.001,
                        "calculation_note": "No data available for cost calculation"
                    }
                }
                
        except Exception as e:
            logger.error(f"Error calculating engaged profiles: {e}")
            # Return safe defaults
            return {
                "engaged_count": total_count,
                "unengaged_count": 0,
                "engaged_percentage": 100.0,
                "unengaged_percentage": 0.0,
                "warning_threshold": False,
                "received_no_emails": 0,
                "received_no_emails_percentage": 0.0,
                "engagement_rate": 100.0,
                "calculation_method": "error_fallback",
                "wasted_spend": {
                    "monthly_cost": 0.0,
                    "annual_cost": 0.0,
                    "cost_per_email": 0.001,
                    "calculation_note": "Error in calculation - using safe defaults"
                }
            }
    
    def _parse_metric_value(self, value: Any) -> float:
        """Helper method to parse metric values consistently."""
        from ..parsers import parse_metric_value
        return parse_metric_value(value)
    
    async def get_list_growth_data(
        self,
        list_id: Optional[str] = None,
        months: int = 6,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Get list growth data over time.
        
        Uses "Subscribed to List" metric aggregates to track growth.
        
        Note: The metric aggregates endpoint doesn't support filtering by list_id,
        so the data returned is aggregated across all lists. For accounts with
        one main list, this is acceptable. For list-specific data, an alternative
        approach would be to use the Profiles API (Get Profiles for List) and
        paginate through profiles, but this is much slower.
        
        Reference: https://developers.klaviyo.com/en/reference/profiles_api_overview
        
        Args:
            list_id: Specific list ID (if None, gets primary/largest list)
            months: Number of months to look back
            
        Returns:
            Dict with growth data including monthly totals
        """
        # Get lists if no specific list provided
        if not list_id:
            lists = await self.get_lists()
            if not lists:
                return {"error": "No lists found"}
            
            # Simple smart selection: Find the primary marketing list
            # Exclude Shopify Collections and prioritize lists with "members" in name
            selected_list = None
            marketing_candidates = []
            
            logger.info(f"Evaluating {len(lists)} total lists for selection...")
            for lst in lists:
                attrs = lst.get("attributes", {})
                name = attrs.get("name", "").lower()
                full_name = attrs.get("name", "")
                
                # Skip Shopify Collections (product collections, not marketing lists)
                if "shopify collection" in name:
                    logger.debug(f"  Skipping Shopify Collection: {full_name}")
                    continue
                
                # Calculate priority:
                # - Highest: Lists with "members" AND "subscribed" (active marketing list)
                # - High: Lists with "members" (main marketing lists)
                # - Medium: Other marketing lists
                priority = 5
                if "members" in name:
                    if "subscribed" in name and "cleaned" not in name:
                        priority = 20  # Prefer subscribed over cleaned
                        logger.debug(f"Found subscribed list: {full_name} (priority: {priority})")
                    elif "cleaned" in name:
                        priority = 15  # Cleaned is good but subscribed is better
                        logger.debug(f"Found cleaned list: {full_name} (priority: {priority})")
                    else:
                        priority = 10  # Just "members" is good
                
                marketing_candidates.append({
                    "list": lst,
                    "priority": priority,
                    "name": full_name
                })
            
            # Get member counts for candidates
            logger.info(f"Evaluating {len(marketing_candidates)} candidate lists for list selection...")
            for candidate in marketing_candidates:
                try:
                    count = await self.get_list_profiles_count(candidate["list"]["id"])
                    candidate["count"] = count
                    logger.debug(f"  - {candidate['name']}: {count} members (priority: {candidate['priority']})")
                except Exception as e:
                    candidate["count"] = 0
                    logger.warning(f"  - {candidate['name']}: 0 members (error getting count: {e})")
            
            # Filter out empty lists and sort by priority then count (largest first)
            marketing_candidates = [m for m in marketing_candidates if m["count"] > 0]
            if marketing_candidates:
                # Sort by priority (highest first), then by count (largest first)
                marketing_candidates.sort(key=lambda x: (x["priority"], x["count"]), reverse=True)
                selected_list = marketing_candidates[0]["list"]
                logger.info(f"✅ Selected list: {selected_list.get('attributes', {}).get('name')} ({marketing_candidates[0]['count']} members, priority: {marketing_candidates[0]['priority']})")
                
                # Log top 3 candidates for debugging
                if len(marketing_candidates) > 1:
                    logger.debug(f"Top 3 candidates:")
                    for i, candidate in enumerate(marketing_candidates[:3], 1):
                        logger.debug(f"  {i}. {candidate['name']}: {candidate['count']} members (priority: {candidate['priority']})")
            else:
                # Fallback to first non-empty list
                for lst in lists:
                    try:
                        count = await self.get_list_profiles_count(lst["id"])
                        if count > 0:
                            selected_list = lst
                            logger.info(f"Selected first non-empty list: {lst.get('attributes', {}).get('name')} ({count} members)")
                            break
                    except:
                        continue
                
                if not selected_list:
                    selected_list = lists[0]
                    logger.warning(f"Using first list as fallback: {selected_list.get('attributes', {}).get('name')}")
            
            list_id = selected_list["id"]
            list_name = selected_list.get("attributes", {}).get("name", "Unknown")
        else:
            # Get list name if list_id provided
            try:
                response = await self.client.request("GET", f"/lists/{list_id}")
                list_name = response.get("data", {}).get("attributes", {}).get("name", "Selected List")
            except:
                list_name = "Selected List"
        
        # Get current subscriber count
        current_count = await self.get_list_profiles_count(list_id)
        
        # Calculate engagement threshold analysis (critical for manual audit quality)
        # Jason mentioned 20% unengaged as a warning threshold
        try:
            # Get engaged vs unengaged metrics for the list
            # This requires checking recent email engagement patterns
            engaged_profiles = await self._calculate_engaged_profiles(list_id, current_count)
            
        except Exception as e:
            logger.warning(f"Could not calculate engagement metrics: {e}")
            engaged_profiles = {
                "engaged_count": current_count,  # Assume all engaged if we can't calculate
                "unengaged_count": 0,
                "engaged_percentage": 100.0,
                "unengaged_percentage": 0.0,
                "warning_threshold": False,
                "received_no_emails": 0,
                "received_no_emails_percentage": 0.0
            }
        
        # Calculate date range
        # Use provided date_range if available (for YTD or custom ranges), otherwise calculate from months
        if date_range:
            from ..utils.date_helpers import parse_iso_date
            start_date = parse_iso_date(date_range["start"])
            end_date = parse_iso_date(date_range["end"])
            # Calculate effective months from date range
            effective_months = max(1, min((end_date - start_date).days // 30, 6))
            if (end_date - start_date).days > 180:
                logger.warning(f"Date range spans {(end_date - start_date).days} days, but capping analysis to 6 months for API compatibility")
        else:
            # IMPORTANT: Klaviyo metric aggregates API has limitations on date ranges
            # Based on sample audits, 6 months is the standard period
            # Cap at 6 months to avoid API errors
            effective_months = min(months, 6)
            if months > 6:
                logger.warning(f"Requested {months} months, but capping to 6 months for API compatibility (matches sample audit format)")
            
            date_range_dict = get_date_range_months(effective_months)
            start_date = date_range_dict["start"]
            end_date = date_range_dict["end"]
        
        # Log date range for debugging
        logger.info(f"List growth date range: {start_date.isoformat()} to {end_date.isoformat()} ({effective_months} months)")
        
        # Try to get subscription metrics over time
        subscribed_metric = await self.metrics.get_metric_by_name("Subscribed to List")
        
        # Try different possible names for churn-related metrics
        # Klaviyo may use different naming conventions for detailed churn breakdown
        unsubscribe_names = [
            "Unsubscribed from List",
            "Unsubscribed",
            "Unsubscribed from Email",
            "Unsubscribed from Campaign",
            "Unsubscribed from Flow"
        ]
        
        # Additional churn metrics for detailed breakdown (as mentioned in manual audits)
        bounce_names = [
            "Bounced Email",
            "Bounced",
            "Hard Bounced",
            "Soft Bounced"
        ]
        
        spam_names = [
            "Marked Email as Spam",
            "Spam Complaint",
            "Marked as Spam"
        ]
        
        one_click_names = [
            "One-Click Unsubscribe",
            "Unsubscribed via One-Click",
            "One Click Unsubscribe"
        ]
        
        # Find each metric type
        unsubscribed_metric = None
        for name in unsubscribe_names:
            unsubscribed_metric = await self.metrics.get_metric_by_name(name)
            if unsubscribed_metric:
                logger.info(f"Found unsubscribe metric: {name}")
                break
        
        bounced_metric = None
        for name in bounce_names:
            bounced_metric = await self.metrics.get_metric_by_name(name)
            if bounced_metric:
                logger.info(f"Found bounce metric: {name}")
                break
        
        spam_metric = None
        for name in spam_names:
            spam_metric = await self.metrics.get_metric_by_name(name)
            if spam_metric:
                logger.info(f"Found spam metric: {name}")
                break
        
        one_click_metric = None
        for name in one_click_names:
            one_click_metric = await self.metrics.get_metric_by_name(name)
            if one_click_metric:
                logger.info(f"Found one-click unsubscribe metric: {name}")
                break
        
        # Log if any churn metrics are missing
        if not unsubscribed_metric:
            # Log available metrics for debugging (first 30 to capture more churn-related metrics)
            all_metrics = await self.metrics.get_metrics()
            metric_names = [m.get("attributes", {}).get("name", "") for m in all_metrics[:30]]
            logger.warning(f"Unsubscribe metric not found. Searched: {unsubscribe_names}")
            logger.warning(f"Available metrics (first 30): {metric_names}")
            logger.warning("List growth data will show 0 for unsubscribes")
        
        if not bounced_metric:
            logger.info(f"Bounce metric not found. Searched: {bounce_names}")
        if not spam_metric:
            logger.info(f"Spam complaint metric not found. Searched: {spam_names}")
        if not one_click_metric:
            logger.info(f"One-click unsubscribe metric not found. Searched: {one_click_names}")
        
        monthly_data = []
        subscriptions_data = {}
        unsubscriptions_data = {}
        bounced_data = {}
        spam_data = {}
        one_click_data = {}
        
        if subscribed_metric:
            metric_id = subscribed_metric.get("id")
            if metric_id:
                try:
                    # Note: Metric aggregates for "Subscribed to List" doesn't support list_id filtering
                    # This will return data across all lists, which is acceptable for most use cases
                    start_str = start_date.strftime("%Y-%m-%dT00:00:00Z")
                    end_str = end_date.strftime("%Y-%m-%dT23:59:59Z")
                    logger.debug(f"Querying subscriptions metric {metric_id} from {start_str} to {end_str}")
                    
                    # Try month interval first (matches sample audit format)
                    # If that fails, try day interval and aggregate manually
                    subscriptions_data = await self.aggregates.query(
                        metric_id=metric_id,
                        start_date=start_str,
                        end_date=end_str,
                        measurements=["count"],
                        interval="month",
                        timezone="UTC"
                    )
                    
                    # If month interval fails, try day interval as fallback
                    if not subscriptions_data or not subscriptions_data.get("data"):
                        logger.debug(f"Month interval failed, trying day interval for {metric_id}")
                        try:
                            day_data = await self.aggregates.query(
                                metric_id=metric_id,
                                start_date=start_str,
                                end_date=end_str,
                                measurements=["count"],
                                interval="day",
                                timezone="UTC"
                            )
                            # If we get day data, we can aggregate it to months later
                            if day_data and day_data.get("data"):
                                logger.info(f"Got day-level data, will aggregate to months")
                                subscriptions_data = day_data
                        except Exception as day_error:
                            logger.debug(f"Day interval also failed: {day_error}")
                    if subscriptions_data:
                        logger.info(f"Successfully retrieved subscription data for metric {metric_id}")
                        # Log sample data for debugging
                        attrs = subscriptions_data.get("data", {}).get("attributes", {})
                        sample_data = attrs.get("data", [])
                        if sample_data:
                            logger.debug(f"Sample subscription data structure: {type(sample_data[0]) if sample_data else 'empty'}")
                    else:
                        logger.warning(f"Empty response from subscriptions metric {metric_id}. This may indicate the metric doesn't support aggregation or the date range is invalid.")
                except Exception as e:
                    logger.error(f"Exception querying subscriptions metric {metric_id}: {e}", exc_info=True)
                    subscriptions_data = {}
        
        if unsubscribed_metric:
            metric_id = unsubscribed_metric.get("id")
            if metric_id:
                try:
                    # Note: Metric aggregates for "Unsubscribed from List" doesn't support list_id filtering
                    # This will return data across all lists, which is acceptable for most use cases
                    start_str = start_date.strftime("%Y-%m-%dT00:00:00Z")
                    end_str = end_date.strftime("%Y-%m-%dT23:59:59Z")
                    logger.debug(f"Querying unsubscriptions metric {metric_id} from {start_str} to {end_str}")
                    
                    # Try month interval first (matches sample audit format)
                    # If that fails, try day interval and aggregate manually
                    unsubscriptions_data = await self.aggregates.query(
                        metric_id=metric_id,
                        start_date=start_str,
                        end_date=end_str,
                        measurements=["count"],
                        interval="month",
                        timezone="UTC"
                    )
                    
                    # If month interval fails, try day interval as fallback
                    if not unsubscriptions_data or not unsubscriptions_data.get("data"):
                        logger.debug(f"Month interval failed, trying day interval for {metric_id}")
                        try:
                            day_data = await self.aggregates.query(
                                metric_id=metric_id,
                                start_date=start_str,
                                end_date=end_str,
                                measurements=["count"],
                                interval="day",
                                timezone="UTC"
                            )
                            # If we get day data, we can aggregate it to months later
                            if day_data and day_data.get("data"):
                                logger.info(f"Got day-level data, will aggregate to months")
                                unsubscriptions_data = day_data
                        except Exception as day_error:
                            logger.debug(f"Day interval also failed: {day_error}")
                    if unsubscriptions_data:
                        logger.info(f"Successfully retrieved unsubscription data for metric {metric_id}")
                        # Log sample data for debugging
                        attrs = unsubscriptions_data.get("data", {}).get("attributes", {})
                        sample_data = attrs.get("data", [])
                        if sample_data:
                            logger.debug(f"Sample unsubscription data structure: {type(sample_data[0]) if sample_data else 'empty'}")
                    else:
                        logger.warning(f"Empty response from unsubscriptions metric {metric_id}. This may indicate the metric doesn't support aggregation or the date range is invalid.")
                except Exception as e:
                    logger.error(f"Exception querying unsubscriptions metric {metric_id}: {e}", exc_info=True)
                    unsubscriptions_data = {}
        
        # Extract bounced email data
        if bounced_metric:
            metric_id = bounced_metric.get("id")
            if metric_id:
                try:
                    start_str = start_date.strftime("%Y-%m-%dT00:00:00Z")
                    end_str = end_date.strftime("%Y-%m-%dT23:59:59Z")
                    logger.debug(f"Querying bounced metric {metric_id} from {start_str} to {end_str}")
                    
                    bounced_data = await self.aggregates.query(
                        metric_id=metric_id,
                        start_date=start_str,
                        end_date=end_str,
                        measurements=["count"],
                        interval="month",
                        timezone="UTC"
                    )
                    
                    # If month interval fails, try day interval as fallback
                    if not bounced_data or not bounced_data.get("data"):
                        day_data = await self.aggregates.query(
                            metric_id=metric_id,
                            start_date=start_str,
                            end_date=end_str,
                            measurements=["count"],
                            interval="day",
                            timezone="UTC"
                        )
                        if day_data and day_data.get("data"):
                            bounced_data = day_data
                    
                    if bounced_data:
                        logger.info(f"Successfully retrieved bounce data for metric {metric_id}")
                except Exception as e:
                    logger.error(f"Exception querying bounce metric {metric_id}: {e}", exc_info=True)
                    bounced_data = {}
        
        # Extract spam complaint data
        if spam_metric:
            metric_id = spam_metric.get("id")
            if metric_id:
                try:
                    start_str = start_date.strftime("%Y-%m-%dT00:00:00Z")
                    end_str = end_date.strftime("%Y-%m-%dT23:59:59Z")
                    logger.debug(f"Querying spam metric {metric_id} from {start_str} to {end_str}")
                    
                    spam_data = await self.aggregates.query(
                        metric_id=metric_id,
                        start_date=start_str,
                        end_date=end_str,
                        measurements=["count"],
                        interval="month",
                        timezone="UTC"
                    )
                    
                    # If month interval fails, try day interval as fallback
                    if not spam_data or not spam_data.get("data"):
                        day_data = await self.aggregates.query(
                            metric_id=metric_id,
                            start_date=start_str,
                            end_date=end_str,
                            measurements=["count"],
                            interval="day",
                            timezone="UTC"
                        )
                        if day_data and day_data.get("data"):
                            spam_data = day_data
                    
                    if spam_data:
                        logger.info(f"Successfully retrieved spam complaint data for metric {metric_id}")
                except Exception as e:
                    logger.error(f"Exception querying spam metric {metric_id}: {e}", exc_info=True)
                    spam_data = {}
        
        # Extract one-click unsubscribe data
        if one_click_metric:
            metric_id = one_click_metric.get("id")
            if metric_id:
                try:
                    start_str = start_date.strftime("%Y-%m-%dT00:00:00Z")
                    end_str = end_date.strftime("%Y-%m-%dT23:59:59Z")
                    logger.debug(f"Querying one-click unsubscribe metric {metric_id} from {start_str} to {end_str}")
                    
                    one_click_data = await self.aggregates.query(
                        metric_id=metric_id,
                        start_date=start_str,
                        end_date=end_str,
                        measurements=["count"],
                        interval="month",
                        timezone="UTC"
                    )
                    
                    # If month interval fails, try day interval as fallback
                    if not one_click_data or not one_click_data.get("data"):
                        day_data = await self.aggregates.query(
                            metric_id=metric_id,
                            start_date=start_str,
                            end_date=end_str,
                            measurements=["count"],
                            interval="day",
                            timezone="UTC"
                        )
                        if day_data and day_data.get("data"):
                            one_click_data = day_data
                    
                    if one_click_data:
                        logger.info(f"Successfully retrieved one-click unsubscribe data for metric {metric_id}")
                except Exception as e:
                    logger.error(f"Exception querying one-click unsubscribe metric {metric_id}: {e}", exc_info=True)
                    one_click_data = {}
        
        # Process the data into monthly breakdown
        # Handle the nested structure: data[0]['measurements']['count'] = [values]
        sub_attrs = subscriptions_data.get("data", {}).get("attributes", {}) if subscriptions_data else {}
        sub_data_list = sub_attrs.get("data", []) if sub_attrs else []
        dates = sub_attrs.get("dates", []) if sub_attrs else []
        
        # Extract values from nested structure: [{'measurements': {'count': [values]}}]
        sub_values = []
        if sub_data_list and len(sub_data_list) > 0:
            if isinstance(sub_data_list[0], dict):
                # New structure: list of dicts with measurements
                measurements = sub_data_list[0].get("measurements", {})
                sub_values = measurements.get("count", [])
                logger.debug(f"Extracted {len(sub_values)} subscription values from nested structure")
            else:
                # Old structure: direct list of values
                sub_values = sub_data_list
                logger.debug(f"Extracted {len(sub_values)} subscription values from direct list")
        
        unsub_attrs = unsubscriptions_data.get("data", {}).get("attributes", {}) if unsubscriptions_data else {}
        unsub_data_list = unsub_attrs.get("data", []) if unsub_attrs else []
        
        # Extract values from nested structure
        unsub_values = []
        if unsub_data_list and len(unsub_data_list) > 0:
            if isinstance(unsub_data_list[0], dict):
                # New structure: list of dicts with measurements
                measurements = unsub_data_list[0].get("measurements", {})
                unsub_values = measurements.get("count", [])
                logger.debug(f"Extracted {len(unsub_values)} unsubscription values from nested structure")
            else:
                # Old structure: direct list of values
                unsub_values = unsub_data_list
                logger.debug(f"Extracted {len(unsub_values)} unsubscription values from direct list")
        
        # Extract bounce values
        bounce_attrs = bounced_data.get("data", {}).get("attributes", {}) if bounced_data else {}
        bounce_data_list = bounce_attrs.get("data", []) if bounce_attrs else []
        bounce_values = []
        if bounce_data_list and len(bounce_data_list) > 0:
            if isinstance(bounce_data_list[0], dict):
                measurements = bounce_data_list[0].get("measurements", {})
                bounce_values = measurements.get("count", [])
                logger.debug(f"Extracted {len(bounce_values)} bounce values from nested structure")
            else:
                bounce_values = bounce_data_list
                logger.debug(f"Extracted {len(bounce_values)} bounce values from direct list")
        
        # Extract spam values
        spam_attrs = spam_data.get("data", {}).get("attributes", {}) if spam_data else {}
        spam_data_list = spam_attrs.get("data", []) if spam_attrs else []
        spam_values = []
        if spam_data_list and len(spam_data_list) > 0:
            if isinstance(spam_data_list[0], dict):
                measurements = spam_data_list[0].get("measurements", {})
                spam_values = measurements.get("count", [])
                logger.debug(f"Extracted {len(spam_values)} spam complaint values from nested structure")
            else:
                spam_values = spam_data_list
                logger.debug(f"Extracted {len(spam_values)} spam complaint values from direct list")
        
        # Extract one-click unsubscribe values
        one_click_attrs = one_click_data.get("data", {}).get("attributes", {}) if one_click_data else {}
        one_click_data_list = one_click_attrs.get("data", []) if one_click_attrs else []
        one_click_values = []
        if one_click_data_list and len(one_click_data_list) > 0:
            if isinstance(one_click_data_list[0], dict):
                measurements = one_click_data_list[0].get("measurements", {})
                one_click_values = measurements.get("count", [])
                logger.debug(f"Extracted {len(one_click_values)} one-click unsubscribe values from nested structure")
            else:
                one_click_values = one_click_data_list
                logger.debug(f"Extracted {len(one_click_values)} one-click unsubscribe values from direct list")
        
        # If we don't have dates from subscriptions, try other sources
        if not dates:
            for source_attrs in [unsub_attrs, bounce_attrs, spam_attrs, one_click_attrs]:
                if source_attrs and source_attrs.get("dates", []):
                    dates = source_attrs.get("dates", [])
                    logger.debug(f"Using dates from alternative source: {len(dates)} dates found")
                    break
        
        total_new = 0
        total_lost = 0
        total_bounced = 0
        total_spam = 0
        total_one_click = 0
        
        # If we have no data at all, create empty monthly entries or skip
        if not dates:
            logger.warning(f"No date range data available for list growth. Found {len(sub_values)} subscription values and {len(unsub_values)} unsubscription values, but no dates.")
            logger.debug(f"Subscription data structure: {subscriptions_data}")
            logger.debug(f"Unsubscription data structure: {unsubscriptions_data}")
        else:
            logger.info(f"Processing {len(dates)} months of list growth data with {len(sub_values)} subscription, {len(unsub_values)} unsubscription, {len(bounce_values)} bounce, {len(spam_values)} spam, and {len(one_click_values)} one-click values")
            logger.debug(f"Dates: {dates[:3]}... (showing first 3)")
            logger.debug(f"Subscription values: {sub_values[:3]}... (showing first 3)")
            logger.debug(f"Unsubscription values: {unsub_values[:3]}... (showing first 3)")
            for i, date in enumerate(dates):
                new_subs_raw = sub_values[i] if i < len(sub_values) else None
                lost_subs_raw = unsub_values[i] if i < len(unsub_values) else None
                bounced_raw = bounce_values[i] if i < len(bounce_values) else None
                spam_raw = spam_values[i] if i < len(spam_values) else None
                one_click_raw = one_click_values[i] if i < len(one_click_values) else None
                
                # Use centralized parser for all metrics
                new_subs = parse_metric_value(new_subs_raw)
                lost_subs = parse_metric_value(lost_subs_raw)
                bounced = parse_metric_value(bounced_raw)
                spam_complaints = parse_metric_value(spam_raw)
                one_click_unsubs = parse_metric_value(one_click_raw)
                
                total_new += int(new_subs)
                total_lost += int(lost_subs)
                total_bounced += int(bounced)
                total_spam += int(spam_complaints)
                total_one_click += int(one_click_unsubs)
                
                # Calculate total churn for the month (all types of list loss)
                total_monthly_churn = int(lost_subs + bounced + spam_complaints + one_click_unsubs)
                
                monthly_data.append({
                    "date": date,
                    "month": datetime.fromisoformat(date.replace("Z", "+00:00")).strftime("%b %Y"),
                    "new_subscribers": int(new_subs),
                    "lost_subscribers": int(lost_subs),
                    "bounced": int(bounced),
                    "spam_complaints": int(spam_complaints),
                    "one_click_unsubscribes": int(one_click_unsubs),
                    "total_churn": total_monthly_churn,
                    "net_change": int(new_subs - total_monthly_churn)
                })
        
        # Calculate comprehensive churn metrics as percentages (key insight from manual audits)
        total_all_churn = total_lost + total_bounced + total_spam + total_one_click
        churn_rate = (total_all_churn / total_new * 100) if total_new > 0 else 0
        
        # Calculate detailed breakdown percentages for client presentation
        unsubscribe_percentage = (total_lost / total_new * 100) if total_new > 0 else 0
        bounce_percentage = (total_bounced / total_new * 100) if total_new > 0 else 0
        spam_percentage = (total_spam / total_new * 100) if total_new > 0 else 0
        one_click_percentage = (total_one_click / total_new * 100) if total_new > 0 else 0
        
        logger.info(f"Churn breakdown - Unsubscribes: {unsubscribe_percentage:.2f}%, Bounces: {bounce_percentage:.2f}%, Spam: {spam_percentage:.2f}%, One-Click: {one_click_percentage:.2f}%")
        
        # Calculate period-over-period comparison (critical for manual audit quality)
        # Split the data into two halves for comparison
        if len(monthly_data) >= 2:
            midpoint = len(monthly_data) // 2
            first_half = monthly_data[:midpoint]
            second_half = monthly_data[midpoint:]
            
            # Calculate metrics for each period
            first_half_new = sum(m["new_subscribers"] for m in first_half)
            second_half_new = sum(m["new_subscribers"] for m in second_half)
            first_half_churn = sum(m["total_churn"] for m in first_half)
            second_half_churn = sum(m["total_churn"] for m in second_half)
            
            # Calculate percentage changes
            growth_change = 0
            churn_change = 0
            if first_half_new > 0:
                growth_change = ((second_half_new - first_half_new) / first_half_new) * 100
            if first_half_churn > 0:
                churn_change = ((second_half_churn - first_half_churn) / first_half_churn) * 100
            
            period_comparison = {
                "first_period_new": first_half_new,
                "second_period_new": second_half_new,
                "first_period_churn": first_half_churn,
                "second_period_churn": second_half_churn,
                "growth_change_percentage": round(growth_change, 2),
                "churn_change_percentage": round(churn_change, 2),
                "periods": {
                    "first": f"{first_half[0]['month']} - {first_half[-1]['month']}" if first_half else "Period 1",
                    "second": f"{second_half[0]['month']} - {second_half[-1]['month']}" if second_half else "Period 2"
                }
            }
            
            logger.info(f"Period comparison - Growth: {growth_change:+.1f}%, Churn: {churn_change:+.1f}%")
        else:
            period_comparison = {
                "first_period_new": 0,
                "second_period_new": 0,
                "first_period_churn": 0,
                "second_period_churn": 0,
                "growth_change_percentage": 0,
                "churn_change_percentage": 0,
                "periods": {"first": "Insufficient Data", "second": "Insufficient Data"}
            }
        
        # If we have no monthly data but have current count, provide basic info with note
        if not monthly_data and current_count > 0:
            logger.warning(f"No historical growth data available via API for list {list_name}. This data may need to be manually entered or obtained from Klaviyo dashboard screenshots.")
            return {
                "list_id": list_id,
                "list_name": list_name,
                "current_total": current_count,
                "period_months": effective_months,
                "growth_subscribers": 0,
                "lost_subscribers": 0,
                "bounced": 0,
                "spam_complaints": 0,
                "one_click_unsubscribes": 0,
                "net_change": 0,
                "churn_rate": 0.0,
                "unsubscribe_percentage": 0.0,
                "bounce_percentage": 0.0,
                "spam_percentage": 0.0,
                "one_click_percentage": 0.0,
                "monthly_data": [],
                "chart_data": {
                    "months": [],
                    "total_members": [],
                    "net_change": [],
                    "new_subscribers": []
                },
                "net_change_chart_data": {
                    "months": [],
                    "net_change": []
                },
                "period_comparison": {
                    "first_period_new": 0,
                    "second_period_new": 0,
                    "first_period_churn": 0,
                    "second_period_churn": 0,
                    "growth_change_percentage": 0,
                    "churn_change_percentage": 0,
                    "periods": {"first": "No Data", "second": "No Data"}
                },
                "engagement_threshold": engaged_profiles,
                "note": f"Historical growth data not available via API. Current list size: {current_count} members. Data may need to be obtained from Klaviyo dashboard screenshots."
            }
        
        return {
            "list_id": list_id,
            "list_name": list_name,
            "current_total": current_count,
            "period_months": effective_months,
            "growth_subscribers": total_new,
            "lost_subscribers": total_lost,
            "bounced": total_bounced,
            "spam_complaints": total_spam,
            "one_click_unsubscribes": total_one_click,
            "net_change": total_new - total_all_churn,
            "churn_rate": round(churn_rate, 2),
            "unsubscribe_percentage": round(unsubscribe_percentage, 2),
            "bounce_percentage": round(bounce_percentage, 2),
            "spam_percentage": round(spam_percentage, 2),
            "one_click_percentage": round(one_click_percentage, 2),
            "monthly_data": monthly_data,
            "chart_data": {
                "months": [m["month"] for m in monthly_data],
                "total_members": [],  # Would need cumulative calculation
                "net_change": [m["net_change"] for m in monthly_data],
                "new_subscribers": [m["new_subscribers"] for m in monthly_data]
            },
            "net_change_chart_data": {
                "months": [m["month"] for m in monthly_data],
                "net_change": [m["net_change"] for m in monthly_data]
            },
            "churn_breakdown": {
                "unsubscribes": total_lost,
                "bounces": total_bounced,
                "spam_complaints": total_spam,
                "one_click_unsubscribes": total_one_click,
                "total_churn": total_all_churn
            },
            "period_comparison": period_comparison,
            "engagement_threshold": engaged_profiles
        }

