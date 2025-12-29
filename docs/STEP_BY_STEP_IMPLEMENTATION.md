# Step-by-Step Implementation Guide

## 🎯 Overview

**Goal:** Replace hardcoded business logic with LLM-powered insights using LangChain for multi-LLM support.

**Timeline:** 3 weeks
**Approach:** Incremental, test as we go

---

## 📅 Week 1: Infrastructure Setup

### **Day 1: Install & Setup LangChain**

#### Step 1.1: Update requirements.txt
```bash
# Add to requirements.txt
langchain>=0.1.0
langchain-anthropic>=0.1.0
langchain-openai>=0.1.0
langchain-google-genai>=0.1.0
```

#### Step 1.2: Create LLM Service Structure
```bash
mkdir -p api/services/llm
touch api/services/llm/__init__.py
touch api/services/llm/prompts.py
touch api/services/llm/formatter.py
touch api/services/llm/config.py
```

#### Step 1.3: Create Multi-LLM Service
**File:** `api/services/llm/__init__.py`
```python
"""Multi-LLM service using LangChain abstraction."""
import os
from typing import Dict, Any, Optional, Literal
import json
import logging

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)

LLMProvider = Literal["claude", "openai", "gemini"]


class LLMService:
    """
    Multi-LLM service with LangChain abstraction.
    
    Supports Claude, OpenAI, and Gemini with unified interface.
    """
    
    def __init__(
        self,
        provider: LLMProvider = "claude",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.3
    ):
        """
        Initialize LLM service.
        
        Args:
            provider: LLM provider ("claude", "openai", "gemini")
            model: Model name (uses default if not provided)
            api_key: API key (uses env var if not provided)
            temperature: Temperature for generation (0.3 for consistent analysis)
        """
        self.provider = provider
        self.temperature = temperature
        self.llm = self._create_llm(provider, model, api_key)
    
    def _create_llm(
        self,
        provider: LLMProvider,
        model: Optional[str],
        api_key: Optional[str]
    ):
        """Create LLM instance based on provider."""
        if provider == "claude":
            return ChatAnthropic(
                model=model or "claude-sonnet-4-20250514",
                api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
                temperature=self.temperature
            )
        elif provider == "openai":
            return ChatOpenAI(
                model=model or "gpt-4",
                api_key=api_key or os.getenv("OPENAI_API_KEY"),
                temperature=self.temperature
            )
        elif provider == "gemini":
            return ChatGoogleGenerativeAI(
                model=model or "gemini-pro",
                api_key=api_key or os.getenv("GOOGLE_API_KEY"),
                temperature=self.temperature
            )
        else:
            raise ValueError(f"Unknown provider: {provider}. Use 'claude', 'openai', or 'gemini'")
    
    async def generate_insights(
        self,
        prompt: str,
        response_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Generate insights using configured LLM.
        
        Args:
            prompt: Prompt string
            response_format: Expected format ("json" or "text")
        
        Returns:
            Dict with insights (parsed from JSON if response_format="json")
        """
        try:
            # LangChain handles async automatically
            response = await self.llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            if response_format == "json":
                return self._parse_json_response(content)
            else:
                return {"text": content}
        
        except Exception as e:
            logger.error(f"LLM generation error ({self.provider}): {e}", exc_info=True)
            return {"error": str(e)}
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response."""
        import re
        
        # Try to find JSON in response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error: {e}")
                logger.debug(f"Response: {response[:500]}")
                return {"error": "Failed to parse JSON response", "raw": response}
        
        logger.warning(f"No JSON found in response: {response[:500]}")
        return {"error": "No JSON found in response", "raw": response}
```

---

### **Day 2: Create Prompt Templates**

