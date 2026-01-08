/**
 * ExportManager - Handles report export functionality
 */
class ExportManager {
  constructor() {
    this.reportId = null;
    this.supportedFormats = ['pdf', 'word', 'html'];
  }

  /**
   * Initialize export manager
   */
  init(reportId) {
    this.reportId = reportId;
    this.setupExportButtons();
    this.setupBackButton();
  }

  /**
   * Setup export button event listeners
   */
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

  /**
   * Setup back button functionality
   */
  setupBackButton() {
    const backBtn = document.querySelector('.btn-back');
    if (backBtn) {
      backBtn.addEventListener('click', () => {
        this.navigateBack();
      });
    }
  }

  /**
   * Export report in specified format
   */
  async exportReport(format) {
    if (!this.reportId) {
      this.showToast('No report ID available', 'error');
      return;
    }

    if (!this.supportedFormats.includes(format)) {
      this.showToast(`Unsupported format: ${format}`, 'error');
      return;
    }

    const button = document.querySelector(`.btn-export.${format}`);
    const originalText = button ? button.innerHTML : '';

    try {
      // Update button state
      if (button) {
        button.disabled = true;
        button.innerHTML = `⏳ Exporting...`;
      }

      this.showToast(`Preparing ${format.toUpperCase()} export...`, 'info');

      // Get report data first
      const response = await fetch(`${window.API_BASE_URL}/api/audit/status/${this.reportId}`);
      if (!response.ok) throw new Error('Failed to get report info');
      
      const data = await response.json();
      let downloadUrl;
      
      // Check if export already exists
      if (format === 'pdf' && data.report_data?.pdf_url) {
        downloadUrl = data.report_data.pdf_url;
      } else if (format === 'word' && data.report_data?.word_url) {
        downloadUrl = data.report_data.word_url;
      } else if (format === 'html' && data.report_data?.html_url) {
        downloadUrl = data.report_data.html_url;
      }

      if (downloadUrl) {
        // Direct download if URL exists
        this.downloadFile(downloadUrl, format);
        this.showToast(`${format.toUpperCase()} export ready!`, 'success');
      } else {
        // Request new export generation
        await this.generateExport(format);
      }
      
    } catch (error) {
      console.error('Export error:', error);
      this.showToast(`Failed to export ${format.toUpperCase()}: ${error.message}`, 'error');
    } finally {
      // Restore button state
      if (button) {
        button.disabled = false;
        button.innerHTML = originalText;
      }
    }
  }

