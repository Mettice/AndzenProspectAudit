# Critical Fix: Using Correct Placed Order Metric ID

## Date: December 26, 2025

## Problem Identified

The code was using the wrong "Placed Order" metric ID, causing attributed revenue to be **9x lower** than the dashboard.

### Root Cause
Cherry Collectables has **TWO** "Placed Order" metrics:
1. **U7yLfB** - API integration (created 2025-11-20)
2. **Y6Hmxn** - Shopify integration (created 2022-01-24) ← **This is the one the dashboard uses**

The `get_metric_by_name()` function was returning the **first match** (U7yLfB), but the dashboard uses **Y6Hmxn** (Shopify).

### Impact
- **Code output:** $375,817 attributed revenue (4.1% KAV)
- **Dashboard:** A$3,531,108 attributed revenue (42.88% KAV)
- **Discrepancy:** 9.4x lower in code

## Solution Implemented

### 1. Updated `get_metric_by_name()` to Prefer Shopify Integration
Modified `api/services/klaviyo/metrics/service.py`:
- Added `prefer_integration` parameter
- When multiple metrics match, prefers the specified integration
- Falls back to first match if preference not found

### 2. Updated All Placed Order Metric Queries
Updated these files to prefer Shopify integration:
- `api/services/klaviyo/revenue/time_series.py` - Main revenue calculation
- `api/services/klaviyo/flows/statistics.py` - Flow statistics
- `api/services/klaviyo/campaigns/statistics.py` - Campaign statistics

### Code Changes
```python
# Before (wrong - gets first match, might be API integration)
placed_order = await self.metrics.get_metric_by_name("Placed Order")

# After (correct - prefers Shopify to match dashboard)
placed_order = await self.metrics.get_metric_by_name("Placed Order", prefer_integration="shopify")
```

## Expected Results

After this fix:
- **Attributed Revenue:** Should increase from $375K to ~$3.5M (matching dashboard)
- **KAV %:** Should increase from 4.1% to ~42.88% (matching dashboard)
- **Flow Revenue:** Should increase significantly
- **Campaign Revenue:** Should increase significantly

## Testing

Run the test again:
```bash
python test_morrison_audit.py
```

Check the logs for:
- `Using Placed Order for attribution: Y6Hmxn (Shopify)` ← Should see this
- Attributed revenue should be much higher (~$3.5M range)

## Files Modified

1. `api/services/klaviyo/metrics/service.py` - Added integration preference
2. `api/services/klaviyo/revenue/time_series.py` - Use Shopify metric
3. `api/services/klaviyo/flows/statistics.py` - Use Shopify metric
4. `api/services/klaviyo/campaigns/statistics.py` - Use Shopify metric

## Reference

From API_ACCESS.md:
- **Y6Hmxn** is the Shopify Placed Order metric (the main one used by dashboard)
- **U7yLfB** is the API Placed Order metric (created later, not used by dashboard)
- The API key has full read-only access
- Revenue data IS accessible through `conversion_value` statistic with correct metric ID

