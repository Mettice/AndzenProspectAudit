"""
Image embedding utility for audit reports.

Supports:
- Converting image files to base64 data URIs
- Embedding images in HTML templates
- Handling URLs, file paths, and base64 strings
"""

import base64
import logging
from pathlib import Path
from typing import Optional, Union
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ImageEmbedder:
    """Utility class for embedding images in HTML reports."""
    
    @staticmethod
    def encode_file_to_base64(image_path: Union[str, Path]) -> Optional[str]:
        """
        Encode an image file to base64 data URI.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 data URI string (e.g., "data:image/png;base64,...") or None if error
        """
        try:
            image_path = Path(image_path)
            if not image_path.exists():
                logger.warning(f"Image file not found: {image_path}")
                return None
            
            # Determine MIME type from extension
            mime_types = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.svg': 'image/svg+xml',
                '.webp': 'image/webp'
            }
            
            ext = image_path.suffix.lower()
            mime_type = mime_types.get(ext, 'image/png')
            
            # Read and encode the image
            with open(image_path, 'rb') as f:
                image_data = f.read()
                base64_data = base64.b64encode(image_data).decode('utf-8')
            
            return f"data:{mime_type};base64,{base64_data}"
            
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {e}")
            return None
    
    @staticmethod
    def encode_url_to_base64(image_url: str) -> Optional[str]:
        """
        Download an image from URL and encode to base64.
        
        Args:
            image_url: URL to the image
            
        Returns:
            Base64 data URI string or None if error
        """
        try:
            import httpx
            
            # Download the image
            response = httpx.get(image_url, timeout=10.0)
            response.raise_for_status()
            
            # Determine MIME type from Content-Type header or URL
            content_type = response.headers.get('Content-Type', 'image/png')
            if not content_type.startswith('image/'):
                # Try to determine from URL extension
                parsed = urlparse(image_url)
                ext = Path(parsed.path).suffix.lower()
                mime_types = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.gif': 'image/gif',
                    '.svg': 'image/svg+xml',
                    '.webp': 'image/webp'
                }
                content_type = mime_types.get(ext, 'image/png')
            
            # Encode to base64
            base64_data = base64.b64encode(response.content).decode('utf-8')
            return f"data:{content_type};base64,{base64_data}"
            
        except Exception as e:
            logger.error(f"Error downloading and encoding image from URL {image_url}: {e}")
            return None
    
    @staticmethod
    def embed_image(
        image_source: Union[str, Path],
        alt_text: str = "",
        css_class: str = ""
    ) -> str:
        """
        Create an HTML img tag with embedded base64 image.
        
        Args:
            image_source: Path to image file, URL, or base64 data URI
            alt_text: Alt text for the image
            css_class: CSS class for styling
            
        Returns:
            HTML img tag string
        """
        # Check if already a data URI
        if isinstance(image_source, str) and image_source.startswith('data:image/'):
            data_uri = image_source
        # Check if it's a URL
        elif isinstance(image_source, str) and (image_source.startswith('http://') or image_source.startswith('https://')):
            data_uri = ImageEmbedder.encode_url_to_base64(image_source)
            if not data_uri:
                logger.warning(f"Failed to embed image from URL: {image_source}")
                return f'<img src="{image_source}" alt="{alt_text}" class="{css_class}">'
        # Assume it's a file path
        else:
            data_uri = ImageEmbedder.encode_file_to_base64(image_source)
            if not data_uri:
                logger.warning(f"Failed to embed image from path: {image_source}")
                return f'<img src="{image_source}" alt="{alt_text}" class="{css_class}">'
        
        class_attr = f' class="{css_class}"' if css_class else ''
        alt_attr = f' alt="{alt_text}"' if alt_text else ''
        
        return f'<img src="{data_uri}"{alt_attr}{class_attr}>'
    
    @staticmethod
    def get_data_uri(image_source: Union[str, Path]) -> Optional[str]:
        """
        Get base64 data URI from image source (file path, URL, or existing data URI).
        
        Args:
            image_source: Path to image file, URL, or base64 data URI
            
        Returns:
            Base64 data URI string or None if error
        """
        # Already a data URI
        if isinstance(image_source, str) and image_source.startswith('data:image/'):
            return image_source
        
        # URL
        if isinstance(image_source, str) and (image_source.startswith('http://') or image_source.startswith('https://')):
            return ImageEmbedder.encode_url_to_base64(image_source)
        
        # File path
        return ImageEmbedder.encode_file_to_base64(image_source)


# Jinja2 filter function for templates
def embed_image_filter(image_source: Union[str, Path], alt_text: str = "", css_class: str = "") -> str:
    """
    Jinja2 filter to embed images in templates.
    
    Usage in template:
        {{ 'path/to/image.png' | embed_image('Alt text', 'image-class') }}
        {{ image_url | embed_image }}
    """
    return ImageEmbedder.embed_image(image_source, alt_text, css_class)


def get_image_data_uri(image_source: Union[str, Path]) -> Optional[str]:
    """
    Jinja2 filter to get base64 data URI.
    
    Usage in template:
        <img src="{{ 'path/to/image.png' | image_data_uri }}" alt="Image">
    """
    return ImageEmbedder.get_data_uri(image_source)

