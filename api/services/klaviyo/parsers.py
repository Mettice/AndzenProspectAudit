"""Response parsing utilities for Klaviyo API responses."""
from typing import Any, Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def parse_metric_value(value: Any) -> float:
    """
    Parse a metric value from various response formats.
    
    Handles:
    - List format: [value, count, unique]
    - Dict format: {"sum_value": X, "count": Y}
    - Scalar format: direct number
    - None values
    
    Args:
        value: Value to parse (can be list, dict, scalar, or None)
        
    Returns:
        Parsed float value (0.0 if parsing fails)
    """
    if value is None:
        return 0.0
    
    if isinstance(value, list):
        if len(value) > 0 and value[0] is not None:
            try:
                val_str = str(value[0]).strip()
                if val_str:
                    return float(value[0])
            except (ValueError, TypeError):
                return 0.0
        return 0.0
    
    if isinstance(value, dict):
        # Try common keys
        for key in ["sum_value", "count", "value"]:
            if key in value and value[key] is not None:
                try:
                    val_str = str(value[key]).strip()
                    if val_str:
                        return float(value[key])
                except (ValueError, TypeError):
                    continue
        return 0.0
    
    # Scalar value
    try:
        if value and str(value).strip():
            return float(value)
    except (ValueError, TypeError):
        pass
    
    return 0.0


def parse_metric_list_value(value: Any, index: int = 0) -> float:
    """
    Parse a specific index from a list metric value.
    
    Args:
        value: List value (e.g., [sum_value, count, unique])
        index: Index to extract (0=sum_value, 1=count, 2=unique)
        
    Returns:
        Parsed float value
    """
    if isinstance(value, list) and len(value) > index:
        return parse_metric_value(value[index])
    return parse_metric_value(value)


def parse_aggregate_data(response: Dict[str, Any]) -> Tuple[List[str], List[Any]]:
    """
    Parse metric aggregate response.
    
    Args:
        response: API response from metric-aggregates endpoint
        
    Returns:
        Tuple of (dates, values) lists
    """
    attrs = response.get("data", {}).get("attributes", {})
    dates = attrs.get("dates", [])
    values = attrs.get("data", [])
    return dates, values


def extract_statistics(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract statistics from reporting API response.
    
    Converts rates from decimal (0.0-1.0) to percentage (0-100).
    
    Args:
        response: API response from campaign-values-reports or flow-values-reports
        
    Returns:
        Dict with extracted statistics
    """
    results = response.get("data", {}).get("attributes", {}).get("results", [])
    if not results:
        logger.debug("extract_statistics: No results in response")
        return {}
    
    result = results[0]
    stats = result.get("statistics", {})
    
    if not stats:
        logger.warning(f"extract_statistics: No statistics dict in result for flow {result.get('id', 'unknown')}")
        return {}
    
    # Convert rates from decimal to percentage
    # Handle case where rates might already be percentages (check if > 1)
    open_rate = stats.get("open_rate", 0)
    click_rate = stats.get("click_rate", 0)
    conversion_rate = stats.get("conversion_rate", 0)
    
    # If rate is > 1, assume it's already a percentage, otherwise convert from decimal
    open_rate_pct = open_rate if open_rate > 1 else open_rate * 100
    click_rate_pct = click_rate if click_rate > 1 else click_rate * 100
    conversion_rate_pct = conversion_rate if conversion_rate > 1 else conversion_rate * 100
    
    extracted = {
        "recipients": stats.get("recipients", 0),
        "opens": stats.get("opens", 0),
        "open_rate": open_rate_pct,
        "clicks": stats.get("clicks", 0),
        "click_rate": click_rate_pct,
        "conversions": stats.get("conversions", 0),
        "conversion_rate": conversion_rate_pct,
        "revenue": stats.get("conversion_value", 0),
    }
    
    logger.debug(f"extract_statistics: Extracted stats - recipients={extracted['recipients']}, revenue={extracted['revenue']}, open_rate={extracted['open_rate']:.2f}%")
    
    return extracted


def parse_nested_aggregate_values(values: List[Any]) -> float:
    """
    Parse and sum nested aggregate values (e.g., flow revenue grouped by flow).
    
    Args:
        values: List of nested values (can be dict, list, or scalar)
        
    Returns:
        Sum of all parsed values
    """
    total = 0.0
    
    if isinstance(values, dict):
        # Sum all values in dict
        for v in values.values():
            total += parse_metric_value(v)
    elif isinstance(values, list):
        # Sum all values in list
        for v in values:
            total += parse_metric_value(v)
    else:
        # Single value
        total = parse_metric_value(values)
    
    return total