**File:** `api/services/llm/prompts.py`
```python
"""Prompt templates based on strategist's ChatGPT method."""
from typing import Dict, Any


class PromptTemplates:
    """Prompt templates for each report section."""
    
    @staticmethod
    def kav_analysis(data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        KAV analysis prompt matching strategist's format.
        
        Based on StrategistChat.md examples.
        """
        return f"""You are a marketing strategist analyzing KAV (Klaviyo Attributed Value) performance for {context.get('client_name', 'the client')} in the {context.get('industry', 'retail')} industry.

Date Range: {context.get('date_range', 'N/A')}

KAV Metrics:
- Total Revenue: ${data.get('total_revenue', 0):,.2f}
- Attributed Revenue: ${data.get('attributed_revenue', 0):,.2f}
- KAV Percentage: {data.get('kav_percentage', 0):.1f}%
- Flow Revenue: ${data.get('flow_revenue', 0):,.2f}
- Campaign Revenue: ${data.get('campaign_revenue', 0):,.2f}

Industry Benchmarks:
- Average KAV: {context.get('benchmarks', {}).get('kav_benchmark', 30):.1f}%

Provide strategic insights in JSON format with this exact structure:
{{
    "primary_narrative": "Strategic overview paragraph explaining KAV performance and what it means",
    "secondary_narrative": "Detailed analysis paragraph with context and implications",
    "strengths": ["strength 1", "strength 2", "strength 3"],
    "opportunities": ["opportunity 1", "opportunity 2", "opportunity 3"],
    "campaign_flow_analysis": "Analysis of campaign vs flow revenue split and what it indicates"
}}

Match the tone and style from the strategist's examples - strategic, contextual, and actionable."""
    
    @staticmethod
    def flow_analysis(flow_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Flow analysis prompt."""
        flow_name = flow_data.get('flow_name', 'Flow')
        return f"""You are a marketing strategist analyzing {flow_name} flow performance for {context.get('client_name', 'the client')} in the {context.get('industry', 'retail')} industry.

Date Range: {context.get('date_range', 'N/A')}

Flow Metrics:
- Open Rate: {flow_data.get('open_rate', 0):.2f}% (Industry avg: {context.get('benchmarks', {}).get('open_rate', 0):.2f}%)
- Click Rate: {flow_data.get('click_rate', 0):.2f}% (Industry avg: {context.get('benchmarks', {}).get('click_rate', 0):.2f}%)
- Conversion Rate: {flow_data.get('conversion_rate', 0):.2f}% (Industry avg: {context.get('benchmarks', {}).get('conversion_rate', 0):.2f}%)
- Revenue: ${flow_data.get('revenue', 0):,.2f}
- Recipients: {flow_data.get('recipients', 0):,}

Flow Details:
- Status: {flow_data.get('status', 'unknown')}
- Number of Emails: {flow_data.get('email_count', 0)}
- Flow Type: {flow_data.get('flow_type', 'unknown')}

Provide strategic insights in JSON format:
{{
    "performance_summary": "How this flow performs vs benchmarks and what it means",
    "optimization_opportunities": ["opportunity 1", "opportunity 2", "opportunity 3"],
    "strategic_insights": "Why this flow matters and how it fits into the overall strategy",
    "recommendations": ["specific recommendation 1", "specific recommendation 2"]
}}"""
    
    @staticmethod
    def campaign_analysis(campaign_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Campaign analysis prompt."""
        return f"""Analyze campaign performance for {context.get('client_name', 'the client')}:

Campaign Metrics:
- Total Campaigns: {campaign_data.get('total_campaigns', 0)}
- Average Open Rate: {campaign_data.get('avg_open_rate', 0):.2f}% (Industry avg: {context.get('benchmarks', {}).get('open_rate', 0):.2f}%)
- Average Click Rate: {campaign_data.get('avg_click_rate', 0):.2f}% (Industry avg: {context.get('benchmarks', {}).get('click_rate', 0):.2f}%)
- Total Campaign Revenue: ${campaign_data.get('total_revenue', 0):,.2f}

Provide insights in JSON format with strengths, opportunities, and recommendations."""
    
    @staticmethod
    def list_growth_analysis(list_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """List growth analysis prompt."""
        return f"""Analyze email list growth for {context.get('client_name', 'the client')}:

List Metrics:
- Current Subscribers: {list_data.get('current_total', 0):,}
- New Subscribers (period): {list_data.get('growth_subscribers', 0):,}
- Lost Subscribers (period): {list_data.get('lost_subscribers', 0):,}
- Churn Rate: {list_data.get('churn_rate', 0):.2f}%

Provide insights in JSON format with growth analysis and recommendations."""
```

