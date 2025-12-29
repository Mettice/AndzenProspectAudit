# Existing LLM Implementation Analysis

## ✅ What Already Exists

### 1. **AgenticAnalysisFramework** (`api/services/analysis.py`)
- ✅ **Uses Claude (Anthropic API)** - Already integrated!
- ✅ **5-Agent Pipeline:**
  1. Data Processing Agent
  2. Benchmark Comparison Agent
  3. Pattern Recognition Agent
  4. Strategic Analysis Agent
  5. Report Synthesis Agent
- ✅ **Claude Integration:** `_call_claude()` method with proper async handling
- ✅ **JSON Parsing:** `_parse_json_response()` for structured outputs

### 2. **MultiAgentFramework** (`api/services/multi_agent_framework.py`)
- ❌ **Manual Logic** - Not using LLM
- Uses hardcoded analysis logic
- Currently used in `_prepare_strategic_recommendations()`

---

## 🔍 Current Usage

### Where It's Used:
- `AgenticAnalysisFramework` - **NOT currently used in report generation**
- `MultiAgentFramework` - Used in `report.py` for strategic recommendations (manual logic)

### Where It Should Be Used:
- **KAV Analysis** - Currently uses `StrategyNarrativeEngine` (manual)
- **Flow Analysis** - Currently uses `FlowLifecycleAnalyzer` (manual)
- **Campaign Analysis** - Currently uses manual insights
- **Strategic Recommendations** - Currently uses `MultiAgentFramework` (manual)

---

## 🎯 Gap Analysis

### Current Approach (Too Complex):
```
AgenticAnalysisFramework:
  Agent 1 → Process Data
  Agent 2 → Compare Benchmarks
  Agent 3 → Find Patterns
  Agent 4 → Generate Insights
  Agent 5 → Synthesize Report
```
- **5 separate Claude calls** per report
- Complex pipeline
- Not section-by-section like strategist

### Strategist's Approach (Simple):
```
For each section:
  Data + Context → One Claude Prompt → Insights
```
- **One prompt per section**
- Simple, direct
- Matches strategist's ChatGPT workflow

---

## 🔄 What Needs to Change

### Option 1: Simplify Existing Framework (Recommended)
**Modify `AgenticAnalysisFramework` to work section-by-section:**

```python
class AgenticAnalysisFramework:
    async def generate_section_insights(
        self,
        section: str,  # "kav", "flows", "campaigns", etc.
        data: Dict[str, Any],
        context: Dict[str, Any]  # industry, benchmarks, date_range
    ) -> Dict[str, Any]:
        """
        Generate insights for ONE section using strategist's method.
        One prompt, one response, done.
        """
        prompt = self._build_section_prompt(section, data, context)
        response = await self._call_claude(prompt, max_tokens=4000)
        return self._parse_json_response(response)
```

### Option 2: Create New Simple Service
**Create `api/services/llm/strategist_service.py`:**
- Simple wrapper around Claude
- One method per section
- Matches strategist's exact workflow

---

## 📋 Implementation Plan

### Step 1: Simplify AgenticAnalysisFramework
- Add `generate_section_insights()` method
- Create prompt templates per section (based on strategist's method)
- Keep existing `_call_claude()` and `_parse_json_response()` methods

### Step 2: Create Section-Specific Prompts
Based on `StrategistChat.md`, create prompts for:
- KAV Analysis
- Campaign vs Flows
- Email vs SMS
- List Growth
- Flow Performance (Welcome, AC, Browse, Post-Purchase)
- Campaign Performance
- Strategic Recommendations

### Step 3: Replace Manual Logic
In `api/services/report.py`:
- Replace `StrategyNarrativeEngine` → `AgenticAnalysisFramework.generate_section_insights("kav", ...)`
- Replace `FlowLifecycleAnalyzer` → `AgenticAnalysisFramework.generate_section_insights("flows", ...)`
- Replace manual campaign insights → `AgenticAnalysisFramework.generate_section_insights("campaigns", ...)`

---

## 🎯 Key Differences

| Aspect | Current (AgenticAnalysisFramework) | Strategist's Method | What We Need |
|--------|-----------------------------------|---------------------|--------------|
| **Approach** | 5-agent pipeline | One prompt per section | One prompt per section |
| **Complexity** | High (5 Claude calls) | Low (1 call per section) | Low |
| **Usage** | Not used in reports | Used manually | Use in reports |
| **Structure** | Pipeline (Agent 1→2→3→4→5) | Independent sections | Independent sections |

---

## ✅ What to Keep

1. **Claude Integration** - `_call_claude()` method works perfectly
2. **JSON Parsing** - `_parse_json_response()` handles Claude responses
3. **Async Support** - Already async/await compatible
4. **Error Handling** - Already has try/catch

## 🔄 What to Change

1. **Add section-by-section method** - `generate_section_insights()`
2. **Create prompt templates** - Based on strategist's method
3. **Simplify approach** - One prompt per section, not 5-agent pipeline
4. **Use in report generation** - Replace manual logic with LLM calls

---

## 🚀 Quick Implementation

### Add to `AgenticAnalysisFramework`:

```python
async def generate_section_insights(
    self,
    section: str,
    data: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate insights for a specific section using strategist's method.
    
    Args:
        section: "kav", "flows", "campaigns", "list_growth", etc.
        data: Section-specific data
        context: Industry, benchmarks, date_range, client_name
    
    Returns:
        Dict with insights matching strategist's format
    """
    from .llm.prompts import SECTION_PROMPTS
    
    prompt_template = SECTION_PROMPTS.get(section)
    if not prompt_template:
        return {"error": f"No prompt template for section: {section}"}
    
    # Format prompt with data and context
    prompt = prompt_template.format(
        client_name=context.get("client_name", "Client"),
        industry=context.get("industry", "retail"),
        date_range=context.get("date_range", ""),
        **data,
        **context.get("benchmarks", {})
    )
    
    # Call Claude
    response = await self._call_claude(prompt, max_tokens=4000)
    return self._parse_json_response(response)
```

---

## 📝 Next Steps

1. **Review existing `AgenticAnalysisFramework`** - Understand current implementation
2. **Add section-by-section method** - Simplify to match strategist's approach
3. **Create prompt templates** - Based on `StrategistChat.md` examples
4. **Test with KAV section** - Replace manual narrative with LLM
5. **Migrate other sections** - One by one

---

**Key Insight:** We already have Claude integration! We just need to simplify it to match the strategist's one-prompt-per-section method instead of the complex 5-agent pipeline.

