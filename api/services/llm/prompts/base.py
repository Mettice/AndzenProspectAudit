"""
Base utilities for prompt generation.
"""
from typing import Dict, Any
from api.utils.security import validate_prompt_data, sanitize_prompt_input


def format_data_for_prompt(data: Dict[str, Any], indent: int = 0, sanitize: bool = True) -> str:
    """
    Format data dictionary for prompt readability with optional sanitization.
    
    Args:
        data: Data dictionary to format
        indent: Indentation level
        sanitize: Whether to sanitize user-controlled inputs
    
    Returns:
        Formatted string representation
    """
    if sanitize:
        # Sanitize user-controlled inputs before formatting
        data = validate_prompt_data(data)
    
    lines = []
    prefix = "  " * indent
    
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(format_data_for_prompt(value, indent + 1, sanitize=False))  # Already sanitized
        elif isinstance(value, list):
            lines.append(f"{prefix}{key}: {len(value)} items")
        else:
            # Additional sanitization for string values in prompts
            if isinstance(value, str) and sanitize:
                value = sanitize_prompt_input(value, max_length=500)
            lines.append(f"{prefix}{key}: {value}")
    
    return "\n".join(lines)


def get_json_output_instructions() -> str:
    """
    Get standardized JSON output instructions that prevent nested JSON.
    
    These instructions are explicit about:
    1. Returning plain JSON (not markdown)
    2. Primary/secondary fields should be plain text strings, NOT JSON objects
    3. No nested JSON structures
    """
    return """
CRITICAL JSON FORMAT REQUIREMENTS:
1. Return ONLY valid JSON - do NOT wrap in markdown code blocks (no ```json)
2. Start with { and end with } - return the JSON object directly
3. The "primary" field must be a plain text string, NOT a JSON object or nested JSON
4. The "secondary" field must be a plain text string, NOT a JSON object or nested JSON
5. Do NOT nest JSON inside the "primary" or "secondary" fields
6. Example of CORRECT format: {"primary": "This is plain text analysis", "secondary": "More plain text"}
7. Example of WRONG format: {"primary": "{\"primary\": \"text\"}"} - DO NOT DO THIS

Return your response as valid JSON now:"""


def get_currency_symbol(currency: str) -> str:
    """
    Get currency symbol for display.
    
    Args:
        currency: Currency code (e.g., "USD", "AUD")
    
    Returns:
        Currency symbol (e.g., "$", "A$")
    """
    try:
        from ....klaviyo.utils import get_currency_symbol
        return get_currency_symbol(currency)
    except ImportError:
        # Fallback if import fails
        return "$" if currency == "USD" else f"{currency} "


def get_strategic_value_instructions() -> str:
    """
    Get standard instructions for including strategic value elements in prompts.
    
    Returns:
        Instructions string for strategic value elements
    """
    return """
STRATEGIC VALUE REQUIREMENTS:
1. **ROI & Impact Quantification**: For each recommendation, estimate:
   - Revenue impact (e.g., "$25K/month", "$100K/year")
   - Effort required (e.g., "2 hours", "1 week", "20 hours")
   - ROI percentage (e.g., "1250% ROI")
   - Payback period (e.g., "1 month")

2. **Quick Wins Identification**: Identify opportunities with:
   - High impact, low effort
   - Quick implementation (1-2 weeks)
   - Immediate revenue recovery or improvement
   - Format: "Fix X (2 hours) → $5K/month revenue recovery"

3. **Risk Flags & Urgency**: Flag critical issues with:
   - Severity level (critical/high/medium/low)
   - Revenue impact if not fixed (e.g., "Losing $5K/month")
   - Urgency timeline (e.g., "Fix within 7 days")
   - Format: "⚠️ CRITICAL: [Issue] - [Impact] - [Urgency]"

4. **Implementation Roadmaps**: For each recommendation, provide:
   - Step-by-step implementation guide
   - Timeline for each step
   - Resource requirements
   - Dependencies (what must be done first)
   - Format: "Step 1: [Action] (1 day), Step 2: [Action] (3 days)..."

5. **Root Cause Analysis**: Explain WHY performance is what it is:
   - Identify performance drivers
   - Explain correlations (e.g., "Open rates dropped because send frequency increased 3x")
   - Diagnose underlying problems
   - Format: "[Metric] is [value] because [root cause], which led to [consequence]"
"""

