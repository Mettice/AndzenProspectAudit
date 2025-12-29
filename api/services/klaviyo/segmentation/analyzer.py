"""
Advanced Segmentation Analyzer - Carissa-level segmentation insights
"""
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class SegmentationAnalyzer:
    """
    Analyze current segmentation vs Carissa's best practices.
    
    Provides sophisticated analysis of flow segmentation, list health segments,
    and engagement-based targeting with specific improvement recommendations.
    """
    
    def __init__(self):
        self.best_practices = self._load_segmentation_best_practices()
    
    def _load_segmentation_best_practices(self) -> Dict[str, Any]:
        """Load Carissa's segmentation best practices."""
        return {
            "flow_segmentation": {
                "abandoned_cart": {
                    "current_common": "sale_vs_non_sale",
                    "recommended": "new_vs_returning",
                    "reasoning": "Customer journey stage drives more relevant messaging than discount status",
                    "expected_uplift": "20-30% improvement in conversion rates",
                    "implementation": {
                        "new_customers": "Trust-building, first-purchase incentives, brand education",
                        "returning_customers": "Loyalty messaging, personalized recommendations, urgency"
                    }
                },
                "welcome_series": {
                    "basic_segmentation": "single_flow",
                    "recommended_segments": ["new_vs_returning", "shopping_preference", "signup_source"],
                    "advanced_personalization": {
                        "new_customers": "Brand introduction, value propositions, product education",
                        "returning_customers": "Thank you messaging, exclusive offers, new arrivals",
                        "gender_based": "Conditional hero images and product feeds",
                        "source_based": "Context-specific messaging based on signup origin"
                    }
                },
                "browse_abandonment": {
                    "behavior_based": {
                        "collection_browsers": "Category-level inspiration and curation",
                        "product_viewers": "Specific product focus with alternatives",
                        "search_users": "Query-specific recommendations",
                        "high_frequency": "VIP treatment and exclusive access"
                    },
                    "customer_type": {
                        "new_visitors": "Trust-building and brand education",
                        "returning_customers": "Personalized based on purchase history"
                    }
                },
                "post_purchase": {
                    "purchase_count_segmentation": {
                        "first_time": "Same category repetition for confidence building",
                        "2x_purchasers": "Cross-category expansion opportunities", 
                        "repeat_customers": "VIP treatment and lifestyle positioning"
                    },
                    "cltv_segmentation": {
                        "entry_price": "Upgrade to hero products",
                        "mid_tier": "Complete-the-look strategies",
                        "high_value": "Exclusive previews and early access"
                    }
                }
            },
            "engagement_segmentation": {
                "benchmark_distribution": {
                    "very_engaged": 30,  # % of list that should be very engaged
                    "somewhat_engaged": 20,  # % somewhat engaged
                    "barely_engaged": 15,   # % barely engaged
                    "not_engaged": 10,      # % not engaged
                    "no_emails_30d": 25     # % who received no emails (max recommended)
                },
                "engagement_strategies": {
                    "very_engaged": "Premium content, early access, advocacy programs",
                    "somewhat_engaged": "Re-engagement with value-driven content",
                    "barely_engaged": "Preference centers, content optimization",
                    "not_engaged": "Winback flows, opt-down options",
                    "no_emails_30d": "Segmented reactivation campaigns"
                }
            },
            "list_health_optimization": {
                "reactivation_strategies": {
                    "90_day_inactive": "Soft re-engagement with preference center",
                    "180_day_inactive": "Stronger incentives and value reminders",
                    "365_day_inactive": "Final winback before suppression"
                },
                "billing_optimization": {
                    "no_emails_threshold": 50,  # % above which billing efficiency is poor
                    "suppression_criteria": "No engagement in 365+ days",
                    "cost_savings_potential": "20-40% reduction in Klaviyo costs"
                }
            }
        }
    
    def analyze_flow_segmentation(self, flows_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze current flow segmentation vs Carissa's best practices.
        
        Args:
            flows_data: Dictionary of flow configurations and performance
            
        Returns:
            Comprehensive segmentation analysis with specific recommendations
        """
        try:
            segmentation_analysis = {}
            improvement_opportunities = []
            priority_implementations = []
            
            # Analyze each core flow type
            for flow_type in ["welcome_series", "abandoned_cart", "browse_abandonment", "post_purchase"]:
                flow_data = flows_data.get(flow_type, {})
                if flow_data.get("found", False):
                    analysis = self._analyze_individual_flow_segmentation(flow_type, flow_data)
                    segmentation_analysis[flow_type] = analysis
                    
                    if analysis.get("improvement_potential", "low") in ["high", "medium"]:
                        improvement_opportunities.append({
                            "flow_type": flow_type,
                            "current_approach": analysis.get("current_segmentation", "basic"),
                            "recommended_approach": analysis.get("recommended_segmentation", "enhanced"),
                            "expected_uplift": analysis.get("expected_uplift", "10-20%"),
                            "implementation_complexity": analysis.get("implementation_complexity", "medium")
                        })
                        
                        if analysis.get("implementation_complexity") == "low":
                            priority_implementations.append(flow_type)
            
            # Generate overall recommendations
            overall_strategy = self._generate_overall_segmentation_strategy(improvement_opportunities)
            
            return {
                "individual_flow_analysis": segmentation_analysis,
                "improvement_opportunities": improvement_opportunities,
                "priority_implementations": priority_implementations,
                "overall_strategy": overall_strategy,
                "implementation_roadmap": self._create_segmentation_implementation_roadmap(
                    improvement_opportunities
                ),
                "revenue_impact_estimate": self._estimate_segmentation_revenue_impact(
                    improvement_opportunities, flows_data
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing flow segmentation: {e}")
            return {
                "error": True,
                "message": "Flow segmentation analysis requires flow configuration data"
            }
    
    def analyze_list_health_segments(self, engagement_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze list engagement distribution and health segments.
        
        Args:
            engagement_data: List engagement distribution data
            
        Returns:
            List health analysis with reactivation strategies
        """
        try:
            # Extract engagement distribution
            engagement_dist = engagement_data.get("engagement_distribution", {})
            total_profiles = engagement_data.get("total_profiles", 0)
            
            # Calculate percentages
            engagement_percentages = self._calculate_engagement_percentages(
                engagement_dist, total_profiles
            )
            
            # Compare to benchmarks
            benchmark_comparison = self._compare_engagement_to_benchmarks(engagement_percentages)
            
            # Identify problem areas
            problem_areas = self._identify_engagement_problem_areas(
                engagement_percentages, benchmark_comparison
            )
            
            # Generate reactivation strategies
            reactivation_strategies = self._generate_reactivation_strategies(
                engagement_percentages, problem_areas
            )
            
            # Calculate billing impact
            billing_analysis = self._analyze_billing_efficiency(engagement_percentages, total_profiles)
            
            return {
                "engagement_distribution": engagement_percentages,
                "benchmark_comparison": benchmark_comparison,
                "list_health_status": self._calculate_overall_list_health(benchmark_comparison),
                "problem_areas": problem_areas,
                "reactivation_strategies": reactivation_strategies,
                "billing_efficiency": billing_analysis,
                "strategic_recommendations": self._generate_list_health_recommendations(
                    problem_areas, billing_analysis
                ),
                "implementation_priority": self._calculate_list_health_priority(problem_areas)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing list health segments: {e}")
            return {
                "error": True,
                "message": "List health analysis requires engagement distribution data"
            }
    
    def generate_segmentation_recommendations(self, flow_analysis: Dict[str, Any], 
                                            list_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive segmentation recommendations combining flow and list insights.
        
        Args:
            flow_analysis: Flow segmentation analysis results
            list_analysis: List health analysis results
            
        Returns:
            Comprehensive segmentation strategy with prioritized implementation plan
        """
        try:
            # Combine insights from both analyses
            combined_opportunities = []
            
            # Flow segmentation opportunities
            if not flow_analysis.get("error"):
                flow_opportunities = flow_analysis.get("improvement_opportunities", [])
                for opp in flow_opportunities:
                    combined_opportunities.append({
                        "category": "flow_segmentation",
                        "type": opp["flow_type"],
                        "impact": opp.get("expected_uplift", "medium"),
                        "complexity": opp.get("implementation_complexity", "medium"),
                        "priority_score": self._calculate_opportunity_priority_score(opp)
                    })
            
            # List health opportunities
            if not list_analysis.get("error"):
                list_opportunities = list_analysis.get("problem_areas", [])
                for area in list_opportunities:
                    combined_opportunities.append({
                        "category": "list_health",
                        "type": area.get("area", "engagement"),
                        "impact": area.get("impact_level", "medium"),
                        "complexity": "low",  # List segmentation typically easier
                        "priority_score": self._calculate_list_health_priority_score(area)
                    })
            
            # Sort by priority score
            combined_opportunities.sort(key=lambda x: x["priority_score"], reverse=True)
            
            # Generate implementation timeline
            implementation_timeline = self._create_combined_implementation_timeline(
                combined_opportunities
            )
            
            # Calculate total revenue impact
            total_revenue_impact = self._calculate_total_segmentation_impact(
                flow_analysis, list_analysis
            )
            
            return {
                "prioritized_opportunities": combined_opportunities[:5],  # Top 5
                "implementation_timeline": implementation_timeline,
                "total_revenue_impact": total_revenue_impact,
                "quick_wins": [opp for opp in combined_opportunities 
                             if opp["complexity"] == "low"][:3],
                "high_impact_initiatives": [opp for opp in combined_opportunities 
                                          if opp["impact"] in ["high", "25-35%"]][:3],
                "strategic_narrative": self._generate_segmentation_strategic_narrative(
                    combined_opportunities, total_revenue_impact
                )
            }
            
        except Exception as e:
            logger.error(f"Error generating segmentation recommendations: {e}")
            return {
                "error": True,
                "message": "Comprehensive segmentation analysis requires both flow and list data"
            }
    
    def _analyze_individual_flow_segmentation(self, flow_type: str, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze segmentation for an individual flow type."""
        best_practices = self.best_practices["flow_segmentation"].get(flow_type, {})
        
        if not best_practices:
            return {"analysis_available": False}
        
        # Detect current segmentation approach (simplified - would need actual flow config)
        current_segmentation = self._detect_current_segmentation(flow_data)
        
        # Compare to best practices
        recommended_approach = best_practices.get("recommended", "new_vs_returning")
        
        if isinstance(recommended_approach, list):
            recommended_approach = recommended_approach[0]  # Take primary recommendation
        
        improvement_potential = "high" if current_segmentation == "basic" else "medium"
        
        return {
            "analysis_available": True,
            "flow_name": flow_data.get("name", flow_type),
            "current_segmentation": current_segmentation,
            "recommended_segmentation": recommended_approach,
            "improvement_potential": improvement_potential,
            "expected_uplift": best_practices.get("expected_uplift", "15-25%"),
            "implementation_complexity": "low" if flow_type == "abandoned_cart" else "medium",
            "specific_recommendations": self._get_flow_specific_recommendations(flow_type, best_practices),
            "reasoning": best_practices.get("reasoning", "Enhanced relevance through better targeting")
        }
    
    def _detect_current_segmentation(self, flow_data: Dict[str, Any]) -> str:
        """Detect current segmentation approach from flow data."""
        # Simplified detection - in reality would analyze flow configuration
        flow_name = flow_data.get("name", "").lower()
        
        if "new" in flow_name or "returning" in flow_name:
            return "new_vs_returning"
        elif "sale" in flow_name or "discount" in flow_name:
            return "sale_vs_non_sale"
        elif "sms" in flow_name:
            return "channel_based"
        else:
            return "basic"
    
    def _get_flow_specific_recommendations(self, flow_type: str, best_practices: Dict[str, Any]) -> List[str]:
        """Get specific recommendations for a flow type."""
        recommendations = []
        
        if flow_type == "abandoned_cart":
            recommendations.extend([
                "Segment by New vs Returning customers instead of sale vs non-sale",
                "New customers: Highlight first-time perks and unused welcome codes",
                "Returning customers: Show loyalty points and purchase history-based urgency"
            ])
        elif flow_type == "welcome_series":
            recommendations.extend([
                "Implement shopping preference segmentation for relevant imagery",
                "Use conditional content blocks based on signup source",
                "Add progressive profiling to collect preferences gradually"
            ])
        elif flow_type == "browse_abandonment":
            recommendations.extend([
                "Segment by browsing behavior (collection vs product vs search)",
                "New visitors: Focus on trust-building and brand education",
                "Returning customers: Personalize based on purchase history"
            ])
        elif flow_type == "post_purchase":
            recommendations.extend([
                "Implement purchase count segmentation (1st, 2nd, 3+ purchases)",
                "Use CLTV-based recommendations for cross-selling",
                "Add PDNO triggers instead of fixed timing"
            ])
        
        return recommendations
    
    def _calculate_engagement_percentages(self, engagement_dist: Dict[str, int], 
                                        total_profiles: int) -> Dict[str, float]:
        """Calculate engagement distribution percentages."""
        if total_profiles == 0:
            return {}
        
        percentages = {}
        for category, count in engagement_dist.items():
            percentages[category] = (count / total_profiles) * 100
        
        return percentages
    
    def _compare_engagement_to_benchmarks(self, engagement_percentages: Dict[str, float]) -> Dict[str, Any]:
        """Compare engagement distribution to Carissa's benchmarks."""
        benchmarks = self.best_practices["engagement_segmentation"]["benchmark_distribution"]
        comparison = {}
        
        for category, percentage in engagement_percentages.items():
            if category in benchmarks:
                benchmark_value = benchmarks[category]
                difference = percentage - benchmark_value
                
                if category == "no_emails_30d":
                    # For no emails, lower is better
                    status = "good" if percentage < benchmark_value else "poor"
                else:
                    # For engagement categories, higher is better
                    status = "good" if percentage >= benchmark_value else "poor"
                
                comparison[category] = {
                    "actual": percentage,
                    "benchmark": benchmark_value,
                    "difference": difference,
                    "status": status
                }
        
        return comparison
    
    def _identify_engagement_problem_areas(self, engagement_percentages: Dict[str, float],
                                         benchmark_comparison: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify problem areas in engagement distribution."""
        problems = []
        
        for category, comparison in benchmark_comparison.items():
            if comparison["status"] == "poor":
                severity = "high" if abs(comparison["difference"]) > 15 else "medium"
                
                problems.append({
                    "area": category,
                    "severity": severity,
                    "gap": comparison["difference"],
                    "impact_level": "high" if category in ["very_engaged", "no_emails_30d"] else "medium",
                    "description": self._get_problem_description(category, comparison)
                })
        
        return problems
    
    def _get_problem_description(self, category: str, comparison: Dict[str, Any]) -> str:
        """Get description of engagement problem."""
        descriptions = {
            "very_engaged": f"Only {comparison['actual']:.1f}% of list is very engaged (benchmark: {comparison['benchmark']:.1f}%)",
            "somewhat_engaged": f"Somewhat engaged segment is {comparison['actual']:.1f}% vs {comparison['benchmark']:.1f}% benchmark",
            "barely_engaged": f"Too many barely engaged subscribers ({comparison['actual']:.1f}% vs {comparison['benchmark']:.1f}%)",
            "not_engaged": f"High percentage of non-engaged subscribers ({comparison['actual']:.1f}%)",
            "no_emails_30d": f"Significant execution gap: {comparison['actual']:.1f}% received no emails in 30 days"
        }
        
        return descriptions.get(category, f"{category} performance below benchmark")
    
    def _generate_reactivation_strategies(self, engagement_percentages: Dict[str, float],
                                        problem_areas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate specific reactivation strategies."""
        strategies = {}
        
        # High-level strategies based on problem areas
        for problem in problem_areas:
            area = problem["area"]
            strategies[area] = {
                "strategy": self._get_reactivation_strategy(area),
                "implementation": self._get_reactivation_implementation(area),
                "expected_improvement": self._get_expected_improvement(area, problem["gap"])
            }
        
        # Overall reactivation approach
        no_emails_pct = engagement_percentages.get("no_emails_30d", 0)
        if no_emails_pct > 50:
            strategies["overall_approach"] = {
                "priority": "high",
                "focus": "Systematic reactivation of dormant profiles",
                "phased_approach": [
                    "Start with 90-day inactive segments",
                    "Implement preference centers before winback",
                    "Create engagement-based send frequency rules"
                ]
            }
        
        return strategies
    
    def _get_reactivation_strategy(self, category: str) -> str:
        """Get specific reactivation strategy for engagement category."""
        strategies = {
            "very_engaged": "Expand very engaged segment through preference centers and exclusive content",
            "somewhat_engaged": "Re-engage through value-driven content and personalization",
            "barely_engaged": "Implement preference centers and frequency optimization",
            "not_engaged": "Deploy winback flows with opt-down options",
            "no_emails_30d": "Systematic reactivation through segmented campaigns"
        }
        
        return strategies.get(category, "Enhance engagement through targeted strategies")
    
    def _calculate_overall_list_health(self, benchmark_comparison: Dict[str, Any]) -> str:
        """Calculate overall list health status."""
        poor_areas = sum(1 for comp in benchmark_comparison.values() if comp["status"] == "poor")
        total_areas = len(benchmark_comparison)
        
        if poor_areas == 0:
            return "excellent"
        elif poor_areas <= total_areas * 0.3:
            return "good"
        elif poor_areas <= total_areas * 0.6:
            return "fair"
        else:
            return "poor"
    
    # Additional helper methods for remaining functionality...
    def _generate_overall_segmentation_strategy(self, opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate overall segmentation strategy."""
        if not opportunities:
            return {"status": "optimized", "message": "Current segmentation appears well-optimized"}
        
        high_impact_count = sum(1 for opp in opportunities if "25%" in opp.get("expected_uplift", ""))
        
        return {
            "status": "optimization_needed",
            "priority_focus": "New vs Returning segmentation across abandonment flows",
            "implementation_sequence": [opp["flow_type"] for opp in opportunities[:3]],
            "expected_timeline": "4-6 weeks for full implementation",
            "success_metrics": [
                "15-25% improvement in flow conversion rates",
                "Increased relevance scores in email performance",
                "Better customer journey progression"
            ]
        }
    
    def _create_segmentation_implementation_roadmap(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Create implementation roadmap for segmentation improvements."""
        roadmap = []
        
        # Sort by implementation complexity and impact
        simple_high_impact = [opp for opp in opportunities 
                             if opp.get("implementation_complexity") == "low"]
        
        week = 1
        for i, opp in enumerate(simple_high_impact[:3]):
            roadmap.append({
                "week": f"Week {week}-{week+1}",
                "initiative": f"Implement {opp['flow_type'].replace('_', ' ')} segmentation",
                "focus": opp.get("recommended_approach", "New vs Returning"),
                "deliverable": f"Enhanced {opp['flow_type']} with customer type segmentation"
            })
            week += 2
        
        return roadmap
    
    def _estimate_segmentation_revenue_impact(self, opportunities: List[Dict[str, Any]], 
                                            flows_data: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate revenue impact of segmentation improvements."""
        total_impact = 0
        flow_impacts = {}
        
        for opp in opportunities:
            flow_type = opp["flow_type"]
            flow_revenue = flows_data.get(flow_type, {}).get("revenue", 0)
            
            # Parse expected uplift percentage
            uplift_str = opp.get("expected_uplift", "15%")
            try:
                uplift_pct = float(uplift_str.split("-")[0].replace("%", "")) / 100
            except:
                uplift_pct = 0.15  # Default 15%
            
            estimated_impact = flow_revenue * uplift_pct
            flow_impacts[flow_type] = estimated_impact
            total_impact += estimated_impact
        
        return {
            "total_estimated_impact": total_impact,
            "flow_level_impacts": flow_impacts,
            "confidence_level": "medium",
            "timeframe": "90 days post-implementation"
        }
    
    def _calculate_opportunity_priority_score(self, opportunity: Dict[str, Any]) -> float:
        """Calculate priority score for segmentation opportunity."""
        # Base score from expected uplift
        uplift_str = opportunity.get("expected_uplift", "15%")
        try:
            uplift_score = float(uplift_str.split("-")[0].replace("%", "")) / 100
        except:
            uplift_score = 0.15
        
        # Complexity modifier (easier = higher priority)
        complexity_modifier = {
            "low": 1.5,
            "medium": 1.0,
            "high": 0.7
        }.get(opportunity.get("implementation_complexity", "medium"), 1.0)
        
        return uplift_score * complexity_modifier