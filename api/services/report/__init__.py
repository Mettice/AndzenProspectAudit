"""
Enhanced Report Service - Generates comprehensive Klaviyo audit reports

Modularized structure:
- formatters.py: Formatting utilities
- data_preparers.py: Data preparation for sections
- pdf_generator.py: PDF generation
"""
from pathlib import Path
from typing import Dict, Any, Optional, List
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import json
import asyncio
import platform

# Import modular components
from .formatters import (
    format_currency,
    format_percentage,
    format_number,
    get_status_class,
    format_benchmark_comparison,
    format_metric_table,
    format_recommendations
)
from .data_preparers import (
    prepare_kav_data,
    prepare_list_growth_data,
    prepare_data_capture_data,
    prepare_automation_data,
    prepare_flow_data,
    prepare_abandoned_cart_data,
    prepare_browse_abandonment_data,
    prepare_post_purchase_data,
    prepare_campaign_performance_data,
    prepare_strategic_recommendations
)
from .pdf_generator import generate_pdf_weasyprint, generate_pdf_playwright


class EnhancedReportService:
    """
    Enhanced report generation matching consultant-quality audits.
    
    Generates reports with:
    - Executive Summary with KAV analysis
    - Data Snapshot
    - Revenue Analysis with trends
    - Campaign Performance vs Benchmarks
    - Flow Analysis (Welcome, AC, Browse, Post-Purchase)
    - List Health Assessment
    - Patterns & Trends
    - Strategic Recommendations (tiered by priority)
    - Visual Charts & Graphs (data for charts)
    """
    
    def __init__(self, template_dir: Optional[Path] = None):
        if template_dir is None:
            # __file__ is at api/services/report/__init__.py
            # Need to go up 4 levels: report -> services -> api -> root
            template_dir = Path(__file__).parent.parent.parent.parent / "templates"
        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        # Add custom filters for formatting
        self.env.filters['format_currency'] = format_currency
        self.env.filters['format_percentage'] = format_percentage
        self.env.filters['format_number'] = format_number
        
        # Add image embedding filters
        from .image_handler import embed_image_filter, get_image_data_uri
        self.env.filters['embed_image'] = embed_image_filter
        self.env.filters['image_data_uri'] = get_image_data_uri
        self.env.filters['status_class'] = get_status_class
    
    async def generate_comprehensive_report(
        self,
        analysis_results: Dict[str, Any],
        auditor_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive audit report.
        
        Args:
            analysis_results: Output from AgenticAnalysisFramework
            auditor_name: Name of auditor (defaults to "Andzen Team")
        
        Returns:
            Dict with report_url and report_data
        """
        template = self.env.get_template("comprehensive_audit_template.html")
        
        # Prepare all sections
        context = {
            "client_name": analysis_results.get("client_name", "Client"),
            "audit_date": analysis_results.get("audit_date", datetime.now().strftime("%B %d, %Y")),
            "auditor_name": auditor_name or "Andzen Team",
            
            # Executive Summary
            "executive_summary": self._prepare_executive_summary(analysis_results),
            
            # Data Snapshot
            "data_snapshot": analysis_results.get("data_snapshot", {}),
            
            # Revenue Analysis
            "revenue_analysis": self._prepare_revenue_analysis(analysis_results),
            
            # Campaign Analysis
            "campaign_analysis": self._prepare_campaign_analysis(analysis_results),
            
            # Flow Analysis
            "flow_analysis": self._prepare_flow_analysis(analysis_results),
            
            # List Health
            "list_health": analysis_results.get("list_health_analysis", {}),
            
            # Patterns & Trends
            "patterns": analysis_results.get("patterns_and_trends", {}),
            
            # Strategic Recommendations
            "recommendations": self._prepare_recommendations(analysis_results),
            
            # Benchmark Comparisons (detailed tables)
            "benchmark_details": self._prepare_benchmark_details(analysis_results)
        }
        
        # Render HTML
        html_content = template.render(**context)
        
        # Save report
        output_dir = Path(__file__).parent.parent.parent / "data" / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        client_slug = analysis_results.get("client_name", "Client").replace(" ", "_").replace("'", "")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"comprehensive_audit_{client_slug}_{timestamp}.html"
        output_path = output_dir / filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return {
            "report_url": str(output_path),
            "report_data": context
        }
    
    async def generate_audit(
        self,
        audit_data: Dict[str, Any],
        client_name: str,
        auditor_name: Optional[str] = None,
        client_code: Optional[str] = None,
        industry: Optional[str] = None,
        llm_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a professional comprehensive audit report.
        
        This method uses the modular template system to create a comprehensive
        audit that matches the quality and depth of manual consultant audits.
        
        Args:
            audit_data: Output from KlaviyoService.extract_audit_data()
            client_name: Name of the client being audited
            auditor_name: Name of auditor (defaults to "Andzen Team")
            client_code: Optional Andzen client code
        
        Returns:
            Dict with report_url, pdf_url (if available), and report_data
        """
        # Load the main audit report template
        template = self.env.get_template("audit_report.html")
        
        # Prepare cover data
        cover_data = {
            "client_name": client_name,
            "client_code": client_code or "",
            "audit_date": datetime.now().strftime("%d %b %Y"),
            "auditor_name": auditor_name or "Andzen Team"
        }
        
        # Merge with audit_data, overriding cover_data
        if "cover_data" in audit_data:
            cover_data.update({k: v for k, v in audit_data["cover_data"].items() if v})
        
        # Load benchmarks based on industry (2025 benchmarks)
        industry_value = industry or audit_data.get("industry", "apparel_accessories")
        benchmarks = self._load_benchmarks(industry=industry_value)
        
        # Get industry for context and add to account_context for LLM
        account_context = audit_data.get("account_context", {})
        account_context["industry"] = industry_value
        
        # Add LLM configuration to account_context so preparers can access it
        if llm_config:
            account_context["llm_config"] = llm_config
        
        # Prepare full context with all section data using modular preparers
        context = {
            # Cover page
            "cover_data": cover_data,
            "client_name": client_name,
            
            # KAV Analysis (Pages 2-3)
            "kav_data": await prepare_kav_data(
                audit_data.get("kav_data", {}), 
                client_name,
                account_context=account_context
            ),
            
            # List Growth (Page 4)
            "list_growth_data": await prepare_list_growth_data(
                audit_data.get("list_growth_data", {}),
                client_name,
                account_context
            ),

            # Data Capture (Pages 5-6)
            "data_capture_data": await prepare_data_capture_data(
                audit_data.get("data_capture_data", {}),
                client_name,
                account_context
            ),

            # Automation Overview (Page 7)
            "automation_overview_data": await prepare_automation_data(
                audit_data.get("automation_overview_data", {}),
                benchmarks,
                client_name,
                account_context
            ),

            # Welcome Series (Page 8)
            "welcome_flow_data": await prepare_flow_data(
                audit_data.get("welcome_flow_data", {}),
                "welcome_series",
                benchmarks,
                client_name,
                account_context
            ),

            # Abandoned Cart (Pages 9-10)
            "abandoned_cart_data": await prepare_abandoned_cart_data(
                audit_data.get("abandoned_cart_data", {}),
                benchmarks,
                client_name,
                account_context
            ),

            # Browse Abandonment (Page 11)
            "browse_abandonment_data": await prepare_browse_abandonment_data(
                audit_data.get("browse_abandonment_data", {}),
                benchmarks,
                client_name,
                account_context
            ),

            # Post Purchase (Pages 12-13)
            "post_purchase_data": await prepare_post_purchase_data(
                audit_data.get("post_purchase_data", {}),
                benchmarks,
                client_name,
                account_context
            ),

            # Reviews (Page 14)
            "reviews_data": audit_data.get("reviews_data", {}),

            # Wishlist (Pages 15-16)
            "wishlist_data": audit_data.get("wishlist_data", {}),

            # Campaign Performance (Page 17)
            "campaign_performance_data": await prepare_campaign_performance_data(
                audit_data.get("campaign_performance_data", {}),
                benchmarks,
                client_name,
                account_context
            ),
            
            # Segmentation Strategy (Page 18)
            "segmentation_data": audit_data.get("segmentation_data", {
                "tracks": [
                    {"name": "Track A: Highly Engaged", "cadence": "Daily"},
                    {"name": "Track B: Moderately Engaged", "cadence": "2-3x/week"},
                    {"name": "Track C: Broad Engaged", "cadence": "1x/week"},
                    {"name": "Track D: Unengaged", "cadence": "Goes through Sunset Flow then suppressed"},
                    {"name": "Track E: For Suppression", "cadence": "Do not send. Needs to be suppressed"}
                ]
            })
        }
        
        # Phase 3: Strategic Recommendations (Enhanced Intelligence)
        # Pass prepared context so strategic thesis can access kav_interpretation, pattern_diagnosis, etc.
        # Must be added AFTER context is fully built
        context["strategic_recommendations_data"] = await prepare_strategic_recommendations(audit_data, prepared_context=context)
        
        # Render HTML
        html_content = template.render(**context)
        
        # Save report
        output_dir = Path(__file__).parent.parent.parent / "data" / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        client_slug = client_name.replace(" ", "_").replace("'", "")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"audit_{client_slug}_{timestamp}.html"
        output_path = output_dir / filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        # Attempt PDF generation with proper error handling
        pdf_path = None
        
        try:
            if platform.system() == "Windows":
                # Try Playwright first on Windows (better compatibility)
                try:
                    pdf_path = await asyncio.wait_for(
                        generate_pdf_playwright(output_path),
                        timeout=60.0  # 60 second timeout
                    )
                    if pdf_path:
                        print("✓ PDF generated using Playwright")
                except asyncio.TimeoutError:
                    print("⚠ PDF generation timed out after 60 seconds")
                except Exception as e:
                    print(f"⚠ Playwright PDF generation failed: {e}")
                    # Fall back to WeasyPrint
                    try:
                        pdf_path = await generate_pdf_weasyprint(output_path)
                        if pdf_path:
                            print("✓ PDF generated using WeasyPrint")
                    except Exception as e2:
                        print(f"⚠ PDF generation skipped: {e2}")
            else:
                # Try WeasyPrint first on Linux/Mac
                try:
                    pdf_path = await generate_pdf_weasyprint(output_path)
                    if pdf_path:
                        print("✓ PDF generated using WeasyPrint")
                except Exception as e:
                    print(f"⚠ WeasyPrint not available - {e}")
                    # Fall back to Playwright
                    try:
                        pdf_path = await asyncio.wait_for(
                            generate_pdf_playwright(output_path),
                            timeout=60.0
                        )
                        if pdf_path:
                            print("✓ PDF generated using Playwright")
                    except asyncio.TimeoutError:
                        print("⚠ PDF generation timed out")
                    except Exception as e2:
                        print(f"⚠ PDF generation skipped: {e2}")
        except Exception as e:
            # Catch any unexpected errors and continue - PDF is optional
            print(f"⚠ PDF generation encountered an error (continuing without PDF): {e}")
            pdf_path = None
        
        # Generate Word document if possible
        word_path = None
        try:
            word_path = await self._generate_word_document(output_path, html_content)
            if word_path:
                print("✓ Word document generated")
        except Exception as e:
            print(f"⚠ Word document generation skipped: {e}")
        
        return {
            "html_url": str(output_path),
            "pdf_url": str(pdf_path) if pdf_path else None,
            "word_url": str(word_path) if word_path else None,
            "html_content": html_content,  # Include HTML content for inline display
            "filename": filename,
            "pages": 19,
            "sections": [
                "Cover Page",
                "KAV Analysis", 
                "List Growth",
                "Data Capture",
                "Automation Overview",
                "Welcome Series",
                "Abandoned Cart",
                "Browse Abandonment",
                "Post Purchase",
                "Reviews",
                "Wishlist",
                "Campaign Performance",
                "Segmentation Strategy",
                "Strategic Recommendations"
            ]
        }
    
    async def _generate_word_document(self, html_path: Path, html_content: str) -> Optional[Path]:
        """
        Generate Word document from HTML content.
        
        Uses python-docx with htmldocx for conversion.
        Falls back to mammoth if htmldocx is not available.
        """
        try:
            from docx import Document
            from htmldocx import HtmlToDocx
            
            word_path = html_path.with_suffix('.docx')
            
            # Create a new Document
            doc = Document()
            
            # Initialize HTML to DOCX converter
            new_parser = HtmlToDocx()
            
            # Clean HTML content - remove script tags and style tags that might cause issues
            import re
            # Remove script tags
            clean_html = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            # Remove style tags (keep inline styles)
            clean_html = re.sub(r'<style[^>]*>.*?</style>', '', clean_html, flags=re.DOTALL | re.IGNORECASE)
            
            # Add HTML content to document
            new_parser.add_html_to_document(clean_html, doc)
            
            # Save document
            doc.save(str(word_path))
            
            return word_path
            
        except ImportError:
            # Try alternative: mammoth for HTML to DOCX conversion
            try:
                import mammoth
                word_path = html_path.with_suffix('.docx')
                
                # Convert HTML to DOCX using mammoth
                result = mammoth.convert_to_docx(html_content.encode('utf-8'))
                with open(word_path, 'wb') as f:
                    f.write(result.value)
                
                return word_path
            except ImportError:
                print("Neither python-docx+htmldocx nor mammoth installed. Word generation unavailable.")
                print("Install with: pip install python-docx htmldocx OR pip install mammoth")
                return None
        except Exception as e:
            print(f"Word document generation failed: {e}")
            return None
    
    def _load_benchmarks(self, industry: str = "apparel_accessories") -> Dict[str, Any]:
        """
        Load benchmarks from JSON file based on industry.
        
        Args:
            industry: Industry identifier (e.g., "apparel_accessories", "fashion_accessories")
            
        Returns:
            Dict with benchmark data (2025 benchmarks)
        """
        # Map industry to benchmark file
        # Add new benchmark files here as you create them
        industry_to_file = {
            "apparel_accessories": "comprehensive_benchmarks.json",
            "fashion_accessories": "fashion_accessories.json",
            "toys_collectibles": "toys_collectibles.json",  # Create this file
            "ecommerce_collections": "ecommerce_collections.json",  # Create this file
            "beauty_cosmetics": "comprehensive_benchmarks.json",  # Use comprehensive as default
            "electronics": "comprehensive_benchmarks.json",
            "home_garden": "comprehensive_benchmarks.json",
            "food_beverage": "comprehensive_benchmarks.json",
            "health_fitness": "comprehensive_benchmarks.json",
            "retail": "comprehensive_benchmarks.json",
            "other": "comprehensive_benchmarks.json"
        }
        
        benchmark_file = industry_to_file.get(industry, "comprehensive_benchmarks.json")
        benchmark_path = Path(__file__).parent.parent.parent.parent / "data" / "benchmarks" / benchmark_file
        
        try:
            with open(benchmark_path, "r") as f:
                benchmarks = json.load(f)
                # Ensure we're using 2025 benchmarks (check metadata)
                metadata = benchmarks.get("metadata", {})
                if metadata.get("source", "").find("2025") == -1 and metadata.get("last_updated", "").find("2025") == -1:
                    print(f"⚠️ Warning: Benchmarks may not be 2025 data. Source: {metadata.get('source', 'Unknown')}")
                return benchmarks
        except FileNotFoundError:
            print(f"Benchmark file not found at {benchmark_path}, using default")
            # Fallback to comprehensive_benchmarks.json
            fallback_path = Path(__file__).parent.parent.parent.parent / "data" / "benchmarks" / "comprehensive_benchmarks.json"
            try:
                with open(fallback_path, "r") as f:
                    return json.load(f)
            except:
                return {}
        except json.JSONDecodeError:
            print(f"Invalid JSON in benchmark file")
            return {}
    
    # Legacy methods for comprehensive report (kept for backward compatibility)
    def _prepare_executive_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare executive summary section."""
        exec_summary = results.get("executive_summary", {})
        
        return {
            "kav_percentage": exec_summary.get("kav_percentage", 0),
            "performance_tier": exec_summary.get("performance_tier", "Average"),
            "top_strengths": exec_summary.get("top_strengths", [])[:3],
            "top_opportunities": exec_summary.get("top_opportunities", [])[:3],
            "key_insight": exec_summary.get("key_insight", ""),
            "overall_health_score": self._calculate_health_score(results)
        }
    
    def _prepare_revenue_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare detailed revenue analysis."""
        revenue = results.get("revenue_analysis", {})
        
        return {
            "totals": {
                "total_revenue": revenue.get("total", 0),
                "klaviyo_revenue": revenue.get("klaviyo_attributed", 0),
                "campaign_revenue": revenue.get("campaign_revenue", 0),
                "flow_revenue": revenue.get("flow_revenue", 0)
            },
            "kav_analysis": {
                "percentage": revenue.get("kav_percentage", 0),
                "target": 30.0,  # Industry standard
                "gap": 30.0 - revenue.get("kav_percentage", 0),
                "status": self._get_kav_status(revenue.get("kav_percentage", 0))
            },
            "campaign_flow_split": revenue.get("campaign_flow_split", {"campaign": 0, "flow": 0}),
            "ideal_split": {"campaign": 50, "flow": 50},
            "daily_trend": revenue.get("daily_trend", []),
            "insights": self._generate_revenue_insights(revenue)
        }
    
    def _prepare_campaign_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare comprehensive campaign analysis."""
        campaign = results.get("campaign_analysis", {})
        metrics = campaign.get("metrics", {})
        benchmarks = campaign.get("benchmarks", {})
        
        return {
            "overview": {
                "total_sent": metrics.get("total_sent", 0),
                "avg_open_rate": metrics.get("avg_open_rate", 0),
                "avg_click_rate": metrics.get("avg_click_rate", 0),
                "avg_conversion_rate": metrics.get("avg_conversion_rate", 0),
                "revenue_per_campaign": metrics.get("revenue_per_campaign", 0)
            },
            "benchmark_comparisons": format_benchmark_comparison(benchmarks),
            "top_performers": metrics.get("top_performers", [])[:5],
            "underperformers": metrics.get("underperformers", [])[:5],
            "insights": campaign.get("insights", []),
            "recommendations": self._generate_campaign_recommendations(metrics, benchmarks)
        }
    
    def _prepare_flow_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare comprehensive flow analysis with core flow breakdown."""
        flow = results.get("flow_analysis", {})
        core_flows = flow.get("core_flows", {})
        benchmarks = flow.get("benchmarks", {})
        
        # Prepare each core flow
        flow_details = {}
        for flow_name in ["welcome_series", "abandoned_cart", "browse_abandonment", "post_purchase"]:
            flow_data = core_flows.get(flow_name, {})
            benchmark = benchmarks.get(flow_name, {})
            
            flow_details[flow_name] = {
                "name": flow_name.replace("_", " ").title(),
                "status": flow_data.get("status", "missing"),
                "messages": flow_data.get("messages", 0),
                "metrics": flow_data.get("metrics", {}),
                "benchmark_comparison": format_benchmark_comparison(benchmark),
                "health_status": self._assess_flow_health(flow_data, benchmark),
                "recommendations": self._generate_flow_recommendations(
                    flow_name,
                    flow_data,
                    benchmark
                )
            }
        
        return {
            "core_flows": flow_details,
            "all_flows": flow.get("all_flows", []),
            "missing_flows": flow.get("missing_flows", []),
            "total_active": len([f for f in core_flows.values() if f.get("status") == "live"]),
            "insights": flow.get("insights", []),
            "priority_actions": self._identify_priority_flow_actions(core_flows, benchmarks)
        }
    
    def _prepare_recommendations(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare tiered recommendations section."""
        recs = results.get("strategic_recommendations", {})
        
        return {
            "tier_1_critical": format_recommendations(
                recs.get("tier_1_critical", []),
                ["CRITICAL"]
            ),
            "tier_2_high_impact": format_recommendations(
                recs.get("tier_2_high_impact", []),
                ["HIGH IMPACT"]
            ),
            "tier_3_strategic": format_recommendations(
                recs.get("tier_3_strategic", []),
                ["STRATEGIC"]
            )
        }
    
    def _prepare_benchmark_details(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare detailed benchmark comparison tables."""
        benchmarks = results.get("benchmark_comparisons", {})
        
        return {
            "campaign_metrics": format_metric_table(
                benchmarks.get("campaign_benchmarks", {})
            ),
            "flow_metrics": {
                flow_name: format_metric_table(flow_data)
                for flow_name, flow_data in benchmarks.get("flow_benchmarks", {}).items()
            },
            "overall_performance": benchmarks.get("overall_assessment", {})
        }
    
    def _calculate_health_score(self, results: Dict[str, Any]) -> int:
        """Calculate overall account health score (0-100)."""
        score = 50  # Base score
        
        # KAV percentage (up to +20)
        kav = results.get("executive_summary", {}).get("kav_percentage", 0)
        if kav >= 30:
            score += 20
        elif kav >= 20:
            score += 10
        
        # Benchmark performance (up to +30)
        overall = results.get("benchmark_comparisons", {}).get("overall_assessment", {})
        metrics_above_avg = overall.get("metrics_above_average", 0)
        metrics_exceeding = overall.get("metrics_exceeding_top10", 0)
        
        score += min(30, (metrics_above_avg * 3) + (metrics_exceeding * 5))
        
        # Red flags (-30)
        red_flags = results.get("patterns_and_trends", {}).get("red_flags", [])
        critical_flags = len([f for f in red_flags if f.get("severity") == "critical"])
        score -= min(30, critical_flags * 10)
        
        return max(0, min(100, score))
    
    def _get_kav_status(self, kav_percentage: float) -> str:
        """Get KAV status label."""
        if kav_percentage >= 30:
            return "healthy"
        elif kav_percentage >= 20:
            return "moderate"
        else:
            return "needs_improvement"
    
    def _generate_revenue_insights(self, revenue: Dict[str, Any]) -> List[str]:
        """Generate insights about revenue performance."""
        insights = []
        
        kav = revenue.get("kav_percentage", 0)
        if kav < 20:
            insights.append(f"KAV at {kav:.1f}% is below target of 30% - significant opportunity to increase Klaviyo attribution")
        elif kav >= 30:
            insights.append(f"Strong KAV at {kav:.1f}% indicates effective email marketing attribution")
        
        split = revenue.get("campaign_flow_split", {})
        campaign_pct = split.get("campaign", 0)
        flow_pct = split.get("flow", 0)
        
        if abs(campaign_pct - 50) > 20:
            if campaign_pct > flow_pct:
                insights.append(f"Revenue heavily weighted toward campaigns ({campaign_pct:.0f}%) - flows need optimization")
            else:
                insights.append(f"Revenue heavily weighted toward flows ({flow_pct:.0f}%) - campaign strategy needs attention")
        
        return insights
    
    def _generate_campaign_recommendations(
        self,
        metrics: Dict[str, Any],
        benchmarks: Dict[str, Any]
    ) -> List[str]:
        """Generate campaign-specific recommendations."""
        recs = []
        
        # Check open rate
        open_rate_data = benchmarks.get("open_rate", {})
        if open_rate_data.get("status") == "below_average":
            recs.append("Improve subject lines and sender reputation to boost open rates")
        
        # Check click rate
        click_rate_data = benchmarks.get("click_rate", {})
        if click_rate_data.get("status") == "below_average":
            recs.append("Enhance email design and CTAs to improve click-through rates")
        
        return recs
    
    def _assess_flow_health(
        self,
        flow_data: Dict[str, Any],
        benchmark: Dict[str, Any]
    ) -> str:
        """Assess health status of a flow."""
        if not flow_data or flow_data.get("status") != "live":
            return "inactive"
        
        metrics = flow_data.get("metrics", {})
        if not metrics:
            return "no_data"
        
        # Check against benchmarks
        open_rate = metrics.get("open_rate", 0)
        benchmark_open = benchmark.get("open_rate", {}).get("avg", 0)
        
        if open_rate >= benchmark_open:
            return "healthy"
        elif open_rate >= benchmark_open * 0.8:
            return "moderate"
        else:
            return "needs_attention"
    
    def _generate_flow_recommendations(
        self,
        flow_name: str,
        flow_data: Dict[str, Any],
        benchmark: Dict[str, Any]
    ) -> List[str]:
        """Generate flow-specific recommendations."""
        recs = []
        
        if not flow_data or flow_data.get("status") != "live":
            recs.append(f"Activate {flow_name.replace('_', ' ')} flow - critical for revenue generation")
            return recs
        
        # Check message count
        messages = flow_data.get("messages", 0)
        ideal_messages = {
            "welcome_series": 3,
            "abandoned_cart": 3,
            "browse_abandonment": 2,
            "post_purchase": 2
        }
        
        if messages < ideal_messages.get(flow_name, 2):
            recs.append(f"Add more messages to {flow_name.replace('_', ' ')} (currently {messages}, recommend {ideal_messages.get(flow_name, 3)})")
        
        return recs
    
    def _identify_priority_flow_actions(
        self,
        core_flows: Dict[str, Any],
        benchmarks: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify top priority flow actions."""
        actions = []
        
        for flow_name, flow_data in core_flows.items():
            if not flow_data or flow_data.get("status") != "live":
                actions.append({
                    "flow": flow_name.replace("_", " ").title(),
                    "action": "Activate flow",
                    "priority": "CRITICAL",
                    "impact": "High"
                })
        
        return actions[:5]  # Top 5 priority actions

