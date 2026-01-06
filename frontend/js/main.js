/**
 * Main Initialization Module
 * Ties everything together and handles page initialization
 */

(function() {
  'use strict';

  // Initialize everything when DOM is ready
  function init() {
    // Set API base URL if not already set
    if (!window.API_BASE_URL) {
      window.API_BASE_URL = window.API_URL || 'http://localhost:8001';
    }
    
    // Initialize dashboard navigation
    initDashboardNavigation();
    
    // Initialize login form
    initLoginForm();
    
    // Initialize logout button
    initLogout();
    
    // Initialize multi-step form
    initMultiStepForm();
    
    // Initialize quick actions
    initQuickActions();
    
    // Initialize LLM provider selector
    initLLMProviderSelector();
    
    // Initialize API test buttons
    initAPITestButtons();
    
    // Show appropriate section based on authentication
    checkAuthAndShowSection();
  }

  // Initialize dashboard navigation
  function initDashboardNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('main[id$="-section"]');

    navItems.forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        
        const targetSection = item.dataset.section;
        if (!targetSection) return;

        // Update active nav item
        navItems.forEach(nav => nav.classList.remove('active'));
        item.classList.add('active');

        // Show target section
        sections.forEach(section => {
          section.style.display = 'none';
        });
        
        const targetEl = document.getElementById(`${targetSection}-section`);
        if (targetEl) {
          targetEl.style.display = 'block';
        }
      });
    });
  }

  // Initialize multi-step form
  function initMultiStepForm() {
    const steps = document.querySelectorAll('.form-section');
    const nextBtn = document.getElementById('btn-next');
    const prevBtn = document.getElementById('btn-previous');
    const launchBtn = document.getElementById('btn-launch');
    const stepIndicators = document.querySelectorAll('.progress-indicator .step');
    const formIndicators = document.querySelectorAll('.step-indicators .indicator');
    
    let currentStep = 1;
    const totalSteps = steps.length;

    function updateStep() {
      // Hide all steps
      steps.forEach(step => step.classList.remove('active'));
      
      // Show current step
      const currentStepEl = document.getElementById(`step-${currentStep}`);
      if (currentStepEl) {
        currentStepEl.classList.add('active');
      }

      // Update progress indicators
      stepIndicators.forEach((indicator, index) => {
        indicator.classList.toggle('active', index < currentStep);
      });
      
      formIndicators.forEach((indicator, index) => {
        indicator.classList.toggle('active', index < currentStep);
      });

      // Update navigation buttons
      if (prevBtn) {
        prevBtn.disabled = currentStep === 1;
      }
      
      if (nextBtn) {
        nextBtn.style.display = currentStep === totalSteps ? 'none' : 'inline-flex';
      }
      
      if (launchBtn) {
        launchBtn.style.display = currentStep === totalSteps ? 'inline-flex' : 'none';
      }
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        if (currentStep < totalSteps) {
          currentStep++;
          updateStep();
        }
      });
    }

    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        if (currentStep > 1) {
          currentStep--;
          updateStep();
        }
      });
    }

    // Handle back to dashboard
    const backBtn = document.querySelector('.btn-back');
    if (backBtn) {
      backBtn.addEventListener('click', () => {
        showDashboard();
      });
    }

    // Handle form submission
    const auditForm = document.getElementById('audit-form');
    if (auditForm) {
      auditForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleAuditFormSubmit();
      });
    }

    // Also handle launch button click directly
    if (launchBtn) {
      launchBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        await handleAuditFormSubmit();
      });
    }

    // Initialize form
    updateStep();
    
    // Handle cancel button in loading modal
    const cancelBtn = document.getElementById('cancel-audit');
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => {
        // Hide loading modal
        const loadingModal = document.getElementById('loading-modal');
        if (loadingModal) {
          loadingModal.style.display = 'none';
        }
        
        // Reset launch button
        if (launchBtn) {
          launchBtn.disabled = false;
          launchBtn.textContent = '🚀 Generate Audit';
        }
        
        if (window.UI) {
          window.UI.showToast('Audit generation cancelled', 'info');
        }
      });
    }
    
    // Handle custom date range showing/hiding
    const periodSelect = document.getElementById('period-select');
    const customDateRange = document.getElementById('custom-date-range');
    
    if (periodSelect && customDateRange) {
      periodSelect.addEventListener('change', (e) => {
        if (e.target.value === 'custom') {
          customDateRange.style.display = 'block';
        } else {
          customDateRange.style.display = 'none';
        }
      });
    }
  }

  // Handle audit form submission
  async function handleAuditFormSubmit() {
    const form = document.getElementById('audit-form');
    if (!form) {
      console.error('Audit form not found');
      return;
    }

    const launchBtn = document.getElementById('btn-launch');
    if (launchBtn) {
      launchBtn.disabled = true;
      launchBtn.textContent = 'Generating...';
    }

    try {
      // Collect form data
      const formData = new FormData(form);
      
      // Build payload
      const payload = {
        client_name: formData.get('client_name'),
        client_code: formData.get('client_code') || null,
        industry: formData.get('industry') || null,
        auditor_name: formData.get('auditor_name') || 'Andzen Team',
        api_key: formData.get('api_key'),
      };

      // Handle analysis period
      const period = formData.get('period');
      if (period === 'custom') {
        const startDate = formData.get('start_date');
        const endDate = formData.get('end_date');
        if (startDate && endDate) {
          payload.date_range = {
            start: startDate,
            end: endDate
          };
        }
      } else if (period) {
        payload.days = parseInt(period);
      }

      // Handle LLM configuration
      const llmProvider = formData.get('llm_provider');
      if (llmProvider) {
        payload.llm_provider = llmProvider;
        const llmApiKey = document.getElementById('llm-api-key-input')?.value;
        const llmModel = document.getElementById('llm-model-select')?.value;
        
        if (llmApiKey) {
          if (llmProvider === 'claude') {
            payload.anthropic_api_key = llmApiKey;
            if (llmModel) payload.claude_model = llmModel;
          } else if (llmProvider === 'openai') {
            payload.openai_api_key = llmApiKey;
            if (llmModel) payload.openai_model = llmModel;
          } else if (llmProvider === 'gemini') {
            payload.gemini_api_key = llmApiKey;
            if (llmModel) payload.gemini_model = llmModel;
          }
        }
      }

      // Show loading modal
      const loadingModal = document.getElementById('loading-modal');
      if (loadingModal) {
        loadingModal.style.display = 'flex';
      }

      // Get auth token if available
      const token = window.Auth ? window.Auth.getAuthToken() : null;
      const headers = { 'Content-Type': 'application/json' };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // Submit to API
      const response = await fetch(`${window.API_BASE_URL}/api/audit/generate`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Show success message
        if (window.UI) {
          window.UI.showToast('Audit generation started successfully!', 'success');
        }
        
        // Navigate to report viewer or start polling
        if (data.report_id) {
          // If report is ready, navigate to it
          if (data.status === 'completed') {
            // Hide loading modal and navigate
            const loadingModal = document.getElementById('loading-modal');
            if (loadingModal) {
              loadingModal.style.display = 'none';
            }
            window.location.href = `report-viewer.html?report_id=${data.report_id}`;
          } else {
            // Start polling for status with our own dashboard-compatible polling
            startAuditPolling(data.report_id, headers);
          }
        } else {
          alert('Audit started but no report ID returned. Please check the reports page.');
        }
      } else {
        throw new Error(data.detail || 'Failed to start audit generation');
      }
    } catch (error) {
      console.error('Error submitting audit:', error);
      if (window.UI) {
        window.UI.showToast(`Error: ${error.message}`, 'error');
      } else {
        alert(`Error: ${error.message}`);
      }
      
      // Hide loading modal
      const loadingModal = document.getElementById('loading-modal');
      if (loadingModal) {
        loadingModal.style.display = 'none';
      }
    } finally {
      if (launchBtn) {
        launchBtn.disabled = false;
        launchBtn.textContent = '🚀 Generate Audit';
      }
    }
  }

  // Start audit polling for dashboard modal
  async function startAuditPolling(reportId, headers) {
    let pollCount = 0;
    const maxPolls = 120; // 10 minutes max (5 second intervals)
    
    const poll = async () => {
      try {
        pollCount++;
        
        const response = await fetch(`${window.API_BASE_URL}/api/audit/status/${reportId}`, {
          headers: headers
        });
        
        if (!response.ok) {
          throw new Error(`Status check failed: ${response.status}`);
        }
        
        const statusData = await response.json();
        
        // Update progress
        if (statusData.progress !== undefined) {
          const step = getStepFromProgress(statusData.progress);
          if (window.UI && window.UI.updateProgress) {
            window.UI.updateProgress(statusData.progress, step);
          }
        }
        
        // Handle completion states
        if (statusData.status === 'completed') {
          // Hide loading modal and navigate to report
          const loadingModal = document.getElementById('loading-modal');
          if (loadingModal) {
            loadingModal.style.display = 'none';
          }
          
          if (window.UI) {
            window.UI.showToast('Audit completed successfully!', 'success');
          }
          
          // Navigate to report viewer
          window.location.href = `report-viewer.html?report_id=${reportId}`;
          return;
        } else if (statusData.status === 'failed') {
          // Hide loading modal and show error
          const loadingModal = document.getElementById('loading-modal');
          if (loadingModal) {
            loadingModal.style.display = 'none';
          }
          
          const errorMessage = statusData.error || 'Audit generation failed';
          if (window.UI) {
            window.UI.showToast(`Error: ${errorMessage}`, 'error');
          } else {
            alert(`Error: ${errorMessage}`);
          }
          return;
        }
        
        // Continue polling if still processing and haven't reached max polls
        if (statusData.status === 'processing' && pollCount < maxPolls) {
          setTimeout(poll, 5000); // Poll every 5 seconds
        } else if (pollCount >= maxPolls) {
          // Timeout - hide modal and show message
          const loadingModal = document.getElementById('loading-modal');
          if (loadingModal) {
            loadingModal.style.display = 'none';
          }
          
          if (window.UI) {
            window.UI.showToast('Polling timeout. Please check reports page for status.', 'warning');
          } else {
            alert('Polling timeout. Please check reports page for status.');
          }
        }
        
      } catch (error) {
        console.error('Polling error:', error);
        
        // Continue polling unless we've tried too many times
        if (pollCount < maxPolls) {
          setTimeout(poll, 5000);
        } else {
          const loadingModal = document.getElementById('loading-modal');
          if (loadingModal) {
            loadingModal.style.display = 'none';
          }
          
          if (window.UI) {
            window.UI.showToast('Connection error. Please check reports page for status.', 'error');
          }
        }
      }
    };
    
    // Start polling
    setTimeout(poll, 2000); // Wait 2 seconds before first poll
  }

  // Get step description from progress percentage
  function getStepFromProgress(progress) {
    if (progress < 10) return 'Connecting to Klaviyo';
    if (progress < 40) return 'Extracting data';
    if (progress < 80) return 'AI analysis';
    if (progress < 95) return 'Generating report';
    return 'Finalizing';
  }

  // Initialize quick actions
  function initQuickActions() {
    const actionCards = document.querySelectorAll('.action-card');
    
    actionCards.forEach(card => {
      card.addEventListener('click', () => {
        const action = card.dataset.action;
        
        switch(action) {
          case 'new-audit':
            showAuditLauncher();
            break;
          case 'bulk-export':
            // Navigate to reports page or show bulk export modal
            window.UI.log('Bulk export feature coming soon');
            break;
          case 'templates':
            // Navigate to templates page
            alert('Templates feature coming soon');
            break;
          case 'analytics':
            // Navigate to analytics page
            window.location.href = 'analytics.html';
            break;
        }
      });
    });
  }

  // Show dashboard
  function showDashboard() {
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('main[id$="-section"]');
    
    // Update nav
    navItems.forEach(nav => nav.classList.remove('active'));
    const dashboardNav = document.querySelector('[data-section="dashboard"]');
    if (dashboardNav) {
      dashboardNav.classList.add('active');
    }
    
    // Show dashboard section
    sections.forEach(section => {
      section.style.display = 'none';
    });
    
    const dashboardSection = document.getElementById('dashboard-section');
    if (dashboardSection) {
      dashboardSection.style.display = 'block';
      // Load real dashboard data
      loadDashboardData();
    }
  }

  // Load real dashboard data
  async function loadDashboardData() {
    try {
      // Get auth token
      const token = window.Auth ? window.Auth.getAuthToken() : null;
      if (!token) {
        console.warn('No auth token available for dashboard data');
        return;
      }

      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Load stats
      const statsResponse = await fetch(`${window.API_BASE_URL}/api/dashboard/stats`, {
        headers: headers
      });
      if (statsResponse.ok) {
        const stats = await statsResponse.json();
        updateDashboardStats(stats);
      } else {
        console.error('Failed to load stats:', statsResponse.status, await statsResponse.text());
      }

      // Load recent audits
      const auditsResponse = await fetch(`${window.API_BASE_URL}/api/dashboard/recent-audits?limit=5`, {
        headers: headers
      });
      if (auditsResponse.ok) {
        const data = await auditsResponse.json();
        updateRecentAudits(data.audits);
      } else {
        console.error('Failed to load recent audits:', auditsResponse.status, await auditsResponse.text());
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    }
  }

  // Update dashboard stats with real data
  function updateDashboardStats(stats) {
    // Update Total Audits
    const auditsValue = document.getElementById('audits-value');
    if (auditsValue && stats.audits_this_month !== undefined) {
      auditsValue.textContent = stats.audits_this_month;
    }
    
    // Update trend for audits
    const auditsTrend = document.getElementById('audits-trend');
    if (auditsTrend && stats.audits_change_percent !== undefined) {
      const isPositive = stats.audits_change_percent >= 0;
      auditsTrend.textContent = `${isPositive ? '+' : ''}${stats.audits_change_percent.toFixed(0)}%`;
      auditsTrend.className = `stat-trend ${isPositive ? 'positive' : 'negative'}`;
    }

    // Update Projected Revenue (using total_revenue_analyzed)
    const revenueValue = document.getElementById('revenue-value');
    if (revenueValue && stats.total_revenue_analyzed !== undefined) {
      const revenue = stats.total_revenue_analyzed;
      if (revenue >= 1000000) {
        revenueValue.textContent = `$${(revenue / 1000000).toFixed(1)}M`;
      } else if (revenue >= 1000) {
        revenueValue.textContent = `$${(revenue / 1000).toFixed(0)}K`;
      } else {
        revenueValue.textContent = `$${revenue.toFixed(0)}`;
      }
    }
    
    const revenueTrend = document.getElementById('revenue-trend');
    if (revenueTrend && stats.revenue_change_percent !== undefined) {
      const isPositive = stats.revenue_change_percent >= 0;
      revenueTrend.textContent = `${isPositive ? '+' : ''}${stats.revenue_change_percent.toFixed(0)}%`;
      revenueTrend.className = `stat-trend ${isPositive ? 'positive' : 'negative'}`;
    }

    // Update Active Prospects (using active_clients)
    const prospectsValue = document.getElementById('prospects-value');
    if (prospectsValue && stats.active_clients !== undefined) {
      prospectsValue.textContent = stats.active_clients;
    }
    
    const prospectsTrend = document.getElementById('prospects-trend');
    if (prospectsTrend && stats.new_clients_this_week !== undefined) {
      prospectsTrend.textContent = `+${stats.new_clients_this_week}`;
      prospectsTrend.className = 'stat-trend positive';
    }

    // Avg Processing Time - would need to calculate from reports
    // For now, keep placeholder or calculate from report timestamps
  }

  // Update recent audits with real data
  function updateRecentAudits(audits) {
    const auditList = document.querySelector('#dashboard-section .audit-list');
    if (!auditList) return;
    
    // Show empty state if no audits
    if (!audits || audits.length === 0) {
      auditList.innerHTML = `
        <div class="empty-state" style="text-align: center; padding: 2rem; color: var(--text-muted);">
          <p>No audits yet. Create your first audit to get started!</p>
        </div>
      `;
      return;
    }

    auditList.innerHTML = audits.map(audit => {
      const status = audit.status === 'completed' ? 'success' : 
                    audit.status === 'processing' ? 'processing' : 'failed';
      const statusText = audit.status === 'completed' ? 'Completed' :
                        audit.status === 'processing' ? 'In Progress' : 'Failed';
      
      const timeAgo = formatTimeAgo(new Date(audit.created_at));
      const revenue = audit.revenue ? formatCurrency(audit.revenue) : '—';
      
      // Extract client code from filename or use ID
      const clientCode = audit.filename ? audit.filename.match(/([A-Z]{2,3}-\d{4}-\d{2})/)?.[0] : `AUD-${audit.id}`;
      
      return `
        <div class="audit-item card" data-audit-id="${audit.id}">
          <div class="audit-info">
            <div class="audit-client">
              <h4>${escapeHtml(audit.client_name)}</h4>
              <span class="audit-code">${clientCode || `AUD-${audit.id}`}</span>
            </div>
            <div class="audit-meta">
              <span class="audit-date">${timeAgo}</span>
              <span class="audit-revenue">${revenue}</span>
            </div>
          </div>
          <div class="audit-status">
            <span class="badge badge-${status}">
              <span class="status-dot ${status}"></span>
              ${statusText}
            </span>
          </div>
          <div class="audit-actions">
            ${audit.status === 'completed' ? `
              <button class="btn btn-ghost btn-xs btn-view-audit" data-audit-id="${audit.id}">View</button>
              <button class="btn btn-outline btn-xs btn-share-audit" data-audit-id="${audit.id}">Share</button>
            ` : audit.status === 'processing' ? `
              <button class="btn btn-ghost btn-xs btn-monitor-audit" data-audit-id="${audit.id}">Monitor</button>
              <button class="btn btn-danger btn-xs btn-cancel-audit" data-audit-id="${audit.id}">Cancel</button>
            ` : `
              <button class="btn btn-ghost btn-xs" disabled>Failed</button>
            `}
          </div>
        </div>
      `;
    }).join('');

    // Add event listeners for buttons
    document.querySelectorAll('.btn-view-audit').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const auditId = e.target.dataset.auditId;
        window.location.href = `report-viewer.html?reportId=${auditId}`;
      });
    });

    document.querySelectorAll('.btn-share-audit').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const auditId = e.target.dataset.auditId;
        // Share functionality - could copy link or open share modal
        alert('Share feature coming soon');
      });
    });

    document.querySelectorAll('.btn-monitor-audit').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const auditId = e.target.dataset.auditId;
        window.location.href = `report-viewer.html?reportId=${auditId}`;
      });
    });

    document.querySelectorAll('.btn-cancel-audit').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const auditId = e.target.dataset.auditId;
        if (confirm('Are you sure you want to cancel this audit?')) {
          try {
            const response = await fetch(`${window.API_BASE_URL}/api/audit/cancel/${auditId}`, {
              method: 'POST'
            });
            if (response.ok) {
              alert('Audit cancelled successfully');
              loadDashboardData(); // Reload to update list
            } else {
              alert('Failed to cancel audit');
            }
          } catch (error) {
            alert('Error cancelling audit');
          }
        }
      });
    });
  }

  // Helper functions
  function formatTimeAgo(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  }

  function formatCurrency(amount) {
    if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(1)}M`;
    } else if (amount >= 1000) {
      return `$${(amount / 1000).toFixed(0)}K`;
    }
    return `$${amount.toFixed(0)}`;
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Show audit launcher
  function showAuditLauncher() {
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('main[id$="-section"]');
    
    // Update nav
    navItems.forEach(nav => nav.classList.remove('active'));
    const auditsNav = document.querySelector('[data-section="audits"]');
    if (auditsNav) {
      auditsNav.classList.add('active');
    }
    
    // Show audits section
    sections.forEach(section => {
      section.style.display = 'none';
    });
    
    const auditsSection = document.getElementById('audits-section');
    if (auditsSection) {
      auditsSection.style.display = 'block';
      // Re-initialize API test buttons when section is shown
      initAPITestButtons();
      // Re-initialize multi-step form when section is shown
      initMultiStepForm();
    }
  }

  // Check authentication and show appropriate section
  function checkAuthAndShowSection() {
    const loginSection = document.getElementById('login-section');
    const dashboardSection = document.getElementById('dashboard-section');
    const auditsSection = document.getElementById('audits-section');
    const reportsSection = document.getElementById('reports-section');

    // Hide all sections initially
    [loginSection, dashboardSection, auditsSection, reportsSection].forEach(section => {
      if (section) section.style.display = 'none';
    });

    // Check if user is authenticated
    if (window.Auth && window.Auth.isAuthenticated()) {
      // Show dashboard by default
      showDashboard();
    } else {
      // Show login
      if (loginSection) {
        loginSection.style.display = 'flex';
      }
    }
  }

  // Initialize login form
  function initLoginForm() {
    const loginForm = document.getElementById('login-form');
    const loginBtn = document.getElementById('login-btn');
    const loginError = document.getElementById('login-error');

    if (loginForm) {
      loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        loginBtn.disabled = true;
        loginError.style.display = 'none';

        const formData = new FormData(loginForm);
        const username = formData.get('username');
        const password = formData.get('password');

        const result = await window.Auth.handleLogin(username, password);

        if (result.success) {
          loginForm.reset();
        } else {
          loginError.textContent = result.error;
          loginError.style.display = 'block';
        }

        loginBtn.disabled = false;
      });
    }
  }

  // Initialize logout button
  function initLogout() {
    const logoutBtn = document.getElementById('btn-logout');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => {
        window.Auth.clearAuthToken();
        window.Auth.showLogin();
      });
    }
  }

  // Initialize LLM provider selector
  function initLLMProviderSelector() {
    const providerSelect = document.getElementById('llm-provider-select');
    const llmApiKeyGroup = document.getElementById('llm-api-key-group');
    const llmApiKeyLabel = document.getElementById('llm-api-key-label');
    const llmApiKeyInput = document.getElementById('llm-api-key-input');
    const llmModelLabel = document.getElementById('llm-model-label');
    const llmModelSelect = document.getElementById('llm-model-select');
    
    if (providerSelect && llmApiKeyGroup) {
      providerSelect.addEventListener('change', (e) => {
        const provider = e.target.value;
        
        if (provider) {
          // Show API key group
          llmApiKeyGroup.style.display = 'block';
          
          // Update label text
          const providerName = provider === 'claude' ? 'Anthropic' : 
                              provider === 'openai' ? 'OpenAI' : 'Google';
          if (llmApiKeyLabel) {
            const labelText = llmApiKeyLabel.querySelector('.label-text');
            if (labelText) {
              labelText.textContent = `${providerName} API Key`;
            }
          }
          
          // Update input placeholder
          if (llmApiKeyInput) {
            if (provider === 'claude') {
              llmApiKeyInput.placeholder = 'sk-ant-...';
            } else if (provider === 'openai') {
              llmApiKeyInput.placeholder = 'sk-...';
            } else if (provider === 'gemini') {
              llmApiKeyInput.placeholder = 'Enter API key...';
            }
          }
          
          // Populate model options
          if (llmModelSelect) {
            llmModelSelect.innerHTML = '<option value="">Use default model</option>';
            if (provider === 'claude') {
              llmModelSelect.innerHTML += '<option value="claude-sonnet-4-20250514">Claude Sonnet 4</option>';
              llmModelSelect.innerHTML += '<option value="claude-sonnet-4-5-20250929">Claude Sonnet 4.5</option>';
              llmModelSelect.innerHTML += '<option value="claude-3-haiku-20240307">Claude 3 Haiku</option>';
            } else if (provider === 'openai') {
              llmModelSelect.innerHTML += '<option value="gpt-4o">GPT-4o</option>';
              llmModelSelect.innerHTML += '<option value="gpt-4-turbo">GPT-4 Turbo</option>';
              llmModelSelect.innerHTML += '<option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>';
            } else if (provider === 'gemini') {
              llmModelSelect.innerHTML += '<option value="gemini-pro">Gemini Pro</option>';
              llmModelSelect.innerHTML += '<option value="gemini-1.5-flash">Gemini 1.5 Flash</option>';
            }
          }
        } else {
          // Hide API key group if no provider selected
          llmApiKeyGroup.style.display = 'none';
          if (llmApiKeyInput) llmApiKeyInput.value = '';
          if (llmModelSelect) llmModelSelect.value = '';
        }
      });
    }
  }

  // Initialize API test buttons
  function initAPITestButtons() {
    // Use event delegation on the audits section to handle buttons even when section is hidden/shown
    const auditsSection = document.getElementById('audits-section');
    
    if (auditsSection) {
      // Remove any existing listeners by cloning the section's event handling
      // Use event delegation on the section itself
      auditsSection.addEventListener('click', async (e) => {
        // Klaviyo test button
        if (e.target.id === 'test-klaviyo-btn' || e.target.closest('#test-klaviyo-btn')) {
          e.preventDefault();
          e.stopPropagation();
          await testKlaviyoAPI();
        }
        
        // LLM test button
        if (e.target.id === 'test-llm-btn' || e.target.closest('#test-llm-btn')) {
          e.preventDefault();
          e.stopPropagation();
          await testLLMAPI();
        }
      });
    }
    
    // Also handle direct button clicks (for immediate initialization)
    const testKlaviyoBtn = document.getElementById('test-klaviyo-btn');
    if (testKlaviyoBtn && !testKlaviyoBtn.hasAttribute('data-listener-attached')) {
      testKlaviyoBtn.setAttribute('data-listener-attached', 'true');
      testKlaviyoBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        e.stopPropagation();
        await testKlaviyoAPI();
      });
    }

    const testLLMBtn = document.getElementById('test-llm-btn');
    if (testLLMBtn && !testLLMBtn.hasAttribute('data-listener-attached')) {
      testLLMBtn.setAttribute('data-listener-attached', 'true');
      testLLMBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        e.stopPropagation();
        await testLLMAPI();
      });
    }

    // Klaviyo API test function
    async function testKlaviyoAPI() {
      const apiKeyInput = document.getElementById('klaviyo-api-key');
      if (!apiKeyInput) {
        console.error('Klaviyo API key input not found');
        return;
      }

      const apiKey = apiKeyInput.value.trim();
      
      if (!apiKey) {
        alert('Please enter a Klaviyo API key');
        return;
      }

      const testBtn = document.getElementById('test-klaviyo-btn');
      if (testBtn) {
        testBtn.disabled = true;
        testBtn.textContent = 'Testing...';
      }

      try {
        const response = await fetch(`${window.API_BASE_URL}/api/audit/test-klaviyo`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ api_key: apiKey })
        });

        const data = await response.json();

        if (response.ok && data.success) {
          if (testBtn) {
            testBtn.textContent = '✓ Connected';
            testBtn.style.background = 'var(--color-success)';
            testBtn.style.color = 'white';
          }
          alert('Klaviyo connection successful!');
        } else {
          if (testBtn) {
            testBtn.textContent = 'Test Connection';
            testBtn.style.background = '';
            testBtn.style.color = '';
          }
          alert(`Connection failed: ${data.detail || 'Unknown error'}`);
        }
      } catch (error) {
        console.error('Error testing Klaviyo API:', error);
        if (testBtn) {
          testBtn.textContent = 'Test Connection';
          testBtn.style.background = '';
          testBtn.style.color = '';
        }
        alert('Error testing connection. Please check your network and try again.');
      } finally {
        if (testBtn) {
          testBtn.disabled = false;
        }
      }
    }

    // LLM API test function
    async function testLLMAPI(provider = null) {
      // Get provider from select if not provided
      if (!provider) {
        const providerSelect = document.getElementById('llm-provider-select');
        if (!providerSelect || !providerSelect.value) {
          alert('Please select an LLM provider first');
          return;
        }
        provider = providerSelect.value;
      }

      // Get API key from the unified input
      const apiKeyInput = document.getElementById('llm-api-key-input');
      if (!apiKeyInput) {
        alert('API key input not found. Please select a provider first.');
        return;
      }

      const apiKey = apiKeyInput.value.trim();
      
      if (!apiKey) {
        alert('Please enter an API key');
        return;
      }

      const testBtn = document.getElementById('test-llm-btn');
      if (testBtn) {
        testBtn.disabled = true;
        testBtn.textContent = 'Testing...';
      }

      try {
        const modelSelect = document.getElementById('llm-model-select');
        const model = modelSelect ? modelSelect.value : null;

        const response = await fetch(`${window.API_BASE_URL}/api/audit/test-llm`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            provider: provider,
            api_key: apiKey,
            model: model
          })
        });

        const data = await response.json();

        if (response.ok && data.success) {
          if (testBtn) {
            testBtn.textContent = '✓ Connected';
            testBtn.style.background = 'var(--color-success)';
            testBtn.style.color = 'white';
          }
          alert('LLM connection successful!');
        } else {
          if (testBtn) {
            testBtn.textContent = 'Test Connection';
            testBtn.style.background = '';
            testBtn.style.color = '';
          }
          alert(`Connection failed: ${data.detail || 'Unknown error'}`);
        }
      } catch (error) {
        console.error('Error testing LLM API:', error);
        if (testBtn) {
          testBtn.textContent = 'Test Connection';
          testBtn.style.background = '';
          testBtn.style.color = '';
        }
        alert('Error testing connection. Please check your network and try again.');
      } finally {
        if (testBtn) {
          testBtn.disabled = false;
        }
      }
    }
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

