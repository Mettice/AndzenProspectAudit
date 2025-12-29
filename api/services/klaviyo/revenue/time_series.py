"""Revenue time series service for KAV analysis."""
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta

from ..client import KlaviyoClient
from ..metrics.service import MetricsService
from ..metrics.aggregates import MetricAggregatesService
from ..flows.statistics import FlowStatisticsService
from ..flows.service import FlowsService
from ..campaigns.statistics import CampaignStatisticsService
from ..campaigns.service import CampaignsService
from ..parsers import parse_metric_value, parse_metric_list_value, parse_nested_aggregate_values, parse_aggregate_data

logger = logging.getLogger(__name__)


class RevenueTimeSeriesService:
    """Service for revenue time series and KAV (Klaviyo Attributed Value) analysis."""
    
    def __init__(self, client: KlaviyoClient):
        """
        Initialize revenue time series service.
        
        Args:
            client: KlaviyoClient instance
        """
        self.client = client
        self.metrics = MetricsService(client)
        self.aggregates = MetricAggregatesService(client)
        self.flow_stats = FlowStatisticsService(client)
        self.flows = FlowsService(client)
        self.campaign_stats = CampaignStatisticsService(client)
        self.campaigns = CampaignsService(client)
    
    async def get_revenue_time_series(
        self,
        days: int = 90,
        interval: str = "day",
        account_timezone: str = "Australia/Sydney",
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Get detailed revenue time series with attribution breakdown.
        
        Uses Reporting API for flow and campaign revenue (matches Klaviyo UI).
        Uses Placed Order metric as it has attribution properties (order-level).
        
        Args:
            days: Number of days to look back (ignored if date_range provided)
            interval: "day", "week", or "month"
            account_timezone: Account timezone for proper date range calculation
            date_range: Optional custom date range (overrides days parameter)
            
        Returns:
            Dict with time series data for total, flow, and campaign revenue
        """
        from ..utils.date_helpers import get_klaviyo_compatible_range, parse_iso_date, ensure_z_suffix
        
        # Use provided date_range if available, otherwise calculate from days
        if date_range:
            start_str = ensure_z_suffix(date_range["start"])
            end_str = ensure_z_suffix(date_range["end"])
            # Calculate days from date range for logging
            start_dt = parse_iso_date(start_str)
            end_dt = parse_iso_date(end_str)
            days = (end_dt - start_dt).days
        else:
            # Get proper date range with timezone handling
            date_range = get_klaviyo_compatible_range(days, account_timezone)
            start_str = date_range["start"]
            end_str = date_range["end"]
        
        logger.info(f"Querying revenue data for {days} days: {start_str} to {end_str}")
        
        # Get Ordered Product metric for total revenue (matches dashboard)
        ordered_product = await self.metrics.get_metric_by_name("Ordered Product")
        if not ordered_product:
            logger.warning("Ordered Product metric not found, falling back to Placed Order")
            ordered_product = await self.metrics.get_metric_by_name("Placed Order")
        
        if not ordered_product:
            logger.error("No revenue metric found")
            return {"error": "No revenue metric found"}
        
        revenue_metric_id = ordered_product.get("id")
        revenue_metric_name = ordered_product.get("attributes", {}).get("name", "Unknown")
        logger.info(f"Using {revenue_metric_name} for total revenue: {revenue_metric_id}")
        
        # Get Placed Order metric for attribution (Reporting API requires this)
        # IMPORTANT: Prefer Shopify integration (Y6Hmxn) over API integration (U7yLfB)
        # The dashboard uses the Shopify metric, so we must match it
        placed_order = await self.metrics.get_metric_by_name("Placed Order", prefer_integration="shopify")
        if not placed_order:
            logger.warning("Shopify Placed Order metric not found, trying any Placed Order metric...")
            placed_order = await self.metrics.get_metric_by_name("Placed Order")
        
        if not placed_order:
            logger.error("Placed Order metric not found - cannot query attribution")
            return {"error": "Placed Order metric required for attribution"}
        
        conversion_metric_id = placed_order.get("id")
        integration = placed_order.get("attributes", {}).get("integration", {})
        integration_name = integration.get("name", "Unknown")
        logger.info(f"Using Placed Order for attribution: {conversion_metric_id} ({integration_name})")
        
        # ===== 1. TOTAL REVENUE via Aggregates API =====
        logger.info("Querying total revenue...")
        total_revenue_data = await self.aggregates.query(
            metric_id=revenue_metric_id,  # Use Ordered Product
            start_date=start_str,
            end_date=end_str,
            measurements=["sum_value", "count"],
            interval=interval,
            timezone=account_timezone
        )
        
        # If Ordered Product fails with month interval, try day interval and aggregate
        if not total_revenue_data or (isinstance(total_revenue_data, dict) and not total_revenue_data.get("data")):
            if interval == "month":
                logger.warning(f"Ordered Product metric ({revenue_metric_id}) failed with month interval, trying day interval...")
                total_revenue_data = await self.aggregates.query(
                    metric_id=revenue_metric_id,
                    start_date=start_str,
                    end_date=end_str,
                    measurements=["sum_value", "count"],
                    interval="day",  # Try day interval
                    timezone=account_timezone
                )
                # If day interval works, we'll aggregate to monthly later
        
        # If still fails, try Placed Order as fallback
        if not total_revenue_data or (isinstance(total_revenue_data, dict) and not total_revenue_data.get("data")):
            logger.warning(f"Ordered Product metric ({revenue_metric_id}) failed, trying Placed Order as fallback...")
            # Try using Placed Order metric for total revenue
            placed_order_metric = await self.metrics.get_metric_by_name("Placed Order", prefer_integration="shopify")
            if placed_order_metric:
                fallback_metric_id = placed_order_metric.get("id")
                logger.info(f"Using Placed Order metric ({fallback_metric_id}) for total revenue")
                # Try original interval first
                total_revenue_data = await self.aggregates.query(
                    metric_id=fallback_metric_id,
                    start_date=start_str,
                    end_date=end_str,
                    measurements=["sum_value", "count"],
                    interval=interval,
                    timezone=account_timezone
                )
                # If that fails and we wanted month, try day
                if (not total_revenue_data or (isinstance(total_revenue_data, dict) and not total_revenue_data.get("data"))) and interval == "month":
                    logger.warning(f"Placed Order metric failed with month interval, trying day interval...")
                    total_revenue_data = await self.aggregates.query(
                        metric_id=fallback_metric_id,
                        start_date=start_str,
                        end_date=end_str,
                        measurements=["sum_value", "count"],
                        interval="day",
                        timezone=account_timezone
                    )
        
        # Parse total revenue
        dates, total_values = parse_aggregate_data(total_revenue_data)
        total_sum = 0
        total_orders = 0
        monthly_revenue_values = []  # Store monthly values for chart
        monthly_order_values = []
        
        # Handle different response structures
        if len(total_values) == 1 and isinstance(total_values[0], dict):
            # Aggregated response (single aggregated value)
            measurements = total_values[0].get("measurements", {})
            sum_values = measurements.get("sum_value", [])
            count_values = measurements.get("count", [])
            total_sum = sum(float(val) for val in sum_values if val is not None)
            total_orders = sum(float(val) for val in count_values if val is not None)
            # For aggregated response, use the arrays directly if they exist
            if sum_values and len(sum_values) > 1:
                monthly_revenue_values = [float(v) if v is not None else 0 for v in sum_values]
                monthly_order_values = [float(v) if v is not None else 0 for v in count_values]
        elif len(total_values) > 1:
            # Multiple data points (monthly/daily breakdown)
            for value_item in total_values:
                if isinstance(value_item, dict):
                    measurements = value_item.get("measurements", {})
                    sum_val = measurements.get("sum_value", [0])[0] if isinstance(measurements.get("sum_value"), list) else measurements.get("sum_value", 0)
                    count_val = measurements.get("count", [0])[0] if isinstance(measurements.get("count"), list) else measurements.get("count", 0)
                    monthly_revenue_values.append(float(sum_val) if sum_val is not None else 0)
                    monthly_order_values.append(float(count_val) if count_val is not None else 0)
                    total_sum += float(sum_val) if sum_val is not None else 0
                    total_orders += float(count_val) if count_val is not None else 0
                elif isinstance(value_item, list):
                    # List format [sum_value, count, unique]
                    monthly_revenue_values.append(float(value_item[0]) if len(value_item) > 0 and value_item[0] is not None else 0)
                    monthly_order_values.append(float(value_item[1]) if len(value_item) > 1 and value_item[1] is not None else 0)
                    total_sum += float(value_item[0]) if len(value_item) > 0 and value_item[0] is not None else 0
                    total_orders += float(value_item[1]) if len(value_item) > 1 and value_item[1] is not None else 0
        
        logger.info(f"✅ Total Revenue: ${total_sum:,.2f} ({total_orders} orders)")
        logger.info(f"   Monthly data points: {len(monthly_revenue_values)} months, {len(dates)} dates")
        
        # ===== 2. FLOW REVENUE via Reporting API =====
        # Use Reporting API to match dashboard attribution model (single-touch, not multi-touch)
        # The metric-aggregates API with $attributed_flow uses multi-touch attribution which
        # can cause double-counting when combined with campaign revenue
        logger.info("Querying flow revenue via Reporting API (matches dashboard attribution)...")
        flow_sum = 0
        
        try:
            # Get all flows
            all_flows = await self.flows.get_flows()
            if all_flows:
                flow_ids = [f["id"] for f in all_flows]
                logger.info(f"Found {len(flow_ids)} flows")
                
                # Map days to timeframe for Reporting API
                if days <= 7:
                    timeframe = "last_7_days"
                elif days <= 30:
                    timeframe = "last_30_days"
                elif days <= 90:
                    timeframe = "last_90_days"
                else:
                    timeframe = "last_365_days"
                
                # CRITICAL FIX: Batch flow queries to avoid rate limiting
                # Process flows in smaller batches with delays
                batch_size = 10  # Smaller batches for revenue queries
                import asyncio
                
                for i in range(0, len(flow_ids), batch_size):
                    batch_ids = flow_ids[i:i + batch_size]
                    batch_num = (i // batch_size) + 1
                    total_batches = (len(flow_ids) + batch_size - 1) // batch_size
                    
                    try:
                        logger.debug(f"Querying flow revenue batch {batch_num}/{total_batches} ({len(batch_ids)} flows)...")
                        
                        # Query flow statistics with conversion_value for this batch
                        flow_stats_response = await self.flow_stats.get_statistics(
                            flow_ids=batch_ids,
                            statistics=["conversion_value", "conversions"],
                            timeframe=timeframe,
                            conversion_metric_id=conversion_metric_id,
                            use_cache=True  # Use cache if available
                        )
                        
                        # Extract revenue from response
                        if flow_stats_response and "data" in flow_stats_response:
                            results = flow_stats_response["data"].get("attributes", {}).get("results", [])
                            for result in results:
                                stats = result.get("statistics", {})
                                revenue = stats.get("conversion_value", 0)
                                flow_sum += float(revenue) if revenue else 0
                        
                        # Add delay between batches to avoid rate limiting
                        if i + batch_size < len(flow_ids):
                            await asyncio.sleep(5.0)  # 5 second delay between batches for revenue queries
                            
                    except Exception as batch_error:
                        logger.warning(f"Batch {batch_num} failed: {batch_error}. Continuing with remaining batches...")
                        # Continue with next batch instead of failing completely
                        if i + batch_size < len(flow_ids):
                            await asyncio.sleep(5.0)  # Still wait before next batch
                        continue
                
                logger.info(f"✅ Flow Revenue: ${flow_sum:,.2f}")
            else:
                logger.warning("No flows found")
        except Exception as e:
            logger.error(f"Error querying flow revenue: {e}", exc_info=True)
        
        # ===== 3. CAMPAIGN REVENUE via Reporting API (with date filtering) =====
        # Note: $attributed_campaign is NOT a valid grouping parameter in metric-aggregates
        # So we use Reporting API but filter campaigns by date range first
        logger.info("Querying campaign revenue via Reporting API (with date filtering)...")
        campaign_sum = 0
        
        try:
            # Filter campaigns by date range (campaigns sent in the period)
            # This ensures we only query statistics for campaigns active in the date range
            all_campaigns = await self.campaigns.get_campaigns(
                start_date=start_str,
                end_date=end_str
            )
            
            if all_campaigns:
                campaign_ids = [c["id"] for c in all_campaigns]
                logger.info(f"Found {len(campaign_ids)} campaigns in date range {start_str} to {end_str}")
                
                # Map days to timeframe for Reporting API
                # Note: Reporting API uses relative timeframes, but we've filtered campaigns by date
                # So the statistics should be for the correct period
                if days <= 7:
                    timeframe = "last_7_days"
                elif days <= 30:
                    timeframe = "last_30_days"
                elif days <= 90:
                    timeframe = "last_90_days"
                else:
                    timeframe = "last_365_days"
                
                # Query campaign statistics with conversion_value
                campaign_stats_response = await self.campaign_stats.get_statistics(
                    campaign_ids=campaign_ids,
                    statistics=["conversion_value", "conversions"],
                    timeframe=timeframe,
                    conversion_metric_id=conversion_metric_id
                )
                
                # Extract revenue from response
                if campaign_stats_response and "data" in campaign_stats_response:
                    results = campaign_stats_response["data"].get("attributes", {}).get("results", [])
                    for result in results:
                        stats = result.get("statistics", {})
                        revenue = stats.get("conversion_value", 0)
                        campaign_sum += float(revenue) if revenue else 0
                
                logger.info(f"✅ Campaign Revenue: ${campaign_sum:,.2f}")
            else:
                logger.warning("No campaigns found in date range")
        except Exception as e:
            logger.error(f"Error querying campaign revenue: {e}", exc_info=True)
        
        # ===== 4. CALCULATE METRICS =====
        attributed_revenue = flow_sum + campaign_sum
        kav_percentage = (attributed_revenue / total_sum * 100) if total_sum > 0 else 0
        flow_percentage = (flow_sum / attributed_revenue * 100) if attributed_revenue > 0 else 0
        campaign_percentage = (campaign_sum / attributed_revenue * 100) if attributed_revenue > 0 else 0
        
        logger.info(f"📊 Summary:")
        logger.info(f"   Total Revenue: ${total_sum:,.2f}")
        logger.info(f"   Attributed Revenue: ${attributed_revenue:,.2f} ({kav_percentage:.1f}% KAV)")
        logger.info(f"   Flow: ${flow_sum:,.2f} ({flow_percentage:.1f}% of attributed)")
        logger.info(f"   Campaign: ${campaign_sum:,.2f} ({campaign_percentage:.1f}% of attributed)")
        
        # ===== 5. GET RECIPIENT DATA =====
        logger.info("📧 Fetching recipient data for charts...")
        
        # Only fetch recipient data if we have a reasonable number of IDs to avoid rate limiting
        max_ids_for_recipients = 20  # Limit recipient queries to avoid rate limiting
        limited_flow_ids = flow_ids[:max_ids_for_recipients] if len(flow_ids) > max_ids_for_recipients else flow_ids
        limited_campaign_ids = campaign_ids[:max_ids_for_recipients] if len(campaign_ids) > max_ids_for_recipients else campaign_ids
        
        if len(flow_ids) > max_ids_for_recipients or len(campaign_ids) > max_ids_for_recipients:
            logger.info(f"Limiting recipient queries to {max_ids_for_recipients} flows and {max_ids_for_recipients} campaigns to avoid rate limiting")
        
        # Get total recipients from campaigns and flows for time series
        total_recipients_data = await self._get_recipients_time_series(
            flow_ids=limited_flow_ids,
            campaign_ids=limited_campaign_ids,
            days=days,
            interval=interval
        )
        
        # ===== 6. BUILD TIME SERIES =====
        # Use actual data from API instead of distributing evenly
        # If we have daily data, aggregate to monthly for chart
        # If we have monthly data, use it directly
        time_series = []
        
        if interval == "month" and dates and monthly_revenue_values:
            # Monthly data - use actual values from API
            # Calculate monthly ratios for flow/campaign (applied proportionally)
            flow_ratio = flow_sum / total_sum if total_sum > 0 else 0
            campaign_ratio = campaign_sum / total_sum if total_sum > 0 else 0
            
            for i, date in enumerate(dates):
                month_revenue = monthly_revenue_values[i] if i < len(monthly_revenue_values) else 0
                month_orders = monthly_order_values[i] if i < len(monthly_order_values) else 0
                
                time_series.append({
                    "date": date,
                    "total_revenue": month_revenue,
                    "flow_revenue": month_revenue * flow_ratio,
                    "campaign_revenue": month_revenue * campaign_ratio,
                    "attributed_revenue": month_revenue * (flow_ratio + campaign_ratio),
                    "unattributed_revenue": month_revenue * (1 - (flow_ratio + campaign_ratio)),
                    "orders": int(month_orders)
                })
        elif interval == "month" and dates:
            # Fallback: distribute evenly if monthly values not available
            monthly_avg_revenue = total_sum / len(dates) if len(dates) > 0 else 0
            monthly_avg_orders = total_orders / len(dates) if len(dates) > 0 else 0
            flow_ratio = flow_sum / total_sum if total_sum > 0 else 0
            campaign_ratio = campaign_sum / total_sum if total_sum > 0 else 0
            
            for date in dates:
                time_series.append({
                    "date": date,
                    "total_revenue": monthly_avg_revenue,
                    "flow_revenue": monthly_avg_revenue * flow_ratio,
                    "campaign_revenue": monthly_avg_revenue * campaign_ratio,
                    "attributed_revenue": monthly_avg_revenue * (flow_ratio + campaign_ratio),
                    "unattributed_revenue": monthly_avg_revenue * (1 - (flow_ratio + campaign_ratio)),
                    "orders": int(monthly_avg_orders)
                })
        else:
            # Daily data - aggregate to monthly for chart
            # Group by month
            from collections import defaultdict
            monthly_data = defaultdict(lambda: {"total": 0, "orders": 0, "dates": []})
            
            for i, date in enumerate(dates):
                date_obj = datetime.fromisoformat(date.replace("Z", "+00:00"))
                month_key = date_obj.strftime("%Y-%m")
                monthly_data[month_key]["dates"].append(date)
            
            # Calculate monthly totals
            flow_ratio = flow_sum / total_sum if total_sum > 0 else 0
            campaign_ratio = campaign_sum / total_sum if total_sum > 0 else 0
            
            for month_key in sorted(monthly_data.keys()):
                month_dates = monthly_data[month_key]["dates"]
                days_in_month = len(month_dates)
                monthly_revenue = (total_sum / len(dates)) * days_in_month if len(dates) > 0 else 0
                monthly_orders = (total_orders / len(dates)) * days_in_month if len(dates) > 0 else 0
                
                # Use first date of month for label
                first_date = month_dates[0]
                time_series.append({
                    "date": first_date,
                    "total_revenue": monthly_revenue,
                    "flow_revenue": monthly_revenue * flow_ratio,
                    "campaign_revenue": monthly_revenue * campaign_ratio,
                    "attributed_revenue": monthly_revenue * (flow_ratio + campaign_ratio),
                    "unattributed_revenue": monthly_revenue * (1 - (flow_ratio + campaign_ratio)),
                    "orders": int(monthly_orders)
                })
        
        # ===== 6. RETURN RESULTS =====
        start_dt = parse_iso_date(start_str)
        end_dt = parse_iso_date(end_str)
        
        return {
            "period": {
                "start_date": start_dt.strftime("%B %d, %Y"),
                "end_date": end_dt.strftime("%B %d, %Y"), 
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
                # Match sample audit format: monthly labels (Nov, Dec, Jan, Feb)
                "labels": [datetime.fromisoformat(ts["date"].replace("Z", "+00:00")).strftime("%b %Y") if isinstance(ts["date"], str) else ts["date"].strftime("%b %Y") for ts in time_series],
                "total_revenue": [ts["total_revenue"] for ts in time_series],
                "attributed_revenue": [ts.get("attributed_revenue", ts["flow_revenue"] + ts["campaign_revenue"]) for ts in time_series],
                "unattributed_revenue": [ts.get("unattributed_revenue", ts["total_revenue"] - (ts["flow_revenue"] + ts["campaign_revenue"])) for ts in time_series],
                "flow_revenue": [ts["flow_revenue"] for ts in time_series],
                "campaign_revenue": [ts["campaign_revenue"] for ts in time_series],
                # Recipients data from campaigns and flows
                "total_recipients": total_recipients_data
            }
        }
    
    async def _get_recipients_time_series(
        self, 
        flow_ids: List[str],
        campaign_ids: List[str], 
        days: int,
        interval: str
    ) -> List[int]:
        """
        Get recipient counts aggregated by time period for chart data.
        
        Since Klaviyo reporting API provides aggregated statistics rather than 
        time-series recipient data, we'll estimate recipient distribution
        based on the available data.
        """
        try:
            total_recipients_count = 0
            
            # Get total recipients from flows
            if flow_ids:
                # Map days to timeframe for flows API
                timeframe_map = {
                    7: "last_7_days",
                    30: "last_30_days", 
                    90: "last_90_days",
                    365: "last_365_days"
                }
                timeframe = timeframe_map.get(days, "last_90_days")
                if days > 365:
                    timeframe = "last_365_days"
                
                try:
                    flow_stats = await self.flow_stats.get_statistics(
                        flow_ids=flow_ids,
                        statistics=["recipients"],
                        timeframe=timeframe
                    )
                    
                    if flow_stats:
                        results = flow_stats.get("data", {}).get("attributes", {}).get("results", [])
                        for result in results:
                            stats = result.get("statistics", {})
                            total_recipients_count += stats.get("recipients", 0)
                        
                        logger.info(f"Flow recipients: {total_recipients_count}")
                        
                except Exception as e:
                    logger.warning(f"Failed to get flow recipients: {e}")
            
            # Get total recipients from campaigns
            if campaign_ids:
                # Map days to timeframe for campaigns API
                timeframe_map = {
                    7: "last_7_days",
                    30: "last_30_days",
                    90: "last_90_days", 
                    365: "last_365_days"
                }
                timeframe = timeframe_map.get(days, "last_90_days")
                if days > 365:
                    timeframe = "last_365_days"
                
                try:
                    campaign_stats = await self.campaign_stats.get_statistics(
                        campaign_ids=campaign_ids,
                        statistics=["recipients"],
                        timeframe=timeframe
                    )
                    
                    if campaign_stats:
                        results = campaign_stats.get("data", {}).get("attributes", {}).get("results", [])
                        for result in results:
                            stats = result.get("statistics", {})
                            total_recipients_count += stats.get("recipients", 0)
                        
                        logger.info(f"Campaign recipients: {stats.get('recipients', 0)}")
                        
                except Exception as e:
                    logger.warning(f"Failed to get campaign recipients: {e}")
            
            logger.info(f"Total recipients for charts: {total_recipients_count}")
            
            # Since we don't have time-series recipient data, we'll distribute 
            # the total recipients across time periods to provide chart data
            if interval == "month":
                # For monthly charts, distribute across months
                months_count = max(1, days // 30)
                avg_recipients_per_month = total_recipients_count // months_count if months_count > 0 else 0
                return [avg_recipients_per_month] * months_count
            else:
                # For other intervals, provide a single data point
                return [total_recipients_count] if total_recipients_count > 0 else [0]
        
        except Exception as e:
            logger.error(f"Failed to get recipients time series: {e}")
            # Return empty array as fallback
            return []
