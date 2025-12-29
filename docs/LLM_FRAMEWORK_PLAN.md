 
 # LLM Framework Integration & Cleanup Plan

## 🎯 Goals

1. **Multi-LLM Support** - Claude, ChatGPT, Gemini
2. **Framework Selection** - CrewAI vs LangChain
3. **Code Cleanup** - Remove hardcoded business logic
4. **Step-by-Step Integration** - Phased approach

---

## 📊 Framework Comparison

### CrewAI vs LangChain

| Feature | CrewAI | LangChain | Recommendation |
|---------|--------|-----------|----------------|
| **Use Case** | Multi-agent collaboration | General LLM orchestration | **LangChain** (simpler for our needs) |
| **Complexity** | Higher (agent coordination) | Lower (direct LLM calls) | **LangChain** (matches strategist's simple method) |
| **Multi-LLM** | Built-in support | Excellent abstraction | **LangChain** (better LLM abstraction) |
| **Learning Curve** | Steeper | Gentler | **LangChain** (easier to adopt) |
| **Our Needs** | One prompt per section | One prompt per section | **LangChain** (perfect fit) |

### Decision: **LangChain** ✅

**Why:**
- Strategist's method is simple (one prompt per section)
- Don't need complex agent coordination
- LangChain has excellent multi-LLM abstraction
- Better documentation and community support
- Easier to maintain

---

## 🏗️ Architecture Plan

### Multi-LLM Abstraction Layer

```
┌─────────────────────────────────────────────────────────┐
│              LLM Abstraction Layer                      │
│  (LangChain LLM Interface)                               │
│  - Claude (Anthropic)                                    │
│  - ChatGPT (OpenAI)                                      │
│  - Gemini (Google)                                       │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│            Prompt Template Engine                        │
│  - Section-specific prompts                              │
│  - Context injection (industry, benchmarks)              │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│            Data Formatter                                │
│  - Format Klaviyo data for LLM                           │
│  - Add context (industry, benchmarks, date range)        │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│            Report Service                                │
│  - Use LLM insights instead of manual logic             │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Step-by-Step Implementation Plan

### **Phase 1: Setup Multi-LLM Infrastructure** (Week 1)

#### Step 1.1: Install Dependencies
```bash
pip install langchain langchain-anthropic langchain-openai langchain-google-genai
```

#### Step 1.2: Create LLM Abstraction Layer
**File:** `api/services/llm/__init__.py`
```python
from langchain.llms.base import BaseLLM
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Literal, Optional

LLMProvider = Literal["claude", "openai", "gemini"]

class LLMService:
    """Multi-LLM service with LangChain abstraction."""
    
    def __init__(
        self,
        provider: LLMProvider = "claude",
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        self.provider = provider
        self.llm = self._create_llm(provider, model, api_key)
    
    def _create_llm(
        self,
        provider: LLMProvider,
        model: Optional[str],
        api_key: Optional[str]
    ) -> BaseLLM:
        """Create LLM instance based on provider."""
        if provider == "claude":
            return ChatAnthropic(
                model=model or "claude-sonnet-4-20250514",
                api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
                temperature=0.3
            )
        elif provider == "openai":
            return ChatOpenAI(
                model=model or "gpt-4",
                api_key=api_key or os.getenv("OPENAI_API_KEY"),
                temperature=0.3
            )
        elif provider == "gemini":
            return ChatGoogleGenerativeAI(
                model=model or "gemini-pro",
                api_key=api_key or os.getenv("GOOGLE_API_KEY"),
                temperature=0.3
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def generate_insights(
        self,
        prompt: str,
        response_format: str = "json"
    ) -> Dict[str, Any]:
        """Generate insights using configured LLM."""
        # LangChain handles async automatically
        response = await self.llm.ainvoke(prompt)
        return self._parse_response(response.content, response_format)
```

#### Step 1.3: Environment Configuration
**File:** `.env.example`
```env
# LLM Configuration
LLM_PROVIDER=claude  # claude, openai, gemini
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# Model Selection (optional, uses defaults if not set)
CLAUDE_MODEL=claude-sonnet-4-20250514
OPENAI_MODEL=gpt-4
GEMINI_MODEL=gemini-pro
```

---

### **Phase 2: Create Prompt Templates** (Week 1)

#### Step 2.1: Prompt Template System
**File:** `api/services/llm/prompts.py`
```python
from typing import Dict, Any

class PromptTemplates:
    """Prompt templates based on strategist's method."""
    
    @staticmethod
    def kav_analysis(data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """KAV analysis prompt matching strategist's format."""
        return f"""You are a marketing strategist analyzing KAV performance for {context['client_name']} 
in the {context['industry']} industry.

Date Range: {context['date_range']}

KAV Metrics:
- Total Revenue: ${data['total_revenue']:,.2f}
- Attributed Revenue: ${data['attributed_revenue']:,.2f}
- KAV Percentage: {data['kav_percentage']}%
- Flow Revenue: ${data['flow_revenue']:,.2f}
- Campaign Revenue: ${data['campaign_revenue']:,.2f}

Industry Benchmarks:
- Average KAV: {context['benchmarks']['kav_benchmark']}%

Provide strategic insights in JSON format with:
- primary_narrative: Strategic overview paragraph
- secondary_narrative: Detailed analysis paragraph
- strengths: List of 3 strengths
- opportunities: List of 3 opportunities
- campaign_flow_analysis: Analysis of campaign vs flow split
"""
    
    @staticmethod
    def flow_analysis(flow_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Flow analysis prompt."""
        return f"""Analyze {flow_data['flow_name']} flow performance for {context['client_name']}:

Metrics:
- Open Rate: {flow_data['open_rate']}% (Industry avg: {context['benchmarks']['open_rate']}%)
- Click Rate: {flow_data['click_rate']}% (Industry avg: {context['benchmarks']['click_rate']}%)
- Revenue: ${flow_data['revenue']:,.2f}

Provide insights in JSON format with:
- performance_summary: How performance compares to benchmarks
- optimization_opportunities: Specific recommendations
- strategic_insights: Why this matters
"""
    
    # Add more section prompts...
```

#### Step 2.2: Data Formatter
**File:** `api/services/llm/formatter.py`
```python
class LLMDataFormatter:
    """Format Klaviyo data for LLM consumption."""
    
    @staticmethod
    def format_kav_data(
        kav_data: Dict[str, Any],
        client_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format KAV data with context."""
        return {
            "total_revenue": kav_data.get("totals", {}).get("total_revenue", 0),
            "attributed_revenue": kav_data.get("totals", {}).get("attributed_revenue", 0),
            "kav_percentage": kav_data.get("totals", {}).get("kav_percentage", 0),
            "flow_revenue": kav_data.get("totals", {}).get("flow_revenue", 0),
            "campaign_revenue": kav_data.get("totals", {}).get("campaign_revenue", 0),
        }
    
    @staticmethod
    def format_context(
        client_name: str,
        industry: str,
        date_range: str,
        benchmarks: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format context for prompts."""
        return {
            "client_name": client_name,
            "industry": industry,
            "date_range": date_range,
            "benchmarks": benchmarks
        }
```

---

### **Phase 3: Replace Manual Logic** (Week 2)

#### Step 3.1: Replace KAV Narrative
**File:** `api/services/report.py`
```python
# OLD:
from .narrative import StrategyNarrativeEngine
narrative_engine = StrategyNarrativeEngine()
strategic_narratives = narrative_engine.generate_kav_narrative(...)

# NEW:
from .llm import LLMService
from .llm.prompts import PromptTemplates
from .llm.formatter import LLMDataFormatter

llm_service = LLMService(provider=os.getenv("LLM_PROVIDER", "claude"))
formatter = LLMDataFormatter()

# Format data
kav_data_formatted = formatter.format_kav_data(kav_data, client_context)
context = formatter.format_context(client_name, industry, date_range, benchmarks)

# Generate prompt
prompt = PromptTemplates.kav_analysis(kav_data_formatted, context)

# Get insights
strategic_narratives = await llm_service.generate_insights(prompt)
```

#### Step 3.2: Replace Flow Analysis
```python
# OLD:
from .klaviyo.flows.lifecycle import FlowLifecycleAnalyzer
analyzer = FlowLifecycleAnalyzer()
flow_analysis = analyzer.analyze_welcome_series(...)

# NEW:
prompt = PromptTemplates.flow_analysis(flow_data, context)
flow_insights = await llm_service.generate_insights(prompt)
```

#### Step 3.3: Replace Campaign Insights
```python
# OLD: Manual campaign insights generation

# NEW:
prompt = PromptTemplates.campaign_analysis(campaign_data, context)
campaign_insights = await llm_service.generate_insights(prompt)
```

---

### **Phase 4: Code Cleanup** (Week 2-3)

#### Files to Remove/Deprecate:
1. ❌ `api/services/narrative.py` - Replace with LLM
2. ❌ `api/services/strategic_decision_engine.py` - Replace with LLM
3. ❌ `api/services/multi_agent_framework.py` - Replace with LLM
4. ⚠️ `api/services/klaviyo/flows/lifecycle.py` - Simplify, use LLM for insights
5. ⚠️ `api/services/klaviyo/segmentation/analyzer.py` - Simplify, use LLM

#### Hardcoded Logic to Remove:

**In `api/services/report.py`:**
- `_generate_revenue_insights()` - Hardcoded insights
- Manual benchmark comparisons
- Hardcoded narrative generation

**In `api/services/klaviyo/revenue/time_series.py`:**
- Complex KAV calculations (keep simple data extraction)
- Revenue estimation logic (let LLM interpret)

**In `api/services/klaviyo/flows/lifecycle.py`:**
- Hardcoded performance narratives
- Manual optimization recommendations

---

## 🧹 Cleanup Checklist

### Files to Clean Up:

1. **`api/services/narrative.py`** ❌
   - **Action:** Delete after migrating to LLM
   - **Lines:** ~200 lines of hardcoded logic

2. **`api/services/strategic_decision_engine.py`** ❌
   - **Action:** Delete after migrating to LLM
   - **Lines:** ~400 lines of prioritization logic

3. **`api/services/multi_agent_framework.py`** ❌
   - **Action:** Delete after migrating to LLM
   - **Lines:** ~500 lines of manual analysis

4. **`api/services/klaviyo/flows/lifecycle.py`** ⚠️
   - **Action:** Simplify, remove hardcoded narratives
   - **Keep:** Flow identification logic
   - **Remove:** Performance narratives, optimization recommendations

5. **`api/services/klaviyo/segmentation/analyzer.py`** ⚠️
   - **Action:** Simplify, use LLM for insights
   - **Keep:** Segmentation detection
   - **Remove:** Hardcoded recommendations

6. **`api/services/report.py`** 🔄
   - **Action:** Replace manual insight generation with LLM calls
   - **Keep:** Template rendering, data preparation
   - **Remove:** `_generate_revenue_insights()`, manual narratives

---

## 📦 New File Structure

```
api/services/
├── llm/
│   ├── __init__.py          # LLMService (multi-LLM abstraction)
│   ├── prompts.py            # Prompt templates (strategist's method)
│   ├── formatter.py         # Data formatting for LLM
│   └── config.py             # LLM configuration
├── klaviyo/                  # ✅ Keep (data extraction)
│   ├── client.py
│   ├── metrics/
│   ├── campaigns/
│   ├── flows/
│   └── ...
├── report.py                 # 🔄 Update (use LLM instead of manual)
└── benchmark.py              # ✅ Keep (benchmark data)
```

---

## 🔧 Implementation Steps

### **Week 1: Infrastructure Setup**

**Day 1-2: Multi-LLM Layer**
- [ ] Install LangChain dependencies
- [ ] Create `api/services/llm/__init__.py` with LLMService
- [ ] Test with Claude (existing)
- [ ] Test with OpenAI
- [ ] Test with Gemini

**Day 3-4: Prompt Templates**
- [ ] Create `api/services/llm/prompts.py`
- [ ] Add KAV analysis prompt (based on strategist's method)
- [ ] Add flow analysis prompt
- [ ] Add campaign analysis prompt
- [ ] Add list growth prompt

**Day 5: Data Formatter**
- [ ] Create `api/services/llm/formatter.py`
- [ ] Format KAV data
- [ ] Format flow data
- [ ] Format context (industry, benchmarks)

---

### **Week 2: Integration & Cleanup**

**Day 1-2: Replace KAV Section**
- [ ] Update `_prepare_kav_data()` in `report.py`
- [ ] Replace `StrategyNarrativeEngine` with LLM
- [ ] Test KAV section with LLM
- [ ] Compare output with manual version

**Day 3-4: Replace Flow Section**
- [ ] Update flow analysis to use LLM
- [ ] Replace `FlowLifecycleAnalyzer` narratives
- [ ] Test flow sections
- [ ] Remove hardcoded flow narratives

**Day 5: Replace Campaign Section**
- [ ] Update campaign analysis to use LLM
- [ ] Remove manual campaign insights
- [ ] Test campaign section

---

### **Week 3: Cleanup & Optimization**

**Day 1-2: Remove Deprecated Files**
- [ ] Delete `narrative.py`
- [ ] Delete `strategic_decision_engine.py`
- [ ] Delete `multi_agent_framework.py`
- [ ] Update imports across codebase

**Day 3-4: Simplify Remaining Files**
- [ ] Simplify `flows/lifecycle.py` (remove narratives)
- [ ] Simplify `segmentation/analyzer.py` (remove recommendations)
- [ ] Clean up `report.py` (remove manual insights)

**Day 5: Testing & Validation**
- [ ] Test full report generation
- [ ] Compare LLM insights vs manual
- [ ] Optimize prompts based on results
- [ ] Document changes

---

## 🎯 Success Metrics

1. **Code Reduction:**
   - Remove ~1,000+ lines of hardcoded logic
   - Simplify remaining code
   - Better maintainability

2. **Flexibility:**
   - Support 3+ LLM providers
   - Easy to switch providers
   - Easy to add new sections

3. **Quality:**
   - Insights match strategist's quality
   - Industry-specific analysis
   - Actionable recommendations

---

## 📝 Configuration Example

**File:** `config/llm_config.py`
```python
LLM_CONFIG = {
    "default_provider": "claude",
    "providers": {
        "claude": {
            "class": "ChatAnthropic",
            "model": "claude-sonnet-4-20250514",
            "temperature": 0.3,
            "api_key_env": "ANTHROPIC_API_KEY"
        },
        "openai": {
            "class": "ChatOpenAI",
            "model": "gpt-4",
            "temperature": 0.3,
            "api_key_env": "OPENAI_API_KEY"
        },
        "gemini": {
            "class": "ChatGoogleGenerativeAI",
            "model": "gemini-pro",
            "temperature": 0.3,
            "api_key_env": "GOOGLE_API_KEY"
        }
    }
}
```

---

## 🚀 Quick Start Implementation

### Step 1: Install Dependencies
```bash
pip install langchain langchain-anthropic langchain-openai langchain-google-genai
```

### Step 2: Create LLM Service
```python
# api/services/llm/__init__.py
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import os

class LLMService:
    def __init__(self, provider="claude"):
        if provider == "claude":
            self.llm = ChatAnthropic(
                model="claude-sonnet-4-20250514",
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
        elif provider == "openai":
            self.llm = ChatOpenAI(
                model="gpt-4",
                api_key=os.getenv("OPENAI_API_KEY")
            )
        elif provider == "gemini":
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-pro",
                api_key=os.getenv("GOOGLE_API_KEY")
            )
    
    async def generate(self, prompt: str) -> str:
        response = await self.llm.ainvoke(prompt)
        return response.content
```

### Step 3: Test with One Section
```python
# Test KAV section
llm = LLMService(provider="claude")
prompt = PromptTemplates.kav_analysis(kav_data, context)
insights = await llm.generate(prompt)
```

---

## ✅ Next Actions

1. **Install LangChain** - Add to requirements.txt
2. **Create LLM service** - Multi-LLM abstraction
3. **Create prompt templates** - Based on strategist's method
4. **Test with KAV section** - Proof of concept
5. **Migrate section by section** - Gradual replacement
6. **Remove deprecated files** - Clean up codebase

---

**Key Decision:** Use **LangChain** for multi-LLM abstraction. It's simpler, better documented, and perfect for our one-prompt-per-section approach.

