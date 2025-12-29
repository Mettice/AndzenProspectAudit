"""Date formatting and parsing utilities."""
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Try to import relativedelta, fallback to timedelta-based approximation
try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    # Simple fallback that approximates relativedelta for months
    class relativedelta:
        def __init__(self, months: int = 0, days: int = 0):
            self.months = months
            self.days = days
        
        def __rsub__(self, other):
            # Approximate months as 30 days each
            total_days = (self.months * 30) + self.days
            return other - timedelta(days=total_days)


def ensure_z_suffix(dt_str: str) -> str:
    """
    Ensure ISO datetime has Z suffix for API.
    
    Handles both Z and +00:00 timezone formats, converting to Z.
    
    Args:
        dt_str: ISO datetime string
        
    Returns:
        ISO datetime string with Z suffix
    """
    # Remove microseconds
    dt_str = dt_str.split(".")[0]
    
    # If already ends with Z, return as-is
    if dt_str.endswith("Z"):
        return dt_str
    
    # If ends with +00:00, replace with Z
    if dt_str.endswith("+00:00"):
        return dt_str.replace("+00:00", "Z")
    
    # Otherwise, add Z
    return f"{dt_str}Z"


def format_date_range(start: datetime, end: datetime) -> Dict[str, str]:
    """
    Format date range for API requests.
    
    Args:
        start: Start datetime
        end: End datetime
        
    Returns:
        Dict with 'start' and 'end' ISO formatted strings with Z suffix
    """
    return {
        "start": ensure_z_suffix(start.isoformat()),
        "end": ensure_z_suffix(end.isoformat())
    }


def parse_iso_date(date_str: str) -> datetime:
    """
    Parse ISO date string to datetime.
    
    Handles both Z suffix and +00:00 timezone formats.
    Prevents double-processing of timezone suffixes.
    
    Args:
        date_str: ISO date string
        
    Returns:
        datetime object
    """
    # Remove any existing +00:00+00:00 (double processing)
    if '+00:00+00:00' in date_str:
        date_str = date_str.replace('+00:00+00:00', '+00:00')
    
    # Replace Z with +00:00 for consistent parsing, but only if Z exists
    if date_str.endswith('Z'):
        normalized = date_str.replace('Z', '+00:00')
    elif date_str.endswith('+00:00'):
        # Already has +00:00, use as-is
        normalized = date_str
    elif '+' in date_str or date_str.endswith('Z'):
        # Has timezone info, use as-is
        normalized = date_str
    else:
        # No timezone, assume UTC
        normalized = f"{date_str}+00:00"
    
    return datetime.fromisoformat(normalized)


def get_date_range_days(days: int, account_timezone: Optional[str] = None) -> Dict[str, datetime]:
    """
    Get date range for last N days with timezone handling.
    
    Args:
        days: Number of days to look back
        account_timezone: Account timezone (e.g., "Australia/Sydney", "US/Eastern")
        
    Returns:
        Dict with 'start' and 'end' datetime objects in UTC
    """
    # Use UTC as default for consistency with Klaviyo API
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    logger.debug(f"Date range: {start_date.isoformat()} to {end_date.isoformat()}")
    
    return {
        "start": start_date,
        "end": end_date
    }


def get_date_range_months(months: int) -> Dict[str, datetime]:
    """
    Get date range for last N months.
    
    Args:
        months: Number of months to look back
        
    Returns:
        Dict with 'start' and 'end' datetime objects
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - relativedelta(months=months)
    return {
        "start": start_date,
        "end": end_date
    }


def get_klaviyo_compatible_range(days: int, timezone_name: str = "UTC") -> Dict[str, str]:
    """
    Get Klaviyo-compatible date range strings with timezone handling.
    
    Cherry Collectables appears to be in Australian timezone, which may cause 
    date range mismatches when using system UTC vs local business timezone.
    
    Args:
        days: Number of days to look back
        timezone_name: Klaviyo timezone name (e.g., "Australia/Sydney", "UTC")
        
    Returns:
        Dict with 'start', 'end' ISO strings and 'timezone' for API requests
    """
    # Get date range in UTC but extend the range to capture timezone differences
    # Add an extra day on each side to ensure we capture data across timezone boundaries
    extended_days = days + 2
    date_range = get_date_range_days(extended_days)
    
    # Start from beginning of first day, end at end of last day to capture all data
    start_dt = date_range["start"].replace(hour=0, minute=0, second=0, microsecond=0)
    end_dt = date_range["end"].replace(hour=23, minute=59, second=59, microsecond=0)
    
    # Format for Klaviyo API (no milliseconds, Z suffix)
    start_str = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    logger.info(f"Klaviyo date range: {start_str} to {end_str} (timezone: {timezone_name}, extended by 2 days)")
    
    return {
        "start": start_str,
        "end": end_str,
        "timezone": timezone_name
    }


def get_previous_period_range(current_start: datetime, current_end: datetime, days: int) -> Dict[str, datetime]:
    """
    Calculate previous period date range for period-over-period comparison.
    
    The strategist always compares with the previous period. If current period
    is 90 days (Sep 28 - Dec 27), previous period is the 90 days before that
    (Jun 30 - Sep 27).
    
    Args:
        current_start: Start date of current period
        current_end: End date of current period (also start of previous period calculation)
        days: Number of days in the period
        
    Returns:
        Dict with 'start' and 'end' datetime objects for previous period
    """
    # Previous period ends just before current period starts
    previous_end = current_start - timedelta(days=1)
    # Previous period starts N days before that
    previous_start = previous_end - timedelta(days=days - 1)
    
    logger.debug(f"Previous period: {previous_start.isoformat()} to {previous_end.isoformat()}")
    
    return {
        "start": previous_start,
        "end": previous_end
    }

