"""
HTML Formatter for LLM Output

Converts markdown-style LLM output to properly formatted HTML with styling.
"""
import re
import logging

logger = logging.getLogger(__name__)


class LLMOutputFormatter:
    """Format LLM output from markdown to clean HTML."""
    
    @staticmethod
    def format_to_html(text: str) -> str:
        """
        Convert markdown-style LLM output to clean, styled HTML.
        
        Args:
            text: Raw LLM output (may contain markdown)
        
        Returns:
            Clean HTML with proper formatting
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Remove any existing <p> tags that might be wrapping everything
        text = re.sub(r'^<p>(.*)</p>$', r'\1', text.strip(), flags=re.DOTALL)
        
        # Convert **bold** to <strong>
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        
        # Convert *italic* to <em> (but not ** which is already handled)
        text = re.sub(r'(?<!\*)\*(?!\*)([^*]+)\*(?!\*)', r'<em>\1</em>', text)
        
        # Convert ### headers to <h4>
        text = re.sub(r'###\s*([^\n]+)', r'<h4 class="content-heading">\1</h4>', text)
        
        # Convert ## headers to <h3>
        text = re.sub(r'##\s*([^\n]+)', r'<h3 class="content-heading">\1</h3>', text)
        
        # Convert bullet points with numbers like (1), (2), (3)
        text = re.sub(r'\((\d+)\)\s*([^\n]+)', r'<div class="numbered-point"><span class="point-number">\1</span><span class="point-text">\2</span></div>', text)
        
        # Convert bullet points with - or * or •
        text = re.sub(r'^[\-\*•]\s+(.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
        
        # Wrap consecutive <li> in <ul>
        text = re.sub(r'(<li>.*?</li>(?:\s*<li>.*?</li>)*)', r'<ul class="content-list">\1</ul>', text, flags=re.DOTALL)
        
        # Split into paragraphs at double newlines
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Wrap non-tag content in <p> tags
        formatted_paragraphs = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Don't wrap if it's already an HTML block element
            if para.startswith(('<h', '<ul', '<ol', '<div', '<table', '<strong', '<p')):
                formatted_paragraphs.append(para)
            else:
                formatted_paragraphs.append(f'<p class="content-text">{para}</p>')
        
        result = '\n'.join(formatted_paragraphs)
        
        # Add styling wrapper
        if result:
            result = f'<div class="formatted-content">{result}</div>'
        
        return result
    
    @staticmethod
    def format_list_items(items: list) -> str:
        """
        Format a list of items into styled HTML list.
        
        Args:
            items: List of strings or dicts
        
        Returns:
            HTML unordered list
        """
        if not items:
            return ""
        
        list_html = '<ul class="formatted-list">'
        for item in items:
            if isinstance(item, dict):
                # Handle structured items
                text = item.get('text') or item.get('recommendation') or str(item)
            else:
                text = str(item)
            
            # Format the text
            text = LLMOutputFormatter.format_to_html(text)
            # Remove the outer wrapper since we're in a list
            text = re.sub(r'<div class="formatted-content">(.*)</div>', r'\1', text, flags=re.DOTALL)
            text = re.sub(r'<p class="content-text">(.*)</p>', r'\1', text, flags=re.DOTALL)
            
            list_html += f'<li>{text}</li>'
        
        list_html += '</ul>'
        return list_html
    
    @staticmethod
    def add_content_styling() -> str:
        """
        Return CSS for formatted content.
        
        Returns:
            CSS string
        """
        return """
        <style>
        .formatted-content {
            font-family: 'Montserrat', sans-serif;
            font-size: 1rem;
            line-height: 1.8;
            color: #000000;
        }
        
        .formatted-content p.content-text {
            margin-bottom: 1.2rem;
            line-height: 1.8;
        }
        
        .formatted-content strong {
            font-weight: 700;
            color: #000000;
        }
        
        .formatted-content em {
            font-style: italic;
            color: #374151;
        }
        
        .formatted-content h3.content-heading {
            font-size: 1.25rem;
            font-weight: 700;
            color: #000000;
            margin: 1.5rem 0 1rem 0;
        }
        
        .formatted-content h4.content-heading {
            font-size: 1.1rem;
            font-weight: 600;
            color: #000000;
            margin: 1.2rem 0 0.8rem 0;
        }
        
        .formatted-content ul.content-list {
            list-style-type: disc;
            padding-left: 2rem;
            margin: 1rem 0;
        }
        
        .formatted-content ul.content-list li {
            margin-bottom: 0.6rem;
            line-height: 1.7;
        }
        
        .formatted-content .numbered-point {
            display: flex;
            gap: 0.75rem;
            margin-bottom: 1rem;
            align-items: flex-start;
        }
        
        .formatted-content .point-number {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 24px;
            height: 24px;
            background: #65DA4F;
            color: white;
            font-weight: 700;
            font-size: 0.85rem;
            border-radius: 50%;
            flex-shrink: 0;
        }
        
        .formatted-content .point-text {
            flex: 1;
            line-height: 1.7;
        }
        
        .formatted-list {
            list-style-type: none;
            padding-left: 0;
        }
        
        .formatted-list li {
            padding-left: 1.5rem;
            margin-bottom: 0.8rem;
            position: relative;
            line-height: 1.7;
        }
        
        .formatted-list li:before {
            content: "→";
            position: absolute;
            left: 0;
            color: #65DA4F;
            font-weight: 700;
        }
        </style>
        """


def format_llm_output(text: str) -> str:
    """
    Quick utility function to format LLM output.
    
    Args:
        text: Raw LLM output
    
    Returns:
        Formatted HTML
    """
    return LLMOutputFormatter.format_to_html(text)

