/**
 * StyleManager - Handles CSS injection and style management for report viewer
 */
class StyleManager {
  constructor() {
    this.injectedStyles = new Set();
  }

  /**
   * Extract and inject styles from report HTML
   * @param {Document} doc - Parsed HTML document
   * @param {string} htmlString - Original HTML string (for fallback extraction)
   */
  injectReportStyles(doc, htmlString = null) {
    console.log('📝 Starting report style injection...');

    let cssContent = '';
    let extractionMethod = 'none';

    // Method 1: Try DOM parsing from document
    let styleTags = doc.querySelectorAll('style');

    if (styleTags.length > 0) {
      console.log(`✓ Found ${styleTags.length} style tags via DOM parsing`);
      styleTags.forEach(style => {
        cssContent += style.textContent + '\n';
      });
      extractionMethod = 'DOM parsing';
    }

    // Method 2: If no styles in DOM or very little, try HTML string extraction
    if ((cssContent.length < 1000 || styleTags.length === 0) && htmlString) {
      console.log('⚠️ DOM extraction yielded minimal styles, trying HTML string extraction...');

      const styleRegex = /<style[^>]*>([\s\S]*?)<\/style>/gi;
      const matches = [...htmlString.matchAll(styleRegex)];

      if (matches.length > 0) {
        console.log(`✓ Found ${matches.length} style blocks via regex extraction`);
        let regexCss = '';
        matches.forEach(match => {
          regexCss += match[1] + '\n';
        });

        // Use whichever is longer
        if (regexCss.length > cssContent.length) {
          cssContent = regexCss;
          extractionMethod = 'regex extraction';
        }
      }
    }

    // Method 3: Check for linked stylesheets in the document
    const linkTags = doc.querySelectorAll('link[rel="stylesheet"]');
    if (linkTags.length > 0) {
      console.log(`ℹ️ Found ${linkTags.length} linked stylesheets (will be loaded separately)`);
      linkTags.forEach(link => {
        const href = link.getAttribute('href');
        console.log(`  - ${href}`);
      });
    }

    // If still no styles, load fallback
    if (cssContent.trim().length === 0) {
      console.warn('⚠️ No embedded styles found in report - loading fallback styles');
      this.injectBasicAuditStyles();
      this.loadFallbackStyles();
      return;
    }

    // Process and inject the extracted CSS
    console.log(`✓ Extracted ${cssContent.length} characters of CSS via ${extractionMethod}`);

    // Remove existing injected styles
    const existingStylesId = 'injected-report-styles';
    let existingStyles = document.getElementById(existingStylesId);
    if (existingStyles) {
      existingStyles.remove();
      console.log('♻️ Removed previous injected styles');
    }

    // Clean up conflicting styles
    cssContent = this.removeConflictingStyles(cssContent);
    console.log(`✓ Cleaned CSS (${cssContent.length} chars after cleanup)`);

    // Create and inject style element
    const combinedStyle = document.createElement('style');
    combinedStyle.id = existingStylesId;
    combinedStyle.textContent = cssContent;
    document.head.appendChild(combinedStyle);

    console.log(`✅ Successfully injected report styles (${extractionMethod})`);
  }

  /**
   * Load fallback styles from external sources
   */
  async loadFallbackStyles() {
    try {
      const stylePaths = [
        '/templates/assets/styles.css',  // FastAPI route
        '/ui/templates/assets/styles.css',
        '/api/static/styles.css',
        '../templates/assets/styles.css',
        'templates/assets/styles.css'
      ];

      let cssContent = '';
      let loaded = false;

      for (const path of stylePaths) {
        try {
          const response = await fetch(path);
          if (response.ok) {
            cssContent = await response.text();
            loaded = true;
            console.log(`✓ Loaded styles from ${path}`);
            break;
          }
        } catch (e) {
          console.warn(`Failed to load styles from ${path}:`, e.message);
        }
      }

      if (loaded && cssContent) {
        const existingStylesId = 'fallback-report-styles';
        let existingStyles = document.getElementById(existingStylesId);
        if (existingStyles) {
          existingStyles.remove();
        }

        const styleEl = document.createElement('style');
        styleEl.id = existingStylesId;
        styleEl.textContent = this.scopeStylesToPageContent(cssContent);
        document.head.appendChild(styleEl);

        console.log(`✓ Loaded fallback audit template styles (${cssContent.length} chars)`);
      } else {
        console.warn('Failed to load fallback styles - no valid path found');
        this.injectBasicAuditStyles();
      }
    } catch (error) {
      console.error('Error loading fallback styles:', error);
      this.injectBasicAuditStyles();
    }
  }

