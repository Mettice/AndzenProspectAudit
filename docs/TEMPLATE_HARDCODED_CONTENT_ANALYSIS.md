# Template Hardcoded Content Analysis

## Issues Found

### 1. KAV Chart Structure Mismatch ❌
**Sample Audit Chart:**
- Monthly data (Nov, Dec, Jan, Feb)
- Bars: "Attributed revenue" (blue), "Unattributed revenue" (green)
- Line: "Total Recipients" (yellow)
- Varying values showing trends

**Our Chart:**
- Daily data (90 days)
- Bars: "Attributed revenue" (green)
- Lines: "Flow Revenue", "Campaign Revenue", "Unattributed revenue", "Total Recipients"
- **FLAT LINES** - all same values (wrong!)

**Root Cause:** `time_series.py` distributes total revenue evenly across all days instead of using actual daily/monthly data.

### 2. Hardcoded Content in Templates

#### `list_growth.html` (Line 12-19)
```html
<p>
    In conducting this audit, we've chosen to concentrate on your latest list, 
    <strong><u>{{ list_growth_data.list_name }}</u></strong>. This is due to the fact that your form 
    submissions are currently directed to this list...
</p>
```
**Status:** Hardcoded intro - should use LLM-generated narrative

#### `flow_welcome.html` (Lines 12-19)
```html
<p>
    Your welcome or nurture series offers a valuable chance to connect with your leads prior to their 
    conversion into customers...
</p>
```
**Status:** Hardcoded intro - should use LLM-generated narrative (already has `{% if welcome_flow_data.narrative %}` but fallback is hardcoded)

#### `flow_abandoned_cart.html` (Lines 12-18)
```html
<p>
    A customer adding an item to their online shopping cart and almost completing checkout is a heavy 
    indication that they are interested in purchasing your product...
</p>
```
**Status:** Hardcoded intro - should use LLM-generated narrative (already has `{% if abandoned_cart_data.narrative %}` but fallback is hardcoded)

#### `segmentation_strategy.html` (Line 17)
```html
<p>
    Below is an example segmentation strategy that aligns with our recommended approach.
</p>
```
**Status:** Hardcoded - should be dynamic or removed

#### `automation_overview.html` (Lines 15-19)
```html
<p>
    The purpose of compiling an overview of your flows is to assess whether any metrics are 
    underperforming and require attention...
</p>
```
**Status:** Hardcoded fallback - should be minimal

#### `advanced_reviews.html` (Lines 12-18)
```html
<p>
    Customer reviews and social proof are powerful tools for building trust and driving conversions...
</p>
```
**Status:** Hardcoded intro - informational section, acceptable but could be dynamic

#### `advanced_wishlist.html` (Lines 12-18)
```html
<p>
    Wishlist and price drop automations target customers who have shown strong purchase intent...
</p>
```
**Status:** Hardcoded intro - informational section, acceptable but could be dynamic

## Fixes Required

1. **Fix KAV Chart:**
   - Aggregate daily data to monthly
   - Match sample structure: bars for attributed/unattributed, line for recipients
   - Use actual monthly data, not evenly distributed

2. **Remove Hardcoded Fallbacks:**
   - Replace with minimal fallback text or LLM-generated content
   - Ensure all sections use `{% if narrative %}` with minimal fallbacks

3. **Chart Data Generation:**
   - Update `time_series.py` to aggregate to monthly intervals
   - Calculate unattributed revenue (total - attributed)
   - Include recipient data in chart

