"""
Security utilities for input validation and sanitization.
"""
import re
import html
from typing import Any, Dict, List, Union


def sanitize_prompt_input(value: str, max_length: int = 200) -> str:
    """
    Sanitize user input for LLM prompts to prevent injection attacks.
    
    Args:
        value: The input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string safe for prompt inclusion
    """
    if not isinstance(value, str):
        value = str(value)
    
    # Remove potentially dangerous patterns
    value = re.sub(r'[{}]', '', value)  # Remove braces that could break JSON
    value = re.sub(r'["\']', '', value)  # Remove quotes
    value = re.sub(r'[\\]', '', value)  # Remove backslashes
    value = re.sub(r'[\r\n\t]', ' ', value)  # Replace newlines/tabs with spaces
    
    # Remove potentially malicious instruction patterns
    dangerous_patterns = [
        r'ignore\s+(previous|all|above)',
        r'forget\s+(everything|instructions|previous)',
        r'you\s+are\s+now',
        r'act\s+as\s+if',
        r'pretend\s+(to\s+be|that)',
        r'system\s*:',
        r'assistant\s*:',
        r'human\s*:',
        r'user\s*:',
        r'<\|.*?\|>',  # Special tokens
        r'}\s*{',  # JSON breaking patterns
    ]
    
    for pattern in dangerous_patterns:
        value = re.sub(pattern, '', value, flags=re.IGNORECASE)
    
    # Truncate to max length
    value = value[:max_length]
    
    # Clean up extra whitespace
    value = ' '.join(value.split())
    
    return value.strip()


