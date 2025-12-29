"""
Strategic Decision Engine - Carissa's Strategic Thinking Framework

This engine replicates Carissa's multi-dimensional decision-making process,
transforming insights into prioritized, implementation-ready recommendations.
"""
from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RecommendationTier(Enum):
    CRITICAL = "critical"        # 0-30 days, immediate impact, low complexity
    HIGH_IMPACT = "high_impact"  # 30-90 days, significant growth, medium complexity
    STRATEGIC = "strategic"      # 90+ days, transformation, high complexity


class ImplementationComplexity(Enum):
    LOW = "low"        # 1-2 weeks, minimal resources
    MEDIUM = "medium"  # 3-8 weeks, moderate resources  
    HIGH = "high"      # 9+ weeks, significant resources


@dataclass
class StrategyRecommendation:
    """Strategic recommendation with Carissa-level analysis."""
    id: str
    title: str
    category: str  # flow_optimization, campaign_strategy, list_health, etc.
    tier: RecommendationTier
    
    # Strategic Analysis
    problem_statement: str
    strategic_rationale: str
    business_impact: str
    
    # Implementation Details
    specific_actions: List[str]
    implementation_complexity: ImplementationComplexity
    estimated_timeline: str
    resource_requirements: List[str]
    
    # Financial Analysis
    revenue_impact_estimate: float
    confidence_level: str  # high, medium, low
    roi_timeline: str
    
    # Prioritization Scores
    priority_score: float  # 0-100 composite score
    impact_score: float    # Revenue/growth impact (0-100)
    effort_score: float    # Implementation effort (0-100, lower = easier)
    urgency_score: float   # Time-sensitive nature (0-100)
    risk_score: float      # Implementation risk (0-100, lower = safer)
    
    # Dependencies and Prerequisites
    prerequisites: List[str]
    dependencies: List[str]
    potential_blockers: List[str]


