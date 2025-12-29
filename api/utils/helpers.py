"""
Utility helper functions.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format amount as currency string."""
    return f"${amount:,.2f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format value as percentage string."""
    return f"{value:.{decimals}f}%"


def calculate_date_range(days: int = 365) -> Dict[str, str]:
    """Calculate date range for last N days."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    return {
        "start": start_date.isoformat(),
        "end": end_date.isoformat()
    }


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero."""
    if denominator == 0:
        return default
    return numerator / denominator


def calculate_growth_rate(current: float, previous: float) -> float:
    """Calculate growth rate percentage."""
    if previous == 0:
        return 0.0
    return ((current - previous) / previous) * 100


def format_date(date_string: str, format: str = "%B %d, %Y") -> str:
    """Format date string to readable format."""
    try:
        dt = datetime.fromisoformat(date_string.replace("Z", "+00:00"))
        return dt.strftime(format)
    except Exception:
        return date_string


def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Load JSON file safely."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def save_json_file(data: Dict[str, Any], file_path: str) -> bool:
    """Save data to JSON file safely."""
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False

