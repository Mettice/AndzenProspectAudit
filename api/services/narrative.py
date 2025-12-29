"""
Strategic Narrative Engine - Transform metrics into business insights like Carissa
"""
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class StrategyNarrativeEngine:
    """
    Transform raw metrics into strategic narratives with business context.
    
    This engine replicates Carissa's approach of turning every metric into 
    a strategic insight with "why it matters" analysis and actionable recommendations.
    """
    
    def __init__(self):
        self.industry_benchmarks = {
            "kav_benchmark": 30.0,  # Industry standard KAV as % of website revenue
            "flow_campaign_split": {"flow": 60.0, "campaign": 40.0},  # Ideal attribution split
            "engagement_benchmark": 50.0,  # % of list that should be engaged
        }
    
    def generate_kav_narrative(self, kav_data: Dict[str, Any], client_context: Dict[str, Any] = None) -> Dict[str, str]:
        """
        Generate Carissa-style KAV narrative with strategic context.
        
        Args:
            kav_data: KAV metrics and percentages
            client_context: Business context (e.g., challenges, industry)
            
        Returns:
            Dict with primary and secondary narrative content
        """
        try:
            # Extract key metrics
            total_kav = kav_data.get("revenue", {}).get("total_attributed", 0)
            kav_percentage = kav_data.get("revenue", {}).get("kav_percentage", 0)
            flow_percentage = kav_data.get("revenue", {}).get("flow_percentage", 0)
            campaign_percentage = kav_data.get("revenue", {}).get("campaign_percentage", 0)
            
            # Get business context
            has_campaign_gap = client_context.get("has_campaign_gap", False) if client_context else False
            client_name = client_context.get("client_name", "the brand") if client_context else "the brand"
            industry = client_context.get("industry", "retail") if client_context else "retail"
            
            # Generate primary narrative based on KAV performance
            primary_narrative = self._generate_kav_primary_narrative(
                total_kav, kav_percentage, flow_percentage, campaign_percentage, 
                has_campaign_gap, client_name
            )
            
            # Generate secondary narrative with strategic implications
            secondary_narrative = self._generate_kav_secondary_narrative(
                flow_percentage, campaign_percentage, has_campaign_gap, client_name
            )
            
            return {
                "primary": primary_narrative,
                "secondary": secondary_narrative,
                "strategic_focus": self._identify_kav_strategic_focus(kav_percentage, flow_percentage, has_campaign_gap)
            }
            
        except Exception as e:
            logger.error(f"Error generating KAV narrative: {e}")
            return {
                "primary": "KAV analysis requires additional data for strategic insights.",
                "secondary": "Contact support for detailed analysis.",
                "strategic_focus": "data_quality"
            }
    
    def _generate_kav_primary_narrative(self, total_kav: float, kav_percentage: float, 
                                      flow_percentage: float, campaign_percentage: float,
                                      has_campaign_gap: bool, client_name: str) -> str:
        """Generate primary KAV narrative with benchmark comparison."""
        
        # Format revenue for readability
        kav_formatted = f"${total_kav:,.0f}" if total_kav > 1000 else f"${total_kav:.2f}"
        
        # Benchmark comparison context
        if kav_percentage >= 28:
            benchmark_context = f"aligns closely with Klaviyo's 30% benchmark and highlights a strong foundation of lifecycle and retention marketing that is actively contributing to overall performance"
        elif kav_percentage >= 20:
            benchmark_context = f"shows solid owned channel performance at {kav_percentage:.1f}%, approaching the industry benchmark of 30%"
        else:
            benchmark_context = f"at {kav_percentage:.1f}% indicates significant untapped potential, falling well below the 30% industry benchmark"
        
        # Campaign gap context
        if has_campaign_gap:
            performance_context = "However, the absence of regular campaign activity presents a clear opportunity to strengthen this foundation and drive KAV closer to benchmark levels."
        else:
            performance_context = "This performance demonstrates that email and SMS programs are providing stabilization and contributing meaningfully to revenue generation."
        
        return f"Owned channels delivered {kav_formatted} in revenue, representing {kav_percentage:.1f}% of total website revenue, which {benchmark_context}. {performance_context}"
    
    def _generate_kav_secondary_narrative(self, flow_percentage: float, campaign_percentage: float,
                                        has_campaign_gap: bool, client_name: str) -> str:
        """Generate secondary narrative focused on attribution split and strategic implications."""
        
        if has_campaign_gap:
            # No campaigns scenario
            return f"""The current revenue attribution shows flows carrying 100% of owned channel performance, which creates an imbalanced ecosystem. In high-performing lifecycle programs, campaigns and flows work as a connected system—campaigns stimulate demand by re-engaging the list and driving fresh traffic, while flows capture the resulting intent through browsing, cart additions, and checkout behaviors.
            
Without campaign activity, flows have fewer opportunities to activate, fewer triggers to fire, and ultimately less revenue to capture. This creates a clear and high-impact opportunity: {client_name} can meaningfully grow KAV by reintroducing campaigns as the primary engine of engagement and pairing them with their existing automation suite."""
        else:
            # Evaluate current split
            ideal_flow = self.industry_benchmarks["flow_campaign_split"]["flow"]
            ideal_campaign = self.industry_benchmarks["flow_campaign_split"]["campaign"]
            
            if flow_percentage > 70:
                return f"""Flows dominate the attribution mix at {flow_percentage:.1f}%, while campaigns contribute {campaign_percentage:.1f}%. While strong flow performance indicates effective automation, this imbalance suggests campaigns are underutilized as an engagement driver. The ideal attribution split typically ranges from 50/50 to 60/40 (flows/campaigns), where campaigns create the upstream activity that flows then convert."""
            elif campaign_percentage > 60:
                return f"""Campaigns drive {campaign_percentage:.1f}% of owned revenue, while flows contribute {flow_percentage:.1f}%. This campaign-heavy split, while generating results, indicates automation is under-leveraged. Flows often provide more efficient mid-to-bottom funnel conversions and should typically account for 40-50% of owned revenue as a scalable foundation for retention."""
            else:
                return f"""The attribution split of {flow_percentage:.1f}% flows and {campaign_percentage:.1f}% campaigns demonstrates a balanced owned channel ecosystem where campaigns drive upstream engagement and flows capture downstream intent. This balanced approach maximizes both reach and conversion efficiency."""
    
    def _identify_kav_strategic_focus(self, kav_percentage: float, flow_percentage: float, has_campaign_gap: bool) -> str:
        """Identify the primary strategic focus area for recommendations."""
        
        if has_campaign_gap:
            return "campaign_reintroduction"
        elif kav_percentage < 20:
            return "kav_growth"
        elif flow_percentage < 30:
            return "flow_optimization"
        elif flow_percentage > 80:
            return "campaign_balance"
        else:
            return "optimization_refinement"
    
    def generate_flow_performance_narrative(self, flow_data: Dict[str, Any], benchmarks: Dict[str, float]) -> Dict[str, str]:
        """
        Generate strategic narrative for individual flow performance.
        
        Args:
            flow_data: Flow metrics (open rate, click rate, placed order rate, revenue)
            benchmarks: Industry benchmarks for comparison
            
        Returns:
            Strategic narrative with performance assessment and recommendations
        """
        try:
            flow_name = flow_data.get("name", "Flow")
            open_rate = flow_data.get("open_rate", 0)
            click_rate = flow_data.get("click_rate", 0)
            placed_order_rate = flow_data.get("placed_order_rate", 0)
            revenue = flow_data.get("revenue", 0)
            revenue_percentage = flow_data.get("revenue_percentage", 0)
            
            # Get relevant benchmarks
            benchmark_open = benchmarks.get("open_rate", 50.0)
            benchmark_click = benchmarks.get("click_rate", 4.0)
            benchmark_order = benchmarks.get("placed_order_rate", 2.0)
            
            # Performance assessment
            performance_summary = self._assess_flow_performance(
                open_rate, click_rate, placed_order_rate,
                benchmark_open, benchmark_click, benchmark_order
            )
            
            # Strategic recommendations based on performance gaps
            recommendations = self._generate_flow_recommendations(
                flow_name, open_rate, click_rate, placed_order_rate,
                benchmark_open, benchmark_click, benchmark_order
            )
            
            # Revenue context
            revenue_context = f"contributed ${revenue:,.0f}, representing {revenue_percentage:.1f}% of total flow revenue" if revenue > 0 else "shows minimal revenue contribution, indicating conversion optimization opportunities"
            
            return {
                "performance_summary": performance_summary,
                "revenue_context": revenue_context,
                "recommendations": recommendations,
                "strategic_priority": self._determine_flow_priority(open_rate, click_rate, placed_order_rate, benchmarks)
            }
            
        except Exception as e:
            logger.error(f"Error generating flow narrative: {e}")
            return {
                "performance_summary": "Flow analysis requires additional data.",
                "revenue_context": "",
                "recommendations": "Contact support for detailed analysis.",
                "strategic_priority": "low"
            }
    
    def _assess_flow_performance(self, open_rate: float, click_rate: float, placed_order_rate: float,
                                benchmark_open: float, benchmark_click: float, benchmark_order: float) -> str:
        """Assess overall flow performance with strategic context."""
        
        # Calculate performance vs benchmarks
        open_vs_benchmark = (open_rate / benchmark_open) * 100 if benchmark_open > 0 else 0
        click_vs_benchmark = (click_rate / benchmark_click) * 100 if benchmark_click > 0 else 0
        order_vs_benchmark = (placed_order_rate / benchmark_order) * 100 if benchmark_order > 0 else 0
        
        # Identify strengths and gaps
        strengths = []
        gaps = []
        
        if open_vs_benchmark >= 100:
            strengths.append(f"open rate ({open_rate:.1f}%) meets or exceeds the industry benchmark")
        else:
            gaps.append(f"open rate ({open_rate:.1f}%) falls {benchmark_open - open_rate:.1f} percentage points below benchmark")
        
        if click_vs_benchmark >= 100:
            strengths.append(f"click rate ({click_rate:.1f}%) demonstrates strong content engagement")
        else:
            gaps.append(f"click rate ({click_rate:.1f}%) indicates content optimization opportunities")
        
        if order_vs_benchmark >= 120:
            strengths.append(f"placed order rate ({placed_order_rate:.1f}%) significantly outperforms benchmark")
        elif order_vs_benchmark >= 100:
            strengths.append(f"placed order rate ({placed_order_rate:.1f}%) meets industry standards")
        else:
            gaps.append(f"placed order rate ({placed_order_rate:.1f}%) suggests conversion optimization potential")
        
        # Build narrative
        if strengths and not gaps:
            return f"Performance exceeds benchmarks across key metrics, with {', '.join(strengths)}."
        elif strengths and gaps:
            return f"Shows mixed performance with {strengths[0]} while {gaps[0]}."
        else:
            return f"Performance indicates optimization opportunities, with {gaps[0]}."
    
    def _generate_flow_recommendations(self, flow_name: str, open_rate: float, click_rate: float, 
                                     placed_order_rate: float, benchmark_open: float, 
                                     benchmark_click: float, benchmark_order: float) -> str:
        """Generate specific recommendations based on performance gaps."""
        
        recommendations = []
        
        # Open rate recommendations
        if open_rate < benchmark_open * 0.9:
            recommendations.append("test curiosity-based subject lines or emphasize exclusivity to improve inbox engagement")
        
        # Click rate recommendations  
        if click_rate < benchmark_click * 0.9:
            recommendations.append("enhance in-email content with clearer CTAs, personalized product recommendations, or urgency messaging")
        
        # Conversion recommendations
        if placed_order_rate < benchmark_order * 0.9:
            recommendations.append("optimize the post-click experience through checkout friction reduction or more persuasive landing page content")
        
        # Flow-specific recommendations
        if "welcome" in flow_name.lower():
            recommendations.append("consider compressing the series to the first 7-10 days when new subscriber engagement is highest")
        elif "abandon" in flow_name.lower():
            recommendations.append("test earlier trigger timing and implement New vs. Returning customer segmentation for more relevant messaging")
        elif "browse" in flow_name.lower():
            recommendations.append("expand to multiple touchpoints and add personalized product feeds based on browsing behavior")
        
        if not recommendations:
            return "Continue current strategy while testing incremental improvements to maintain strong performance."
        
        return "Optimization opportunities include: " + ", ".join(recommendations) + "."
    
    def _determine_flow_priority(self, open_rate: float, click_rate: float, placed_order_rate: float, 
                                benchmarks: Dict[str, float]) -> str:
        """Determine strategic priority level for flow optimization."""
        
        benchmark_gaps = 0
        
        if open_rate < benchmarks.get("open_rate", 50.0) * 0.8:
            benchmark_gaps += 2
        elif open_rate < benchmarks.get("open_rate", 50.0):
            benchmark_gaps += 1
            
        if click_rate < benchmarks.get("click_rate", 4.0) * 0.8:
            benchmark_gaps += 2
        elif click_rate < benchmarks.get("click_rate", 4.0):
            benchmark_gaps += 1
            
        if placed_order_rate < benchmarks.get("placed_order_rate", 2.0) * 0.8:
            benchmark_gaps += 2
        elif placed_order_rate < benchmarks.get("placed_order_rate", 2.0):
            benchmark_gaps += 1
        
        if benchmark_gaps >= 4:
            return "high"
        elif benchmark_gaps >= 2:
            return "medium"
        else:
            return "low"
    
    def generate_list_health_narrative(self, list_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate strategic narrative for list health and engagement.
        
        Args:
            list_data: List metrics including growth, engagement, churn
            
        Returns:
            Strategic narrative about list health and opportunities
        """
        try:
            current_total = list_data.get("current_total", 0)
            growth_rate = list_data.get("growth_rate", 0)
            churn_rate = list_data.get("churn_rate", 0)
            engagement_distribution = list_data.get("engagement", {})
            
            # Calculate engagement percentages
            very_engaged = engagement_distribution.get("very_engaged", 0)
            somewhat_engaged = engagement_distribution.get("somewhat_engaged", 0)
            total_engaged = very_engaged + somewhat_engaged
            no_emails = engagement_distribution.get("no_emails_30d", 0)
            
            # Generate narrative based on list health
            health_narrative = self._assess_list_health(total_engaged, no_emails, growth_rate, churn_rate)
            
            # Identify opportunities
            opportunities = self._identify_list_opportunities(total_engaged, no_emails, current_total)
            
            return {
                "health_assessment": health_narrative,
                "opportunities": opportunities,
                "strategic_priority": "high" if no_emails > 60 else "medium" if total_engaged < 40 else "low"
            }
            
        except Exception as e:
            logger.error(f"Error generating list health narrative: {e}")
            return {
                "health_assessment": "List health analysis requires additional engagement data.",
                "opportunities": "Contact support for detailed analysis.",
                "strategic_priority": "medium"
            }
    
    def _assess_list_health(self, total_engaged: float, no_emails: float, growth_rate: float, churn_rate: float) -> str:
        """Assess overall list health with strategic context."""
        
        engagement_benchmark = self.industry_benchmarks["engagement_benchmark"]
        
        if total_engaged >= engagement_benchmark:
            engagement_status = f"demonstrates healthy engagement with {total_engaged:.1f}% actively engaging"
        else:
            engagement_status = f"shows engagement challenges with only {total_engaged:.1f}% actively engaging, below the {engagement_benchmark:.0f}% benchmark"
        
        if no_emails > 70:
            execution_gap = f"However, {no_emails:.1f}% of profiles have received zero emails in the past 30 days, indicating a significant execution and revenue opportunity."
        elif no_emails > 30:
            execution_gap = f"Additionally, {no_emails:.1f}% of profiles haven't received emails recently, suggesting untapped engagement potential."
        else:
            execution_gap = ""
        
        return f"The email list {engagement_status}. {execution_gap}".strip()
    
    def _identify_list_opportunities(self, total_engaged: float, no_emails: float, current_total: int) -> str:
        """Identify specific list optimization opportunities."""
        
        opportunities = []
        
        if no_emails > 50:
            potential_reach = int((no_emails / 100) * current_total)
            opportunities.append(f"Reactivate {potential_reach:,} dormant profiles through segmented re-engagement campaigns")
        
        if total_engaged < 40:
            opportunities.append("Implement engagement-based segmentation to improve deliverability and reduce churn risk")
        
        if total_engaged < 30:
            opportunities.append("Launch winback flows with preference centers and opt-down options before suppression")
        
        opportunities.append("Optimize signup forms and incentives to attract higher-quality, engagement-ready profiles")
        
        return "; ".join(opportunities) + "." if opportunities else "Continue current list management strategy with minor optimizations."


class BusinessContextService:
    """
    Integrate business challenges and context into audit insights.
    """
    
    @staticmethod
    def detect_business_context(campaign_data: Dict[str, Any], flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect business context from data patterns.
        
        Args:
            campaign_data: Campaign performance and volume data
            flow_data: Flow performance data
            
        Returns:
            Business context indicators
        """
        context = {}
        
        # Detect campaign gap
        recent_campaigns = campaign_data.get("recent_campaign_count", 0)
        context["has_campaign_gap"] = recent_campaigns == 0
        
        # Detect flow performance patterns
        context["flow_dominant"] = campaign_data.get("campaign_revenue_percentage", 0) < 20
        
        # Detect list utilization issues
        context["list_underutilized"] = campaign_data.get("profiles_receiving_no_emails", 0) > 50
        
        return context
    
    @staticmethod
    def generate_context_insights(context: Dict[str, Any], client_name: str = "the brand") -> Dict[str, str]:
        """
        Generate context-specific insights.
        
        Args:
            context: Business context indicators
            client_name: Client brand name
            
        Returns:
            Context-driven insights
        """
        insights = {}
        
        if context.get("has_campaign_gap"):
            insights["campaign_opportunity"] = f"The absence of regular campaign activity represents {client_name}'s highest-leverage growth opportunity, as campaigns create the upstream engagement that flows then convert."
        
        if context.get("flow_dominant"):
            insights["balance_opportunity"] = f"Flow-dominant attribution indicates {client_name} has strong automation but is missing the campaign activity needed for optimal lifecycle balance."
        
        if context.get("list_underutilized"):
            insights["reach_opportunity"] = f"A significant portion of {client_name}'s list represents untapped revenue potential through strategic re-engagement."
        
        return insights