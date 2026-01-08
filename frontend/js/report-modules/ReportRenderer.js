/**
 * ReportRenderer - Handles content loading, section parsing, and page generation
 * Updated: 2026-01-06 - Fixed syntax errors and protected sections
 */
class ReportRenderer {
  constructor() {
    this.sections = [];
    this.totalPages = 0;
    this.styleManager = new StyleManager();

    // Splitting thresholds - Much more conservative to prevent over-splitting
    this.SPLIT_TEXT_THRESHOLD = 8000;  // Greatly increased to prevent unnecessary splits
    this.SPLIT_ELEMENT_THRESHOLD = 100;  // Greatly increased 
    this.maxCharsPerPage = 6000;  // Allow much larger pages
  }

  /**
   * Load and render report content
   */
  async loadReportContent(reportId) {
    if (!reportId) {
      throw new Error('No report ID provided');
    }

    try {
      const apiUrl = window.API_BASE_URL || '';
      console.log('Making request to:', `${apiUrl}/api/audit/status/${reportId}`);
      const response = await fetch(`${apiUrl}/api/audit/status/${reportId}`);
      console.log('Response status:', response.status, response.statusText);
      if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unknown error');
        console.error('Failed to load report. Response:', errorText);
        throw new Error(`Failed to load report: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();

      if (data.html_content) {
        return this.renderReportContent(data.html_content, data.report_data);
      } else {
        throw new Error('Report content not available. Please wait for generation to complete.');
      }
    } catch (error) {
      console.error('Error loading report content:', error);
      throw error;
    }
  }

  /**
   * Render HTML content into paginated sections
   */
  renderReportContent(htmlContent, reportData = null) {
    if (!htmlContent) {
      throw new Error('No HTML content provided');
    }

    const pageContainer = document.getElementById('page-container');
    if (!pageContainer) {
      throw new Error('Page container not found');
    }

    // Parse HTML content
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlContent, 'text/html');

    // 1. Extract and inject embedded styles from the report
    // Pass both the parsed doc and original HTML string for style extraction
    this.styleManager.injectReportStyles(doc, htmlContent);

    // 2. Find all sections - prioritize semantic IDs from data-section
    // Try multiple selectors to find sections
    let sections = Array.from(doc.querySelectorAll('section[data-section]'));

    // If no sections with data-section, try other patterns
    if (sections.length === 0) {
      sections = Array.from(doc.querySelectorAll('[data-section]'));
    }

    // Fallback to class-based selectors
    if (sections.length === 0) {
      sections = Array.from(doc.querySelectorAll('.section.page, section.page, .cover-page'));
    }

    if (sections.length === 0) {
      sections = Array.from(doc.querySelectorAll('.section, section[data-page], [data-page]'));
    }

    // Also try finding sections by ID pattern (kav_analysis, executive_summary, etc.)
    if (sections.length === 0) {
      const semanticIds = ['kav_analysis', 'executive_summary', 'list_growth', 'data_capture',
        'automation_overview', 'campaign_performance', 'strategic_recommendations'];
      semanticIds.forEach(id => {
        const el = doc.getElementById(id) || doc.querySelector(`[data-section="${id}"]`);
        if (el) sections.push(el);
      });
    }

    console.log(`Found ${sections.length} sections in report content`);

    // Log section IDs for debugging
    if (sections.length > 0) {
      const sectionInfo = sections.slice(0, 5).map(s => ({
        dataSection: s.getAttribute('data-section'),
        id: s.id,
        className: s.className,
        title: s.querySelector('h1, h2, .section-title')?.textContent?.substring(0, 50) || 'no-title'
      }));
      console.log(`First 5 sections info:`, sectionInfo);
    }

    if (sections.length === 0) {
      return this.renderFallbackContent(doc.body.innerHTML, pageContainer);
    }

    // 3. Extract and preserve semantic section IDs before sorting
    // Map generic IDs to semantic IDs by checking content/titles
    this.mapSemanticIds(sections, doc);

    // 4. Sort sections by logical order
    sections.sort((a, b) => this.compareSections(a, b));

    // 4. Clear existing content and render pages
    pageContainer.innerHTML = '';
    this.sections = [];

    // 5. Create pages from sections with intelligent splitting and quality filtering
    let pageNumber = 1;
    let skippedSections = 0;
    const processedSectionIds = new Set(); // Track processed sections to prevent duplicates

    sections.forEach((section) => {
      if (section.classList.contains('page-break')) {
        return;
      }

      // Get section ID - prioritize data-section attribute (should have semantic ID after mapping)
      let sectionId = section.getAttribute('data-section');

      // If no data-section or it's generic, try ID attribute
      if (!sectionId || sectionId.match(/^section-\d+$/)) {
        sectionId = section.id;
      }

      // If still generic or missing, generate one (but log it for debugging)
      if (!sectionId || sectionId.match(/^section-\d+$/)) {
        const originalId = sectionId;
        sectionId = `section-${pageNumber + skippedSections}`;
        if (originalId !== sectionId) {
          console.warn(`⚠️ Section ${pageNumber} has generic ID "${originalId || 'none'}", using "${sectionId}"`);
        }
      }

      // Check for duplicate sections  
      if (processedSectionIds.has(sectionId)) {
        console.warn(`⚠️ Skipping duplicate section: ${sectionId}`);
        skippedSections++;
        return;
      }
      processedSectionIds.add(sectionId);

      // Log semantic IDs for debugging
      if (sectionId && !sectionId.match(/^section-\d+$/)) {
        console.log(`✓ Found semantic section ID: ${sectionId}`);
      }

      const sectionTitle = section.querySelector('h1, h2, .section-title, [class*="title"]');
      const baseTitle = sectionTitle ? sectionTitle.textContent.trim() : this.formatSectionId(sectionId);

      // Check if section should be split into multiple pages
      const subPages = this.splitSectionIntoPages(section, sectionId, baseTitle);

      // Skip sections that returned empty (low quality content)
      if (subPages.length === 0) {
        skippedSections++;
        console.log(`⚠️ Skipped low-quality section: ${sectionId}`);
        return;
      }

      subPages.forEach((subPage, subIndex) => {
        const pageEl = this.createPageElement(pageNumber, sectionId, subPage, subIndex, subPages.length, baseTitle);
        pageContainer.appendChild(pageEl);

        // Track section info
        this.sections.push({
          pageNumber,
          sectionId,
          title: pageEl.dataset.sectionTitle,
          subPage: subIndex + 1,
          totalSubPages: subPages.length,
          baseTitle,
          hasContent: true // Mark as having actual content
        });

        pageNumber++;
      });
    });

    // 6. Update totals and UI
    this.totalPages = Math.max(1, pageNumber - 1);

    // Remove loading page
    const loadingPage = document.getElementById('page-loading');
    if (loadingPage && pageContainer.contains(loadingPage)) {
      pageContainer.removeChild(loadingPage);
    }

    // Update section information for chat system
    this.updateChatSectionInfo();

    console.log(`✓ Rendered ${this.totalPages} pages from ${sections.length} original sections (${skippedSections} low-quality sections skipped)`);
    console.log(`✓ Final result: ${this.sections.length} quality sections with actual content`);

    return {
      totalPages: this.totalPages,
      sections: this.sections
    };
  }

  /**
   * Create page element from sub-page data
   */
  createPageElement(pageNumber, sectionId, subPage, subIndex, totalSubPages, baseTitle) {
    const pageEl = document.createElement('div');
    pageEl.className = 'report-page';
    pageEl.id = `page-${pageNumber}`;
    pageEl.dataset.page = pageNumber;
    pageEl.dataset.sectionId = sectionId;
    pageEl.dataset.subPage = subIndex + 1;
    pageEl.dataset.totalSubPages = totalSubPages;

    if (pageNumber === 1) {
      pageEl.classList.add('active');
    }

    // Create page title with sub-page indicator if needed
    let pageTitle = baseTitle;
    if (totalSubPages > 1) {
      if (subPage.title) {
        pageTitle = `${baseTitle} - ${subPage.title}`;
      } else {
        pageTitle = `${baseTitle} (${subIndex + 1}/${totalSubPages})`;
      }
    }
    pageEl.dataset.sectionTitle = pageTitle;

    // Create page content
    const pageContent = document.createElement('div');
    pageContent.className = 'page-content';
    pageContent.innerHTML = subPage.content;

    pageEl.appendChild(pageContent);
    return pageEl;
  }

  /**
   * Split large sections into multiple pages
   */
  splitSectionIntoPages(section, sectionId, baseTitle) {
    const sectionClone = section.cloneNode(true);
    const sectionHTML = sectionClone.outerHTML;

    const textLength = sectionClone.textContent.trim().length;
    const elementCount = sectionClone.querySelectorAll('*').length;

    console.log(`Section "${sectionId}": ${textLength} chars, ${elementCount} elements - Will split: ${textLength >= this.SPLIT_TEXT_THRESHOLD || elementCount >= this.SPLIT_ELEMENT_THRESHOLD}`);

    // Warn about sections with minimal content but don't skip them
    if (textLength < 100) {
      console.warn(`⚠️ Section "${sectionId}" has minimal content (${textLength} chars) - keeping for review`);
      // Don't skip - render as-is for visibility
      return [{ content: sectionHTML, title: null }];
    }

    // For very short sections, check quality but still preserve
    if (textLength < 300 && elementCount < 5) {
      const contentText = sectionClone.textContent.trim().toLowerCase();
      if (contentText.includes('loading') || contentText.includes('generated on invalid date') || contentText.length < 50) {
        console.warn(`⚠️ Section "${sectionId}" appears to be placeholder content: "${contentText.substring(0, 100)}..." - keeping for review`);
        // Keep it visible so issues can be identified
        return [{ content: sectionHTML, title: null }];
      }
    }

    // Don't split small sections or special pages
    if (textLength < this.SPLIT_TEXT_THRESHOLD && elementCount < this.SPLIT_ELEMENT_THRESHOLD) {
      return [{ content: sectionHTML, title: null }];
    }

    // Don't split key sections that should remain intact - ALWAYS return whole section
    const protectedSections = [
      'cover', 'executive_summary', 'kav_analysis', 'why_andzen', 
      'table_of_contents', 'strategic_recommendations', 'next_steps'
    ];
    
    if (protectedSections.some(protectedSection => sectionId.toLowerCase().includes(protectedSection))) {
      console.log(`🔒 Protected section "${sectionId}" - preventing split`);
      return [{ content: sectionHTML, title: null }];
    }

    // Try to find natural break points
    const breakPoints = this.findSectionBreakPoints(sectionClone);

    if (breakPoints.length <= 1) {
      return this.splitByContentBlocks(sectionHTML, baseTitle, sectionId);
    }

    // Split at break points
    const subPages = [];
    breakPoints.forEach((breakPoint) => {
      if (breakPoint.content.trim()) {
        subPages.push({
          content: this.wrapContentInSection(breakPoint.content, sectionId),
          title: breakPoint.title
        });
      }
    });

    if (subPages.length === 0) {
      return [{ content: sectionHTML, title: null }];
    }

    console.log(`Split section "${sectionId}" into ${subPages.length} pages`);
    return subPages;
  }

  /**
   * Find natural break points in section
   */
  findSectionBreakPoints(sectionElement) {
    const breakPoints = [];

    // Look for major headers as break points (only h2, not h3)
    const headers = sectionElement.querySelectorAll('h2');

    if (headers.length === 0) {
      // No headers - try major elements
      const majorElements = sectionElement.querySelectorAll('table, .metric-card, .recommendation-card, .flow-card, .chart-container');

      if (majorElements.length > 8) {  // Much more conservative - only split if LOTS of elements
        let elementGroups = [];
        let currentGroup = [];

        Array.from(sectionElement.children).forEach(child => {
          currentGroup.push(child);
          if (currentGroup.length >= 6 || (child.tagName === 'TABLE' && currentGroup.length >= 2)) {  // Larger groups
            elementGroups.push(currentGroup);
            currentGroup = [];
          }
        });

        if (currentGroup.length > 0) {
          elementGroups.push(currentGroup);
        }

        elementGroups.forEach((group, index) => {
          const groupHtml = group.map(el => el.outerHTML).join('\n');
          breakPoints.push({
            content: groupHtml,
            title: `Part ${index + 1}`
          });
        });
      }

      return breakPoints;
    }

    // Split by headers
    let contentBefore = '';

    // Get content before first header
    const firstHeader = headers[0];
    let walker = document.createTreeWalker(
      sectionElement,
      NodeFilter.SHOW_ELEMENT,
      null,
      false
    );

    let node;
    while (node = walker.nextNode()) {
      if (node === firstHeader) break;
      if (node.parentNode === sectionElement) {
        contentBefore += node.outerHTML;
      }
    }

    if (contentBefore.trim()) {
      breakPoints.push({
        content: contentBefore,
        title: 'Overview'
      });
    }

    // Process each header and its content
    headers.forEach((header, index) => {
      const headerText = header.textContent.trim();
      let sectionContent = header.outerHTML;

      // Get content until next header
      let nextSibling = header.nextElementSibling;
      const nextHeader = headers[index + 1];

      while (nextSibling && nextSibling !== nextHeader) {
        sectionContent += nextSibling.outerHTML;
        nextSibling = nextSibling.nextElementSibling;
      }

      if (sectionContent.trim()) {
        breakPoints.push({
          content: sectionContent,
          title: headerText
        });
      }
    });

    return breakPoints;
  }

  /**
   * Split content by size when no natural breaks found
   */
  splitByContentBlocks(sectionHTML, baseTitle, sectionId) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(sectionHTML, 'text/html');
    const sectionEl = doc.body.firstElementChild;

    if (!sectionEl) {
      return [{ content: sectionHTML, title: null }];
    }

    const children = Array.from(sectionEl.children);
    const pages = [];
    let currentPageContent = [];
    let currentCharCount = 0;

    children.forEach(child => {
      const childText = child.textContent.length;

      // Much more conservative splitting - only if we have a LOT of content AND multiple elements
      if (currentCharCount + childText > this.maxCharsPerPage && 
          currentPageContent.length > 3 &&  // Require at least 4 elements before considering a split
          currentCharCount > this.maxCharsPerPage * 0.8) {  // And we're substantially over the limit
        pages.push({
          content: this.wrapContentInSection(
            currentPageContent.map(el => el.outerHTML).join('\n'),
            sectionId
          ),
          title: `Part ${pages.length + 1}`
        });
        currentPageContent = [child];
        currentCharCount = childText;
      } else {
        currentPageContent.push(child);
        currentCharCount += childText;
      }
    });

    // Add final page
    if (currentPageContent.length > 0) {
      pages.push({
        content: this.wrapContentInSection(
          currentPageContent.map(el => el.outerHTML).join('\n'),
          sectionId
        ),
        title: pages.length > 0 ? `Part ${pages.length + 1}` : null
      });
    }

    return pages.length > 0 ? pages : [{ content: sectionHTML, title: null }];
  }

  /**
   * Wrap content in proper section structure
   */
  wrapContentInSection(content, sectionId) {
    const knownSections = {
      'executive_summary': 'executive-summary',
      'kav_analysis': 'kav-analysis',
      'strategic_recommendations': 'strategic-recommendations',
      'campaign_performance': 'campaign-performance',
      'automation_overview': 'automation-overview',
      'list_growth': 'list-growth',
      'data_capture': 'data-capture',
      'flow_welcome': 'flow-welcome',
      'flow_abandoned_cart': 'flow-abandoned-cart',
      'segmentation_strategy': 'segmentation-strategy'
    };

    const sectionClass = sectionId.toLowerCase().replace(/_/g, '-');
    const backendId = knownSections[sectionId] || sectionId;

    return `<section 
      data-section="${sectionId}" 
      data-backend-section="${backendId}"
      id="${sectionClass}-section" 
      class="section page-section">
      ${content}
    </section>`;
  }

  /**
   * Map generic section IDs to semantic IDs by analyzing content
   */
  mapSemanticIds(sections, doc) {
    // Semantic ID patterns based on content analysis
    const semanticPatterns = {
      'kav_analysis': ['kav', 'klaviyo attributed value', 'attributed revenue', 'kav percentage', 'your klaviyo'],
      'executive_summary': ['executive summary', 'summary', 'overview', 'executive'],
      'strategic_recommendations': ['strategic recommendations', 'recommendations', 'next steps', 'strategic'],
      'list_growth': ['list growth', 'subscriber growth', 'list size', 'growth'],
      'data_capture': ['data capture', 'forms', 'signup forms', 'form performance'],
      'automation_overview': ['automation', 'flows overview', 'active flows', 'overall automation'],
      'campaign_performance': ['campaign performance', 'campaigns', 'email campaigns', 'campaign'],
      'segmentation_strategy': ['segmentation', 'segments', 'audience', 'segmentation strategy'],
      'flow_welcome': ['welcome', 'welcome series', 'welcome flow'],
      'flow_abandoned_cart': ['abandoned cart', 'cart abandonment', 'abandoned checkout'],
      'flow_browse_abandonment': ['browse abandonment', 'browse', 'browse abandonment flow'],
      'flow_post_purchase': ['post purchase', 'post-purchase', 'post purchase flow'],
      'cover': ['cover', 'title page', 'customer journey marketing'],
      'why_andzen': ['why andzen', 'about andzen', 'andzen'],
      'table_of_contents': ['table of contents', 'contents', 'toc']
    };

    let mappedCount = 0;

    sections.forEach((section) => {
      const currentId = section.getAttribute('data-section') || section.id || '';

      // If already has semantic ID, keep it
      if (currentId && !currentId.match(/^section-\d+$/)) {
        return;
      }

      // Try to find semantic ID by content
      const sectionText = section.textContent.toLowerCase();
      const sectionTitle = section.querySelector('h1, h2, h3, .section-title')?.textContent.toLowerCase() || '';
      const combinedText = (sectionText.substring(0, 500) + ' ' + sectionTitle).toLowerCase();

      // Also check for data-section in child elements (in case it's nested)
      const nestedDataSection = section.querySelector('[data-section]');
      if (nestedDataSection) {
        const nestedId = nestedDataSection.getAttribute('data-section');
        if (nestedId && !nestedId.match(/^section-\d+$/)) {
          section.setAttribute('data-section', nestedId);
          if (!section.id || section.id.match(/^section-\d+$/)) {
            section.id = nestedId;
          }
          mappedCount++;
          console.log(`✓ Mapped ${currentId} → ${nestedId} (from nested element)`);
          return;
        }
      }

      // Try pattern matching
      for (const [semanticId, patterns] of Object.entries(semanticPatterns)) {
        for (const pattern of patterns) {
          if (combinedText.includes(pattern)) {
            // Set semantic ID
            section.setAttribute('data-section', semanticId);
            if (!section.id || section.id.match(/^section-\d+$/)) {
              section.id = semanticId;
            }
            mappedCount++;
            console.log(`✓ Mapped ${currentId || 'unnamed'} → ${semanticId} (matched: "${pattern}")`);
            return; // Found a match, move to next section
          }
        }
      }
    });

    console.log(`✓ Semantic ID mapping complete: ${mappedCount} sections mapped`);
  }

  /**
   * Compare sections for sorting
   */
  compareSections(a, b) {
    const pageA = a.getAttribute('data-page') || a.dataset.page || a.getAttribute('data-section') || '999';
    const pageB = b.getAttribute('data-page') || b.dataset.page || b.getAttribute('data-section') || '999';

    const numA = parseInt(pageA);
    const numB = parseInt(pageB);

    if (!isNaN(numA) && !isNaN(numB)) {
      return numA - numB;
    }

    const sectionOrder = {
      'cover': 1, 'cover-page': 1, '1': 1,
      'why_andzen': 2, 'why-andzen': 2, 'andzen': 2,
      'table_of_contents': 3, 'toc': 3,
      'executive_summary': 4, 'executive-summary': 4, 'summary': 4,
      'list_growth': 5, 'list-growth': 5, 'growth': 5,
      'data_capture': 6, 'data-capture': 6, 'capture': 6,
      'automation_overview': 7, 'automation-overview': 7, 'automation': 7,
      'flow_welcome': 8, 'flow-welcome': 8, 'welcome': 8,
      'flow_abandoned_cart': 9, 'flow-abandoned-cart': 9, 'abandoned_cart': 9, 'abandoned-cart': 9,
      'flow_browse_abandonment': 10, 'flow-browse-abandonment': 10, 'browse_abandonment': 10, 'browse-abandonment': 10,
      'flow_post_purchase': 11, 'flow-post-purchase': 11, 'post_purchase': 11, 'post-purchase': 11,
      'advanced_reviews': 12, 'advanced-reviews': 12, 'reviews': 12,
      'advanced_wishlist': 13, 'advanced-wishlist': 13, 'wishlist': 13,
      'kav_analysis': 14, 'kav-analysis': 14, 'kav': 14,
      'campaign_performance': 15, 'campaign-performance': 15, 'campaigns': 15,
      'segmentation_strategy': 16, 'segmentation-strategy': 16, 'segmentation': 16,
      'strategic_recommendations': 17, 'strategic-recommendations': 17, 'recommendations': 17, 'strategic': 17,
      'next_steps': 18, 'next-steps': 18
    };

    const getSectionOrder = (pageId) => {
      const id = pageId.toLowerCase();

      if (sectionOrder[id] !== undefined) {
        return sectionOrder[id];
      }

      for (const [key, order] of Object.entries(sectionOrder)) {
        if (id.includes(key.replace(/_/g, '-')) || id.includes(key.replace(/-/g, '_'))) {
          return order;
        }
      }

      return 999;
    };

    const orderA = getSectionOrder(pageA);
    const orderB = getSectionOrder(pageB);

    return orderA - orderB;
  }

  /**
   * Render fallback content when no sections found
   */
  renderFallbackContent(htmlContent, container) {
    const pageEl = document.createElement('div');
    pageEl.className = 'report-page active';
    pageEl.id = 'page-1';
    pageEl.dataset.page = 1;

    const pageContent = document.createElement('div');
    pageContent.className = 'page-content';
    pageContent.innerHTML = htmlContent;

    pageEl.appendChild(pageContent);
    container.innerHTML = '';
    container.appendChild(pageEl);

    this.totalPages = 1;
    this.sections = [{ pageNumber: 1, sectionId: 'content', title: 'Report Content' }];
  }

  /**
   * Format section ID to readable title
   */
  formatSectionId(sectionId) {
    return sectionId
      .replace(/_/g, ' ')
      .replace(/-/g, ' ')
      .replace(/\b\w/g, c => c.toUpperCase());
  }

  /**
   * Update chat system with section information
   */
  updateChatSectionInfo() {
    const sectionMap = {};
    const sectionContent = {};
    const fullReportContent = [];

    this.sections.forEach(section => {
      const baseId = section.sectionId;
      if (!sectionMap[baseId]) {
        sectionMap[baseId] = [];
        sectionContent[baseId] = '';
      }
      sectionMap[baseId].push({
        pageNumber: section.pageNumber,
        title: section.title,
        subPage: section.subPage || 1,
        totalSubPages: section.totalSubPages || 1
      });

      const pageEl = document.getElementById(`page-${section.pageNumber}`);
      if (pageEl) {
        const pageContent = pageEl.textContent + '\n';
        sectionContent[baseId] += pageContent;

        // Also add to full report content with page context
        fullReportContent.push({
          pageNumber: section.pageNumber,
          sectionId: baseId,
          title: section.title,
          content: pageContent.trim()
        });
      }
    });

    window.reportSections = {
      map: sectionMap,
      content: sectionContent,
      fullContent: fullReportContent, // Complete report content for chat context
      available: Object.keys(sectionMap),

      // Enhanced section finder with better mapping
      findSection: (sectionName) => {
        const normalizedName = sectionName.toLowerCase()
          .replace(/\s+/g, '_')
          .replace(/-/g, '_');

        if (sectionContent[normalizedName]) {
          return sectionContent[normalizedName];
        }

        // Check partial matches
        for (const [id, content] of Object.entries(sectionContent)) {
          if (id.includes(normalizedName) || normalizedName.includes(id)) {
            return content;
          }
        }

        // Enhanced mappings for better section detection
        const mappings = {
          'kav': ['kav_analysis', 'section-14', 'section-19'],
          'executive': ['executive_summary', 'summary', 'section-4'],
          'summary': ['executive_summary', 'section-4'],
          'strategic': ['strategic_recommendations', 'recommendations', 'section-62'],
          'recommendations': ['strategic_recommendations', 'section-62'],
          'campaigns': ['campaign_performance', 'section-26'],
          'automation': ['automation_overview', 'flows', 'section-11'],
          'flows': ['automation_overview', 'section-11'],
          'growth': ['list_growth', 'section-1'],
          'capture': ['data_capture', 'section-8'],
          'segmentation': ['segmentation_strategy', 'section-59'],
          'data': ['data_capture', 'section-8'],
          'form': ['data_capture', 'section-8']
        };

        const possibleIds = mappings[normalizedName];
        if (possibleIds) {
          for (const id of possibleIds) {
            if (sectionContent[id]) {
              return sectionContent[id];
            }
          }
        }

        return null;
      },

      // Get full report context for AI
      getFullContext: () => {
        return {
          totalPages: fullReportContent.length,
          sections: Object.keys(sectionMap),
          content: fullReportContent,
          summary: fullReportContent.map(item => ({
            page: item.pageNumber,
            section: item.sectionId,
            title: item.title,
            preview: item.content.substring(0, 200) + '...'
          }))
        };
      }
    };

    console.log('Available sections for chat:', Object.keys(sectionMap));
  }

  /**
   * Get current sections data
   */
  getSections() {
    return this.sections;
  }

  /**
   * Get total pages
   */
  getTotalPages() {
    return this.totalPages;
  }
}

// Export for use
window.ReportRenderer = ReportRenderer;