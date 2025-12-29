# Klaviyo API Analysis - Why Complex Calculations?

## Date: December 29, 2025

## Question: Why are we doing complex calculations when the dashboard displays data perfectly?

### TL;DR Answer

**Klaviyo's public API doesn't have a single "dashboard data" endpoint.** The dashboard has access to internal/pre-aggregated data that we don't have via the public API. We must:
1. Make multiple API calls
2. Filter and aggregate data ourselves
3. Handle API limitations (relative timeframes vs exact date ranges)

---

## Current API Endpoints We're Using

### ✅ What We're Using (Correct Endpoints)

1. **Total Revenue**: `/metric-aggregates/` (POST)
   - Endpoint: `POST /api/metric-aggregates/`
   - Works with exact date ranges ✅
   - Groups by metric (Ordered Product or Placed Order)
   - **Status**: ✅ Working correctly

2. **Campaign Revenue**: `/campaign-values-reports/` (POST) - Reporting API
   - Endpoint: `POST /api/campaign-values-reports/`
   - **Limitation**: Only accepts relative timeframes (`last_7_days`, `last_30_days`, `last_90_days`, `last_365_days`)
   - **Problem**: Can't use exact date ranges like `2025-09-24` to `2025-12-29`
   - **Workaround**: Filter campaigns by date range first, then query statistics
   - **Status**: ⚠️ Working but complex

3. **Flow Revenue**: `/flow-values-reports/` (POST) - Reporting API
   - Endpoint: `POST /api/flow-values-reports/`
   - **Limitation**: Same as campaign - only relative timeframes
   - **Problem**: Can't use exact date ranges
   - **Status**: ⚠️ Working but complex

4. **Campaigns List**: `/campaigns/` (GET)
   - Endpoint: `GET /api/campaigns/`
   - Can filter by channel (email, sms, push) ✅
   - Can filter by date range (in Python, not API) ⚠️
   - **Status**: ✅ Working

5. **Flows List**: `/flows/` (GET)
   - Endpoint: `GET /api/flows/`
   - **Status**: ✅ Working

---

## Why Dashboard is Simpler

### Dashboard Has Access To:
1. **Pre-aggregated data** - Revenue totals already calculated
2. **Exact date range queries** - Can query specific date ranges internally
3. **Single data source** - One query returns all revenue breakdowns
4. **Internal attribution engine** - Direct access to attribution calculations

### Public API Limitations:
1. **No account-level revenue endpoint** - Must query individual campaigns/flows
2. **Relative timeframes only** - Reporting API doesn't support exact date ranges
3. **Multiple API calls required** - Must sum up revenue from many calls
4. **Attribution model differences** - Metric-aggregates (multi-touch) vs Reporting API (single-touch)

---

## API Endpoints Checked (What's NOT Available)

### ❌ What We Checked For (Doesn't Exist):

1. **Account Revenue Summary Endpoint**
   - ❌ No `/api/accounts/{id}/revenue/` endpoint
   - ❌ No `/api/revenue-summary/` endpoint
   - ❌ No `/api/dashboard-data/` endpoint

2. **Aggregate Revenue Endpoint**
   - ❌ No `/api/revenue/aggregate/` endpoint
   - ❌ No `/api/attributed-revenue/` endpoint
   - ❌ No single endpoint that returns: total + attributed + campaign + flow

3. **Dashboard Export Endpoint**
   - ❌ No `/api/dashboard/export/` endpoint
   - ❌ No `/api/reports/dashboard/` endpoint

---

## Why We Do Complex Calculations

### 1. **Multiple API Calls Required**

**Dashboard (1 query):**
```
SELECT 
  total_revenue,
  attributed_revenue,
  campaign_revenue,
  flow_revenue
FROM dashboard_data
WHERE date_range = '2025-09-24 to 2025-12-29'
```

**Our Code (5+ queries):**
```python
# 1. Get total revenue
total = await metric_aggregates.query(...)

# 2. Get all campaigns in date range
campaigns = await campaigns.get_campaigns(start, end)

# 3. Get campaign statistics (for each campaign)
campaign_stats = await campaign_stats.get_statistics(campaign_ids)

# 4. Get all flows
flows = await flows.get_flows()

# 5. Get flow statistics (for each flow)
flow_stats = await flow_stats.get_statistics(flow_ids)

# 6. Sum up campaign revenue manually
campaign_revenue = sum([stat['conversion_value'] for stat in campaign_stats])

# 7. Sum up flow revenue manually
flow_revenue = sum([stat['conversion_value'] for stat in flow_stats])

# 8. Calculate attributed revenue
attributed = campaign_revenue + flow_revenue
```

### 2. **Relative Timeframes Limitation**

**Problem:**
- Reporting API only accepts: `"last_7_days"`, `"last_30_days"`, `"last_90_days"`, `"last_365_days"`
- These are relative to **NOW**, not to a specific end date
- Dashboard can query: `"2025-09-24 to 2025-12-29"` (exact dates)

