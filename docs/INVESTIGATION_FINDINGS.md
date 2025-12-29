# Investigation Findings - Report Generation Issues

## Date: 2025-12-29
## Generated Report: `morrison_audit_Test_Client_20251229_042725.html`

---

## 🔍 Issues Identified

### 1. **KAV Overview - Narrative Formatting Issue** ❌

**Problem:**
- The KAV "Performance Overview" section (line 613 in HTML) shows raw JSON structure instead of formatted HTML paragraphs
- The narrative text contains the entire JSON response structure as a string: `"Above-benchmark KAV...", "correlations": [...], "impact": "...", etc.`
- This suggests the LLM response parsing is failing and returning the entire JSON object as a string in the `primary` field

**Root Cause Analysis:**
- Location: `api/services/report/preparers/kav_preparer.py` lines 69-84
- The preparer formats `primary_narrative` as HTML paragraphs, but the LLM is returning JSON structure in the `primary` field
- The JSON parsing in `api/services/llm/__init__.py` (lines 194-284) is trying to extract text but failing
- Terminal shows: "Could not extract text from JSON for campaign_performance, using fallback"

**Questions:**
1. Is the LLM actually returning valid JSON, or is it returning a JSON string inside the `primary` field?
2. Why is the `_parse_response` method not correctly extracting just the text from the `primary` field?
3. Should we check what the actual LLM response looks like before parsing?

---

### 2. **List Growth - Missing LLM Analysis** ❌

**Problem:**
- List Growth section (line 1344) shows fallback text: "Email List Growth Overview: Test Client"
- This suggests the LLM call is either:
  - Failing silently
  - Returning empty `primary` field
  - Not being called at all

**Root Cause Analysis:**
- Location: `api/services/report/preparers/list_growth_preparer.py` lines 29-106
- The preparer tries to call LLM service but falls back to empty `analysis_text` if it fails
- The template checks `{% if list_growth_data.analysis_text %}` which is empty, so it shows the fallback

**Questions:**
1. Is the LLM service actually being called for list_growth?
2. What error is being caught in the exception handler (line 98)?
3. Should we check the logs to see if there's an LLM error?

---

### 3. **Channel Breakdown - SMS/Push Data Missing** ❌

**Problem:**
- SMS and Push revenue are hardcoded to 0 in `kav_preparer.py` (lines 212-213, 217-218)
- Channel breakdown charts don't display because there's no data
- The TODO comment says: "Extract actual channel data from campaigns and flows"

