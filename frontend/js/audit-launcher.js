/**
 * Audit Launcher - Multi-step form for creating new audits.
 * Handles form navigation, validation, connection testing, and submission.
 */

class AuditLauncher {
  constructor() {
    this.currentStep = 1;
    this.totalSteps = 3;
    this.formData = {};
    this.init();
  }

  init() {
    this.setupStepNavigation();
    this.setupFormValidation();
    this.setupConnectionTesting();
    this.setupFormSubmission();
    this.setupCustomDateRange();
    this.setupProviderSelection();
    this.loadSavedData();
  }

  setupStepNavigation() {
    const prevBtn = document.getElementById('btn-previous');
    const nextBtn = document.getElementById('btn-next');
    const launchBtn = document.getElementById('btn-launch');

    if (prevBtn) {
      prevBtn.addEventListener('click', () => this.previousStep());
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', () => this.nextStep());
    }

    if (launchBtn) {
      launchBtn.addEventListener('click', () => this.submitAudit());
    }

    // Cancel button
    const cancelBtn = document.getElementById('cancel-audit');
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => this.cancelAudit());
    }
  }

  setupFormValidation() {
    // Real-time validation for required fields
    const requiredFields = document.querySelectorAll('[required]');
    requiredFields.forEach(field => {
      field.addEventListener('blur', () => this.validateField(field));
      field.addEventListener('input', () => {
        if (field.classList.contains('error')) {
          this.validateField(field);
        }
      });
    });
  }

  validateField(field) {
    const value = field.value.trim();
    const isValid = field.checkValidity();

    if (!isValid) {
      field.classList.add('error');
      this.showFieldError(field, field.validationMessage);
    } else {
      field.classList.remove('error');
      this.hideFieldError(field);
    }

    return isValid;
  }

  validateStep(stepNumber) {
    const step = document.getElementById(`step-${stepNumber}`);
    if (!step) return false;

    const requiredFields = step.querySelectorAll('[required]');
    let isValid = true;

    requiredFields.forEach(field => {
      if (!this.validateField(field)) {
        isValid = false;
      }
    });

    return isValid;
  }

  showFieldError(field, message) {
    this.hideFieldError(field);
    const errorEl = document.createElement('div');
    errorEl.className = 'field-error';
    errorEl.textContent = message;
    field.parentElement.appendChild(errorEl);
  }

  hideFieldError(field) {
    const errorEl = field.parentElement.querySelector('.field-error');
    if (errorEl) {
      errorEl.remove();
    }
  }

  nextStep() {
    if (!this.validateStep(this.currentStep)) {
      this.showError('Please fill in all required fields.');
      return;
    }

    this.saveStepData(this.currentStep);

    if (this.currentStep < this.totalSteps) {
      this.currentStep++;
      this.updateStepDisplay();
    }
  }

  previousStep() {
    if (this.currentStep > 1) {
      this.currentStep--;
      this.updateStepDisplay();
    }
  }

  updateStepDisplay() {
    // Hide all steps
    for (let i = 1; i <= this.totalSteps; i++) {
      const step = document.getElementById(`step-${i}`);
      if (step) {
        step.classList.remove('active');
      }
    }

    // Show current step
    const currentStepEl = document.getElementById(`step-${this.currentStep}`);
    if (currentStepEl) {
      currentStepEl.classList.add('active');
    }

    // Update step indicators
    const indicators = document.querySelectorAll('.step-indicators .indicator');
    indicators.forEach((indicator, index) => {
      if (index < this.currentStep) {
        indicator.classList.add('active');
      } else {
        indicator.classList.remove('active');
      }
    });

    // Update progress indicator in header
    const headerSteps = document.querySelectorAll('.progress-indicator .step');
    headerSteps.forEach((step, index) => {
      if (index < this.currentStep) {
        step.classList.add('active');
      } else {
        step.classList.remove('active');
      }
    });

    // Update navigation buttons
    const prevBtn = document.getElementById('btn-previous');
    const nextBtn = document.getElementById('btn-next');
    const launchBtn = document.getElementById('btn-launch');

    if (prevBtn) {
      prevBtn.disabled = this.currentStep === 1;
    }

    if (nextBtn) {
      nextBtn.style.display = this.currentStep < this.totalSteps ? 'block' : 'none';
    }

    if (launchBtn) {
      launchBtn.style.display = this.currentStep === this.totalSteps ? 'block' : 'none';
    }
  }

  saveStepData(stepNumber) {
    const step = document.getElementById(`step-${stepNumber}`);
    if (!step) return;

    const inputs = step.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
      if (input.name) {
        this.formData[input.name] = input.value;
      }
    });

    // Save to localStorage
    localStorage.setItem('auditLauncherData', JSON.stringify(this.formData));
  }

  loadSavedData() {
    const saved = localStorage.getItem('auditLauncherData');
    if (saved) {
      try {
        this.formData = JSON.parse(saved);
        this.populateForm(this.formData);
      } catch (e) {
        console.error('Error loading saved data:', e);
      }
    }
  }

  populateForm(data) {
    Object.keys(data).forEach(key => {
      const field = document.querySelector(`[name="${key}"]`);
      if (field) {
        field.value = data[key];
      }
    });
  }

  setupCustomDateRange() {
    const periodSelect = document.getElementById('analysis-period');
    const customRange = document.getElementById('custom-date-range');

    if (periodSelect && customRange) {
      periodSelect.addEventListener('change', (e) => {
        if (e.target.value === 'custom') {
          customRange.style.display = 'block';
        } else {
          customRange.style.display = 'none';
        }
      });
    }
  }

  setupProviderSelection() {
    const defaultOption = document.querySelector('[data-provider="default"]');
    const customOption = document.querySelector('[data-provider="custom"]');
    const customConfig = document.getElementById('custom-ai-config');
    const providerCards = document.querySelectorAll('.provider-card');
    const aiApiConfig = document.getElementById('ai-api-config');

    if (defaultOption) {
      defaultOption.addEventListener('click', () => {
        this.selectProvider('default');
        if (customConfig) customConfig.style.display = 'none';
      });
    }

    if (customOption) {
      customOption.addEventListener('click', () => {
        this.selectProvider('custom');
        if (customConfig) customConfig.style.display = 'block';
      });
    }

    providerCards.forEach(card => {
      card.addEventListener('click', () => {
        const provider = card.dataset.provider;
        this.selectProvider('custom', provider);
        if (aiApiConfig) aiApiConfig.style.display = 'block';
      });
    });
  }

  selectProvider(type, provider = null) {
    this.formData.ai_provider_type = type;
    if (provider) {
      this.formData.llm_provider = provider;
    }
  }

  setupConnectionTesting() {
    // Klaviyo connection test
    const testKlaviyoBtn = document.getElementById('test-klaviyo');
    if (testKlaviyoBtn) {
      testKlaviyoBtn.addEventListener('click', () => this.testKlaviyoConnection());
    }

    // AI connection test
    const testAIBtn = document.getElementById('test-ai');
    if (testAIBtn) {
      testAIBtn.addEventListener('click', () => this.testAIConnection());
    }

    // API key visibility toggle
    const toggleApiKey = document.getElementById('toggle-api-key');
    if (toggleApiKey) {
      toggleApiKey.addEventListener('click', () => {
        const apiKeyInput = document.getElementById('api-key');
        if (apiKeyInput) {
          apiKeyInput.type = apiKeyInput.type === 'password' ? 'text' : 'password';
        }
      });
    }
  }

  async testKlaviyoConnection() {
    const apiKeyInput = document.getElementById('api-key');
    const apiKey = apiKeyInput?.value.trim();

    if (!apiKey) {
      this.showError('Please enter a Klaviyo API key first.');
      return;
    }

    const testBtn = document.getElementById('test-klaviyo');
    const statusEl = document.getElementById('klaviyo-status');
    const resultsEl = document.getElementById('connection-results');

    if (testBtn) testBtn.disabled = true;
    if (statusEl) {
      statusEl.innerHTML = '<span class="status-dot pending"></span><span class="status-text">Testing...</span>';
    }

    try {
      const response = await fetch('/api/audit/test-klaviyo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKey })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        if (statusEl) {
          statusEl.innerHTML = '<span class="status-dot success"></span><span class="status-text">Connected</span>';
        }
        if (resultsEl) {
          resultsEl.style.display = 'block';
          // Populate preview data if available
          if (data.account_name) {
            const accountNameEl = document.getElementById('account-name');
            if (accountNameEl) accountNameEl.textContent = data.account_name;
          }
        }
      } else {
        throw new Error(data.detail || 'Connection failed');
      }
    } catch (error) {
      console.error('Klaviyo connection test failed:', error);
      if (statusEl) {
        statusEl.innerHTML = '<span class="status-dot error"></span><span class="status-text">Failed</span>';
      }
      this.showError(`Connection test failed: ${error.message}`);
    } finally {
      if (testBtn) testBtn.disabled = false;
    }
  }

  async testAIConnection() {
    const apiKeyInput = document.getElementById('ai-api-key');
    const modelSelect = document.getElementById('ai-model');
    const provider = this.formData.llm_provider || 'claude';

    const apiKey = apiKeyInput?.value.trim();
    const model = modelSelect?.value || '';

    if (!apiKey) {
      this.showError('Please enter an API key first.');
      return;
    }

    const testBtn = document.getElementById('test-ai');
    if (testBtn) testBtn.disabled = true;

    try {
      const requestBody = {
        provider: provider,
        api_key: apiKey
      };
      if (model) {
        requestBody.model = model;
      }

      const response = await fetch('/api/audit/test-llm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      const data = await response.json();

      if (response.ok && data.success) {
        this.showSuccess('AI connection successful!');
      } else {
        throw new Error(data.detail || 'Connection failed');
      }
    } catch (error) {
      console.error('AI connection test failed:', error);
      this.showError(`Connection test failed: ${error.message}`);
    } finally {
      if (testBtn) testBtn.disabled = false;
    }
  }

  setupFormSubmission() {
    // Form is submitted via launch button
  }

  async submitAudit() {
    if (!this.validateStep(this.currentStep)) {
      this.showError('Please fill in all required fields.');
      return;
    }

    this.saveStepData(this.currentStep);

    // Build request payload
    const requestData = this.buildRequestData();

    // Show loading modal
    this.showLoadingModal();

    try {
      const response = await fetch('/api/audit/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Clear saved form data
        localStorage.removeItem('auditLauncherData');

        // Navigate to report viewer or show success
        if (data.report_id) {
          this.hideLoadingModal();
          window.location.href = `report-viewer.html?reportId=${data.report_id}`;
        } else {
          // Poll for status
          this.pollReportStatus(data.report_id);
        }
      } else {
        throw new Error(data.detail || 'Audit generation failed');
      }
    } catch (error) {
      console.error('Audit submission failed:', error);
      this.hideLoadingModal();
      this.showError(`Failed to start audit: ${error.message}`);
    }
  }

  buildRequestData() {
    const data = {
      client_name: this.formData.client_name,
      api_key: this.formData.api_key,
      days: parseInt(this.formData.days) || 90,
      industry: this.formData.industry || 'apparel_accessories'
    };

    if (this.formData.auditor_name) {
      data.auditor_name = this.formData.auditor_name;
    }

    if (this.formData.client_code) {
      data.client_code = this.formData.client_code;
    }

    if (this.formData.client_type) {
      data.client_type = this.formData.client_type;
    }

    // Custom date range
    if (this.formData.days === 'custom' && this.formData.start_date && this.formData.end_date) {
      data.date_range = {
        start: this.formData.start_date,
        end: this.formData.end_date
      };
    }

    // AI configuration
    if (this.formData.ai_provider_type === 'custom' && this.formData.llm_provider) {
      data.llm_provider = this.formData.llm_provider;

      const aiApiKey = document.getElementById('ai-api-key')?.value;
      if (aiApiKey) {
        if (this.formData.llm_provider === 'claude') {
          data.anthropic_api_key = aiApiKey;
        } else if (this.formData.llm_provider === 'openai') {
          data.openai_api_key = aiApiKey;
        } else if (this.formData.llm_provider === 'gemini') {
          data.gemini_api_key = aiApiKey;
        }
      }

      const aiModel = document.getElementById('ai-model')?.value;
      if (aiModel) {
        if (this.formData.llm_provider === 'claude') {
          data.claude_model = aiModel;
        } else if (this.formData.llm_provider === 'openai') {
          data.openai_model = aiModel;
        } else if (this.formData.llm_provider === 'gemini') {
          data.gemini_model = aiModel;
        }
      }
    }

    return data;
  }

  async pollReportStatus(reportId) {
    const maxAttempts = 300; // 5 minutes max
    let attempts = 0;

    const poll = async () => {
      attempts++;

      try {
        const response = await fetch(`/api/audit/status/${reportId}`);
        const data = await response.json();

        if (data.status === 'completed') {
          this.hideLoadingModal();
          window.location.href = `report-viewer.html?reportId=${reportId}`;
          return;
        } else if (data.status === 'failed') {
          throw new Error(data.error || 'Audit generation failed');
        } else {
          // Update progress - handle both formats (top-level or nested in report_data)
          const progress = data.progress || data.report_data?.progress || 0;
          const step = data.step || data.report_data?.step || 'Processing...';

          console.log(`Progress update: ${progress}% - ${step}`);
          this.updateProgress(progress, step);

          if (attempts < maxAttempts) {
            setTimeout(poll, 2000); // Poll every 2 seconds
          } else {
            throw new Error('Audit generation timed out');
          }
        }
      } catch (error) {
        console.error('Error polling status:', error);
        this.hideLoadingModal();
        this.showError(`Failed to check audit status: ${error.message}`);
      }
    };

    poll();
  }

  updateProgress(progress, step) {
    const progressPercent = document.querySelector('.progress-percent');
    const progressLabel = document.querySelector('.progress-label');
    const progressDescription = document.getElementById('progress-description');

    if (progressPercent) {
      progressPercent.textContent = `${Math.round(progress)}%`;
    }

    if (progressLabel) {
      progressLabel.textContent = step;
    }

    if (progressDescription) {
      progressDescription.textContent = step;
    }

    // Update progress steps
    const progressSteps = document.querySelectorAll('.progress-step');
    if (progress < 25) {
      progressSteps[0]?.classList.add('active');
    } else if (progress < 50) {
      progressSteps[0]?.classList.add('active');
      progressSteps[1]?.classList.add('active');
    } else if (progress < 75) {
      progressSteps[0]?.classList.add('active');
      progressSteps[1]?.classList.add('active');
      progressSteps[2]?.classList.add('active');
    } else {
      progressSteps.forEach(step => step.classList.add('active'));
    }
  }

  showLoadingModal() {
    const modal = document.getElementById('loading-modal');
    if (modal) {
      modal.style.display = 'flex';
    }
  }

  hideLoadingModal() {
    const modal = document.getElementById('loading-modal');
    if (modal) {
      modal.style.display = 'none';
    }
  }

  cancelAudit() {
    if (confirm('Are you sure you want to cancel this audit?')) {
      this.hideLoadingModal();
      // Could implement cancellation API call here
    }
  }

  showError(message) {
    // Simple error display - could be enhanced with toast notifications
    alert(message);
  }

  showSuccess(message) {
    // Simple success display - could be enhanced with toast notifications
    console.log('Success:', message);
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.auditLauncher = new AuditLauncher();
  });
} else {
  window.auditLauncher = new AuditLauncher();
}

// Export for use in other modules
window.AuditLauncher = AuditLauncher;