  /**
   * Generate new export
   */
  async generateExport(format) {
    const exportResponse = await fetch(`${window.API_BASE_URL}/api/audit/${this.reportId}/export/${format}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        report_id: this.reportId,
        format: format
      })
    });

    if (!exportResponse.ok) {
      const errorData = await exportResponse.json();
      throw new Error(errorData.detail || `Export generation failed`);
    }

    const exportData = await exportResponse.json();
    
    if (exportData.download_url) {
      this.downloadFile(exportData.download_url, format);
      this.showToast(`${format.toUpperCase()} export generated successfully!`, 'success');
    } else if (exportData.message) {
      // Async generation - show status
      this.showToast(exportData.message, 'info');
      this.pollExportStatus(format);
    } else {
      throw new Error('No download URL provided');
    }
  }

  /**
   * Poll export generation status
   */
  async pollExportStatus(format) {
    const maxAttempts = 30; // 30 attempts = 1.5 minutes max wait
    const pollInterval = 3000; // 3 seconds
    let attempts = 0;

    const poll = async () => {
      attempts++;
      
      try {
        const response = await fetch(`${window.API_BASE_URL}/api/audit/status/${this.reportId}`);
        if (!response.ok) return;
        
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
          this.downloadFile(downloadUrl, format);
          this.showToast(`${format.toUpperCase()} export ready!`, 'success');
          return;
        }

        if (attempts < maxAttempts) {
          setTimeout(poll, pollInterval);
        } else {
          this.showToast(`Export generation timed out. Please try again later.`, 'warning');
        }
      } catch (error) {
        console.error('Export polling error:', error);
        this.showToast(`Export status check failed: ${error.message}`, 'error');
      }
    };

    setTimeout(poll, pollInterval);
  }

  /**
   * Download file from URL
   */
  downloadFile(url, format) {
    try {
      // Create temporary download link
      const link = document.createElement('a');
      link.href = url;
      link.target = '_blank';
      
      // Set filename if possible
      const urlParts = url.split('/');
      const filename = urlParts[urlParts.length - 1];
      if (filename && filename.includes('.')) {
        link.download = filename;
      } else {
        // Generate filename based on report
        const timestamp = new Date().toISOString().split('T')[0];
        link.download = `audit-report-${this.reportId}-${timestamp}.${format}`;
      }
      
      // Trigger download
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
    } catch (error) {
      console.error('Download error:', error);
      // Fallback - open in new window
      window.open(url, '_blank');
    }
  }

  /**
   * Navigate back to dashboard
   */
  navigateBack() {
    try {
      // Check if there's a dashboard URL in session or use default
      const dashboardUrl = sessionStorage.getItem('dashboardUrl') || '/ui/';
      
      // Add confirmation if there are unsaved changes
      if (this.hasUnsavedChanges()) {
        const confirmLeave = confirm('You have unsaved changes. Are you sure you want to leave?');
        if (!confirmLeave) return;
      }
      
      window.location.href = dashboardUrl;
    } catch (error) {
      console.error('Navigation error:', error);
      window.location.href = '/ui/';
    }
  }

  /**
   * Check for unsaved changes
   */
  hasUnsavedChanges() {
    // Check if edit mode is active
    const editToggle = document.querySelector('.edit-mode-toggle');
    if (editToggle && editToggle.innerHTML.includes('View Mode')) {
      return true;
    }

    // Check if there are items in quote builder
    const quoteItems = document.querySelectorAll('.quote-item');
    if (quoteItems.length > 0) {
      return true;
    }

    // Check for any unsaved chat messages
    const chatInput = document.getElementById('chat-input');
    if (chatInput && chatInput.value.trim()) {
      return true;
    }

    return false;
  }

  /**
   * Generate custom export with options
   */
  async generateCustomExport(options = {}) {
    if (!this.reportId) {
      throw new Error('No report ID available');
    }

    const defaultOptions = {
      format: 'pdf',
      includeCharts: true,
      includeRecommendations: true,
      includeTechnicalDetails: false,
      brandingEnabled: true,
      pageSize: 'A4',
      orientation: 'portrait'
    };

    const exportOptions = { ...defaultOptions, ...options };

    try {
      const response = await fetch(`${window.API_BASE_URL}/api/audit/${this.reportId}/export/custom`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          report_id: this.reportId,
          options: exportOptions
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Custom export failed');
      }

      const data = await response.json();
      
      if (data.download_url) {
        this.downloadFile(data.download_url, exportOptions.format);
        this.showToast(`Custom ${exportOptions.format.toUpperCase()} export ready!`, 'success');
      } else {
        this.showToast(data.message || 'Export generation started', 'info');
      }

      return data;
    } catch (error) {
      this.showToast(`Custom export failed: ${error.message}`, 'error');
      throw error;
    }
  }

  /**
   * Get export history
   */
  async getExportHistory() {
    if (!this.reportId) return [];

    try {
      const response = await fetch(`${window.API_BASE_URL}/api/audit/${this.reportId}/export/history`);
      if (!response.ok) return [];

      const data = await response.json();
      return data.exports || [];
    } catch (error) {
      console.error('Failed to get export history:', error);
      return [];
    }
  }

  /**
   * Show export options modal
   */
  showExportOptions() {
    // This could be expanded to show a modal with export customization options
    const options = {
      format: 'pdf',
      includeCharts: true,
      includeRecommendations: true,
      brandingEnabled: true
    };

    this.generateCustomExport(options);
  }

  /**
   * Show toast notification
   */
  showToast(message, type = 'info') {
    // Emit event for main UI to handle
    window.dispatchEvent(new CustomEvent('showToast', {
      detail: { message, type }
    }));
  }

  /**
   * Get supported export formats
   */
  getSupportedFormats() {
    return [...this.supportedFormats];
  }

  /**
   * Check if format is supported
   */
  isFormatSupported(format) {
    return this.supportedFormats.includes(format.toLowerCase());
  }
}

// Export for use
window.ExportManager = ExportManager;