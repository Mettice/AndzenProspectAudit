"""
Benchmark comparison service.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional


class BenchmarkService:
    """Service for comparing metrics against industry benchmarks."""
    
    def __init__(self, benchmark_file: Optional[str] = None):
        if benchmark_file is None:
            benchmark_file = Path(__file__).parent.parent.parent / "data" / "benchmarks" / "fashion_accessories.json"
        self.benchmark_file = Path(benchmark_file)
        self.benchmarks = self._load_benchmarks()
    
    def _load_benchmarks(self) -> Dict[str, Any]:
        """Load benchmark data from JSON file."""
        if not self.benchmark_file.exists():
            return {}
        
        with open(self.benchmark_file, "r") as f:
            return json.load(f)
    
    def compare_metric(
        self,
        metric_name: str,
        value: float,
        benchmark_type: str = "average"
    ) -> Dict[str, Any]:
        """
        Compare a metric value against benchmarks.
        
        Args:
            metric_name: Name of the metric (e.g., "open_rate", "click_rate")
            value: The actual value to compare
            benchmark_type: "average" or "top_10_percent"
        
        Returns:
            Dictionary with comparison results
        """
        if metric_name not in self.benchmarks:
            return {
                "metric": metric_name,
                "value": value,
                "benchmark": None,
                "difference": None,
                "percentile": None
            }
        
        benchmark_data = self.benchmarks[metric_name]
        benchmark_value = benchmark_data.get(benchmark_type)
        
        if benchmark_value is None:
            return {
                "metric": metric_name,
                "value": value,
                "benchmark": None,
                "difference": None,
                "percentile": None
            }
        
        difference = value - benchmark_value
        percent_difference = (difference / benchmark_value * 100) if benchmark_value > 0 else 0
        
        # Calculate percentile (simplified)
        percentile = self._calculate_percentile(value, benchmark_data)
        
        return {
            "metric": metric_name,
            "value": value,
            "benchmark": benchmark_value,
            "benchmark_type": benchmark_type,
            "difference": difference,
            "percent_difference": percent_difference,
            "percentile": percentile,
            "status": "above" if difference > 0 else "below"
        }
    
    def _calculate_percentile(
        self,
        value: float,
        benchmark_data: Dict[str, float]
    ) -> float:
        """Calculate approximate percentile based on benchmarks."""
        average = benchmark_data.get("average", 0)
        top_10 = benchmark_data.get("top_10_percent", 0)
        
        if average == 0:
            return 50.0
        
        if value >= top_10:
            return 90.0
        elif value >= average:
            # Linear interpolation between average and top 10%
            if top_10 > average:
                ratio = (value - average) / (top_10 - average)
                return 50.0 + (ratio * 40.0)
            return 50.0
        else:
            # Below average
            if average > 0:
                ratio = value / average
                return max(0.0, min(50.0, ratio * 50.0))
            return 0.0
    
    def get_all_benchmarks(self) -> Dict[str, Any]:
        """Get all available benchmarks."""
        return self.benchmarks
    
    def get_performance_tier(self, metric_name: str, value: float) -> Dict[str, Any]:
        """
        Classify performance into tiers (Poor/Average/Good/Excellent) with strategic context.
        
        Args:
            metric_name: Name of the metric
            value: The actual value
            
        Returns:
            Performance tier with strategic insights
        """
        if metric_name not in self.benchmarks:
            return {
                "tier": "unknown",
                "percentile": 50.0,
                "gap_analysis": "Benchmark data not available",
                "improvement_potential": "low"
            }
        
        benchmark_data = self.benchmarks[metric_name]
        percentile = self._calculate_percentile(value, benchmark_data)
        
        # Determine performance tier
        if percentile >= 90:
            tier = "excellent"
            gap_analysis = f"Performance significantly exceeds industry standards (top 10%)"
        elif percentile >= 50:
            tier = "good"
            average = benchmark_data.get("average", 0)
            top_10 = benchmark_data.get("top_10_percent", 0)
            gap_to_top = top_10 - value if top_10 > 0 else 0
            gap_analysis = f"Above industry average, {gap_to_top:.1f} points from top 10% performance"
        elif percentile >= 25:
            tier = "average"
            average = benchmark_data.get("average", 0)
            gap_to_average = average - value if average > 0 else 0
            gap_analysis = f"Below industry average by {gap_to_average:.1f} points"
        else:
            tier = "poor"
            gap_analysis = f"Significant gap vs industry standards (bottom quartile)"
        
        # Calculate improvement potential
        improvement_potential = self._calculate_improvement_potential(percentile)
        
        return {
            "tier": tier,
            "percentile": percentile,
            "gap_analysis": gap_analysis,
            "improvement_potential": improvement_potential,
            "benchmark_average": benchmark_data.get("average", 0),
            "benchmark_top_10": benchmark_data.get("top_10_percent", 0)
        }
    
    def _calculate_improvement_potential(self, percentile: float) -> str:
        """Calculate improvement potential based on current percentile."""
        if percentile >= 85:
            return "low"  # Already in top tier
        elif percentile >= 50:
            return "medium"  # Above average but can reach top 10%
        else:
            return "high"  # Below average, significant upside
    
    def generate_benchmark_narrative(self, metrics: Dict[str, float], flow_type: str = "general") -> Dict[str, str]:
        """
        Generate Carissa-style benchmark narrative with strategic context.
        
        Args:
            metrics: Dictionary of metric values (open_rate, click_rate, etc.)
            flow_type: Type of flow for context-specific insights
            
        Returns:
            Strategic narrative about benchmark performance
        """
        narratives = {}
        priority_areas = []
        strengths = []
        
        for metric_name, value in metrics.items():
            if metric_name in self.benchmarks:
                performance = self.get_performance_tier(metric_name, value)
                
                if performance["tier"] in ["excellent", "good"]:
                    strengths.append(f"{metric_name.replace('_', ' ')} ({value:.1f}%)")
                elif performance["improvement_potential"] == "high":
                    priority_areas.append({
                        "metric": metric_name.replace('_', ' '),
                        "value": value,
                        "gap": performance["gap_analysis"],
                        "potential": self._get_metric_improvement_strategy(metric_name, flow_type)
                    })
        
        # Generate overall narrative
        if strengths and not priority_areas:
            narratives["overall"] = f"Performance exceeds benchmarks across {', '.join(strengths)}, indicating a well-optimized flow with potential for incremental gains."
        elif priority_areas and not strengths:
            top_priority = priority_areas[0]
            narratives["overall"] = f"Performance indicates clear optimization opportunities, with {top_priority['metric']} showing the highest improvement potential through {top_priority['potential']}."
        elif strengths and priority_areas:
            narratives["overall"] = f"Mixed performance with strengths in {strengths[0]} while {priority_areas[0]['metric']} presents optimization opportunities."
        else:
            narratives["overall"] = "Benchmark comparison requires additional performance data for strategic analysis."
        
        # Generate specific recommendations
        if priority_areas:
            recommendations = []
            for area in priority_areas[:2]:  # Focus on top 2 priorities
                recommendations.append(f"Improve {area['metric']} through {area['potential']}")
            narratives["recommendations"] = "; ".join(recommendations) + "."
        else:
            narratives["recommendations"] = "Continue current strategy while testing incremental improvements to maintain strong performance."
        
        return narratives
    
    def _get_metric_improvement_strategy(self, metric_name: str, flow_type: str) -> str:
        """Get metric-specific improvement strategies."""
        
        strategies = {
            "open_rate": {
                "general": "subject line testing with curiosity-based messaging or exclusivity themes",
                "welcome": "timing optimization to the first 7 days when engagement is highest",
                "abandoned_cart": "urgency messaging and personalized subject lines based on cart contents",
                "browse": "product-specific subject lines referencing viewed items"
            },
            "click_rate": {
                "general": "clearer CTAs, personalized content blocks, and dynamic product recommendations",
                "welcome": "progressive profiling and benefit-focused messaging",
                "abandoned_cart": "social proof integration and limited-time offers",
                "browse": "multi-product showcases and 'complete the look' suggestions"
            },
            "placed_order_rate": {
                "general": "checkout friction reduction and post-click experience optimization",
                "welcome": "first-purchase incentive optimization and onboarding sequence refinement",
                "abandoned_cart": "exit-intent detection and multi-step recovery sequences",
                "browse": "scarcity messaging and personalized product feeds"
            }
        }
        
        return strategies.get(metric_name, {}).get(flow_type, strategies.get(metric_name, {}).get("general", "strategic optimization and A/B testing"))

