/**
 * Report Viewer - Page Navigation & Interactive Features
 */

class ReportViewer {
  constructor() {
    this.currentPage = 1;
    this.totalPages = 15;
    this.pages = [];
    this.reportId = null;
    this.chatHistory = [];
    this.quoteItems = [];
    this.init();
  }

  init() {
    // Get report ID from URL (try multiple param names)
    const urlParams = new URLSearchParams(window.location.search);
    this.reportId = parseInt(urlParams.get('reportId') || urlParams.get('report_id') || urlParams.get('id'));

    if (!this.reportId) {
      console.error('No report ID provided in URL');
      this.showError('No report ID provided. Please navigate from the dashboard.');
      return;
    }

    console.log(`Initializing report viewer for report ID: ${this.reportId}`);

    this.setupPageNavigation();
    this.setupChatInterface();
    this.setupQuoteBuilder();
    this.setupTabs();
    this.setupBackButton();
    this.setupExportButtons();
    this.setupEditMode(); // Add edit mode controls
    this.loadReportContent(); // This will also update sidebar and pagination
    this.loadChatHistory();

    // Keyboard navigation
    document.addEventListener('keydown', (e) => this.handleKeyboardNavigation(e));
  }

  setupBackButton() {
    const backBtn = document.querySelector('.btn-back');
    if (backBtn) {
      backBtn.addEventListener('click', () => {
        window.location.href = '/ui/';
      });
    }
  }

  setupExportButtons() {
    const pdfBtn = document.querySelector('.btn-export.pdf');
    const wordBtn = document.querySelector('.btn-export.word');
    const htmlBtn = document.querySelector('.btn-export.html');

    if (pdfBtn) {
      pdfBtn.addEventListener('click', () => this.exportReport('pdf'));
    }
    if (wordBtn) {
      wordBtn.addEventListener('click', () => this.exportReport('word'));
    }
    if (htmlBtn) {
      htmlBtn.addEventListener('click', () => this.exportReport('html'));
    }
  }

  async exportReport(format) {
    if (!this.reportId) return;

    try {
      const response = await fetch(`/api/audit/status/${this.reportId}`);
      if (!response.ok) throw new Error('Failed to get report info');

      const data = await response.json();
      let downloadUrl;

      if (format === 'pdf' && data.report_data?.pdf_url) {
        downloadUrl = data.report_data.pdf_url;
      } else if (format === 'word' && data.report_data?.word_url) {
        downloadUrl = data.report_data.word_url;
      } else if (format === 'html' && data.report_data?.html_url) {
        downloadUrl = data.report_data.html_url;
      }

      if (downloadUrl) {
        window.open(downloadUrl, '_blank');
      } else {
        this.showToast(`${format.toUpperCase()} export not available for this report`, 'warning');
      }
    } catch (error) {
      console.error('Export error:', error);
      this.showToast('Failed to export report', 'error');
    }
  }

  setupPageNavigation() {
    const prevBtn = document.querySelector('.btn-nav.prev');
    const nextBtn = document.querySelector('.btn-nav.next');

    if (prevBtn) {
      prevBtn.addEventListener('click', () => this.previousPage());
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', () => this.nextPage());
    }

    // Page swipe support for mobile
    this.setupSwipeNavigation();
  }

  setupSidebarNavigation() {
    // Use event delegation for dynamically created nav links
    const navContainer = document.querySelector('.section-nav');
    if (!navContainer) return;

    navContainer.addEventListener('click', (e) => {
      const link = e.target.closest('.nav-link');
      if (!link) return;

      e.preventDefault();

      // Get page number from data attribute or href
      let pageNumber = parseInt(link.dataset.page);
      if (!pageNumber) {
        const href = link.getAttribute('href');
        const match = href?.match(/page-(\d+)/);
        if (match) {
          pageNumber = parseInt(match[1]);
        }
      }

      if (pageNumber && pageNumber >= 1 && pageNumber <= this.totalPages) {
        this.goToPage(pageNumber);

        // Update active state
        navContainer.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        link.classList.add('active');
      }
    });
  }