def validate_prompt_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize all user inputs in prompt data.
    
    Args:
        data: Dictionary containing user inputs for prompts
        
    Returns:
        Sanitized data dictionary
        
    Raises:
        ValueError: If suspicious input patterns are detected
    """
    sanitized_data = {}
    
    # Fields that need sanitization (user-controlled inputs)
    user_input_fields = {
        'client_name': 100,
        'industry': 50,
        'auditor_name': 100,
        'client_type': 20,
        'client_code': 20,
    }
    
    for key, value in data.items():
        if key in user_input_fields:
            max_length = user_input_fields[key]
            
            # Additional validation for critical fields
            if key == 'client_name' and isinstance(value, str):
                # Check for suspicious patterns in client name
                if re.search(r'(system|admin|root|test)', value.lower()):
                    raise ValueError(f"Suspicious client name detected: {value}")
            
            sanitized_data[key] = sanitize_prompt_input(str(value), max_length)
        else:
            # Pass through non-user inputs (metrics, calculated data, etc.)
            sanitized_data[key] = value
    
    return sanitized_data


def escape_html_content(content: str) -> str:
    """
    Escape HTML content to prevent XSS attacks.
    
    Args:
        content: Raw HTML content
        
    Returns:
        Escaped HTML content
    """
    if not isinstance(content, str):
        content = str(content)
    
    # Use html.escape to escape HTML entities
    escaped = html.escape(content, quote=True)
    
    # Additional escaping for JavaScript contexts
    escaped = escaped.replace('<', '&lt;')
    escaped = escaped.replace('>', '&gt;')
    escaped = escaped.replace('"', '&quot;')
    escaped = escaped.replace("'", '&#x27;')
    escaped = escaped.replace('/', '&#x2F;')
    
    return escaped


def sanitize_html_content(content: str, allowed_tags: List[str] = None) -> str:
    """
    Sanitize HTML content by allowing only safe tags and removing dangerous ones.
    
    Args:
        content: HTML content to sanitize
        allowed_tags: List of allowed HTML tags (default: basic formatting tags)
        
    Returns:
        Sanitized HTML content
    """
    if not isinstance(content, str):
        content = str(content)
    
    if allowed_tags is None:
        # Allow only basic, safe formatting tags
        allowed_tags = [
            'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'blockquote', 'table', 'thead', 'tbody', 'tr', 'td', 'th',
            'div', 'span'
        ]
    
    # Remove script tags and their content
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove dangerous event handlers
    content = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', content, flags=re.IGNORECASE)
    
    # Remove javascript: protocols
    content = re.sub(r'javascript\s*:', '', content, flags=re.IGNORECASE)
    
    # Remove data: protocols (except basic data)
    content = re.sub(r'data\s*:[^,]*,', '', content, flags=re.IGNORECASE)
    
    # Remove style attributes that could contain CSS expressions
    content = re.sub(r'style\s*=\s*["\'][^"\']*["\']', '', content, flags=re.IGNORECASE)
    
    # If no tags allowed, escape all HTML
    if not allowed_tags:
        return escape_html_content(content)
    
    # Remove any tags not in the allowed list
    allowed_pattern = '|'.join(allowed_tags)
    # Remove disallowed opening tags
    content = re.sub(f'<(?!/?(?:{allowed_pattern})(?:\s[^>]*)?>) [^>]*>', '', content, flags=re.IGNORECASE)
    
    return content


def create_safe_html_template_filter():
    """
    Create a safe HTML filter that can be used in Jinja2 templates.
    This should replace |safe in templates.
    """
    def safe_html(content: str) -> str:
        """Template filter for safe HTML rendering."""
        if not content:
            return ""
        
        # Check if content looks like it contains user input
        is_suspicious, reason = check_suspicious_input(content)
        if is_suspicious:
            # If suspicious, escape all HTML
            return escape_html_content(content)
        
        # Otherwise, sanitize while preserving safe formatting
        return sanitize_html_content(content)
    
    return safe_html


def validate_file_path(file_path: str, allowed_dirs: List[str] = None) -> bool:
    """
    Validate file path to prevent directory traversal attacks.
    
    Args:
        file_path: File path to validate
        allowed_dirs: List of allowed directory prefixes
        
    Returns:
        True if path is safe, False otherwise
    """
    if not isinstance(file_path, str):
        return False
    
    # Check for directory traversal patterns
    dangerous_patterns = [
        '..',
        '~/',
        '/etc/',
        '/proc/',
        '/sys/',
        '/var/',
        '/tmp/',
        '\\',
    ]
    
    for pattern in dangerous_patterns:
        if pattern in file_path:
            return False
    
    # If allowed directories specified, check against them
    if allowed_dirs:
        for allowed_dir in allowed_dirs:
            if file_path.startswith(allowed_dir):
                return True
        return False
    
    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent security issues.
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename
    """
    if not isinstance(filename, str):
        filename = str(filename)
    
    # Remove dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)  # Remove control characters
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure minimum length
    if not filename:
        filename = 'file'
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_len = 250 - len(ext) - 1
        filename = name[:max_name_len] + ('.' + ext if ext else '')
    
    return filename


def check_suspicious_input(text: str) -> tuple[bool, str]:
    """
    Check if input contains suspicious patterns that might indicate attack attempts.
    
    Args:
        text: Text to check
        
    Returns:
        Tuple of (is_suspicious, reason)
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Patterns that indicate potential attacks
    suspicious_patterns = [
        (r'<script[^>]*>.*?</script>', 'Script tag detected'),
        (r'javascript:', 'JavaScript protocol detected'),
        (r'data:.*?base64', 'Base64 data URI detected'),
        (r'on\w+\s*=', 'Event handler detected'),
        (r'eval\s*\(', 'eval() function detected'),
        (r'document\.(cookie|domain)', 'Document property access detected'),
        (r'window\.(location|open)', 'Window method access detected'),
        (r'\.\./', 'Directory traversal detected'),
        (r'(union|select|insert|drop|delete)\s+', 'SQL keywords detected'),
        (r'<\?php', 'PHP code detected'),
        (r'<%.*?%>', 'Template code detected'),
    ]
    
    for pattern, reason in suspicious_patterns:
        if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
            return True, reason
    
    return False, ""