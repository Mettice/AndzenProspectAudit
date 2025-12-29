# Revenue Calculation Fixes - Implementation Summary

## Date: December 25, 2025

### Issues Fixed

#### 1. ✅ KAV Calculation Bug (CRITICAL)
**Problem:** 
- Line 231 had: `estimated_total_attributed = max(total_sum * 0.25, flow_sum * 1.2)`
- This caused KAV to exceed 100% (showing 120%)
- Attributed revenue ($10.47M) > Total revenue ($8.72M)

**Fix:**
- Removed broken estimation logic
- Now calculates: `attributed_revenue = flow_revenue + campaign_revenue` (both from API)
- Added validation to cap KAV at 100% if data quality issues occur

#### 2. ✅ Campaign Revenue Query
**Problem:**
- Campaign revenue was being estimated, not queried
- Used broken logic based on flow_sum * 1.2

**Fix:**
- Added direct query using `by=["$attributed_campaign"]`
- Campaign revenue now comes directly from Klaviyo API
- Matches dashboard data structure

#### 3. ✅ Flow Revenue Query Validation
**Problem:**
- Flow revenue ($8.72M) equaled total revenue ($8.72M)
- Indicates query returning total instead of attributed flow revenue

**Fix:**
- Added validation to detect when flow revenue equals total
- Checks response structure for proper grouping
- Logs warnings and handles edge cases
- Prevents impossible KAV percentages

#### 4. ✅ Flow Statistics Timeframe
**Problem:**
- Flow statistics used hardcoded "last_90_days" timeframe
- Didn't match actual date range parameter

**Fix:**
- Added dynamic timeframe mapping based on days parameter
- Maps: 7→last_7_days, 30→last_30_days, 90→last_90_days, 365→last_365_days

#### 5. ✅ Unsubscribe Metric Detection
**Problem:**
- "Unsubscribed" metric not found
- List growth showing 0 for new/lost subscribers

**Fix:**
- Expanded search to try multiple metric name variations:
  - "Unsubscribed from List"
  - "Unsubscribed"
  - "Unsubscribed from Email"
  - "Unsubscribed from Campaign"
  - "Unsubscribed from Flow"
- Added logging to show available metrics for debugging

### Expected Results After Fixes

| Metric | Dashboard | Expected Code Output | Status |
|--------|-----------|----------------------|--------|
| Total Revenue | A$7,986,007.82 | ~$7.99M | Should match |
| Attributed Revenue | A$3,313,157.35 | ~$3.31M | Should match |
| KAV % | 41.49% | ~41.5% | Should match |
| Flow Revenue | A$1,601,073.64 | ~$1.60M | Should match |
| Campaign Revenue | A$1,712,083.72 | ~$1.71M | Should match |

### Files Modified

1. `api/services/klaviyo/revenue/time_series.py`
   - Added campaign revenue query
   - Removed broken KAV calculation
   - Added validation and error handling
   - Improved response parsing

2. `api/services/klaviyo/flows/statistics.py`
   - Fixed timeframe mapping for flow statistics

3. `api/services/klaviyo/lists/service.py`
   - Improved unsubscribe metric detection
   - Added better error logging

### Testing Required

1. Run test with matching date range (Sep 26 - Dec 25, 2025)
2. Verify KAV percentage is between 0-100%
3. Verify flow revenue < total revenue
4. Verify campaign revenue is queried (not estimated)
5. Check that attributed revenue = flow + campaign
6. Verify list growth data shows actual values (if metrics found)

### Known Limitations

1. **Flow Revenue Query:** If `$attributed_flow` query continues to return total revenue, may need to:
   - Check Klaviyo API documentation for correct query syntax
   - Use flow statistics API instead of metric aggregates
   - Add additional filters to ensure only attributed revenue

2. **Unsubscribe Metric:** If metric still not found, may need to:
   - Query all metrics and search by pattern
   - Use alternative method to calculate list churn
   - Accept that unsubscribe data may not be available for some accounts

### Next Steps

1. Test the fixes with actual API calls
2. Monitor logs for validation warnings
3. If flow revenue still equals total, investigate API response structure
4. Consider using flow statistics API for individual flow revenue instead of aggregates

