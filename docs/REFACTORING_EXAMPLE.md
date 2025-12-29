# Refactoring Example: Metrics Module

This document shows how the metrics functionality would be refactored into a modular structure.

## Before (Current Structure)

```python
# In klaviyo.py - 1,795 lines
class KlaviyoService:
    async def get_metrics(self) -> List[Dict[str, Any]]:
        try:
            response = await self._make_request("GET", "/metrics/")
            return response.get("data", [])
        except HTTPStatusError as e:
            print(f"Error fetching metrics: {e}")
            return []
    
    async def get_metric_by_name(self, metric_name: str) -> Optional[Dict[str, Any]]:
        metrics = await self.get_metrics()
        for metric in metrics:
            if metric.get("attributes", {}).get("name") == metric_name:
                return metric
        print(f"Metric '{metric_name}' not found in {len(metrics)} available metrics")
        return None
    
    async def query_metric_aggregates(self, ...):
        # 68 lines of code with nested parsing logic
        ...
```

## After (Modular Structure)

### `api/services/klaviyo/client.py`
```python
"""Base HTTP client for Klaviyo API."""
import httpx
import asyncio
from typing import Dict, Optional, Any
from httpx import HTTPStatusError
import logging

from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class KlaviyoClient:
    """Base HTTP client with rate limiting and retry logic."""
    
    BASE_URL = "https://a.klaviyo.com/api"
    
    def __init__(self, api_key: str, rate_limit_tier: str = "medium"):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Klaviyo-API-Key {api_key}",
            "revision": "2025-10-15",
            "accept": "application/vnd.api+json",
            "Content-Type": "application/json"
        }
        
        rate_limits = {
            "small": (3.0, 60),
            "medium": (8.0, 120),
            "large": (50.0, 600),
            "xl": (200.0, 3000)
        }
        
        rps, rpm = rate_limits.get(rate_limit_tier.lower(), rate_limits["medium"])
        self.rate_limiter = RateLimiter(requests_per_second=rps, requests_per_minute=rpm)
    
    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        retry_on_429: bool = True,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Make HTTP request with rate limiting and retry logic."""
        url = f"{self.BASE_URL}{endpoint}"
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
                    
                    if response.status_code == 429 and retry_on_429 and attempt < max_retries:
                        retry_after = self._extract_retry_after(response)
                        if not retry_after:
                            retry_after = 2 ** attempt
                        retry_after = min(retry_after + 1, 60)
                        
                        logger.warning(f"Rate limited. Waiting {retry_after}s before retry {attempt + 1}/{max_retries}")
                        await asyncio.sleep(retry_after)
                        await self.rate_limiter.acquire()
                        continue
                    
                    response.raise_for_status()
                    return response.json()
                    
            except HTTPStatusError as e:
                if e.response.status_code == 429 and retry_on_429 and attempt < max_retries:
                    continue
                raise
        
        raise HTTPStatusError("Rate limit exceeded after all retries", request=None, response=None)
    
    def _extract_retry_after(self, response) -> Optional[int]:
        """Extract retry-after from 429 response."""
        try:
            error_data = response.json()
            error_detail = error_data.get("errors", [{}])[0]
            retry_after = error_detail.get("meta", {}).get("retry_after")
            if not retry_after:
                detail = error_detail.get("detail", "")
                if "Expected available in" in detail:
                    import re
                    match = re.search(r'(\d+) seconds?', detail)
                    if match:
                        return int(match.group(1))
        except:
            pass
        return None
```

### `api/services/klaviyo/parsers.py`
```python
"""Response parsing utilities."""
from typing import Any, Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def parse_metric_value(value: Any) -> float:
    """
    Parse a metric value from various response formats.
    
    Handles:
    - List format: [value, count, unique]
    - Dict format: {"sum_value": X, "count": Y}
    - Scalar format: direct number
    """
    if value is None:
        return 0.0
    
    if isinstance(value, list):
        if len(value) > 0 and value[0] is not None:
            try:
                return float(value[0])
            except (ValueError, TypeError):
                return 0.0
        return 0.0
    
    if isinstance(value, dict):
        # Try common keys
        for key in ["sum_value", "count", "value"]:
            if key in value and value[key] is not None:
                try:
                    return float(value[key])
                except (ValueError, TypeError):
                    continue
        return 0.0
    
    # Scalar value
    try:
        if value and str(value).strip():
            return float(value)
    except (ValueError, TypeError):
        pass
    
    return 0.0


def parse_aggregate_data(response: Dict[str, Any]) -> Tuple[List[str], List[Any]]:
    """
    Parse metric aggregate response.
    
    Returns:
        Tuple of (dates, values)
    """
    attrs = response.get("data", {}).get("attributes", {})
    dates = attrs.get("dates", [])
    values = attrs.get("data", [])
    return dates, values


def extract_statistics(response: Dict[str, Any]) -> Dict[str, Any]:
    """Extract statistics from reporting API response."""
    results = response.get("data", {}).get("attributes", {}).get("results", [])
    if not results:
        return {}
    
    result = results[0]
    stats = result.get("statistics", {})
    
    # Convert rates from decimal to percentage
    return {
        "recipients": stats.get("recipients", 0),
        "opens": stats.get("opens", 0),
        "open_rate": stats.get("open_rate", 0) * 100,
        "clicks": stats.get("clicks", 0),
        "click_rate": stats.get("click_rate", 0) * 100,
        "conversions": stats.get("conversions", 0),
        "conversion_rate": stats.get("conversion_rate", 0) * 100,
        "revenue": stats.get("conversion_value", 0),
    }
```

