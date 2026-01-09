/**
 * ReportViewer - Modular Report Viewer Controller
 * Coordinates between all report viewer modules
 */
class ReportViewer {
  constructor() {
    this.reportId = null;
    
    // Initialize all modules
    this.styleManager = new StyleManager();
    this.reportRenderer = new ReportRenderer();
    this.pageNavigator = new PageNavigator();
    this.chatInterface = new ChatInterface();
    this.editModal = new EditModal();
    this.quoteBuilder = new QuoteBuilder();
    this.exportManager = new ExportManager();
    
    // State
    this.isInitialized = false;
    
    this.init();
  }

  /**
   * Initialize report viewer
   */
  async init() {
    try {
      // Get report ID from URL
      this.reportId = this.getReportIdFromUrl();
      
      if (!this.reportId) {
        this.showError('No report ID provided. Please navigate from the dashboard.');
        return;
      }

      console.log(`Initializing modular report viewer for report ID: ${this.reportId}`);

      // Setup UI components
      this.setupTabs();
      this.setupToastNotifications();
      this.setupModuleEventListeners();

      // Initialize all modules
      this.exportManager.init(this.reportId);
      this.editModal.init(this.reportId);
      this.quoteBuilder.init(this.reportId);
      this.chatInterface.init(this.reportId);

      // Load and render report content
      await this.loadReportContent();
      
      this.isInitialized = true;
      console.log('✓ Modular report viewer initialized successfully');
      
    } catch (error) {
      console.error('Failed to initialize report viewer:', error);
      this.showError(`Failed to initialize report viewer: ${error.message}`);
    }
  }

