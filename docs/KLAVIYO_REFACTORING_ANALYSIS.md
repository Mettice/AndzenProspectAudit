# Klaviyo Service Analysis & Modular Refactoring Proposal

## Executive Summary

The `klaviyo.py` file is **1,795 lines** with a single `KlaviyoService` class containing **30+ methods**. This violates Single Responsibility Principle and makes the code difficult to maintain, test, and extend.

## 🔍 Inconsistencies Found

### 1. **Unused Imports**
- Line 19: `Tuple` imported but never used
- Line 21: `os` imported but never used

### 2. **Unused Parameters**
- Line 1219: `retry_count` parameter in `get_flow_statistics()` is defined but never used

### 3. **Inconsistent Error Handling**
- Some methods return `{}` on error (e.g., `query_metric_aggregates`, `get_campaign_statistics`)
- Some methods return `[]` on error (e.g., `get_metrics`, `get_campaigns`, `get_flows`)
- Some methods use bare `except:` clauses (lines 201, 379, 409, 681, 706, 1289)
- Inconsistent error messages and logging

### 4. **Inconsistent Date Formatting**
- Mix of `strftime()` and `isoformat()`
- Some methods use `datetime.now()`, others use passed dates
- Inconsistent timezone handling (some use Z suffix, some don't)

### 5. **Code Duplication**
- **Nested response parsing** appears in multiple places:
  - Lines 554-570 (list growth)
  - Lines 674-680 (form views)
  - Lines 699-705 (form submissions)
  - Lines 836-867 (revenue time series)
  - Lines 877-898 (flow revenue)
- **Date filtering logic** duplicated in `get_campaigns()` (lines 368-381 and 398-407)
- **Metric fetching pattern** repeated (get_metric_by_name called multiple times)

### 6. **Inconsistent Return Types**
- Some methods return raw API responses
- Some return processed/transformed data
- Some return empty dicts, some return empty lists

### 7. **Hardcoded Business Logic**
- Line 917: Campaign revenue calculation uses hardcoded estimate `total_sum * 0.3 - flow_sum`
- Line 584: Churn rate calculation formula may need validation
- Form standing thresholds hardcoded (lines 713-730)

### 8. **Inconsistent Logging**
- Mix of `print()` statements (122 occurrences) instead of proper logging
- Some methods have `verbose` parameter, others don't
- Inconsistent message formatting

### 9. **Inconsistent Filter Building**
- Campaign filters use different syntax than flow filters
- Some filters built inline, some in helper functions

### 10. **Missing Type Hints**
- Some return types are `Dict[str, Any]` when more specific types would help
- Optional parameters not always properly typed

## 📦 Proposed Modular Structure

```
api/services/klaviyo/
├── __init__.py                 # Public API exports
├── client.py                   # Base HTTP client with rate limiting
├── rate_limiter.py            # RateLimiter class (extracted)
├── parsers.py                  # Response parsing utilities
├── filters.py                  # Filter building utilities
├── metrics/
│   ├── __init__.py
│   ├── service.py              # MetricsService
│   └── aggregates.py           # Metric aggregates queries
├── campaigns/
│   ├── __init__.py
│   ├── service.py              # CampaignsService
│   └── statistics.py           # Campaign statistics/reporting
├── flows/
│   ├── __init__.py
│   ├── service.py              # FlowsService
│   ├── statistics.py           # Flow statistics/reporting
│   └── patterns.py             # Flow pattern matching
├── lists/
│   ├── __init__.py
│   └── service.py              # ListsService (growth, subscribers)
├── forms/
│   ├── __init__.py
│   └── service.py              # FormsService (performance)
├── revenue/
│   ├── __init__.py
│   ├── service.py              # RevenueService (KAV analysis)
│   └── time_series.py          # Time series data
├── extraction/
│   ├── __init__.py
│   ├── orchestrator.py         # Data extraction orchestrator
│   └── morrison.py             # Morrison audit data formatter
└── utils/
    ├── __init__.py
    ├── date_helpers.py         # Date formatting utilities
    ├── currency.py             # Currency formatting
    └── validators.py            # Input validation
```

## 🏗️ Detailed Module Breakdown

### 1. **`client.py`** - Base HTTP Client
**Responsibilities:**
- HTTP request handling
- Rate limiting integration
- Retry logic with exponential backoff
- Error handling and response parsing
- Authentication headers

**Methods:**
- `_make_request()` (moved from KlaviyoService)
- `test_connection()`

### 2. **`rate_limiter.py`** - Rate Limiting
**Responsibilities:**
- Request rate limiting per second/minute
- Thread-safe async operations

**Classes:**
- `RateLimiter` (extracted as-is)

### 3. **`parsers.py`** - Response Parsing
**Responsibilities:**
- Parse nested API response structures
- Handle different data formats (list, dict, scalar)
- Extract values from metric aggregates

**Functions:**
- `parse_metric_value(value: Any) -> float`
- `parse_aggregate_data(response: Dict) -> Tuple[List, List]`
- `extract_statistics(response: Dict) -> Dict`

### 4. **`filters.py`** - Filter Building
**Responsibilities:**
- Build Klaviyo filter strings
- Support different filter syntaxes (regular API vs Reporting API)
- Combine multiple filters with `and()` operator

**Functions:**
- `build_campaign_filter(channel: str, start_date: Optional[str], end_date: Optional[str]) -> str`
- `build_reporting_filter(ids: List[str], id_type: str) -> str`
- `build_metric_filter(start_date: str, end_date: str, additional: List[str]) -> List[str]`

### 5. **`metrics/service.py`** - Metrics Service
**Responsibilities:**
- Fetch all metrics
- Get metric by name/ID
- Query metric aggregates

**Methods:**
- `get_metrics() -> List[Dict]`
- `get_metric_by_name(name: str) -> Optional[Dict]`
- `get_metric_by_id(metric_id: str) -> Optional[Dict]`

### 6. **`metrics/aggregates.py`** - Metric Aggregates
**Responsibilities:**
- Query metric aggregates endpoint
- Build aggregate payloads
- Handle different measurement types

**Methods:**
- `query_aggregates(metric_id, start_date, end_date, measurements, interval, by, filters)`

### 7. **`campaigns/service.py`** - Campaigns Service
**Responsibilities:**
- Fetch campaigns
- Filter campaigns by date/channel
- Get campaign details

**Methods:**
- `get_campaigns(start_date, end_date, channel) -> List[Dict]`
- `get_campaign(campaign_id: str) -> Dict`

### 8. **`campaigns/statistics.py`** - Campaign Statistics
**Responsibilities:**
- Get campaign statistics using Reporting API
- Format statistics responses

**Methods:**
- `get_statistics(campaign_ids, statistics, timeframe, conversion_metric_id)`

### 9. **`flows/service.py`** - Flows Service
**Responsibilities:**
- Fetch flows
- Get flow actions and messages
- Get individual flow details

**Methods:**
- `get_flows() -> List[Dict]`
- `get_flow(flow_id: str) -> Dict`
- `get_flow_actions(flow_id: str) -> List[Dict]`
- `get_flow_action_messages(action_id: str) -> List[Dict]`

### 10. **`flows/statistics.py`** - Flow Statistics
**Responsibilities:**
- Get flow statistics using Reporting API
- Get individual flow performance

**Methods:**
- `get_statistics(flow_ids, statistics, timeframe, conversion_metric_id)`
- `get_individual_stats(flow_id, days) -> Dict`

### 11. **`flows/patterns.py`** - Flow Pattern Matching
**Responsibilities:**
- Identify flows by name patterns
- Get core flows (Welcome, AC, etc.)

**Methods:**
- `identify_flow_type(flow_name: str) -> Optional[str]`
- `get_core_flows(flows: List[Dict]) -> Dict[str, Dict]`

### 12. **`lists/service.py`** - Lists Service
**Responsibilities:**
- Fetch lists
- Get list subscriber counts
- Get list growth data

**Methods:**
- `get_lists() -> List[Dict]`
- `get_list_profiles_count(list_id: str) -> int`
- `get_list_growth_data(list_id, months) -> Dict`

### 13. **`forms/service.py`** - Forms Service
**Responsibilities:**
- Fetch forms
- Get form performance metrics

**Methods:**
- `get_forms() -> List[Dict]`
- `get_form_performance(days) -> Dict`

### 14. **`revenue/service.py`** - Revenue Service
**Responsibilities:**
- KAV (Klaviyo Attributed Value) analysis
- Revenue attribution breakdown

**Methods:**
- `get_kav_analysis(days, interval) -> Dict`

### 15. **`revenue/time_series.py`** - Revenue Time Series
**Responsibilities:**
- Get revenue time series data
- Calculate attribution breakdowns

**Methods:**
- `get_revenue_time_series(days, interval) -> Dict`

### 16. **`extraction/orchestrator.py`** - Data Extraction Orchestrator
**Responsibilities:**
- Coordinate data extraction from all services
- Structure data for reports
- Handle verbose logging

**Methods:**
- `extract_all_data(date_range, include_enhanced, verbose) -> Dict`

### 17. **`extraction/morrison.py`** - Morrison Audit Formatter
**Responsibilities:**
- Format data for Morrison audit template
- Structure data according to audit format

**Methods:**
- `extract_morrison_audit_data(days, verbose) -> Dict`

### 18. **`utils/date_helpers.py`** - Date Utilities
**Functions:**
- `ensure_z_suffix(dt_str: str) -> str`
- `format_date_range(start: datetime, end: datetime) -> Dict`
- `parse_iso_date(date_str: str) -> datetime`

### 19. **`utils/currency.py`** - Currency Formatting
**Functions:**
- `format_currency(value: float, prefix: str = "$") -> str`
- `format_large_number(value: float) -> str`

### 20. **`utils/validators.py`** - Input Validation
**Functions:**
- `validate_date_range(start: str, end: str) -> bool`
- `validate_metric_id(metric_id: str) -> bool`

## 🔄 Migration Strategy

### Phase 1: Extract Utilities (Non-Breaking)
1. Extract `RateLimiter` to `rate_limiter.py`
2. Extract date helpers to `utils/date_helpers.py`
3. Extract currency formatting to `utils/currency.py`
4. Extract response parsers to `parsers.py`
5. Extract filter builders to `filters.py`

### Phase 2: Extract Service Modules (Backward Compatible)
1. Create `client.py` with base HTTP client
2. Extract metrics to `metrics/` module
3. Extract campaigns to `campaigns/` module
4. Extract flows to `flows/` module
5. Extract lists to `lists/` module
6. Extract forms to `forms/` module
7. Extract revenue to `revenue/` module

### Phase 3: Create Facade (Maintain Compatibility)
1. Create new `KlaviyoService` in `__init__.py` that:
   - Composes all service modules
   - Maintains same public API
   - Delegates to appropriate services
2. Keep old file as `klaviyo_legacy.py` for reference

### Phase 4: Update Dependencies
1. Update all imports to use new structure
2. Update tests
3. Remove legacy file

## ✅ Benefits of Refactoring

1. **Maintainability**: Smaller, focused modules are easier to understand and modify
2. **Testability**: Each module can be tested independently
3. **Reusability**: Services can be used independently
4. **Extensibility**: Easy to add new features without touching existing code
5. **Performance**: Can optimize individual services
6. **Code Quality**: Eliminates duplication and inconsistencies

## 🚨 Breaking Changes

**None** - The refactoring maintains backward compatibility through the facade pattern.

## 📝 Implementation Notes

1. All services will share the same `KlaviyoClient` instance
2. Rate limiting is handled at the client level
3. Error handling should be consistent across all services
4. Use proper logging instead of print statements
5. Add comprehensive type hints
6. Add docstrings to all public methods

## 🔧 Fixes for Inconsistencies

1. Remove unused imports (`os`, `Tuple`)
2. Remove unused `retry_count` parameter
3. Standardize error handling (use custom exceptions)
4. Create unified date formatting utilities
5. Extract duplicate parsing logic to `parsers.py`
6. Replace all `print()` with proper logging
7. Add type hints to all methods
8. Fix hardcoded business logic (make configurable)
9. Standardize return types
10. Add input validation

