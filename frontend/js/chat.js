/**
 * Chat Module
 * Handles chat interface for interacting with audit reports
 */

(function() {
  'use strict';

  let chatHistory = [];

  // Initialize chat interface
  function initChat(reportId) {
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-chat-btn');
    const clearBtn = document.getElementById('clear-chat-btn');
    const quoteBtn = document.getElementById('generate-quote-btn');

    if (chatInput && sendBtn) {
      sendBtn.addEventListener('click', () => {
        const message = chatInput.value.trim();
        if (message) {
          sendChatMessage(reportId, message);
          chatInput.value = '';
        }
      });

      chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          sendBtn.click();
        }
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        clearChat();
      });
    }

    if (quoteBtn) {
      quoteBtn.addEventListener('click', () => {
        generateQuote(reportId);
      });
    }

    // Load chat history
    loadChatHistory(reportId);
  }

  // Send chat message
  async function sendChatMessage(reportId, message, sectionId = null) {
    if (!reportId || !message) return;

    // Add user message to UI
    addChatMessage('user', message);

    try {
      const token = window.Auth.getAuthToken();
      const headers = {
        'Content-Type': 'application/json'
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${window.API_BASE_URL}/api/audit/${reportId}/chat`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          message: message,
          section_id: sectionId,
          report_id: reportId
        })
      });

      if (!response.ok) {
        throw new Error(`Chat request failed: ${response.statusText}`);
      }

      const data = await response.json();

      // Add AI response to UI
      addChatMessage('assistant', data.response, data.suggested_edits);

      // If AI suggested edits, show preview buttons
      if (data.suggested_edits && data.suggested_edits.length > 0) {
        showSuggestedEdits(data.suggested_edits, reportId);
      }

      // Handle navigation actions (scroll to sections)
      if (data.navigation_actions && data.navigation_actions.length > 0) {
        data.navigation_actions.forEach(action => {
          if (action.action === 'scroll_to' && action.section_id) {
            // Use editor's scroll function
            if (window.Editor && window.Editor.scrollToSection) {
              setTimeout(() => {
                window.Editor.scrollToSection(action.section_id);
              }, 500); // Small delay to ensure UI is ready
            }
          }
        });
      }

      // Auto-scroll to first referenced section if any
      if (data.section_references && data.section_references.length > 0) {
        const firstSection = data.section_references[0];
        if (window.Editor && window.Editor.scrollToSection) {
          setTimeout(() => {
            window.Editor.scrollToSection(firstSection);
          }, 500);
        }
      }

      // Update chat history
      chatHistory.push({ role: 'user', message });
      chatHistory.push({ role: 'assistant', message: data.response });

    } catch (error) {
      window.UI.log(`Chat error: ${error.message}`);
      addChatMessage('assistant', `Error: ${error.message}. Please try again.`);
    }
  }

  // Add chat message to UI
  function addChatMessage(role, message, suggestedEdits = null) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message chat-message-${role}`;
    
    // Format message with clickable section references
    let formattedMessage = escapeHtml(message);
    
    // Make section references clickable
    formattedMessage = formattedMessage.replace(
      /(executive_summary|kav_analysis|campaign_performance|flow_performance|data_capture|segmentation_strategy|list_growth|automation_overview|strategic_recommendations)/gi,
      '<span class="section-reference" data-section="$1" style="color: var(--andzen-green); cursor: pointer; text-decoration: underline;">$1</span>'
    );
    
    let content = `<div class="message-content">${formattedMessage}</div>`;
    
    if (suggestedEdits && suggestedEdits.length > 0) {
      content += '<div class="suggested-edits">';
      suggestedEdits.forEach((edit, index) => {
        const editId = `edit-${Date.now()}-${index}`;
        const previewText = edit.new_content.replace(/<[^>]*>/g, '').substring(0, 200);
        content += `
          <div class="suggested-edit">
            <p><strong>📝 Suggested edit to ${edit.section_id}:</strong></p>
            <p class="edit-reason" style="font-size: 0.9em; color: #666; margin: 4px 0;">${escapeHtml(edit.reason || 'User requested edit')}</p>
            <div class="edit-preview">${escapeHtml(previewText)}${previewText.length >= 200 ? '...' : ''}</div>
            <div class="edit-actions">
              <button class="btn-apply-edit" onclick="window.Chat.applyEdit('${editId}', '${edit.section_id}', ${JSON.stringify(edit.new_content).replace(/"/g, '&quot;')})">✅ Apply</button>
              <button class="btn-cancel-edit" onclick="window.Chat.cancelEdit('${editId}')">❌ Cancel</button>
              <button class="btn-preview-section" onclick="window.Chat.scrollToSection('${edit.section_id}')" title="View section">👁️ View</button>
            </div>
            <div id="${editId}" style="display: none;"></div>
          </div>
        `;
      });
      content += '</div>';
    }
    
    messageDiv.innerHTML = content;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Add click handlers for section references
    messageDiv.querySelectorAll('.section-reference').forEach(ref => {
      ref.addEventListener('click', () => {
        const sectionId = ref.getAttribute('data-section');
        if (sectionId && window.Editor && window.Editor.scrollToSection) {
          window.Editor.scrollToSection(sectionId);
        }
      });
    });
  }

  // Show suggested edits
  function showSuggestedEdits(suggestedEdits, reportId) {
    // Edits are already shown in addChatMessage
    // This function can be extended for additional UI
  }

  // Apply edit
  async function applyEdit(editId, sectionId, newContent) {
    const reportId = window.Editor.getCurrentReportId();
    if (!reportId) {
      window.UI.log('No report loaded');
      return;
    }

    try {
      const token = window.Auth.getAuthToken();
      const headers = {
        'Content-Type': 'application/json'
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${window.API_BASE_URL}/api/audit/${reportId}/edit`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          report_id: reportId,
          section_id: sectionId,
          new_content: newContent,
          edit_source: 'chat'
        })
      });

      if (!response.ok) {
        throw new Error(`Edit request failed: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.success) {
        // Reload report content
        window.Editor.loadReportContent(reportId);
        addChatMessage('assistant', `✅ Changes applied to ${sectionId}!`);
        
        // Scroll to the edited section
        if (window.Editor && window.Editor.scrollToSection) {
          setTimeout(() => {
            window.Editor.scrollToSection(sectionId);
          }, 300);
        }
        
        // Hide the edit suggestion
        const editElement = document.getElementById(editId);
        if (editElement) {
          editElement.closest('.suggested-edit').style.display = 'none';
        }
      } else {
        throw new Error('Edit failed');
      }

    } catch (error) {
      window.UI.log(`Edit error: ${error.message}`);
      addChatMessage('assistant', `Error applying edit: ${error.message}`);
    }
  }

  // Cancel edit
  function cancelEdit(editId) {
    const editElement = document.getElementById(editId);
    if (editElement) {
      editElement.closest('.suggested-edit').style.display = 'none';
    }
  }

  // Load chat history
  async function loadChatHistory(reportId) {
    if (!reportId) return;

    try {
      const token = window.Auth.getAuthToken();
      const headers = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${window.API_BASE_URL}/api/audit/${reportId}/chat/history`, {
        method: 'GET',
        headers: headers
      });

      if (response.ok) {
        const data = await response.json();
        const messages = data.messages || [];

        // Clear existing messages
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages) {
          chatMessages.innerHTML = '';
        }

        // Add messages to UI
        messages.forEach(msg => {
          addChatMessage(msg.role, msg.message, msg.suggested_edits);
        });

        chatHistory = messages;
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  }

  // Clear chat
  function clearChat() {
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
      chatMessages.innerHTML = '';
    }
    chatHistory = [];
  }

  // Generate quote
  async function generateQuote(reportId) {
    if (!reportId) {
      window.UI.log('No report loaded');
      return;
    }

    try {
      window.UI.log('Generating quote from audit findings...');
      
      // Show loading message
      addChatMessage('assistant', '💼 Generating quote based on audit findings...');

      const token = window.Auth.getAuthToken();
      const headers = {
        'Content-Type': 'application/json'
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // Ask user for priorities (optional)
      const priorities = prompt('Enter priorities (one per line, or leave empty for top recommendations):');
      const prioritiesList = priorities ? priorities.split('\n').filter(p => p.trim()) : null;

      const response = await fetch(`${window.API_BASE_URL}/api/audit/${reportId}/quote`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          priorities: prioritiesList,
          custom_message: null
        })
      });

      if (!response.ok) {
        throw new Error(`Quote generation failed: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.success && data.quote) {
        // Format and display quote
        displayQuote(data.quote);
      } else {
        throw new Error('Quote generation failed');
      }

    } catch (error) {
      window.UI.log(`Quote generation error: ${error.message}`);
      addChatMessage('assistant', `Error generating quote: ${error.message}. Please try again.`);
    }
  }

  // Display quote
  function displayQuote(quote) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;

    const quoteDiv = document.createElement('div');
    quoteDiv.className = 'chat-message chat-message-assistant quote-message';
    
    let quoteHtml = `
      <div class="quote-container">
        <h4 class="quote-title">${escapeHtml(quote.quote_title || 'Sales Quote')}</h4>
        <div class="quote-summary">
          <p><strong>Executive Summary:</strong></p>
          <p>${escapeHtml(quote.executive_summary || '')}</p>
        </div>
    `;

    if (quote.services && quote.services.length > 0) {
      quoteHtml += '<div class="quote-services"><p><strong>Services:</strong></p><ul>';
      quote.services.forEach(service => {
        quoteHtml += `
          <li class="quote-service">
            <strong>${escapeHtml(service.service_name || 'Service')}</strong>
            <p>${escapeHtml(service.description || '')}</p>
            ${service.deliverables ? `<ul>${service.deliverables.map(d => `<li>${escapeHtml(d)}</li>`).join('')}</ul>` : ''}
            <div class="quote-service-meta">
              <span>Timeline: ${escapeHtml(service.timeline || 'TBD')}</span>
              <span>Investment: ${escapeHtml(service.investment || 'Contact for pricing')}</span>
            </div>
          </li>
        `;
      });
      quoteHtml += '</ul></div>';
    }

    if (quote.total_investment) {
      quoteHtml += `<div class="quote-total"><strong>Total Investment:</strong> ${escapeHtml(quote.total_investment)}</div>`;
    }

    if (quote.expected_roi) {
      quoteHtml += `<div class="quote-roi"><strong>Expected ROI:</strong> ${escapeHtml(quote.expected_roi)}</div>`;
    }

    if (quote.next_steps && quote.next_steps.length > 0) {
      quoteHtml += '<div class="quote-next-steps"><p><strong>Next Steps:</strong></p><ul>';
      quote.next_steps.forEach(step => {
        quoteHtml += `<li>${escapeHtml(step)}</li>`;
      });
      quoteHtml += '</ul></div>';
    }

    if (quote.quote_valid_until) {
      quoteHtml += `<div class="quote-validity">Quote valid until: ${escapeHtml(quote.quote_valid_until)}</div>`;
    }

    quoteHtml += `
        <div class="quote-actions">
          <button class="btn-download-quote" onclick="window.Chat.downloadQuote(${JSON.stringify(quote).replace(/"/g, '&quot;')})">📥 Download Quote</button>
        </div>
      </div>
    `;

    quoteDiv.innerHTML = quoteHtml;
    chatMessages.appendChild(quoteDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // Download quote
  function downloadQuote(quote) {
    // Create a formatted quote document
    let quoteText = `${quote.quote_title || 'Sales Quote'}\n`;
    quoteText += '='.repeat(50) + '\n\n';
    quoteText += `Executive Summary:\n${quote.executive_summary || ''}\n\n`;
    
    if (quote.services && quote.services.length > 0) {
      quoteText += 'Services:\n';
      quote.services.forEach(service => {
        quoteText += `\n${service.service_name || 'Service'}\n`;
        quoteText += `${service.description || ''}\n`;
        if (service.deliverables) {
          quoteText += 'Deliverables:\n';
          service.deliverables.forEach(d => {
            quoteText += `  - ${d}\n`;
          });
        }
        quoteText += `Timeline: ${service.timeline || 'TBD'}\n`;
        quoteText += `Investment: ${service.investment || 'Contact for pricing'}\n\n`;
      });
    }

    if (quote.total_investment) {
      quoteText += `Total Investment: ${quote.total_investment}\n\n`;
    }

    if (quote.expected_roi) {
      quoteText += `Expected ROI: ${quote.expected_roi}\n\n`;
    }

    if (quote.next_steps && quote.next_steps.length > 0) {
      quoteText += 'Next Steps:\n';
      quote.next_steps.forEach(step => {
        quoteText += `  - ${step}\n`;
      });
    }

    // Create and download file
    const blob = new Blob([quoteText], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `quote_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    window.UI.log('Quote downloaded');
  }

  // Escape HTML
  function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Scroll to section (helper function)
  function scrollToSection(sectionId) {
    if (window.Editor && window.Editor.scrollToSection) {
      window.Editor.scrollToSection(sectionId);
    } else {
      window.UI.log(`Cannot scroll to section ${sectionId} - editor not initialized`);
    }
  }

  // Export public API
  window.Chat = {
    initChat,
    sendChatMessage,
    addChatMessage,
    applyEdit,
    cancelEdit,
    loadChatHistory,
    clearChat,
    generateQuote,
    downloadQuote,
    scrollToSection
  };
})();

