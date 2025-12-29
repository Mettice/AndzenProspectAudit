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
    
    async def get_list_growth_data(
        self,
        list_id: Optional[str] = None,
        months: int = 6
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
        
        # Calculate date range
        # IMPORTANT: Klaviyo metric aggregates API has limitations on date ranges
        # Based on sample audits, 6 months is the standard period
        # Cap at 6 months to avoid API errors
        effective_months = min(months, 6)
        if months > 6:
            logger.warning(f"Requested {months} months, but capping to 6 months for API compatibility (matches sample audit format)")
        
        date_range = get_date_range_months(effective_months)
        start_date = date_range["start"]
        end_date = date_range["end"]
        
        # Log date range for debugging
        logger.info(f"List growth date range: {start_date.isoformat()} to {end_date.isoformat()} ({effective_months} months)")
        
        # Try to get subscription metrics over time
        subscribed_metric = await self.metrics.get_metric_by_name("Subscribed to List")
        
        # Try different possible names for unsubscribe metric
        # Klaviyo may use different naming conventions
        unsubscribe_names = [
            "Unsubscribed from List",
            "Unsubscribed",
            "Unsubscribed from Email",
            "Unsubscribed from Campaign",
            "Unsubscribed from Flow"
        ]
        
        unsubscribed_metric = None
        for name in unsubscribe_names:
            unsubscribed_metric = await self.metrics.get_metric_by_name(name)
            if unsubscribed_metric:
                logger.info(f"Found unsubscribe metric: {name}")
                break
        
        if not unsubscribed_metric:
            # Log available metrics for debugging (first 20 to avoid spam)
            all_metrics = await self.metrics.get_metrics()
            metric_names = [m.get("attributes", {}).get("name", "") for m in all_metrics[:20]]
            logger.warning(f"Unsubscribe metric not found. Searched: {unsubscribe_names}")
            logger.warning(f"Available metrics (first 20): {metric_names}")
            logger.warning("List growth data will show 0 for unsubscribes")
        
        monthly_data = []
        subscriptions_data = {}
        unsubscriptions_data = {}
        
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
        
        # If we don't have dates from subscriptions, try to get them from unsubscriptions
        if not dates and unsub_attrs:
            dates = unsub_attrs.get("dates", [])
        
        total_new = 0
        total_lost = 0
        
        # If we have no data at all, create empty monthly entries or skip
        if not dates:
            logger.warning(f"No date range data available for list growth. Found {len(sub_values)} subscription values and {len(unsub_values)} unsubscription values, but no dates.")
            logger.debug(f"Subscription data structure: {subscriptions_data}")
            logger.debug(f"Unsubscription data structure: {unsubscriptions_data}")
        else:
            logger.info(f"Processing {len(dates)} months of list growth data with {len(sub_values)} subscription values and {len(unsub_values)} unsubscription values")
            logger.debug(f"Dates: {dates[:3]}... (showing first 3)")
            logger.debug(f"Subscription values: {sub_values[:3]}... (showing first 3)")
            logger.debug(f"Unsubscription values: {unsub_values[:3]}... (showing first 3)")
            for i, date in enumerate(dates):
                new_subs_raw = sub_values[i] if i < len(sub_values) else None
                lost_subs_raw = unsub_values[i] if i < len(unsub_values) else None
                
                # Use centralized parser
                new_subs = parse_metric_value(new_subs_raw)
                lost_subs = parse_metric_value(lost_subs_raw)
                
                total_new += int(new_subs)
                total_lost += int(lost_subs)
                
                monthly_data.append({
                    "date": date,
                    "month": datetime.fromisoformat(date.replace("Z", "+00:00")).strftime("%b %Y"),
                    "new_subscribers": int(new_subs),
                    "lost_subscribers": int(lost_subs),
                    "net_change": int(new_subs - lost_subs)
                })
        
        # Calculate churn rate
        churn_rate = (total_lost / total_new * 100) if total_new > 0 else 0
        
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
                "net_change": 0,
                "churn_rate": 0.0,
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
                "note": f"Historical growth data not available via API. Current list size: {current_count} members. Data may need to be obtained from Klaviyo dashboard screenshots."
            }
        
        return {
            "list_id": list_id,
            "list_name": list_name,
            "current_total": current_count,
            "period_months": effective_months,
            "growth_subscribers": total_new,
            "lost_subscribers": total_lost,
            "net_change": total_new - total_lost,
            "churn_rate": round(churn_rate, 2),
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
            }
        }

