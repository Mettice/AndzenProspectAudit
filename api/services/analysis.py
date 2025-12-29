"""
Enhanced Agentic Analysis Framework for Klaviyo Audits

This implements a multi-agent system that:
1. Data Extraction Agent - Processes raw Klaviyo data
2. Benchmark Comparison Agent - Compares against industry standards
3. Pattern Recognition Agent - Identifies trends and anomalies
4. Strategic Analysis Agent - Generates insights and recommendations
5. Report Synthesis Agent - Creates comprehensive report

Based on comprehensive audits (Urth & Dreamland Baby examples)
"""
import os
from typing import Dict, Any, List, Optional, Callable
from anthropic import Anthropic
import json
from datetime import datetime


class AgenticAnalysisFramework:
    """
    Multi-agent system for comprehensive Klaviyo audit analysis.
    
    Each agent has a specific role and expertise area, working together
    to produce a comprehensive audit report matching the quality of
    manual consultant audits.
    """
    
    def __init__(self, anthropic_api_key: Optional[str] = None):
        self.api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY required")
        self.client = Anthropic(api_key=self.api_key)
        
    async def run_comprehensive_analysis(
        self,
        klaviyo_data: Dict[str, Any],
        benchmarks: Dict[str, Any],
        client_name: str,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Run complete multi-agent analysis pipeline.
        
        Args:
            klaviyo_data: Raw Klaviyo API data
            benchmarks: Industry benchmark data
            client_name: Client name for personalization
            progress_callback: Optional callback function(progress: float, step: str) to report progress
        
        Returns comprehensive analysis with:
        - Executive summary with KAV analysis
        - Campaign performance analysis
        - Flow performance analysis  
        - List health analysis
        - Benchmark comparisons
        - Trend identification
        - Strategic recommendations
        """
        print("🤖 Starting Agentic Analysis Framework...")
        
        # Stage 1: Data Processing Agent (30-38%)
        print("  📊 Agent 1: Processing and structuring data...")
        if progress_callback:
            progress_callback(30.0, "Processing and structuring data...")
        processed_data = await self._data_processing_agent(klaviyo_data)
        if progress_callback:
            progress_callback(38.0, "Data processing complete")
        
        # Stage 2: Benchmark Comparison Agent (38-46%)
        print("  📈 Agent 2: Running benchmark comparisons...")
        if progress_callback:
            progress_callback(38.0, "Running benchmark comparisons...")
        benchmark_analysis = await self._benchmark_comparison_agent(
            processed_data,
            benchmarks
        )
        if progress_callback:
            progress_callback(46.0, "Benchmark comparisons complete")
        
        # Stage 3: Pattern Recognition Agent (46-52%)
        print("  🔍 Agent 3: Identifying patterns and trends...")
        if progress_callback:
            progress_callback(46.0, "Identifying patterns and trends...")
        pattern_analysis = await self._pattern_recognition_agent(
            processed_data,
            benchmark_analysis
        )
        if progress_callback:
            progress_callback(52.0, "Pattern recognition complete")
        
        # Stage 4: Strategic Analysis Agent (52-56%)
        print("  💡 Agent 4: Generating strategic insights...")
        if progress_callback:
            progress_callback(52.0, "Generating strategic insights...")
        strategic_analysis = await self._strategic_analysis_agent(
            processed_data,
            benchmark_analysis,
            pattern_analysis
        )
        if progress_callback:
            progress_callback(56.0, "Strategic analysis complete")
        
        # Stage 5: Report Synthesis Agent (56-60%)
        print("  📝 Agent 5: Synthesizing final report...")
        if progress_callback:
            progress_callback(56.0, "Synthesizing final report...")
        final_report = await self._report_synthesis_agent(
            client_name,
            processed_data,
            benchmark_analysis,
            pattern_analysis,
            strategic_analysis
        )
        if progress_callback:
            progress_callback(60.0, "AI analysis complete")
        
        print("✅ Agentic analysis complete!")
        return final_report
    
    async def _data_processing_agent(
        self,
        klaviyo_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Agent 1: Process and structure raw Klaviyo data.
        
        Responsibilities:
        - Extract metrics from nested API responses
        - Calculate derived metrics (AOV, conversion rates, etc.)
        - Organize data by category (campaigns, flows, revenue, etc.)
        - Identify key flows (welcome, AC, browse, post-purchase)
        """
        # Create a structured summary of the data for Claude to process
        data_summary = {
            "revenue_data_keys": list(klaviyo_data.get("revenue", {}).keys()) if klaviyo_data.get("revenue") else [],
            "campaigns_count": len(klaviyo_data.get("campaigns", [])),
            "flows_count": len(klaviyo_data.get("flows", [])),
            "campaign_statistics_count": len(klaviyo_data.get("campaign_statistics", [])) if isinstance(klaviyo_data.get("campaign_statistics"), list) else 0,
            "flow_statistics_count": len(klaviyo_data.get("flow_statistics", [])) if isinstance(klaviyo_data.get("flow_statistics"), list) else 0,
            "date_range": klaviyo_data.get("date_range", {}),
            
            # Include first few campaigns and flows as samples
            "sample_campaigns": (klaviyo_data.get("campaigns", []) or [])[:3],
            "sample_flows": (klaviyo_data.get("flows", []) or [])[:3],
            "sample_campaign_stats": (klaviyo_data.get("campaign_statistics", []) or [])[:3] if isinstance(klaviyo_data.get("campaign_statistics"), list) else [],
            "sample_flow_stats": (klaviyo_data.get("flow_statistics", []) or [])[:3] if isinstance(klaviyo_data.get("flow_statistics"), list) else [],
            
            # Include full revenue data since it's usually small
            "revenue_data": klaviyo_data.get("revenue", {})
        }

        # Debug: Print what we're sending to Claude
        print("🔍 DEBUG: Data being sent to Claude for processing:")
        print(f"  Revenue data structure: {json.dumps(klaviyo_data.get('revenue', {}), indent=2)[:500]}...")
        
        campaign_stats = klaviyo_data.get('campaign_statistics')
        if campaign_stats and isinstance(campaign_stats, list) and len(campaign_stats) > 0:
            print(f"  First campaign stat: {json.dumps(campaign_stats[0], indent=2)}")
        else:
            print(f"  Campaign stats: {type(campaign_stats)} - {campaign_stats}")
            
        flow_stats = klaviyo_data.get('flow_statistics') 
        if flow_stats and isinstance(flow_stats, list) and len(flow_stats) > 0:
            print(f"  First flow stat: {json.dumps(flow_stats[0], indent=2)}")
        else:
            print(f"  Flow stats: {type(flow_stats)} - {flow_stats}")

        prompt = f"""You are a data processing specialist for Klaviyo email marketing analysis.

Your task: Process and structure this Klaviyo API data into organized metrics.

DATA STRUCTURE SUMMARY:
- Revenue data: {json.dumps(klaviyo_data.get("revenue", {}), indent=2)}
- Campaigns: {len(klaviyo_data.get("campaigns", []))} total
- Flows: {len(klaviyo_data.get("flows", []))} total  
- Campaign Statistics: {len(klaviyo_data.get("campaign_statistics", []))} entries
- Flow Statistics: {len(klaviyo_data.get("flow_statistics", []))} entries

SAMPLE DATA:
{json.dumps(data_summary, indent=2)}

IMPORTANT: The revenue data structure is from Klaviyo's metric-aggregate API. Look for 'data.attributes.data' array with revenue values.
Campaign and flow statistics are separate arrays with metrics like open_rate, click_rate, conversion_rate.

Extract and calculate:

**REVENUE METRICS:**
- Extract total revenue from revenue_data.data.attributes.data (sum all values)
- Klaviyo attributed revenue = campaign revenue + flow revenue
- KAV percentage = (Klaviyo revenue / Total revenue * 100)
- Campaign revenue: sum from campaign_statistics where available
- Flow revenue: sum from flow_statistics where available  
- Campaign/Flow split percentage

**CAMPAIGN METRICS:**
- Total campaigns: count from campaigns array
- From campaign_statistics array, calculate:
  * Average open_rate (sum rates / count)
  * Average click_rate (sum rates / count)
  * Average conversion_rate (sum rates / count)
- Revenue per campaign (total campaign revenue / campaign count)

**FLOW METRICS:**
- Total flows: count from flows array
- From flows array, identify core flows by name patterns:
  * Welcome Series: names containing "welcome"
  * Abandoned Cart: names containing "abandon", "cart"
  * Browse Abandonment: names containing "browse"
  * Post-Purchase: names containing "post", "purchase", "thank"
- For each core flow, extract:
  * Status from flow.attributes.status
  * Number of messages from flow_details if available
  * Open/click rates from flow_statistics matching flow ID

**LIST HEALTH:**
- Total subscribers (if available)
- Growth rate
- Engagement tiers

Return ONLY valid JSON with this exact structure:
{{
    "revenue": {{
        "total": 0.0,
        "klaviyo_attributed": 0.0,
        "kav_percentage": 0.0,
        "campaign_revenue": 0.0,
        "flow_revenue": 0.0,
        "campaign_flow_split": {{"campaign": 0.0, "flow": 0.0}},
        "daily_trend": []
    }},
    "campaigns": {{
        "total_sent": 0,
        "avg_open_rate": 0.0,
        "avg_click_rate": 0.0,
        "avg_conversion_rate": 0.0,
        "revenue_per_campaign": 0.0,
        "top_performers": [],
        "underperformers": []
    }},
    "flows": {{
        "total_active": 0,
        "core_flows": {{
            "welcome_series": {{"status": "", "messages": 0, "metrics": {{}}}},
            "abandoned_cart": {{"status": "", "messages": 0, "metrics": {{}}}},
            "browse_abandonment": {{"status": "", "messages": 0, "metrics": {{}}}},
            "post_purchase": {{"status": "", "messages": 0, "metrics": {{}}}}
        }},
        "all_flows": []
    }},
    "list_health": {{
        "total_subscribers": 0,
        "growth_rate": 0.0
    }}
}}

Extract real numbers from the data. If data is missing, use 0 or null."""

        response = await self._call_claude(prompt, max_tokens=4000)
        return self._parse_json_response(response)
    
    async def _benchmark_comparison_agent(
        self,
        processed_data: Dict[str, Any],
        benchmarks: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Agent 2: Compare metrics against industry benchmarks.
        
        Responsibilities:
        - Compare campaign metrics vs benchmarks
        - Compare flow metrics vs benchmarks
        - Calculate percentile rankings
        - Identify gaps (positive and negative)
        """
        prompt = f"""You are a benchmark comparison specialist for Klaviyo email marketing.

PROCESSED DATA:
{json.dumps(processed_data, indent=2)}

BENCHMARKS (2025 Klaviyo Industry Standards):
{json.dumps(benchmarks, indent=2)}

Compare the client's metrics against benchmarks and provide:

**CAMPAIGN BENCHMARKS:**
For each metric (open rate, click rate, conversion rate):
- Client value
- Industry average
- Top 10% benchmark
- Gap to average (percentage points)
- Gap to top 10% (percentage points)
- Percentile estimate (0-100)
- Status: "exceeds_top10" | "above_average" | "below_average" | "significantly_below"

**FLOW BENCHMARKS:**
For each core flow type (Welcome, AC, Browse, Post-Purchase):
- Same comparison as campaigns
- Identify missing flows
- Highlight underperforming flows

**OVERALL PERFORMANCE ASSESSMENT:**
- How many metrics exceed top 10%?
- How many metrics are above average?
- How many metrics are below average?
- Overall performance tier: "Top 10%" | "Above Average" | "Average" | "Below Average" | "Needs Improvement"

Return ONLY valid JSON with this structure:
{{
    "campaign_benchmarks": {{
        "open_rate": {{"client": 0.0, "avg": 0.0, "top10": 0.0, "gap_to_avg": 0.0, "gap_to_top10": 0.0, "percentile": 0, "status": ""}},
        "click_rate": {{...}},
        "conversion_rate": {{...}}
    }},
    "flow_benchmarks": {{
        "welcome_series": {{...}},
        "abandoned_cart": {{...}},
        "browse_abandonment": {{...}},
        "post_purchase": {{...}}
    }},
    "overall_assessment": {{
        "metrics_exceeding_top10": 0,
        "metrics_above_average": 0,
        "metrics_below_average": 0,
        "performance_tier": "",
        "percentile_overall": 0
    }},
    "key_gaps": []
}}"""

        response = await self._call_claude(prompt, max_tokens=3000)
        return self._parse_json_response(response)
    
    async def _pattern_recognition_agent(
        self,
        processed_data: Dict[str, Any],
        benchmark_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Agent 3: Identify patterns, trends, and anomalies.
        
        Responsibilities:
        - Identify revenue trends (growth, decline, volatility)
        - Detect seasonality patterns
        - Flag anomalies (sudden drops, spikes)
        - Identify missing or broken flows
        - Detect list health issues
        """
        prompt = f"""You are a pattern recognition specialist for email marketing data.

PROCESSED DATA:
{json.dumps(processed_data, indent=2)}

BENCHMARK ANALYSIS:
{json.dumps(benchmark_analysis, indent=2)}

Analyze the data to identify:

**REVENUE PATTERNS:**
- Trend: "growing" | "stable" | "declining" | "volatile"
- Growth rate (month-over-month or year-over-year if available)
- Seasonality indicators
- Revenue concentration (is revenue from campaigns or flows balanced?)

**PERFORMANCE PATTERNS:**
- Campaign performance consistency (stable vs volatile)
- Flow performance vs campaign performance
- Best performing channel/format
- Underutilized opportunities

**RED FLAGS:**
- Missing core flows (should have Welcome, AC, Browse, Post-Purchase)
- Broken flows (0 revenue despite being live)
- List health issues (high attrition, low engagement)
- Revenue over-reliance on campaigns (should be 50/50 split)
- Declining engagement trends

**OPPORTUNITIES:**
- Quick wins (flows close to benchmarks that need small tweaks)
- High-impact gaps (missing flows that competitors use)
- Untapped potential (segments, channels not being used)

Return ONLY valid JSON:
{{
    "revenue_patterns": {{
        "trend": "",
        "growth_rate": 0.0,
        "volatility": "",
        "balance": ""
    }},
    "performance_patterns": {{
        "campaign_consistency": "",
        "flow_vs_campaign": "",
        "best_channel": ""
    }},
    "red_flags": [
        {{
            "severity": "critical" | "high" | "medium" | "low",
            "category": "",
            "issue": "",
            "impact": ""
        }}
    ],
    "opportunities": [
        {{
            "priority": "high" | "medium" | "low",
            "category": "",
            "opportunity": "",
            "potential_impact": ""
        }}
    ]
}}"""

        response = await self._call_claude(prompt, max_tokens=3000)
        return self._parse_json_response(response)
    
    async def _strategic_analysis_agent(
        self,
        processed_data: Dict[str, Any],
        benchmark_analysis: Dict[str, Any],
        pattern_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Agent 4: Generate strategic insights and recommendations.
        
        Responsibilities:
        - Synthesize all analysis into strategic insights
        - Prioritize opportunities by impact
        - Create actionable recommendations
        - Estimate ROI/impact for each recommendation
        """
        prompt = f"""You are a senior email marketing strategist specializing in Klaviyo optimization.

You have analyzed a client's Klaviyo account. Now provide strategic guidance.

PROCESSED DATA:
{json.dumps(processed_data, indent=2)[:3000]}

BENCHMARK COMPARISON:
{json.dumps(benchmark_analysis, indent=2)[:2000]}

PATTERN ANALYSIS:
{json.dumps(pattern_analysis, indent=2)[:2000]}

Provide strategic analysis with:

**TOP 3 STRENGTHS:**
What is working well? What should they keep doing?

**TOP 3 OPPORTUNITIES:**
What are the biggest areas for improvement? Focus on high-impact items.

**KEY INSIGHTS:**
2-3 paragraphs of strategic insights that connect the data, benchmarks, and patterns
into a cohesive narrative about this account's performance and potential.

**PRIORITIZED RECOMMENDATIONS:**
Provide 5-10 specific, actionable recommendations organized by:

Tier 1 - Critical (implement immediately, 0-30 days):
- Items that fix broken/missing core functionality
- High ROI, low effort improvements

Tier 2 - High Impact (implement next, 30-90 days):
- Major optimization opportunities  
- New flow implementations

Tier 3 - Strategic (implement long-term, 90+ days):
- Advanced personalization
- New channels/strategies

For EACH recommendation include:
- Title (what to do)
- Description (how to do it)
- Expected impact (specific metrics)
- Estimated effort (hours/days)
- Priority tier

Return ONLY valid JSON:
{{
    "strengths": ["strength 1", "strength 2", "strength 3"],
    "opportunities": ["opp 1", "opp 2", "opp 3"],
    "insights": "detailed strategic insights paragraph",
    "recommendations": {{
        "tier_1_critical": [
            {{
                "title": "",
                "description": "",
                "expected_impact": "",
                "effort": "",
                "timeframe": "0-30 days"
            }}
        ],
        "tier_2_high_impact": [...],
        "tier_3_strategic": [...]
    }}
}}"""

        response = await self._call_claude(prompt, max_tokens=4000)
        return self._parse_json_response(response)
    
    async def _report_synthesis_agent(
        self,
        client_name: str,
        processed_data: Dict[str, Any],
        benchmark_analysis: Dict[str, Any],
        pattern_analysis: Dict[str, Any],
        strategic_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Agent 5: Synthesize all analysis into final report structure.
        
        Responsibilities:
        - Organize all insights into report sections
        - Ensure narrative flow and consistency
        - Format for report template
        - Add executive summary
        """
        return {
            "client_name": client_name,
            "audit_date": datetime.now().strftime("%B %d, %Y"),
            "executive_summary": {
                "kav_percentage": processed_data.get("revenue", {}).get("kav_percentage", 0),
                "performance_tier": benchmark_analysis.get("overall_assessment", {}).get("performance_tier", "Average"),
                "top_strengths": strategic_analysis.get("strengths", [])[:3],
                "top_opportunities": strategic_analysis.get("opportunities", [])[:3],
                "key_insight": strategic_analysis.get("insights", "")
            },
            "data_snapshot": {
                "total_campaigns": processed_data.get("campaigns", {}).get("total_sent", 0),
                "total_flows": processed_data.get("flows", {}).get("total_active", 0),
                "total_revenue": processed_data.get("revenue", {}).get("total", 0),
                "klaviyo_revenue": processed_data.get("revenue", {}).get("klaviyo_attributed", 0)
            },
            "revenue_analysis": processed_data.get("revenue", {}),
            "campaign_analysis": {
                "metrics": processed_data.get("campaigns", {}),
                "benchmarks": benchmark_analysis.get("campaign_benchmarks", {}),
                "insights": self._extract_campaign_insights(
                    processed_data,
                    benchmark_analysis,
                    pattern_analysis
                )
            },
            "flow_analysis": {
                "core_flows": processed_data.get("flows", {}).get("core_flows", {}),
                "all_flows": processed_data.get("flows", {}).get("all_flows", []),
                "benchmarks": benchmark_analysis.get("flow_benchmarks", {}),
                "missing_flows": self._identify_missing_flows(processed_data),
                "insights": self._extract_flow_insights(
                    processed_data,
                    benchmark_analysis,
                    pattern_analysis
                )
            },
            "list_health_analysis": {
                "metrics": processed_data.get("list_health", {}),
                "red_flags": [
                    flag for flag in pattern_analysis.get("red_flags", [])
                    if flag.get("category") == "list_health"
                ]
            },
            "patterns_and_trends": pattern_analysis,
            "strategic_recommendations": strategic_analysis.get("recommendations", {}),
            "benchmark_comparisons": benchmark_analysis
        }
    
    # Helper methods
    
    async def _call_claude(self, prompt: str, max_tokens: int = 4000) -> str:
        """Call Claude API with consistent settings."""
        import asyncio
        loop = asyncio.get_event_loop()
        
        response = await loop.run_in_executor(
            None,
            lambda: self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                temperature=0.3,  # Lower for more consistent analysis
                messages=[{"role": "user", "content": prompt}]
            )
        )
        
        return response.content[0].text
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Extract and parse JSON from Claude's response."""
        import re
        
        # Try to find JSON in response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError as e:
                print(f"Warning: JSON parse error: {e}")
                print(f"Response was: {response[:500]}")
                return {}
        
        print(f"Warning: No JSON found in response: {response[:500]}")
        return {}
    
    def _extract_campaign_insights(
        self,
        processed_data: Dict[str, Any],
        benchmark_analysis: Dict[str, Any],
        pattern_analysis: Dict[str, Any]
    ) -> List[str]:
        """Extract campaign-specific insights."""
        insights = []
        
        campaign_benchmarks = benchmark_analysis.get("campaign_benchmarks", {})
        
        # Check if campaigns are performing well
        metrics_above_avg = sum(
            1 for metric in campaign_benchmarks.values()
            if metric.get("status") in ["above_average", "exceeds_top10"]
        )
        
        if metrics_above_avg >= 2:
            insights.append("Campaigns performing above industry average in multiple metrics")
        else:
            insights.append("Campaign performance below industry benchmarks - optimization needed")
        
        return insights
    
    def _extract_flow_insights(
        self,
        processed_data: Dict[str, Any],
        benchmark_analysis: Dict[str, Any],
        pattern_analysis: Dict[str, Any]
    ) -> List[str]:
        """Extract flow-specific insights."""
        insights = []
        
        core_flows = processed_data.get("flows", {}).get("core_flows", {})
        
        # Check for missing or underperforming flows
        for flow_name, flow_data in core_flows.items():
            if not flow_data or flow_data.get("status") == "missing":
                insights.append(f"Missing critical flow: {flow_name.replace('_', ' ').title()}")
        
        return insights
    
    def _identify_missing_flows(self, processed_data: Dict[str, Any]) -> List[str]:
        """Identify which critical flows are missing."""
        missing = []
        core_flows = processed_data.get("flows", {}).get("core_flows", {})
        
        required_flows = ["welcome_series", "abandoned_cart", "browse_abandonment", "post_purchase"]
        
        for flow in required_flows:
            if flow not in core_flows or not core_flows[flow]:
                missing.append(flow.replace("_", " ").title())
        
        return missing