class StrategicDecisionEngine:
    """
    Carissa's strategic decision-making framework systematized.
    
    Analyzes multiple data sources and generates prioritized,
    implementation-ready strategic recommendations.
    """
    
    def __init__(self):
        self.decision_matrix = self._load_carissa_decision_matrix()
        self.priority_weights = self._load_priority_weights()
        
    def _load_carissa_decision_matrix(self) -> Dict[str, Any]:
        """Load Carissa's strategic decision-making criteria."""
        return {
            "revenue_impact_thresholds": {
                "high": 0.25,      # 25%+ revenue increase
                "medium": 0.15,    # 15-25% revenue increase  
                "low": 0.05        # 5-15% revenue increase
            },
            "complexity_factors": {
                "technical_complexity": 0.3,
                "resource_intensity": 0.25, 
                "timeline_length": 0.25,
                "cross_team_coordination": 0.2
            },
            "urgency_indicators": {
                "revenue_bleeding": 40,      # Immediate revenue loss
                "competitive_pressure": 30,  # Market timing critical
                "seasonal_timing": 20,       # Seasonal opportunity window
                "foundation_building": 10    # Strategic foundation
            },
            "risk_assessment": {
                "implementation_risk": 0.4,
                "business_disruption": 0.3,
                "financial_exposure": 0.3
            }
        }
    
    def _load_priority_weights(self) -> Dict[str, float]:
        """Load Carissa's priority weighting system."""
        return {
            "impact_weight": 0.35,    # Revenue/growth impact
            "effort_weight": 0.25,    # Implementation difficulty (inverted)
            "urgency_weight": 0.25,   # Time-sensitive nature
            "risk_weight": 0.15       # Implementation risk (inverted)
        }
    
    def generate_strategic_recommendations(
        self, 
        analysis_results: Dict[str, Any],
        client_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive strategic recommendations using Carissa's framework.
        
        Args:
            analysis_results: Combined analysis from all previous phases
            client_context: Business context and constraints
            
        Returns:
            Comprehensive strategic recommendation framework
        """
        try:
            recommendations = []
            
            # Analyze each major area for strategic opportunities
            areas_to_analyze = [
                "flow_optimization",
                "campaign_strategy", 
                "list_health",
                "data_capture",
                "segmentation"
            ]
            
            for area in areas_to_analyze:
                area_recommendations = self._analyze_area_for_recommendations(
                    area, analysis_results, client_context
                )
                recommendations.extend(area_recommendations)
            
            # Apply Carissa's prioritization framework
            prioritized_recommendations = self._apply_strategic_prioritization(
                recommendations, client_context
            )
            
            # Create implementation roadmap
            implementation_roadmap = self._create_strategic_roadmap(
                prioritized_recommendations
            )
            
            # Generate executive summary
            executive_summary = self._generate_strategic_executive_summary(
                prioritized_recommendations, implementation_roadmap
            )
            
            return {
                "executive_summary": executive_summary,
                "recommendations": {
                    "tier_1_critical": [r for r in prioritized_recommendations 
                                      if r.tier == RecommendationTier.CRITICAL],
                    "tier_2_high_impact": [r for r in prioritized_recommendations 
                                         if r.tier == RecommendationTier.HIGH_IMPACT],
                    "tier_3_strategic": [r for r in prioritized_recommendations 
                                       if r.tier == RecommendationTier.STRATEGIC]
                },
                "implementation_roadmap": implementation_roadmap,
                "total_revenue_impact": sum(r.revenue_impact_estimate for r in prioritized_recommendations),
                "quick_wins": [r for r in prioritized_recommendations 
                             if r.implementation_complexity == ImplementationComplexity.LOW][:3],
                "strategic_priorities": self._identify_strategic_priorities(prioritized_recommendations)
            }
            
        except Exception as e:
            logger.error(f"Error generating strategic recommendations: {e}")
            return {
                "error": True,
                "message": "Strategic recommendations require comprehensive analysis data"
            }
    
    def _analyze_area_for_recommendations(
        self, 
        area: str, 
        analysis_results: Dict[str, Any],
        client_context: Dict[str, Any] = None
    ) -> List[StrategyRecommendation]:
        """Analyze specific area for strategic recommendations."""
        recommendations = []
        
        if area == "flow_optimization":
            recommendations.extend(self._analyze_flow_optimization_opportunities(
                analysis_results, client_context
            ))
        elif area == "campaign_strategy":
            recommendations.extend(self._analyze_campaign_strategy_opportunities(
                analysis_results, client_context
            ))
        elif area == "list_health":
            recommendations.extend(self._analyze_list_health_opportunities(
                analysis_results, client_context
            ))
        elif area == "data_capture":
            recommendations.extend(self._analyze_data_capture_opportunities(
                analysis_results, client_context
            ))
        elif area == "segmentation":
            recommendations.extend(self._analyze_segmentation_opportunities(
                analysis_results, client_context
            ))
        
        return recommendations
    
    def _analyze_flow_optimization_opportunities(
        self, 
        analysis_results: Dict[str, Any],
        client_context: Dict[str, Any] = None
    ) -> List[StrategyRecommendation]:
        """Analyze flow data for strategic optimization opportunities."""
        recommendations = []
        
        # Get flow analysis from Phase 2
        flow_lifecycle_analysis = analysis_results.get("automation_overview_data", {}).get("flow_lifecycle_analysis")
        if not flow_lifecycle_analysis:
            return recommendations
        
        optimization_matrix = flow_lifecycle_analysis.get("optimization_priority_matrix", {})
        top_priority = optimization_matrix.get("top_priority")
        
        if top_priority:
            # Create strategic recommendation for top priority flow
            rec = StrategyRecommendation(
                id=f"flow_opt_{top_priority.get('flow_type', 'unknown')}",
                title=f"Optimize {top_priority.get('flow_name', 'Priority Flow')} for Maximum Revenue Impact",
                category="flow_optimization",
                tier=self._determine_recommendation_tier(
                    impact=top_priority.get('estimated_revenue_impact', 0),
                    complexity=top_priority.get('performance_tier', 'average')
                ),
                problem_statement=f"{top_priority.get('flow_name')} shows {top_priority.get('performance_tier')} performance with clear optimization potential",
                strategic_rationale=f"Flow optimization represents immediate revenue opportunity with {top_priority.get('key_optimization')} as the primary lever",
                business_impact=f"Estimated ${top_priority.get('estimated_revenue_impact', 0):,.0f} revenue uplift through strategic flow enhancement",
                specific_actions=self._get_flow_optimization_actions(top_priority),
                implementation_complexity=self._assess_flow_implementation_complexity(top_priority),
                estimated_timeline=self._estimate_flow_optimization_timeline(top_priority),
                resource_requirements=["Email marketing specialist", "Klaviyo flow configuration", "A/B testing setup"],
                revenue_impact_estimate=top_priority.get('estimated_revenue_impact', 0),
                confidence_level="high",
                roi_timeline="30-60 days",
                priority_score=0,  # Will be calculated
                impact_score=0,    # Will be calculated
                effort_score=0,    # Will be calculated
                urgency_score=0,   # Will be calculated
                risk_score=0,      # Will be calculated
                prerequisites=[],
                dependencies=[],
                potential_blockers=["Rate limiting", "Complex segmentation requirements"]
            )
            
            # Calculate scores
            rec.impact_score = self._calculate_impact_score(rec)
            rec.effort_score = self._calculate_effort_score(rec)
            rec.urgency_score = self._calculate_urgency_score(rec)
            rec.risk_score = self._calculate_risk_score(rec)
            rec.priority_score = self._calculate_priority_score(rec)
            
            recommendations.append(rec)
        
        return recommendations
    
    def _determine_recommendation_tier(self, impact: float, complexity: str) -> RecommendationTier:
        """Determine recommendation tier based on impact and complexity."""
        if impact > 10000 and complexity in ["good", "excellent"]:  # High impact, manageable complexity
            return RecommendationTier.CRITICAL
        elif impact > 5000:  # Significant impact
            return RecommendationTier.HIGH_IMPACT
        else:
            return RecommendationTier.STRATEGIC
    
    def _get_flow_optimization_actions(self, flow_priority: Dict[str, Any]) -> List[str]:
        """Get specific optimization actions for a flow."""
        flow_type = flow_priority.get('flow_type', '')
        actions = []
        
        if 'welcome' in flow_type:
            actions.extend([
                "Compress welcome series to first 7-10 days when engagement is highest",
                "Implement New vs Returning customer segmentation",
                "Add dynamic content blocks based on browsing behavior"
            ])
        elif 'abandon' in flow_type:
            actions.extend([
                "Test trigger timing optimization (20min vs 2hr vs 4hr)",
                "Implement New vs Returning customer segmentation",
                "Add personalized product recommendations with urgency messaging"
            ])
        elif 'browse' in flow_type:
            actions.extend([
                "Expand to 2-touchpoint sequence (24hr, 3-day)",
                "Add dynamic product feeds based on browsed items",
                "Implement behavioral segmentation"
            ])
        
        return actions
    
    # Additional helper methods for scoring and analysis...
    def _calculate_impact_score(self, rec: StrategyRecommendation) -> float:
        """Calculate impact score based on revenue potential."""
        if rec.revenue_impact_estimate > 20000:
            return 100
        elif rec.revenue_impact_estimate > 10000:
            return 80
        elif rec.revenue_impact_estimate > 5000:
            return 60
        else:
            return 40
    
    def _calculate_effort_score(self, rec: StrategyRecommendation) -> float:
        """Calculate effort score (lower is better)."""
        complexity_scores = {
            ImplementationComplexity.LOW: 20,
            ImplementationComplexity.MEDIUM: 50,
            ImplementationComplexity.HIGH: 80
        }
        return complexity_scores.get(rec.implementation_complexity, 50)
    
    def _calculate_urgency_score(self, rec: StrategyRecommendation) -> float:
        """Calculate urgency score based on opportunity timing."""
        if rec.tier == RecommendationTier.CRITICAL:
            return 90
        elif rec.tier == RecommendationTier.HIGH_IMPACT:
            return 70
        else:
            return 40
    
    def _calculate_risk_score(self, rec: StrategyRecommendation) -> float:
        """Calculate implementation risk score (lower is better)."""
        base_risk = 30  # Base implementation risk
        
        # Add risk based on complexity
        complexity_risk = {
            ImplementationComplexity.LOW: 10,
            ImplementationComplexity.MEDIUM: 30,
            ImplementationComplexity.HIGH: 50
        }
        
        return base_risk + complexity_risk.get(rec.implementation_complexity, 30)
    
    def _calculate_priority_score(self, rec: StrategyRecommendation) -> float:
        """Calculate composite priority score using Carissa's weighting."""
        weights = self.priority_weights
        
        # Invert effort and risk scores (lower is better)
        effort_score_inverted = 100 - rec.effort_score
        risk_score_inverted = 100 - rec.risk_score
        
        priority_score = (
            rec.impact_score * weights["impact_weight"] +
            effort_score_inverted * weights["effort_weight"] +
            rec.urgency_score * weights["urgency_weight"] +
            risk_score_inverted * weights["risk_weight"]
        )
        
        return round(priority_score, 2)
    
    # Implemented analysis methods for other areas
    def _analyze_campaign_strategy_opportunities(self, analysis_results: Dict[str, Any], client_context: Dict[str, Any] = None) -> List[StrategyRecommendation]:
        """Analyze campaign strategy opportunities."""
        recommendations = []
        
        # Get campaign data
        campaign_data = analysis_results.get("campaign_performance_data", {})
        kav_data = analysis_results.get("kav_data", {})
        
        campaign_revenue = kav_data.get("revenue", {}).get("campaign_attributed", 0)
        flow_revenue = kav_data.get("revenue", {}).get("flow_attributed", 0)
        
        # If campaign revenue is low compared to flow revenue, recommend campaign reintroduction
        if campaign_revenue < flow_revenue * 0.3 and flow_revenue > 0:
            estimated_impact = flow_revenue * 0.5  # Conservative estimate
            
            rec = StrategyRecommendation(
                id="campaign_reintroduction",
                title="Reintroduce Regular Campaign Activity to Drive Engagement",
                category="campaign_strategy",
                tier=RecommendationTier.CRITICAL if estimated_impact > 10000 else RecommendationTier.HIGH_IMPACT,
                problem_statement=f"Campaign revenue (${campaign_revenue:,.0f}) is significantly lower than flow revenue (${flow_revenue:,.0f}), indicating minimal campaign activity",
                strategic_rationale="Campaigns and flows work as a connected system—campaigns stimulate demand while flows capture intent",
                business_impact=f"Estimated ${estimated_impact:,.0f} revenue uplift through strategic campaign reintroduction",
                specific_actions=[
                    "Launch weekly promotional campaigns to re-engage list",
                    "Implement product launch campaigns for new releases",
                    "Create seasonal campaigns aligned with business calendar"
                ],
                implementation_complexity=ImplementationComplexity.MEDIUM,
                estimated_timeline="4-6 weeks",
                resource_requirements=["Email marketing specialist", "Content creation", "Campaign planning"],
                revenue_impact_estimate=estimated_impact,
                confidence_level="high",
                roi_timeline="60-90 days",
                priority_score=0,
                impact_score=0,
                effort_score=0,
                urgency_score=0,
                risk_score=0,
                prerequisites=[],
                dependencies=[],
                potential_blockers=["Content creation capacity", "Design resources"]
            )
            
            rec.impact_score = self._calculate_impact_score(rec)
            rec.effort_score = self._calculate_effort_score(rec)
            rec.urgency_score = self._calculate_urgency_score(rec)
            rec.risk_score = self._calculate_risk_score(rec)
            rec.priority_score = self._calculate_priority_score(rec)
            
            recommendations.append(rec)
        
        return recommendations
    
    def _analyze_list_health_opportunities(self, analysis_results: Dict[str, Any], client_context: Dict[str, Any] = None) -> List[StrategyRecommendation]:
        """Analyze list health opportunities."""
        recommendations = []
        
        list_data = analysis_results.get("list_growth_data", {})
        churn_rate = list_data.get("churn_rate", 0)
        current_total = list_data.get("current_total", 0)
        
        # If churn rate is high, recommend reactivation
        if churn_rate > 5 and current_total > 0:
            estimated_impact = current_total * 0.10 * 50  # 10% reactivation, $50 avg order
            
            rec = StrategyRecommendation(
                id="list_reactivation",
                title="Implement List Reactivation Strategy",
                category="list_health",
                tier=RecommendationTier.HIGH_IMPACT,
                problem_statement=f"Churn rate of {churn_rate:.1f}% indicates list health issues requiring attention",
                strategic_rationale="Reactivation campaigns can recover lost revenue from disengaged subscribers",
                business_impact=f"Estimated ${estimated_impact:,.0f} revenue recovery potential",
                specific_actions=[
                    "Create win-back email series for inactive subscribers",
                    "Implement sunset flow for unengaged profiles",
                    "Segment list by engagement level for targeted messaging"
                ],
                implementation_complexity=ImplementationComplexity.LOW,
                estimated_timeline="2-3 weeks",
                resource_requirements=["Flow configuration", "Email templates"],
                revenue_impact_estimate=estimated_impact,
                confidence_level="medium",
                roi_timeline="30-60 days",
                priority_score=0,
                impact_score=0,
                effort_score=0,
                urgency_score=0,
                risk_score=0,
                prerequisites=[],
                dependencies=[],
                potential_blockers=[]
            )
            
            rec.impact_score = self._calculate_impact_score(rec)
            rec.effort_score = self._calculate_effort_score(rec)
            rec.urgency_score = self._calculate_urgency_score(rec)
            rec.risk_score = self._calculate_risk_score(rec)
            rec.priority_score = self._calculate_priority_score(rec)
            
            recommendations.append(rec)
        
        return recommendations
    
    def _analyze_data_capture_opportunities(self, analysis_results: Dict[str, Any], client_context: Dict[str, Any] = None) -> List[StrategyRecommendation]:
        """Analyze data capture opportunities."""
        recommendations = []
        
        form_data = analysis_results.get("data_capture_data", {})
        forms = form_data.get("forms", [])
        
        # Find forms with low submit rates
        low_performing_forms = [f for f in forms if f.get("submit_rate", 0) < 5 and f.get("views", 0) > 0]
        
        if low_performing_forms:
            total_views = sum(f.get("views", 0) for f in low_performing_forms)
            potential_captures = total_views * 0.10  # 10% improvement potential
            estimated_impact = potential_captures * 50  # $50 avg customer value
            
            rec = StrategyRecommendation(
                id="form_optimization",
                title="Optimize Form Performance to Increase Data Capture",
                category="data_capture",
                tier=RecommendationTier.HIGH_IMPACT if estimated_impact > 5000 else RecommendationTier.STRATEGIC,
                problem_statement=f"{len(low_performing_forms)} forms showing low submit rates (<5%), missing data capture opportunities",
                strategic_rationale="Form optimization directly increases list growth and marketing reach",
                business_impact=f"Estimated ${estimated_impact:,.0f} revenue potential from improved data capture",
                specific_actions=[
                    "A/B test form designs and copy",
                    "Optimize form placement and timing",
                    "Implement exit-intent popups for better capture rates"
                ],
                implementation_complexity=ImplementationComplexity.LOW,
                estimated_timeline="2-4 weeks",
                resource_requirements=["Design resources", "A/B testing setup"],
                revenue_impact_estimate=estimated_impact,
                confidence_level="medium",
                roi_timeline="30-45 days",
                priority_score=0,
                impact_score=0,
                effort_score=0,
                urgency_score=0,
                risk_score=0,
                prerequisites=[],
                dependencies=[],
                potential_blockers=["Design resources"]
            )
            
            rec.impact_score = self._calculate_impact_score(rec)
            rec.effort_score = self._calculate_effort_score(rec)
            rec.urgency_score = self._calculate_urgency_score(rec)
            rec.risk_score = self._calculate_risk_score(rec)
            rec.priority_score = self._calculate_priority_score(rec)
            
            recommendations.append(rec)
        
        return recommendations
    
    def _analyze_segmentation_opportunities(self, analysis_results: Dict[str, Any], client_context: Dict[str, Any] = None) -> List[StrategyRecommendation]:
        """Analyze segmentation opportunities."""
        recommendations = []
        
        segmentation_data = analysis_results.get("segmentation_data", {})
        automation_data = analysis_results.get("automation_overview_data", {})
        
        # Check if segmentation is being used effectively
        flows = automation_data.get("flows", [])
        if flows:
            # Estimate impact of better segmentation
            total_flow_revenue = sum(f.get("revenue", 0) for f in flows)
            estimated_impact = total_flow_revenue * 0.15  # 15% improvement from segmentation
            
            if estimated_impact > 1000:
                rec = StrategyRecommendation(
                    id="segmentation_enhancement",
                    title="Enhance Flow Segmentation for Better Targeting",
                    category="segmentation",
                    tier=RecommendationTier.STRATEGIC,
                    problem_statement="Flows may not be using advanced segmentation for optimal targeting",
                    strategic_rationale="Segmentation improves relevance and engagement, driving higher conversion rates",
                    business_impact=f"Estimated ${estimated_impact:,.0f} revenue uplift through improved segmentation",
                    specific_actions=[
                        "Implement behavioral segmentation in flows",
                        "Create customer lifecycle segments",
                        "Add purchase history-based targeting"
                    ],
                    implementation_complexity=ImplementationComplexity.MEDIUM,
                    estimated_timeline="4-6 weeks",
                    resource_requirements=["Segmentation strategy", "Flow reconfiguration"],
                    revenue_impact_estimate=estimated_impact,
                    confidence_level="medium",
                    roi_timeline="60-90 days",
                    priority_score=0,
                    impact_score=0,
                    effort_score=0,
                    urgency_score=0,
                    risk_score=0,
                    prerequisites=[],
                    dependencies=[],
                    potential_blockers=["Data quality", "Segmentation complexity"]
                )
                
                rec.impact_score = self._calculate_impact_score(rec)
                rec.effort_score = self._calculate_effort_score(rec)
                rec.urgency_score = self._calculate_urgency_score(rec)
                rec.risk_score = self._calculate_risk_score(rec)
                rec.priority_score = self._calculate_priority_score(rec)
                
                recommendations.append(rec)
        
        return recommendations
    
    def _apply_strategic_prioritization(self, recommendations: List[StrategyRecommendation], client_context: Dict[str, Any] = None) -> List[StrategyRecommendation]:
        """Apply Carissa's strategic prioritization framework."""
        return sorted(recommendations, key=lambda r: r.priority_score, reverse=True)
    
    def _create_strategic_roadmap(self, recommendations: List[StrategyRecommendation]) -> List[Dict[str, Any]]:
        """Create strategic implementation roadmap."""
        return []  # Will implement
    
    def _generate_strategic_executive_summary(self, recommendations: List[StrategyRecommendation], roadmap: List[Dict[str, Any]]) -> str:
        """Generate executive summary of strategic recommendations."""
        if not recommendations:
            return "Strategic analysis requires comprehensive data for recommendation generation."
        
        total_impact = sum(r.revenue_impact_estimate for r in recommendations)
        critical_count = len([r for r in recommendations if r.tier == RecommendationTier.CRITICAL])
        
        return f"Strategic analysis identifies {len(recommendations)} optimization opportunities with ${total_impact:,.0f} total revenue potential. {critical_count} critical initiatives require immediate attention for maximum impact."
    
    def _identify_strategic_priorities(self, recommendations: List[StrategyRecommendation]) -> List[str]:
        """Identify top strategic priorities."""
        return [rec.title for rec in recommendations[:3]]
    
    # Additional helper methods will be implemented as needed
    def _assess_flow_implementation_complexity(self, flow_priority: Dict[str, Any]) -> ImplementationComplexity:
        """Assess implementation complexity for flow optimization."""
        performance_tier = flow_priority.get('performance_tier', 'average')
        
        if performance_tier in ['poor', 'average']:
            return ImplementationComplexity.MEDIUM  # Requires more extensive changes
        else:
            return ImplementationComplexity.LOW     # Incremental improvements
    
    def _estimate_flow_optimization_timeline(self, flow_priority: Dict[str, Any]) -> str:
        """Estimate timeline for flow optimization."""
        complexity = self._assess_flow_implementation_complexity(flow_priority)
        
        timeline_map = {
            ImplementationComplexity.LOW: "2-3 weeks",
            ImplementationComplexity.MEDIUM: "4-6 weeks", 
            ImplementationComplexity.HIGH: "8-12 weeks"
        }
        
        return timeline_map.get(complexity, "4-6 weeks")