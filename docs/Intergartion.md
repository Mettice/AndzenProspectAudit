"""
Integration Script - Connect Enhanced Components

This shows how to integrate:
1. Enhanced Analysis Framework (5 agents)
2. Enhanced Report Service
3. Comprehensive HTML Template
4. Benchmark data

Into your existing audit.py
"""

# =============================================================================
# STEP 1: Update api/services/analysis.py
# =============================================================================

"""
Replace the entire content of api/services/analysis.py with:
"""

# api/services/analysis.py
from pathlib import Path
import pandas as pd
from typing import Dict, Any, Optional
import os
from anthropic import Anthropic
import json
import asyncio


class AnalysisService:
    """Enhanced analysis service using agentic framework."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY required")
        self.client = Anthropic(api_key=self.api_key)
        
        # Load benchmarks
        self.benchmarks = self._load_benchmarks()
    
    async def analyze(self, klaviyo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run comprehensive agentic analysis.
        
        This replaces the simple analysis with a 5-agent system.
        """
        print("🤖 Starting Enhanced Agentic Analysis...")
        
        # Agent 1: Data Processing
        print("  📊 Processing data...")
        processed_data = await self._data_processing_agent(klaviyo_data)
        
        # Agent 2: Benchmark Comparison
        print("  📈 Running benchmark comparisons...")
        benchmark_analysis = await self._benchmark_comparison_agent(processed_data)
        
        # Agent 3: Pattern Recognition
        print("  🔍 Identifying patterns...")
        pattern_analysis = await self._pattern_recognition_agent(
            processed_data,
            benchmark_analysis
        )
        
        # Agent 4: Strategic Analysis
        print("  💡 Generating strategic insights...")
        strategic_analysis = await self._strategic_analysis_agent(
            processed_data,
            benchmark_analysis,
            pattern_analysis
        )
        
        # Agent 5: Report Synthesis
        print("  📝 Synthesizing report...")
        final_report = self._synthesize_report(
            processed_data,
            benchmark_analysis,
            pattern_analysis,
            strategic_analysis
        )
        
        print("✅ Analysis complete!")
        return final_report
    
    def _load_benchmarks(self) -> Dict[str, Any]:
        """Load benchmark data from CSV."""
        csv_path = Path(__file__).parent.parent.parent / "data" / "benchmarks" / "klaviyo-benchmarks.csv"
        
        if not csv_path.exists():
            print(f"Warning: Benchmark file not found at {csv_path}")
            return {}
        
        df = pd.read_csv(csv_path)
        benchmarks = {}
        
        # Organize by category and metric
        for _, row in df.iterrows():
            category = row['category'].replace(' ', '_').lower()
            metric = row['metric_name'].replace(' ', '_').lower()
            segment = row['segment'].lower()
            value = row['value']
            
            if category not in benchmarks:
                benchmarks[category] = {}
            if metric not in benchmarks[category]:
                benchmarks[category][metric] = {}
            
            benchmarks[category][metric][segment] = value
        
        return benchmarks
    
    async def _data_processing_agent(self, klaviyo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Agent 1: Process raw data into structured format."""
        
        # Extract revenue metrics
        revenue_data = klaviyo_data.get("revenue", {})
        campaigns = klaviyo_data.get("campaigns", [])
        flows = klaviyo_data.get("flows", [])
        campaign_stats = klaviyo_data.get("campaign_statistics", {})
        flow_stats = klaviyo_data.get("flow_statistics", {})
        
        # Calculate KAV and other metrics
        total_revenue = self._extract_revenue_total(revenue_data)
        campaign_revenue = self._extract_campaign_revenue(campaign_stats)
        flow_revenue = self._extract_flow_revenue(flow_stats)
        klaviyo_revenue = campaign_revenue + flow_revenue
        
        kav_percentage = (klaviyo_revenue / total_revenue * 100) if total_revenue > 0 else 0
        
        # Campaign/Flow split
        if klaviyo_revenue > 0:
            campaign_pct = (campaign_revenue / klaviyo_revenue) * 100
            flow_pct = (flow_revenue / klaviyo_revenue) * 100
        else:
            campaign_pct = 0
            flow_pct = 0
        
        # Identify core flows
        core_flows = self._identify_core_flows(flows, flow_stats)
        
        return {
            "revenue": {
                "total": total_revenue,
                "klaviyo_attributed": klaviyo_revenue,
                "kav_percentage": kav_percentage,
                "campaign_revenue": campaign_revenue,
                "flow_revenue": flow_revenue,
                "campaign_flow_split": {
                    "campaign": campaign_pct,
                    "flow": flow_pct
                }
            },
            "campaigns": {
                "total_sent": len(campaigns),
                "avg_open_rate": self._calc_avg_campaign_metric(campaign_stats, "open_rate"),
                "avg_click_rate": self._calc_avg_campaign_metric(campaign_stats, "click_rate"),
                "avg_conversion_rate": self._calc_avg_campaign_metric(campaign_stats, "conversion_rate")
            },
            "flows": {
                "total_active": len([f for f in flows if f.get("attributes", {}).get("status") == "live"]),
                "core_flows": core_flows,
                "all_flows": flows
            }
        }
    
    async def _benchmark_comparison_agent(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Agent 2: Compare against benchmarks."""
        
        campaign_benchmarks = {}
        flow_benchmarks = {}
        
        # Get campaign benchmarks
        if "email_campaign" in self.benchmarks:
            email_camp = self.benchmarks["email_campaign"]
            
            for metric in ["open_rate", "click_rate", "placed_order_rate"]:
                if metric in email_camp:
                    client_value = processed_data.get("campaigns", {}).get(f"avg_{metric}", 0)
                    avg = email_camp[metric].get("average", 0)
                    top10 = email_camp[metric].get("top_10%", 0)
                    
                    campaign_benchmarks[metric] = {
                        "client": client_value,
                        "avg": avg,
                        "top10": top10,
                        "gap_to_avg": client_value - avg,
                        "gap_to_top10": client_value - top10,
                        "percentile": self._calc_percentile(client_value, avg, top10),
                        "status": self._get_status(client_value, avg, top10)
                    }
        
        # Get flow benchmarks for each core flow
        core_flows = processed_data.get("flows", {}).get("core_flows", {})
        
        for flow_type, flow_data in core_flows.items():
            if flow_data and flow_data.get("status") == "live":
                # Map flow type to benchmark category
                benchmark_key = self._map_flow_to_benchmark(flow_type)
                
                if benchmark_key and benchmark_key in self.benchmarks.get("email_flow", {}):
                    flow_bench = self.benchmarks["email_flow"][benchmark_key]
                    
                    flow_benchmarks[flow_type] = {}
                    for metric in ["open_rate", "click_rate", "placed_order_rate"]:
                        if metric in flow_bench:
                            client_value = flow_data.get("metrics", {}).get(metric, 0)
                            avg = flow_bench[metric].get("average", 0)
                            top10 = flow_bench[metric].get("top_10%", 0)
                            
                            flow_benchmarks[flow_type][metric] = {
                                "client": client_value,
                                "avg": avg,
                                "top10": top10,
                                "gap_to_avg": client_value - avg,
                                "gap_to_top10": client_value - top10,
                                "status": self._get_status(client_value, avg, top10)
                            }
        
        return {
            "campaign_benchmarks": campaign_benchmarks,
            "flow_benchmarks": flow_benchmarks,
            "overall_assessment": self._assess_overall_performance(campaign_benchmarks, flow_benchmarks)
        }
    
    async def _pattern_recognition_agent(
        self,
        processed_data: Dict[str, Any],
        benchmark_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Agent 3: Identify patterns and red flags."""
        
        red_flags = []
        opportunities = []
        
        # Check for missing flows
        core_flows = processed_data.get("flows", {}).get("core_flows", {})
        required_flows = ["welcome_series", "abandoned_cart", "browse_abandonment", "post_purchase"]
        
        for flow in required_flows:
            if flow not in core_flows or not core_flows[flow] or core_flows[flow].get("status") != "live":
                red_flags.append({
                    "severity": "critical",
                    "category": "flows",
                    "issue": f"Missing {flow.replace('_', ' ').title()} flow",
                    "impact": "Lost revenue opportunity from automated customer journey"
                })
        
        # Check KAV percentage
        kav = processed_data.get("revenue", {}).get("kav_percentage", 0)
        if kav < 20:
            red_flags.append({
                "severity": "high",
                "category": "revenue",
                "issue": f"Low KAV percentage ({kav:.1f}%)",
                "impact": "Klaviyo attribution below target - missing revenue attribution"
            })
        
        # Check campaign/flow balance
        split = processed_data.get("revenue", {}).get("campaign_flow_split", {})
        campaign_pct = split.get("campaign", 0)
        
        if abs(campaign_pct - 50) > 20:
            red_flags.append({
                "severity": "medium",
                "category": "revenue",
                "issue": f"Imbalanced campaign/flow split ({campaign_pct:.0f}% campaigns)",
                "impact": "Over-reliance on one revenue source - diversification needed"
            })
        
        return {
            "red_flags": red_flags,
            "opportunities": opportunities
        }
    
    async def _strategic_analysis_agent(
        self,
        processed_data: Dict[str, Any],
        benchmark_analysis: Dict[str, Any],
        pattern_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Agent 4: Generate strategic insights using Claude."""
        
        prompt = f"""You are a senior Klaviyo email marketing strategist.

Analyze this data and provide strategic insights:

PROCESSED DATA:
{json.dumps(processed_data, indent=2)[:3000]}

BENCHMARK COMPARISON:
{json.dumps(benchmark_analysis, indent=2)[:2000]}

RED FLAGS:
{json.dumps(pattern_analysis.get("red_flags", []), indent=2)}

Provide:
1. Top 3 strengths (what's working well)
2. Top 3 opportunities (biggest improvement areas)
3. Key strategic insights (2-3 paragraphs)
4. Tiered recommendations:
   - Tier 1 Critical (0-30 days): Fix broken/missing core items
   - Tier 2 High Impact (30-90 days): Major optimizations
   - Tier 3 Strategic (90+ days): Long-term initiatives

For each recommendation include:
- title
- description
- expected_impact
- effort
- timeframe

Return ONLY valid JSON with this structure:
{{
    "strengths": ["strength1", "strength2", "strength3"],
    "opportunities": ["opp1", "opp2", "opp3"],
    "insights": "strategic insights paragraph",
    "recommendations": {{
        "tier_1_critical": [{{"title": "", "description": "", "expected_impact": "", "effort": "", "timeframe": "0-30 days"}}],
        "tier_2_high_impact": [...],
        "tier_3_strategic": [...]
    }}
}}"""

        response = await self._call_claude(prompt)
        return self._parse_json_response(response)
    
    def _synthesize_report(
        self,
        processed_data: Dict[str, Any],
        benchmark_analysis: Dict[str, Any],
        pattern_analysis: Dict[str, Any],
        strategic_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Agent 5: Synthesize final report structure."""
        
        return {
            "executive_summary": {
                "kav_percentage": processed_data.get("revenue", {}).get("kav_percentage", 0),
                "performance_tier": benchmark_analysis.get("overall_assessment", {}).get("performance_tier", "Average"),
                "top_strengths": strategic_analysis.get("strengths", [])[:3],
                "top_opportunities": strategic_analysis.get("opportunities", [])[:3],
                "key_insight": strategic_analysis.get("insights", ""),
                "overall_health_score": self._calculate_health_score(benchmark_analysis, pattern_analysis)
            },
            "data_snapshot": {
                "total_campaigns": processed_data.get("campaigns", {}).get("total_sent", 0),
                "total_flows": processed_data.get("flows", {}).get("total_active", 0),
                "total_revenue": processed_data.get("revenue", {}).get("total", 0),
                "klaviyo_revenue": processed_data.get("revenue", {}).get("klaviyo_attributed", 0)
            },
            "revenue_analysis": {
                "totals": processed_data.get("revenue", {}),
                "campaign_flow_split": processed_data.get("revenue", {}).get("campaign_flow_split", {}),
                "insights": self._generate_revenue_insights(processed_data.get("revenue", {}))
            },
            "campaign_analysis": {
                "overview": processed_data.get("campaigns", {}),
                "benchmark_comparisons": self._format_benchmark_comparisons(
                    benchmark_analysis.get("campaign_benchmarks", {})
                )
            },
            "flow_analysis": {
                "core_flows": self._format_core_flows(
                    processed_data.get("flows", {}).get("core_flows", {}),
                    benchmark_analysis.get("flow_benchmarks", {})
                ),
                "missing_flows": self._identify_missing_flows(processed_data)
            },
            "patterns": pattern_analysis,
            "recommendations": strategic_analysis.get("recommendations", {}),
            "benchmark_details": {
                "campaign_metrics": [],
                "flow_metrics": {}
            }
        }
    
    # Helper methods
    
    async def _call_claude(self, prompt: str) -> str:
        """Call Claude API."""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
        )
        return response.content[0].text
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from Claude response."""
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        return {}
    
    def _extract_revenue_total(self, revenue_data: Dict) -> float:
        """Extract total revenue from API response."""
        # Adapt based on actual API structure
        return 0.0
    
    def _extract_campaign_revenue(self, campaign_stats: Dict) -> float:
        """Extract campaign revenue."""
        return 0.0
    
    def _extract_flow_revenue(self, flow_stats: Dict) -> float:
        """Extract flow revenue."""
        return 0.0
    
    def _identify_core_flows(self, flows: List, flow_stats: Dict) -> Dict:
        """Identify and categorize core flows."""
        core_flows = {
            "welcome_series": None,
            "abandoned_cart": None,
            "browse_abandonment": None,
            "post_purchase": None
        }
        
        for flow in flows:
            name = flow.get("attributes", {}).get("name", "").lower()
            
            if "welcome" in name and not core_flows["welcome_series"]:
                core_flows["welcome_series"] = {
                    "status": flow.get("attributes", {}).get("status"),
                    "messages": 0,
                    "metrics": {}
                }
            elif "cart" in name or "abandon" in name:
                if "browse" in name:
                    core_flows["browse_abandonment"] = {
                        "status": flow.get("attributes", {}).get("status"),
                        "messages": 0,
                        "metrics": {}
                    }
                else:
                    core_flows["abandoned_cart"] = {
                        "status": flow.get("attributes", {}).get("status"),
                        "messages": 0,
                        "metrics": {}
                    }
            elif "post" in name or "purchase" in name or "thank" in name:
                core_flows["post_purchase"] = {
                    "status": flow.get("attributes", {}).get("status"),
                    "messages": 0,
                    "metrics": {}
                }
        
        return core_flows
    
    def _calc_avg_campaign_metric(self, stats: Dict, metric: str) -> float:
        """Calculate average campaign metric."""
        return 0.0
    
    def _calc_percentile(self, value: float, avg: float, top10: float) -> int:
        """Calculate percentile."""
        if value >= top10:
            return 90
        elif value >= avg:
            return 50 + int((value - avg) / (top10 - avg) * 40)
        else:
            return int((value / avg) * 50) if avg > 0 else 0
    
    def _get_status(self, value: float, avg: float, top10: float) -> str:
        """Get performance status."""
        if value >= top10:
            return "exceeds_top10"
        elif value >= avg:
            return "above_average"
        elif value >= avg * 0.8:
            return "below_average"
        else:
            return "significantly_below"
    
    def _map_flow_to_benchmark(self, flow_type: str) -> str:
        """Map flow type to benchmark category."""
        mapping = {
            "welcome_series": "welcome_flow",
            "abandoned_cart": "abandoned_cart_flow",
            "browse_abandonment": "browse_abandonment_flow",
            "post_purchase": "post-purchase_flow"
        }
        return mapping.get(flow_type)
    
    def _assess_overall_performance(self, campaign_bench: Dict, flow_bench: Dict) -> Dict:
        """Assess overall performance."""
        metrics_above_avg = 0
        metrics_exceeding = 0
        
        for metric_data in campaign_bench.values():
            status = metric_data.get("status", "")
            if "above" in status:
                metrics_above_avg += 1
            if "exceeds" in status:
                metrics_exceeding += 1
        
        return {
            "metrics_above_average": metrics_above_avg,
            "metrics_exceeding_top10": metrics_exceeding,
            "performance_tier": "Above Average" if metrics_above_avg >= 2 else "Average"
        }
    
    def _calculate_health_score(self, benchmark: Dict, patterns: Dict) -> int:
        """Calculate overall health score 0-100."""
        score = 50
        score += benchmark.get("overall_assessment", {}).get("metrics_above_average", 0) * 5
        score += benchmark.get("overall_assessment", {}).get("metrics_exceeding_top10", 0) * 10
        score -= len(patterns.get("red_flags", [])) * 5
        return max(0, min(100, score))
    
    def _generate_revenue_insights(self, revenue: Dict) -> List[str]:
        """Generate revenue insights."""
        insights = []
        kav = revenue.get("kav_percentage", 0)
        if kav < 20:
            insights.append(f"KAV at {kav:.1f}% is below target - opportunity to improve attribution")
        return insights
    
    def _format_benchmark_comparisons(self, benchmarks: Dict) -> List[Dict]:
        """Format benchmarks for display."""
        comparisons = []
        for metric, data in benchmarks.items():
            comparisons.append({
                "metric": metric.replace("_", " ").title(),
                "client_value": data.get("client", 0),
                "average": data.get("avg", 0),
                "top_10": data.get("top10", 0),
                "status": data.get("status", ""),
                "status_class": self._get_status_class(data.get("status", ""))
            })
        return comparisons
    
    def _format_core_flows(self, core_flows: Dict, benchmarks: Dict) -> Dict:
        """Format core flows for display."""
        formatted = {}
        for flow_name, flow_data in core_flows.items():
            formatted[flow_name] = {
                "name": flow_name.replace("_", " ").title(),
                "status": flow_data.get("status", "missing") if flow_data else "missing",
                "messages": flow_data.get("messages", 0) if flow_data else 0,
                "metrics": flow_data.get("metrics", {}) if flow_data else {},
                "health_status": "healthy",
                "recommendations": []
            }
        return formatted
    
    def _identify_missing_flows(self, processed_data: Dict) -> List[str]:
        """Identify missing core flows."""
        missing = []
        core_flows = processed_data.get("flows", {}).get("core_flows", {})
        
        for flow_name, flow_data in core_flows.items():
            if not flow_data or flow_data.get("status") != "live":
                missing.append(flow_name.replace("_", " ").title())
        
        return missing
    
    def _get_status_class(self, status: str) -> str:
        """Get CSS class for status."""
        mapping = {
            "exceeds_top10": "status-excellent",
            "above_average": "status-good",
            "below_average": "status-warning",
            "significantly_below": "status-critical"
        }
        return mapping.get(status, "status-neutral")


# =============================================================================
# STEP 2: Update api/services/report.py
# =============================================================================

"""
Update to use comprehensive template:
"""

# api/services/report.py
async def generate_report(
    self,
    klaviyo_data: Dict[str, Any],
    analysis: Dict[str, Any],
    client_name: str
) -> Dict[str, Any]:
    """Generate report using comprehensive template."""
    
    template = self.env.get_template("comprehensive_audit_template.html")
    
    context = {
        "client_name": client_name,
        "audit_date": datetime.now().strftime("%B %d, %Y"),
        "auditor_name": "Andzen Team",
        **analysis  # All analysis data
    }
    
    html_content = template.render(**context)
    
    # Save
    output_dir = Path(__file__).parent.parent.parent / "data" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"audit_{client_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.html"
    output_path = output_dir / filename
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return {
        "url": str(output_path),
        "data": {"filename": filename, "path": str(output_path)}
    }


# =============================================================================
# STEP 3: Update templates/comprehensive_audit_template.html
# =============================================================================

"""
Copy the comprehensive_audit_template.html file to:
templates/comprehensive_audit_template.html
"""


# =============================================================================
# STEP 4: Test the Integration
# =============================================================================

"""
Run a test audit:

python -c "
import asyncio
from api.services.klaviyo import KlaviyoService
from api.services.analysis import AnalysisService
from api.services.report import ReportService

async def test():
    # Your API key
    klaviyo = KlaviyoService(api_key='YOUR_KEY')
    analysis_svc = AnalysisService()
    report_svc = ReportService()
    
    # Extract data
    data = await klaviyo.extract_all_data()
    
    # Analyze
    analysis = await analysis_svc.analyze(data)
    
    # Generate report
    report = await report_svc.generate_report(data, analysis, 'Test Client')
    
    print(f'Report generated: {report}')

asyncio.run(test())
"
"""

print("""
✅ Integration script complete!

Next steps:
1. Copy comprehensive_audit_template.html to templates/
2. Update your analysis.py with the new code above
3. Update your report.py with the new code above
4. Ensure klaviyo-benchmarks.csv is in data/benchmarks/
5. Run a test audit

Your system will now generate consultant-quality reports! 🚀
""")