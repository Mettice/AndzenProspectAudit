"""Currency and number formatting utilities."""
from typing import Optional

# Currency code to symbol mapping
CURRENCY_SYMBOLS = {
    "USD": "$",
    "AUD": "A$",
    "GBP": "£",
    "EUR": "€",
    "CAD": "C$",
    "NZD": "NZ$",
    "JPY": "¥",
    "CNY": "¥",
    "INR": "₹",
    "SGD": "S$",
    "HKD": "HK$",
    "CHF": "CHF ",
    "SEK": "kr ",
    "NOK": "kr ",
    "DKK": "kr ",
    "PLN": "zł ",
    "MXN": "MX$",
    "BRL": "R$",
    "ZAR": "R ",
}


def get_currency_symbol(currency_code: str) -> str:
    """
    Get currency symbol for a currency code.
    
    Args:
        currency_code: ISO currency code (e.g., "AUD", "USD", "GBP")
        
    Returns:
        Currency symbol (e.g., "A$", "$", "£")
    """
    return CURRENCY_SYMBOLS.get(currency_code.upper(), f"{currency_code} ")


def format_currency(value: float, currency_code: str = "USD", prefix: Optional[str] = None) -> str:
    """
    Format currency value with appropriate suffix (K, M).
    
    Args:
        value: Currency value
        currency_code: ISO currency code (e.g., "AUD", "USD", "GBP")
                      If provided, will use appropriate symbol
        prefix: Optional currency prefix (overrides currency_code if provided)
        
    Returns:
        Formatted currency string (e.g., "A$1,234.56", "$1.2M")
    """
    if prefix is None:
        prefix = get_currency_symbol(currency_code)
    
    if value >= 1000000:
        return f"{prefix}{value/1000000:.2f}M"
    elif value >= 1000:
        return f"{prefix}{value/1000:.1f}K"
    return f"{prefix}{value:,.2f}"


def format_currency_simple(value: float, prefix: str = "$") -> str:
    """
    Simple currency formatter (backward compatibility).
    
    Args:
        value: Currency value
        prefix: Currency prefix (default: "$")
        
    Returns:
        Formatted currency string
    """
    return format_currency(value, "USD", prefix)


def format_large_number(value: float) -> str:
    """
    Format large number with appropriate suffix (k, M).
    Matches sample audit format: 81k (not 81.0k), 1.3M (not 1.30M).
    
    Args:
        value: Number value
        
    Returns:
        Formatted number string
    """
    if value >= 1000000:
        # Format as M, remove .0 if whole number
        millions = value / 1000000
        if millions == int(millions):
            return f"{int(millions)}M"
        return f"{millions:.1f}M"
    elif value >= 1000:
        # Format as k, remove .0 if whole number
        thousands = value / 1000
        if thousands == int(thousands):
            return f"{int(thousands)}k"
        return f"{thousands:.1f}k"
    return str(int(value))

