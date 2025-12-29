# Image Embedding Guide

## Overview

The audit report system now supports embedding images directly into HTML reports using base64 data URIs. This matches the format used in sample audits like Dreamland Baby and Urth.

## Features

- **File Path Support**: Embed images from local file paths
- **URL Support**: Download and embed images from URLs
- **Base64 Support**: Use existing base64 data URIs
- **Automatic Encoding**: Automatically detects image type and encodes to base64

## Usage in Templates

### Method 1: Using the `embed_image` filter

```jinja2
{# Embed from file path #}
{{ 'assets/client_logo.png' | embed_image('Client Logo', 'client-logo') }}

{# Embed from URL #}
{{ 'https://example.com/image.png' | embed_image('Image', 'section-image') }}

{# Embed with just alt text #}
{{ 'path/to/image.png' | embed_image('Alt text') }}
```

### Method 2: Using the `image_data_uri` filter

```jinja2
{# Get data URI and use in img tag #}
<img src="{{ 'assets/image.png' | image_data_uri }}" alt="Image" class="my-image">
```

### Method 3: In Python Code (Data Preparation)

```python
from api.services.report.image_handler import ImageEmbedder

# Embed image and add to context
image_html = ImageEmbedder.embed_image(
    'path/to/image.png',
    alt_text='Description',
    css_class='report-image'
)

# Or get just the data URI
data_uri = ImageEmbedder.get_data_uri('path/to/image.png')
```

## Supported Image Formats

- PNG (`.png`)
- JPEG (`.jpg`, `.jpeg`)
- GIF (`.gif`)
- SVG (`.svg`)
- WebP (`.webp`)

## Example Use Cases

### 1. Client Logo on Cover Page

```jinja2
{# In templates/sections/cover.html #}
<div class="cover-client">
    {% if client_logo_path %}
        {{ client_logo_path | embed_image(client_name, 'client-logo') }}
    {% else %}
        <h1 class="client-name">{{ client_name|upper }}</h1>
    {% endif %}
</div>
```

### 2. Screenshots in Sections

```jinja2
{# In any section template #}
<div class="screenshot-section">
    <h3>Dashboard Screenshot</h3>
    {{ dashboard_screenshot_path | embed_image('Klaviyo Dashboard', 'dashboard-screenshot') }}
</div>
```

### 3. Decorative Images

```jinja2
{# Background or decorative images #}
<div class="section-header">
    {{ 'assets/decorative-brush.png' | embed_image('', 'decorative-image') }}
    <h1>Section Title</h1>
</div>
```

## Benefits

1. **Self-Contained Reports**: Images are embedded directly in HTML, no external dependencies
2. **PDF Compatibility**: Embedded images work perfectly when converting to PDF
3. **Offline Viewing**: Reports can be viewed offline without broken image links
4. **Consistent Format**: Matches the format used in sample audits

## Implementation Details

- Images are automatically encoded to base64 when the template is rendered
- Large images may increase HTML file size (consider compression for production)
- Failed image loads fall back to using the original source (file path or URL)
- All errors are logged for debugging

## File Structure

```
api/services/report/
  ├── image_handler.py      # Image embedding utility
  └── __init__.py           # Registers Jinja2 filters
```

## Notes

- For very large images, consider optimizing before embedding
- Base64 encoding increases file size by ~33% compared to binary
- Images embedded this way are included in the HTML file size
- Consider using this for logos, screenshots, and small decorative images

