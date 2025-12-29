# Report Review Checklist - Section by Section

## Issues Fixed

### 1. Missing LLM Prompt Functions ✅
- **Issue**: `_get_browse_abandonment_prompt` and `_get_post_purchase_prompt` were missing
- **Fix**: Added both functions to `api/services/llm/prompts.py`
- **Status**: Fixed

### 2. Abandoned Cart Showing 0 Values ✅
- **Issue**: Abandoned Checkout flow showing 0% even when flow doesn't exist
- **Fix**: Updated `_prepare_abandoned_cart_data()` to only include flows that were found (`found: True`)
- **Status**: Fixed - Now only shows flows that actually exist

### 3. Browse Abandonment Empty Flows ✅
- **Issue**: Browse abandonment showing empty flow entries
- **Fix**: Updated `_prepare_browse_abandonment_data()` to only include flows with actual data
- **Status**: Fixed

## Section-by-Section Review

### Page 1: Cover Page
- [ ] Client name correct
- [ ] Audit date correct
- [ ] Auditor name correct

### Pages 2-3: KAV Analysis
- [ ] Total revenue matches logs ($9,017,510.33)
- [ ] Attributed revenue matches logs ($3,254,655.32)
- [ ] KAV percentage matches logs (36.1%)
- [ ] Flow vs Campaign breakdown shown
- [ ] LLM-generated narrative present (not hardcoded)
- [ ] Chart displays correctly

### Page 4: List Growth
- [ ] Current subscribers matches logs (10,574)
- [ ] New subscribers matches logs (10,446)
- [ ] Lost subscribers matches logs (341)
- [ ] Churn rate matches logs (3.26%)
- [ ] Monthly breakdown chart displays
- [ ] LLM-generated narrative present

### Pages 5-6: Data Capture
- [ ] Forms with impressions > 0 only shown
- [ ] Submit rates formatted correctly (0.90% vs 12.6%)
- [ ] Form standings correct (Excellent/Good/Average/Poor)
- [ ] LLM-generated analysis present
- [ ] Recommendations list present

### Page 7: Automation Overview
- [ ] Flow performance table shows all active flows
- [ ] Revenue per recipient calculated correctly
- [ ] Total recipients shown
- [ ] LLM-generated narrative present
- [ ] Chart displays correctly

### Page 8: Welcome Series
- [ ] Flow name correct
- [ ] Performance metrics match logs
- [ ] Benchmark comparison shown
- [ ] LLM-generated analysis present
- [ ] Recommendations present

### Pages 9-10: Abandoned Cart ⚠️ CHECK THIS
- [ ] **Abandoned Checkout**: Should NOT show if flow not found (logs show "MISSING")
- [ ] **Abandoned Cart Reminder**: Should show with actual data (47.48% open, $21,238.56 revenue)
- [ ] Only flows that exist are shown
- [ ] No 0% entries for missing flows
- [ ] LLM-generated narrative present
- [ ] Recommendations present

### Page 11: Browse Abandonment
- [ ] Flow shown only if exists (logs show it exists: 7.3% open, $420 revenue)
- [ ] Performance metrics match logs
- [ ] LLM-generated narrative present (not "LLM analysis unavailable")
- [ ] Recommendations present

### Pages 12-13: Post Purchase
- [ ] Flow shown only if exists
- [ ] Performance metrics correct
- [ ] LLM-generated narrative present
- [ ] Recommendations present

### Page 14: Reviews
- [ ] Section displays correctly
- [ ] Checklist items shown

### Pages 15-16: Wishlist
- [ ] Section displays correctly
- [ ] Checklist items shown

### Page 17: Campaign Performance
- [ ] Average open rate shown
- [ ] Average click rate shown
- [ ] Average placed order rate shown (NOT 0%)
- [ ] Total revenue shown
- [ ] LLM-generated narrative present
- [ ] Benchmark comparison shown

### Page 18: Segmentation Strategy
- [ ] Tracks listed correctly
- [ ] Cadence shown for each track

### Page 19: Strategic Recommendations
- [ ] LLM-generated recommendations present
- [ ] Sections organized correctly

## Common Issues to Check

1. **Zero Values**: Any section showing 0% or $0.00 should be verified:
   - Is the flow/campaign actually missing?
   - Or is it just not performing?

2. **LLM Analysis**: Check for "LLM analysis unavailable" messages:
   - Should be minimal fallback text
   - Not long hardcoded paragraphs

3. **Data Accuracy**: Compare numbers in report to logs:
   - KAV: $9,017,510.33 total, $3,254,655.32 attributed
   - List: 10,574 current, 10,446 new, 341 lost
   - Forms: Check which ones have impressions > 0

4. **Missing Flows**: 
   - Abandoned Checkout: MISSING (should not show in table)
   - Other flows: Check logs for "MISSING" or "✓" indicators

## Next Steps

1. Regenerate report with fixes
2. Check each section against this checklist
3. Verify all LLM-generated content is present
4. Confirm no hardcoded fallback text appears
5. Verify abandoned cart only shows existing flows

