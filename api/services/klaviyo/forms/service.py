"""Forms service for fetching Klaviyo form performance data."""
from typing import Dict, List, Any, Optional
import logging
import asyncio
from datetime import datetime, timedelta

from ..client import KlaviyoClient
from ..metrics.service import MetricsService
from ..metrics.aggregates import MetricAggregatesService
from ..parsers import parse_metric_value, parse_aggregate_data
from ..utils.currency import format_large_number

logger = logging.getLogger(__name__)


class FormsService:
    """Service for interacting with Klaviyo forms and performance data."""
    
    def __init__(self, client: KlaviyoClient):
        """
        Initialize forms service.
        
        Args:
            client: KlaviyoClient instance
        """
        self.client = client
        self.metrics = MetricsService(client)
        self.aggregates = MetricAggregatesService(client)
    
    async def get_forms(self) -> List[Dict[str, Any]]:
        """
        Get all forms in the account.
        
        Returns:
            List of form objects
        """
        try:
            response = await self.client.request("GET", "/forms/")
            forms = response.get("data", [])
            
            # Enhanced logging for debugging
            logger.info(f"📋 Forms API Response: Found {len(forms)} forms")
            if forms:
                for i, form in enumerate(forms[:3]):  # Log first 3 forms
                    form_attrs = form.get("attributes", {})
                    logger.info(f"   Form {i+1}: {form_attrs.get('name', 'Unnamed')} (ID: {form.get('id', 'No ID')})")
            else:
                logger.warning("⚠️ No forms found in Klaviyo account - this may indicate:")
                logger.warning("   1. Account has no data capture forms deployed")
                logger.warning("   2. API permissions don't include form access")
                logger.warning("   3. Forms exist but aren't accessible via API")
                
            return forms
            
        except Exception as e:
            logger.error(f"❌ Error fetching forms: {e}", exc_info=True)
            return []
    
    async def get_form_performance(self, days: int = 90, date_range: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Get form performance data.
        
        Args:
            days: Number of days to look back (used if date_range not provided)
            date_range: Optional explicit date range with 'start' and 'end' ISO strings
            
        Returns:
            Dict with form performance metrics
        """
        forms = await self.get_forms()
        
        if not forms:
            return {"forms": [], "error": "No forms found"}
        
        # Use date_range if provided, otherwise calculate from days
        if date_range:
            from ..utils.date_helpers import ensure_z_suffix
            start_str = ensure_z_suffix(date_range["start"])
            end_str = ensure_z_suffix(date_range["end"])
        else:
            # Use proper timezone handling
            from ..utils.date_helpers import get_klaviyo_compatible_range
            date_range_dict = get_klaviyo_compatible_range(days, "Australia/Sydney")
            start_str = date_range_dict["start"]
            end_str = date_range_dict["end"]
        
        # Get form submission metrics with enhanced discovery
        submitted_metric = await self._discover_form_submission_metric()
        viewed_metric = await self._discover_form_view_metric()
        
        logger.info(f"📊 Form Metrics Discovery:")
        logger.info(f"   Submitted Form Metric: {'✓ Found' if submitted_metric else '✗ Not Found'}")
        logger.info(f"   Viewed Form Metric: {'✓ Found' if viewed_metric else '✗ Not Found'}")
        
        if not submitted_metric and not viewed_metric:
            logger.warning("⚠️ No form metrics found - this may indicate:")
            logger.warning("   1. Account doesn't track form submissions/views")
            logger.warning("   2. Form tracking not enabled in Klaviyo")
            logger.warning("   3. Different metric naming convention used")
            
            # If forms exist but no metrics, provide basic form structure with zero data
            if forms:
                logger.info(f"📋 Providing basic form data structure for {len(forms)} forms with zero metrics")
                form_data = []
                for form in forms:
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
                    
                    form_data.append({
                        "id": form.get("id"),
                        "name": form_name,
                        "type": type_display,
                        "impressions": 0,
                        "impressions_fmt": "0",
                        "submitted": 0,
                        "submitted_fmt": "0",
                        "submit_rate": 0.0,
                        "standing": "No Data",
                        "note": "Form exists but metrics not tracked"
                    })
                
                return {
                    "period_days": days,
                    "forms": form_data,
                    "warning": "Forms found but metrics not available - check Klaviyo form tracking settings"
                }
            else:
                return {
                    "period_days": days,
                    "forms": [],
                    "error": "No forms found in account"
                }
        
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
            views = 0
            if viewed_metric:
                try:
                    views_data = await self.aggregates.query(
                        metric_id=viewed_metric.get("id"),
                        start_date=start_str,
                        end_date=end_str,
                        measurements=["count"],
                        interval="day",
                        filter_conditions=[f'equals(form_id,"{form_id}")'],
                        timezone="Australia/Sydney"
                    )
                    _, views_values = parse_aggregate_data(views_data)
                    
                    # Handle aggregated response format (same as revenue fix)
                    if len(views_values) == 1 and isinstance(views_values[0], dict):
                        # Aggregated response
                        measurements = views_values[0].get("measurements", {})
                        count_values = measurements.get("count", [])
                        views = sum(float(val) for val in count_values if val is not None)
                    else:
                        # Individual daily values (original logic)
                        for v in views_values:
                            views += parse_metric_value(v)
                            
                    logger.info(f"Form {form_name} (ID: {form_id}): Views={views} (filter: equals(form_id,\"{form_id}\"))")
                except Exception as e:
                    # Skip failed metrics - don't retry 400 errors
                    error_msg = str(e)
                    if "400" in error_msg or "Bad Request" in error_msg:
                        logger.warning(f"Skipping views metric for form {form_id} ({form_name}): {error_msg}")
                    else:
                        logger.error(f"Error getting views for form {form_id} ({form_name}): {e}", exc_info=True)
                    logger.debug(f"View metric ID: {viewed_metric.get('id') if viewed_metric else 'N/A'}, Date range: {start_str} to {end_str}")
            
            # Get submissions for this form
            submissions = 0
            if submitted_metric:
                try:
                    submit_data = await self.aggregates.query(
                        metric_id=submitted_metric.get("id"),
                        start_date=start_str,
                        end_date=end_str,
                        measurements=["count"],
                        interval="day",
                        filter_conditions=[f'equals(form_id,"{form_id}")'],
                        timezone="Australia/Sydney"
                    )
                    _, submit_values = parse_aggregate_data(submit_data)
                    
                    # Handle aggregated response format (same as revenue fix)
                    if len(submit_values) == 1 and isinstance(submit_values[0], dict):
                        # Aggregated response
                        measurements = submit_values[0].get("measurements", {})
                        count_values = measurements.get("count", [])
                        submissions = sum(float(val) for val in count_values if val is not None)
                    else:
                        # Individual daily values (original logic)
                        for v in submit_values:
                            submissions += parse_metric_value(v)
                            
                    logger.info(f"Form {form_name} (ID: {form_id}): Submissions={submissions} (filter: equals(form_id,\"{form_id}\"))")
                except Exception as e:
                    # Skip failed metrics - don't retry 400 errors
                    error_msg = str(e)
                    if "400" in error_msg or "Bad Request" in error_msg:
                        logger.warning(f"Skipping submissions metric for form {form_id} ({form_name}): {error_msg}")
                    else:
                        logger.error(f"Error getting submissions for form {form_id} ({form_name}): {e}", exc_info=True)
                    logger.debug(f"Submit metric ID: {submitted_metric.get('id') if submitted_metric else 'N/A'}, Date range: {start_str} to {end_str}")
            
            # Calculate submit rate
            submit_rate = (submissions / views * 100) if views > 0 else 0
            
            # Determine standing based on form type and submit rate
            standing = self._calculate_standing(form_type, submit_rate)
            
            form_data.append({
                "id": form_id,
                "name": form_name,
                "type": type_display,
                "impressions": int(views),
                "impressions_fmt": format_large_number(views),
                "submitted": int(submissions),
                "submitted_fmt": format_large_number(submissions),
                "submit_rate": round(submit_rate, 2),
                "standing": standing
            })
            
            # Increased delay to avoid rate limiting
            await asyncio.sleep(0.5)
        
        return {
            "period_days": days,
            "forms": sorted(form_data, key=lambda x: x["impressions"], reverse=True)
        }
    
    @staticmethod
    def _calculate_standing(form_type: str, submit_rate: float) -> str:
        """
        Calculate form standing based on type and submit rate.
        
        Args:
            form_type: Type of form (popup, embed, etc.)
            submit_rate: Submit rate percentage
            
        Returns:
            Standing string (Excellent, Good, Average, Poor)
        """
        if form_type == "popup":
            if submit_rate >= 8:
                return "Excellent"
            elif submit_rate >= 3:
                return "Good"
            elif submit_rate >= 1:
                return "Average"
            else:
                return "Poor"
        else:  # embed, flyout, etc.
            if submit_rate >= 2:
                return "Excellent"
            elif submit_rate >= 0.5:
                return "Good"
            elif submit_rate >= 0.1:
                return "Average"
            else:
                return "Poor"
    
    async def _discover_form_submission_metric(self) -> Dict[str, Any]:
        """
        Discover form submission metrics with multiple fallback options.
        
        Returns:
            Form submission metric if found, None otherwise
        """
        submission_metric_names = [
            "Submitted Form",        # Standard Klaviyo
            "Submit Form",           # Alternative
            "Form Submission",       # Variation
            "Form Submit",           # Variation
            "Signup Form Submit",    # Common custom name
            "Newsletter Signup",     # Common custom name
            "Email Signup",          # Common custom name
            "Form Completed"         # Alternative name
        ]
        
        logger.debug("🔍 Searching for form submission metrics...")
        
        for metric_name in submission_metric_names:
            try:
                metric = await self.metrics.get_metric_by_name(metric_name)
                if metric:
                    logger.info(f"✅ Found submission metric: {metric_name} (ID: {metric.get('id')})")
                    return metric
                else:
                    logger.debug(f"   ❌ Not found: {metric_name}")
            except Exception as e:
                logger.debug(f"   ⚠️ Error checking {metric_name}: {e}")
        
        logger.warning("❌ No form submission metric found")
        return None
    
    async def _discover_form_view_metric(self) -> Dict[str, Any]:
        """
        Discover form view metrics with multiple fallback options.
        
        Returns:
            Form view metric if found, None otherwise  
        """
        view_metric_names = [
            "Viewed Form",           # Standard Klaviyo
            "View Form",             # Alternative
            "Form View",             # Variation
            "Form Impression",       # Alternative name
            "Form Display",          # Variation
            "Signup Form View",      # Common custom name
            "Newsletter Form View",  # Common custom name
            "Form Shown"             # Alternative name
        ]
        
        logger.debug("🔍 Searching for form view metrics...")
        
        for metric_name in view_metric_names:
            try:
                metric = await self.metrics.get_metric_by_name(metric_name)
                if metric:
                    logger.info(f"✅ Found view metric: {metric_name} (ID: {metric.get('id')})")
                    return metric
                else:
                    logger.debug(f"   ❌ Not found: {metric_name}")
            except Exception as e:
                logger.debug(f"   ⚠️ Error checking {metric_name}: {e}")
        
        logger.warning("❌ No form view metric found")
        return None

