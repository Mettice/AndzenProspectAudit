# Image Embedding Examples

## Sample Audit Analysis

After reviewing the sample audits (Dreamland Baby, Urth, Ritual Hockey), I found that they use base64-embedded images for:

1. **Page backgrounds/decorative elements** - Converted from PDF pages
2. **Client branding** - Logos and brand elements
3. **Screenshots** - Dashboard screenshots, flow examples
4. **Visual aids** - Charts, diagrams, illustrations

## How to Add Images to Your Reports

### Option 1: Add to Data Preparation

In your preparer functions, you can add image paths/URLs:

```python
# In api/services/report/preparers/kav_preparer.py
async def prepare_kav_data(...):
    # ... existing code ...
    
    return {
        # ... existing data ...
        "chart_screenshot": "assets/screenshots/kav_chart.png",  # Will be auto-embedded
        "dashboard_image": "https://example.com/dashboard.png",  # Will be downloaded and embedded
    }
```

### Option 2: Add to Templates Directly

```jinja2
{# In templates/sections/kav_analysis.html #}
<div class="visual-aid">
    {{ 'assets/kav_explanation.png' | embed_image('KAV Explanation', 'explanation-image') }}
</div>
```

### Option 3: Pass Images in Context

```python
# In api/services/report/__init__.py
context = {
    # ... existing context ...
    "section_images": {
        "kav_screenshot": "path/to/kav_screenshot.png",
        "dashboard_view": "https://klaviyo.com/dashboard.png",
    }
}
```

Then in template:
```jinja2
{% if section_images.kav_screenshot %}
    {{ section_images.kav_screenshot | embed_image('KAV Dashboard', 'dashboard-img') }}
{% endif %}
```

## Common Use Cases

### 1. Client Logo
```python
# In report generation
context = {
    "client_logo_path": f"assets/logos/{client_slug}.png",
    # or
    "client_logo_url": "https://example.com/logo.png",
}
```

### 2. Section Screenshots
```python
# Add to section data
kav_data = {
    # ... existing data ...
    "screenshots": {
        "revenue_dashboard": "screenshots/revenue_dashboard.png",
        "attribution_view": "screenshots/attribution.png",
    }
}
```

### 3. Flow Visualizations
```python
# In flow preparers
flow_data = {
    # ... existing data ...
    "flow_diagram": "assets/flow_diagrams/abandoned_cart.png",
}
```

## Image Optimization Tips

1. **Compress images** before embedding (use tools like TinyPNG)
2. **Use appropriate formats**: PNG for logos, JPEG for photos
3. **Resize large images** to reasonable dimensions (e.g., 1200px width max)
4. **Consider file size**: Base64 increases size by ~33%, so optimize source images

## Testing

To test image embedding:

```python
from api.services.report.image_handler import ImageEmbedder

# Test file encoding
data_uri = ImageEmbedder.encode_file_to_base64("test_image.png")
print(f"Encoded: {data_uri[:50]}...")

# Test URL encoding
data_uri = ImageEmbedder.encode_url_to_base64("https://example.com/image.png")

# Test HTML generation
html = ImageEmbedder.embed_image("test.png", "Test", "test-class")
print(html)
```

