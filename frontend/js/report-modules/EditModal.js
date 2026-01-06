/**
 * EditModal - Handles content editing functionality
 */
class EditModal {
  constructor() {
    this.reportId = null;
    this.editHistory = [];
    this.editHistoryIndex = -1;
    this.isEditModeEnabled = false;
  }

  /**
   * Initialize edit modal functionality
   */
  init(reportId) {
    this.reportId = reportId;
    this.setupEditMode();
    this.setupEventListeners();
  }

  /**
   * Setup event listeners for edit modal
   */
  setupEventListeners() {
    // Listen for edit modal requests
    window.addEventListener('showEditModal', (e) => {
      this.showEditModal(e.detail.content);
    });

    // Listen for undo/redo keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      if (e.ctrlKey || e.metaKey) {
        if (e.key === 'z' && !e.shiftKey) {
          e.preventDefault();
          this.undo();
        } else if ((e.key === 'z' && e.shiftKey) || e.key === 'y') {
          e.preventDefault();
          this.redo();
        }
      }
    });
  }

  /**
   * Setup edit mode controls
   */
  setupEditMode() {
    // Add edit mode toggle button if it doesn't exist
    const reportHeader = document.querySelector('.report-header');
    if (reportHeader && !document.querySelector('.edit-mode-toggle')) {
      const editToggle = document.createElement('button');
      editToggle.className = 'edit-mode-toggle btn-back';
      editToggle.innerHTML = '✏️ Edit Mode';
      editToggle.style.marginBottom = '8px';
      editToggle.addEventListener('click', () => this.toggleEditMode());
      reportHeader.appendChild(editToggle);
    }
  }

  /**
   * Toggle edit mode
   */
  toggleEditMode() {
    this.isEditModeEnabled = !this.isEditModeEnabled;
    const toggle = document.querySelector('.edit-mode-toggle');
    const pages = document.querySelectorAll('.report-page .page-content');
    
    if (this.isEditModeEnabled) {
      if (toggle) {
        toggle.innerHTML = '👁️ View Mode';
        toggle.style.background = 'var(--warning)';
        toggle.style.color = 'white';
        toggle.style.borderColor = 'var(--warning)';
      }
      
      // Make content editable
      pages.forEach(page => {
        page.contentEditable = true;
        page.style.outline = '2px dashed var(--warning)';
        page.style.outlineOffset = '4px';
      });
      
      this.showToast('Edit mode enabled. Click any content to edit.', 'info');
    } else {
      if (toggle) {
        toggle.innerHTML = '✏️ Edit Mode';
        toggle.style.background = '';
        toggle.style.color = '';
        toggle.style.borderColor = '';
      }
      
      // Disable content editing
      pages.forEach(page => {
        page.contentEditable = false;
        page.style.outline = '';
        page.style.outlineOffset = '';
      });
      
      this.showToast('Edit mode disabled.', 'info');
    }
  }

  /**
   * Show edit modal for content
   */
  showEditModal(content = '') {
    // Remove existing modal if present
    const existingModal = document.getElementById('edit-modal');
    if (existingModal) {
      existingModal.remove();
    }

    const modal = this.createEditModal(content);
    document.body.appendChild(modal);
    
    // Show modal with animation
    setTimeout(() => {
      modal.classList.add('show');
      const textarea = modal.querySelector('textarea');
      if (textarea) {
        textarea.focus();
      }
    }, 10);
  }

  /**
   * Create edit modal element
   */
  createEditModal(content = '') {
    const modal = document.createElement('div');
    modal.id = 'edit-modal';
    modal.className = 'edit-modal';
    modal.innerHTML = `
      <div class="edit-modal-backdrop"></div>
      <div class="edit-modal-content">
        <div class="edit-modal-header">
          <h3>Edit Content</h3>
          <button class="edit-modal-close">×</button>
        </div>
        <div class="edit-modal-body">
          <textarea class="edit-textarea" placeholder="Enter your content here...">${content}</textarea>
          <div class="edit-preview" style="display: none;">
            <h4>Preview:</h4>
            <div class="preview-content"></div>
          </div>
        </div>
        <div class="edit-modal-footer">
          <div class="edit-controls">
            <button class="btn-preview">👁️ Preview</button>
            <button class="btn-undo" ${this.editHistoryIndex <= 0 ? 'disabled' : ''}>↶ Undo</button>
            <button class="btn-redo" ${this.editHistoryIndex >= this.editHistory.length - 1 ? 'disabled' : ''}>↷ Redo</button>
          </div>
          <div class="edit-actions">
            <button class="btn-cancel">Cancel</button>
            <button class="btn-save-edit">Save Changes</button>
          </div>
        </div>
      </div>
      
      <style>
        .edit-modal {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          z-index: 10000;
          display: flex;
          align-items: center;
          justify-content: center;
          opacity: 0;
          visibility: hidden;
          transition: all 0.3s ease;
        }
        
        .edit-modal.show {
          opacity: 1;
          visibility: visible;
        }
        
        .edit-modal-backdrop {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: rgba(0, 0, 0, 0.6);
          backdrop-filter: blur(4px);
        }
        
        .edit-modal-content {
          background: white;
          border-radius: 16px;
          width: 90%;
          max-width: 800px;
          max-height: 90vh;
          position: relative;
          box-shadow: var(--shadow-page);
          overflow: hidden;
          transform: scale(0.9);
          transition: transform 0.3s ease;
        }
        
        .edit-modal.show .edit-modal-content {
          transform: scale(1);
        }
        
        .edit-modal-header {
          padding: 24px 24px 16px;
          border-bottom: 1px solid var(--page-border);
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .edit-modal-header h3 {
          margin: 0;
          font-size: 20px;
          font-weight: 600;
        }
        
        .edit-modal-close {
          background: none;
          border: none;
          font-size: 24px;
          cursor: pointer;
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
          transition: background 0.2s ease;
        }
        
        .edit-modal-close:hover {
          background: var(--page-border);
        }
        
        .edit-modal-body {
          padding: 24px;
          max-height: 60vh;
          overflow-y: auto;
        }
        
        .edit-textarea {
          width: 100%;
          min-height: 200px;
          padding: 16px;
          border: 1px solid var(--page-border);
          border-radius: 8px;
          font-family: var(--font-body);
          font-size: 14px;
          line-height: 1.6;
          resize: vertical;
        }
        
        .edit-textarea:focus {
          outline: none;
          border-color: var(--andzen-green);
        }
        
        .edit-preview {
          margin-top: 16px;
          padding: 16px;
          border: 1px solid var(--page-border);
          border-radius: 8px;
          background: var(--sidebar-bg);
        }
        
        .edit-preview h4 {
          margin: 0 0 12px 0;
          font-size: 14px;
          font-weight: 600;
        }
        
        .preview-content {
          font-size: 14px;
          line-height: 1.6;
        }
        
        .edit-modal-footer {
          padding: 16px 24px;
          border-top: 1px solid var(--page-border);
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: var(--sidebar-bg);
        }
        
        .edit-controls {
          display: flex;
          gap: 8px;
        }
        
        .edit-controls button {
          padding: 8px 12px;
          border: 1px solid var(--page-border);
          background: white;
          border-radius: 6px;
          cursor: pointer;
          font-size: 12px;
          transition: all 0.2s ease;
        }
        
        .edit-controls button:hover:not(:disabled) {
          border-color: var(--andzen-green);
          color: var(--andzen-green);
        }
        
        .edit-controls button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        
        .edit-actions {
          display: flex;
          gap: 8px;
        }
        
        .btn-cancel {
          padding: 10px 20px;
          border: 1px solid var(--page-border);
          background: white;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 500;
          transition: all 0.2s ease;
        }
        
        .btn-cancel:hover {
          background: var(--sidebar-bg);
        }
        
        .btn-save-edit {
          padding: 10px 20px;
          background: var(--andzen-green);
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 600;
          transition: all 0.2s ease;
        }
        
        .btn-save-edit:hover {
          background: var(--andzen-green-dark);
        }
      </style>
    `;

    // Setup modal event listeners
    this.setupModalEventListeners(modal);
    
    return modal;
  }

  /**
   * Setup modal event listeners
   */
  setupModalEventListeners(modal) {
    const closeBtn = modal.querySelector('.edit-modal-close');
    const cancelBtn = modal.querySelector('.btn-cancel');
    const saveBtn = modal.querySelector('.btn-save-edit');
    const previewBtn = modal.querySelector('.btn-preview');
    const undoBtn = modal.querySelector('.btn-undo');
    const redoBtn = modal.querySelector('.btn-redo');
    const backdrop = modal.querySelector('.edit-modal-backdrop');
    const textarea = modal.querySelector('.edit-textarea');

    // Close modal functions
    const closeModal = () => {
      modal.classList.remove('show');
      setTimeout(() => modal.remove(), 300);
    };

    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);
    backdrop.addEventListener('click', closeModal);

    // Preview toggle
    previewBtn.addEventListener('click', () => {
      const preview = modal.querySelector('.edit-preview');
      const previewContent = modal.querySelector('.preview-content');
      
      if (preview.style.display === 'none') {
        preview.style.display = 'block';
        previewContent.innerHTML = this.formatPreviewContent(textarea.value);
        previewBtn.textContent = '📝 Edit';
      } else {
        preview.style.display = 'none';
        previewBtn.textContent = '👁️ Preview';
      }
    });

    // Save changes
    saveBtn.addEventListener('click', () => {
      this.saveEdits(textarea.value);
      closeModal();
    });

    // Undo/Redo
    undoBtn.addEventListener('click', () => this.undo());
    redoBtn.addEventListener('click', () => this.redo());

    // Escape key to close
    modal.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeModal();
      }
    });
  }

  /**
   * Format content for preview
   */
  formatPreviewContent(content) {
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code style="background: rgba(0,0,0,0.1); padding: 2px 4px; border-radius: 3px;">$1</code>')
      .replace(/\n/g, '<br>');
  }

  /**
   * Save edits to history and apply changes
   */
  saveEdits(content) {
    // Save to history
    this.saveToHistory();
    
    // Apply changes to current page
    const activePage = document.querySelector('.report-page.active .page-content');
    if (activePage && this.isEditModeEnabled) {
      activePage.innerHTML = this.formatPreviewContent(content);
    }
    
    this.showToast('Changes saved successfully!', 'success');
  }

  /**
   * Save current state to history
   */
  saveToHistory() {
    const activePage = document.querySelector('.report-page.active .page-content');
    if (!activePage) return;

    // Remove future history if we're not at the end
    this.editHistory = this.editHistory.slice(0, this.editHistoryIndex + 1);
    
    // Add current state
    this.editHistory.push({
      pageId: document.querySelector('.report-page.active').id,
      content: activePage.innerHTML,
      timestamp: Date.now()
    });
    
    this.editHistoryIndex = this.editHistory.length - 1;
    
    // Limit history size
    if (this.editHistory.length > 50) {
      this.editHistory.shift();
      this.editHistoryIndex--;
    }
  }

  /**
   * Undo last edit
   */
  undo() {
    if (this.editHistoryIndex <= 0) {
      this.showToast('Nothing to undo', 'warning');
      return;
    }

    this.editHistoryIndex--;
    this.applyHistoryState();
    this.showToast('Undid last change', 'info');
  }

  /**
   * Redo last undone edit
   */
  redo() {
    if (this.editHistoryIndex >= this.editHistory.length - 1) {
      this.showToast('Nothing to redo', 'warning');
      return;
    }

    this.editHistoryIndex++;
    this.applyHistoryState();
    this.showToast('Redid change', 'info');
  }

  /**
   * Apply history state to current page
   */
  applyHistoryState() {
    if (this.editHistoryIndex < 0 || this.editHistoryIndex >= this.editHistory.length) {
      return;
    }

    const historyState = this.editHistory[this.editHistoryIndex];
    const pageElement = document.getElementById(historyState.pageId);
    
    if (pageElement) {
      const pageContent = pageElement.querySelector('.page-content');
      if (pageContent) {
        pageContent.innerHTML = historyState.content;
      }
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
   * Get edit history
   */
  getEditHistory() {
    return this.editHistory;
  }

  /**
   * Clear edit history
   */
  clearHistory() {
    this.editHistory = [];
    this.editHistoryIndex = -1;
    this.showToast('Edit history cleared', 'info');
  }
}

// Export for use
window.EditModal = EditModal;