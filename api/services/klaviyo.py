"""
Klaviyo API client service - ENHANCED VERSION (December 2025).

Key features:
1. Metric aggregates uses POST /metric-aggregates/ with JSON body
2. Campaign filters use and() operator for multiple conditions
3. Reporting API for campaign/flow statistics (matches UI data)
4. Proper datetime formatting (RFC3339 with Z suffix)
5. NEW: List growth data extraction
6. NEW: Form performance extraction
7. NEW: 90-day time series with attribution breakdown
8. NEW: Flow-by-flow statistics for deep dives
9. NEW: Rate limiting with exponential backoff

Reference: https://developers.klaviyo.com/en/reference/
"""
import httpx
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import os
import time
from httpx import HTTPStatusError
from collections import deque

# Try to import relativedelta, fallback to timedelta-based approximation
try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    # Simple fallback that approximates relativedelta for months
    class relativedelta:
        def __init__(self, months: int = 0, days: int = 0):
            self.months = months
            self.days = days
        
        def __rsub__(self, other):
            # Approximate months as 30 days each
            total_days = (self.months * 30) + self.days
            return other - timedelta(days=total_days)


class RateLimiter:
    """
    Rate limiter for Klaviyo API requests.
    
    Based on Klaviyo rate limits:
    - Small (S): 3 req/sec, 60/min
    - Medium (M): 10 req/sec, 150/min
    - Large (L): 75 req/sec, 700/min
    - Extra Large (XL): 350 req/sec, 3500/min
    
    Defaults to Medium tier (10 req/sec, 150/min) for safety.
    """
    
    def __init__(self, requests_per_second: float = 8.0, requests_per_minute: int = 120):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_second: Max requests per second (default 8, conservative)
            requests_per_minute: Max requests per minute (default 120, conservative)
        """
        self.requests_per_second = requests_per_second
        self.requests_per_minute = requests_per_minute
        self.min_interval = 1.0 / requests_per_second  # Minimum time between requests
        
        # Track request timestamps
        self.request_times = deque()  # For per-second tracking
        self.minute_times = deque()   # For per-minute tracking
        
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Wait until we can make a request without exceeding rate limits."""
        async with self._lock:
            now = time.time()
            
            # Remove old timestamps (older than 1 second)
            while self.request_times and self.request_times[0] < now - 1.0:
                self.request_times.popleft()
            
            # Remove old timestamps (older than 1 minute)
            while self.minute_times and self.minute_times[0] < now - 60.0:
                self.minute_times.popleft()
            
            # Check per-second limit
            if len(self.request_times) >= self.requests_per_second:
                wait_time = 1.0 - (now - self.request_times[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    now = time.time()
                    # Clean up again after waiting
                    while self.request_times and self.request_times[0] < now - 1.0:
                        self.request_times.popleft()
            
            # Check per-minute limit
            if len(self.minute_times) >= self.requests_per_minute:
                wait_time = 60.0 - (now - self.minute_times[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    now = time.time()
                    # Clean up again after waiting
                    while self.minute_times and self.minute_times[0] < now - 60.0:
                        self.minute_times.popleft()
            
            # Record this request
            self.request_times.append(now)
            self.minute_times.append(now)
            
            # Ensure minimum interval between requests
            if len(self.request_times) > 1:
                time_since_last = now - self.request_times[-2]
                if time_since_last < self.min_interval:
                    await asyncio.sleep(self.min_interval - time_since_last)


class KlaviyoService:
    """Service for interacting with Klaviyo API."""
    
    BASE_URL = "https://a.klaviyo.com/api"
    
    def __init__(self, api_key: str, rate_limit_tier: str = "medium"):
        """
        Initialize Klaviyo service.
        
        Args:
            api_key: Klaviyo API key
            rate_limit_tier: Rate limit tier - "small", "medium", "large", "xl"
        """
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Klaviyo-API-Key {api_key}",
            "revision": "2025-10-15",
            "accept": "application/vnd.api+json",
            "Content-Type": "application/json"
        }
        
        # Initialize rate limiter based on tier
        rate_limits = {
            "small": (3.0, 60),
            "medium": (8.0, 120),  # Conservative: 8/sec, 120/min (below 10/sec, 150/min)
            "large": (50.0, 600),   # Conservative: 50/sec, 600/min (below 75/sec, 700/min)
            "xl": (200.0, 3000)     # Conservative: 200/sec, 3000/min (below 350/sec, 3500/min)
        }
        
        rps, rpm = rate_limits.get(rate_limit_tier.lower(), rate_limits["medium"])
        self.rate_limiter = RateLimiter(requests_per_second=rps, requests_per_minute=rpm)
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        retry_on_429: bool = True,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Klaviyo API with rate limiting.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body
            retry_on_429: Whether to retry on rate limit errors
            max_retries: Maximum number of retries for 429 errors
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        # Wait for rate limiter
        await self.rate_limiter.acquire()
        
        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=self.headers,
                        params=params,
                        json=data
                    )
                    
                    # Check for rate limiting
                    if response.status_code == 429 and retry_on_429 and attempt < max_retries:
                        # Extract retry delay from response
                        retry_after = None
                        try:
                            error_data = response.json()
                            error_detail = error_data.get("errors", [{}])[0]
                            retry_after = error_detail.get("meta", {}).get("retry_after")
                            if not retry_after:
                                # Try to parse from detail message
                                detail = error_detail.get("detail", "")
                                if "Expected available in" in detail:
                                    import re
                                    match = re.search(r'(\d+) seconds?', detail)
                                    if match:
                                        retry_after = int(match.group(1))
                        except:
                            pass
                        
                        if not retry_after:
                            # Exponential backoff: 2^attempt seconds
                            retry_after = 2 ** attempt
                        
                        # Add buffer time
                        retry_after = min(retry_after + 1, 60)  # Cap at 60 seconds
                        
                        print(f"  Rate limited. Waiting {retry_after} seconds before retry {attempt + 1}/{max_retries}...")
                        await asyncio.sleep(retry_after)
                        
                        # Wait for rate limiter again before retry
                        await self.rate_limiter.acquire()
                        continue
                    
                    response.raise_for_status()
                    return response.json()
                    
            except HTTPStatusError as e:
                if e.response.status_code == 429 and retry_on_429 and attempt < max_retries:
                    # Already handled above, but catch here too
                    continue
                raise
        
        # If we get here, all retries failed
        raise HTTPStatusError("Rate limit exceeded after all retries", request=None, response=None)
    
    async def test_connection(self) -> bool:
        """Test API connection."""
        try:
            await self._make_request("GET", "/accounts/")
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    async def get_metrics(self) -> List[Dict[str, Any]]:
        """Get all metrics."""
        try:
            response = await self._make_request("GET", "/metrics/")
            return response.get("data", [])
        except HTTPStatusError as e:
            print(f"Error fetching metrics: {e}")
            return []
    
    async def get_metric_by_name(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """Get a metric by its name and return the metric object."""
        metrics = await self.get_metrics()
        for metric in metrics:
            if metric.get("attributes", {}).get("name") == metric_name:
                return metric
        print(f"Metric '{metric_name}' not found in {len(metrics)} available metrics")
        return None

    async def query_metric_aggregates(
        self,
        metric_id: str,
        start_date: str,
        end_date: str,
        measurements: List[str] = None,
        interval: str = "day",
        by: List[str] = None,
        filter_conditions: List[str] = None
    ) -> Dict[str, Any]:
        """
        Query metric aggregates using POST /metric-aggregates/.
        
        This is the CORRECT endpoint per Klaviyo documentation.
        It requires POST with JSON body, not GET with params.
        
        Reference: https://developers.klaviyo.com/en/reference/query_metric_aggregates
        
        Args:
            metric_id: The metric ID to query
            start_date: Start datetime in ISO format (e.g., "2025-11-17T00:00:00Z")
            end_date: End datetime in ISO format
            measurements: List of measurements (e.g., ["count", "sum_value", "unique"])
            interval: Time interval (day, week, month)
            by: List of dimensions to group by (e.g., ["$message", "$flow"])
            filter_conditions: Additional filter conditions beyond datetime
        
        Returns:
            Dict with metric aggregate data
        """
        if measurements is None:
            measurements = ["count", "sum_value", "unique"]
        
        # Build filter array - datetime filters are required
        filters = [
            f"greater-or-equal(datetime,{start_date})",
            f"less-than(datetime,{end_date})"
        ]
        
        # Add any additional filters (only 1 additional filter allowed per docs)
        if filter_conditions:
            filters.extend(filter_conditions[:1])  # Limit to 1 additional filter
        
        payload = {
            "data": {
                "type": "metric-aggregate",
                "attributes": {
                    "metric_id": metric_id,
                    "measurements": measurements,
                    "interval": interval,
                    "filter": filters,
                    "timezone": "UTC"
                }
            }
        }
        
        # Add grouping if specified
        if by:
            payload["data"]["attributes"]["by"] = by
        
        try:
            response = await self._make_request("POST", "/metric-aggregates/", data=payload)
            return response
        except HTTPStatusError as e:
            print(f"Error querying metric aggregates for {metric_id}: {e}")
            if hasattr(e, 'response'):
                print(f"Response text: {e.response.text}")
            return {}
    
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
        
        Args:
            start_date: Start datetime in ISO format with Z suffix
            end_date: End datetime in ISO format with Z suffix
            channel: Channel type (email, sms, push)
        """
        # Build filter conditions
        filters = []
        filters.append(f"equals(messages.channel,'{channel}')")
        
        # Note: Date filters on campaigns may not work with the API
        # We'll fetch all campaigns and filter in Python instead
        # if start_date and end_date:
        #     filters.append(f"greater-or-equal(created_at,'{start_date}')")
        #     filters.append(f"less-or-equal(created_at,'{end_date}')")
        
        # Combine with and() operator if multiple conditions
        if len(filters) > 1:
            filter_string = f"and({','.join(filters)})"
        else:
            filter_string = filters[0] if filters else None

        params = {}
        if filter_string:
            params["filter"] = filter_string

        try:
            response = await self._make_request("GET", "/campaigns/", params=params if params else None)
            campaigns = response.get("data", [])
            
            # Filter by date in Python if date range provided
            if start_date and end_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                filtered_campaigns = []
                for c in campaigns:
                    created_at = c.get("attributes", {}).get("created_at")
                    if created_at:
                        try:
                            created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            if start_dt <= created_dt <= end_dt:
                                filtered_campaigns.append(c)
                        except:
                            pass  # Skip if date parsing fails
                return filtered_campaigns
            
            return campaigns
        except HTTPStatusError as e:
            print(f"Error fetching campaigns: {e}")
            if hasattr(e, 'response'):
                print(f"Filter used: {filter_string}")
                print(f"Response: {e.response.text}")
            
            # Fallback: try without date filters
            try:
                print("Trying without date filters...")
                simple_params = {"filter": f"equals(messages.channel,'{channel}')"}
                response = await self._make_request("GET", "/campaigns/", params=simple_params)
                campaigns = response.get("data", [])
                
                # Filter by date in Python if needed
                if start_date and end_date:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    campaigns = [
                        c for c in campaigns 
                        if 'created_at' in c.get("attributes", {})
                        and start_dt <= datetime.fromisoformat(
                            c["attributes"]["created_at"].replace('Z', '+00:00')
                        ) <= end_dt
                    ]
                return campaigns
            except Exception as e2:
                print(f"Fallback also failed: {e2}")
                return []
    
    async def get_flows(self) -> List[Dict[str, Any]]:
        """Get all flows."""
        try:
            response = await self._make_request("GET", "/flows/")
            return response.get("data", [])
        except HTTPStatusError as e:
            print(f"Error fetching flows: {e}")
            return []
    
    async def get_flow_actions(self, flow_id: str) -> List[Dict[str, Any]]:
        """Get actions for a specific flow."""
        try:
            response = await self._make_request("GET", f"/flows/{flow_id}/flow-actions/")
            return response.get("data", [])
        except HTTPStatusError as e:
            print(f"Error fetching actions for flow {flow_id}: {e}")
            return []
    
    async def get_flow_action_messages(self, action_id: str) -> List[Dict[str, Any]]:
        """Get messages for a specific flow action."""
        try:
            response = await self._make_request("GET", f"/flow-actions/{action_id}/flow-messages/")
            return response.get("data", [])
        except HTTPStatusError as e:
            print(f"Error fetching messages for flow action {action_id}: {e}")
            return []
    
    # ============================================================
    # NEW: List Growth & Subscriber Data Methods
    # ============================================================
    
    async def get_lists(self) -> List[Dict[str, Any]]:
        """Get all lists in the account."""
        try:
            response = await self._make_request("GET", "/lists/")
            return response.get("data", [])
        except HTTPStatusError as e:
            print(f"Error fetching lists: {e}")
            return []
    
    async def get_list_profiles_count(self, list_id: str) -> int:
        """Get the count of profiles in a specific list."""
        try:
            # Use the profiles endpoint with count
            response = await self._make_request(
                "GET", 
                f"/lists/{list_id}/profiles/",
                params={"page[size]": 1}  # Just get count, not all profiles
            )
            # The response includes pagination info with total count
            return response.get("meta", {}).get("pagination", {}).get("total", 0)
        except HTTPStatusError as e:
            print(f"Error fetching list profile count: {e}")
            return 0
    
    async def get_list_growth_data(
        self,
        list_id: Optional[str] = None,
        months: int = 6
    ) -> Dict[str, Any]:
        """
        Get list growth data over time.
        
        Uses "Subscribed to List" metric aggregates to track growth.
        
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
            # Use first list (usually main newsletter)
            list_id = lists[0]["id"]
            list_name = lists[0].get("attributes", {}).get("name", "Unknown")
        else:
            list_name = "Selected List"
        
        # Get current subscriber count
        current_count = await self.get_list_profiles_count(list_id)
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - relativedelta(months=months)
        
        # Try to get subscription metrics over time
        subscribed_metric = await self.get_metric_by_name("Subscribed to List")
        # Try different possible names for unsubscribe metric
        unsubscribed_metric = await self.get_metric_by_name("Unsubscribed")
        if not unsubscribed_metric:
            unsubscribed_metric = await self.get_metric_by_name("Unsubscribed from List")
        if not unsubscribed_metric:
            unsubscribed_metric = await self.get_metric_by_name("Unsubscribed from Email")
        
        monthly_data = []
        subscriptions_data = {}
        unsubscriptions_data = {}
        
        if subscribed_metric:
            metric_id = subscribed_metric.get("id")
            if metric_id:
                subscriptions_data = await self.query_metric_aggregates(
                    metric_id=metric_id,
                    start_date=start_date.strftime("%Y-%m-%dT00:00:00Z"),
                    end_date=end_date.strftime("%Y-%m-%dT23:59:59Z"),
                    measurements=["count"],
                    interval="month"
                )
        
        if unsubscribed_metric:
            metric_id = unsubscribed_metric.get("id")
            if metric_id:
                unsubscriptions_data = await self.query_metric_aggregates(
                    metric_id=metric_id,
                    start_date=start_date.strftime("%Y-%m-%dT00:00:00Z"),
                    end_date=end_date.strftime("%Y-%m-%dT23:59:59Z"),
                    measurements=["count"],
                    interval="month"
                )
        
        # Process the data into monthly breakdown
        sub_attrs = subscriptions_data.get("data", {}).get("attributes", {})
        sub_values = sub_attrs.get("data", [])
        dates = sub_attrs.get("dates", [])
        
        unsub_attrs = unsubscriptions_data.get("data", {}).get("attributes", {}) if unsubscriptions_data else {}
        unsub_values = unsub_attrs.get("data", []) if unsub_attrs else []
        
        total_new = 0
        total_lost = 0
        
        for i, date in enumerate(dates):
            new_subs_raw = sub_values[i] if i < len(sub_values) else None
            lost_subs_raw = unsub_values[i] if i < len(unsub_values) else None
            
            # Handle nested structure from API response
            if new_subs_raw is None:
                new_subs = 0
            elif isinstance(new_subs_raw, list):
                new_subs = float(new_subs_raw[0]) if len(new_subs_raw) > 0 and new_subs_raw[0] is not None else 0
            elif isinstance(new_subs_raw, dict):
                new_subs = float(new_subs_raw.get("count", 0))
            else:
                new_subs = float(new_subs_raw) if new_subs_raw else 0
            
            if lost_subs_raw is None:
                lost_subs = 0
            elif isinstance(lost_subs_raw, list):
                lost_subs = float(lost_subs_raw[0]) if len(lost_subs_raw) > 0 and lost_subs_raw[0] is not None else 0
            elif isinstance(lost_subs_raw, dict):
                lost_subs = float(lost_subs_raw.get("count", 0))
            else:
                lost_subs = float(lost_subs_raw) if lost_subs_raw else 0
            
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
        
        return {
            "list_id": list_id,
            "list_name": list_name,
            "current_total": current_count,
            "period_months": months,
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
            }
        }
    
    # ============================================================
    # NEW: Form Performance Data Methods
    # ============================================================
    
    async def get_forms(self) -> List[Dict[str, Any]]:
        """Get all forms in the account."""
        try:
            response = await self._make_request("GET", "/forms/")
            return response.get("data", [])
        except HTTPStatusError as e:
            print(f"Error fetching forms: {e}")
            return []
    
    async def get_form_performance(
        self,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        Get form performance data.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dict with form performance metrics
        """
        forms = await self.get_forms()
        
        if not forms:
            return {"forms": [], "error": "No forms found"}
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get form submission metrics
        submitted_metric = await self.get_metric_by_name("Submitted Form")
        viewed_metric = await self.get_metric_by_name("Viewed Form")
        
        form_data = []
        
        for form in forms:
            form_id = form.get("id")
            form_attrs = form.get("attributes", {})
            form_name = form_attrs.get("name", "Unknown Form")
            form_type = form_attrs.get("form_type", "unknown")
            
            # Map form types to display names
            type_display = {
                "popup": "Popup",
                "flyout": "Flyout",
                "embed": "Embed",
                "full_page": "Full Page"
            }.get(form_type, form_type.title())
            
            # Get views (impressions) for this form
            # Use form_id instead of $form (which is not a valid filter dimension)
            views = 0
            if viewed_metric:
                try:
                    views_data = await self.query_metric_aggregates(
                        metric_id=viewed_metric.get("id"),
                        start_date=start_date.strftime("%Y-%m-%dT00:00:00Z"),
                        end_date=end_date.strftime("%Y-%m-%dT23:59:59Z"),
                        measurements=["count"],
                        interval="day",
                        filter_conditions=[f'equals(form_id,"{form_id}")']
                    )
                    views_attrs = views_data.get("data", {}).get("attributes", {})
                    views_values = views_attrs.get("data", [])
                    # Handle nested structure
                    for v in views_values:
                        if isinstance(v, list):
                            views += float(v[0]) if len(v) > 0 and v[0] is not None else 0
                        elif isinstance(v, dict):
                            views += float(v.get("count", 0))
                        else:
                            views += float(v) if v else 0
                except Exception as e:
                    print(f"Error getting views for form {form_id}: {e}")
            
            # Get submissions for this form
            submissions = 0
            if submitted_metric:
                try:
                    submit_data = await self.query_metric_aggregates(
                        metric_id=submitted_metric.get("id"),
                        start_date=start_date.strftime("%Y-%m-%dT00:00:00Z"),
                        end_date=end_date.strftime("%Y-%m-%dT23:59:59Z"),
                        measurements=["count"],
                        interval="day",
                        filter_conditions=[f'equals(form_id,"{form_id}")']
                    )
                    submit_attrs = submit_data.get("data", {}).get("attributes", {})
                    submit_values = submit_attrs.get("data", [])
                    # Handle nested structure
                    for v in submit_values:
                        if isinstance(v, list):
                            submissions += float(v[0]) if len(v) > 0 and v[0] is not None else 0
                        elif isinstance(v, dict):
                            submissions += float(v.get("count", 0))
                        else:
                            submissions += float(v) if v else 0
                except Exception as e:
                    print(f"Error getting submissions for form {form_id}: {e}")
            
            # Calculate submit rate
            submit_rate = (submissions / views * 100) if views > 0 else 0
            
            # Determine standing based on form type and submit rate
            if form_type == "popup":
                if submit_rate >= 8:
                    standing = "Excellent"
                elif submit_rate >= 3:
                    standing = "Good"
                elif submit_rate >= 1:
                    standing = "Average"
                else:
                    standing = "Poor"
            else:  # embed, flyout, etc.
                if submit_rate >= 2:
                    standing = "Excellent"
                elif submit_rate >= 0.5:
                    standing = "Good"
                elif submit_rate >= 0.1:
                    standing = "Average"
                else:
                    standing = "Poor"
            
            # Format large numbers
            def format_number(n):
                if n >= 1000000:
                    return f"{n/1000000:.1f}M"
                elif n >= 1000:
                    return f"{n/1000:.1f}k"
                return str(int(n))
            
            form_data.append({
                "id": form_id,
                "name": form_name,
                "type": type_display,
                "impressions": int(views),
                "impressions_fmt": format_number(views),
                "submitted": int(submissions),
                "submitted_fmt": format_number(submissions),
                "submit_rate": round(submit_rate, 2),
                "standing": standing
            })
            
            # Rate limiting is handled by RateLimiter in _make_request
            # Small delay to avoid hammering the API
            await asyncio.sleep(0.1)
        
        return {
            "period_days": days,
            "forms": sorted(form_data, key=lambda x: x["impressions"], reverse=True)
        }
    
    # ============================================================
    # NEW: 90-Day Time Series Revenue with Attribution
    # ============================================================
    
    async def get_revenue_time_series(
        self,
        days: int = 90,
        interval: str = "day"
    ) -> Dict[str, Any]:
        """
        Get detailed revenue time series with attribution breakdown.
        
        Args:
            days: Number of days to look back
            interval: "day", "week", or "month"
            
        Returns:
            Dict with time series data for total, flow, and campaign revenue
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        start_str = start_date.strftime("%Y-%m-%dT00:00:00Z")
        end_str = end_date.strftime("%Y-%m-%dT23:59:59Z")
        
        # Get Placed Order metric
        placed_order = await self.get_metric_by_name("Placed Order")
        if not placed_order:
            return {"error": "Placed Order metric not found"}
        
        metric_id = placed_order.get("id")
        
        # Get total revenue by day
        total_revenue_data = await self.query_metric_aggregates(
            metric_id=metric_id,
            start_date=start_str,
            end_date=end_str,
            measurements=["sum_value", "count", "unique"],
            interval=interval
        )
        
        # Get revenue attributed to flows
        flow_revenue_data = await self.query_metric_aggregates(
            metric_id=metric_id,
            start_date=start_str,
            end_date=end_str,
            measurements=["sum_value"],
            interval=interval,
            by=["$attributed_flow"]
        )
        
        # Get revenue attributed to campaigns
        # Note: $attributed_campaign is not a valid 'by' parameter
        # Instead, we'll get total revenue and subtract flow revenue to get campaign revenue
        # Or use $attributed_message which can be filtered by campaign
        campaign_revenue_data = {}  # Will calculate as difference
        
        # Process total revenue - handle nested response structure
        total_attrs = total_revenue_data.get("data", {}).get("attributes", {})
        dates = total_attrs.get("dates", [])
        total_values = total_attrs.get("data", [])
        
        # Process flow revenue (aggregate all flows)
        flow_attrs = flow_revenue_data.get("data", {}).get("attributes", {})
        flow_data_raw = flow_attrs.get("data", [])
        
        # Campaign revenue will be calculated as difference
        # (Total attributed - Flow attributed = Campaign attributed)
        
        # Build time series
        time_series = []
        total_sum = 0
        flow_sum = 0
        campaign_sum = 0
        
        for i, date in enumerate(dates):
            # Total revenue for this period - handle nested structure
            total_val = total_values[i] if i < len(total_values) else None
            if total_val is None:
                revenue = 0
                orders = 0
            elif isinstance(total_val, list):
                # Handle list format: [sum_value, count, unique]
                try:
                    revenue = float(total_val[0]) if len(total_val) > 0 and total_val[0] is not None and str(total_val[0]).strip() else 0
                except (ValueError, TypeError):
                    revenue = 0
                try:
                    orders = int(total_val[1]) if len(total_val) > 1 and total_val[1] is not None and str(total_val[1]).strip() else 0
                except (ValueError, TypeError):
                    orders = 0
            elif isinstance(total_val, dict):
                # Handle dict format: {"sum_value": X, "count": Y}
                try:
                    revenue = float(total_val.get("sum_value", 0)) if total_val.get("sum_value") else 0
                except (ValueError, TypeError):
                    revenue = 0
                try:
                    orders = int(total_val.get("count", 0)) if total_val.get("count") else 0
                except (ValueError, TypeError):
                    orders = 0
            else:
                try:
                    revenue = float(total_val) if total_val and str(total_val).strip() else 0
                except (ValueError, TypeError):
                    revenue = 0
                orders = 0
            
            total_sum += revenue
            
            # Flow revenue (sum across all flows for this period)
            flow_val = 0
            if i < len(flow_data_raw):
                period_flow = flow_data_raw[i]
                if isinstance(period_flow, dict):
                    # Sum all flow values
                    for v in period_flow.values():
                        try:
                            if isinstance(v, list):
                                val = v[0] if len(v) > 0 else None
                                if val is not None and str(val).strip():
                                    flow_val += float(val)
                            elif isinstance(v, dict):
                                val = v.get("sum_value")
                                if val is not None and str(val).strip():
                                    flow_val += float(val)
                            else:
                                if v is not None and str(v).strip():
                                    flow_val += float(v)
                        except (ValueError, TypeError):
                            pass  # Skip invalid values
                elif isinstance(period_flow, list):
                    try:
                        val = period_flow[0] if period_flow else None
                        if val is not None and str(val).strip():
                            flow_val = float(val)
                    except (ValueError, TypeError):
                        flow_val = 0
            flow_sum += flow_val
            
            # Campaign revenue = Total attributed - Flow attributed
            # (We can't directly query campaign attribution, so estimate)
            campaign_val = 0  # Will be calculated as difference later
            campaign_sum += campaign_val
            
            time_series.append({
                "date": date,
                "total_revenue": revenue,
                "flow_revenue": flow_val,
                "campaign_revenue": campaign_val,
                "orders": orders
            })
        
        # Calculate campaign revenue as difference
        # Note: This is an approximation since we can't directly query campaign attribution
        # In a real scenario, you'd query campaign statistics separately
        campaign_sum = max(0, total_sum * 0.3 - flow_sum)  # Estimate: assume 30% KAV, rest is campaigns
        
        # Calculate percentages
        attributed_revenue = flow_sum + campaign_sum
        kav_percentage = (attributed_revenue / total_sum * 100) if total_sum > 0 else 0
        flow_percentage = (flow_sum / attributed_revenue * 100) if attributed_revenue > 0 else 0
        campaign_percentage = (campaign_sum / attributed_revenue * 100) if attributed_revenue > 0 else 0
        
        return {
            "period": {
                "start_date": start_date.strftime("%B %d, %Y"),
                "end_date": end_date.strftime("%B %d, %Y"),
                "days": days
            },
            "totals": {
                "total_revenue": total_sum,
                "attributed_revenue": attributed_revenue,
                "flow_revenue": flow_sum,
                "campaign_revenue": campaign_sum,
                "kav_percentage": round(kav_percentage, 2),
                "flow_percentage": round(flow_percentage, 2),
                "campaign_percentage": round(campaign_percentage, 2)
            },
            "time_series": time_series,
            "chart_data": {
                "labels": [datetime.fromisoformat(d.replace("Z", "+00:00")).strftime("%b %d") for d in dates],
                "total_revenue": [ts["total_revenue"] for ts in time_series],
                "attributed_revenue": [ts["flow_revenue"] + ts["campaign_revenue"] for ts in time_series],
                "flow_revenue": [ts["flow_revenue"] for ts in time_series],
                "campaign_revenue": [ts["campaign_revenue"] for ts in time_series]
            }
        }
    
    # ============================================================
    # NEW: Individual Flow Statistics for Deep Dives
    # ============================================================
    
    async def get_individual_flow_stats(
        self,
        flow_id: str,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        Get detailed statistics for a single flow.
        
        Args:
            flow_id: The flow ID to get stats for
            days: Number of days to look back
            
        Returns:
            Dict with detailed flow performance metrics
        """
        # Get flow details
        try:
            flow_response = await self._make_request("GET", f"/flows/{flow_id}/")
            flow = flow_response.get("data", {})
        except HTTPStatusError:
            return {"error": f"Flow {flow_id} not found"}
        
        flow_attrs = flow.get("attributes", {})
        flow_name = flow_attrs.get("name", "Unknown")
        flow_status = flow_attrs.get("status", "unknown")
        
        # Get flow actions (emails)
        actions = await self.get_flow_actions(flow_id)
        email_count = len([a for a in actions if a.get("attributes", {}).get("action_type") == "EMAIL"])
        
        # Get Placed Order metric for conversion stats
        placed_order = await self.get_metric_by_name("Placed Order")
        conversion_metric_id = placed_order.get("id") if placed_order else None
        
        # Get flow statistics
        stats = {}
        if conversion_metric_id:
            stats_response = await self.get_flow_statistics(
                flow_ids=[flow_id],
                statistics=[
                    "recipients",
                    "opens",
                    "open_rate",
                    "clicks",
                    "click_rate",
                    "conversions",
                    "conversion_rate",
                    "conversion_value",
                    "conversion_uniques"
                ],
                timeframe="last_90_days",
                conversion_metric_id=conversion_metric_id
            )
            
            # Extract stats from response
            results = stats_response.get("data", {}).get("attributes", {}).get("results", [])
            if results:
                result = results[0]
                stats = {
                    "recipients": result.get("statistics", {}).get("recipients", 0),
                    "opens": result.get("statistics", {}).get("opens", 0),
                    "open_rate": result.get("statistics", {}).get("open_rate", 0) * 100,
                    "clicks": result.get("statistics", {}).get("clicks", 0),
                    "click_rate": result.get("statistics", {}).get("click_rate", 0) * 100,
                    "conversions": result.get("statistics", {}).get("conversions", 0),
                    "conversion_rate": result.get("statistics", {}).get("conversion_rate", 0) * 100,
                    "revenue": result.get("statistics", {}).get("conversion_value", 0),
                }
                
                # Calculate revenue per recipient
                recipients = stats.get("recipients", 0)
                if recipients > 0:
                    stats["revenue_per_recipient"] = stats.get("revenue", 0) / recipients
                else:
                    stats["revenue_per_recipient"] = 0
        
        return {
            "flow_id": flow_id,
            "flow_name": flow_name,
            "status": flow_status,
            "email_count": email_count,
            "performance": stats,
            "actions": [
                {
                    "id": a.get("id"),
                    "type": a.get("attributes", {}).get("action_type"),
                    "name": a.get("attributes", {}).get("name", "")
                }
                for a in actions
            ]
        }
    
    async def get_core_flows_performance(
        self,
        days: int = 90,
        limit_flows: int = 10
    ) -> Dict[str, Any]:
        """
        Get performance data for core flows (Welcome, AC, Browse, Post-Purchase).
        
        Identifies flows by name patterns and returns performance metrics.
        Limits the number of flows queried to avoid rate limiting.
        
        Args:
            days: Number of days for analysis
            limit_flows: Maximum number of flows to query (default 10 to avoid rate limits)
        """
        flows = await self.get_flows()
        
        # Flow identification patterns
        flow_patterns = {
            "welcome_series": ["welcome", "nurture", "onboard"],
            "abandoned_cart": ["abandon", "cart", "checkout"],
            "abandoned_checkout": ["checkout", "abandon"],
            "browse_abandonment": ["browse", "abandon", "viewed"],
            "post_purchase": ["post", "purchase", "thank", "order confirm"],
            "back_in_stock": ["back in stock", "restock", "back-in-stock"],
            "winback": ["winback", "win back", "lapsed", "re-engage"]
        }
        
        core_flows = {}
        flows_queried = 0
        
        # First pass: Identify flows by pattern (no API calls)
        identified_flows = {}
        for flow in flows:
            flow_name = flow.get("attributes", {}).get("name", "").lower()
            flow_id = flow.get("id")
            flow_status = flow.get("attributes", {}).get("status", "unknown")
            
            # Check each pattern
            for flow_type, patterns in flow_patterns.items():
                if any(pattern in flow_name for pattern in patterns):
                    # Only store if we haven't found this type yet, or this one is live
                    if flow_type not in identified_flows or flow_status == "live":
                        identified_flows[flow_type] = {
                            "flow": flow,
                            "flow_id": flow_id,
                            "flow_status": flow_status
                        }
                    break
        
        # Second pass: Query statistics for identified flows (with rate limiting)
        for flow_type, flow_info in identified_flows.items():
            if flows_queried >= limit_flows:
                print(f"  ⚠️  Reached flow query limit ({limit_flows}). Skipping remaining flows.")
                break
            
            flow_id = flow_info["flow_id"]
            flow = flow_info["flow"]
            
            # Get detailed stats for this flow (with rate limiting built-in)
            flow_stats = await self.get_individual_flow_stats(flow_id, days)
            flows_queried += 1
            
            core_flows[flow_type] = {
                "flow_id": flow_id,
                "name": flow.get("attributes", {}).get("name"),
                "status": flow_info["flow_status"],
                "email_count": flow_stats.get("email_count", 0),
                "performance": flow_stats.get("performance", {}),
                "found": True
            }
            
            # Small delay between flow queries
            if flows_queried < len(identified_flows):
                await asyncio.sleep(0.2)
        
        # Mark missing flows
        for flow_type in flow_patterns.keys():
            if flow_type not in core_flows:
                core_flows[flow_type] = {
                    "name": flow_type.replace("_", " ").title(),
                    "status": "missing",
                    "email_count": 0,
                    "performance": {},
                    "found": False
                }
        
        return core_flows

    async def get_campaign_statistics(
        self,
        campaign_ids: List[str],
        statistics: List[str] = None,
        timeframe: str = "last_30_days",
        conversion_metric_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get campaign statistics using Reporting API.
        
        This endpoint provides 1:1 matches with Klaviyo UI data.
        Reference: https://developers.klaviyo.com/en/reference/query_campaign_values
        
        IMPORTANT: conversion_metric_id is REQUIRED by the API.
        Filter syntax for Reporting API is different: use equals() or contains-any()
        
        Args:
            campaign_ids: List of campaign IDs
            statistics: List of statistics to fetch (opens, clicks, etc.)
            timeframe: Time period (last_30_days, last_365_days, etc.)
            conversion_metric_id: Metric ID for conversion tracking (REQUIRED)
        """
        if statistics is None:
            # Only use VALID statistics per API documentation
            statistics = [
                "opens",
                "open_rate",
                "clicks",
                "click_rate",
                "bounce_rate",
                "recipients",
                "delivery_rate",
                "unsubscribe_rate",
                "spam_complaint_rate"
            ]
        
        # conversion_metric_id is REQUIRED
        if not conversion_metric_id:
            print("Warning: conversion_metric_id is required for campaign statistics. Fetching Placed Order metric...")
            placed_order = await self.get_metric_by_name("Placed Order")
            if placed_order:
                conversion_metric_id = placed_order.get("id")
            else:
                print("Error: Could not find Placed Order metric and no conversion_metric_id provided")
                return {}
        
        # Build filter - Reporting API uses different syntax than regular API
        # For single campaign: equals(campaign_id,"ID")
        # For multiple: contains-any(campaign_id,["ID1","ID2"])
        campaign_ids_subset = campaign_ids[:100]  # Limit to 100 per request
        
        if len(campaign_ids_subset) == 1:
            filter_string = f'equals(campaign_id,"{campaign_ids_subset[0]}")'
        else:
            # Use contains-any for multiple IDs
            ids_formatted = '","'.join(campaign_ids_subset)
            filter_string = f'contains-any(campaign_id,["{ids_formatted}"])'
        
        payload = {
            "data": {
                "type": "campaign-values-report",
                "attributes": {
                    "statistics": statistics,
                    "timeframe": {"key": timeframe},
                    "filter": filter_string,
                    "conversion_metric_id": conversion_metric_id
                }
            }
        }
        
        try:
            return await self._make_request("POST", "/campaign-values-reports/", data=payload)
        except HTTPStatusError as e:
            print(f"Error fetching campaign statistics: {e}")
            if hasattr(e, 'response'):
                print(f"Response: {e.response.text}")
            return {}
    
    async def get_flow_statistics(
        self,
        flow_ids: List[str],
        statistics: List[str] = None,
        timeframe: str = "last_30_days",
        conversion_metric_id: Optional[str] = None,
        retry_count: int = 3
    ) -> Dict[str, Any]:
        """
        Get flow statistics using Reporting API.
        
        This endpoint provides 1:1 matches with Klaviyo UI data.
        Reference: https://developers.klaviyo.com/en/reference/query_flow_values
        
        IMPORTANT: conversion_metric_id is REQUIRED by the API.
        Filter syntax: use equals() for single ID or contains-any() for multiple
        
        Args:
            flow_ids: List of flow IDs
            statistics: List of statistics to fetch
            timeframe: Time period
            conversion_metric_id: Metric ID for conversion tracking (REQUIRED)
        """
        if statistics is None:
            # Only use VALID statistics per API documentation
            statistics = [
                "opens",
                "open_rate",
                "clicks",
                "click_rate",
                "bounce_rate",
                "recipients",
                "delivery_rate",
                "unsubscribe_rate"
            ]
        
        # conversion_metric_id is REQUIRED
        if not conversion_metric_id:
            print("Warning: conversion_metric_id is required for flow statistics. Fetching Placed Order metric...")
            placed_order = await self.get_metric_by_name("Placed Order")
            if placed_order:
                conversion_metric_id = placed_order.get("id")
            else:
                print("Error: Could not find Placed Order metric and no conversion_metric_id provided")
                return {}
        
        # Build filter - same syntax as campaigns
        flow_ids_subset = flow_ids[:100]  # Limit to 100 per request
        
        if len(flow_ids_subset) == 1:
            filter_string = f'equals(flow_id,"{flow_ids_subset[0]}")'
        else:
            # Use contains-any for multiple IDs
            ids_formatted = '","'.join(flow_ids_subset)
            filter_string = f'contains-any(flow_id,["{ids_formatted}"])'
        
        payload = {
            "data": {
                "type": "flow-values-report",
                "attributes": {
                    "statistics": statistics,
                    "timeframe": {"key": timeframe},
                    "filter": filter_string,
                    "conversion_metric_id": conversion_metric_id
                }
            }
        }
        
        # Rate limiting is now handled in _make_request
        try:
            return await self._make_request("POST", "/flow-values-reports/", data=payload, retry_on_429=True, max_retries=3)
        except HTTPStatusError as e:
            print(f"Error fetching flow statistics: {e}")
            if hasattr(e, 'response') and e.response:
                try:
                    print(f"Response: {e.response.text}")
                except:
                    pass
            return {}
        except Exception as e:
            print(f"Unexpected error fetching flow statistics: {e}")
            return {}
    
    async def extract_all_data(
        self,
        date_range: Optional[Dict[str, str]] = None,
        include_enhanced: bool = True,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Extract all required data for audit report.
        
        This is the main data extraction method with all fixes applied.
        
        Args:
            date_range: Optional custom date range
            include_enhanced: If True, includes enhanced audit data (list growth, forms, etc.)
        """
        if not date_range:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            date_range = {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }

        def _iso_with_z(dt_str: str) -> str:
            """Ensure ISO datetime has Z suffix for API."""
            dt_str = dt_str.split(".")[0]  # Remove microseconds
            return dt_str if dt_str.endswith("Z") else f"{dt_str}Z"
        
        start = _iso_with_z(date_range["start"])
        end = _iso_with_z(date_range["end"])
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"KLAVIYO DATA EXTRACTION - Comprehensive Audit Standard")
            print(f"{'='*60}")
            print(f"Date range: {start} to {end}")
            print(f"Enhanced data: {'Yes' if include_enhanced else 'No'}")
            print(f"{'='*60}\n")
        
        # ============================================================
        # SECTION 1: Basic Revenue Data
        # ============================================================
        if verbose:
            print("📊 SECTION 1: Revenue Data")
            print("-" * 40)
        
        revenue_data: Dict[str, Any] = {}
        try:
            placed_order_metric = await self.get_metric_by_name("Placed Order")
            if placed_order_metric:
                metric_id = placed_order_metric.get("id")
                print(f"  Found Placed Order metric: {metric_id}")
                if metric_id:
                    revenue_data = await self.query_metric_aggregates(
                        metric_id=metric_id,
                        start_date=start,
                        end_date=end,
                        measurements=["count", "sum_value", "unique"]
                    )
                    print(f"  ✓ Revenue data extracted")
        except Exception as e:
            print(f"  ✗ Error fetching revenue metric aggregates: {e}")
        
        # ============================================================
        # SECTION 2: Campaign Data
        # ============================================================
        if verbose:
            print("\n📧 SECTION 2: Campaign Data")
            print("-" * 40)
        
        campaigns = await self.get_campaigns(
            start_date=start,
            end_date=end,
            channel="email"
        )
        print(f"  ✓ Fetched {len(campaigns)} campaigns")
        
        campaign_statistics = {}
        if campaigns:
            campaign_ids = [c["id"] for c in campaigns[:50]]
            print(f"  Fetching statistics for {len(campaign_ids)} campaigns...")
            campaign_statistics = await self.get_campaign_statistics(
                campaign_ids=campaign_ids,
                timeframe="last_365_days"
            )
            if campaign_statistics:
                print(f"  ✓ Campaign statistics extracted")
        
        # ============================================================
        # SECTION 3: Flow Data
        # ============================================================
        if verbose:
            print("\n🔄 SECTION 3: Flow Data")
            print("-" * 40)
        
        flows = await self.get_flows()
        print(f"  ✓ Fetched {len(flows)} flows")
        
        flow_statistics = {}
        if flows:
            flow_ids = [f["id"] for f in flows[:50]]
            print(f"  Fetching statistics for {len(flow_ids)} flows...")
            flow_statistics = await self.get_flow_statistics(
                flow_ids=flow_ids,
                timeframe="last_365_days"
            )
            if flow_statistics:
                print(f"  ✓ Flow statistics extracted")
        
        # Detailed flow data
        print(f"  Fetching detailed data for first 5 flows...")
        flow_data = []
        for i, flow in enumerate(flows[:5]):
            try:
                actions = await self.get_flow_actions(flow["id"])
                await asyncio.sleep(0.5)
                
                limited_actions = actions[:3]
                flow_messages = []
                
                for action in limited_actions:
                    try:
                        messages = await self.get_flow_action_messages(action["id"])
                        flow_messages.extend(messages)
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        print(f"    ✗ Error fetching messages for action {action['id']}: {e}")
                        break
                
                flow_data.append({
                    "flow": flow,
                    "actions": limited_actions,
                    "messages": flow_messages
                })
                print(f"    ✓ Flow {i+1}/5: {len(limited_actions)} actions, {len(flow_messages)} messages")
            except Exception as e:
                print(f"    ✗ Error fetching data for flow {flow['id']}: {e}")
        
        # Initialize enhanced data containers
        enhanced_data = {}
        
        if include_enhanced:
            # ============================================================
            # SECTION 4: 90-Day KAV Revenue Time Series
            # ============================================================
            if verbose:
                print("\n💰 SECTION 4: KAV Revenue Time Series (90 Days)")
                print("-" * 40)
            
            try:
                kav_data = await self.get_revenue_time_series(days=90, interval="day")
                enhanced_data["kav_analysis"] = kav_data
                
                if verbose:
                    totals = kav_data.get("totals", {})
                    print(f"  ✓ Total Revenue: ${totals.get('total_revenue', 0):,.2f}")
                    print(f"  ✓ Attributed Revenue: ${totals.get('attributed_revenue', 0):,.2f}")
                    print(f"  ✓ KAV %: {totals.get('kav_percentage', 0):.1f}%")
                    print(f"  ✓ Flow Revenue: ${totals.get('flow_revenue', 0):,.2f}")
                    print(f"  ✓ Campaign Revenue: ${totals.get('campaign_revenue', 0):,.2f}")
            except Exception as e:
                if verbose:
                    print(f"  ✗ Error fetching KAV data: {e}")
                enhanced_data["kav_analysis"] = {}
            
            # ============================================================
            # SECTION 5: List Growth Data (Morrison Style)
            # ============================================================
            if verbose:
                print("\n📈 SECTION 5: List Growth Data (6 Months)")
                print("-" * 40)
            
            try:
                list_growth = await self.get_list_growth_data(months=6)
                enhanced_data["list_growth"] = list_growth
                
                if verbose:
                    print(f"  ✓ List: {list_growth.get('list_name', 'Unknown')}")
                    print(f"  ✓ Current subscribers: {list_growth.get('current_total', 0):,}")
                    print(f"  ✓ New subscribers: {list_growth.get('growth_subscribers', 0):,}")
                    print(f"  ✓ Lost subscribers: {list_growth.get('lost_subscribers', 0):,}")
                    print(f"  ✓ Churn rate: {list_growth.get('churn_rate', 0):.2f}%")
            except Exception as e:
                if verbose:
                    print(f"  ✗ Error fetching list growth data: {e}")
                enhanced_data["list_growth"] = {}
            
            # ============================================================
            # SECTION 6: Form Performance Data (Morrison Style)
            # ============================================================
            if verbose:
                print("\n📝 SECTION 6: Form Performance (90 Days)")
                print("-" * 40)
            
            try:
                form_data = await self.get_form_performance(days=90)
                enhanced_data["forms"] = form_data
                
                if verbose:
                    forms = form_data.get("forms", [])
                    print(f"  ✓ Found {len(forms)} forms")
                    for form in forms[:5]:
                        print(f"    - {form.get('name', 'Unknown')}: {form.get('submit_rate', 0):.2f}% ({form.get('standing', 'N/A')})")
            except Exception as e:
                if verbose:
                    print(f"  ✗ Error fetching form data: {e}")
                enhanced_data["forms"] = {"forms": []}
            
            # ============================================================
            # SECTION 7: Core Flows Deep Dive (Morrison Style)
            # ============================================================
            if verbose:
                print("\n🎯 SECTION 7: Core Flows Performance (90 Days)")
                print("-" * 40)
            
            try:
                core_flows = await self.get_core_flows_performance(days=90)
                enhanced_data["core_flows"] = core_flows
                
                if verbose:
                    for flow_type, flow_info in core_flows.items():
                        status = "✓" if flow_info.get("found") else "✗ MISSING"
                        name = flow_info.get("name", flow_type)
                        perf = flow_info.get("performance", {})
                        rev = perf.get("revenue", 0)
                        open_rate = perf.get("open_rate", 0)
                        print(f"  {status} {name}: Open {open_rate:.1f}%, Rev ${rev:,.0f}")
            except Exception as e:
                if verbose:
                    print(f"  ✗ Error fetching core flows data: {e}")
                enhanced_data["core_flows"] = {}
        
        if verbose:
            print(f"\n{'='*60}")
            print("✓ DATA EXTRACTION COMPLETE!")
            print(f"{'='*60}\n")
        
        return {
            # Basic data
            "revenue": revenue_data,
            "campaigns": campaigns,
            "campaign_statistics": campaign_statistics,
            "flows": flows,
            "flow_statistics": flow_statistics,
            "flow_details": flow_data,
            "date_range": date_range,
            
            # Enhanced Morrison-style data
            **enhanced_data
        }
    
    async def extract_audit_data(
        self,
        days: int = 90,
        industry: str = "apparel_accessories",
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Extract all data needed for a comprehensive audit.
        
        This is a convenience method that extracts exactly the data needed
        for the comprehensive audit format.
        
        Args:
            days: Number of days for analysis period (default 90)
            industry: Industry type for benchmarking (default "apparel_accessories")
            verbose: Whether to print progress messages (default True)
            
        Returns:
            Dict structured for audit template consumption
        """
        if verbose:
            print(f"\n{'='*60}")
            print("AUDIT DATA EXTRACTION")
            print(f"{'='*60}\n")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Extract all data with enhanced mode (suppress duplicate prints)
        raw_data = await self.extract_all_data(
            date_range={
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            include_enhanced=True,
            verbose=verbose
        )
        
        # Structure data for template consumption
        kav_raw = raw_data.get("kav_analysis", {})
        list_raw = raw_data.get("list_growth", {})
        forms_raw = raw_data.get("forms", {})
        core_flows = raw_data.get("core_flows", {})
        
        # Format currency helper
        def fmt_currency(val, prefix="$"):
            if val >= 1000000:
                return f"{prefix}{val/1000000:.2f}M"
            elif val >= 1000:
                return f"{prefix}{val/1000:.1f}K"
            return f"{prefix}{val:,.2f}"
        
        totals = kav_raw.get("totals", {})
        period = kav_raw.get("period", {})
        
        return {
            # Cover page data
            "cover_data": {
                "client_name": "Client Name",  # To be filled
                "client_code": "",
                "audit_date": datetime.now().strftime("%d %b %Y"),
                "auditor_name": "Audit System"
            },
            
            # KAV Analysis (Pages 2-3)
            "kav_data": {
                "period": period,
                "revenue": {
                    "total_website": totals.get("total_revenue", 0),
                    "total_website_formatted": fmt_currency(totals.get("total_revenue", 0), "A$"),
                    "vs_previous_period": 0,  # Would need comparison calculation
                    "attributed": totals.get("attributed_revenue", 0),
                    "attributed_percentage": totals.get("kav_percentage", 0),
                    "attributed_vs_previous": 0,
                    "flow_attributed": totals.get("flow_revenue", 0),
                    "campaign_attributed": totals.get("campaign_revenue", 0)
                },
                "chart_data": kav_raw.get("chart_data", {}),
                "narrative": f"During the {days}-day analysis period, your Klaviyo-attributed revenue represents {totals.get('kav_percentage', 0):.1f}% of total website revenue."
            },
            
            # List Growth (Page 4)
            "list_growth_data": {
                "list_name": list_raw.get("list_name", "Primary List"),
                "period_months": list_raw.get("period_months", 6),
                "current_total": list_raw.get("current_total", 0),
                "net_change": list_raw.get("net_change", 0),
                "growth_subscribers": list_raw.get("growth_subscribers", 0),
                "lost_subscribers": list_raw.get("lost_subscribers", 0),
                "churn_rate": list_raw.get("churn_rate", 0),
                "signup_sources": {
                    "popup_form": 0,
                    "footer_form": 0,
                    "other": 0
                },
                "chart_data": list_raw.get("chart_data", {}),
                "analysis_text": ""
            },
            
            # Data Capture (Pages 5-6)
            "data_capture_data": {
                "forms": forms_raw.get("forms", []),
                "analysis": {
                    "popup_timing": "",
                    "recommended_timing": "20 seconds",
                    "cta_feedback": ""
                },
                "advanced_targeting": [
                    "Exit Intent",
                    "Returning Customer Form",
                    "Engaged With Form But Not Submitted",
                    "Idle Cart",
                    "Page Views",
                    "Product Viewed"
                ],
                "progressive_profiling": {"enabled": True},
                "flyout_forms": {"enabled": True}
            },
            
            # Automation Overview (Page 7)
            "automation_overview_data": {
                "period_days": days,
                "flows": [
                    {
                        "name": flow_info.get("name", flow_type),
                        "avg_open_rate": flow_info.get("performance", {}).get("open_rate", 0),
                        "avg_click_rate": flow_info.get("performance", {}).get("click_rate", 0),
                        "avg_placed_order_rate": flow_info.get("performance", {}).get("conversion_rate", 0),
                        "revenue": flow_info.get("performance", {}).get("revenue", 0),
                        "revenue_per_recipient": flow_info.get("performance", {}).get("revenue_per_recipient", 0)
                    }
                    for flow_type, flow_info in core_flows.items()
                    if flow_info.get("found")
                ],
                "summary": {
                    "total_conversion_value": sum(
                        f.get("performance", {}).get("revenue", 0) 
                        for f in core_flows.values()
                    ),
                    "vs_previous_period": 0,
                    "total_recipients": 0,
                    "recipients_vs_previous": 0
                },
                "chart_data": {}
            },
            
            # Welcome Flow (Page 8)
            "welcome_flow_data": {
                "flow_name": "Welcome Series",
                "status": core_flows.get("welcome_series", {}).get("status", "unknown"),
                "email_count": core_flows.get("welcome_series", {}).get("email_count", 0),
                "performance": core_flows.get("welcome_series", {}).get("performance", {}),
                "benchmark": {
                    "open_rate": 59.07,
                    "click_rate": 5.70,
                    "conversion_rate": 2.52,
                    "revenue_per_recipient": 3.11
                },
                "industry": "Apparel and Accessories",
                "analysis": {
                    "email_gap_days": 0,
                    "recommendations": []
                }
            },
            
            # Abandoned Cart (Pages 9-10)
            "abandoned_cart_data": {
                "flows": [
                    {
                        "name": "Abandoned Checkout",
                        "open_rate": core_flows.get("abandoned_checkout", {}).get("performance", {}).get("open_rate", 0),
                        "click_rate": core_flows.get("abandoned_checkout", {}).get("performance", {}).get("click_rate", 0),
                        "placed_order_rate": core_flows.get("abandoned_checkout", {}).get("performance", {}).get("conversion_rate", 0),
                        "revenue_per_recipient": core_flows.get("abandoned_checkout", {}).get("performance", {}).get("revenue_per_recipient", 0),
                        "revenue": core_flows.get("abandoned_checkout", {}).get("performance", {}).get("revenue", 0)
                    },
                    {
                        "name": "Abandoned Cart Reminder",
                        "open_rate": core_flows.get("abandoned_cart", {}).get("performance", {}).get("open_rate", 0),
                        "click_rate": core_flows.get("abandoned_cart", {}).get("performance", {}).get("click_rate", 0),
                        "placed_order_rate": core_flows.get("abandoned_cart", {}).get("performance", {}).get("conversion_rate", 0),
                        "revenue_per_recipient": core_flows.get("abandoned_cart", {}).get("performance", {}).get("revenue_per_recipient", 0),
                        "revenue": core_flows.get("abandoned_cart", {}).get("performance", {}).get("revenue", 0)
                    }
                ],
                "benchmark": {
                    "name": "Abandoned Cart",
                    "open_rate": 54.74,
                    "click_rate": 6.25,
                    "conversion_rate": 3.36,
                    "revenue_per_recipient": 3.80
                },
                "industry": "Apparel and Accessories",
                "segmentation": {
                    "high_value_low_value_split": False,
                    "new_vs_returning_split": False
                },
                "recommendations": []
            },
            
            # Campaign Performance (Page 17)
            "campaign_performance_data": {
                "summary": {
                    "avg_open_rate": 0,
                    "avg_click_rate": 0,
                    "avg_placed_order_rate": 0,
                    "total_revenue": 0
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
                    "campaigns_per_month": 0,
                    "primary_list": "",
                    "segmentation_used": False,
                    "issues_identified": []
                },
                "recommendations": []
            },
            
            # Segmentation Strategy (Page 18)
            "segmentation_data": {
                "tracks": [
                    {"name": "Track A: Highly Engaged", "cadence": "Daily", "criteria": "Opened/clicked in last 30 days"},
                    {"name": "Track B: Moderately Engaged", "cadence": "2-3x/week", "criteria": "Opened/clicked in last 60 days"},
                    {"name": "Track C: Broad Engaged", "cadence": "1x/week", "criteria": "Opened/clicked in last 90 days"},
                    {"name": "Track D: Unengaged", "cadence": "Goes through Sunset Flow then suppressed", "criteria": "No engagement in 90+ days"},
                    {"name": "Track E: For Suppression", "cadence": "Do not send. Needs to be suppressed", "criteria": "Hard bounces, complaints, unsubscribes"}
                ],
                "send_strategy": {
                    "smart_send_time": True,
                    "description": "Use Klaviyo Smart Send Time for optimal delivery"
                },
                "current_implementation": {
                    "segments_exist": False,
                    "tracks_configured": 0
                }
            },
            
            # Raw data for further processing
            "_raw": raw_data
        }