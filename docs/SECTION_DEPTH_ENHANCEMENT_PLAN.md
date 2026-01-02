# Section Depth Enhancement Plan

## 📊 **CURRENT STATE vs SAMPLE AUDITS**

### Sample Audits (DOCX):
- **410 paragraphs** total
- **15 tables** per audit
- **2-3 pages per section** with multiple subsections
- **Detailed "Areas of Opportunity" tables**
- **Year-over-year comparisons**
- **"Growing Your KAV" recommendation frameworks**

### Our Generated Reports:
- **~1 page per section**
- **Single paragraph intros**
- **Missing detailed subsections**
- **Missing "Areas of Opportunity" tables**
- **Missing comprehensive recommendation frameworks**

---

## 🎯 **ENHANCEMENT PLAN BY SECTION**

### 1. **KAV Analysis** (Currently: ~1 page → Target: 2-3 pages)

#### Add Subsections:
- ✅ "Growth Overview & Insights" (2-3 paragraphs)
- ✅ "Campaigns vs. Flows Breakdown" (detailed comparison table + narrative)
- ✅ "Flow Performance Insights" (dedicated paragraph)
- ✅ "Campaign Performance Insights" (dedicated paragraph)
- ✅ "What This Means for KAV Performance" (2-3 bullet points with analysis)

#### Add "Growing Your KAV" Section:
- ✅ "Reignite Campaign Performance" (Objective + 3 bullet points)
- ✅ "Strengthen and Expand Flow Strategy" (2 paragraphs)
- ✅ "Set the Foundation for Scalable Growth" (detailed paragraph)

#### Enhance LLM Prompt:
- Request **5-7 paragraphs** of analysis (not 1-2)
- Include **year-over-year comparisons** if data available
- Generate **specific action items** with timelines

---

### 2. **List Growth** (Currently: ~1 page → Target: 1-2 pages)

#### Add Subsections:
- ✅ "Email List Growth Overview" (detailed paragraph with specific numbers)
- ✅ "Growth Drivers" subsection:
  - Multiple bullet points explaining each source
  - Specific numbers and percentages
- ✅ "Attrition Sources" subsection:
  - Detailed breakdown of where losses come from
  - "Manual Suppressions" with explanation
  - "Subscriber Opt-Outs" analysis

#### Enhance LLM Prompt:
- Analyze **signup sources** in detail
- Explain **churn patterns** with specific numbers
- Provide **growth acceleration recommendations**

---

### 3. **Data Capture** (Currently: ~1-2 pages → Target: 2 pages)

#### Add "Areas of Opportunity" Section:
- ✅ "Optimise Desktop Form" (detailed bullet points)
- ✅ "Optimise Thank You Screen" (detailed recommendations)
- ✅ "Progressive Profiling" (detailed explanation, not just list)
- ✅ "Flyout Forms" (detailed explanation, not just list)

#### Enhance LLM Prompt:
- Generate **specific optimization recommendations per form type**
- Include **implementation steps** for each recommendation
- Provide **expected impact** for each optimization

---

### 4. **Automation Performance Overview** (Currently: ~1 page → Target: 1-2 pages)

#### Add Subsections:
- ✅ "Flow Performance Insights" (detailed paragraph)
- ✅ "Campaign Performance Insights" (detailed paragraph)
- ✅ "What This Means for KAV Performance" (detailed analysis)

#### Enhance LLM Prompt:
- Generate **separate insights** for flows vs campaigns
- Provide **strategic analysis** connecting performance to KAV

---

### 5. **Welcome Series / Nurture** (Currently: ~1 page → Target: 1-2 pages)

#### Add "Areas of Opportunity" Table:
- ✅ Table format with columns:
  - Optimization/Expansion Opportunity
  - Recommended Action / Quick Fix
  - Why it Matters (Impact & Rationale)
- ✅ Multiple rows with detailed recommendations

#### Enhance LLM Prompt:
- Generate **structured opportunity table** data
- Include **specific implementation steps**
- Provide **benchmark comparisons** in narrative

---

### 6. **Abandoned Cart** (Currently: ~1 page → Target: 1-2 pages)

#### Add "Areas of Opportunity" Table:
- ✅ Same table structure as Welcome Series
- ✅ Cart recovery specific recommendations
- ✅ Timing optimization recommendations

---

### 7. **Browse Abandonment** (Currently: ~1 page → Target: 1-2 pages)

#### Add "Areas of Opportunity" Table:
- ✅ Browse-specific recommendations
- ✅ Product recommendation strategies
- ✅ Re-engagement tactics

---

### 8. **Post Purchase** (Currently: ~1 page → Target: 1-2 pages)

#### Add "Areas of Opportunity" Table:
- ✅ Post-purchase specific recommendations
- ✅ Cross-sell/upsell strategies
- ✅ Review collection strategies

---

## 🔧 **IMPLEMENTATION STEPS**

### Step 1: Enhance LLM Prompts
- **File**: `api/services/llm/prompts/`
- **Action**: Update all section prompts to request:
  - 5-7 paragraphs of analysis (not 1-2)
  - Multiple subsections
  - "Areas of Opportunity" structured data
  - Year-over-year comparisons
  - Specific action items with timelines

### Step 2: Update Templates
- **Files**: `templates/sections/*.html`
- **Action**: Add subsections for:
  - "Growth Overview & Insights"
  - "Performance Insights" (separate for flows/campaigns)
  - "Areas of Opportunity" tables
  - "Growing Your KAV" type recommendation sections

### Step 3: Add "Areas of Opportunity" Table Component
- **File**: `templates/sections/_opportunity_table.html` (new)
- **Action**: Create reusable table component with columns:
  - Optimization/Expansion Opportunity
  - Recommended Action / Quick Fix
  - Why it Matters (Impact & Rationale)

### Step 4: Enhance Data Preparation
- **Files**: `api/services/report/preparers/*.py`
- **Action**: Structure LLM output to include:
  - Multiple narrative sections
  - Opportunity table data
  - Year-over-year comparison data (if available)

---

## 📋 **PRIORITY ORDER**

1. **HIGH PRIORITY** (Most visible sections):
   - KAV Analysis (2-3 pages)
   - Welcome Series (1-2 pages)
   - Abandoned Cart (1-2 pages)

2. **MEDIUM PRIORITY**:
   - List Growth (1-2 pages)
   - Data Capture (2 pages)
   - Automation Overview (1-2 pages)

3. **LOW PRIORITY** (Already detailed):
   - Browse Abandonment
   - Post Purchase
   - Campaign Performance

---

## ✅ **SUCCESS METRICS**

- Each major section should have **2-3 pages** of content
- Each section should have **3-5 subsections**
- Each section should have **1 "Areas of Opportunity" table**
- Total report should be **30-40 pages** (currently ~18 pages)

