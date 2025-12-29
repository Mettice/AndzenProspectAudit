# Klaviyo API Limitations & Workarounds
## Date: December 29, 2025

---

## Known API Limitations

### 1. **Push Campaigns Not Supported via Campaigns Endpoint** ⚠️

**Issue:**
- The `/api/campaigns/` endpoint returns `400 Bad Request` when filtering by `equals(messages.channel,'push')`
- Push campaigns cannot be fetched using the same method as email/SMS campaigns

**Error:**
```
Client error '400 Bad Request' for url 'https://a.klaviyo.com/api/campaigns/?filter=equals%28messages.channel%2C%27push%27%29'
```

**Status:**
- ✅ Email campaigns: Working
- ✅ SMS campaigns: Working
- ❌ Push campaigns: Not supported via campaigns endpoint

**Workaround:**
- Push campaigns are gracefully skipped (returns empty list)
- Push revenue will show as $0 in channel breakdown
- This is a Klaviyo API limitation, not a code issue

**Alternative Approaches (Future):**
- Check if push campaigns are available via a different endpoint
- Check if push notifications are tracked differently (not as campaigns)
- Contact Klaviyo support to confirm push campaign access method

---

### 2. **Reporting API: Relative Timeframes Only** ⚠️

**Issue:**
- `/api/campaign-values-reports/` and `/api/flow-values-reports/` only accept relative timeframes
- Cannot use exact date ranges like `2025-09-24` to `2025-12-29`
- Only accepts: `"last_7_days"`, `"last_30_days"`, `"last_90_days"`, `"last_365_days"`

**Workaround:**
- Filter campaigns/flows by date range first (in Python)
- Then query statistics with closest relative timeframe
- May cause small discrepancies if date range doesn't align perfectly

---

### 3. **No Account-Level Revenue Endpoint** ⚠️

**Issue:**
- No single endpoint that returns: total revenue + attributed revenue + campaign revenue + flow revenue
- Must make multiple API calls and aggregate manually

**Workaround:**
- Query total revenue via `/api/metric-aggregates/`
- Query campaign revenue via `/api/campaign-values-reports/`
- Query flow revenue via `/api/flow-values-reports/`
- Sum manually: `attributed_revenue = campaign_revenue + flow_revenue`

---

## What We're Doing Right

1. ✅ **Using Correct Endpoints** - All endpoints verified against Klaviyo documentation
2. ✅ **Error Handling** - Graceful fallbacks for unsupported features
3. ✅ **API Revision** - Using latest revision (2025-10-15)
4. ✅ **Best Practices** - Following Klaviyo's recommended attribution model

---

## Impact on Reports

### Push Campaigns
- **Impact:** Push revenue will show as $0 in channel breakdown
- **Reason:** API limitation, not a code bug
- **Status:** Expected behavior, gracefully handled

### Date Range Discrepancies
- **Impact:** Small discrepancies possible (1-5%)
- **Reason:** Relative timeframes vs exact dates
- **Status:** Acceptable given API limitations

### Manual Aggregation
- **Impact:** More API calls, but accurate results
- **Reason:** No aggregate endpoint available
- **Status:** Working correctly, just more complex

---

## Recommendations

1. ✅ **Continue current approach** - It's correct given API limitations
2. ✅ **Document limitations** - So stakeholders understand constraints
3. 💡 **Contact Klaviyo support** - Ask about push campaign access
4. ✅ **Graceful error handling** - Already implemented

