"""Filter building utilities for Klaviyo API filters."""
from typing import List, Optional


def build_metric_filter(
    start_date: str,
    end_date: str,
    additional_filters: Optional[List[str]] = None
) -> List[str]:
    """
    Build filter array for metric aggregates endpoint.
    
    Args:
        start_date: Start datetime in ISO format with Z suffix
        end_date: End datetime in ISO format with Z suffix
        additional_filters: Additional filter conditions (max 1 allowed by API)
        
    Returns:
        List of filter strings
    """
    filters = [
        f"greater-or-equal(datetime,{start_date})",
        f"less-than(datetime,{end_date})"
    ]
    
    # Add any additional filters (only 1 additional filter allowed per docs)
    if additional_filters:
        filters.extend(additional_filters[:1])  # Limit to 1 additional filter
    
    return filters


def build_campaign_filter(
    channel: str = "email",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Optional[str]:
    """
    Build filter string for campaigns endpoint.
    
    Note: Date filters on campaigns may not work with the API,
    so they're commented out. Filtering is done in Python instead.
    
    Args:
        channel: Channel type (email, sms, push)
        start_date: Start datetime (not used in filter, for reference only)
        end_date: End datetime (not used in filter, for reference only)
        
    Returns:
        Filter string or None
    """
    filters = []
    filters.append(f"equals(messages.channel,'{channel}')")
    
    # Note: Date filters on campaigns may not work with the API
    # We'll fetch all campaigns and filter in Python instead
    # if start_date and end_date:
    #     filters.append(f"greater-or-equal(created_at,'{start_date}')")
    #     filters.append(f"less-or-equal(created_at,'{end_date}')")
    
    # Combine with and() operator if multiple conditions
    if len(filters) > 1:
        return f"and({','.join(filters)})"
    elif filters:
        return filters[0]
    return None


def build_reporting_filter(ids: List[str], id_type: str) -> str:
    """
    Build filter string for Reporting API (campaign-values-reports, flow-values-reports).
    
    Uses different syntax than regular API:
    - Single ID: equals(campaign_id,"ID")
    - Multiple IDs: contains-any(campaign_id,["ID1","ID2"])
    
    Args:
        ids: List of IDs to filter by
        id_type: Type of ID ("campaign_id", "flow_id", etc.)
        
    Returns:
        Filter string
    """
    ids_subset = ids[:100]  # Limit to 100 per request
    
    if len(ids_subset) == 1:
        return f'equals({id_type},"{ids_subset[0]}")'
    else:
        # Use contains-any for multiple IDs
        ids_formatted = '","'.join(ids_subset)
        return f'contains-any({id_type},["{ids_formatted}"])'