**Root Cause Analysis:**
- Location: `api/services/report/preparers/kav_preparer.py` lines 207-250
- Campaign extraction only fetches "email" channel: `api/services/klaviyo/campaigns/service.py` line 29
- No extraction of SMS/Push revenue from:
  - Campaigns (only email campaigns are fetched)
  - Flows (channel data not extracted from flow statistics)
  - Revenue time series (doesn't break down by channel)

**Questions:**
1. Does Klaviyo API provide SMS/Push revenue data in campaign/flow statistics?
2. Should we fetch campaigns/flows for all channels (email, sms, push)?
3. Does the revenue time series service support channel breakdown?
4. Where should channel data come from - campaigns, flows, or both?

---

### 4. **Chart Data Structure Mismatch** ⚠️

**Problem:**
- Charts may not be rendering because:
  - SMS/Push charts have no data (all 0)
  - Chart data structure might not match JavaScript expectations
  - JavaScript might be failing silently

**Root Cause Analysis:**
- Location: `templates/base.html` lines 100-130 (chart initialization)
- List growth chart data structure: `{"months": [...], "new_subscribers": [...], "net_change": [...]}`
- JavaScript expects: `config.new_subscribers || config.net_change` (line 101)
- This should work, but need to verify charts are actually rendering

**Questions:**
1. Are charts rendering but just empty (no data)?
2. Is JavaScript console showing errors?
3. Does the chart data structure match what the JavaScript expects for each chart type?

---

## 📋 Data Flow Investigation

### KAV Section Data Flow:
1. **Extraction**: `api/services/klaviyo/revenue/time_series.py` → `get_revenue_time_series()`
   - Returns: `chart_data` with `labels`, `total_revenue`, `attributed_revenue`, `unattributed_revenue`, `flow_revenue`, `campaign_revenue`
   - ✅ This looks correct

2. **Preparation**: `api/services/report/preparers/kav_preparer.py` → `prepare_kav_data()`
   - Calls LLM: `llm_service.generate_insights(section="kav", ...)`
   - Formats narratives as HTML paragraphs
   - ❌ Channel breakdown hardcoded to Email only

3. **Template**: `templates/sections/kav_analysis.html`
   - Renders: `{{ kav_data.narrative|safe }}` (line 235)
   - ❌ Getting raw JSON instead of formatted HTML

### List Growth Section Data Flow:
1. **Extraction**: `api/services/klaviyo/lists/service.py` → `get_list_growth_data()`
   - Returns: `chart_data` with `months`, `new_subscribers`, `net_change`
   - ✅ This looks correct

2. **Preparation**: `api/services/report/preparers/list_growth_preparer.py` → `prepare_list_growth_data()`
   - Calls LLM: `llm_service.generate_insights(section="list_growth", ...)`
   - ❌ Falls back to empty `analysis_text` if LLM fails

3. **Template**: `templates/sections/list_growth.html`
   - Checks: `{% if list_growth_data.analysis_text %}` (line 12)
   - ❌ Shows fallback because `analysis_text` is empty

---

## 🔧 LLM Response Parsing Investigation

### Current Parsing Logic (`api/services/llm/__init__.py`):
1. **Line 152**: Invokes LLM and gets response
2. **Line 161**: Calls `_parse_response()` to parse JSON
3. **Lines 194-284**: Validates and extracts `primary` field
   - Handles nested JSON strings
   - Tries multiple extraction strategies
   - Falls back if extraction fails

### Issues Found:
1. **Line 274**: "Could not extract text from JSON for {section}, using fallback"
   - This is being triggered, suggesting the extraction is failing
   - The raw response might be valid JSON, but the `primary` field contains a JSON string

2. **Line 613 in HTML**: Shows the entire JSON structure as text
   - This means the `primary` field contains the full JSON response as a string
   - The parsing logic isn't extracting just the text value

---

## ❓ Questions for User

1. **KAV Narrative Formatting:**
   - Should the "Performance Overview" show just the `primary` narrative text, or should it include other fields like `root_cause_analysis`, `risk_flags`, etc.?
   - The template shows `{{ kav_data.narrative|safe }}` - is this the right field to use?

2. **List Growth:**
   - Is the LLM service actually working? Are there any errors in the logs?
   - Should we check what the actual LLM response looks like for list_growth?

3. **Channel Data:**
   - Does the Klaviyo account actually have SMS/Push campaigns or flows?
   - Should we extract channel data from:
     - Campaign statistics (by channel type)?
     - Flow statistics (by channel type)?
     - Revenue time series (if it supports channel breakdown)?
   - Or is it okay to show Email only if that's all the account uses?

4. **Chart Display:**
   - Are the charts actually rendering but just empty (no data)?
   - Or are they completely missing from the page?
   - Should we check the browser console for JavaScript errors?

5. **When did this break?**
   - The user mentioned "all that happened when we modularized the prompts"
   - What specific changes were made during modularization?
   - Did the prompt structure change, or just the file organization?

---

## 🎯 Next Steps (After User Answers)

1. **Fix KAV Narrative Formatting:**
   - Check what the actual LLM response looks like
   - Fix the parsing logic to correctly extract text from `primary` field
   - Ensure HTML formatting is applied correctly

2. **Fix List Growth:**
   - Check if LLM service is being called
   - Check what error is being caught
   - Fix the LLM call or improve error handling

3. **Fix Channel Data:**
   - Investigate if Klaviyo API provides channel breakdown
   - Update extraction to fetch SMS/Push data if available
   - Update preparer to use actual channel data instead of hardcoded values

4. **Verify Chart Rendering:**
   - Check browser console for JavaScript errors
   - Verify chart data structure matches JavaScript expectations
   - Fix chart initialization if needed

---

## 📝 Files to Review

1. `api/services/llm/__init__.py` - LLM response parsing
2. `api/services/report/preparers/kav_preparer.py` - KAV data preparation
3. `api/services/report/preparers/list_growth_preparer.py` - List growth data preparation
4. `api/services/llm/prompts/kav_prompt.py` - KAV prompt template
5. `api/services/llm/prompts/section_prompts.py` - List growth prompt template
6. `templates/sections/kav_analysis.html` - KAV template rendering
7. `templates/sections/list_growth.html` - List growth template rendering
8. `api/services/klaviyo/campaigns/service.py` - Campaign extraction (channel filtering)
9. `api/services/klaviyo/revenue/time_series.py` - Revenue time series (channel breakdown?)

---

## ⚠️ Important Notes

- **DO NOT MAKE CHANGES YET** - User requested investigation only
- All findings are based on code review and generated HTML analysis
- Need user confirmation on expected behavior before fixing
- Need to understand what changed during "modularization" that broke things