---

### **Day 3: Create Data Formatter**

**File:** `api/services/llm/formatter.py`
```python
"""Format Klaviyo data for LLM consumption."""
from typing import Dict, Any


class LLMDataFormatter:
    """Format data and context for LLM prompts."""
    
    @staticmethod
    def format_kav_data(
        kav_data: Dict[str, Any],
        client_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format KAV data for LLM prompt."""
        totals = kav_data.get("totals", {})
        return {
            "total_revenue": totals.get("total_revenue", 0),
            "attributed_revenue": totals.get("attributed_revenue", 0),
            "kav_percentage": totals.get("kav_percentage", 0),
            "flow_revenue": totals.get("flow_revenue", 0),
            "campaign_revenue": totals.get("campaign_revenue", 0),
        }
    
    @staticmethod
    def format_flow_data(
        flow_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format flow data for LLM prompt."""
        performance = flow_data.get("performance", {})
        return {
            "flow_name": flow_data.get("name", "Unknown Flow"),
            "flow_type": flow_data.get("flow_type", "unknown"),
            "status": flow_data.get("status", "unknown"),
            "email_count": flow_data.get("email_count", 0),
            "open_rate": performance.get("open_rate", 0),
            "click_rate": performance.get("click_rate", 0),
            "conversion_rate": performance.get("conversion_rate", 0),
            "revenue": performance.get("revenue", 0),
            "recipients": performance.get("recipients", 0),
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

### **Day 4-5: Test Infrastructure**

**File:** `test_llm_service.py` (temporary test file)
```python
"""Test LLM service with sample data."""
import asyncio
import os
from api.services.llm import LLMService
from api.services.llm.prompts import PromptTemplates
from api.services.llm.formatter import LLMDataFormatter

async def test_kav_analysis():
    """Test KAV analysis with LLM."""
    # Initialize LLM service
    llm = LLMService(provider="claude")  # or "openai", "gemini"
    
    # Sample data
    kav_data = {
        "totals": {
            "total_revenue": 8738532.03,
            "attributed_revenue": 3313157.35,
            "kav_percentage": 37.9,
            "flow_revenue": 1601073.64,
            "campaign_revenue": 1712083.72
        }
    }
    
    context = {
        "client_name": "Test Client",
        "industry": "apparel",
        "date_range": "Sep 26 - Dec 25, 2025",
        "benchmarks": {
            "kav_benchmark": 30.0,
            "open_rate": 45.0,
            "click_rate": 4.5
        }
    }
    
    # Format data
    formatter = LLMDataFormatter()
    formatted_data = formatter.format_kav_data(kav_data, context)
    
    # Generate prompt
    prompt = PromptTemplates.kav_analysis(formatted_data, context)
    
    # Get insights
    insights = await llm.generate_insights(prompt, response_format="json")
    
    print("LLM Insights:")
    print(json.dumps(insights, indent=2))

if __name__ == "__main__":
    asyncio.run(test_kav_analysis())
