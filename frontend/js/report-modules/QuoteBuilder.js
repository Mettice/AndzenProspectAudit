/**
 * QuoteBuilder - Handles quote generation and management
 */
class QuoteBuilder {
  constructor() {
    this.reportId = null;
    this.quoteItems = [];
  }

  /**
   * Initialize quote builder
   */
  init(reportId) {
    this.reportId = reportId;
    this.setupQuoteBuilder();
    this.setupEventListeners();
  }

  /**
   * Setup event listeners for quote builder
   */
  setupEventListeners() {
    // Listen for add to quote requests
    window.addEventListener('addToQuote', (e) => {
      this.addQuoteItem(e.detail.content);
    });
  }

  /**
   * Setup quote builder interface
   */
  setupQuoteBuilder() {
    const generateBtn = document.querySelector('.btn-generate-quote');
    
    if (generateBtn) {
      generateBtn.addEventListener('click', () => this.generateQuoteDocument());
    }

    // Setup remove buttons using event delegation
    const quoteContainer = document.getElementById('quote-items');
    if (quoteContainer) {
      quoteContainer.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-remove')) {
          const quoteItem = e.target.closest('.quote-item');
          if (quoteItem) {
            const itemId = quoteItem.dataset.itemId;
            this.removeQuoteItem(itemId);
          }
        }
      });
    }
  }

  /**
   * Add item to quote
   */
  addQuoteItem(content, effort = null, impact = null) {
    // Check for duplicates - compare content (normalized)
    const normalizedContent = content.trim().toLowerCase().substring(0, 100); // First 100 chars for comparison
    const isDuplicate = this.quoteItems.some(item => {
      const itemContent = (item.content || '').trim().toLowerCase().substring(0, 100);
      return itemContent === normalizedContent;
    });
    
    if (isDuplicate) {
      this.showToast('This item is already in the quote', 'warning');
      return;
    }
    
    const item = {
      id: Date.now().toString(),
      content: content,
      effort: effort || this.estimateEffort(content),
      impact: impact || this.estimateImpact(content),
      timestamp: Date.now()
    };

    this.quoteItems.push(item);
    this.updateQuoteDisplay();
    this.updateQuoteTotals();
    
    this.showToast(`Added item to quote`, 'success');
  }

  /**
   * Remove item from quote
   */
  removeQuoteItem(itemId) {
    const index = this.quoteItems.findIndex(item => item.id === itemId);
    if (index === -1) return;

    const removedItem = this.quoteItems.splice(index, 1)[0];
    this.updateQuoteDisplay();
    this.updateQuoteTotals();
    
    this.showToast(`Removed "${removedItem.title || 'item'}" from quote`, 'info');
  }

  /**
   * Update quote display in UI
   */
  updateQuoteDisplay() {
    const quoteContainer = document.getElementById('quote-items');
    if (!quoteContainer) return;

    if (this.quoteItems.length === 0) {
      quoteContainer.innerHTML = `
        <div class="quote-empty" style="padding: 20px; color: var(--text-muted); text-align: center;">
          <p>No items in quote yet.</p>
          <p style="font-size: 12px; margin-top: 8px;">Add items by clicking "Add to Quote" in the chat.</p>
        </div>
      `;
      return;
    }

    let html = '';
    this.quoteItems.forEach(item => {
      html += this.createQuoteItemHTML(item);
    });

    quoteContainer.innerHTML = html;
  }

  /**
   * Create HTML for quote item
   */
  createQuoteItemHTML(item) {
    const title = item.title || this.extractTitle(item.content);
    const description = item.description || this.extractDescription(item.content);
    
    return `
      <div class="quote-item" data-item-id="${item.id}">
        <div class="quote-icon">${this.getItemIcon(item)}</div>
        <div class="quote-details">
          <h4>${title}</h4>
          <p>${description}</p>
          <div class="quote-value">
            <span class="effort">⏱️ ${item.effort} hours</span>
            <span class="impact">💰 $${item.impact}/mo</span>
          </div>
        </div>
        <button class="btn-remove">×</button>
      </div>
    `;
  }

  /**
   * Extract title from content
   */
  extractTitle(content) {
    // Extract the first line or sentence as title
    const lines = content.split('\n');
    const firstLine = lines[0].trim();
    
    // If first line looks like a title (short and ends with colon or is standalone)
    if (firstLine.length < 60 && (firstLine.endsWith(':') || lines.length > 1)) {
      return firstLine.replace(':', '');
    }
    
    // Extract first sentence
    const sentences = content.split(/[.!?]+/);
    const firstSentence = sentences[0].trim();
    
    if (firstSentence.length < 80) {
      return firstSentence;
    }
    
    // Fallback to truncated content
    return content.substring(0, 50) + '...';
  }

  /**
   * Extract description from content
   */
  extractDescription(content) {
    // Remove the title part and get remaining content
    const lines = content.split('\n');
    const firstLine = lines[0].trim();
    
    let description = content;
    
    if (firstLine.length < 60 && (firstLine.endsWith(':') || lines.length > 1)) {
      description = lines.slice(1).join(' ').trim();
    } else {
      // Skip first sentence if it's being used as title
      const sentences = content.split(/[.!?]+/);
      if (sentences[0].trim().length < 80) {
        description = sentences.slice(1).join('.').trim();
      }
    }
    
    // Clean and truncate description
    description = description.replace(/^\s*[.-]\s*/, '').trim();
    
    if (description.length > 120) {
      description = description.substring(0, 120) + '...';
    }
    
    return description || 'Strategic improvement recommendation';
  }

  /**
   * Get icon for quote item based on content
   */
  getItemIcon(item) {
    const content = item.content.toLowerCase();
    
    if (content.includes('email') || content.includes('campaign')) return '📧';
    if (content.includes('automation') || content.includes('flow')) return '⚙️';
    if (content.includes('segment') || content.includes('list')) return '👥';
    if (content.includes('analytics') || content.includes('tracking')) return '📊';
    if (content.includes('form') || content.includes('signup')) return '📝';
    if (content.includes('design') || content.includes('template')) return '🎨';
    if (content.includes('integration') || content.includes('api')) return '🔗';
    if (content.includes('strategy') || content.includes('planning')) return '🎯';
    
    return '💡';
  }

  /**
   * Estimate effort for content
   */
  estimateEffort(content) {
    const length = content.length;
    const complexity = this.analyzeComplexity(content);
    
    // Base hours based on content length and complexity
    let hours = Math.ceil(length / 100) * complexity;
    
    // Minimum 2 hours, maximum 40 hours
    return Math.min(Math.max(hours, 2), 40);
  }

  /**
   * Estimate monthly impact for content
   */
  estimateImpact(content) {
    const content_lower = content.toLowerCase();
    let baseImpact = 500; // Base monthly impact
    
    // Increase impact based on content type
    if (content_lower.includes('automation') || content_lower.includes('flow')) {
      baseImpact *= 2;
    }
    if (content_lower.includes('email') || content_lower.includes('campaign')) {
      baseImpact *= 1.5;
    }
    if (content_lower.includes('segment') || content_lower.includes('personalization')) {
      baseImpact *= 1.8;
    }
    if (content_lower.includes('analytics') || content_lower.includes('tracking')) {
      baseImpact *= 1.3;
    }
    
    // Add randomness to make it feel more realistic
    const randomMultiplier = 0.8 + Math.random() * 0.4; // 0.8 to 1.2
    baseImpact *= randomMultiplier;
    
    // Round to nearest 50
    return Math.round(baseImpact / 50) * 50;
  }

  /**
   * Analyze content complexity
   */
  analyzeComplexity(content) {
    const content_lower = content.toLowerCase();
    let complexity = 1;
    
    // Technical terms increase complexity
    const technicalTerms = [
      'integration', 'api', 'webhook', 'segmentation', 'automation',
      'analytics', 'attribution', 'personalization', 'a/b testing'
    ];
    
    technicalTerms.forEach(term => {
      if (content_lower.includes(term)) {
        complexity += 0.5;
      }
    });
    
    // Multiple sentences or bullet points indicate complexity
    if (content.split('\n').length > 3) {
      complexity += 0.5;
    }
    
    return Math.min(complexity, 3); // Cap at 3x complexity
  }

  /**
   * Update quote totals
   */
  updateQuoteTotals() {
    const totalEffort = this.quoteItems.reduce((sum, item) => sum + item.effort, 0);
    const totalImpact = this.quoteItems.reduce((sum, item) => sum + item.impact, 0);

    const effortEl = document.getElementById('total-effort');
    const impactEl = document.getElementById('total-impact');

    if (effortEl) effortEl.textContent = `${totalEffort} hours`;
    if (impactEl) impactEl.textContent = `$${totalImpact.toLocaleString()}`;

    // Update generate button state
    const generateBtn = document.querySelector('.btn-generate-quote');
    if (generateBtn) {
      generateBtn.disabled = this.quoteItems.length === 0;
      generateBtn.textContent = this.quoteItems.length === 0 
        ? 'Generate Full Proposal' 
        : `Generate Proposal (${this.quoteItems.length} items)`;
    }
  }

  /**
   * Generate quote document
   */
  async generateQuoteDocument() {
    if (this.quoteItems.length === 0) {
      this.showToast('Add items to your quote first', 'warning');
      return;
    }

    if (!this.reportId) {
      this.showToast('No report ID available', 'error');
      return;
    }

    try {
      const generateBtn = document.querySelector('.btn-generate-quote');
      if (generateBtn) {
        generateBtn.disabled = true;
        generateBtn.textContent = 'Generating...';
      }

      const response = await fetch(`${window.API_BASE_URL}/api/audit/${this.reportId}/quote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          items: this.quoteItems,
          report_id: this.reportId
        })
      });

      if (!response.ok) {
        throw new Error('Failed to generate quote');
      }

      const data = await response.json();
      
      if (data.quote_url) {
        window.open(data.quote_url, '_blank');
        this.showToast('Quote generated successfully!', 'success');
      } else {
        throw new Error('No quote URL returned');
      }
      
    } catch (error) {
      console.error('Quote generation error:', error);
      this.showToast(`Failed to generate quote: ${error.message}`, 'error');
    } finally {
      const generateBtn = document.querySelector('.btn-generate-quote');
      if (generateBtn) {
        generateBtn.disabled = false;
        this.updateQuoteTotals(); // Restore button text
      }
    }
  }

  /**
   * Clear all quote items
   */
  clearQuote() {
    this.quoteItems = [];
    this.updateQuoteDisplay();
    this.updateQuoteTotals();
    this.showToast('Quote cleared', 'info');
  }

  /**
   * Export quote data
   */
  exportQuoteData() {
    return {
      items: this.quoteItems,
      totals: {
        effort: this.quoteItems.reduce((sum, item) => sum + item.effort, 0),
        impact: this.quoteItems.reduce((sum, item) => sum + item.impact, 0)
      },
      reportId: this.reportId,
      timestamp: Date.now()
    };
  }

  /**
   * Import quote data
   */
  importQuoteData(data) {
    if (data.items && Array.isArray(data.items)) {
      this.quoteItems = data.items;
      this.updateQuoteDisplay();
      this.updateQuoteTotals();
      this.showToast(`Imported ${data.items.length} quote items`, 'success');
    }
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
   * Get quote items
   */
  getQuoteItems() {
    return this.quoteItems;
  }

  /**
   * Get quote totals
   */
  getQuoteTotals() {
    return {
      effort: this.quoteItems.reduce((sum, item) => sum + item.effort, 0),
      impact: this.quoteItems.reduce((sum, item) => sum + item.impact, 0),
      itemCount: this.quoteItems.length
    };
  }
}

// Export for use
window.QuoteBuilder = QuoteBuilder;