  /**
   * Get report ID from URL parameters
   */
  getReportIdFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return parseInt(urlParams.get('reportId') || urlParams.get('report_id') || urlParams.get('id'));
  }

  /**
   * Load report content using ReportRenderer
   */
  async loadReportContent() {
    try {
      console.log('Loading report content...');
      
      // Use ReportRenderer to load and render content
      const renderResult = await this.reportRenderer.loadReportContent(this.reportId);
      
      if (renderResult) {
        // Initialize PageNavigator with the rendered content
        this.pageNavigator.init(renderResult.totalPages, renderResult.sections);
        
        // Update report header info
        this.updateReportHeader();
        
        console.log(`✓ Report content loaded: ${renderResult.totalPages} pages, ${renderResult.sections.length} sections`);
      }
      
    } catch (error) {
      console.error('Error loading report content:', error);
      this.showError(`Failed to load report: ${error.message}`);
    }
  }

  /**
   * Update report header with report information
   */
  async updateReportHeader() {
    try {
      const response = await fetch(`${window.API_BASE_URL}/api/audit/status/${this.reportId}`);
      if (!response.ok) return;

      const data = await response.json();
      
      const titleEl = document.querySelector('.report-title h1');
      const descEl = document.querySelector('.report-title p');
      
      // Update title
      if (titleEl) {
        if (data.report_data?.client_name) {
          titleEl.textContent = data.report_data.client_name;
        } else {
          titleEl.textContent = 'Audit Report';
        }
      }
      
      // Update date - use created_at from the response
      if (descEl) {
        let dateStr = '';
        if (data.created_at) {
          try {
            const date = new Date(data.created_at);
            if (!isNaN(date.getTime())) {
              dateStr = date.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              });
            }
          } catch (e) {
            console.error('Error parsing date:', e);
          }
        }
        
        if (dateStr) {
          descEl.textContent = `Generated on ${dateStr}`;
        } else {
          descEl.textContent = '';
        }
      }
      
    } catch (error) {
      console.error('Failed to update report header:', error);
      // Set fallback text if update fails
      const titleEl = document.querySelector('.report-title h1');
      const descEl = document.querySelector('.report-title p');
      if (titleEl) titleEl.textContent = 'Audit Report';
      if (descEl) descEl.textContent = '';
    }
  }

  /**
   * Setup tab switching functionality
   */
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

  /**
   * Setup toast notification system
   */
  setupToastNotifications() {
    // Listen for toast events from modules
    window.addEventListener('showToast', (e) => {
      this.showToast(e.detail.message, e.detail.type);
    });
  }

  /**
   * Setup event listeners for inter-module communication
   */
  setupModuleEventListeners() {
    // Back to dashboard button is handled by ExportManager.setupBackButton()
    // No need to duplicate here
    
    // Edit report button
    const editBtn = document.getElementById('btn-edit-report');
    if (editBtn) {
      editBtn.addEventListener('click', () => {
        if (this.editModal) {
          this.editModal.toggleEditMode();
        }
      });
    }
    
    // Page navigation events
    window.addEventListener('navigateToPage', (e) => {
      this.pageNavigator.goToPage(e.detail.page);
    });

    // Content refresh events (when edits are made)
    window.addEventListener('contentUpdated', (e) => {
      // Refresh section information for chat
      this.reportRenderer.updateChatSectionInfo();
    });

    // Update navigation when sections change
    window.addEventListener('sectionsUpdated', (e) => {
      if (e.detail.sections) {
        this.pageNavigator.setSections(e.detail.sections);
      }
    });
  }

  /**
   * Show toast notification
   */
  showToast(message, type = 'info') {
    // Remove existing toast
    const existingToast = document.getElementById('toast-notification');
    if (existingToast) {
      existingToast.remove();
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.id = 'toast-notification';
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <div class="toast-content">
        <span class="toast-icon">${this.getToastIcon(type)}</span>
        <span class="toast-message">${message}</span>
        <button class="toast-close">×</button>
      </div>
    `;

    // Add styles
    toast.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 10001;
      min-width: 300px;
      max-width: 500px;
      background: white;
      border-radius: 8px;
      box-shadow: var(--shadow-card);
      border-left: 4px solid var(--${type === 'error' ? 'error' : type === 'warning' ? 'warning' : type === 'success' ? 'success' : 'info'});
      transform: translateX(100%);
      transition: transform 0.3s ease;
      font-family: var(--font-body);
    `;

    // Style toast content
    const toastContent = toast.querySelector('.toast-content');
    toastContent.style.cssText = `
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 16px;
    `;

    // Style close button
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.style.cssText = `
      background: none;
      border: none;
      font-size: 16px;
      cursor: pointer;
      padding: 0;
      margin-left: auto;
    `;

    // Add to page
    document.body.appendChild(toast);

    // Show toast
    setTimeout(() => {
      toast.style.transform = 'translateX(0)';
    }, 10);

    // Setup close functionality
    const closeToast = () => {
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => {
        if (toast.parentNode) {
          toast.parentNode.removeChild(toast);
        }
      }, 300);
    };

    closeBtn.addEventListener('click', closeToast);
    toast.addEventListener('click', (e) => {
      if (e.target === toast) closeToast();
    });

    // Auto-close after delay
    setTimeout(closeToast, type === 'error' ? 7000 : 4000);
  }

  /**
   * Get icon for toast type
   */
  getToastIcon(type) {
    const icons = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️'
    };
    return icons[type] || icons.info;
  }

  /**
   * Show error message
   */
  showError(message) {
    const pageContainer = document.getElementById('page-container');
    if (pageContainer) {
      pageContainer.innerHTML = `
        <div class="report-page active" style="display: flex; align-items: center; justify-content: center;">
          <div class="page-content" style="text-align: center; padding: 40px;">
            <h1 style="color: var(--error); margin-bottom: 16px;">Error Loading Report</h1>
            <p style="color: var(--text-secondary); margin-bottom: 24px;">${message}</p>
            <button onclick="window.location.reload()" style="
              padding: 12px 24px;
              background: var(--andzen-green);
              color: white;
              border: none;
              border-radius: 8px;
              cursor: pointer;
              font-weight: 500;
            ">Reload Page</button>
          </div>
        </div>
      `;
    }
  }

  /**
   * Refresh report content
   */
  async refreshReport() {
    try {
      this.showToast('Refreshing report...', 'info');
      
      // Clear current content
      const pageContainer = document.getElementById('page-container');
      if (pageContainer) {
        pageContainer.innerHTML = '<div class="report-page active" id="page-loading"><div class="page-content" style="display: flex; align-items: center; justify-content: center; min-height: 400px;"><p>Refreshing report...</p></div></div>';
      }

      // Reload content
      await this.loadReportContent();
      
      this.showToast('Report refreshed successfully', 'success');
      
    } catch (error) {
      console.error('Failed to refresh report:', error);
      this.showToast(`Failed to refresh report: ${error.message}`, 'error');
    }
  }

  /**
   * Get current viewer state
   */
  getViewerState() {
    return {
      reportId: this.reportId,
      currentPage: this.pageNavigator.getCurrentPage(),
      totalPages: this.pageNavigator.getTotalPages(),
      sections: this.reportRenderer.getSections(),
      quoteItems: this.quoteBuilder.getQuoteItems(),
      chatHistory: this.chatInterface.getChatHistory(),
      isInitialized: this.isInitialized
    };
  }

  /**
   * Get module references for debugging
   */
  getModules() {
    return {
      styleManager: this.styleManager,
      reportRenderer: this.reportRenderer,
      pageNavigator: this.pageNavigator,
      chatInterface: this.chatInterface,
      editModal: this.editModal,
      quoteBuilder: this.quoteBuilder,
      exportManager: this.exportManager
    };
  }

  /**
   * Cleanup resources
   */
  destroy() {
    // Remove event listeners and cleanup
    window.removeEventListener('showToast', this.setupToastNotifications);
    window.removeEventListener('navigateToPage', this.setupModuleEventListeners);
    window.removeEventListener('contentUpdated', this.setupModuleEventListeners);
    window.removeEventListener('sectionsUpdated', this.setupModuleEventListeners);
    
    this.isInitialized = false;
    console.log('Report viewer destroyed');
  }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
  console.log('Initializing modular report viewer...');
  window.reportViewer = new ReportViewer();
});

// Export for debugging
window.ReportViewer = ReportViewer;