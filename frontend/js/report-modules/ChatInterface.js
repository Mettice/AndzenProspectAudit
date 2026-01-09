/**
 * ChatInterface - Handles AI chat functionality and message management
 */
class ChatInterface {
  constructor() {
    this.reportId = null;
    this.chatHistory = [];
    this.isProcessing = false;
  }

  /**
   * Initialize chat interface
   */
  init(reportId) {
    this.reportId = reportId;
    this.setupChatInterface();
    this.setupEditRequestButtons();
    this.loadChatHistory();
  }

  /**
   * Setup chat interface event listeners
   */
  setupChatInterface() {
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.querySelector('.btn-send');
    const clearBtn = document.getElementById('btn-clear-chat');

    const sendMessage = async () => {
      const message = chatInput.value.trim();
      if (!message || this.isProcessing) return;

      this.addChatMessage('user', message);
      chatInput.value = '';
      
      // Disable input while processing
      this.setProcessingState(true);

      try {
        await this.sendChatMessageToAPI(message);
      } catch (error) {
        console.error('Chat error:', error);
        
        // Show retry option for failed messages
        const retryActions = `
          <button class="btn-retry-chat" onclick="window.reportViewer.getModules().chatInterface.retryLastMessage('${message.replace(/'/g, "\\'")}')">🔄 Retry</button>
        `;
        
        this.addChatMessage('assistant', `Sorry, I encountered an error: ${error.message}. Please try again.`, retryActions);
      } finally {
        this.setProcessingState(false);
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

    // Clear chat button
    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        if (confirm('Clear all chat messages? This cannot be undone.')) {
          this.clearChatHistory();
        }
      });
    }
  }

  /**
   * Set processing state for UI
   */
  setProcessingState(processing) {
    this.isProcessing = processing;
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.querySelector('.btn-send');
    const messagesContainer = document.getElementById('chat-messages');

    if (chatInput) chatInput.disabled = processing;
    if (sendBtn) sendBtn.disabled = processing;
    
    // Show/hide loading indicator
    let loadingIndicator = document.getElementById('chat-loading-indicator');
    if (processing) {
      if (!loadingIndicator) {
        loadingIndicator = document.createElement('div');
        loadingIndicator.id = 'chat-loading-indicator';
        loadingIndicator.className = 'message assistant loading';
        loadingIndicator.innerHTML = `
          <div class="message-avatar">🤖</div>
          <div class="message-content">
            <div class="loading-dots">
              <span></span><span></span><span></span>
            </div>
            <span style="margin-left: 8px; color: #999;">Analyzing report...</span>
          </div>
        `;
        if (messagesContainer) {
          messagesContainer.appendChild(loadingIndicator);
          messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
      }
    } else {
      if (loadingIndicator) {
        loadingIndicator.remove();
      }
    }
    
    if (!processing && chatInput) {
      chatInput.focus();
    }
  }

  /**
   * Send chat message to API
   */
  async sendChatMessageToAPI(message) {
    if (!this.reportId) {
      throw new Error('No report ID available');
    }

    console.log('Sending chat message to API:', message);
    
    // Prepare comprehensive request data with full context
    // NOTE: report_id is in the URL path, not in the body
    const requestData = {
      message: message,
      context_type: 'full_report', // Indicate we're sending full context
    };
    
    // Add comprehensive context for intelligent responses
    if (window.reportSections) {
      const fullContext = window.reportSections.getFullContext ? window.reportSections.getFullContext() : null;
      
      if (fullContext) {
        // Send comprehensive context including full content
        requestData.full_context = {
          report_summary: fullContext.summary || [],
          available_sections: fullContext.sections || [],
          total_pages: fullContext.totalPages || 0,
          content_preview: fullContext.content ? fullContext.content.slice(0, 20) : [] // Send first 20 pages
        };
      }
      
      // Also send full content if available (for better context)
      if (window.reportSections && window.reportSections.fullContent) {
        requestData.full_context = requestData.full_context || {};
        requestData.full_context.full_content = window.reportSections.fullContent.slice(0, 30); // First 30 pages
        console.log(`✓ Sending full content context: ${window.reportSections.fullContent.length} pages available, sending ${Math.min(30, window.reportSections.fullContent.length)}`);
      }
      
      // Also include specific section mapping for backend reference
      if (window.reportSections.available) {
        requestData.available_sections = window.reportSections.available;
      }
      
      // Log what we're sending for debugging
      if (requestData.full_context) {
        console.log('📤 Chat context being sent:', {
          has_full_content: !!requestData.full_context.full_content,
          full_content_pages: requestData.full_context.full_content?.length || 0,
          has_summary: !!requestData.full_context.report_summary,
          summary_items: requestData.full_context.report_summary?.length || 0,
          available_sections: requestData.available_sections?.length || 0,
          has_system_context: !!requestData.system_context
        });
      } else {
        console.warn('⚠️ No report sections available - chat will have limited context. window.reportSections:', !!window.reportSections);
      }
      
      // Add system prompt context for the AI
      requestData.system_context = {
        role: "You are an expert email marketing auditor and strategist. You have access to the complete audit report for this client. When answering questions, reference specific sections, provide actionable insights, and offer strategic recommendations based on the data shown.",
        capabilities: [
          "Answer questions about specific sections (KAV, Executive Summary, Strategic Recommendations, etc.)",
          "Provide strategic insights and recommendations",
          "Reference specific data points and metrics from the audit", 
          "Suggest improvements and action items",
          "Help with content editing and modifications"
        ],
        guidelines: [
          "Always reference specific sections when answering",
          "Provide actionable, stakeholder-focused recommendations",
          "Use data from the audit to support your responses",
          "Be professional and strategic in your communication style",
          "When editing content, maintain the professional audit tone"
        ]
      };
    }

    const response = await fetch(`${window.API_BASE_URL}/api/audit/${this.reportId}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Chat request failed');
    }

    const data = await response.json();
    console.log('Chat response received:', data);
    
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

  /**
   * Load chat history from API
   */
  async loadChatHistory() {
    if (!this.reportId) return;

    try {
      const response = await fetch(`${window.API_BASE_URL}/api/audit/${this.reportId}/chat/history`);
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
            this.addChatMessage(msg.role, msg.message, actions);
          });
        }
      }
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
  }

  /**
   * Add message to chat interface
   */
  addChatMessage(role, content, actions = null) {
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;

    const messageEl = document.createElement('div');
    messageEl.className = `message ${role}`;
    
    const avatar = role === 'user' ? '👤' : '🤖';
    const formattedContent = this.formatChatContent(content);
    
    messageEl.innerHTML = `
      <div class="message-avatar">${avatar}</div>
      <div class="message-content">
        ${formattedContent}
        ${actions ? `<div class="message-actions">${actions}</div>` : ''}
      </div>
    `;
    
    messagesContainer.appendChild(messageEl);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Re-setup edit request buttons for new messages
    this.setupEditRequestButtons();
  }

  /**
   * Escape HTML to prevent XSS and syntax errors
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Format chat content with proper styling
   */
  formatChatContent(content) {
    if (!content) return '';
    
    // First escape HTML to prevent XSS and syntax errors
    let escaped = this.escapeHtml(content);
    
    // Handle markdown-style formatting (after escaping)
    let formatted = escaped
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code style="background: rgba(0,0,0,0.1); padding: 2px 4px; border-radius: 3px;">$1</code>')
      .replace(/\n/g, '<br>');
    
    // Handle headers (## Header or ### Header)
    formatted = formatted
      .replace(/###\s+(.+?)(<br>|$)/g, '<h3 style="margin: 12px 0 8px 0; font-size: 16px; font-weight: 600;">$1</h3>')
      .replace(/##\s+(.+?)(<br>|$)/g, '<h2 style="margin: 16px 0 10px 0; font-size: 18px; font-weight: 700;">$1</h2>')
      .replace(/#\s+(.+?)(<br>|$)/g, '<h1 style="margin: 20px 0 12px 0; font-size: 20px; font-weight: 700;">$1</h1>');
    
    // Handle numbered lists (1. item or 1) item)
    formatted = formatted.replace(/(\d+[.)]\s+)(.+?)(<br>|$)/g, (match, num, text, br) => {
      return `<ol style="margin: 8px 0; padding-left: 24px; list-style-type: decimal;">${text}</ol>`;
    });
    
    // Handle bullet lists
    const lines = formatted.split('<br>');
    let inList = false;
    let result = '';
    
    for (let line of lines) {
      const trimmed = line.trim();
      // Check for bullet points (-, *, •)
      if (trimmed.match(/^[-*•]\s+/)) {
        if (!inList) {
          result += '<ul style="margin: 8px 0; padding-left: 20px; list-style-type: disc;">';
          inList = true;
        }
        result += `<li style="margin: 4px 0;">${trimmed.replace(/^[-*•]\s+/, '')}</li>`;
      } else {
        if (inList) {
          result += '</ul>';
          inList = false;
        }
        if (trimmed) {
          // Wrap in paragraph if not already a header
          if (!trimmed.startsWith('<h') && !trimmed.startsWith('<ul') && !trimmed.startsWith('<ol')) {
            result += `<p style="margin: 6px 0; line-height: 1.6;">${line}</p>`;
          } else {
            result += line;
          }
        }
      }
    }
    
    if (inList) {
      result += '</ul>';
    }
    
    formatted = result;
    
    return formatted;
  }

  /**
   * Setup edit request button functionality
   */
  setupEditRequestButtons() {
    // Use event delegation for dynamically created buttons
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;

    // Remove existing listeners to prevent duplicates
    messagesContainer.removeEventListener('click', this.handleMessageActions);
    messagesContainer.addEventListener('click', this.handleMessageActions.bind(this));
  }

  /**
   * Handle message action button clicks
   */
  handleMessageActions(e) {
    if (e.target.classList.contains('btn-edit-request')) {
      const messageContent = e.target.closest('.message-content');
      if (messageContent) {
        const content = messageContent.textContent.trim();
        this.requestEdit(content);
      }
    } else if (e.target.classList.contains('btn-add-quote')) {
      const messageContent = e.target.closest('.message-content');
      if (messageContent) {
        const content = messageContent.textContent.trim();
        this.addToQuote(content);
      }
    }
  }

  /**
   * Request edit for content - now uses inline editing
   */
  requestEdit(content) {
    // Enable inline editing mode instead of modal
    if (window.reportViewer && window.reportViewer.getModules().editModal) {
      const editModal = window.reportViewer.getModules().editModal;
      // Use toggleEditMode if available, otherwise use basic inline editing
      if (editModal.toggleEditMode && !editModal.isEditModeEnabled) {
        editModal.toggleEditMode();
        this.addChatMessage('assistant', '✏️ Edit mode enabled! Click any content on the current page to edit it directly. Click "Edit Mode" again when you\'re done to save changes.');
      } else {
        // Fallback to basic editing mode
        this.enableBasicInlineEditing();
      }
    } else {
      // Fallback to basic editing mode
      this.enableBasicInlineEditing();
    }
  }

  /**
   * Add content to quote builder
   */
  addToQuote(content) {
    // Emit event for quote builder
    window.dispatchEvent(new CustomEvent('addToQuote', {
      detail: { content: content }
    }));
  }

  /**
   * Handle navigation actions from chat responses
   */
  handleNavigationActions(actions) {
    actions.forEach(action => {
      if (action.type === 'go_to_page' && action.page) {
        // Emit event for page navigation
        window.dispatchEvent(new CustomEvent('navigateToPage', {
          detail: { page: action.page }
        }));
      } else if (action.type === 'scroll_to_section' && action.section) {
        this.scrollToSection(action.section);
      }
    });
  }

  /**
   * Scroll to specific section
   */
  scrollToSection(sectionName) {
    if (!window.reportSections || !window.reportSections.findSection) {
      console.warn('Report sections not available for navigation');
      return;
    }

    const sectionContent = window.reportSections.findSection(sectionName);
    if (sectionContent) {
      // Find the page containing this section
      const sections = window.reportSections.map;
      for (const [sectionId, pages] of Object.entries(sections)) {
        if (sectionId.toLowerCase().includes(sectionName.toLowerCase()) || 
            sectionName.toLowerCase().includes(sectionId.toLowerCase())) {
          if (pages.length > 0) {
            window.dispatchEvent(new CustomEvent('navigateToPage', {
              detail: { page: pages[0].pageNumber }
            }));
            break;
          }
        }
      }
    }
  }

  /**
   * Get chat history
   */
  getChatHistory() {
    return this.chatHistory;
  }

  /**
   * Clear chat history (UI only)
   */
  clearChatHistory() {
    const messagesContainer = document.getElementById('chat-messages');
    if (messagesContainer) {
      messagesContainer.innerHTML = '';
      this.chatHistory = [];
      this.addChatMessage('assistant', 'Chat cleared. How can I help you with this audit?');
    }
  }

  /**
   * Retry last failed message
   */
  async retryLastMessage(message) {
    console.log('Retrying message:', message);
    this.setProcessingState(true);
    
    try {
      await this.sendChatMessageToAPI(message);
    } catch (error) {
      console.error('Retry failed:', error);
      this.addChatMessage('assistant', `Retry failed: ${error.message}. Please check your connection and try again.`);
    } finally {
      this.setProcessingState(false);
    }
  }

  /**
   * Enable basic inline editing mode
   */
  enableBasicInlineEditing() {
    const activePage = document.querySelector('.report-page.active .page-content');
    if (!activePage) {
      this.addChatMessage('assistant', '❌ No active page found for editing.');
      return;
    }

    // Toggle editing mode
    const isEditable = activePage.contentEditable === 'true';
    
    if (!isEditable) {
      // Enable editing
      activePage.contentEditable = true;
      activePage.style.outline = '2px dashed #65DA4F';
      activePage.style.outlineOffset = '4px';
      activePage.style.backgroundColor = 'rgba(101, 218, 79, 0.05)';
      
      // Add editing instructions
      const editInstructions = document.createElement('div');
      editInstructions.id = 'edit-instructions';
      editInstructions.style.cssText = `
        position: fixed;
        top: 20px;
        right: 380px;
        background: #65DA4F;
        color: white;
        padding: 10px 15px;
        border-radius: 8px;
        font-size: 14px;
        z-index: 1000;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
      `;
      editInstructions.innerHTML = '✏️ Editing Mode Active - Click text to edit, then click "Save Changes" in chat when done';
      document.body.appendChild(editInstructions);
      
      this.addChatMessage('assistant', '✅ Inline editing enabled! You can now click and edit content directly on the page. When you\'re done, I\'ll provide a "Save Changes" button.');
      
      // Add save option to next assistant message
      setTimeout(() => {
        const saveActions = `<button class="btn-save-inline" onclick="window.reportViewer.getModules().chatInterface.saveInlineEdits()">💾 Save Changes</button>`;
        this.addChatMessage('assistant', '👆 When you\'re finished editing, click the button below to save your changes:', saveActions);
      }, 1000);
      
    } else {
      // Disable editing mode
      this.disableInlineEditing();
    }
  }

  /**
   * Save inline edits
   */
  saveInlineEdits() {
    const activePage = document.querySelector('.report-page.active .page-content');
    if (!activePage) return;

    // Disable editing
    this.disableInlineEditing();
    
    // Show success message
    this.addChatMessage('assistant', '✅ Changes saved successfully! Your edits have been applied to the current page.');
    
    // Emit event to update other systems
    window.dispatchEvent(new CustomEvent('contentUpdated', {
      detail: { 
        pageContent: activePage.innerHTML,
        timestamp: Date.now()
      }
    }));
  }

  /**
   * Disable inline editing mode
   */
  disableInlineEditing() {
    const activePage = document.querySelector('.report-page.active .page-content');
    if (activePage) {
      activePage.contentEditable = false;
      activePage.style.outline = '';
      activePage.style.outlineOffset = '';
      activePage.style.backgroundColor = '';
    }

    // Remove instructions
    const instructions = document.getElementById('edit-instructions');
    if (instructions) {
      instructions.remove();
    }
  }
}

// Export for use
window.ChatInterface = ChatInterface;