```

---

## 📅 Week 2: Integration

### **Day 1: Replace KAV Section**

**File:** `api/services/report.py` - Update `_prepare_kav_data()`

```python
def _prepare_kav_data(self, kav_raw: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare KAV data with LLM-generated insights."""
    from .llm import LLMService
    from .llm.prompts import PromptTemplates
    from .llm.formatter import LLMDataFormatter
    
    # Initialize LLM service
    llm_provider = os.getenv("LLM_PROVIDER", "claude")
    llm_service = LLMService(provider=llm_provider)
    formatter = LLMDataFormatter()
    
    # Format data and context
    kav_data_formatted = formatter.format_kav_data(kav_raw, {})
    context = formatter.format_context(
        client_name=self.client_name,
        industry="apparel",  # TODO: Get from config
        date_range=f"{kav_raw.get('period', {}).get('start_date', '')} to {kav_raw.get('period', {}).get('end_date', '')}",
        benchmarks=self._load_benchmarks()
    )
    
    # Generate insights with LLM
    prompt = PromptTemplates.kav_analysis(kav_data_formatted, context)
    llm_insights = await llm_service.generate_insights(prompt, response_format="json")
    
    # Use LLM insights (fallback to empty if error)
    if "error" not in llm_insights:
        primary_narrative = llm_insights.get("primary_narrative", "")
        secondary_narrative = llm_insights.get("secondary_narrative", "")
        strengths = llm_insights.get("strengths", [])
        opportunities = llm_insights.get("opportunities", [])
    else:
        # Fallback if LLM fails
        primary_narrative = kav_raw.get("narrative", "")
        secondary_narrative = ""
        strengths = []
        opportunities = []
    
    return {
        "period": kav_raw.get("period", {}),
        "totals": kav_raw.get("totals", {}),
        "chart_data": kav_raw.get("chart_data", {}),
        "narrative": primary_narrative,
        "secondary_narrative": secondary_narrative,
        "strengths": strengths,
        "opportunities": opportunities,
        "campaign_flow_analysis": llm_insights.get("campaign_flow_analysis", "")
    }
```

---

### **Day 2-3: Replace Flow Sections**

**Update flow analysis methods:**
```python
def _prepare_flow_data(self, flow_data: Dict[str, Any], flow_type: str, benchmarks: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare flow data with LLM-generated insights."""
    from .llm import LLMService
    from .llm.prompts import PromptTemplates
    from .llm.formatter import LLMDataFormatter
    
    llm_service = LLMService(provider=os.getenv("LLM_PROVIDER", "claude"))
    formatter = LLMDataFormatter()
    
    # Format flow data
    formatted_flow = formatter.format_flow_data(flow_data)
    context = formatter.format_context(
        client_name=self.client_name,
        industry="apparel",
        date_range="...",
        benchmarks=benchmarks
    )
    
    # Generate insights
    prompt = PromptTemplates.flow_analysis(formatted_flow, context)
    insights = await llm_service.generate_insights(prompt, response_format="json")
    
    return {
        "name": flow_data.get("name"),
        "status": flow_data.get("status"),
        "performance": flow_data.get("performance", {}),
        "insights": insights.get("performance_summary", ""),
        "recommendations": insights.get("recommendations", [])
    }
```

---

### **Day 4-5: Replace Campaign Section**

Similar pattern for campaign analysis.

---

## 📅 Week 3: Cleanup

### **Day 1: Remove Deprecated Files**

```bash
# Files to delete
rm api/services/narrative.py
rm api/services/strategic_decision_engine.py
rm api/services/multi_agent_framework.py
```

### **Day 2: Update Imports**

Search and replace imports:
```python
# Remove these imports
from .narrative import StrategyNarrativeEngine
from .strategic_decision_engine import StrategicDecisionEngine
from .multi_agent_framework import MultiAgentFramework

# Add these
from .llm import LLMService
from .llm.prompts import PromptTemplates
from .llm.formatter import LLMDataFormatter
```

### **Day 3-5: Simplify Remaining Files**

Remove hardcoded narratives from:
- `api/services/klaviyo/flows/lifecycle.py`
- `api/services/klaviyo/segmentation/analyzer.py`
- `api/services/report.py`

---

## ✅ Validation Checklist

After each phase:
- [ ] LLM service works with all providers
- [ ] Prompts generate valid JSON
- [ ] Insights match strategist's quality
- [ ] Reports still generate correctly
- [ ] No broken imports
- [ ] Code is cleaner (less hardcoded logic)

---

**Ready to start?** Let's begin with Day 1: Install LangChain and create the LLM service!