  setupSwipeNavigation() {
    let touchStartX = null;
    let touchStartY = null;

    const pageContainer = document.getElementById('page-container');

    pageContainer.addEventListener('touchstart', (e) => {
      touchStartX = e.touches[0].clientX;
      touchStartY = e.touches[0].clientY;
    }, { passive: true });

    pageContainer.addEventListener('touchend', (e) => {
      if (!touchStartX || !touchStartY) return;

      const touchEndX = e.changedTouches[0].clientX;
      const touchEndY = e.changedTouches[0].clientY;

      const diffX = touchStartX - touchEndX;
      const diffY = touchStartY - touchEndY;

      // Only trigger if horizontal swipe is more significant than vertical
      if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
        if (diffX > 0) {
          this.nextPage(); // Swipe left - next page
        } else {
          this.previousPage(); // Swipe right - previous page
        }
      }

      touchStartX = null;
      touchStartY = null;
    }, { passive: true });
  }

  goToPage(pageNumber) {
    console.log(`Navigating to page ${pageNumber}/${this.totalPages}`);

    if (pageNumber < 1 || pageNumber > this.totalPages) {
      console.warn(`Invalid page number: ${pageNumber}. Valid range: 1-${this.totalPages}`);
      return;
    }

    // Hide current page
    const currentPageEl = document.querySelector('.report-page.active');
    if (currentPageEl) {
      console.log(`Hiding current page: ${currentPageEl.id}`);
      currentPageEl.classList.remove('active');
    }

    // Show new page
    const newPageEl = document.getElementById(`page-${pageNumber}`);
    if (newPageEl) {
      console.log(`Showing page: ${newPageEl.id}`);
      newPageEl.classList.add('active');
      this.currentPage = pageNumber;
    } else {
      console.warn(`Page element not found: page-${pageNumber}. Available pages:`,
        Array.from(document.querySelectorAll('.report-page')).map(p => p.id));
      // For debugging - let's not generate placeholder pages, just log the issue
      return;
    }

    this.updatePageIndicators();
    this.updateNavigationButtons();

    // Scroll to top after a brief delay to ensure DOM has updated
    setTimeout(() => {
      this.scrollPageToTop();
    }, 50);
  }

  generatePage(pageNumber) {
    const pageContainer = document.getElementById('page-container');

    // This would typically load content from your API
    // For demo, we'll create a placeholder page
    const pageEl = document.createElement('div');
    pageEl.className = 'report-page active';
    pageEl.id = `page-${pageNumber}`;
    pageEl.innerHTML = `
      <div class="page-content">
        <h1 class="page-title">Page ${pageNumber}</h1>
        <div class="page-placeholder">
          <p>This page content would be loaded dynamically from your audit data.</p>
          <p>Page ${pageNumber} content goes here...</p>
        </div>
      </div>
    `;

    // Remove any existing active page
    document.querySelectorAll('.report-page').forEach(page => {
      page.classList.remove('active');
    });

    pageContainer.appendChild(pageEl);
  }

  nextPage() {
    console.log(`Next page requested. Current: ${this.currentPage}, Total: ${this.totalPages}`);
    if (this.currentPage < this.totalPages) {
      this.goToPage(this.currentPage + 1);
    } else {
      console.log('Already on last page');
    }
  }

  previousPage() {
    console.log(`Previous page requested. Current: ${this.currentPage}, Total: ${this.totalPages}`);
    if (this.currentPage > 1) {
      this.goToPage(this.currentPage - 1);
    } else {
      console.log('Already on first page');
    }
  }

  updatePageIndicators() {
    const currentPageEl = document.querySelector('.current-page');
    const totalPagesEl = document.querySelector('.total-pages');

    if (currentPageEl) currentPageEl.textContent = this.currentPage;
    if (totalPagesEl) totalPagesEl.textContent = this.totalPages;
  }

  updateNavigationButtons() {
    const prevBtn = document.querySelector('.btn-nav.prev');
    const nextBtn = document.querySelector('.btn-nav.next');

    if (prevBtn) {
      prevBtn.disabled = this.currentPage === 1;
    }

    if (nextBtn) {
      nextBtn.disabled = this.currentPage === this.totalPages;
    }
  }

  updateActiveNavLink(activeLink) {
    document.querySelectorAll('.nav-link').forEach(link => {
      link.classList.remove('active');
    });

    if (activeLink) {
      activeLink.classList.add('active');
    } else {
      // Auto-select based on current page
      const navLinks = document.querySelectorAll('.nav-link');
      if (navLinks[this.currentPage - 1]) {
        navLinks[this.currentPage - 1].classList.add('active');
      }
    }
  }

  scrollPageToTop() {
    // Scroll the page container to top (smooth scroll)
    const pageContainer = document.getElementById('page-container');
    if (pageContainer) {
      pageContainer.scrollTo({ top: 0, behavior: 'smooth' });
    }
    // Also scroll the active page content to top
    const activePage = document.querySelector('.report-page.active');
    if (activePage) {
      activePage.scrollTo({ top: 0, behavior: 'smooth' });
    }
    // Scroll the report content area to top
    const reportContent = document.querySelector('.report-content');
    if (reportContent) {
      reportContent.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  handleKeyboardNavigation(e) {
    // Arrow key navigation
    if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      e.preventDefault();
      this.previousPage();
    } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      e.preventDefault();
      this.nextPage();
    }

    // Number key navigation (1-9)
    const pageNumber = parseInt(e.key);
    if (pageNumber >= 1 && pageNumber <= 9 && pageNumber <= this.totalPages) {
      this.goToPage(pageNumber);
    }
  }

  setupTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const targetTab = btn.dataset.tab;

        // Update tab buttons
        tabBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Update tab content
        tabContents.forEach(content => {
          content.classList.remove('active');
        });

        const targetContent = document.getElementById(`${targetTab}-content`);
        if (targetContent) {
          targetContent.classList.add('active');
        }
      });
    });
  }

  setupChatInterface() {
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.querySelector('.btn-send');
    const messagesContainer = document.getElementById('chat-messages');

    const sendMessage = async () => {
      const message = chatInput.value.trim();
      if (!message) return;

      this.addChatMessage('user', message);
      chatInput.value = '';

      // Disable input while processing
      if (chatInput) chatInput.disabled = true;
      if (sendBtn) sendBtn.disabled = true;

      try {
        await this.sendChatMessageToAPI(message);
      } catch (error) {
        console.error('Chat error:', error);
        this.addChatMessage('assistant', `Sorry, I encountered an error: ${error.message}`);
      } finally {
        if (chatInput) chatInput.disabled = false;
        if (sendBtn) sendBtn.disabled = false;
        if (chatInput) chatInput.focus();
      }
    };

    if (sendBtn) {
      sendBtn.addEventListener('click', sendMessage);
    }

    if (chatInput) {
      chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          sendMessage();
        }
      });
    }

    // Setup edit request buttons
    this.setupEditRequestButtons();
  }

  async sendChatMessageToAPI(message) {
    if (!this.reportId) {
      throw new Error('No report ID available');
    }

    const response = await fetch(`/api/audit/${this.reportId}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: message,
        report_id: this.reportId
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Chat request failed');
    }

    const data = await response.json();

    // Add assistant response
    const actions = `
      <button class="btn-edit-request">✏️ Request Edit</button>
      <button class="btn-add-quote">💼 Add to Quote</button>
    `;

    this.addChatMessage('assistant', data.response, actions);

    // Handle navigation actions if provided
    if (data.navigation_actions && data.navigation_actions.length > 0) {
      this.handleNavigationActions(data.navigation_actions);
    }
  }

  async loadChatHistory() {
    if (!this.reportId) return;

    try {
      const response = await fetch(`/api/audit/${this.reportId}/chat/history`);
      if (!response.ok) return;

      const data = await response.json();
      this.chatHistory = data.messages || [];

      // Display chat history
      const messagesContainer = document.getElementById('chat-messages');
      if (messagesContainer) {
        // Clear the initial placeholder message
        messagesContainer.innerHTML = '';

        // Only show welcome message if no history
        if (this.chatHistory.length === 0) {
          this.addChatMessage('assistant', 'Hi! I\'ve analyzed this client\'s Klaviyo data. Ask me anything about their email marketing performance, flows, campaigns, or strategic recommendations.');
        } else {
          // Show chat history
          this.chatHistory.forEach(msg => {
            const actions = msg.role === 'assistant' ? `
              <button class="btn-edit-request">✏️ Request Edit</button>
              <button class="btn-add-quote">💼 Add to Quote</button>
            ` : null;
            // addChatMessage will handle formatting via formatChatContent
            this.addChatMessage(msg.role, msg.message, actions);
          });
        }
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  }

  handleNavigationActions(actions) {
    actions.forEach(action => {
      if (action.type === 'scroll_to_section' && action.section_id) {
        this.scrollToSection(action.section_id);
      }
    });
  }

  async loadReportContent() {
    if (!this.reportId) return;

    const maxRetries = 3;
    let attempt = 0;

    while (attempt < maxRetries) {
      try {
        attempt++;

        if (attempt > 1) {
          console.log(`Retry attempt ${attempt}/${maxRetries}...`);
          this.showToast(`Retrying... (${attempt}/${maxRetries})`, 'info');
        }

        const response = await fetch(`/api/audit/status/${this.reportId}`);

        if (!response.ok) {
          const errorText = await response.text();
          let errorMessage = 'Failed to load report';

          try {
            const errorJson = JSON.parse(errorText);
            errorMessage = errorJson.detail || errorJson.message || errorMessage;
          } catch {
            errorMessage = `${errorMessage} (HTTP ${response.status})`;
          }

          // Don't retry on 404 - report doesn't exist
          if (response.status === 404) {
            this.showError('Report not found. Please check the report ID.');
            return;
          }

          // Don't retry on 4xx errors (client errors)
          if (response.status >= 400 && response.status < 500) {
            this.showError(errorMessage);
            return;
          }

          throw new Error(errorMessage);
        }

        const data = await response.json();

        // Update page title and header with report info
        if (data.report_data) {
          this.updateReportHeader(data.report_data);
        }

        if (data.html_content) {
          // Load report content into page container
          this.renderReportContent(data.html_content);
          return; // Success!
        } else if (data.status === 'generating' || data.status === 'pending') {
          this.showError(`Report is still generating. Status: ${data.status}. Please wait and refresh.`);
          return;
        } else {
          this.showError('Report content not available. Generation may have failed.');
          return;
        }
      } catch (error) {
        console.error(`Error loading report content (attempt ${attempt}/${maxRetries}):`, error);

        // If this was the last attempt, show error
        if (attempt >= maxRetries) {
          this.showError(`Failed to load report after ${maxRetries} attempts: ${error.message}`);
          return;
        }

        // Wait before retrying (exponential backoff: 1s, 2s, 4s)
        const delay = Math.pow(2, attempt - 1) * 1000;
        console.log(`Waiting ${delay}ms before retry...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  updateReportHeader(reportData) {
    // Update page title
    document.title = `${reportData.client_name || 'Report'} - Andzen Audit`;

    // Update sidebar header
    const reportTitle = document.querySelector('.report-title h1');
    const reportSubtitle = document.querySelector('.report-title p');

    if (reportTitle && reportData.client_name) {
      reportTitle.textContent = reportData.client_name;
    }

    if (reportSubtitle) {
      const industry = reportData.industry || 'E-commerce';
      const revenue = reportData.total_revenue
        ? `$${(reportData.total_revenue / 1000).toFixed(0)}K Revenue Analyzed`
        : 'Revenue Analyzed';
      
      // Add proper generation date with validation
      let dateString = '';
      if (reportData.created_at) {
        const generatedDate = new Date(reportData.created_at);
        console.log('Report created_at:', reportData.created_at, 'Parsed date:', generatedDate);
        
        if (isNaN(generatedDate.getTime())) {
          // Invalid date, use current date
          console.warn('Invalid created_at date, using current date');
          const currentDate = new Date();
          dateString = currentDate.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long', 
            day: 'numeric'
          });
        } else {
          dateString = generatedDate.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
          });
        }
      } else {
        // No created_at, use current date
        const currentDate = new Date();
        dateString = currentDate.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        });
      }
      
      reportSubtitle.textContent = `${industry} • ${revenue} • Generated on ${dateString}`;
    }
  }

  renderReportContent(htmlContent) {
    if (!htmlContent) {
      console.error('No HTML content provided');
      return;
    }

    const pageContainer = document.getElementById('page-container');
    if (!pageContainer) {
      console.error('Page container not found');
      return;
    }

    // Parse HTML content
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlContent, 'text/html');

    // 1. Extract and inject embedded styles from the report
    this.injectReportStyles(doc);

    // 2. Find all sections - use data-section attribute first
    let sections = Array.from(doc.querySelectorAll('section[data-section], [data-section]'));

    // Fallback to other selectors
    if (sections.length === 0) {
      sections = Array.from(doc.querySelectorAll('.section.page, section.page, .cover-page'));
    }

    // If still no sections, try finding main content areas
    if (sections.length === 0) {
      sections = Array.from(doc.querySelectorAll('.section, section[data-page], [data-page]'));
    }

    console.log(`Found ${sections.length} sections in report content`);

    if (sections.length === 0) {
      // Final fallback: create single scrollable page with all content
      this.renderFallbackContent(doc.body.innerHTML, pageContainer);
      return;
    }

    // Sort sections by data-page attribute and section order to maintain correct structure
    sections.sort((a, b) => {
      // Get page numbers and section identifiers
      const pageA = a.getAttribute('data-page') || a.dataset.page || a.getAttribute('data-section') || '999';
      const pageB = b.getAttribute('data-page') || b.dataset.page || b.getAttribute('data-section') || '999';

      // First try pure numeric comparison for explicit page numbers
      const numA = parseInt(pageA);
      const numB = parseInt(pageB);

      if (!isNaN(numA) && !isNaN(numB)) {
        return numA - numB;
      }

      // Define the logical order of sections based on audit structure
      const sectionOrder = {
        // Cover and intro pages
        'cover': 1, 'cover-page': 1, '1': 1,
        'why_andzen': 2, 'why-andzen': 2, 'andzen': 2,
        'table_of_contents': 3, 'toc': 3,

        // Executive summary  
        'executive_summary': 4, 'executive-summary': 4, 'summary': 4,

        // Performance sections
        'list_growth': 5, 'list-growth': 5, 'growth': 5,
        'data_capture': 6, 'data-capture': 6, 'capture': 6,
        'automation_overview': 7, 'automation-overview': 7, 'automation': 7,

        // Flow analysis
        'flow_welcome': 8, 'flow-welcome': 8, 'welcome': 8,
        'flow_abandoned_cart': 9, 'flow-abandoned-cart': 9, 'abandoned_cart': 9, 'abandoned-cart': 9,
        'flow_browse_abandonment': 10, 'flow-browse-abandonment': 10, 'browse_abandonment': 10, 'browse-abandonment': 10,
        'flow_post_purchase': 11, 'flow-post-purchase': 11, 'post_purchase': 11, 'post-purchase': 11,
        'advanced_reviews': 12, 'advanced-reviews': 12, 'reviews': 12,
        'advanced_wishlist': 13, 'advanced-wishlist': 13, 'wishlist': 13,

        // Strategic analysis
        'kav_analysis': 14, 'kav-analysis': 14, 'kav': 14,
        'campaign_performance': 15, 'campaign-performance': 15, 'campaigns': 15,
        'segmentation_strategy': 16, 'segmentation-strategy': 16, 'segmentation': 16,

        // Conclusions
        'strategic_recommendations': 17, 'strategic-recommendations': 17, 'recommendations': 17, 'strategic': 17,
        'next_steps': 18, 'next-steps': 18
      };

      // Try to match section IDs for order
      const getSectionOrder = (pageId) => {
        const id = pageId.toLowerCase();

        // Direct match
        if (sectionOrder[id] !== undefined) {
          return sectionOrder[id];
        }

        // Partial match - find if any key is contained in the section ID
        for (const [key, order] of Object.entries(sectionOrder)) {
          if (id.includes(key.replace(/_/g, '-')) || id.includes(key.replace(/-/g, '_'))) {
            return order;
          }
        }

        return 999; // Default for unknown sections
      };

      const orderA = getSectionOrder(pageA);
      const orderB = getSectionOrder(pageB);

      return orderA - orderB;
    });

    // Clear existing placeholder pages
    pageContainer.innerHTML = '';

    // Store section info for navigation
    this.sections = [];

    // Create pages from sections with intelligent splitting
    let pageNumber = 1;
    sections.forEach((section) => {
      // Skip page breaks themselves
      if (section.classList.contains('page-break')) {
        return;
      }

      // Store section identifier and title for sub-pages
      const sectionId = section.getAttribute('data-section') || section.id || `section-${pageNumber}`;
      const sectionTitle = section.querySelector('h1, h2, .section-title, [class*="title"]');
      const baseTitle = sectionTitle ? sectionTitle.textContent.trim() : this.formatSectionId(sectionId);

      // Check if section should be split into multiple pages
      const subPages = this.splitSectionIntoPages(section, sectionId, baseTitle);

      subPages.forEach((subPage, subIndex) => {
        const pageEl = document.createElement('div');
        pageEl.className = 'report-page';
        pageEl.id = `page-${pageNumber}`;
        pageEl.dataset.page = pageNumber;
        pageEl.dataset.sectionId = sectionId;
        pageEl.dataset.subPage = subIndex + 1;
        pageEl.dataset.totalSubPages = subPages.length;

        if (pageNumber === 1) {
          pageEl.classList.add('active');
        }

        // Create page title with sub-page indicator if needed
        let pageTitle = baseTitle;
        if (subPages.length > 1) {
          if (subPage.title) {
            pageTitle = `${baseTitle} - ${subPage.title}`;
          } else {
            pageTitle = `${baseTitle} (${subIndex + 1}/${subPages.length})`;
          }
        }
        pageEl.dataset.sectionTitle = pageTitle;

        // Clone section content into page wrapper
        const pageContent = document.createElement('div');
        pageContent.className = 'page-content';
        pageContent.innerHTML = subPage.content;

        pageEl.appendChild(pageContent);
        pageContainer.appendChild(pageEl);

        // Track section info
        this.sections.push({
          pageNumber,
          sectionId,
          title: pageTitle,
          subPage: subIndex + 1,
          totalSubPages: subPages.length,
          baseTitle
        });

        pageNumber++;
      });
    });

    // Update total pages and ensure we have at least page 1
    this.totalPages = Math.max(1, pageNumber - 1);
    this.currentPage = 1; // Reset to first page

    // Update UI elements
    this.updatePageIndicators();
    this.updateNavigationButtons();

    // Update sidebar navigation dynamically
    this.updateSidebarNavigation();

    // Setup sidebar click handlers
    this.setupSidebarNavigation();

    // Remove loading page if it exists
    const loadingPage = document.getElementById('page-loading');
    if (loadingPage && pageContainer.contains(loadingPage)) {
      pageContainer.removeChild(loadingPage);
    }

    // Update the window with section information for chat system
    this.updateChatSectionInfo();

    console.log(`✓ Rendered ${this.totalPages} pages from report content with ${this.sections.length} sections`);
  }

  updateChatSectionInfo() {
    // Provide section information to chat system
    const sectionMap = {};
    const sectionContent = {};

    // Group sections by base section ID
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

      // Extract content for chat context
      const pageEl = document.getElementById(`page-${section.pageNumber}`);
      if (pageEl) {
        sectionContent[baseId] += pageEl.textContent + '\n';
      }
    });

    // Store for chat system access
    window.reportSections = {
      map: sectionMap,
      content: sectionContent,
      available: Object.keys(sectionMap),
      findSection: (sectionName) => {
        const normalizedName = sectionName.toLowerCase()
          .replace(/\s+/g, '_')
          .replace(/-/g, '_');

        // Try exact match first
        if (sectionContent[normalizedName]) {
          return sectionContent[normalizedName];
        }

        // Try partial match
        for (const [id, content] of Object.entries(sectionContent)) {
          if (id.includes(normalizedName) || normalizedName.includes(id)) {
            return content;
          }
        }

        // Try common section name mappings
        const mappings = {
          'kav': 'kav_analysis',
          'executive': 'executive_summary',
          'summary': 'executive_summary',
          'strategic': 'strategic_recommendations',
          'recommendations': 'strategic_recommendations',
          'campaigns': 'campaign_performance',
          'automation': 'automation_overview',
          'flows': 'automation_overview',
          'growth': 'list_growth',
          'capture': 'data_capture',
          'segmentation': 'segmentation_strategy'
        };

        const mapped = mappings[normalizedName];
        if (mapped && sectionContent[mapped]) {
          return sectionContent[mapped];
        }

        return null;
      }
    };

    console.log('Available sections for chat:', Object.keys(sectionMap));
  }

  splitSectionIntoPages(section, sectionId, baseTitle) {
    // Clone the section to work with
    const sectionClone = section.cloneNode(true);
    const sectionHTML = sectionClone.outerHTML;

    // Check content length and complexity to decide if splitting is needed
    const textLength = sectionClone.textContent.length;
    const elementCount = sectionClone.querySelectorAll('*').length;

    // Thresholds for splitting (made more aggressive to ensure splitting)
    const SPLIT_TEXT_THRESHOLD = 1500; // characters (reduced from 3000)
    const SPLIT_ELEMENT_THRESHOLD = 25; // DOM elements (reduced from 50)

    console.log(`Section "${sectionId}": ${textLength} chars, ${elementCount} elements - Will split: ${textLength >= SPLIT_TEXT_THRESHOLD || elementCount >= SPLIT_ELEMENT_THRESHOLD}`);

    // Don't split small sections or cover pages
    if (textLength < SPLIT_TEXT_THRESHOLD && elementCount < SPLIT_ELEMENT_THRESHOLD) {
      return [{ content: sectionHTML, title: null }];
    }

    // For cover pages, always keep as single page
    if (sectionId.toLowerCase().includes('cover')) {
      return [{ content: sectionHTML, title: null }];
    }

    // Try to find natural break points (h2, h3 headers, major containers)
    const breakPoints = this.findSectionBreakPoints(sectionClone);

    if (breakPoints.length <= 1) {
      // No good break points found, but content is large - split by content blocks
      return this.splitByContentBlocks(sectionHTML, baseTitle);
    }

    // Split at break points
    const subPages = [];
    let currentContent = '';
    let currentTitle = null;

    breakPoints.forEach((breakPoint, index) => {
      if (breakPoint.content.trim()) {
        subPages.push({
          content: this.wrapContentInSection(breakPoint.content, sectionId),
          title: breakPoint.title
        });
      }
    });

    // If no valid sub-pages were created, return original
    if (subPages.length === 0) {
      return [{ content: sectionHTML, title: null }];
    }

    console.log(`Split section "${sectionId}" into ${subPages.length} pages`);
    return subPages;
  }

  findSectionBreakPoints(sectionElement) {
    const breakPoints = [];

    // Look for h2 and h3 headers as natural break points
    const headers = sectionElement.querySelectorAll('h2, h3');

    if (headers.length === 0) {
      // No headers found, try other break points like tables, cards, or divs
      const majorElements = sectionElement.querySelectorAll('table, .metric-card, .recommendation-card, .flow-card, .chart-container');

      if (majorElements.length > 3) {
        // Group elements into logical chunks
        let elementGroups = [];
        let currentGroup = [];

        Array.from(sectionElement.children).forEach(child => {
          currentGroup.push(child);
          if (currentGroup.length >= 3 || child.classList.contains('metric-card') || child.tagName === 'TABLE') {
            elementGroups.push(currentGroup);
            currentGroup = [];
          }
        });

        // Add remaining elements
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
    let currentSection = '';
    let currentTitle = null;
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

  splitByContentBlocks(sectionHTML, baseTitle) {
    // Simple content splitting by approximate size (reduced for better page breaks)
    const maxCharsPerPage = 1200;
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

      if (currentCharCount + childText > maxCharsPerPage && currentPageContent.length > 0) {
        // Start new page
        pages.push({
          content: this.wrapContentInSection(
            currentPageContent.map(el => el.outerHTML).join('\n'),
            sectionEl.getAttribute('data-section') || sectionEl.id || 'section'
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
          sectionEl.getAttribute('data-section') || sectionEl.id || 'section'
        ),
        title: pages.length > 0 ? `Part ${pages.length + 1}` : null
      });
    }

    return pages.length > 0 ? pages : [{ content: sectionHTML, title: null }];
  }

  wrapContentInSection(content, sectionId) {
    // Ensure section has proper identifiers for chat system
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

    // Add multiple identifiers to help backend find sections
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

  formatSectionId(sectionId) {
    // Convert section_id to Title Case
    return sectionId
      .replace(/_/g, ' ')
      .replace(/-/g, ' ')
      .replace(/\b\w/g, c => c.toUpperCase());
  }

  injectReportStyles(doc) {
    // Extract all <style> tags from the parsed document
    const styleTags = doc.querySelectorAll('style');

    if (styleTags.length === 0) {
      console.warn('No style tags found in report HTML - using basic styles immediately');
      this.injectBasicAuditStyles();
      // Also try to load external styles asynchronously
      this.loadFallbackStyles();
      return;
    }

    // Check if we already injected these styles
    const existingStylesId = 'injected-report-styles';
    let existingStyles = document.getElementById(existingStylesId);
    if (existingStyles) {
      existingStyles.remove();
    }

    // Create a combined style element
    const combinedStyle = document.createElement('style');
    combinedStyle.id = existingStylesId;

    let cssContent = '';
    styleTags.forEach(style => {
      cssContent += style.textContent + '\n';
    });

    // Scope styles to apply only within .page-content containers
    // This prevents conflicts with report-viewer styles while allowing report styles to work
    cssContent = this.scopeStylesToPageContent(cssContent);

    combinedStyle.textContent = cssContent;
    document.head.appendChild(combinedStyle);

    console.log(`✓ Injected ${styleTags.length} style blocks (${cssContent.length} chars) from report`);
  }

  async loadFallbackStyles() {
    // Load the template styles as fallback when HTML doesn't include them
    try {
      // Try multiple paths to find the styles
      const stylePaths = [
        '/templates/assets/styles.css',
        '/api/static/styles.css',
        '../templates/assets/styles.css'
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
        // Check if we already injected fallback styles
        const existingStylesId = 'fallback-report-styles';
        let existingStyles = document.getElementById(existingStylesId);
        if (existingStyles) {
          existingStyles.remove();
        }

        // Create style element
        const styleEl = document.createElement('style');
        styleEl.id = existingStylesId;
        styleEl.textContent = this.scopeStylesToPageContent(cssContent);
        document.head.appendChild(styleEl);

        console.log(`✓ Loaded fallback audit template styles (${cssContent.length} chars)`);
      } else {
        console.warn('Failed to load fallback styles - no valid path found');
        // If we can't load external styles, embed basic audit styles directly
        this.injectBasicAuditStyles();
      }
    } catch (error) {
      console.error('Error loading fallback styles:', error);
      this.injectBasicAuditStyles();
    }
  }

  injectBasicAuditStyles() {
    // Inject essential audit styles directly as fallback
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
      
      .page-content .flow-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
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
      
      .page-content .chart-container {
        margin: 1.5rem 0;
        text-align: center;
      }
      
      .page-content .chart-placeholder {
        background: #f8f9fa;
        border: 2px dashed #dee2e6;
        padding: 2rem;
        border-radius: 8px;
        color: #6c757d;
      }
    `;

    const styleEl = document.createElement('style');
    styleEl.id = existingStylesId;
    styleEl.textContent = basicStyles;
    document.head.appendChild(styleEl);

    console.log('✓ Injected basic audit styles as fallback');
  }

  scopeStylesToPageContent(css) {
    // Scope styles to .page-content to prevent conflicts
    // But don't scope @rules, :root, html, body selectors
    const lines = css.split('\n');
    let scoped = '';
    let inAtRule = false;
    let currentRule = '';

    for (let line of lines) {
      const trimmed = line.trim();

      // Handle @rules (media queries, keyframes, etc.)
      if (trimmed.startsWith('@')) {
        inAtRule = true;
        scoped += line + '\n';
        continue;
      }

      if (inAtRule) {
        scoped += line + '\n';
        if (trimmed === '}' || trimmed.endsWith('}')) {
          inAtRule = false;
        }
        continue;
      }

      // Handle regular CSS rules
      if (trimmed.includes('{')) {
        const parts = line.split('{');
        if (parts.length === 2) {
          const selectors = parts[0].trim();
          const declarations = parts[1];

          // Don't scope root-level selectors
          if (selectors.includes(':root') ||
            selectors.includes('html') ||
            selectors.includes('body') ||
            selectors.trim() === '') {
            scoped += line + '\n';
            continue;
          }

          // Scope to .page-content
          const scopedSelectors = selectors
            .split(',')
            .map(s => {
              s = s.trim();
              if (!s || s.startsWith('.')) return s;
              // Only scope if not already scoped
              if (s.includes('.page-content')) return s;
              return `.page-content ${s}`;
            })
            .join(', ');

          scoped += `${scopedSelectors} {${declarations}\n`;
        } else {
          scoped += line + '\n';
        }
      } else {
        scoped += line + '\n';
      }
    }

    return scoped;
  }

  renderByPageBreaks(htmlContent, container, doc) {
    // Split content by page breaks
    const pageBreaks = doc.querySelectorAll('.page-break');
    const body = doc.body || doc.documentElement;

    if (pageBreaks.length === 0) {
      this.renderFallbackContent(htmlContent, container);
      return;
    }

    container.innerHTML = '';
    let pageNumber = 1;
    let currentContent = [];
    let currentElement = body.firstChild;

    while (currentElement) {
      if (currentElement.classList && currentElement.classList.contains('page-break')) {
        // Create page from accumulated content
        if (currentContent.length > 0) {
          const pageEl = this.createPageFromContent(currentContent, pageNumber, pageNumber === 1);
          container.appendChild(pageEl);
          pageNumber++;
        }
        currentContent = [];
      } else {
        currentContent.push(currentElement.cloneNode(true));
      }
      currentElement = currentElement.nextSibling;
    }

    // Add final page
    if (currentContent.length > 0) {
      const pageEl = this.createPageFromContent(currentContent, pageNumber, pageNumber === 1);
      container.appendChild(pageEl);
    }

    this.totalPages = pageNumber;
    this.updatePageIndicators();
    this.updateNavigationButtons();
  }

  createPageFromContent(contentNodes, pageNumber, isActive) {
    const pageEl = document.createElement('div');
    pageEl.className = 'report-page';
    if (isActive) {
      pageEl.classList.add('active');
    }
    pageEl.id = `page-${pageNumber}`;
    pageEl.dataset.page = pageNumber;

    const pageContent = document.createElement('div');
    pageContent.className = 'page-content';

    contentNodes.forEach(node => {
      pageContent.appendChild(node);
    });

    pageEl.appendChild(pageContent);
    return pageEl;
  }

  renderFallbackContent(htmlContent, container) {
    // Fallback: create a single page with all content
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
    this.updatePageIndicators();
    this.updateNavigationButtons();
  }

  updateSidebarNavigation() {
    const navList = document.querySelector('.section-nav');
    if (!navList || !this.sections || this.sections.length === 0) return;

    // Clear existing navigation
    navList.innerHTML = '';

    // Group sections by category based on section ID
    const categories = {
      'Executive Summary': ['cover', 'why_andzen', 'table_of_contents', 'executive_summary'],
      'Performance Analysis': ['list_growth', 'data_capture', 'automation_overview', 'campaign_performance'],
      'Flow Deep Dive': ['flow_welcome', 'flow_abandoned_cart', 'flow_browse_abandonment', 'flow_post_purchase', 'advanced_reviews', 'advanced_wishlist'],
      'Strategic Insights': ['kav_analysis', 'segmentation_strategy', 'strategic_recommendations', 'next_steps']
    };

    // Build grouped navigation
    const groupedSections = {};

    this.sections.forEach((section, index) => {
      const sectionId = section.sectionId || '';
      let category = 'Other';

      for (const [catName, ids] of Object.entries(categories)) {
        if (ids.some(id => sectionId.toLowerCase().includes(id.toLowerCase()))) {
          category = catName;
          break;
        }
      }

      if (!groupedSections[category]) {
        groupedSections[category] = [];
      }
      groupedSections[category].push({
        ...section,
        index
      });
    });

    // Render navigation groups
    for (const [categoryName, sectionsList] of Object.entries(groupedSections)) {
      if (sectionsList.length === 0) continue;

      const navSection = document.createElement('div');
      navSection.className = 'nav-section';

      const categoryTitle = document.createElement('h3');
      categoryTitle.textContent = categoryName;
      navSection.appendChild(categoryTitle);

      const ul = document.createElement('ul');

      sectionsList.forEach(section => {
        const li = document.createElement('li');
        const link = document.createElement('a');
        link.href = `#page-${section.pageNumber}`;
        link.className = 'nav-link';
        link.dataset.page = section.pageNumber;
        link.textContent = section.title;

        if (section.pageNumber === this.currentPage) {
          link.classList.add('active');
        }

        li.appendChild(link);
        ul.appendChild(li);
      });

      navSection.appendChild(ul);
      navList.appendChild(navSection);
    }

    console.log(`Updated sidebar with ${this.sections.length} sections in ${Object.keys(groupedSections).length} categories`);
  }

  // Legacy function kept for compatibility
  updateSidebarNavigationLegacy(sections) {
    const navList = document.querySelector('.section-nav');
    if (!navList) return;

    const navSections = navList.querySelectorAll('.nav-section');
    navSections.forEach(section => section.remove());

    const categories = {
      'Executive Summary': [],
      'Performance Analysis': [],
      'Flow Deep Dive': [],
      'Strategic Insights': []
    };

    sections.forEach((section, index) => {
      const title = section.querySelector('h1, h2, .section-title')?.textContent?.trim() || `Section ${index + 1}`;
      const pageNum = index + 1;

      // Categorize based on title
      let category = 'Strategic Insights'; // default
      if (title.toLowerCase().includes('executive') || title.toLowerCase().includes('summary')) {
        category = 'Executive Summary';
      } else if (title.toLowerCase().includes('campaign') || title.toLowerCase().includes('automation') || title.toLowerCase().includes('list')) {
        category = 'Performance Analysis';
      } else if (title.toLowerCase().includes('flow') || title.toLowerCase().includes('welcome') || title.toLowerCase().includes('abandoned') || title.toLowerCase().includes('browse')) {
        category = 'Flow Deep Dive';
      }

      categories[category].push({ title, pageNum });
    });

    // Create navigation structure
    Object.entries(categories).forEach(([categoryName, items]) => {
      if (items.length === 0) return;

      const navSection = document.createElement('div');
      navSection.className = 'nav-section';

      const navTitle = document.createElement('h3');
      navTitle.textContent = categoryName;
      navSection.appendChild(navTitle);

      const navList = document.createElement('ul');
      items.forEach(item => {
        const navItem = document.createElement('li');
        const navLink = document.createElement('a');
        navLink.href = `#page-${item.pageNum}`;
        navLink.className = 'nav-link';
        navLink.textContent = item.title;
        navLink.addEventListener('click', (e) => {
          e.preventDefault();
          this.goToPage(item.pageNum);
        });
        navItem.appendChild(navLink);
        navList.appendChild(navItem);
      });

      navSection.appendChild(navList);
      document.querySelector('.section-nav')?.appendChild(navSection);
    });
  }

  addChatMessage(type, content, actions = null) {
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;

    const messageEl = document.createElement('div');
    messageEl.className = `message ${type}`;

    const avatar = type === 'user' ? '👤' : '🤖';
    const actionsHtml = actions ? `<div class="message-actions">${actions}</div>` : '';

    // Format content - handle markdown-like formatting and cleanup
    const formattedContent = this.formatChatContent(content);

    messageEl.innerHTML = `
      <div class="message-avatar">${avatar}</div>
      <div class="message-content">
        ${formattedContent}
        ${actionsHtml}
      </div>
    `;

    messagesContainer.appendChild(messageEl);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Setup action buttons if present
    if (actions) {
      this.setupMessageActionButtons(messageEl);
    }
  }

  formatChatContent(content) {
    if (!content) return '<p>No response available.</p>';

    // Clean up any remaining JSON artifacts
    let text = String(content);

    // Remove JSON wrapper artifacts
    if (text.trim().startsWith('{') || text.trim().startsWith('[')) {
      // Try to extract just the response text
      const responseMatch = text.match(/"response"\s*:\s*"((?:[^"\\]|\\.)*)"/s);
      if (responseMatch) {
        text = responseMatch[1].replace(/\\n/g, '\n').replace(/\\"/g, '"');
      }
    }

    // Clean up Python dict-like syntax that might slip through
    // Handle both 'primary': '...' and "primary": "..." formats
    if (text.includes("'primary':") || text.includes('"primary":') || text.includes("primary:")) {
      // Try to extract primary and secondary content
      const primaryMatch = text.match(/['"]?primary['"]?\s*:\s*['"](.+?)['"](?:\s*,\s*['"]?secondary|$)/s);
      const secondaryMatch = text.match(/['"]?secondary['"]?\s*:\s*['"](.+?)['"](?:}|\]|$)/s);

      const parts = [];
      if (primaryMatch) {
        parts.push(primaryMatch[1].replace(/\\n/g, '\n').replace(/\\"/g, '"').replace(/\\'/g, "'"));
      }
      if (secondaryMatch) {
        parts.push(secondaryMatch[1].replace(/\\n/g, '\n').replace(/\\"/g, '"').replace(/\\'/g, "'"));
      }

      if (parts.length > 0) {
        text = parts.join('\n\n');
      }
    }

    // Remove any remaining dict/JSON artifacts
    text = text
      .replace(/\{'primary':\s*['"](.+?)['"]\s*,\s*'secondary':\s*['"](.+?)['"]\}/s, '$1\n\n$2')
      .replace(/\{"primary":\s*"(.+?)"\s*,\s*"secondary":\s*"(.+?)"\}/s, '$1\n\n$2')
      .replace(/^\{.*?'primary':\s*['"]/s, '')
      .replace(/['"]\s*,\s*'secondary':\s*['"]/s, '\n\n')
      .replace(/['"]\s*\}$/s, '');

    // Escape HTML to prevent XSS (but preserve line breaks)
    text = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Convert double newlines to paragraph breaks, single newlines to <br>
    const paragraphs = text.split(/\n\n+/).filter(p => p.trim());
    if (paragraphs.length > 1) {
      return paragraphs.map(p => {
        const para = p.trim().replace(/\n/g, '<br>');
        return `<p>${para}</p>`;
      }).join('');
    }

    // Single paragraph - preserve line breaks
    return `<p>${text.trim().replace(/\n/g, '<br>')}</p>`;
  }

  simulateAIResponse(userMessage) {
    const responses = {
      'revenue': 'The biggest revenue opportunity is optimizing the abandoned cart flow, which could generate an additional $34K monthly.',
      'flows': 'Currently, you have 18 active flows. The welcome series and abandoned cart flows are performing well, but browse abandonment needs attention.',
      'default': 'I can help you analyze various aspects of this audit. Try asking about revenue opportunities, flow performance, or specific recommendations.'
    };

    let response = responses.default;
    const lowerMessage = userMessage.toLowerCase();

    if (lowerMessage.includes('revenue') || lowerMessage.includes('growth') || lowerMessage.includes('money')) {
      response = responses.revenue;
    } else if (lowerMessage.includes('flow') || lowerMessage.includes('automation')) {
      response = responses.flows;
    }

    const actions = `
      <button class="btn-edit-request">✏️ Request Edit</button>
      <button class="btn-add-quote">💼 Add to Quote</button>
    `;

    this.addChatMessage('assistant', response, actions);
  }

  setupMessageActionButtons(messageEl) {
    const editBtn = messageEl.querySelector('.btn-edit-request');
    const quoteBtn = messageEl.querySelector('.btn-add-quote');

    if (editBtn) {
      editBtn.addEventListener('click', () => {
        this.handleEditRequest(messageEl);
      });
    }

    if (quoteBtn) {
      quoteBtn.addEventListener('click', () => {
        this.addToQuote(messageEl);
      });
    }
  }

  setupEditRequestButtons() {
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('btn-edit-request')) {
        this.handleEditRequest(e.target.closest('.message'));
      }
    });
  }

  handleEditRequest(messageEl) {
    // Switch to quote builder tab and highlight the opportunity
    const quoteTab = document.querySelector('[data-tab="quotes"]');
    if (quoteTab) {
      quoteTab.click();
    }

    // Show edit interface (this would be expanded in full implementation)
    this.showEditModal(messageEl);
  }

  showEditModal(messageEl) {
    // Get the assistant message content to edit
    const messageContent = messageEl.querySelector('.message-content p');
    const originalText = messageContent ? messageContent.textContent : '';

    // Create modal if it doesn't exist
    let editModal = document.getElementById('edit-content-modal');
    if (!editModal) {
      editModal = this.createEditModal();
    }

    // Populate modal with content
    const modalTextarea = editModal.querySelector('#edit-content-textarea');
    const modalTitle = editModal.querySelector('.modal-title');

    if (modalTextarea) {
      modalTextarea.value = originalText;
    }

    if (modalTitle) {
      modalTitle.textContent = 'Edit AI Response';
    }

    // Show modal
    editModal.style.display = 'flex';

    // Focus textarea
    setTimeout(() => {
      if (modalTextarea) {
        modalTextarea.focus();
        modalTextarea.setSelectionRange(0, 0); // Cursor at beginning
      }
    }, 100);

    // Store reference to original message for saving
    editModal.dataset.originalMessageId = messageEl.id || `msg-${Date.now()}`;
    if (!messageEl.id) {
      messageEl.id = editModal.dataset.originalMessageId;
    }
  }

  createEditModal() {
    // Create edit modal structure
    const modal = document.createElement('div');
    modal.id = 'edit-content-modal';
    modal.className = 'edit-modal';
    modal.innerHTML = `
      <div class="modal-backdrop"></div>
      <div class="modal-container">
        <div class="modal-header">
          <h3 class="modal-title">Edit Content</h3>
          <button class="modal-close" id="close-edit-modal">&times;</button>
        </div>
        
        <div class="modal-body">
          <label for="edit-content-textarea">Content:</label>
          <textarea 
            id="edit-content-textarea" 
            placeholder="Edit the content here..."
            rows="10"
          ></textarea>
          
          <div class="edit-options">
            <label>
              <input type="checkbox" id="apply-to-report" />
              Apply changes to report
            </label>
            <label>
              <input type="checkbox" id="save-as-note" checked />
              Save as note for final review
            </label>
          </div>
        </div>
        
        <div class="modal-footer">
          <button class="btn btn-ghost" id="cancel-edit">Cancel</button>
          <button class="btn btn-primary" id="save-edit">Save Changes</button>
        </div>
      </div>
    `;

    // Add modal styles
    this.addEditModalStyles();

    // Add event listeners
    const closeBtn = modal.querySelector('#close-edit-modal');
    const cancelBtn = modal.querySelector('#cancel-edit');
    const saveBtn = modal.querySelector('#save-edit');
    const backdrop = modal.querySelector('.modal-backdrop');

    const closeModal = () => {
      modal.style.display = 'none';
    };

    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);
    backdrop.addEventListener('click', closeModal);

    saveBtn.addEventListener('click', () => {
      this.saveEditedContent(modal);
      closeModal();
    });

    // Append to body
    document.body.appendChild(modal);

    return modal;
  }

  addEditModalStyles() {
    if (document.getElementById('edit-modal-styles')) return;

    const styles = document.createElement('style');
    styles.id = 'edit-modal-styles';
    styles.textContent = `
      .edit-modal {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 10000;
        display: none;
        align-items: center;
        justify-content: center;
        font-family: 'Montserrat', sans-serif;
      }
      
      .modal-backdrop {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(4px);
      }
      
      .modal-container {
        background: white;
        border-radius: 12px;
        width: 90%;
        max-width: 600px;
        max-height: 80vh;
        display: flex;
        flex-direction: column;
        position: relative;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
      }
      
      .modal-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.5rem;
        border-bottom: 1px solid #e2e8f0;
      }
      
      .modal-title {
        margin: 0;
        color: #1e293b;
        font-weight: 600;
      }
      
      .modal-close {
        background: none;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        color: #64748b;
        width: 32px;
        height: 32px;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      
      .modal-close:hover {
        background: #f1f5f9;
        color: #1e293b;
      }
      
      .modal-body {
        padding: 1.5rem;
        flex: 1;
        overflow-y: auto;
      }
      
      .modal-body label {
        display: block;
        margin-bottom: 0.5rem;
        font-weight: 500;
        color: #374151;
      }
      
      #edit-content-textarea {
        width: 100%;
        min-height: 200px;
        padding: 0.75rem;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        font-family: 'Montserrat', sans-serif;
        font-size: 0.9rem;
        line-height: 1.5;
        resize: vertical;
        margin-bottom: 1rem;
      }
      
      #edit-content-textarea:focus {
        outline: none;
        border-color: #65DA4F;
        box-shadow: 0 0 0 3px rgba(101, 218, 79, 0.1);
      }
      
      .edit-options {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
      }
      
      .edit-options label {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.9rem;
        margin: 0;
      }
      
      .edit-options input[type="checkbox"] {
        width: 16px;
        height: 16px;
      }
      
      .modal-footer {
        display: flex;
        gap: 0.75rem;
        justify-content: flex-end;
        padding: 1.5rem;
        border-top: 1px solid #e2e8f0;
      }
      
      .modal-footer .btn {
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-weight: 500;
        border: 1px solid transparent;
        cursor: pointer;
        transition: all 0.2s;
      }
      
      .modal-footer .btn-ghost {
        background: white;
        color: #64748b;
        border-color: #d1d5db;
      }
      
      .modal-footer .btn-ghost:hover {
        background: #f8fafc;
        color: #1e293b;
      }
      
      .modal-footer .btn-primary {
        background: #65DA4F;
        color: white;
        border-color: #65DA4F;
      }
      
      .modal-footer .btn-primary:hover {
        background: #5BC946;
        border-color: #5BC946;
      }
    `;

    document.head.appendChild(styles);
  }

  saveEditedContent(modal) {
    const textarea = modal.querySelector('#edit-content-textarea');
    const applyToReport = modal.querySelector('#apply-to-report').checked;
    const saveAsNote = modal.querySelector('#save-as-note').checked;

    if (!textarea) return;

    const newContent = textarea.value.trim();
    if (!newContent) {
      alert('Please enter some content');
      return;
    }

    // Find the original message element
    const originalMessageId = modal.dataset.originalMessageId;
    const originalMessage = document.getElementById(originalMessageId);

    if (originalMessage) {
      // Update the message content
      const messageContentEl = originalMessage.querySelector('.message-content p');
      if (messageContentEl) {
        messageContentEl.textContent = newContent;
      }

      // Add edit indicator
      const editIndicator = originalMessage.querySelector('.edit-indicator') || document.createElement('div');
      editIndicator.className = 'edit-indicator';
      editIndicator.innerHTML = '<small style="color: #65DA4F; font-style: italic;">✏️ Edited</small>';

      if (!originalMessage.querySelector('.edit-indicator')) {
        const messageContent = originalMessage.querySelector('.message-content');
        if (messageContent) {
          messageContent.appendChild(editIndicator);
        }
      }
    }

    // Handle apply to report
    if (applyToReport) {
      this.showToast('Content updated in chat. To apply to report, use the "Request Edit" button again.', 'info');
    }

    // Handle save as note
    if (saveAsNote) {
      this.saveEditNote(newContent);
    }

    this.showToast('Changes saved successfully!', 'success');
  }

  saveEditNote(content) {
    // Store edit notes for later review
    if (!window.editNotes) {
      window.editNotes = [];
    }

    window.editNotes.push({
      content: content,
      timestamp: new Date().toISOString(),
      reportId: this.reportId
    });

    console.log('Saved edit note:', content);
  }

  addToQuote(messageEl) {
    const messageContent = messageEl.querySelector('.message-content p').textContent;

    // Extract value from message (this would be more sophisticated)
    const match = messageContent.match(/\$(\d+(?:,\d+)*(?:K)?)/);
    const value = match ? match[0] : '+$0';

    this.addQuoteItem('🚀', 'Custom Recommendation', messageContent.substring(0, 60) + '...', '8 hours', value);

    // Switch to quotes tab
    const quoteTab = document.querySelector('[data-tab="quotes"]');
    if (quoteTab) {
      quoteTab.click();
    }

    // Show success feedback
    this.showToast('Added to quote builder!');
  }

  setupQuoteBuilder() {
    const generateBtn = document.querySelector('.btn-generate-quote');

    if (generateBtn) {
      generateBtn.addEventListener('click', () => {
        this.generateQuoteDocument();
      });
    }

    // Setup remove buttons for quote items
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('btn-remove')) {
        this.removeQuoteItem(e.target.closest('.quote-item'));
      }
    });
  }

  addQuoteItem(icon, title, description, effort, impact) {
    const quoteItems = document.querySelector('.quote-items');
    if (!quoteItems) return;

    const itemEl = document.createElement('div');
    itemEl.className = 'quote-item';
    itemEl.innerHTML = `
      <div class="quote-icon">${icon}</div>
      <div class="quote-details">
        <h4>${title}</h4>
        <p>${description}</p>
        <div class="quote-value">
          <span class="effort">${effort}</span>
          <span class="impact">${impact}</span>
        </div>
      </div>
      <button class="btn-remove">×</button>
    `;

    quoteItems.appendChild(itemEl);
    this.updateQuoteTotals();
  }

  removeQuoteItem(itemEl) {
    if (itemEl) {
      itemEl.remove();
      this.updateQuoteTotals();
    }
  }

  updateQuoteTotals() {
    const quoteItems = document.querySelectorAll('.quote-item');
    let totalHours = 0;
    let totalImpact = 0;

    quoteItems.forEach(item => {
      const effortText = item.querySelector('.effort').textContent;
      const impactText = item.querySelector('.impact').textContent;

      // Extract numbers (simplified parsing)
      const hours = parseInt(effortText.match(/\d+/)?.[0] || 0);
      const impact = parseInt(impactText.replace(/[^\d]/g, '') || 0);

      totalHours += hours;
      totalImpact += impact;
    });

    // Update displays
    const totalEffortEl = document.querySelector('.total-effort .value');
    const totalImpactEl = document.querySelector('.total-impact .value');

    if (totalEffortEl) totalEffortEl.textContent = `${totalHours} hours`;
    if (totalImpactEl) totalImpactEl.textContent = `+$${totalImpact}K`;
  }

  async generateQuoteDocument() {
    if (!this.reportId) {
      this.showToast('No report ID available', 'error');
      return;
    }

    this.showToast('Generating quote document...');

    try {
      const response = await fetch(`/api/audit/${this.reportId}/quote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          priorities: this.quoteItems.map(item => ({
            title: item.title,
            description: item.description,
            effort: item.effort,
            impact: item.impact
          }))
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Quote generation failed');
      }

      const data = await response.json();

      // Download quote document
      if (data.quote_url) {
        window.open(data.quote_url, '_blank');
        this.showToast('Quote document ready!', 'success');
      } else if (data.quote_content) {
        // Create download link for quote content
        const blob = new Blob([data.quote_content], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `quote_${this.reportId}_${Date.now()}.html`;
        a.click();
        URL.revokeObjectURL(url);
        this.showToast('Quote downloaded!', 'success');
      }
    } catch (error) {
      console.error('Quote generation error:', error);
      this.showToast(`Error: ${error.message}`, 'error');
    }
  }

  showToast(message, type = 'info') {
    // Create a simple toast notification
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    const colors = {
      success: 'var(--andzen-green)',
      error: '#EF4444',
      info: 'var(--andzen-green)',
      warning: '#F59E0B'
    };

    toast.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: ${colors[type] || colors.info};
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      z-index: 1000;
      font-weight: 500;
      box-shadow: var(--shadow-lg);
      animation: slideIn 0.3s ease;
    `;

    // Add animation styles if not already present
    if (!document.getElementById('toast-styles')) {
      const style = document.createElement('style');
      style.id = 'toast-styles';
      style.textContent = `
        @keyframes slideIn {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
      `;
      document.head.appendChild(style);
    }

    document.body.appendChild(toast);

    // Remove toast after 3 seconds
    setTimeout(() => {
      toast.style.animation = 'slideOut 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  showError(message) {
    this.showToast(message, 'error');
  }

  scrollToSection(sectionId) {
    if (!sectionId || !this.sections) return;

    // Find the section in our tracked sections
    const section = this.sections.find(s =>
      s.sectionId.toLowerCase() === sectionId.toLowerCase() ||
      s.sectionId.toLowerCase().includes(sectionId.toLowerCase())
    );

    if (section) {
      this.goToPage(section.pageNumber);

      // Update active nav link
      const navLinks = document.querySelectorAll('.nav-link');
      navLinks.forEach(link => link.classList.remove('active'));
      const activeLink = document.querySelector(`.nav-link[data-page="${section.pageNumber}"]`);
      if (activeLink) activeLink.classList.add('active');

      this.showToast(`Navigated to ${section.title}`, 'info');
    } else {
      console.warn(`Section not found: ${sectionId}`);
    }
  }

  // ==================== EDIT MODE FUNCTIONALITY ====================

  setupEditMode() {
    this.editHistory = [];
    this.editHistoryIndex = -1;
    this.isEditMode = false;

    // Add edit mode toggle button
    this.addEditModeControls();
  }

  addEditModeControls() {
    const pageControls = document.querySelector('.page-controls');
    if (!pageControls) return;

    // Create edit mode toggle button
    const editControls = document.createElement('div');
    editControls.className = 'edit-controls';
    editControls.innerHTML = `
      <button class="btn-edit-mode" title="Toggle Edit Mode">✏️ Edit</button>
      <div class="edit-toolbar" style="display: none;">
        <button class="btn-undo" disabled title="Undo (Ctrl+Z)">↩️</button>
        <button class="btn-redo" disabled title="Redo (Ctrl+Y)">↪️</button>
        <div class="format-divider"></div>
        <button class="btn-bold" title="Bold (Ctrl+B)"><strong>B</strong></button>
        <button class="btn-italic" title="Italic (Ctrl+I)"><em>I</em></button>
        <button class="btn-underline" title="Underline (Ctrl+U)"><u>U</u></button>
        <div class="format-divider"></div>
        <button class="btn-save-edit" title="Save Changes">💾 Save</button>
      </div>
    `;

    pageControls.prepend(editControls);

    // Add styles for edit controls
    this.addEditStyles();

    // Setup event listeners
    const editModeBtn = editControls.querySelector('.btn-edit-mode');
    const undoBtn = editControls.querySelector('.btn-undo');
    const redoBtn = editControls.querySelector('.btn-redo');
    const boldBtn = editControls.querySelector('.btn-bold');
    const italicBtn = editControls.querySelector('.btn-italic');
    const underlineBtn = editControls.querySelector('.btn-underline');
    const saveBtn = editControls.querySelector('.btn-save-edit');

    editModeBtn.addEventListener('click', () => this.toggleEditMode());
    undoBtn.addEventListener('click', () => this.undo());
    redoBtn.addEventListener('click', () => this.redo());
    boldBtn.addEventListener('click', () => document.execCommand('bold'));
    italicBtn.addEventListener('click', () => document.execCommand('italic'));
    underlineBtn.addEventListener('click', () => document.execCommand('underline'));
    saveBtn.addEventListener('click', () => this.saveEdits());

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      if (!this.isEditMode) return;

      if (e.ctrlKey || e.metaKey) {
        switch (e.key.toLowerCase()) {
          case 'z':
            e.preventDefault();
            if (e.shiftKey) this.redo();
            else this.undo();
            break;
          case 'y':
            e.preventDefault();
            this.redo();
            break;
          case 's':
            e.preventDefault();
            this.saveEdits();
            break;
        }
      }
    });
  }

  addEditStyles() {
    if (document.getElementById('edit-mode-styles')) return;

    const style = document.createElement('style');
    style.id = 'edit-mode-styles';
    style.textContent = `
      .edit-controls {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-right: auto;
      }
      
      .btn-edit-mode {
        background: var(--andzen-dark);
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 500;
        transition: all 0.2s;
      }
      
      .btn-edit-mode:hover,
      .btn-edit-mode.active {
        background: var(--andzen-green);
        color: var(--andzen-dark);
      }
      
      .edit-toolbar {
        display: flex;
        align-items: center;
        gap: 4px;
        background: var(--sidebar-bg);
        border: 1px solid var(--page-border);
        padding: 4px 8px;
        border-radius: 6px;
      }
      
      .edit-toolbar button {
        background: none;
        border: 1px solid transparent;
        padding: 6px 10px;
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.2s;
      }
      
      .edit-toolbar button:hover:not(:disabled) {
        background: var(--andzen-green-light);
        border-color: var(--andzen-green);
      }
      
      .edit-toolbar button:disabled {
        opacity: 0.4;
        cursor: not-allowed;
      }
      
      .format-divider {
        width: 1px;
        height: 20px;
        background: var(--page-border);
        margin: 0 4px;
      }
      
      .btn-save-edit {
        background: var(--andzen-green) !important;
        color: white !important;
        font-weight: 500;
      }
      
      .report-page.edit-mode .page-content {
        outline: 2px dashed var(--andzen-green);
        outline-offset: 4px;
      }
      
      .report-page.edit-mode [contenteditable="true"] {
        cursor: text;
        padding: 2px 4px;
        margin: -2px -4px;
        border-radius: 2px;
      }
      
      .report-page.edit-mode [contenteditable="true"]:focus {
        background: rgba(110, 216, 85, 0.1);
        outline: 1px solid var(--andzen-green);
      }
    `;
    document.head.appendChild(style);
  }

  toggleEditMode() {
    this.isEditMode = !this.isEditMode;

    const editModeBtn = document.querySelector('.btn-edit-mode');
    const editToolbar = document.querySelector('.edit-toolbar');
    const pages = document.querySelectorAll('.report-page');

    if (this.isEditMode) {
      editModeBtn.classList.add('active');
      editModeBtn.textContent = '✏️ Editing';
      editToolbar.style.display = 'flex';

      // Make content editable
      pages.forEach(page => {
        page.classList.add('edit-mode');
        const editableElements = page.querySelectorAll('p, h1, h2, h3, h4, h5, h6, li, td, th, span:not(.metric-value):not(.stat-value)');
        editableElements.forEach(el => {
          el.setAttribute('contenteditable', 'true');
          el.addEventListener('input', () => this.saveToHistory());
        });
      });

      // Save initial state
      this.saveToHistory();
      this.showToast('Edit mode enabled. Click on text to edit.', 'info');
    } else {
      editModeBtn.classList.remove('active');
      editModeBtn.textContent = '✏️ Edit';
      editToolbar.style.display = 'none';

      // Make content non-editable
      pages.forEach(page => {
        page.classList.remove('edit-mode');
        page.querySelectorAll('[contenteditable]').forEach(el => {
          el.removeAttribute('contenteditable');
        });
      });

      this.showToast('Edit mode disabled', 'info');
    }
  }

  saveToHistory() {
    const pageContainer = document.getElementById('page-container');
    if (!pageContainer) return;

    const currentState = pageContainer.innerHTML;

    // Don't save if it's the same as the last state
    if (this.editHistory.length > 0 && this.editHistory[this.editHistoryIndex] === currentState) {
      return;
    }

    // Remove any states after current index (when undone)
    this.editHistory = this.editHistory.slice(0, this.editHistoryIndex + 1);

    // Add new state
    this.editHistory.push(currentState);
    this.editHistoryIndex = this.editHistory.length - 1;

    // Limit history size
    if (this.editHistory.length > 50) {
      this.editHistory.shift();
      this.editHistoryIndex--;
    }

    this.updateUndoRedoButtons();
  }

  undo() {
    if (this.editHistoryIndex <= 0) return;

    this.editHistoryIndex--;
    const pageContainer = document.getElementById('page-container');
    if (pageContainer) {
      pageContainer.innerHTML = this.editHistory[this.editHistoryIndex];
      this.reattachEditListeners();
    }

    this.updateUndoRedoButtons();
  }

  redo() {
    if (this.editHistoryIndex >= this.editHistory.length - 1) return;

    this.editHistoryIndex++;
    const pageContainer = document.getElementById('page-container');
    if (pageContainer) {
      pageContainer.innerHTML = this.editHistory[this.editHistoryIndex];
      this.reattachEditListeners();
    }

    this.updateUndoRedoButtons();
  }

  reattachEditListeners() {
    if (!this.isEditMode) return;

    const pages = document.querySelectorAll('.report-page');
    pages.forEach(page => {
      page.classList.add('edit-mode');
      const editableElements = page.querySelectorAll('p, h1, h2, h3, h4, h5, h6, li, td, th');
      editableElements.forEach(el => {
        el.setAttribute('contenteditable', 'true');
        el.addEventListener('input', () => this.saveToHistory());
      });
    });
  }

  updateUndoRedoButtons() {
    const undoBtn = document.querySelector('.btn-undo');
    const redoBtn = document.querySelector('.btn-redo');

    if (undoBtn) undoBtn.disabled = this.editHistoryIndex <= 0;
    if (redoBtn) redoBtn.disabled = this.editHistoryIndex >= this.editHistory.length - 1;
  }

  async saveEdits() {
    if (!this.reportId) {
      this.showToast('No report ID available', 'error');
      return;
    }

    const pageContainer = document.getElementById('page-container');
    if (!pageContainer) return;

    // Get the edited HTML content
    const editedContent = pageContainer.innerHTML;

    this.showToast('Saving changes...', 'info');

    try {
      const response = await fetch(`/api/audit/${this.reportId}/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          html_content: editedContent
        })
      });

      if (response.ok) {
        this.showToast('Changes saved successfully!', 'success');
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save');
      }
    } catch (error) {
      console.error('Save error:', error);
      this.showToast(`Error saving: ${error.message}`, 'error');
    }
  }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
  new ReportViewer();
});

// Export for use in other modules
window.ReportViewer = ReportViewer;