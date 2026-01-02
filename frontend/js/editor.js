/**
 * Report Editor Module
 * Handles editable report display and editing functionality
 */

(function() {
  'use strict';

  let currentReportId = null;
  let isEditMode = false;
  let undoStack = [];
  let redoStack = [];
  let maxHistorySize = 50;

  // Initialize report editor
  function initReportEditor(reportId, htmlContent, filename, downloadButtons) {
    currentReportId = reportId;

    const resultBox = document.getElementById('result-box');
    if (!resultBox) return;

    // Create editable report + chat layout
    resultBox.innerHTML = `
      <div class="success-box">
        <p class="label">Report Generated Successfully</p>
        <p class="value">${filename}</p>
        ${downloadButtons}
      </div>
      <div class="report-chat-layout">
        <!-- Left Sidebar: Chat Widget -->
        <div class="left-sidebar">
          <div class="chat-widget-card" id="chat-widget-card">
            <div class="chat-widget-header">
              <span class="chat-icon">💬</span>
              <h3>Chat with AI</h3>
            </div>
            <div class="chat-messages" id="chat-messages"></div>
            <div class="chat-input-container">
              <div class="chat-input-wrapper">
                <input 
                  type="text" 
                  id="chat-input" 
                  placeholder="Ask about the report..."
                />
                <button id="send-chat-btn" class="btn-send-chat">Send</button>
              </div>
              <button id="generate-quote-btn" class="btn-generate-quote" title="Generate quote">
                <span class="quote-icon">💼</span>
                <span class="quote-text">Quote</span>
              </button>
            </div>
          </div>
          
          <!-- Formatting Widget -->
          <div class="formatting-widget-card" id="formatting-widget-card" style="display: none;">
            <div class="formatting-widget-header">
              <span class="format-icon">🎨</span>
              <h3>Formatting</h3>
            </div>
            <div class="formatting-widget-content">
              <div class="format-row">
                <label>Font Family</label>
                <select id="font-family" class="format-select" title="Font Family">
                  <option value="Montserrat">Montserrat</option>
                  <option value="Arial">Arial</option>
                  <option value="Helvetica">Helvetica</option>
                  <option value="Georgia">Georgia</option>
                  <option value="Times New Roman">Times New Roman</option>
                  <option value="Courier New">Courier New</option>
                  <option value="Verdana">Verdana</option>
                </select>
              </div>
              <div class="format-row">
                <label>Font Size</label>
                <select id="font-size" class="format-select" title="Font Size">
                  <option value="10px">10px</option>
                  <option value="12px">12px</option>
                  <option value="14px" selected>14px</option>
                  <option value="16px">16px</option>
                  <option value="18px">18px</option>
                  <option value="20px">20px</option>
                  <option value="24px">24px</option>
                  <option value="28px">28px</option>
                  <option value="32px">32px</option>
                </select>
              </div>
              <div class="format-row">
                <label>Text Style</label>
                <div class="format-buttons-group">
                  <button class="format-btn-small" data-command="bold" title="Bold">B</button>
                  <button class="format-btn-small" data-command="italic" title="Italic">I</button>
                  <button class="format-btn-small" data-command="underline" title="Underline">U</button>
                </div>
              </div>
              <div class="format-row">
                <label>Colors</label>
                <div class="color-inputs-group">
                  <div class="color-input-wrapper">
                    <label for="text-color" class="color-label-small">Text</label>
                    <input type="color" id="text-color" class="format-color-small" value="#000000">
                  </div>
                  <div class="color-input-wrapper">
                    <label for="bg-color" class="color-label-small">Bg</label>
                    <input type="color" id="bg-color" class="format-color-small" value="#ffffff">
                  </div>
                </div>
              </div>
              <div class="format-row">
                <label>Alignment</label>
                <div class="format-buttons-group">
                  <button class="format-btn-small" data-command="justifyLeft" title="Left">⬅</button>
                  <button class="format-btn-small" data-command="justifyCenter" title="Center">⬌</button>
                  <button class="format-btn-small" data-command="justifyRight" title="Right">➡</button>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Center: Report Editor -->
        <div class="report-editor-panel">
          <div class="editor-toolbar">
            <div class="toolbar-left">
              <button id="edit-mode-toggle" class="btn-edit-mode">
                <span class="btn-icon">✏️</span>
                <span class="btn-text">Edit Mode</span>
              </button>
              <div class="toolbar-divider"></div>
              <button id="undo-btn" class="btn-toolbar" title="Undo (Ctrl+Z)" disabled>
                <span class="btn-icon">↶</span>
                <span class="btn-text">Undo</span>
              </button>
              <button id="redo-btn" class="btn-toolbar" title="Redo (Ctrl+Y)" disabled>
                <span class="btn-icon">↷</span>
                <span class="btn-text">Redo</span>
              </button>
              <div class="toolbar-divider"></div>
              <button id="toggle-formatting-widget" class="btn-toolbar" title="Show Formatting">
                <span class="btn-icon">🎨</span>
                <span class="btn-text">Format</span>
              </button>
            </div>
            <div class="toolbar-right">
              <button id="export-btn" class="btn-toolbar btn-primary" title="Export edited report">
                <span class="btn-icon">📥</span>
                <span class="btn-text">Export</span>
              </button>
              <button id="save-btn" class="btn-toolbar btn-success" style="display: none;">
                <span class="btn-icon">💾</span>
                <span class="btn-text">Save</span>
              </button>
            </div>
          </div>
          <div class="report-content" id="report-content" contenteditable="false">
            ${htmlContent}
          </div>
        </div>
        
        <!-- Right Sidebar: Sections -->
        <div class="section-nav-sidebar" id="section-nav-sidebar">
          <div class="sidebar-header">
            <span class="sidebar-icon">📑</span>
            <h4>Sections</h4>
            <button id="toggle-sidebar" class="btn-toggle-sidebar" title="Toggle sidebar">◀</button>
          </div>
          <div class="section-nav-list" id="section-nav-list">
            <!-- Sections will be populated here -->
          </div>
        </div>
      </div>
    `;

    // Initialize editor controls
    initEditorControls();
    
    // Initialize section navigation
    initSectionNavigation();
    
    // Initialize undo/redo
    initUndoRedo();
    
    // Initialize chat
    window.Chat.initChat(reportId);
    
    // Initialize formatting toolbar
    initFormattingToolbar();
    
    // Initialize floating chat
    initFloatingChat();
    
    // Save initial state for undo
    saveState();
  }

  // Initialize formatting toolbar (works with widget now)
  function initFormattingToolbar() {
    // Get formatting widget instead of toolbar
    const formattingWidget = document.getElementById('formatting-widget-card');
    if (!formattingWidget) return;

    // Format buttons - with undo state saving
    formattingWidget.querySelectorAll('.format-btn-small').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const command = btn.dataset.command;
        document.execCommand(command, false, null);
        updateFormattingButtons();
        // Save state for undo after formatting
        saveState();
      });
    });

    // Font family - improved implementation
    const fontFamily = document.getElementById('font-family');
    if (fontFamily) {
      fontFamily.addEventListener('change', (e) => {
        const font = e.target.value;
        document.execCommand('fontName', false, font);
        // Update button states
        updateFormattingButtons();
        // Save state for undo
        saveState();
      });
      
      // Update font family selector to show current selection font
      const updateFontFamily = () => {
        try {
          const selection = window.getSelection();
          if (selection.rangeCount > 0 && !selection.isCollapsed) {
            const range = selection.getRangeAt(0);
            const container = range.commonAncestorContainer;
            const element = container.nodeType === 3 ? container.parentElement : container;
            if (element) {
              const computedFont = window.getComputedStyle(element).fontFamily;
              // Try to match with available options
              const availableFonts = Array.from(fontFamily.options).map(opt => opt.value);
              for (const availableFont of availableFonts) {
                if (computedFont.includes(availableFont)) {
                  fontFamily.value = availableFont;
                  break;
                }
              }
            }
          }
        } catch (e) {
          // Ignore errors
        }
      };
      
      const reportContent = document.getElementById('report-content');
      if (reportContent) {
        reportContent.addEventListener('mouseup', updateFontFamily);
        reportContent.addEventListener('keyup', updateFontFamily);
      }
    }

    // Font size - improved implementation
    const fontSize = document.getElementById('font-size');
    if (fontSize) {
      fontSize.addEventListener('change', (e) => {
        const size = e.target.value;
        const selection = window.getSelection();
        if (selection.rangeCount > 0 && !selection.isCollapsed) {
          const range = selection.getRangeAt(0);
          const span = document.createElement('span');
          span.style.fontSize = size;
          try {
            range.surroundContents(span);
          } catch (err) {
            // If surroundContents fails, extract and wrap
            const contents = range.extractContents();
            span.appendChild(contents);
            range.insertNode(span);
          }
          // Update button states after formatting
          updateFormattingButtons();
        } else {
          // If no selection, apply to next typed text
          document.execCommand('fontSize', false, '3');
          // Then find and update the font tag
          setTimeout(() => {
            const fontTags = document.querySelectorAll('font[size="3"]');
            fontTags.forEach(tag => {
              if (tag === document.activeElement || tag.contains(document.activeElement)) {
                const span = document.createElement('span');
                span.style.fontSize = size;
                span.innerHTML = tag.innerHTML;
                tag.parentNode.replaceChild(span, tag);
              }
            });
          }, 10);
        }
      });
    }

    // Text color - with visual feedback
    const textColor = document.getElementById('text-color');
    if (textColor) {
      textColor.addEventListener('change', (e) => {
        const color = e.target.value;
        document.execCommand('foreColor', false, color);
        // Update button states
        updateFormattingButtons();
        // Save state for undo
        saveState();
      });
      
      // Update color picker to show current selection color
      const updateColorPicker = () => {
        try {
          const selection = window.getSelection();
          if (selection.rangeCount > 0 && !selection.isCollapsed) {
            const range = selection.getRangeAt(0);
            const container = range.commonAncestorContainer;
            const element = container.nodeType === 3 ? container.parentElement : container;
            if (element) {
              const computedColor = window.getComputedStyle(element).color;
              // Convert rgb to hex if needed
              if (computedColor && computedColor !== 'rgb(0, 0, 0)') {
                const rgb = computedColor.match(/\d+/g);
                if (rgb && rgb.length === 3) {
                  const hex = '#' + rgb.map(x => {
                    const hex = parseInt(x).toString(16);
                    return hex.length === 1 ? '0' + hex : hex;
                  }).join('');
                  textColor.value = hex;
                }
              }
            }
          }
        } catch (e) {
          // Ignore errors
        }
      };
      
      // Update color picker on selection
      const reportContent = document.getElementById('report-content');
      if (reportContent) {
        reportContent.addEventListener('mouseup', updateColorPicker);
        reportContent.addEventListener('keyup', updateColorPicker);
      }
    }

    // Background color - with visual feedback
    const bgColor = document.getElementById('bg-color');
    if (bgColor) {
      bgColor.addEventListener('change', (e) => {
        const color = e.target.value;
        document.execCommand('backColor', false, color);
        // Update button states
        updateFormattingButtons();
        // Save state for undo
        saveState();
      });
    }

    // Update button states on selection change
    const reportContent = document.getElementById('report-content');
    if (reportContent) {
      reportContent.addEventListener('mouseup', updateFormattingButtons);
      reportContent.addEventListener('keyup', updateFormattingButtons);
      
      // Handle image paste
      reportContent.addEventListener('paste', handleImagePaste);
    }
  }
  
  // Handle image paste from clipboard
  function handleImagePaste(e) {
    const reportContent = document.getElementById('report-content');
    if (!reportContent || !isEditMode) return;
    
    const items = e.clipboardData?.items;
    if (!items) return;
    
    // Look for image in clipboard
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      
      if (item.type.indexOf('image') !== -1) {
        e.preventDefault();
        e.stopPropagation();
        
        const file = item.getAsFile();
        if (!file) continue;
        
        // Check file size (limit to 5MB)
        if (file.size > 5 * 1024 * 1024) {
          window.UI.log('Image too large. Maximum size is 5MB.');
          return;
        }
        
        // Show loading indicator
        window.UI.log('Processing image...');
        
        // Convert to base64
        const reader = new FileReader();
        reader.onload = function(event) {
          try {
            const base64Image = event.target.result;
            
            // Create container div for better styling
            const container = document.createElement('div');
            container.className = 'pasted-image-container';
            container.style.cssText = 'margin: 12px 0; text-align: center;';
            
            // Create img element
            const img = document.createElement('img');
            img.src = base64Image;
            img.className = 'pasted-image';
            img.style.cssText = 'max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); display: block; margin: 0 auto;';
            img.alt = 'Pasted image';
            
            // Add caption input (optional)
            const caption = document.createElement('div');
            caption.className = 'image-caption';
            caption.contentEditable = 'true';
            caption.style.cssText = 'margin-top: 8px; font-size: 12px; color: #666; font-style: italic; text-align: center; min-height: 20px;';
            caption.textContent = 'Click to add caption (optional)';
            caption.addEventListener('focus', function() {
              if (this.textContent === 'Click to add caption (optional)') {
                this.textContent = '';
              }
            });
            caption.addEventListener('blur', function() {
              if (!this.textContent.trim()) {
                this.textContent = 'Click to add caption (optional)';
              }
            });
            
            container.appendChild(img);
            container.appendChild(caption);
            
            // Insert at cursor position
            const selection = window.getSelection();
            if (selection.rangeCount > 0) {
              const range = selection.getRangeAt(0);
              range.deleteContents();
              
              // Insert container
              range.insertNode(container);
              
              // Move cursor after container
              range.setStartAfter(container);
              range.collapse(true);
              selection.removeAllRanges();
              selection.addRange(range);
            } else {
              // If no selection, append to content
              reportContent.appendChild(container);
              // Scroll to image
              container.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            
            // Save state for undo
            saveState();
            
            // Show success message
            window.UI.log('✓ Image pasted successfully');
          } catch (error) {
            console.error('Error pasting image:', error);
            window.UI.log('Error pasting image. Please try again.');
          }
        };
        
        reader.onerror = function() {
          window.UI.log('Error reading image file');
        };
        
        reader.readAsDataURL(file);
        break;
      }
    }
  }

  // Update formatting button states
  function updateFormattingButtons() {
    const formattingWidget = document.getElementById('formatting-widget-card');
    if (!formattingWidget) return;

    formattingWidget.querySelectorAll('.format-btn-small').forEach(btn => {
      const command = btn.dataset.command;
      if (command === 'bold' || command === 'italic' || command === 'underline') {
        try {
          const isActive = document.queryCommandState(command);
          btn.classList.toggle('active', isActive);
        } catch (e) {
          // Command not supported
        }
      } else if (command === 'justifyLeft' || command === 'justifyCenter' || 
                 command === 'justifyRight' || command === 'justifyFull') {
        try {
          const isActive = document.queryCommandState(command);
          btn.classList.toggle('active', isActive);
        } catch (e) {
          // Command not supported
        }
      }
    });
    
    // Update font size selector if possible
    const fontSize = document.getElementById('font-size');
    if (fontSize) {
      try {
        const selection = window.getSelection();
        if (selection.rangeCount > 0 && !selection.isCollapsed) {
          const range = selection.getRangeAt(0);
          const container = range.commonAncestorContainer;
          const element = container.nodeType === 3 ? container.parentElement : container;
          if (element) {
            const computedSize = window.getComputedStyle(element).fontSize;
            // Match to closest option
            const options = Array.from(fontSize.options);
            let closestOption = options[0];
            let closestDiff = Math.abs(parseInt(computedSize) - parseInt(closestOption.value));
            options.forEach(opt => {
              const diff = Math.abs(parseInt(computedSize) - parseInt(opt.value));
              if (diff < closestDiff) {
                closestDiff = diff;
                closestOption = opt;
              }
            });
            if (closestDiff < 5) { // Only update if close match (within 5px)
              fontSize.value = closestOption.value;
            }
          }
        }
      } catch (e) {
        // Ignore errors
      }
    }
  }

  // Initialize formatting widget toggle
  function initFormattingWidget() {
    const toggleBtn = document.getElementById('toggle-formatting-widget');
    const formattingWidget = document.getElementById('formatting-widget-card');
    
    if (toggleBtn && formattingWidget) {
      toggleBtn.addEventListener('click', () => {
        const isVisible = formattingWidget.style.display !== 'none';
        formattingWidget.style.display = isVisible ? 'none' : 'block';
        
        // Update button text
        const btnText = toggleBtn.querySelector('.btn-text');
        if (btnText) {
          btnText.textContent = isVisible ? 'Format' : 'Hide Format';
        }
      });
    }
  }

  // Initialize section navigation
  function initSectionNavigation() {
    const reportContent = document.getElementById('report-content');
    if (!reportContent) return;

    // Extract sections from HTML
    const sections = reportContent.querySelectorAll('section[data-section], section[id], h2, h3');
    const sectionNavList = document.getElementById('section-nav-list');
    if (!sectionNavList) return;

    sectionNavList.innerHTML = '';
    const sectionMap = {};

    sections.forEach((section, index) => {
      const sectionId = section.getAttribute('data-section') || section.id || `section-${index}`;
      const sectionTitle = section.querySelector('h2, h3, h4')?.textContent || 
                          section.getAttribute('data-section') || 
                          `Section ${index + 1}`;
      
      sectionMap[sectionId] = section;
      
      const navItem = document.createElement('div');
      navItem.className = 'nav-item';
      navItem.dataset.sectionId = sectionId;
      navItem.innerHTML = `
        <span class="nav-item-icon">📄</span>
        <span class="nav-item-text">${sectionTitle.substring(0, 30)}${sectionTitle.length > 30 ? '...' : ''}</span>
      `;
      
      navItem.addEventListener('click', () => {
        scrollToSection(sectionId);
        highlightNavItem(navItem);
      });
      
      sectionNavList.appendChild(navItem);
    });

    // Store section map for quick access
    window.Editor._sectionMap = sectionMap;

    // Toggle sidebar button
    const toggleBtn = document.getElementById('toggle-sidebar');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', toggleSidebar);
    }
  }

  // Toggle sidebar
  function toggleSidebar() {
    const sidebar = document.getElementById('section-nav-sidebar');
    const toggleBtn = document.getElementById('toggle-sidebar');
    if (sidebar && toggleBtn) {
      sidebar.classList.toggle('collapsed');
      toggleBtn.textContent = sidebar.classList.contains('collapsed') ? '▶' : '◀';
    }
  }

  // Scroll to section
  function scrollToSection(sectionId) {
    const sectionMap = window.Editor._sectionMap || {};
    const section = sectionMap[sectionId];
    if (section) {
      section.scrollIntoView({ behavior: 'smooth', block: 'start' });
      highlightSection(section);
    }
  }

  // Highlight nav item
  function highlightNavItem(navItem) {
    document.querySelectorAll('.nav-item').forEach(item => {
      item.classList.remove('active');
    });
    navItem.classList.add('active');
  }

  // Initialize undo/redo
  function initUndoRedo() {
    const undoBtn = document.getElementById('undo-btn');
    const redoBtn = document.getElementById('redo-btn');
    const reportContent = document.getElementById('report-content');

    if (undoBtn) {
      undoBtn.addEventListener('click', undo);
    }

    if (redoBtn) {
      redoBtn.addEventListener('click', redo);
    }

    // Keyboard shortcuts
    if (reportContent) {
      reportContent.addEventListener('keydown', (e) => {
        // Ctrl+Z for undo, Ctrl+Y or Ctrl+Shift+Z for redo
        if (e.ctrlKey && e.key === 'z' && !e.shiftKey) {
          e.preventDefault();
          undo();
        } else if ((e.ctrlKey && e.key === 'y') || (e.ctrlKey && e.shiftKey && e.key === 'Z')) {
          e.preventDefault();
          redo();
        }
      });

      // Track changes for undo/redo
      let changeTimeout;
      reportContent.addEventListener('input', () => {
        clearTimeout(changeTimeout);
        changeTimeout = setTimeout(() => {
          saveState();
        }, 500); // Debounce: save state 500ms after last change
      });
    }
  }

  // Save state for undo
  function saveState() {
    const reportContent = document.getElementById('report-content');
    if (!reportContent) return;

    const currentState = reportContent.innerHTML;
    
    // Don't save if it's the same as the last state
    if (undoStack.length > 0 && undoStack[undoStack.length - 1] === currentState) {
      return;
    }

    // Add to undo stack
    undoStack.push(currentState);
    
    // Limit stack size
    if (undoStack.length > maxHistorySize) {
      undoStack.shift();
    }

    // Clear redo stack when new change is made
    redoStack = [];

    // Update button states
    updateUndoRedoButtons();
  }

  // Undo
  function undo() {
    if (undoStack.length <= 1) return; // Keep at least one state

    const reportContent = document.getElementById('report-content');
    if (!reportContent) return;

    // Move current state to redo stack
    const currentState = reportContent.innerHTML;
    redoStack.push(currentState);

    // Restore previous state
    const previousState = undoStack.pop();
    reportContent.innerHTML = previousState;

    updateUndoRedoButtons();
    window.UI.log('Undo: Restored previous state');
  }

  // Redo
  function redo() {
    if (redoStack.length === 0) return;

    const reportContent = document.getElementById('report-content');
    if (!reportContent) return;

    // Save current state to undo stack
    const currentState = reportContent.innerHTML;
    undoStack.push(currentState);

    // Restore next state from redo stack
    const nextState = redoStack.pop();
    reportContent.innerHTML = nextState;

    updateUndoRedoButtons();
    window.UI.log('Redo: Restored next state');
  }

  // Update undo/redo button states
  function updateUndoRedoButtons() {
    const undoBtn = document.getElementById('undo-btn');
    const redoBtn = document.getElementById('redo-btn');

    if (undoBtn) {
      undoBtn.disabled = undoStack.length <= 1;
    }

    if (redoBtn) {
      redoBtn.disabled = redoStack.length === 0;
    }
  }

  // Initialize editor controls
  function initEditorControls() {
    const editToggle = document.getElementById('edit-mode-toggle');
    const saveBtn = document.getElementById('save-btn');
    const previewBtn = document.getElementById('preview-btn');
    const exportBtn = document.getElementById('export-btn');
    const reportContent = document.getElementById('report-content');

    if (editToggle) {
      editToggle.addEventListener('click', toggleEditMode);
    }

    if (saveBtn) {
      saveBtn.addEventListener('click', saveReport);
    }

    if (previewBtn) {
      previewBtn.addEventListener('click', () => {
        toggleEditMode();
      });
    }

    if (exportBtn) {
      exportBtn.addEventListener('click', exportReport);
    }

    // Handle section clicks for chat context
    if (reportContent) {
      reportContent.addEventListener('click', (e) => {
        if (isEditMode) return; // Don't interfere with editing
        
        // Find the closest section element
        const section = e.target.closest('section[data-section], section[id], div[data-section]');
        if (section) {
          const sectionId = section.getAttribute('data-section') || section.id;
          if (sectionId) {
            // Highlight section
            highlightSection(section);
            
            // Optionally auto-focus chat input with section context
            const chatInput = document.getElementById('chat-input');
            if (chatInput) {
              chatInput.placeholder = `Ask about ${sectionId}...`;
              chatInput.focus();
            }
          }
        }
      });
    }
  }

  // Toggle edit mode
  function toggleEditMode() {
    isEditMode = !isEditMode;
    const reportContent = document.getElementById('report-content');
    const editToggle = document.getElementById('edit-mode-toggle');
    const saveBtn = document.getElementById('save-btn');
    const formattingWidget = document.getElementById('formatting-widget-card');
    const toggleFormatBtn = document.getElementById('toggle-formatting-widget');

    if (reportContent) {
      reportContent.contentEditable = isEditMode;
      if (isEditMode) {
        reportContent.classList.add('editing');
        reportContent.focus();
      } else {
        reportContent.classList.remove('editing');
      }
    }

    if (editToggle) {
      const btnText = editToggle.querySelector('.btn-text');
      if (btnText) {
        btnText.textContent = isEditMode ? 'Preview Mode' : 'Edit Mode';
      }
      editToggle.classList.toggle('active', isEditMode);
    }

    if (saveBtn) {
      saveBtn.style.display = isEditMode ? 'inline-block' : 'none';
    }

    // Show/hide formatting widget (only show when in edit mode)
    if (formattingWidget) {
      formattingWidget.style.display = isEditMode ? 'block' : 'none';
    }
    
    if (toggleFormatBtn) {
      toggleFormatBtn.style.display = isEditMode ? 'inline-flex' : 'none';
    }
  }

  // Save report
  async function saveReport() {
    if (!currentReportId) {
      window.UI.log('No report loaded');
      return;
    }

    const reportContent = document.getElementById('report-content');
    if (!reportContent) return;

    const updatedHtml = reportContent.innerHTML;

    try {
      const token = window.Auth.getAuthToken();
      const headers = {
        'Content-Type': 'application/json'
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // Save to backend
      const response = await fetch(`${window.API_BASE_URL}/api/audit/${currentReportId}/save`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          html_content: updatedHtml
        })
      });

      if (!response.ok) {
        throw new Error(`Save failed: ${response.statusText}`);
      }

      // Also store in localStorage as backup
      localStorage.setItem(`report_${currentReportId}_backup`, updatedHtml);

      window.UI.log('Report changes saved successfully');
      window.UI.setStatus('Saved', 'success');

      // Show success message
      const saveBtn = document.getElementById('save-btn');
      if (saveBtn) {
        const originalText = saveBtn.textContent;
        saveBtn.textContent = '✓ Saved';
        saveBtn.disabled = true;
        setTimeout(() => {
          saveBtn.textContent = originalText;
          saveBtn.disabled = false;
        }, 2000);
      }

    } catch (error) {
      window.UI.log(`Save error: ${error.message}`);
      window.UI.setStatus('Save Failed', 'error');
      
      // Fallback to localStorage
      localStorage.setItem(`report_${currentReportId}_backup`, updatedHtml);
      window.UI.log('Saved to local backup');
    }
  }

  // Export edited report
  async function exportReport() {
    if (!currentReportId) {
      window.UI.log('No report loaded');
      return;
    }

    const reportContent = document.getElementById('report-content');
    if (!reportContent) return;

    const updatedHtml = reportContent.innerHTML;

    try {
      window.UI.log('Exporting edited report...');

      const token = window.Auth.getAuthToken();
      const headers = {
        'Content-Type': 'application/json'
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // Request export from backend
      const response = await fetch(`${window.API_BASE_URL}/api/audit/${currentReportId}/export`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          html_content: updatedHtml,
          format: 'html' // Can be extended to support PDF/Word
        })
      });

      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Download the exported file
      if (data.download_url) {
        const filename = data.filename || `audit_edited_${currentReportId}.html`;
        window.UI.downloadFile(data.download_url, filename);
        window.UI.log(`Report exported: ${filename}`);
      } else {
        // Fallback: create blob and download
        const blob = new Blob([updatedHtml], { type: 'text/html' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `audit_edited_${currentReportId}.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        window.UI.log('Report exported locally');
      }

    } catch (error) {
      window.UI.log(`Export error: ${error.message}`);
      
      // Fallback: download as HTML blob
      const blob = new Blob([updatedHtml], { type: 'text/html' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit_edited_${currentReportId}.html`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      window.UI.log('Report exported locally (fallback)');
    }
  }

  // Load report content
  async function loadReportContent(reportId) {
    if (!reportId) return;

    try {
      const token = window.Auth.getAuthToken();
      const headers = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${window.API_BASE_URL}/api/audit/status/${reportId}`, {
        method: 'GET',
        headers: headers
      });

      if (response.ok) {
        const data = await response.json();
        if (data.html_content) {
          const reportContent = document.getElementById('report-content');
          if (reportContent) {
            reportContent.innerHTML = data.html_content;
          }
        }
      }
    } catch (error) {
      console.error('Error loading report content:', error);
    }
  }

  // Highlight section
  function highlightSection(section) {
    // Remove previous highlights
    document.querySelectorAll('.section-highlight').forEach(el => {
      el.classList.remove('section-highlight');
    });

    // Add highlight to current section
    section.classList.add('section-highlight');

    // Scroll to section
    section.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    // Remove highlight after 3 seconds
    setTimeout(() => {
      section.classList.remove('section-highlight');
    }, 3000);
  }

  // Export public API
  window.Editor = {
    initReportEditor,
    toggleEditMode,
    saveReport,
    exportReport,
    loadReportContent,
    undo,
    redo,
    scrollToSection,
    getCurrentReportId: () => currentReportId,
    _sectionMap: {} // For internal use
  };
})();

