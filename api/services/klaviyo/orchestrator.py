"""
Data extraction orchestrator.

Coordinates data extraction from all services and formats data for audit templates.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone

from .utils.date_helpers import ensure_z_suffix, parse_iso_date
from .utils.currency import format_currency
from .extraction import (
    RevenueExtractor,
    CampaignExtractor,
    FlowExtractor,
    ListExtractor,
    FormExtractor,
    KAVExtractor
)
from .formatters import (
    PeriodComparisonFormatter,
    CampaignFormatter,
    FlowFormatter
)

logger = logging.getLogger(__name__)


class DataExtractionOrchestrator:
    """Orchestrates data extraction from all Klaviyo services."""
    
    def __init__(
        self,
        metrics,
        metric_aggregates,
        campaigns,
        campaign_stats,
        flows,
        flow_stats,
        flow_patterns,
        lists,
        forms,
        revenue,
        account=None
    ):
        """
        Initialize orchestrator with all services.
        
        Args:
            metrics: MetricsService instance
            metric_aggregates: MetricAggregatesService instance
            campaigns: CampaignsService instance
            campaign_stats: CampaignStatisticsService instance
            flows: FlowsService instance
            flow_stats: FlowStatisticsService instance
            flow_patterns: FlowPatternMatcher instance
            lists: ListsService instance
            forms: FormsService instance
            revenue: RevenueTimeSeriesService instance
        """
        # Store services
        self.metrics = metrics
        self.metric_aggregates = metric_aggregates
        self.campaigns = campaigns
        self.campaign_stats = campaign_stats
        self.flows = flows
        self.flow_stats = flow_stats
        self.flow_patterns = flow_patterns
        self.lists = lists
        self.forms = forms
        self.revenue = revenue
        self.account = account
        
        # Initialize extractors
        self.revenue_extractor = RevenueExtractor(metrics, metric_aggregates)
        self.campaign_extractor = CampaignExtractor(campaigns, campaign_stats)
        self.flow_extractor = FlowExtractor(flows, flow_stats)
        self.list_extractor = ListExtractor(lists)
        self.form_extractor = FormExtractor(forms)
        self.kav_extractor = KAVExtractor(revenue)
        
        # Initialize formatters
        self.period_comparison = PeriodComparisonFormatter(revenue)
        self.campaign_formatter = CampaignFormatter()
        self.flow_formatter = FlowFormatter()
    
    async def extract_all_data(
        self,
        date_range: Optional[Dict[str, str]] = None,
        include_enhanced: bool = True,
        verbose: bool = True,
        fast_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Extract all data from Klaviyo for audit reports.
        
        This method coordinates extraction from all services and structures
        the data for use in audit report templates.
        
        Args:
            date_range: Optional custom date range
            include_enhanced: If True, includes enhanced data (list growth, forms, etc.)
            verbose: Whether to print progress messages
            
        Returns:
            Dict with all extracted Klaviyo data
        """
        if not date_range:
            # Use proper timezone-aware date calculation
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=365)
            date_range = {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        
        # Validate date_range - ensure end is not in the future
        # Initialize variables before try block to ensure they're available
        start_dt = None
        end_dt = None
        try:
            start_dt = parse_iso_date(date_range["start"])
            end_dt = parse_iso_date(date_range["end"])
            now_dt = datetime.now(timezone.utc)
            
            # Check if end date is in the future (more than 1 day ahead)
            if end_dt > now_dt + timedelta(days=1):
                logger.warning(f"⚠️  WARNING: End date is in the future! {end_dt.isoformat()} > {now_dt.isoformat()}")
                logger.warning(f"   Adjusting end date to current time: {now_dt.isoformat()}")
                end_dt = now_dt
                date_range["end"] = end_dt.isoformat()
            
            # Check if start date is after end date
            if start_dt >= end_dt:
                logger.error(f"❌ ERROR: Start date ({start_dt.isoformat()}) is after or equal to end date ({end_dt.isoformat()})")
                raise ValueError(f"Invalid date range: start must be before end")
            
            # Log date range validation
            days_span = (end_dt - start_dt).days
            logger.info(f"✅ Date range validated: {start_dt.date()} to {end_dt.date()} ({days_span} days)")
        except Exception as e:
            logger.error(f"❌ Error validating date_range: {e}", exc_info=True)
            raise
        
        # Ensure variables are defined (should be if we reach here)
        if start_dt is None or end_dt is None:
            raise ValueError("Failed to parse date range")
        
        start = ensure_z_suffix(date_range["start"])
        end = ensure_z_suffix(date_range["end"])
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"KLAVIYO DATA EXTRACTION")
            print(f"{'='*60}")
            print(f"Date range: {start} to {end}")
            print(f"Days: {(end_dt - start_dt).days}")
            print(f"Enhanced data: {'Yes' if include_enhanced else 'No'}")
            print(f"{'='*60}\n")
        
        # SECTION 1: Basic Revenue Data
        revenue_data = await self.revenue_extractor.extract(start, end, verbose)
        
        # SECTION 2: Campaign Data
        campaign_data = await self.campaign_extractor.extract(start, end, verbose)
        campaigns = campaign_data["campaigns"]
        campaign_statistics = campaign_data["campaign_statistics"]
        
        # SECTION 3: Flow Data
        flow_data_result = await self.flow_extractor.extract(verbose)
        flows = flow_data_result["flows"]
        flow_statistics = flow_data_result["flow_statistics"]
        flow_data = flow_data_result["flow_details"]
        
        # Initialize enhanced data containers
        enhanced_data = {}
        
        if include_enhanced:
            # Calculate days from date_range if provided
            days_for_analysis = 90  # Default
            if date_range:
                try:
                    # parse_iso_date is already imported at the top of the file
                    start_dt = parse_iso_date(date_range["start"])
                    end_dt = parse_iso_date(date_range["end"])
                    days_for_analysis = (end_dt - start_dt).days
                except Exception as e:
                    logger.warning(f"Could not calculate days from date_range: {e}")
            
            # SECTION 4: KAV Revenue Time Series
            kav_data = await self.kav_extractor.extract(
                days_for_analysis,
                account_timezone="Australia/Sydney",  # Will be overridden by account timezone in format_audit_data
                verbose=verbose,
                date_range=date_range  # Pass date_range for YTD support
            )
            enhanced_data["kav_analysis"] = kav_data
            
            # SECTION 5: List Growth Data (skip in fast mode - expensive)
            if not fast_mode:
                try:
                    list_growth = await self.list_extractor.extract(
                        days_for_analysis, 
                        date_range=date_range,  # Pass date_range to optimize API calls
                        verbose=verbose
                    )
                    enhanced_data["list_growth"] = list_growth
                except Exception as e:
                    logger.warning(f"⚠️  List growth extraction failed (continuing): {e}")
                    enhanced_data["list_growth"] = {"lists": [], "growth_data": []}
            else:
                if verbose:
                    print("  ⏭️  Skipping list growth (fast mode)")
                enhanced_data["list_growth"] = {"lists": [], "growth_data": []}
            
            # SECTION 6: Form Performance Data (skip in fast mode - expensive)
            if not fast_mode:
                try:
                    form_data = await self.form_extractor.extract(days_for_analysis, verbose, date_range=date_range)
                    enhanced_data["forms"] = form_data
                except Exception as e:
                    logger.warning(f"⚠️  Form performance extraction failed (continuing): {e}")
                    enhanced_data["forms"] = {"forms": []}
            else:
                if verbose:
                    print("  ⏭️  Skipping form performance (fast mode)")
                enhanced_data["forms"] = {"forms": []}
            
            # SECTION 7: Core Flows Deep Dive (skip in fast mode - very expensive)
            if not fast_mode:
                if verbose:
                    period_label = f"{days_for_analysis} Days" if days_for_analysis < 365 else f"{days_for_analysis // 30} Months" if days_for_analysis < 730 else "Year to Date"
                    print(f"\n🎯 SECTION 7: Core Flows Performance ({period_label})")
                    print("-" * 40)
                
                try:
                    core_flows = await self.flow_patterns.get_core_flows_performance(days=days_for_analysis)
                    enhanced_data["core_flows"] = core_flows
                except Exception as e:
                    logger.warning(f"⚠️  Core flows extraction failed (continuing): {e}")
                    enhanced_data["core_flows"] = {}
            else:
                if verbose:
                    print("  ⏭️  Skipping core flows deep dive (fast mode)")
                enhanced_data["core_flows"] = {}
                
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
                logger.error(f"Error fetching core flows data: {e}", exc_info=True)
                enhanced_data["core_flows"] = {}
        
        if verbose:
            print(f"\n{'='*60}")
            print("✓ DATA EXTRACTION COMPLETE!")
            print(f"{'='*60}")
        
        return {
            # Basic data
            "revenue": revenue_data,
            "campaigns": campaigns,
            "campaign_statistics": campaign_statistics,
            "flows": flows,
            "flow_statistics": flow_statistics,
            "flow_details": flow_data,
            "date_range": date_range,
            
            # Enhanced data
            **enhanced_data
        }
    
    async def format_audit_data(
        self,
        days: int = 90,
        verbose: bool = True,
        industry: Optional[str] = None,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Format extracted data for audit report templates.
        
        This method takes raw Klaviyo data and structures it for use
        in audit report templates. Works with any audit format/length.
        
        Args:
            days: Number of days for analysis period (default 90, ignored if date_range provided)
            verbose: Whether to print progress messages
            industry: Industry identifier for benchmark selection
            date_range: Optional custom date range (overrides days parameter)
            
        Returns:
            Dict structured for audit template consumption
        """
        # Use date_range if provided, otherwise calculate from days
        start_dt = None
        end_dt = None
        if date_range:
            # parse_iso_date is already imported at the top of the file
            start_dt = parse_iso_date(date_range["start"])
            end_dt = parse_iso_date(date_range["end"])
            start_date = start_dt
            end_date = end_dt
            days = (end_dt - start_dt).days
        else:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
        
        if verbose:
            print(f"\n{'='*60}")
            print("AUDIT DATA FORMATTING")
            print(f"{'='*60}\n")
            # Show period label
            if date_range and start_dt and end_dt:
                # Custom date range or YTD
                if days >= 365:
                    # Check if it's YTD (starts on Jan 1 of current year)
                    start_year = start_dt.year
                    current_year = datetime.now(timezone.utc).year
                    if start_dt.month == 1 and start_dt.day == 1 and start_year == current_year:
                        period_label = "Year to Date"
                    else:
                        period_label = f"Custom Range ({days} days)"
                elif days >= 180:
                    period_label = f"Custom Range ({days // 30} Months)"
                else:
                    period_label = f"Custom Range ({days} Days)"
            elif days >= 365:
                period_label = "1 Year"
            elif days >= 180:
                period_label = f"{days // 30} Months"
            else:
                period_label = f"{days} Days"
            print(f"Analysis Period: {period_label} ({days} days)\n")
            if date_range:
                print(f"Date Range: {date_range['start']} to {date_range['end']}\n")
        
        # Fetch account currency and timezone
        account_currency = "USD"  # Default fallback
        account_timezone = "UTC"  # Default fallback
        if self.account:
            try:
                account_context = await self.account.get_account_context()
                account_currency = account_context.get("currency", "USD")
                account_timezone = account_context.get("timezone", "UTC")
                if verbose:
                    logger.info(f"Account currency: {account_currency}, timezone: {account_timezone}")
            except Exception as e:
                logger.warning(f"Could not fetch account info: {e}, using defaults")
        
        # Extract all data with enhanced mode
        # Ensure dates are formatted with Z suffix for Klaviyo API
        from .utils.date_helpers import ensure_z_suffix
        date_range_for_extraction = {
            "start": ensure_z_suffix(start_date.isoformat()),
            "end": ensure_z_suffix(end_date.isoformat())
        }
        raw_data = await self.extract_all_data(
            date_range=date_range_for_extraction,
            include_enhanced=True,
            verbose=verbose
        )
        
        # Structure data for template consumption
        kav_raw = raw_data.get("kav_analysis", {})
        list_raw = raw_data.get("list_growth", {})
        forms_raw = raw_data.get("forms", {})
        core_flows = raw_data.get("core_flows", {})
        
        # Get campaign data for channel breakdown calculation
        campaigns = raw_data.get("campaigns", [])
        campaign_statistics = raw_data.get("campaign_statistics", {})
        email_campaigns = raw_data.get("email_campaigns", [])
        sms_campaigns = raw_data.get("sms_campaigns", [])
        push_campaigns = raw_data.get("push_campaigns", [])
        
        totals = kav_raw.get("totals", {})
        period = kav_raw.get("period", {})
        
        # Calculate channel breakdown from campaign statistics
        # Aggregate revenue by channel from campaign statistics
        channel_revenue = {"email": 0, "sms": 0, "push": 0}
        if campaign_statistics and "data" in campaign_statistics:
            results = campaign_statistics["data"].get("attributes", {}).get("results", [])
            # Create a map of campaign ID to channel
            # Since we fetch campaigns separately by channel, we can map them
            campaign_channel_map = {}
            # Map email campaigns
            for campaign in email_campaigns:
                campaign_id = campaign.get("id")
                campaign_channel_map[campaign_id] = "email"
            # Map SMS campaigns
            for campaign in sms_campaigns:
                campaign_id = campaign.get("id")
                campaign_channel_map[campaign_id] = "sms"
            # Map push campaigns
            for campaign in push_campaigns:
                campaign_id = campaign.get("id")
                campaign_channel_map[campaign_id] = "push"
            
            # Aggregate revenue by channel
            for result in results:
                campaign_id = result.get("id")
                stats = result.get("statistics", {})
                revenue = stats.get("conversion_value", 0) or 0
                channel = campaign_channel_map.get(campaign_id, "email")  # Default to email if not found
                channel_revenue[channel] = channel_revenue.get(channel, 0) + float(revenue)
        
        # Calculate previous period comparison (period-over-period)
        # Strategist always compares with previous period
        comparison_result = await self.period_comparison.calculate_comparison(
            totals,
            period,
            days,
            account_timezone,
            verbose
        )
        vs_previous_period = comparison_result["vs_previous_period"]
        attributed_vs_previous = comparison_result["attributed_vs_previous"]
        previous_period_data = comparison_result["previous_period_data"]
        
        return {
            # Cover page data
            "cover_data": {
                "client_name": "Client Name",  # To be filled
                "client_code": "",
                "audit_date": datetime.now().strftime("%d %b %Y"),
                "auditor_name": "Audit System"
            },
            
            # Account context (for LLM and formatting)
            "account_context": {
                "currency": account_currency,
                "timezone": account_timezone,
                "industry": industry or "apparel_accessories"  # Add industry to context
            },
            
            # Store days for period labels
            "period_days": days,
            
            # Store industry for benchmark selection
            "industry": industry or "apparel_accessories",
            
            # KAV Analysis - preserve full structure including totals for LLM
            "kav_data": {
                "period": period,
                "revenue": {
                    "total_website": totals.get("total_revenue", 0),
                    "total_website_formatted": format_currency(totals.get("total_revenue", 0), account_currency),
                    "vs_previous_period": round(vs_previous_period, 1),  # Period-over-period change
                    "attributed": totals.get("attributed_revenue", 0),
                    "attributed_percentage": totals.get("kav_percentage", 0),
                    "attributed_vs_previous": round(attributed_vs_previous, 1),  # Period-over-period change
                    "flow_attributed": totals.get("flow_revenue", 0),
                    "campaign_attributed": totals.get("campaign_revenue", 0),
                    "flow_percentage": totals.get("flow_percentage", 0),  # Include percentages
                    "campaign_percentage": totals.get("campaign_percentage", 0)  # Include percentages
                },
                "previous_period": previous_period_data,  # Include previous period data for context
                "totals": totals,  # Preserve totals for LLM formatter
                "chart_data": kav_raw.get("chart_data", {}),
                "narrative": f"During the {days}-day analysis period, your Klaviyo-attributed revenue represents {totals.get('kav_percentage', 0):.1f}% of total website revenue.",
                # Include channel breakdown data for KAV preparer
                "channel_revenue": channel_revenue,
                "email_campaigns": email_campaigns,
                "sms_campaigns": sms_campaigns,
                "push_campaigns": push_campaigns
            },
            
            # List Growth
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
                "net_change_chart_data": list_raw.get("net_change_chart_data", {}),
                "analysis_text": ""
            },
            
            # Data Capture
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
            
            # Automation Overview
            "automation_overview_data": {
                "period_days": days,
                "flows": [
                    {
                        "name": flow_info.get("name", flow_type),
                        "avg_open_rate": flow_info.get("performance", {}).get("open_rate", 0),
                        "avg_click_rate": flow_info.get("performance", {}).get("click_rate", 0),
                        "avg_placed_order_rate": flow_info.get("performance", {}).get("conversion_rate", 0),
                        "revenue": flow_info.get("performance", {}).get("revenue", 0),
                        "revenue_per_recipient": flow_info.get("performance", {}).get("revenue_per_recipient", 0),
                        "recipients": flow_info.get("performance", {}).get("recipients", 0)  # Include recipients
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
                    "total_recipients": sum(
                        f.get("performance", {}).get("recipients", 0)
                        for f in core_flows.values()
                    ),
                    "recipients_vs_previous": 0
                },
                "chart_data": {
                    "labels": [f.get("name", "Flow") for f in [
                        {
                            "name": flow_info.get("name", flow_type),
                            "revenue": flow_info.get("performance", {}).get("revenue", 0),
                            "recipients": flow_info.get("performance", {}).get("recipients", 0)
                        }
                        for flow_type, flow_info in core_flows.items()
                        if flow_info.get("found")
                    ]],
                    "values": [
                        f.get("performance", {}).get("revenue", 0)
                        for f in core_flows.values()
                        if f.get("found")
                    ]
                } if core_flows else {}
            },
            
            # Welcome Flow
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
            
            # Abandoned Cart - only include flows that were found
            "abandoned_cart_data": self.flow_formatter.prepare_abandoned_cart_data(core_flows),
            
            # Campaign Performance
            "campaign_performance_data": self.campaign_formatter.calculate_summary(
                raw_data.get("campaign_statistics", {}),
                totals.get("campaign_revenue", 0),
                raw_data.get("campaigns", [])
            ),
            
            # Segmentation Strategy
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
            
            # Browse Abandonment Data - only include if flow exists and has data
            "browse_abandonment_data": self.flow_formatter.prepare_browse_abandonment_data(core_flows),
            
            # Post Purchase Data
            "post_purchase_data": {
                "flows": [
                    {
                        "name": "Post Purchase",
                        "open_rate": core_flows.get("post_purchase", {}).get("performance", {}).get("open_rate", 0),
                        "click_rate": core_flows.get("post_purchase", {}).get("performance", {}).get("click_rate", 0),
                        "placed_order_rate": core_flows.get("post_purchase", {}).get("performance", {}).get("conversion_rate", 0),
                        "revenue_per_recipient": core_flows.get("post_purchase", {}).get("performance", {}).get("revenue_per_recipient", 0),
                        "revenue": core_flows.get("post_purchase", {}).get("performance", {}).get("revenue", 0)
                    }
                ],
                "benchmark": {
                    "name": "Post Purchase",
                    "open_rate": 65.30,
                    "click_rate": 8.90,
                    "conversion_rate": 4.20,
                    "revenue_per_recipient": 5.75
                },
                "industry": "Apparel and Accessories",
                "recommendations": []
            },
            
            # Reviews Data (placeholder for advanced features)
            "reviews_data": {
                "enabled": False,
                "integration": "None",
                "review_flows": [],
                "recommendations": ["Consider implementing review collection flows"]
            },
            
            # Wishlist Data (placeholder for advanced features)
            "wishlist_data": {
                "enabled": False,
                "integration": "None", 
                "wishlist_flows": [],
                "recommendations": ["Consider implementing wishlist abandonment flows"]
            },
            
            # Add top-level cover data for template compatibility
            "client_name": "Client Name",  # Will be overridden by report service
            "audit_date": datetime.now().strftime("%d %b %Y"),
            "auditor_name": "Andzen Team",
            
            # Raw data for further processing
            "_raw": raw_data
        }

