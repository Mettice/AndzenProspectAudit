# LLM Section Expectations

This document defines what each section of the Morrison audit report should generate via LLM, including expected output format and data requirements.

## Section Prompt Mapping

Each section has a dedicated prompt function that generates LLM instructions. The LLM should always return JSON with specific fields.

### 1. KAV Analysis (`kav`)
**Prompt Function:** `_get_kav_prompt()`
**Expected Output:**
```json
{
    "primary": "5-7 sentence overview with specific numbers and percentages",
    "secondary": "Strategic implications and optimization opportunities",
    "strategic_focus": "optimization|growth|rebalancing|excellence"
}
```
**Data Required:** Total revenue, attributed revenue, KAV percentage, flow/campaign breakdown, industry benchmarks

### 2. List Growth (`list_growth`)
**Prompt Function:** `_get_list_growth_prompt()`
**Expected Output:**
```json
{
    "primary": "3-5 sentence overview of list health and growth trends",
    "secondary": "Strategic recommendations for growth and retention"
}
```
**Data Required:** Current total, net change, new/lost subscribers, churn rate, period months

### 3. Data Capture (`data_capture`)
**Prompt Function:** `_get_data_capture_prompt()`
**Expected Output:**
```json
{
    "primary": "5-7 sentence analysis with specific form names and percentages",
    "recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"]
}
```
**Data Required:** Form list with impressions, submissions, submit rates, standings, industry benchmarks

### 4. Automation Overview (`automation_overview`)
**Prompt Function:** `_get_automation_prompt()`
**Expected Output:**
```json
{
    "primary": "4-6 sentence overview of automation performance",
    "secondary": "Strategic recommendations for optimization"
}
```
**Data Required:** Total revenue, total recipients, flow breakdown, period days

### 5. Flow Performance (`flow_performance`)
**Used for:** Welcome Series, Abandoned Cart, Browse Abandonment, Post Purchase
**Prompt Function:** `_get_flow_prompt()`
**Expected Output:**
```json
{
    "primary": "3-5 sentence analysis with specific metrics and benchmark comparison",
    "secondary": "2-4 sentence strategic recommendations",
    "performance_status": "excellent|good|needs_improvement|poor"
}
```
**Data Required:** Flow name, open rate, click rate, conversion rate, revenue, revenue per recipient, conversions, industry benchmarks

### 6. Campaign Performance (`campaign_performance`)
**Prompt Function:** `_get_campaign_prompt()`
**Expected Output:**
```json
{
    "primary": "4-6 sentence analysis with specific metrics and benchmark comparison",
    "secondary": "3-5 sentence strategic recommendations",
    "performance_status": "excellent|good|needs_improvement|poor"
}
```
**Data Required:** Average open/click/conversion rates, total revenue, industry benchmarks

## Critical Requirements

1. **ALWAYS include specific numbers** from the data
2. **ALWAYS compare to industry benchmarks**
3. **Match Morrison audit style** - professional, consultant tone
4. **Be actionable** - provide specific recommendations
5. **Avoid generic statements** - reference actual metrics

## Fallback Behavior

If LLM fails:
- Log error with full traceback
- Provide minimal data-driven fallback (not hardcoded generic text)
- Show message: "LLM analysis unavailable. Review metrics above."

## Page Structure

The Morrison audit follows this structure:
1. Cover Page
2. KAV Analysis (2 pages)
3. List Growth (1 page)
4. Data Capture (2 pages)
5. Automation Overview (1 page)
6. Welcome Series (1 page)
7. Abandoned Cart (2 pages)
8. Browse Abandonment (1 page)
9. Post Purchase (2 pages)
10. Reviews (1 page)
11. Wishlist (2 pages)
12. Campaign Performance (1 page)
13. Segmentation Strategy (1 page)
14. Strategic Recommendations (1 page)

**Total: ~18-19 pages** (varies based on data availability)

