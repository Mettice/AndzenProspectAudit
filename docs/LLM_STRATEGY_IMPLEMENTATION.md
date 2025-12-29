# LLM-Powered Audit Strategy - Implementation Plan

## 🎯 Core Strategy (Based on Strategist's Method)

**The strategist's process:**
1. Pull raw data/metrics from Klaviyo (screenshots or API)
2. Feed data to ChatGPT with context (industry, benchmarks, date range)
3. Get strategic insights back
4. Format insights into Morrison-style report

**Our approach:**
1. ✅ **Data Extraction** - Pull all metrics from Klaviyo API (already working)
2. 🔄 **Data Formatting** - Format data for LLM with context (industry, benchmarks, date range)
3. ❌ **LLM Integration** - Use ChatGPT to generate insights (MISSING - this is the gap)
4. ✅ **Report Generation** - Use existing templates/charts/style (already working)

---

## 📋 What We Keep

### ✅ Templates & Styling
- All existing templates in `templates/` folder
- Morrison-style formatting (green headers, charts, tables)
- PDF/HTML generation
- Chart.js visualizations
- Page structure (18-40 pages, varies by client)

### ✅ Data Extraction
- Klaviyo API integration (already working)
- All metric extraction (revenue, flows, campaigns, etc.)
- Date range handling
- Timezone support

### ✅ Report Structure
- Cover page
- KAV Analysis
- List Growth
- Data Capture
- Automation Overview
- Flow deep dives (Welcome, Abandoned Cart, Browse, Post-Purchase)
- Campaign Performance
- Segmentation Strategy
- Strategic Recommendations

---

## 🔄 What We Replace

### ❌ Manual Insight Generation → LLM-Powered Insights

**Current (Manual Logic):**
- `StrategyNarrativeEngine` - hardcoded narrative logic
- `FlowLifecycleAnalyzer` - manual analysis
- `SegmentationAnalyzer` - manual recommendations
- `StrategicDecisionEngine` - manual prioritization
- Hardcoded benchmark comparisons

**New (LLM-Powered):**
- Format data + context → ChatGPT API
- Get strategic insights back
- Insert into existing templates

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│              DATA EXTRACTION (✅ Complete)              │
│  Klaviyo API → Raw Metrics → Structured Data            │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│            DATA FORMATTING (🔄 To Build)                │
│  Structured Data → LLM-Friendly Format                  │
│  + Add Context: industry, benchmarks, date range        │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│            LLM INTEGRATION (❌ To Build)                 │
│  Formatted Data → Prompt Templates → ChatGPT API        │
│  → Strategic Insights (JSON)                            │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│         REPORT GENERATION (✅ Complete)                  │
│  LLM Insights + Metrics → Templates → PDF/HTML           │
└─────────────────────────────────────────────────────────┘
```

---

## 📝 Implementation Steps

### Phase 1: LLM Service (Week 1)

**File:** `api/services/llm/__init__.py`
```python
class LLMService:
    """Wrapper for ChatGPT/OpenAI API"""
    
    async def generate_insights(
        self,
        section: str,  # "kav", "flows", "campaigns", etc.
        data: Dict[str, Any],
        context: Dict[str, Any]  # industry, benchmarks, date_range
    ) -> Dict[str, Any]:
        """
        Generate strategic insights using ChatGPT.
        
        Format matches strategist's method:
        - Pull data
        - Add context (industry, benchmarks)
        - Prompt ChatGPT
        - Get insights back
        """
