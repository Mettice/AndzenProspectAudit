/**
 * Audit Generation Module
 * Handles audit form submission, status polling, and report display
 */

(function() {
  'use strict';

  let startTime = null;
  let pollTimer = null;
  let currentReportId = null;
  let initialProgressInterval = null;

  // Initialize audit form
  function initAuditForm() {
    const form = document.getElementById('audit-form');
    const periodSelect = document.getElementById('period-select');
    const customDates = document.getElementById('custom-dates');
    const submitBtn = document.getElementById('submit-btn');

    // Update YTD option label
    updateYTDOption();

    // Handle period selection
    if (periodSelect) {
      periodSelect.addEventListener('change', (e) => {
        if (e.target.value === 'custom') {
          customDates.style.display = 'block';
        } else {
          customDates.style.display = 'none';
        }
      });
    }

    // Handle form submission
    if (form) {
      form.addEventListener('submit', handleAuditSubmit);
    }
  }

  // Update YTD option label
  function updateYTDOption() {
    const today = new Date();
    const yearStart = new Date(today.getFullYear(), 0, 1);
    const daysSinceYearStart = Math.floor((today - yearStart) / (1000 * 60 * 60 * 24));
    const ytdOption = document.getElementById('ytd-option');
    if (ytdOption) {
      ytdOption.textContent = `Year to Date (YTD) - ${daysSinceYearStart} days`;
    }
  }

  // Handle audit form submission
  async function handleAuditSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = document.getElementById('submit-btn');
    submitBtn.disabled = true;

    try {
      // Build payload
      const formData = new FormData(form);
      const payload = {
        api_key: formData.get('api_key'),
        client_name: formData.get('client_name'),
        client_code: formData.get('client_code') || null,
        auditor_name: formData.get('auditor_name') || null,
        industry: formData.get('industry') || 'apparel_accessories',
      };

      // LLM configuration
      const llmProvider = formData.get('llm_provider');
      if (llmProvider) {
        payload.llm_provider = llmProvider;
        if (llmProvider === 'claude') {
          payload.anthropic_api_key = formData.get('anthropic_api_key') || null;
          payload.claude_model = formData.get('claude_model') || null;
        } else if (llmProvider === 'openai') {
          payload.openai_api_key = formData.get('openai_api_key') || null;
          payload.openai_model = formData.get('openai_model') || null;
        } else if (llmProvider === 'gemini') {
          payload.gemini_api_key = formData.get('gemini_api_key') || null;
          payload.gemini_model = formData.get('gemini_model') || null;
        }
      }

      // Date range handling
      const period = formData.get('period');
      if (period === 'custom') {
        const startDate = formData.get('start_date');
        const endDate = formData.get('end_date');
        if (startDate && endDate) {
          payload.date_range = {
            start: new Date(startDate).toISOString(),
            end: new Date(endDate + 'T23:59:59Z').toISOString()
          };
        }
      } else if (period === 'ytd') {
        const today = new Date();
        const yearStart = new Date(today.getFullYear(), 0, 1);
        const todayEnd = new Date(today);
        todayEnd.setUTCHours(23, 59, 59, 999);
        
        payload.date_range = {
          start: yearStart.toISOString(),
          end: todayEnd.toISOString()
        };
        
        const daysSinceYearStart = Math.floor((today - yearStart) / (1000 * 60 * 60 * 24));
        payload.days = daysSinceYearStart;
        
        window.UI.log(`Year to Date: ${yearStart.toISOString().split('T')[0]} to ${todayEnd.toISOString().split('T')[0]} (${daysSinceYearStart} days)`);
      } else {
        const days = parseInt(period);
        const endDate = new Date();
        const startDate = new Date(endDate);
        startDate.setUTCDate(startDate.getUTCDate() - days);
        startDate.setUTCHours(0, 0, 0, 0);
        
        payload.date_range = {
          start: startDate.toISOString(),
          end: endDate.toISOString()
        };
        payload.days = days;
        
        window.UI.log(`${days} days period: ${startDate.toISOString().split('T')[0]} to ${endDate.toISOString()}`);
      }

      window.UI.log('Submitting audit request...');
      window.UI.showProgress();
      
      // Start initial progress animation (will be replaced by real progress from server)
      startInitialProgressAnimation();

      // Submit audit request
      const token = window.Auth.getAuthToken();
      const headers = { 'Content-Type': 'application/json' };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const res = await fetch(`${window.API_BASE_URL}/api/audit/generate`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(payload)
      });
      
      const json = await res.json();
      if (!res.ok || !json.success) {
        throw new Error(json.detail || 'Failed to start audit generation');
      }

      const reportId = json.report_id || json.report_data?.report_id;
      if (!reportId) {
        throw new Error('No report ID returned from server');
      }

      currentReportId = reportId;
      window.UI.log(`Audit generation started. Report ID: ${reportId}`);
      window.UI.log('Polling for status...');

      // Start polling
      startTime = Date.now();
      await pollStatus(reportId, headers);
      pollTimer = setInterval(() => pollStatus(reportId, headers), 5000);

    } catch (err) {
      stopInitialProgressAnimation();
      window.UI.hideProgress();
      window.UI.setStatus('Error', 'error');
      
      let errorMessage = err.message;
      if (err.name === 'AbortError' || err.message.includes('timeout')) {
        errorMessage = 'Request timed out. Please try again.';
      } else if (err.message === 'Failed to fetch') {
        errorMessage = 'Network error. Check your connection.';
      }
      
      window.UI.log('Error: ' + errorMessage);
      const resultBox = document.getElementById('result-box');
      if (resultBox) {
        resultBox.innerHTML = `<p class="error">Error: ${errorMessage}</p>`;
      }
    } finally {
      submitBtn.disabled = false;
    }
  }

  // Poll for audit status
  async function pollStatus(reportId, headers) {
    try {
      const statusRes = await fetch(`${window.API_BASE_URL}/api/audit/status/${reportId}`, {
        method: 'GET',
        headers: headers
      });
      
      if (!statusRes.ok) {
        throw new Error(`Status check failed: ${statusRes.statusText}`);
      }
      
      const statusJson = await statusRes.json();
      
      // Update UI visibility
      const progressContainer = document.getElementById('progress-container');
      const resultBox = document.getElementById('result-box');
      if (progressContainer && resultBox) {
        if (statusJson.status === 'processing') {
          progressContainer.style.display = 'block';
          resultBox.style.display = 'none';
        } else if (statusJson.status === 'completed' || statusJson.status === 'failed') {
          progressContainer.style.display = 'none';
          resultBox.style.display = 'block';
        }
      }
      
      // Update progress
      if (statusJson.progress !== undefined) {
        // Stop initial animation once we get real progress from server
        stopInitialProgressAnimation();
        
        window.UI.updateProgress(statusJson.progress);
        
        const reportData = statusJson.report_data || {};
        if (reportData.start_time && !startTime) {
          startTime = new Date(reportData.start_time).getTime();
        } else if (!startTime) {
          startTime = Date.now();
        }
        
        // Handle time estimates
        const serverEstimate = reportData.estimated_remaining_minutes;
        const currentProgress = statusJson.progress || 0;
        
        if (statusJson.status === 'processing') {
          if (currentProgress >= 95) {
            window.UI.stopCountdownTimer();
            window.UI.updateTimeDisplay(0);
          } else if (serverEstimate !== undefined && serverEstimate !== null && serverEstimate > 0) {
            window.UI.startCountdownTimer(serverEstimate);
          }
        }
      }
      
      // Handle completion
      if (statusJson.status === 'completed') {
        if (pollTimer) {
          clearInterval(pollTimer);
          pollTimer = null;
        }
        stopInitialProgressAnimation();
        window.UI.stopCountdownTimer();
        window.UI.hideProgress();
        window.UI.setStatus('Completed', 'success');
        window.UI.log('Audit completed successfully.');
        
        displayReport(statusJson, reportId);
        return;
      }
      
      // Handle failure
      if (statusJson.status === 'failed') {
        if (pollTimer) {
          clearInterval(pollTimer);
          pollTimer = null;
        }
        stopInitialProgressAnimation();
        window.UI.hideProgress();
        window.UI.setStatus('Failed', 'error');
        throw new Error(statusJson.error || 'Audit generation failed');
      }
      
      // Still processing
      if (statusJson.status === 'processing') {
        window.UI.log(`Status: Processing... (${Math.round(statusJson.progress || 0)}%)`);
      }
      
    } catch (error) {
      if (error.message.includes('failed') || error.message.includes('Audit generation')) {
        if (pollTimer) {
          clearInterval(pollTimer);
          pollTimer = null;
        }
        stopInitialProgressAnimation();
        window.UI.hideProgress();
        window.UI.setStatus('Error', 'error');
        throw error;
      }
      window.UI.log(`Status check error: ${error.message}. Retrying...`);
    }
  }

  // Start initial progress animation (before server responds)
  function startInitialProgressAnimation() {
    // Stop any existing animation
    if (initialProgressInterval) {
      clearInterval(initialProgressInterval);
      initialProgressInterval = null;
    }
    
    let progress = 0;
    const ESTIMATED_TIME_MS = 27.5 * 60 * 1000; // 27.5 minutes in milliseconds
    startTime = Date.now();
    
    initialProgressInterval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const estimatedProgress = Math.min(95, (elapsed / ESTIMATED_TIME_MS) * 100);
      
      // Smooth progress animation
      progress = Math.min(progress + 0.3, estimatedProgress);
      window.UI.updateProgress(progress);
      
      // Stop animation once we get real progress from server (handled in pollStatus)
    }, 100); // Update every 100ms
  }

  // Stop initial progress animation
  function stopInitialProgressAnimation() {
    if (initialProgressInterval) {
      clearInterval(initialProgressInterval);
      initialProgressInterval = null;
    }
  }

  // Display completed report
  function displayReport(statusJson, reportId) {
    const resultBox = document.getElementById('result-box');
    if (!resultBox) return;

    const htmlContent = statusJson.html_content;
    const reportData = statusJson.report_data || {};
    const reportFilename = reportData.filename || 'report.html';

    // Build download buttons
    function getFullDownloadUrl(relativePath) {
      if (!relativePath) return null;
      if (relativePath.startsWith('http')) return relativePath;
      if (relativePath.startsWith('/')) return `${window.API_BASE_URL}${relativePath}`;
      return `${window.API_BASE_URL}/api/audit/download-file?path=${encodeURIComponent(relativePath)}`;
    }

    let downloadButtons = '<div class="download-buttons">';
    
    const htmlDownloadUrl = getFullDownloadUrl(reportData.html_url);
    if (htmlDownloadUrl) {
      downloadButtons += `<button class="btn-download" onclick="window.UI.downloadFile('${htmlDownloadUrl}', '${reportFilename}')">Download HTML</button>`;
    }
    
    const pdfDownloadUrl = getFullDownloadUrl(reportData.pdf_url);
    if (pdfDownloadUrl) {
      const pdfFilename = reportFilename.replace('.html', '.pdf');
      downloadButtons += `<button class="btn-download" onclick="window.UI.downloadFile('${pdfDownloadUrl}', '${pdfFilename}')">Download PDF</button>`;
    } else {
      downloadButtons += `<button class="btn-download btn-disabled" disabled title="PDF generation failed or unavailable">Download PDF (Unavailable)</button>`;
    }
    
    const wordDownloadUrl = getFullDownloadUrl(reportData.word_url);
    if (wordDownloadUrl) {
      const wordFilename = reportFilename.replace('.html', '.docx');
      downloadButtons += `<button class="btn-download" onclick="window.UI.downloadFile('${wordDownloadUrl}', '${wordFilename}')">Download Word</button>`;
    } else {
      downloadButtons += `<button class="btn-download btn-disabled" disabled title="Word generation failed or unavailable">Download Word (Unavailable)</button>`;
    }
    
    downloadButtons += '</div>';

    // Display report with editable interface
    if (htmlContent) {
      // Initialize editable report + chat interface
      window.Editor.initReportEditor(reportId, htmlContent, reportFilename, downloadButtons);
    } else {
      resultBox.innerHTML = `
        <div class="success-box">
          <p class="label">Report Generated Successfully</p>
          <p class="value">${reportFilename}</p>
          ${downloadButtons}
        </div>
        <p>Report generated. Use download buttons above.</p>
      `;
    }
  }

  // Export public API
  window.Audit = {
    initAuditForm,
    getCurrentReportId: () => currentReportId
  };

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      initAuditForm();
    });
  } else {
    initAuditForm();
  }
})();