  /**
   * Inject basic embedded audit styles
   */
  injectBasicAuditStyles() {
    const existingStylesId = 'basic-audit-styles';
    let existingStyles = document.getElementById(existingStylesId);
    if (existingStyles) {
      existingStyles.remove();
    }

    const basicStyles = `
      /* Basic Audit Styles - Embedded Fallback */
      .page-content {
        font-family: 'Montserrat', sans-serif;
        color: #262626;
        line-height: 1.6;
      }
      
      .page-content h1 {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2.5rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #262626;
        margin: 1rem 0;
      }
      
      .page-content h2 {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        color: #262626;
        margin: 1.5rem 0 1rem 0;
      }
      
      .page-content h3 {
        font-family: 'Montserrat', sans-serif;
        font-weight: 700;
        font-size: 1.2rem;
        color: #262626;
        margin: 1rem 0 0.5rem 0;
      }
      
      .page-content table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        background: white;
      }
      
      .page-content table th {
        background: #65DA4F;
        color: white;
        padding: 12px;
        text-align: left;
        font-weight: 600;
        border: 1px solid #ddd;
      }
      
      .page-content table td {
        padding: 10px 12px;
        border: 1px solid #ddd;
        vertical-align: top;
      }
      
      .page-content table tr:nth-child(even) {
        background: #f8f9fa;
      }
      
      .page-content .metric-card,
      .page-content .stat-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      }
      
      .page-content .metric-value,
      .page-content .stat-value {
        font-size: 2rem;
        font-weight: 700;
        color: #65DA4F;
        margin: 0.5rem 0;
      }
      
      .page-content .recommendation-card {
        background: #f8fff4;
        border: 1px solid #65DA4F;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
      }
      
      .page-content .cover-page {
        background: linear-gradient(to bottom, #000000 0%, #000000 70%, #001a00 100%);
        color: white;
        text-align: center;
        padding: 3rem;
        min-height: 80vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
      }
      
      .page-content .cover-page h1 {
        color: white;
        font-size: 3rem;
        margin: 1rem 0;
      }
      
      .page-content .section {
        background: white;
        padding: 2rem;
        margin: 1rem 0;
      }
      
      .page-content .green-text {
        color: #65DA4F;
      }
      
      .page-content .highlight {
        background: #65DA4F;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
      }
    `;

    const styleEl = document.createElement('style');
    styleEl.id = existingStylesId;
    styleEl.textContent = basicStyles;
    document.head.appendChild(styleEl);

    console.log('✓ Injected basic audit styles as fallback');
  }

  /**
   * Remove styles that conflict with viewer layout
   */
  removeConflictingStyles(css) {
    // Remove rules that break the viewer layout
    const conflicts = [
      /body\s*\{[^}]*height[^}]*\}/gi,
      /html\s*\{[^}]*height[^}]*\}/gi,
      /\.page-content\s*\{[^}]*min-height:\s*calc\(100vh[^}]*\}/gi,
      /\.page-content\s*\{[^}]*height:\s*100vh[^}]*\}/gi,
      /\.section\s*\{[^}]*min-height:\s*calc\(100vh[^}]*\}/gi,
    ];

    let cleaned = css;
    conflicts.forEach(pattern => {
      cleaned = cleaned.replace(pattern, '');
    });

    return cleaned;
  }

  /**
   * Scope CSS styles to page content (currently disabled)
   */
  scopeStylesToPageContent(css) {
    // Don't scope - just return CSS as-is
    // The report styles should work globally within the page container
    return css;
  }
}

// Export for use
window.StyleManager = StyleManager;