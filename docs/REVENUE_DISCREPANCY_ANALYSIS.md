# Revenue Discrepancy Analysis & Fix

## Date: December 26, 2025

## Problem Identified

### Dashboard vs Code Values
**Dashboard Screenshot (Sep 24 - Dec 26, 2025):**
- Total revenue: A$8,740,485.30
- Attributed revenue: A$3,673,689.62 (42.03% of total)
- Campaigns: A$1,924,913.62 (52.40%)
- Flows: A$1,748,776.01 (47.60%)

**Code Output (from logs):**
- Total Revenue: $9,133,497.55
- Attributed Revenue: $115,777.74 (1.3% KAV)
- Flow Revenue: $61,313.93
- Campaign Revenue: $54,463.81

**Discrepancy:** 
- Total revenue is close (8.7M vs 9.1M - ~4% difference, likely due to date range calculation)
- **Attributed revenue is 31x lower** in code ($115K vs $3.6M) - This is the critical issue

## Root Cause Analysis

### 1. **Relative Timeframes vs Custom Date Ranges**
The Reporting API (`/flow-values-reports/` and `/campaign-values-reports/`) only accepts **relative timeframes**:
- `"last_7_days"`, `"last_30_days"`, `"last_90_days"`, `"last_365_days"`
- These are relative to **NOW**, not to the end date of the date range

**Problem:**
- Code was using `timeframe="last_90_days"` which means "last 90 days from NOW"
- Dashboard shows data for specific date range: "Sep 24 - Dec 26, 2025"
- If the code runs on a different date, the timeframe won't match

### 2. **No Date Filtering Before Querying Statistics**
- Code was querying **ALL flows** and **ALL campaigns** without filtering by date range
- Dashboard only shows statistics for flows/campaigns active in the date range
- This caused inclusion of flows/campaigns outside the period

### 3. **Attribution Model Differences**
According to Klaviyo documentation:
- **Dashboard:** Groups data based on when the attributed message was **sent**
- **API:** Groups data based on when events **occur**
- This can cause discrepancies even with correct date ranges

## Solution Implemented

### 1. **Flow Revenue: Use Metric Aggregates API with Date Range**
Changed from Reporting API (relative timeframe) to Metric Aggregates API:
```python
flow_revenue_data = await self.aggregates.query(
    metric_id=conversion_metric_id,
    start_date=start_str,  # Exact date range
    end_date=end_str,
    measurements=["sum_value"],
    interval=interval,
    by=["$attributed_flow"],  # Group by attributed flow
    timezone=account_timezone
)
```

**Benefits:**
- Uses exact date range (not relative)
- Groups by `$attributed_flow` to get flow-attributed revenue
- Matches dashboard calculation method

### 2. **Campaign Revenue: Filter by Date Range First**
Since `$attributed_campaign` is NOT a valid grouping parameter:
- Filter campaigns by date range before querying statistics
- Use Reporting API with relative timeframe (limitation remains)
- This ensures we only query campaigns active in the period

```python
# Filter campaigns by date range
all_campaigns = await self.campaigns.get_campaigns(
    start_date=start_str,
    end_date=end_str
)

# Then query statistics for filtered campaigns
campaign_stats_response = await self.campaign_stats.get_statistics(
    campaign_ids=campaign_ids,
    statistics=["conversion_value", "conversions"],
    timeframe=timeframe,  # Still relative, but campaigns are filtered
    conversion_metric_id=conversion_metric_id
)
```

### 3. **Improved Error Handling**
- Added fallback to Reporting API if Metric Aggregates fails
- Better parsing of different response structures
- More detailed logging for debugging

## Remaining Limitations

### 1. **Campaign Revenue Still Uses Relative Timeframe**
- Campaign revenue query still uses `timeframe="last_90_days"` (relative to NOW)
- This may not exactly match the dashboard's date range
- **Workaround:** Filter campaigns by date range first, then query statistics
- **Impact:** Small discrepancy possible if date range doesn't align with relative timeframe

### 2. **Attribution Model Differences**
- Dashboard and API may use different attribution models
- Dashboard: based on message send date
- API: based on event occurrence date
- **Impact:** May cause small discrepancies even with correct date ranges

### 3. **Timezone Handling**
- Code uses `account_timezone="Australia/Sydney"` for date range calculation
- Dashboard may use account timezone or UTC
- **Impact:** Potential 1-day discrepancies at timezone boundaries

## Expected Improvements

After these fixes:
1. **Flow Revenue:** Should match dashboard more closely (using exact date range)
2. **Campaign Revenue:** Should be closer (filtered by date range, but still uses relative timeframe)
3. **Total Revenue:** Already close (8.7M vs 9.1M - likely timezone/date boundary issue)
4. **Attributed Revenue:** Should increase significantly (from $115K toward $3.6M range)

## Testing Recommendations

1. **Run test with same date range as dashboard:**
   ```python
   python test_morrison_audit.py
   ```

2. **Compare values:**
   - Check if attributed revenue is closer to dashboard ($3.6M)
   - Verify flow revenue matches dashboard ($1.7M)
   - Check campaign revenue ($1.9M)

3. **Check logs for:**
   - "Flow Revenue (Aggregates API)" - should show higher value
   - "Campaign Revenue" - should show higher value
   - Any fallback messages

4. **If discrepancies persist:**
   - Check if `$attributed_flow` grouping works correctly
   - Verify date range calculation matches dashboard exactly
   - Consider using individual flow/campaign statistics API with date filtering

## Files Modified

- `api/services/klaviyo/revenue/time_series.py`
  - Changed flow revenue to use Metric Aggregates API with `$attributed_flow`
  - Added date filtering for campaigns before querying statistics
  - Improved response parsing and error handling
  - Added fallback mechanisms

## Next Steps (If Issues Persist)

1. **Investigate Metric Aggregates Response Structure**
   - Verify `$attributed_flow` grouping returns correct data
   - Check if response structure matches expected format
   - Add more detailed logging of response structure

2. **Consider Alternative Approach for Campaign Revenue**
   - Query individual campaign statistics with date filtering
   - Sum conversion_value across all campaigns in date range
   - May require batching to avoid rate limits

3. **Add Date Range Validation**
   - Ensure date range calculation matches dashboard exactly
   - Account for timezone differences
   - Handle edge cases (partial days, timezone boundaries)

4. **Compare with Dashboard API**
   - If available, check if Klaviyo provides a dashboard data export API
   - Compare raw API responses with dashboard values
   - Identify any additional filtering/calculation differences

