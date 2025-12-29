"""
Advanced Flow Lifecycle Analyzer - Carissa-level flow optimization insights
"""
from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FlowLifecycleAnalyzer:
    """
    Advanced flow analysis matching Carissa's depth and strategic insight.
    
    Analyzes flow performance with sophisticated timing, segmentation, and 
    optimization recommendations based on industry best practices.
    """
    
    def __init__(self):
        self.benchmarks = self._load_flow_benchmarks()
        self.optimization_strategies = self._load_optimization_strategies()
    
    def _load_flow_benchmarks(self) -> Dict[str, Dict[str, float]]:
        """Load flow-specific benchmarks from Carissa's methodology."""
        return {
            "welcome": {
                "open_rate_avg": 51.52,
                "open_rate_top10": 74.64,
                "click_rate_avg": 4.55,
                "click_rate_top10": 14.81,
                "placed_order_rate_avg": 2.00,
                "optimal_day_range": 7,  # First 7 days most crucial
                "engagement_dropoff_day": 8
            },
            "abandoned_cart": {
                "open_rate_avg": 51.43,
                "open_rate_top10": 66.67,
                "click_rate_avg": 6.25,
                "click_rate_top10": 10.5,
                "placed_order_rate_avg": 3.42,
                "optimal_triggers": [20, 120, 240],  # 20min, 2hr, 4hr in minutes
                "max_effective_emails": 3
            },
            "abandoned_checkout": {
                "open_rate_avg": 51.43,
                "open_rate_top10": 66.67,
                "click_rate_avg": 6.25,
                "click_rate_top10": 10.5,
                "placed_order_rate_avg": 4.12,
                "optimal_triggers": [20, 60, 240],  # Earlier triggers for higher intent
                "max_effective_emails": 3
            },
            "browse_abandonment": {
                "open_rate_avg": 54.10,
                "open_rate_top10": 65.0,
                "click_rate_avg": 4.74,
                "click_rate_top10": 7.5,
                "placed_order_rate_avg": 0.82,
                "optimal_touchpoints": 2,  # Current single touchpoint is suboptimal
                "personalization_uplift": 25  # % improvement with personalized product feeds
            },
            "post_purchase": {
                "open_rate_avg": 60.09,
                "open_rate_top10": 75.0,
                "click_rate_avg": 3.33,
                "click_rate_top10": 6.0,
                "placed_order_rate_avg": 0.52,
                "pdno_vs_fixed_uplift": 35,  # % improvement with PDNO triggers
                "cross_sell_opportunity": 40  # % of customers open to cross-sell
            }
        }
    
    def _load_optimization_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Load flow-specific optimization strategies."""
        return {
            "welcome": {
                "timing_optimization": {
                    "first_7_days_focus": "Compress series to first 7-10 days when engagement is highest",
                    "day_0_importance": "Day 0 email should be immediate welcome with clear value prop",
                    "engagement_dropoff": "Performance typically drops significantly after day 8"
                },
                "segmentation_opportunities": {
                    "new_vs_returning": "Segment by customer type for relevant messaging",
                    "shopping_preference": "Use conditional hero images based on gender/preference",
                    "purchase_intent": "Different messaging for browsers vs purchasers"
                },
                "personalization": {
                    "dynamic_content": "Product feeds based on browsing behavior",
                    "conditional_blocks": "Gender-specific imagery and product recommendations",
                    "progressive_profiling": "Collect preferences gradually across sequence"
                }
            },
            "abandoned_cart": {
                "timing_optimization": {
                    "trigger_testing": "A/B test 20min vs 2hr vs 4hr initial triggers",
                    "checkout_priority": "Abandoned checkout should fire earlier (20-60min)",
                    "diminishing_returns": "More than 3 emails typically show poor ROI"
                },
                "segmentation_opportunities": {
                    "new_vs_returning": "More effective than sale/non-sale segmentation",
                    "cart_value": "High-value carts warrant different messaging",
                    "product_category": "Category-specific recovery strategies"
                },
                "personalization": {
                    "dynamic_cart_display": "Show exact products left in cart",
                    "social_proof": "Reviews and ratings for abandoned products",
                    "scarcity_messaging": "Stock levels and urgency indicators"
                }
            },
            "browse_abandonment": {
                "touchpoint_expansion": {
                    "current_limitation": "Single touchpoint leaves revenue on table",
                    "optimal_sequence": "2-3 touchpoints with progressive value",
                    "timing_gaps": "24hr, 3-day, 7-day sequence recommended"
                },
                "segmentation_opportunities": {
                    "browsing_behavior": "Collection vs product vs search abandonment",
                    "new_vs_returning": "Trust-building vs personalization focus",
                    "engagement_frequency": "High browsers vs occasional visitors"
                },
                "personalization": {
                    "product_feeds": "Dynamic recommendations based on viewed items",
                    "category_affinity": "Similar products in same category",
                    "complete_the_look": "Complementary product suggestions"
                }
            },
            "post_purchase": {
                "trigger_optimization": {
                    "pdno_advantage": "PDNO triggers outperform fixed timing by 35%",
                    "customer_lifecycle": "Different timing for 1st vs repeat customers",
                    "seasonal_adjustment": "Trigger timing varies by industry/season"
                },
                "segmentation_opportunities": {
                    "purchase_count": "First-time vs repeat customer strategies",
                    "category_loyalty": "Cross-category vs same-category recommendations",
                    "cltv_potential": "High-value customers get premium treatment"
                },
                "cross_sell_strategies": {
                    "first_time_customers": "Same category repetition builds confidence",
                    "repeat_customers": "Cross-category expansion opportunities",
                    "vip_customers": "Exclusive previews and early access"
                }
            }
        }
    
    def analyze_welcome_series(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze Welcome Series with Carissa's depth - focusing on first 7 days optimization.
        
        Args:
            flow_data: Flow performance data including metrics by email/day
            
        Returns:
            Comprehensive analysis with specific optimization recommendations
        """
        try:
            # Extract basic metrics
            overall_metrics = self._extract_flow_metrics(flow_data)
            
            # Analyze timing patterns (if email-level data available)
            timing_analysis = self._analyze_welcome_timing(flow_data)
            
            # Generate segmentation recommendations
            segmentation_recs = self._analyze_welcome_segmentation(flow_data)
            
            # Benchmark comparison
            benchmark_analysis = self._compare_to_benchmarks("welcome", overall_metrics)
            
            # Strategic recommendations
            strategic_recs = self._generate_welcome_recommendations(
                overall_metrics, timing_analysis, benchmark_analysis
            )
            
            return {
                "flow_name": flow_data.get("name", "Welcome Series"),
                "performance_summary": self._generate_welcome_performance_narrative(
                    overall_metrics, benchmark_analysis, timing_analysis
                ),
                "timing_insights": timing_analysis,
                "segmentation_opportunities": segmentation_recs,
                "benchmark_comparison": benchmark_analysis,
                "strategic_recommendations": strategic_recs,
                "optimization_priority": self._calculate_optimization_priority(benchmark_analysis),
                "revenue_impact_estimate": self._estimate_welcome_revenue_impact(
                    overall_metrics, benchmark_analysis
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing welcome series: {e}")
            return self._get_error_response("Welcome Series")
    
    def analyze_abandonment_flows(self, cart_data: Dict[str, Any], checkout_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze Abandoned Cart and Checkout flows with timing and segmentation focus.
        
        Args:
            cart_data: Abandoned Cart flow data
            checkout_data: Abandoned Checkout flow data (if separate)
            
        Returns:
            Comprehensive abandonment analysis with optimization strategies
        """
        try:
            # Analyze cart abandonment
            cart_analysis = self._analyze_single_abandonment_flow(cart_data, "abandoned_cart")
            
            # Analyze checkout abandonment if available
            checkout_analysis = None
            if checkout_data:
                checkout_analysis = self._analyze_single_abandonment_flow(checkout_data, "abandoned_checkout")
            
            # Combined insights and recommendations
            combined_insights = self._generate_abandonment_combined_insights(cart_analysis, checkout_analysis)
            
            return {
                "cart_abandonment": cart_analysis,
                "checkout_abandonment": checkout_analysis,
                "combined_insights": combined_insights,
                "timing_optimization_recommendations": self._generate_abandonment_timing_recs(
                    cart_analysis, checkout_analysis
                ),
                "segmentation_strategy": self._generate_abandonment_segmentation_strategy(),
                "revenue_recovery_potential": self._calculate_abandonment_revenue_potential(
                    cart_analysis, checkout_analysis
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing abandonment flows: {e}")
            return self._get_error_response("Abandonment Flows")
    
    def analyze_browse_abandonment(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze Browse Abandonment with focus on touchpoint expansion and personalization.
        
        Args:
            flow_data: Browse abandonment flow data
            
        Returns:
            Analysis focused on touchpoint optimization and personalization strategies
        """
        try:
            # Extract basic metrics
            overall_metrics = self._extract_flow_metrics(flow_data)
            
            # Analyze touchpoint limitations
            touchpoint_analysis = self._analyze_browse_touchpoints(flow_data)
            
            # Benchmark comparison
            benchmark_analysis = self._compare_to_benchmarks("browse_abandonment", overall_metrics)
            
            # Segmentation opportunities
            segmentation_analysis = self._analyze_browse_segmentation_opportunities()
            
            # Strategic recommendations
            strategic_recs = self._generate_browse_recommendations(
                overall_metrics, touchpoint_analysis, benchmark_analysis
            )
            
            return {
                "flow_name": flow_data.get("name", "Browse Abandonment"),
                "performance_summary": self._generate_browse_performance_narrative(
                    overall_metrics, benchmark_analysis, touchpoint_analysis
                ),
                "touchpoint_analysis": touchpoint_analysis,
                "personalization_opportunities": self._generate_browse_personalization_opportunities(),
                "segmentation_strategies": segmentation_analysis,
                "benchmark_comparison": benchmark_analysis,
                "strategic_recommendations": strategic_recs,
                "revenue_expansion_potential": self._calculate_browse_revenue_potential(
                    overall_metrics, touchpoint_analysis
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing browse abandonment: {e}")
            return self._get_error_response("Browse Abandonment")
    
    def analyze_post_purchase_flows(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze Post-Purchase flows with PDNO and cross-sell focus.
        
        Args:
            flow_data: Post-purchase flow data
            
        Returns:
            Analysis focused on PDNO optimization and cross-sell strategies
        """
        try:
            # Extract basic metrics
            overall_metrics = self._extract_flow_metrics(flow_data)
            
            # Analyze trigger timing (PDNO vs fixed)
            trigger_analysis = self._analyze_post_purchase_triggers(flow_data)
            
            # Benchmark comparison
            benchmark_analysis = self._compare_to_benchmarks("post_purchase", overall_metrics)
            
            # Cross-sell opportunity analysis
            cross_sell_analysis = self._analyze_cross_sell_opportunities(flow_data)
            
            # Strategic recommendations
            strategic_recs = self._generate_post_purchase_recommendations(
                overall_metrics, trigger_analysis, cross_sell_analysis
            )
            
            return {
                "flow_name": flow_data.get("name", "Post Purchase"),
                "performance_summary": self._generate_post_purchase_performance_narrative(
                    overall_metrics, benchmark_analysis, trigger_analysis
                ),
                "pdno_optimization": trigger_analysis,
                "cross_sell_strategy": cross_sell_analysis,
                "segmentation_by_purchase_count": self._generate_post_purchase_segmentation(),
                "benchmark_comparison": benchmark_analysis,
                "strategic_recommendations": strategic_recs,
                "revenue_growth_potential": self._calculate_post_purchase_revenue_potential(
                    overall_metrics, trigger_analysis, cross_sell_analysis
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing post-purchase flows: {e}")
            return self._get_error_response("Post Purchase")
    
    def _extract_flow_metrics(self, flow_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract standardized metrics from flow data."""
        return {
            "open_rate": float(flow_data.get("open_rate", 0)),
            "click_rate": float(flow_data.get("click_rate", 0)),
            "placed_order_rate": float(flow_data.get("placed_order_rate", 0)),
            "revenue": float(flow_data.get("revenue", 0)),
            "recipients": int(flow_data.get("recipients", 0))
        }
    
    def _analyze_welcome_timing(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Welcome Series timing patterns."""
        # Check if we have email-level data
        emails = flow_data.get("emails", [])
        
        if not emails:
            return {
                "analysis_available": False,
                "recommendation": "Analyze individual email performance to optimize timing",
                "key_insight": "First 7 days are crucial for welcome series engagement"
            }
        
        # Analyze first 7 days vs later performance
        early_performance = []
        late_performance = []
        
        for email in emails:
            day_sent = email.get("days_after_trigger", 0)
            if day_sent <= 7:
                early_performance.append(email.get("open_rate", 0))
            else:
                late_performance.append(email.get("open_rate", 0))
        
        early_avg = sum(early_performance) / len(early_performance) if early_performance else 0
        late_avg = sum(late_performance) / len(late_performance) if late_performance else 0
        
        engagement_dropoff = early_avg - late_avg if late_avg > 0 else 0
        
        return {
            "analysis_available": True,
            "early_days_performance": early_avg,
            "later_days_performance": late_avg,
            "engagement_dropoff": engagement_dropoff,
            "optimization_opportunity": engagement_dropoff > 10,  # Significant dropoff
            "recommendation": self._get_welcome_timing_recommendation(engagement_dropoff, len(emails))
        }
    
    def _get_welcome_timing_recommendation(self, engagement_dropoff: float, total_emails: int) -> str:
        """Generate timing-specific recommendations for welcome series."""
        if engagement_dropoff > 20:
            return "Significant engagement dropoff detected. Consider compressing the series to the first 7-10 days when new subscriber engagement is highest."
        elif engagement_dropoff > 10:
            return "Moderate engagement decline observed. Test reducing email frequency after day 7 or adding more value-driven content."
        elif total_emails > 5:
            return "Consider testing a more compressed welcome sequence focused on the first week when engagement is typically strongest."
        else:
            return "Current timing appears optimized. Focus on content and personalization improvements."
    
    def _compare_to_benchmarks(self, flow_type: str, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Compare flow metrics to industry benchmarks."""
        benchmarks = self.benchmarks.get(flow_type, {})
        if not benchmarks:
            return {"analysis_available": False}
        
        comparison = {}
        
        for metric in ["open_rate", "click_rate", "placed_order_rate"]:
            if metric in metrics:
                value = metrics[metric]
                avg_benchmark = benchmarks.get(f"{metric}_avg", 0)
                top10_benchmark = benchmarks.get(f"{metric}_top10", 0)
                
                if avg_benchmark > 0:
                    vs_avg = ((value - avg_benchmark) / avg_benchmark) * 100
                    vs_top10 = ((value - top10_benchmark) / top10_benchmark) * 100 if top10_benchmark > 0 else -100
                    
                    if value >= top10_benchmark:
                        tier = "excellent"
                        status = "top_10_percent"
                    elif value >= avg_benchmark:
                        tier = "good"
                        status = "above_average"
                    elif value >= avg_benchmark * 0.8:
                        tier = "average"
                        status = "near_average"
                    else:
                        tier = "poor"
                        status = "below_average"
                    
                    comparison[metric] = {
                        "value": value,
                        "vs_average": vs_avg,
                        "vs_top10": vs_top10,
                        "tier": tier,
                        "status": status,
                        "gap_to_avg": avg_benchmark - value,
                        "gap_to_top10": top10_benchmark - value
                    }
        
        return {
            "analysis_available": True,
            "metrics": comparison,
            "overall_performance": self._calculate_overall_performance_tier(comparison),
            "priority_metric": self._identify_priority_optimization_metric(comparison)
        }
    
    def _calculate_overall_performance_tier(self, comparison: Dict[str, Dict[str, Any]]) -> str:
        """Calculate overall performance tier across all metrics."""
        tiers = [metric.get("tier", "poor") for metric in comparison.values()]
        
        tier_scores = {"excellent": 4, "good": 3, "average": 2, "poor": 1}
        avg_score = sum(tier_scores.get(tier, 1) for tier in tiers) / len(tiers) if tiers else 1
        
        if avg_score >= 3.5:
            return "excellent"
        elif avg_score >= 2.5:
            return "good"
        elif avg_score >= 1.5:
            return "average"
        else:
            return "poor"
    
    def _identify_priority_optimization_metric(self, comparison: Dict[str, Dict[str, Any]]) -> str:
        """Identify which metric has the highest optimization potential."""
        max_gap = 0
        priority_metric = "open_rate"
        
        for metric, data in comparison.items():
            gap_to_avg = data.get("gap_to_avg", 0)
            if gap_to_avg > max_gap and data.get("tier") in ["poor", "average"]:
                max_gap = gap_to_avg
                priority_metric = metric
        
        return priority_metric
    
    def _generate_welcome_performance_narrative(self, metrics: Dict[str, float], 
                                              benchmark_analysis: Dict[str, Any],
                                              timing_analysis: Dict[str, Any]) -> str:
        """Generate Carissa-style performance narrative for Welcome Series."""
        if not benchmark_analysis.get("analysis_available"):
            return "Welcome Series performance requires benchmark comparison for strategic analysis."
        
        overall_tier = benchmark_analysis.get("overall_performance", "average")
        priority_metric = benchmark_analysis.get("priority_metric", "open_rate")
        
        # Build narrative based on performance tier
        if overall_tier == "excellent":
            base_narrative = f"Welcome Series performance exceeds industry benchmarks across key metrics"
        elif overall_tier == "good":
            base_narrative = f"Welcome Series shows solid performance above industry averages"
        else:
            base_narrative = f"Welcome Series indicates clear optimization opportunities"
        
        # Add timing insights if available
        timing_context = ""
        if timing_analysis.get("analysis_available") and timing_analysis.get("engagement_dropoff", 0) > 10:
            timing_context = f" Analysis reveals significant engagement decline after the first week, suggesting the series could benefit from compression to the first 7-10 days when new subscriber attention is highest."
        
        # Add specific metric context
        metrics_data = benchmark_analysis.get("metrics", {})
        priority_data = metrics_data.get(priority_metric, {})
        
        if priority_data.get("tier") in ["poor", "average"]:
            metric_context = f" {priority_metric.replace('_', ' ').title()} shows the highest improvement potential"
            if priority_data.get("gap_to_avg", 0) > 0:
                gap = priority_data["gap_to_avg"]
                metric_context += f", currently {gap:.1f} percentage points below industry average"
        else:
            metric_context = f" with particularly strong {priority_metric.replace('_', ' ')}"
        
        return f"{base_narrative}{metric_context}.{timing_context}"
    
    def _get_error_response(self, flow_name: str) -> Dict[str, Any]:
        """Return standardized error response for flow analysis."""
        return {
            "flow_name": flow_name,
            "error": True,
            "message": f"{flow_name} analysis requires additional performance data for strategic insights.",
            "recommendations": ["Ensure flow has sufficient data for analysis", "Verify flow is active and sending emails"]
        }
    
    # Additional helper methods would continue here...
    # (Implementing all the other analysis methods for space efficiency)
    
    def get_flow_optimization_priority_matrix(self, all_flows: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create optimization priority matrix across all flows.
        
        Args:
            all_flows: Dictionary of all flow analyses
            
        Returns:
            Priority matrix with recommended optimization sequence
        """
        priorities = []
        
        for flow_type, flow_data in all_flows.items():
            if flow_data.get("error"):
                continue
                
            benchmark_comparison = flow_data.get("benchmark_comparison", {})
            if not benchmark_comparison.get("analysis_available"):
                continue
            
            overall_tier = benchmark_comparison.get("overall_performance", "average")
            revenue = flow_data.get("revenue_impact_estimate", {}).get("potential_uplift", 0)
            
            # Calculate priority score
            tier_scores = {"poor": 4, "average": 3, "good": 2, "excellent": 1}
            priority_score = tier_scores.get(overall_tier, 2) * (1 + revenue / 10000)
            
            priorities.append({
                "flow_type": flow_type,
                "flow_name": flow_data.get("flow_name", flow_type),
                "priority_score": priority_score,
                "performance_tier": overall_tier,
                "estimated_revenue_impact": revenue,
                "key_optimization": self._get_key_optimization_focus(flow_type, flow_data)
            })
        
        # Sort by priority score (highest first)
        priorities.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return {
            "prioritized_flows": priorities,
            "top_priority": priorities[0] if priorities else None,
            "total_estimated_impact": sum(p["estimated_revenue_impact"] for p in priorities),
            "optimization_sequence": [p["flow_type"] for p in priorities[:3]]  # Top 3
        }
    
    def _get_key_optimization_focus(self, flow_type: str, flow_data: Dict[str, Any]) -> str:
        """Get the key optimization focus for a flow."""
        focus_map = {
            "welcome": "Timing compression to first 7 days",
            "abandoned_cart": "New vs Returning segmentation", 
            "browse_abandonment": "Multiple touchpoint expansion",
            "post_purchase": "PDNO trigger implementation"
        }
        
        return focus_map.get(flow_type, "Performance optimization")
    
    def _analyze_post_purchase_triggers(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze post-purchase trigger timing and optimization opportunities."""
        return {
            "current_trigger_type": flow_data.get("trigger_type", "fixed_timing"),
            "pdno_opportunity": {
                "available": True,
                "expected_uplift": "35% improvement vs fixed timing",
                "implementation": "Switch to PDNO (Previous Delivery Next Order) triggers"
            },
            "timing_analysis": {
                "current_delay": flow_data.get("trigger_delay_days", 30),
                "optimal_range": "7-14 days for first-time customers, 21-30 days for repeat",
                "customer_type_variation": "Timing should vary by purchase count"
            },
            "recommendations": [
                "Implement PDNO triggers for repeat customers",
                "Segment by purchase count (1st, 2nd, 3+ purchases)", 
                "Test different timing for first-time vs repeat customers"
            ]
        }
    
    def _analyze_browse_touchpoints(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze browse abandonment touchpoint limitations and expansion opportunities."""
        current_emails = flow_data.get("email_count", 1)
        
        return {
            "current_touchpoints": current_emails,
            "optimal_touchpoints": 2,
            "revenue_opportunity": {
                "current_limitation": "Single touchpoint leaves revenue on table",
                "expansion_potential": "25% revenue increase with 2-touchpoint sequence",
                "optimal_timing": "24hr, 3-day sequence recommended"
            },
            "personalization_gaps": {
                "product_feeds": "Static content vs dynamic browsed items",
                "behavioral_segmentation": "All browsers treated the same",
                "engagement_frequency": "No distinction between high/low browsers"
            },
            "recommendations": [
                "Expand to 2-touchpoint sequence (24hr, 3-day)",
                "Add personalized product feeds based on browsed items",
                "Segment by browsing behavior (collection vs product vs search)",
                "Implement new vs returning customer messaging"
            ]
        }
    
    # Placeholder implementations for remaining methods
    def _analyze_welcome_segmentation(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze welcome series segmentation opportunities."""
        return {
            "current_segmentation": "Basic welcome series",
            "opportunities": [
                "New vs Returning customer split for relevant messaging",
                "Shopping preference segmentation (gender/category)",
                "Purchase intent based on browsing behavior"
            ],
            "implementation_priority": "high",
            "expected_uplift": "15-25% improvement in engagement"
        }
    
    def _generate_welcome_recommendations(self, metrics: Dict[str, float], 
                                        timing: Dict[str, Any], 
                                        benchmarks: Dict[str, Any]) -> List[str]:
        """Generate specific welcome series recommendations."""
        recommendations = []
        
        if timing.get("engagement_dropoff", 0) > 15:
            recommendations.append("Compress welcome series to first 7-10 days when engagement is highest")
        
        if benchmarks.get("priority_metric") == "open_rate":
            recommendations.append("Test curiosity-based subject lines and exclusivity messaging")
        
        if benchmarks.get("priority_metric") == "click_rate":
            recommendations.append("Implement dynamic content blocks and personalized product recommendations")
        
        recommendations.append("Segment by New vs Returning customers for more relevant messaging")
        recommendations.append("Add conditional hero images based on shopping preferences")
        
        return recommendations
    
    def _estimate_welcome_revenue_impact(self, metrics: Dict[str, float], 
                                       benchmarks: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate revenue impact of welcome series optimization."""
        current_revenue = metrics.get("revenue", 0)
        current_conversion = metrics.get("placed_order_rate", 0)
        
        # Estimate improvement potential based on benchmark gaps
        benchmark_metrics = benchmarks.get("metrics", {})
        conversion_data = benchmark_metrics.get("placed_order_rate", {})
        
        if conversion_data and current_conversion > 0:
            gap_to_avg = conversion_data.get("gap_to_avg", 0)
            if gap_to_avg > 0:
                improvement_potential = min(gap_to_avg / current_conversion, 0.5)  # Cap at 50% improvement
                potential_uplift = current_revenue * improvement_potential
                
                return {
                    "current_revenue": current_revenue,
                    "potential_uplift": potential_uplift,
                    "improvement_percentage": improvement_potential * 100,
                    "confidence_level": "medium" if improvement_potential > 0.1 else "low"
                }
        
        return {
            "current_revenue": current_revenue,
            "potential_uplift": 0,
            "improvement_percentage": 0,
            "confidence_level": "low"
        }
    
    def _calculate_optimization_priority(self, benchmark_analysis: Dict[str, Any]) -> str:
        """Calculate optimization priority level."""
        if not benchmark_analysis.get("analysis_available"):
            return "medium"
        
        overall_tier = benchmark_analysis.get("overall_performance", "average")
        
        priority_map = {
            "poor": "high",
            "average": "medium", 
            "good": "low",
            "excellent": "maintenance"
        }
        
        return priority_map.get(overall_tier, "medium")
    
    def _analyze_single_abandonment_flow(self, flow_data: Dict[str, Any], flow_type: str) -> Dict[str, Any]:
        """Analyze a single abandonment flow."""
        metrics = self._extract_flow_metrics(flow_data)
        benchmark_analysis = self._compare_to_benchmarks(flow_type, metrics)
        
        return {
            "flow_name": flow_data.get("name", flow_type.replace("_", " ").title()),
            "metrics": metrics,
            "benchmark_comparison": benchmark_analysis,
            "timing_analysis": self._analyze_abandonment_timing(flow_data, flow_type),
            "performance_narrative": self._generate_abandonment_narrative(metrics, benchmark_analysis, flow_type)
        }
    
    def _analyze_abandonment_timing(self, flow_data: Dict[str, Any], flow_type: str) -> Dict[str, Any]:
        """Analyze abandonment flow timing."""
        benchmarks = self.benchmarks.get(flow_type, {})
        optimal_triggers = benchmarks.get("optimal_triggers", [120])
        
        return {
            "current_trigger": flow_data.get("trigger_delay_minutes", 120),
            "optimal_triggers": optimal_triggers,
            "recommendation": self._get_abandonment_timing_recommendation(flow_type),
            "a_b_test_suggestion": f"Test {optimal_triggers[0]}min vs {optimal_triggers[1] if len(optimal_triggers) > 1 else 240}min triggers"
        }
    
    def _get_abandonment_timing_recommendation(self, flow_type: str) -> str:
        """Get timing recommendation for abandonment flows."""
        if flow_type == "abandoned_checkout":
            return "Test earlier triggers (20-60 minutes) as checkout abandoners have higher intent"
        else:
            return "Test 20 minute vs 2 hour vs 4 hour trigger timing to optimize for customer receptivity"
    
    def _generate_abandonment_narrative(self, metrics: Dict[str, float], 
                                      benchmark_analysis: Dict[str, Any], 
                                      flow_type: str) -> str:
        """Generate performance narrative for abandonment flows."""
        if not benchmark_analysis.get("analysis_available"):
            return f"{flow_type.replace('_', ' ').title()} requires benchmark data for analysis."
        
        overall_tier = benchmark_analysis.get("overall_performance", "average")
        priority_metric = benchmark_analysis.get("priority_metric", "open_rate")
        
        flow_name = flow_type.replace("_", " ").title()
        
        if overall_tier in ["excellent", "good"]:
            return f"{flow_name} demonstrates solid recovery performance with opportunity for timing optimization and segmentation enhancement."
        else:
            return f"{flow_name} shows optimization potential, particularly in {priority_metric.replace('_', ' ')} through timing adjustments and New vs Returning customer segmentation."
    
    # Missing methods implementation
    def _generate_abandonment_combined_insights(self, cart_analysis: Dict[str, Any], 
                                               checkout_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate combined insights for abandonment flows."""
        insights = {}
        
        if cart_analysis and not cart_analysis.get("error"):
            insights["cart_performance"] = cart_analysis.get("performance_narrative", "")
            
        if checkout_analysis and not checkout_analysis.get("error"):
            insights["checkout_performance"] = checkout_analysis.get("performance_narrative", "")
            insights["strategy_recommendation"] = "Optimize both cart and checkout abandonment with earlier triggers for checkout flows"
        else:
            insights["strategy_recommendation"] = "Focus on cart abandonment optimization with timing and segmentation improvements"
            
        return insights
    
    def _generate_abandonment_timing_recs(self, cart_analysis: Dict[str, Any], 
                                         checkout_analysis: Dict[str, Any] = None) -> List[str]:
        """Generate timing recommendations for abandonment flows."""
        recommendations = []
        
        if cart_analysis:
            recommendations.append("Test 20 minute vs 2 hour vs 4 hour trigger timing for cart abandonment")
            
        if checkout_analysis:
            recommendations.append("Implement earlier triggers (20-60 minutes) for checkout abandonment due to higher intent")
        else:
            recommendations.append("Consider adding abandoned checkout flow with earlier trigger timing")
            
        recommendations.extend([
            "Implement New vs Returning customer segmentation",
            "Limit to maximum 3 emails per abandonment sequence",
            "Add dynamic cart/product display in email content"
        ])
        
        return recommendations
    
    def _generate_abandonment_segmentation_strategy(self) -> Dict[str, Any]:
        """Generate segmentation strategy for abandonment flows."""
        return {
            "recommended_approach": "New vs Returning Customer",
            "current_common_approach": "Sale vs Non-Sale (less effective)",
            "implementation": {
                "new_customers": "Trust-building, first-purchase incentives, brand education",
                "returning_customers": "Loyalty messaging, personalized recommendations, urgency"
            },
            "expected_improvement": "20-30% increase in conversion rates",
            "a_b_test_suggestion": "Test New vs Returning segmentation against current approach"
        }
    
    def _calculate_abandonment_revenue_potential(self, cart_analysis: Dict[str, Any], 
                                               checkout_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Calculate revenue recovery potential for abandonment flows."""
        total_potential = 0
        breakdown = {}
        
        if cart_analysis and cart_analysis.get("metrics"):
            current_revenue = cart_analysis["metrics"].get("revenue", 0)
            potential_uplift = current_revenue * 0.25  # 25% improvement estimate
            breakdown["cart_abandonment"] = potential_uplift
            total_potential += potential_uplift
            
        if checkout_analysis and checkout_analysis.get("metrics"):
            current_revenue = checkout_analysis["metrics"].get("revenue", 0)
            potential_uplift = current_revenue * 0.35  # 35% improvement estimate
            breakdown["checkout_abandonment"] = potential_uplift
            total_potential += potential_uplift
        
        return {
            "total_potential": total_potential,
            "breakdown": breakdown,
            "timeframe": "60-90 days post implementation",
            "confidence_level": "medium"
        }
    
    def _analyze_browse_segmentation_opportunities(self) -> Dict[str, Any]:
        """Analyze browse abandonment segmentation opportunities."""
        return {
            "behavioral_segmentation": {
                "collection_browsers": "Category-level inspiration and curation",
                "product_viewers": "Specific product focus with alternatives",
                "search_users": "Query-specific recommendations"
            },
            "customer_type_segmentation": {
                "new_visitors": "Trust-building and brand education focus",
                "returning_customers": "Personalized based on purchase history"
            },
            "implementation_priority": "high",
            "expected_impact": "15-25% improvement in browse abandonment conversion"
        }
    
    def _generate_browse_recommendations(self, metrics: Dict[str, float], 
                                       touchpoint_analysis: Dict[str, Any],
                                       benchmark_analysis: Dict[str, Any]) -> List[str]:
        """Generate browse abandonment recommendations."""
        recommendations = []
        
        # Touchpoint expansion
        current_touchpoints = touchpoint_analysis.get("current_touchpoints", 1)
        if current_touchpoints < 2:
            recommendations.append("Expand to 2-touchpoint sequence (24hr, 3-day timing)")
            
        # Performance gaps
        if benchmark_analysis.get("analysis_available"):
            overall_tier = benchmark_analysis.get("overall_performance", "average")
            if overall_tier in ["poor", "average"]:
                recommendations.append("Add personalized product feeds based on browsed items")
                
        recommendations.extend([
            "Implement behavioral segmentation (collection vs product vs search)",
            "Add New vs Returning customer messaging",
            "Test complete-the-look product recommendations"
        ])
        
        return recommendations
    
    def _generate_browse_performance_narrative(self, metrics: Dict[str, float],
                                             benchmark_analysis: Dict[str, Any],
                                             touchpoint_analysis: Dict[str, Any]) -> str:
        """Generate performance narrative for browse abandonment."""
        if not benchmark_analysis.get("analysis_available"):
            return "Browse abandonment requires additional performance data for strategic analysis."
            
        overall_tier = benchmark_analysis.get("overall_performance", "average")
        current_touchpoints = touchpoint_analysis.get("current_touchpoints", 1)
        
        if overall_tier in ["excellent", "good"] and current_touchpoints >= 2:
            return "Browse abandonment demonstrates solid performance with opportunity for personalization enhancement through dynamic product feeds and behavioral segmentation."
        elif current_touchpoints < 2:
            return f"Browse abandonment shows {overall_tier} performance but is limited by single touchpoint approach, representing significant revenue expansion opportunity through sequence extension."
        else:
            return f"Browse abandonment indicates {overall_tier} performance with clear optimization potential through touchpoint expansion and personalized content strategies."
    
    def _generate_browse_personalization_opportunities(self) -> Dict[str, Any]:
        """Generate browse abandonment personalization opportunities."""
        return {
            "dynamic_product_feeds": {
                "current_limitation": "Static or generic product recommendations",
                "opportunity": "Dynamic feeds showing exact browsed items plus alternatives",
                "expected_uplift": "25% improvement in click-through rates"
            },
            "behavioral_targeting": {
                "collection_browsers": "Category-level inspiration and curation content",
                "product_viewers": "Specific product focus with social proof",
                "search_abandoners": "Query-specific recommendations and alternatives"
            },
            "engagement_based": {
                "high_frequency_browsers": "VIP treatment and exclusive access messaging",
                "occasional_visitors": "Trust-building and value proposition focus"
            },
            "implementation_roadmap": [
                "Week 1-2: Add dynamic product feeds",
                "Week 3-4: Implement browsing behavior segmentation", 
                "Week 5-6: Test engagement frequency targeting"
            ]
        }
    
    def _calculate_browse_revenue_potential(self, metrics: Dict[str, float], 
                                          touchpoint_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate browse abandonment revenue expansion potential."""
        current_revenue = metrics.get("revenue", 0)
        current_touchpoints = touchpoint_analysis.get("current_touchpoints", 1)
        
        # Calculate potential from touchpoint expansion
        touchpoint_uplift = 0
        if current_touchpoints < 2:
            touchpoint_uplift = current_revenue * 0.25  # 25% from sequence expansion
            
        # Calculate potential from personalization
        personalization_uplift = current_revenue * 0.15  # 15% from dynamic content
        
        total_potential = touchpoint_uplift + personalization_uplift
        
        return {
            "current_revenue": current_revenue,
            "touchpoint_expansion_potential": touchpoint_uplift,
            "personalization_potential": personalization_uplift,
            "total_potential": total_potential,
            "improvement_percentage": (total_potential / current_revenue * 100) if current_revenue > 0 else 0,
            "timeframe": "90 days post implementation",
            "confidence_level": "medium"
        }
    
    def _analyze_cross_sell_opportunities(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze post-purchase cross-sell opportunities."""
        return {
            "current_approach": "Generic recommendations",
            "segmentation_opportunities": {
                "first_time_customers": "Same category repetition for confidence building",
                "repeat_customers": "Cross-category expansion opportunities",
                "vip_customers": "Exclusive previews and early access"
            },
            "cltv_based_strategy": {
                "entry_price_customers": "Upgrade to hero products",
                "mid_tier_customers": "Complete-the-look strategies",
                "high_value_customers": "Lifestyle and premium positioning"
            },
            "implementation_priority": "medium",
            "expected_impact": "15-30% increase in post-purchase revenue"
        }
    
    def _generate_post_purchase_recommendations(self, metrics: Dict[str, float],
                                              trigger_analysis: Dict[str, Any],
                                              cross_sell_analysis: Dict[str, Any]) -> List[str]:
        """Generate post-purchase flow recommendations."""
        recommendations = []
        
        # PDNO optimization
        if trigger_analysis.get("pdno_opportunity", {}).get("available"):
            recommendations.append("Implement PDNO (Previous Delivery Next Order) triggers for 35% performance improvement")
        
        # Segmentation
        recommendations.extend([
            "Segment by purchase count (1st, 2nd, 3+ purchases)",
            "Implement CLTV-based recommendation strategy",
            "Add customer lifecycle-specific messaging"
        ])
        
        # Cross-sell optimization
        if cross_sell_analysis:
            recommendations.append("Enhance cross-sell strategy with category-specific approaches")
        
        return recommendations
    
    def _generate_post_purchase_performance_narrative(self, metrics: Dict[str, float],
                                                    benchmark_analysis: Dict[str, Any],
                                                    trigger_analysis: Dict[str, Any]) -> str:
        """Generate performance narrative for post-purchase flows."""
        if not benchmark_analysis.get("analysis_available"):
            return "Post-purchase flow requires additional performance data for strategic analysis."
            
        overall_tier = benchmark_analysis.get("overall_performance", "average")
        pdno_available = trigger_analysis.get("pdno_opportunity", {}).get("available", False)
        
        if overall_tier in ["excellent", "good"] and pdno_available:
            return "Post-purchase flow demonstrates solid performance with significant optimization opportunity through PDNO trigger implementation for enhanced timing precision."
        elif pdno_available:
            return f"Post-purchase flow shows {overall_tier} performance with clear optimization pathway through PDNO triggers and purchase count segmentation."
        else:
            return f"Post-purchase flow indicates {overall_tier} performance with optimization opportunities in timing and customer lifecycle segmentation."
    
    def _generate_post_purchase_segmentation(self) -> Dict[str, Any]:
        """Generate post-purchase segmentation strategy."""
        return {
            "purchase_count_segmentation": {
                "first_time": "Same category repetition for confidence building",
                "second_purchase": "Cross-category expansion opportunities", 
                "repeat_customers": "VIP treatment and lifestyle positioning"
            },
            "cltv_segmentation": {
                "entry_price": "Upgrade to hero products",
                "mid_tier": "Complete-the-look strategies",
                "high_value": "Exclusive previews and early access"
            },
            "timing_optimization": {
                "first_time_customers": "7-14 days post-purchase",
                "repeat_customers": "Based on previous purchase cycle (PDNO)"
            },
            "implementation_priority": "high",
            "expected_improvement": "20-35% increase in repeat purchase rates"
        }
    
    def _calculate_post_purchase_revenue_potential(self, metrics: Dict[str, float],
                                                 trigger_analysis: Dict[str, Any],
                                                 cross_sell_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate post-purchase revenue growth potential."""
        current_revenue = metrics.get("revenue", 0)
        
        # PDNO optimization potential
        pdno_uplift = 0
        if trigger_analysis.get("pdno_opportunity", {}).get("available"):
            pdno_uplift = current_revenue * 0.35  # 35% from PDNO
        
        # Segmentation potential
        segmentation_uplift = current_revenue * 0.20  # 20% from better segmentation
        
        # Cross-sell potential
        cross_sell_uplift = current_revenue * 0.15  # 15% from enhanced cross-sell
        
        total_potential = pdno_uplift + segmentation_uplift + cross_sell_uplift
        
        return {
            "current_revenue": current_revenue,
            "pdno_potential": pdno_uplift,
            "segmentation_potential": segmentation_uplift,
            "cross_sell_potential": cross_sell_uplift,
            "total_potential": total_potential,
            "improvement_percentage": (total_potential / current_revenue * 100) if current_revenue > 0 else 0,
            "timeframe": "120 days post implementation",
            "confidence_level": "high"
        }