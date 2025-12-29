"""
Klaviyo API client service - Modular structure with backward compatibility.

This module provides a backward-compatible facade that uses the new modular
structure internally. Existing code continues to work without changes.

New code can import specific services directly:
    from api.services.klaviyo.metrics import MetricsService
    from api.services.klaviyo.client import KlaviyoClient
"""
import logging
from typing import Dict, List, Optional, Any

from .client import KlaviyoClient
from .rate_limiter import RateLimiter
from .metrics.service import MetricsService
from .metrics.aggregates import MetricAggregatesService
from .campaigns.service import CampaignsService
from .campaigns.statistics import CampaignStatisticsService
from .flows.service import FlowsService
from .flows.statistics import FlowStatisticsService
from .flows.patterns import FlowPatternMatcher
from .lists.service import ListsService
from .forms.service import FormsService
from .revenue.time_series import RevenueTimeSeriesService

# Import for backward compatibility - will be populated as we extract more services
logger = logging.getLogger(__name__)


class KlaviyoService:
    """
    Main Klaviyo service - facade that composes all sub-services.
    
    Maintains backward compatibility with existing API while using
    new modular structure internally.
    
    Usage:
        # Old way (still works)
        service = KlaviyoService(api_key="...")
        metrics = await service.get_metrics()
        
        # New way (more flexible)
        service = KlaviyoService(api_key="...")
        metrics = await service.metrics.get_metrics()
    """
    
    BASE_URL = "https://a.klaviyo.com/api"
    
    def __init__(self, api_key: str, rate_limit_tier: str = "medium"):
        """
        Initialize Klaviyo service.
        
        Args:
            api_key: Klaviyo API key
            rate_limit_tier: Rate limit tier - "small", "medium", "large", "xl"
        """
        self.api_key = api_key
        self._client = KlaviyoClient(api_key, rate_limit_tier)
        
        # Initialize all services
        from .account.service import AccountService
        self.account = AccountService(self._client)
        self.metrics = MetricsService(self._client)
        self.metric_aggregates = MetricAggregatesService(self._client)
        self.campaigns = CampaignsService(self._client)
        self.campaign_stats = CampaignStatisticsService(self._client)
        self.flows = FlowsService(self._client)
        self.flow_stats = FlowStatisticsService(self._client)
        self.flow_patterns = FlowPatternMatcher(self.flows, self.flow_stats)
        self.lists = ListsService(self._client)
        self.forms = FormsService(self._client)
        self.revenue = RevenueTimeSeriesService(self._client)
        
        # Initialize orchestrator for data extraction/formatting
        from .orchestrator import DataExtractionOrchestrator
        self._orchestrator = DataExtractionOrchestrator(
            metrics=self.metrics,
            metric_aggregates=self.metric_aggregates,
            campaigns=self.campaigns,
            campaign_stats=self.campaign_stats,
            flows=self.flows,
            flow_stats=self.flow_stats,
            flow_patterns=self.flow_patterns,
            lists=self.lists,
            forms=self.forms,
            revenue=self.revenue,
            account=self.account
        )
        
        # Store for backward compatibility
        self.rate_limiter = self._client.rate_limiter
        self.headers = self._client.headers
    
    # ============================================================
    # Backward Compatibility Methods
    # ============================================================
    
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
        Make HTTP request (backward compatible wrapper).
        
        Delegates to KlaviyoClient.request()
        """
        return await self._client.request(
            method=method,
            endpoint=endpoint,
            params=params,
            data=data,
            retry_on_429=retry_on_429,
            max_retries=max_retries
        )
    
    async def test_connection(self) -> bool:
        """Test API connection (backward compatible)."""
        return await self._client.test_connection()
    
    async def get_metrics(self) -> List[Dict[str, Any]]:
        """Get all metrics (backward compatible)."""
        return await self.metrics.get_metrics()
    
    async def get_metric_by_name(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """Get metric by name (backward compatible)."""
        return await self.metrics.get_metric_by_name(metric_name)
    
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
        """Query metric aggregates (backward compatible)."""
        return await self.metric_aggregates.query(
            metric_id=metric_id,
            start_date=start_date,
            end_date=end_date,
            measurements=measurements,
            interval=interval,
            by=by,
            filter_conditions=filter_conditions
        )
    
    # ============================================================
    # Placeholder methods for services not yet extracted
    # These will be replaced as we extract more services
    # ============================================================
    
    # Campaign methods - will be extracted to campaigns/ module
    async def get_campaigns(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        channel: str = "email"
    ) -> List[Dict[str, Any]]:
        """Get campaigns (backward compatible)."""
        return await self.campaigns.get_campaigns(start_date, end_date, channel)
    
    # Flow methods - fully extracted
    async def get_flows(self) -> List[Dict[str, Any]]:
        """Get all flows (backward compatible)."""
        return await self.flows.get_flows()
    
    async def get_flow_actions(self, flow_id: str) -> List[Dict[str, Any]]:
        """Get flow actions (backward compatible)."""
        return await self.flows.get_flow_actions(flow_id)
    
    async def get_flow_action_messages(self, action_id: str) -> List[Dict[str, Any]]:
        """Get flow action messages (backward compatible)."""
        return await self.flows.get_flow_action_messages(action_id)
    
    # List methods - fully extracted
    async def get_lists(self) -> List[Dict[str, Any]]:
        """Get all lists (backward compatible)."""
        return await self.lists.get_lists()
    
    async def get_list_profiles_count(self, list_id: str) -> int:
        """Get list profiles count (backward compatible)."""
        return await self.lists.get_list_profiles_count(list_id)
    
    async def get_list_growth_data(
        self,
        list_id: Optional[str] = None,
        months: int = 6
    ) -> Dict[str, Any]:
        """Get list growth data (backward compatible)."""
        return await self.lists.get_list_growth_data(list_id, months)
    
    # Form methods - fully extracted
    async def get_forms(self) -> List[Dict[str, Any]]:
        """Get all forms (backward compatible)."""
        return await self.forms.get_forms()
    
    async def get_form_performance(self, days: int = 90) -> Dict[str, Any]:
        """Get form performance (backward compatible)."""
        return await self.forms.get_form_performance(days)
    
    # Revenue methods - fully extracted
    async def get_revenue_time_series(
        self,
        days: int = 90,
        interval: str = "day"
    ) -> Dict[str, Any]:
        """Get revenue time series (backward compatible)."""
        return await self.revenue.get_revenue_time_series(days, interval)
    
    # Flow statistics - fully extracted
    async def get_flow_statistics(
        self,
        flow_ids: List[str],
        statistics: List[str] = None,
        timeframe: str = "last_30_days",
        conversion_metric_id: Optional[str] = None,
        retry_count: int = 3  # Note: This parameter is unused, kept for backward compatibility
    ) -> Dict[str, Any]:
        """Get flow statistics (backward compatible)."""
        return await self.flow_stats.get_statistics(
            flow_ids, statistics, timeframe, conversion_metric_id
        )
    
    async def get_individual_flow_stats(
        self,
        flow_id: str,
        days: int = 90
    ) -> Dict[str, Any]:
        """Get individual flow stats (backward compatible)."""
        return await self.flow_stats.get_individual_stats(flow_id, days)
    
    async def get_core_flows_performance(
        self,
        days: int = 90,
        limit_flows: int = 10
    ) -> Dict[str, Any]:
        """Get core flows performance (backward compatible)."""
        return await self.flow_patterns.get_core_flows_performance(days, limit_flows)
    
    # Campaign statistics - fully extracted
    async def get_campaign_statistics(
        self,
        campaign_ids: List[str],
        statistics: List[str] = None,
        timeframe: str = "last_30_days",
        conversion_metric_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get campaign statistics (backward compatible)."""
        return await self.campaign_stats.get_statistics(
            campaign_ids, statistics, timeframe, conversion_metric_id
        )
    
    # Data extraction methods - coordinate extraction from all services
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
        return await self._orchestrator.extract_all_data(
            date_range=date_range,
            include_enhanced=include_enhanced,
            verbose=verbose
        )
    
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
        return await self._orchestrator.format_audit_data(
            days=days, 
            verbose=verbose, 
            industry=industry,
            date_range=date_range
        )
    
    # Backward compatibility alias
    async def extract_audit_data(
        self,
        days: int = 90,
        verbose: bool = True,
        industry: Optional[str] = None
    ) -> Dict[str, Any]:
        """Backward compatibility alias for format_audit_data()."""
        return await self.format_audit_data(days, verbose, industry)


# Export for backward compatibility
__all__ = ["KlaviyoService", "KlaviyoClient", "RateLimiter", "MetricsService", "MetricAggregatesService"]

