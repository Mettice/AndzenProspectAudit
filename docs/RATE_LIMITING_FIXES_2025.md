# Rate Limiting Fixes - January 2025

## Problem Summary
After deployment, the application was experiencing severe rate limiting (429 errors) when generating audit reports. The issue was caused by:
1. **Multiple redundant API calls** to `/flow-values-reports/` endpoint
2. **Inefficient individual flow statistics** - calling API separately for each flow
3. **Too conservative rate limiter** settings
4. **No caching** between duplicate requests
5. **Insufficient delays** between batches

## Root Causes

### 1. Core Flows Performance - Individual API Calls
**Location**: `api/services/klaviyo/flows/patterns.py`

**Problem**: `get_core_flows_performance()` was calling `get_individual_stats()` for each flow sequentially, making 7-10 separate API calls.

**Fix**: Refactored to batch all flow statistics in a single API call, reducing from 7-10 calls to just 1 call.

### 2. No Caching
**Location**: `api/services/klaviyo/flows/statistics.py`

**Problem**: Same flow statistics were being fetched multiple times without caching.

**Fix**: Added in-memory cache with cache key based on:
- Flow IDs (sorted tuple)
- Timeframe
- Statistics requested
- Conversion metric ID

Cache size limited to 50 entries to prevent memory issues.

### 3. Rate Limiter Too Conservative
**Location**: `api/services/klaviyo/client.py`

**Problem**: Rate limiter was set to 4 req/sec, 80/min for medium tier, which is only 40% of the actual limit (10/sec, 150/min).

**Fix**: Updated to 80% of limits for safety margin:
- Small: 2.4/sec, 48/min (was 1.5/sec, 30/min)
- Medium: 8.0/sec, 120/min (was 4.0/sec, 80/min) ⬆️ **2x improvement**
- Large: 60.0/sec, 560/min (was 15.0/sec, 300/min)
- XL: 280.0/sec, 2800/min (was 50.0/sec, 1000/min)

### 4. Insufficient Delays Between Batches
**Location**: `api/services/klaviyo/extraction/flow_extractor.py`

**Problem**: Only 2 second delay between batches wasn't enough to prevent rate limiting.

**Fix**: Increased delay to 3 seconds between batches.

## Changes Made

### File: `api/services/klaviyo/flows/patterns.py`
- **Refactored `get_core_flows_performance()`**:
  - Changed from sequential `get_individual_stats()` calls to batched `get_statistics()` call
  - Fetches flow details and actions in parallel
  - Single API call for all flow statistics instead of 7-10 separate calls
  - **Result**: ~90% reduction in API calls for core flows

### File: `api/services/klaviyo/flows/statistics.py`
- **Added caching**:
  - `_stats_cache` dictionary to cache responses
  - Cache key includes: flow_ids, timeframe, statistics, conversion_metric_id
  - Cache size limited to 50 entries (FIFO eviction)
  - `use_cache` parameter (default True) to enable/disable caching
  - **Result**: Eliminates duplicate API calls for same parameters

### File: `api/services/klaviyo/client.py`
- **Optimized rate limiter settings**:
  - Medium tier: 4.0→8.0 req/sec, 80→120 req/min (2x improvement)
  - All tiers now use 80% of Klaviyo limits for safety margin
  - **Result**: 2x faster throughput while staying safe

### File: `api/services/klaviyo/extraction/flow_extractor.py`
- **Increased batch delays**:
  - Changed from 2.0s to 3.0s between batches
  - **Result**: Better rate limit compliance

## Expected Impact

### Before Fixes:
- **Core flows**: 7-10 API calls (one per flow)
- **Flow extractor**: 5+ API calls (batches of 10)
- **Revenue time series**: 1 API call (all flows)
- **Total**: ~15-20 API calls to `/flow-values-reports/`
- **Rate limit hits**: Frequent 429 errors
- **Time**: Very slow due to retries and delays

### After Fixes:
- **Core flows**: 1 API call (batched) ✅
- **Flow extractor**: 5+ API calls (cached on subsequent calls) ✅
- **Revenue time series**: 1 API call (cached if already fetched) ✅
- **Total**: ~6-8 API calls (60% reduction)
- **Rate limit hits**: Should be rare with optimized rate limiter
- **Time**: Much faster due to batching and caching

## Testing Recommendations

1. **Monitor rate limiting**: Check logs for 429 errors
2. **Verify cache hits**: Check debug logs for "Using cached flow statistics"
3. **Performance**: Measure time to generate audit reports
4. **Memory**: Monitor cache size (should stay under 50 entries)

## Additional Notes

- Caching is per-service instance, so it persists during a single audit generation
- Cache is cleared when service instance is destroyed
- Rate limiter respects Klaviyo's actual limits with 20% safety margin
- All changes maintain backward compatibility

## Future Optimizations

1. **Shared cache across service instances** (Redis/memcached)
2. **Pre-fetch flow statistics** during initial flow extraction
3. **Parallel batch processing** with controlled concurrency
4. **Adaptive rate limiting** based on API response headers

