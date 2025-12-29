"""
Helper functions for data preparers.
"""
from typing import Dict, Any, List


def generate_flow_strategic_summary(
    priority_matrix: Dict[str, Any], 
    segmentation_analysis: Dict[str, Any]
) -> str:
    """Generate strategic summary combining flow optimization and segmentation insights."""
    if not priority_matrix or not segmentation_analysis:
        return "Flow optimization analysis requires additional performance data for strategic insights."
    
    top_priority = priority_matrix.get("top_priority")
    if not top_priority:
        return "Current flow performance appears optimized with minimal strategic adjustments needed."
    
    # Build strategic narrative
    summary_parts = []
    
    # Top priority insight
    summary_parts.append(f"Priority optimization focus: {top_priority['flow_name']} shows {top_priority['performance_tier']} performance with {top_priority['key_optimization']} representing the highest-impact improvement opportunity.")
    
    # Segmentation opportunities
    if not segmentation_analysis.get("error"):
        improvement_opportunities = segmentation_analysis.get("improvement_opportunities", [])
        if improvement_opportunities:
            high_impact_flows = [opp for opp in improvement_opportunities if "25%" in opp.get("expected_uplift", "")]
            if high_impact_flows:
                summary_parts.append(f"Segmentation enhancement across {len(high_impact_flows)} flows offers 20-30% conversion improvements through customer type-based messaging.")
    
    # Revenue impact context
    total_impact = priority_matrix.get("total_estimated_impact", 0)
    if total_impact > 0:
        summary_parts.append(f"Combined optimization initiatives represent ${total_impact:,.0f} in estimated revenue uplift.")
    
    return " ".join(summary_parts)


def create_flow_implementation_roadmap(
    priority_matrix: Dict[str, Any], 
    segmentation_analysis: Dict[str, Any]
) -> List[Dict[str, str]]:
    """Create phased implementation roadmap for flow optimizations."""
    roadmap = []
    
    # Get prioritized flows from optimization matrix
    prioritized_flows = priority_matrix.get("prioritized_flows", [])[:3] if priority_matrix else []
    
    week = 1
    for i, flow_priority in enumerate(prioritized_flows):
        roadmap.append({
            "week": f"Week {week}-{week+1}",
            "initiative": f"Optimize {flow_priority['flow_name']}",
            "focus": flow_priority.get("key_optimization", "Performance enhancement"),
            "deliverable": f"Enhanced {flow_priority['flow_name']} with strategic improvements"
        })
        week += 2
    
    # Add segmentation initiatives if not covered
    if segmentation_analysis and not segmentation_analysis.get("error"):
        priority_implementations = segmentation_analysis.get("priority_implementations", [])
        remaining_implementations = [impl for impl in priority_implementations 
                                   if impl not in [f['flow_type'] for f in prioritized_flows]]
        
        for impl in remaining_implementations[:2]:  # Add up to 2 more
            roadmap.append({
                "week": f"Week {week}-{week+1}",
                "initiative": f"Implement {impl.replace('_', ' ')} segmentation",
                "focus": "New vs Returning customer messaging",
                "deliverable": f"Segmented {impl.replace('_', ' ')} flow"
            })
            week += 2
    
    return roadmap

