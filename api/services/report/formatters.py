"""
Formatting utilities for report generation.
"""
from typing import Dict, Any, List, Optional


def format_currency(value: Optional[float]) -> str:
    """Format number as currency."""
    if value is None:
        return "$0.00"
    return f"${value:,.2f}"


def format_percentage(value: Optional[float]) -> str:
    """Format number as percentage."""
    if value is None:
        return "0.0%"
    return f"{value:.1f}%"


def format_number(value: Optional[float]) -> str:
    """Format number with commas."""
    if value is None:
        return "0"
    return f"{value:,.0f}"


def get_status_class(status: str) -> str:
    """Get CSS class for status."""
    status_map = {
        "exceeds_top10": "status-excellent",
        "above_average": "status-good",
        "below_average": "status-warning",
        "significantly_below": "status-critical",
        "healthy": "status-good",
        "moderate": "status-warning",
        "needs_improvement": "status-critical",
        "needs_attention": "status-warning",
        "inactive": "status-critical",
        "no_data": "status-neutral"
    }
    return status_map.get(status, "status-neutral")


def format_benchmark_comparison(benchmark: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Format benchmark comparison data for template."""
    formatted = []
    for key, value in benchmark.items():
        if isinstance(value, dict) and "value" in value:
            formatted.append({
                "metric": key.replace("_", " ").title(),
                "client_value": value.get("value", 0),
                "benchmark": value.get("benchmark", 0),
                "status": value.get("status", "neutral"),
                "difference": value.get("difference", 0)
            })
    return formatted


def format_metric_table(metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Format metrics into table rows."""
    rows = []
    for key, value in metrics.items():
        rows.append({
            "label": key.replace("_", " ").title(),
            "value": value
        })
    return rows


def format_recommendations(
    recommendations: List[Dict[str, Any]],
    priority_levels: Optional[List[str]] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Format recommendations by priority level.
    
    Args:
        recommendations: List of recommendation dicts
        priority_levels: List of priority levels (default: ["high", "medium", "low"])
        
    Returns:
        Dict with priority levels as keys and lists of recommendations as values
    """
    if priority_levels is None:
        priority_levels = ["high", "medium", "low"]
    
    formatted = {level: [] for level in priority_levels}
    
    for rec in recommendations:
        priority = rec.get("priority", "medium").lower()
        if priority in formatted:
            formatted[priority].append(rec)
        else:
            formatted["medium"].append(rec)
    
    return formatted