```

**File:** `api/services/llm/prompts.py`
```python
class PromptTemplates:
    """Prompt templates for each report section"""
    
    KAV_PROMPT = """
    You are a marketing strategist analyzing Klaviyo performance for {client_name} 
    in the {industry} industry.
    
    Date Range: {date_range}
    
    KAV Analysis:
    - Total Revenue: ${total_revenue:,.2f}
    - Attributed Revenue: ${attributed_revenue:,.2f}
    - KAV Percentage: {kav_percentage}%
    - Flow Revenue: ${flow_revenue:,.2f}
    - Campaign Revenue: ${campaign_revenue:,.2f}
    
    Industry Benchmarks:
    - Average KAV: {kav_benchmark}%
    - Average Flow Open Rate: {flow_open_rate_benchmark}%
    
    Provide strategic insights:
    1. How does this KAV percentage compare to industry benchmarks?
    2. What does the flow vs campaign split indicate?
    3. What are the top 3 opportunities for improvement?
    4. What are the top 3 strengths?
    
    Format your response as JSON with:
    - primary_narrative: Strategic overview paragraph
    - secondary_narrative: Detailed analysis paragraph
    - strengths: List of 3 strengths
    - opportunities: List of 3 opportunities
    """
    
    FLOW_PROMPT = """
    Analyze {flow_name} flow performance for {client_name}:
    
    Metrics:
    - Open Rate: {open_rate}% (Industry avg: {benchmark_open}%)
    - Click Rate: {click_rate}% (Industry avg: {benchmark_click}%)
    - Revenue: ${revenue:,.2f}
    
    Provide insights on:
    1. Performance vs benchmarks
    2. Optimization opportunities
    3. Strategic recommendations
    
    Format as JSON with narrative and recommendations.
    """
