# Attribution Model Fix - Flow Revenue Too High

## Date: December 26, 2025

## Problem Identified

After fixing the metric ID issue, attributed revenue is now **higher** than total revenue:
- **Total Revenue:** $9,156,703.55
- **Attributed Revenue:** $10,532,053.18 (115% KAV - **impossible!**)
- **Flow Revenue:** $8,694,063.73 (almost equal to total!)
- **Campaign Revenue:** $1,837,989.45

### Root Cause

The `metric-aggregates` API with `$attributed_flow` grouping uses **multi-touch attribution**, which means:
- An order can be attributed to BOTH a flow AND a campaign
- When we sum flow revenue + campaign revenue, we get double-counting
- This causes attributed revenue to exceed total revenue

The **dashboard uses single-touch attribution** (likely last-touch), where:
- Each order is attributed to EITHER a flow OR a campaign (not both)
- Flow revenue + Campaign revenue = Attributed revenue (no overlap)

### Evidence

**Dashboard (single-touch):**
- Campaigns: A$1,831,395.93 (51.86%)
- Flows: A$1,699,712.67 (48.14%)
- **Total Attributed: A$3,531,108.59** (adds up correctly, no overlap)

**Code (multi-touch):**
- Flow Revenue: $8,694,063.73
- Campaign Revenue: $1,837,989.45
- **Total: $10,532,053.18** (exceeds total revenue due to double-counting)

## Solution Implemented

Changed flow revenue query from `metric-aggregates` API to **Reporting API**:
- Reporting API uses the **same attribution model as the dashboard**
- Single-touch attribution (no double-counting)
- Flow revenue + Campaign revenue will add up correctly

### Code Changes

**Before (multi-touch attribution):**
```python
flow_revenue_data = await self.aggregates.query(
    metric_id=conversion_metric_id,
    by=["$attributed_flow"],  # Multi-touch attribution
    ...
)
```

**After (single-touch attribution, matches dashboard):**
```python
flow_stats_response = await self.flow_stats.get_statistics(
    flow_ids=flow_ids,
    statistics=["conversion_value", "conversions"],
    timeframe=timeframe,
    conversion_metric_id=conversion_metric_id  # Uses dashboard attribution model
)
```

## Expected Results

After this fix:
- **Flow Revenue:** Should decrease from $8.7M to ~$1.7M (matching dashboard)
- **Attributed Revenue:** Should decrease from $10.5M to ~$3.5M (matching dashboard)
- **KAV %:** Should decrease from 115% to ~42.88% (matching dashboard)
- **Flow + Campaign:** Should add up to attributed revenue (no double-counting)

## Files Modified

- `api/services/klaviyo/revenue/time_series.py` - Changed flow revenue to use Reporting API

## Testing

Run the test again:
```bash
python test_morrison_audit.py
```

Check the logs for:
- Flow Revenue should be ~$1.7M (not $8.7M)
- Attributed Revenue should be ~$3.5M (not $10.5M)
- KAV % should be ~42.88% (not 115%)

## Key Learnings

1. **Metric Aggregates API** uses multi-touch attribution (can cause double-counting)
2. **Reporting API** uses single-touch attribution (matches dashboard)
3. When combining flow + campaign revenue, must use same attribution model for both
4. Dashboard uses single-touch attribution (last-touch model)

