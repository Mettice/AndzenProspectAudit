/**
 * Main Initialization Module
 * Ties everything together and handles page initialization
 */

(function() {
  'use strict';

  // Initialize everything when DOM is ready
  function init() {
    // Initialize login form
    initLoginForm();
    
    // Initialize logout button
    initLogout();
    
    // Initialize LLM provider selector
    initLLMProviderSelector();
    
    // Initialize API test buttons
    initAPITestButtons();
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
    if (providerSelect) {
      // Initially hide all provider-specific fields
      document.querySelectorAll('[id$="-api-key-label"], [id$="-model-label"]').forEach(el => {
        el.style.display = 'none';
      });
      
      providerSelect.addEventListener('change', (e) => {
        const provider = e.target.value;
        
        // Hide all provider-specific fields
        document.querySelectorAll('[id$="-api-key-label"], [id$="-model-label"]').forEach(el => {
          el.style.display = 'none';
        });

        // Show fields for selected provider (only if a provider is selected)
        if (provider === 'claude') {
          document.getElementById('claude-api-key-label').style.display = 'block';
          document.getElementById('claude-model-label').style.display = 'block';
        } else if (provider === 'openai') {
          document.getElementById('openai-api-key-label').style.display = 'block';
          document.getElementById('openai-model-label').style.display = 'block';
        } else if (provider === 'gemini') {
          document.getElementById('gemini-api-key-label').style.display = 'block';
          document.getElementById('gemini-model-label').style.display = 'block';
        }
      });
    }
  }

  // Initialize API test buttons
  function initAPITestButtons() {
    // Klaviyo API test
    window.testKlaviyoAPI = async function() {
      const apiKey = document.getElementById('klaviyo-api-key').value;
      const statusEl = document.getElementById('klaviyo-api-status');
      
      if (!apiKey) {
        statusEl.textContent = 'Please enter API key';
        statusEl.className = 'api-status error';
        return;
      }

      statusEl.textContent = 'Testing...';
      statusEl.className = 'api-status testing';

      try {
        const response = await fetch(`${window.API_BASE_URL}/api/audit/test-klaviyo`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ api_key: apiKey })
        });

        if (response.ok) {
          statusEl.textContent = '✓ Connected';
          statusEl.className = 'api-status success';
        } else {
          statusEl.textContent = '✗ Failed';
          statusEl.className = 'api-status error';
        }
      } catch (error) {
        statusEl.textContent = '✗ Error';
        statusEl.className = 'api-status error';
      }
    };

    // LLM API test
    window.testLLMAPI = async function(provider) {
      const apiKeyId = provider === 'claude' ? 'claude-api-key' : 
                      provider === 'openai' ? 'openai-api-key' : 'gemini-api-key';
      const statusId = provider === 'claude' ? 'claude-api-status' : 
                      provider === 'openai' ? 'openai-api-status' : 'gemini-api-status';
      
      const apiKey = document.getElementById(apiKeyId).value;
      const statusEl = document.getElementById(statusId);
      
      if (!apiKey) {
        statusEl.textContent = 'Please enter API key';
        statusEl.className = 'api-status error';
        return;
      }

      statusEl.textContent = 'Testing...';
      statusEl.className = 'api-status testing';

      try {
        // Get model if available
        const modelId = provider === 'claude' ? 'claude-model-select' : 
                       provider === 'openai' ? 'openai-model-select' : 'gemini-model-select';
        const modelSelect = document.getElementById(modelId);
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
          statusEl.textContent = '✓ Connected';
          statusEl.className = 'api-status success';
        } else {
          statusEl.textContent = data.message || '✗ Failed';
          statusEl.className = 'api-status error';
        }
      } catch (error) {
        statusEl.textContent = '✗ Error';
        statusEl.className = 'api-status error';
        console.error('LLM test error:', error);
      }
    };
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