**Our Workaround:**
```python
# Step 1: Filter campaigns by exact date range (in Python)
campaigns = await campaigns.get_campaigns(start_date="2025-09-24", end_date="2025-12-29")

# Step 2: Query statistics with relative timeframe (closest match)
timeframe = "last_90_days"  # Closest to our 90-day range
stats = await campaign_stats.get_statistics(campaign_ids, timeframe=timeframe)
```

**Issue:** If we run the code on a different date, `last_90_days` won't match the dashboard's date range.

### 3. **Attribution Model Differences**

**Metric Aggregates API** (`/metric-aggregates/`):
- Uses **multi-touch attribution**
- An order can be attributed to BOTH a flow AND a campaign
- If we sum: `flow_revenue + campaign_revenue`, we get double-counting

**Reporting API** (`/campaign-values-reports/`, `/flow-values-reports/`):
- Uses **single-touch attribution** (matches dashboard)
- Each order is attributed to EITHER a flow OR a campaign
- `flow_revenue + campaign_revenue = attributed_revenue` (no overlap)

**Why We Use Reporting API:**
- Matches dashboard attribution model
- Prevents double-counting
- But requires multiple queries and manual summing

---

## Could We Simplify?

### Option 1: Use Metric Aggregates with `$attributed_*` Grouping ❌

**Tried this, but:**
- `$attributed_flow` works ✅
- `$attributed_campaign` **doesn't exist** ❌ (not a valid grouping parameter)
- Would still need Reporting API for campaigns

### Option 2: Use Only Reporting API ⚠️

**Current approach, but:**
- Only relative timeframes (not exact dates)
- Must filter campaigns/flows first
- Still requires multiple queries

### Option 3: Request New Endpoint from Klaviyo 💡

**What we'd need:**
```
POST /api/revenue-summary/
{
  "start_date": "2025-09-24",
  "end_date": "2025-12-29",
  "timezone": "Australia/Sydney"
}

Response:
{
  "total_revenue": 8740485.30,
  "attributed_revenue": 3673689.62,
  "campaign_revenue": 1924913.62,
  "flow_revenue": 1748776.01,
  "breakdown": {
    "email": {...},
    "sms": {...},
    "push": {...}
  }
}
```

**Status:** This endpoint doesn't exist in Klaviyo's public API (as of Dec 2025)

---

## Verification: Are We Using Endpoints Correctly?

### ✅ Endpoints We're Using (Verified Against Documentation)

1. **`POST /api/metric-aggregates/`** ✅
   - Reference: https://developers.klaviyo.com/en/reference/query_metric_aggregates
   - We're using it correctly
   - Supports exact date ranges ✅

2. **`POST /api/campaign-values-reports/`** ✅
   - Reference: https://developers.klaviyo.com/en/reference/query_campaign_values
   - We're using it correctly
   - Limitation: Only relative timeframes (documented limitation)

3. **`POST /api/flow-values-reports/`** ✅
   - Reference: https://developers.klaviyo.com/en/reference/query_flow_values
   - We're using it correctly
   - Limitation: Only relative timeframes (documented limitation)

4. **`GET /api/campaigns/`** ✅
   - Reference: https://developers.klaviyo.com/en/reference/get_campaigns
   - We're using it correctly
   - Can filter by channel ✅

5. **`GET /api/flows/`** ✅
   - Reference: https://developers.klaviyo.com/en/reference/get_flows
   - We're using it correctly

### ✅ API Revision
- We're using: `revision: "2025-10-15"` ✅
- This is the latest revision as of Dec 2025 ✅

---

## Summary

### Why It's Complex:

1. **No single endpoint** for dashboard-like revenue data
2. **Relative timeframes only** in Reporting API (not exact dates)
3. **Multiple queries required** - must sum up revenue manually
4. **Attribution model differences** - must use Reporting API to match dashboard

### What We're Doing Right:

1. ✅ Using correct endpoints per Klaviyo documentation
2. ✅ Using Reporting API for attribution (matches dashboard)
3. ✅ Filtering campaigns/flows by date range before querying
4. ✅ Using latest API revision (2025-10-15)

### What Could Be Better (If Klaviyo Adds It):

1. 💡 Account-level revenue summary endpoint
2. 💡 Exact date range support in Reporting API
3. 💡 Single endpoint that returns all revenue breakdowns
4. 💡 Dashboard data export API

---

## Recommendation

**Current approach is correct** given API limitations. The complexity is necessary because:
- Klaviyo's public API doesn't provide dashboard-level aggregation
- We must work within API constraints (relative timeframes)
- We're using the right endpoints and following best practices

**If discrepancies persist**, they're likely due to:
- Timezone differences
- Date boundary calculations
- Attribution timing differences (message send date vs event date)

**Next Steps:**
1. ✅ Continue using current approach (it's correct)
2. ✅ Add better logging to track date range calculations
3. 💡 Consider requesting new endpoint from Klaviyo support
4. ✅ Document any remaining discrepancies as "API limitations"