### `api/services/klaviyo/metrics/service.py`
```python
"""Metrics service for fetching and querying Klaviyo metrics."""
from typing import Dict, List, Optional, Any
import logging

from ..client import KlaviyoClient
from ..parsers import parse_metric_value, parse_aggregate_data

logger = logging.getLogger(__name__)


class MetricsService:
    """Service for interacting with Klaviyo metrics."""
    
    def __init__(self, client: KlaviyoClient):
        self.client = client
    
    async def get_metrics(self) -> List[Dict[str, Any]]:
        """Get all metrics from Klaviyo account."""
        try:
            response = await self.client.request("GET", "/metrics/")
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Error fetching metrics: {e}", exc_info=True)
            return []
    
    async def get_metric_by_name(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """Get a metric by its name."""
        metrics = await self.get_metrics()
        for metric in metrics:
            if metric.get("attributes", {}).get("name") == metric_name:
                return metric
        logger.warning(f"Metric '{metric_name}' not found in {len(metrics)} available metrics")
        return None
    
    async def get_metric_by_id(self, metric_id: str) -> Optional[Dict[str, Any]]:
        """Get a metric by its ID."""
        try:
            response = await self.client.request("GET", f"/metrics/{metric_id}/")
            return response.get("data")
        except Exception as e:
            logger.error(f"Error fetching metric {metric_id}: {e}", exc_info=True)
            return None
```

### `api/services/klaviyo/metrics/aggregates.py`
```python
"""Metric aggregates query service."""
from typing import Dict, List, Optional, Any
import logging

from ..client import KlaviyoClient
from ..filters import build_metric_filter
from ..parsers import parse_aggregate_data, parse_metric_value

logger = logging.getLogger(__name__)


class MetricAggregatesService:
    """Service for querying metric aggregates."""
    
    def __init__(self, client: KlaviyoClient):
        self.client = client
    
    async def query(
        self,
        metric_id: str,
        start_date: str,
        end_date: str,
        measurements: Optional[List[str]] = None,
        interval: str = "day",
        by: Optional[List[str]] = None,
        filter_conditions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Query metric aggregates using POST /metric-aggregates/.
        
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
        
        # Build filter array
        filters = build_metric_filter(start_date, end_date, filter_conditions)
        
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
        
        if by:
            payload["data"]["attributes"]["by"] = by
        
        try:
            response = await self.client.request("POST", "/metric-aggregates/", data=payload)
            return response
        except Exception as e:
            logger.error(f"Error querying metric aggregates for {metric_id}: {e}", exc_info=True)
            return {}
    
    def parse_response(self, response: Dict[str, Any]) -> Dict[str, List]:
        """
        Parse metric aggregates response into structured format.
        
        Returns:
            Dict with 'dates' and 'values' lists
        """
        dates, values = parse_aggregate_data(response)
        
        # Parse values based on structure
        parsed_values = []
        for val in values:
            parsed_values.append(parse_metric_value(val))
        
        return {
            "dates": dates,
            "values": parsed_values
        }
```

### `api/services/klaviyo/__init__.py` (Facade)
```python
"""Klaviyo API client - modular structure with backward compatibility."""
from typing import Dict, List, Optional, Any

from .client import KlaviyoClient
from .metrics.service import MetricsService
from .metrics.aggregates import MetricAggregatesService
from .campaigns.service import CampaignsService
from .campaigns.statistics import CampaignStatisticsService
# ... other imports

# For backward compatibility
class KlaviyoService:
    """
    Main Klaviyo service - facade that composes all sub-services.
    
    Maintains backward compatibility with existing API.
    """
    
    def __init__(self, api_key: str, rate_limit_tier: str = "medium"):
        self._client = KlaviyoClient(api_key, rate_limit_tier)
        
        # Initialize all services
        self.metrics = MetricsService(self._client)
        self.metric_aggregates = MetricAggregatesService(self._client)
        self.campaigns = CampaignsService(self._client)
        self.campaign_stats = CampaignStatisticsService(self._client)
        # ... other services
    
    # Backward compatibility methods
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
        measurements: Optional[List[str]] = None,
        interval: str = "day",
        by: Optional[List[str]] = None,
        filter_conditions: Optional[List[str]] = None
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
    
    # ... other backward compatible methods
```

## Benefits of This Structure

1. **Separation of Concerns**: Each module has a single, clear responsibility
2. **Reusability**: `MetricsService` can be used independently
3. **Testability**: Each service can be mocked and tested separately
4. **Maintainability**: Changes to metrics don't affect campaigns or flows
5. **Extensibility**: Easy to add new metric-related features
6. **Backward Compatibility**: Existing code continues to work

## Usage Examples

### Old Way (Still Works)
```python
from api.services.klaviyo import KlaviyoService

service = KlaviyoService(api_key="...")
metrics = await service.get_metrics()
```

### New Way (More Flexible)
```python
from api.services.klaviyo import KlaviyoClient
from api.services.klaviyo.metrics import MetricsService

client = KlaviyoClient(api_key="...")
metrics_service = MetricsService(client)
metrics = await metrics_service.get_metrics()
```

### Direct Service Access (Also Available)
```python
from api.services.klaviyo import KlaviyoService

service = KlaviyoService(api_key="...")
# Access sub-services directly
metrics = await service.metrics.get_metrics()
campaigns = await service.campaigns.get_campaigns()
```