```

### Phase 2: Data Formatter (Week 1)

**File:** `api/services/llm/formatter.py`
```python
class LLMDataFormatter:
    """Format Klaviyo data for LLM consumption"""
    
    def format_for_kav_analysis(
        self,
        kav_data: Dict[str, Any],
        client_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format KAV data with context for LLM.
        
        Returns:
        {
            "client_name": "...",
            "industry": "...",
            "date_range": "...",
            "metrics": {
                "total_revenue": 8738532.03,
                "attributed_revenue": 3313157.35,
                "kav_percentage": 37.9,
                ...
            },
            "benchmarks": {
                "kav_benchmark": 30.0,
                ...
            }
        }
        """
    
    def format_for_flow_analysis(
        self,
        flow_data: Dict[str, Any],
        benchmarks: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format flow data with benchmarks for LLM"""
```

### Phase 3: Replace Manual Logic (Week 2)

**Replace in `api/services/report.py`:**
```python
# OLD:
from .narrative import StrategyNarrativeEngine
narrative_engine = StrategyNarrativeEngine()
strategic_narratives = narrative_engine.generate_kav_narrative(...)

# NEW:
from .llm import LLMService
llm_service = LLMService()
strategic_narratives = await llm_service.generate_insights(
    section="kav",
    data=formatted_kav_data,
    context=client_context
)
```

### Phase 4: Section-by-Section Migration (Week 2-3)

1. **KAV Analysis** - Replace `StrategyNarrativeEngine.generate_kav_narrative()`
2. **Flow Analysis** - Replace `FlowLifecycleAnalyzer` with LLM
3. **Campaign Analysis** - Replace manual insights with LLM
4. **List Growth** - Replace manual analysis with LLM
5. **Strategic Recommendations** - Replace `StrategicDecisionEngine` with LLM

---

## 📊 Prompt Strategy (Based on Strategist's Method)

### Pattern from StrategistChat.md:

**Input:**
- Raw metrics/data
- Industry context
- Benchmarks
- Date range

**Prompt Structure:**
```
You are a marketing strategist analyzing [section] for [client] in [industry].

Date Range: [range]

[Section] Data:
- Metric 1: [value] (Benchmark: [benchmark])
- Metric 2: [value] (Benchmark: [benchmark])
...

Provide strategic insights:
1. [Question 1]
2. [Question 2]
3. [Question 3]

Format as JSON with [structure].
```

**Output:**
- Strategic narrative
- Strengths
- Opportunities
- Recommendations

---

## 🎨 Report Format (Keep Existing)

### Sections (from `templates/audit_report.html`):
1. Cover Page
2. KAV Analysis (Pages 2-3)
3. List Growth (Page 4)
4. Data Capture (Pages 5-6)
5. Automation Overview (Page 7)
6. Welcome Series (Page 8)
7. Abandoned Cart (Pages 9-10)
8. Browse Abandonment (Page 11)
9. Post Purchase (Pages 12-13)
10. Reviews (Page 14)
11. Wishlist (Pages 15-16)
12. Campaign Performance (Page 17)
13. Segmentation Strategy (Page 18)
14. Strategic Recommendations (Page 19+)

**Note:** Reports vary 35-40 pages depending on client/industry. Some sections may be longer/shorter.

---

## 🔧 Technical Implementation

### 1. LLM Service Setup

**Dependencies:**
```python
# requirements.txt
openai>=1.0.0
# or
anthropic>=0.18.0  # for Claude
```

**Configuration:**
```python
# config.py
LLM_PROVIDER = "openai"  # or "anthropic"
LLM_MODEL = "gpt-4"  # or "gpt-3.5-turbo" or "claude-3-opus"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```

### 2. Prompt Template System

**File:** `api/services/llm/prompts.py`
- One prompt template per report section
- Placeholders for data and context
- JSON output format specification

### 3. Data Formatting

**File:** `api/services/llm/formatter.py`
- Convert API data to LLM-friendly format
- Add industry benchmarks
- Include date range context
- Structure for prompt injection

### 4. Integration Points

**Replace in:**
- `api/services/report.py` - `_prepare_kav_data()`
- `api/services/report.py` - `_prepare_automation_data()`
- `api/services/report.py` - `_prepare_flow_data()`
- `api/services/report.py` - `_prepare_strategic_recommendations()`

---

## 📈 Expected Results

### Before (Manual Logic):
- Hardcoded narratives
- Limited flexibility
- Generic insights
- Difficult to customize

### After (LLM-Powered):
- Dynamic, contextual insights
- Matches strategist's method
- Industry-specific analysis
- Easy to customize prompts

---

## 🚀 Quick Start Implementation

### Step 1: Create LLM Service
```python
# api/services/llm/__init__.py
import openai
from typing import Dict, Any

class LLMService:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
    
    async def generate_insights(self, prompt: str) -> Dict[str, Any]:
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
```

### Step 2: Create Prompt Template
```python
# api/services/llm/prompts.py
KAV_PROMPT = """
You are a marketing strategist analyzing KAV performance for {client_name} 
in the {industry} industry.

Date Range: {date_range}

KAV Metrics:
- Total Revenue: ${total_revenue:,.2f}
- Attributed Revenue: ${attributed_revenue:,.2f}
- KAV Percentage: {kav_percentage}%
- Flow Revenue: ${flow_revenue:,.2f}
- Campaign Revenue: ${campaign_revenue:,.2f}

Industry Benchmarks:
- Average KAV: {kav_benchmark}%

Provide strategic insights in JSON format with:
- primary_narrative: Strategic overview
- secondary_narrative: Detailed analysis
- strengths: List of 3 strengths
- opportunities: List of 3 opportunities
"""
```

### Step 3: Replace in Report Service
```python
# In api/services/report.py
from .llm import LLMService
from .llm.prompts import KAV_PROMPT

llm_service = LLMService(api_key=os.getenv("OPENAI_API_KEY"))

# Replace manual narrative generation
prompt = KAV_PROMPT.format(
    client_name=client_name,
    industry=industry,
    date_range=date_range,
    total_revenue=kav_data["totals"]["total_revenue"],
    attributed_revenue=kav_data["totals"]["attributed_revenue"],
    kav_percentage=kav_data["totals"]["kav_percentage"],
    flow_revenue=kav_data["totals"]["flow_revenue"],
    campaign_revenue=kav_data["totals"]["campaign_revenue"],
    kav_benchmark=benchmarks["kav"]["average"]
)

insights = await llm_service.generate_insights(prompt)
```

---

## ✅ Success Criteria

1. **Insights match strategist's quality** - Strategic, contextual, actionable
2. **Reports maintain Morrison format** - Same structure, charts, styling
3. **Variable page length** - 35-40 pages depending on client
4. **Industry-specific** - Insights adapt to industry context
5. **Benchmark comparisons** - LLM compares to industry benchmarks
6. **No manual logic** - All insights from LLM, not hardcoded

---

## 🎯 Next Steps

1. **Set up LLM service** - Choose provider (OpenAI/Anthropic), get API key
2. **Create prompt templates** - One per section, based on strategist's method
3. **Build data formatter** - Convert API data to LLM-friendly format
4. **Test with one section** - Start with KAV analysis
5. **Migrate section by section** - Replace manual logic gradually
6. **Validate output** - Compare LLM insights to strategist's manual insights

---

**Key Insight:** We're not building a complex analysis engine. We're building a simple LLM integration layer that replicates the strategist's ChatGPT workflow. Data + Context + LLM = Strategic Insights.

