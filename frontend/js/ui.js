/**
 * UI Helper Module
 * Handles progress bars, status updates, logging, and UI state management
 */

(function () {
  'use strict';

  let progressInterval = null;
  let countdownInterval = null;
  let currentTimeEstimate = 0;

  // Logging function
  function log(message) {
    const logBox = document.getElementById('log-box');
    if (logBox) {
      const timestamp = new Date().toLocaleTimeString();
      const logEntry = document.createElement('div');
      logEntry.className = 'log-entry';
      logEntry.textContent = `[${timestamp}] ${message}`;
      logBox.appendChild(logEntry);
      logBox.scrollTop = logBox.scrollHeight;
    }
    console.log(message);
  }

  // Status pill update
  function setStatus(text, type = 'info') {
    const statusPill = document.getElementById('status-pill');
    if (statusPill) {
      statusPill.textContent = text;
      statusPill.className = `status status-${type}`;
    }
  }

  // Progress bar update
  function updateProgress(percentage, step = null) {
    const clampedPercentage = Math.max(0, Math.min(100, percentage));

    // Update old progress bar (if exists)
    const progressFill = document.getElementById('progress-fill');
    const progressPercentage = document.getElementById('progress-percentage');

    if (progressFill && progressPercentage) {
      progressFill.style.width = `${clampedPercentage}%`;
      progressPercentage.textContent = `${Math.floor(clampedPercentage)}%`;
    }

    // Update new dashboard modal progress (if exists)
    const progressPercent = document.getElementById('progress-percent');
    const progressLabel = document.getElementById('progress-label');

    if (progressPercent) {
      progressPercent.textContent = `${Math.floor(clampedPercentage)}%`;
    }

    if (progressLabel && step) {
      progressLabel.textContent = step;
    }

    // Update progress steps based on percentage
    updateProgressSteps(clampedPercentage);

    // Update stages based on progress (old modal)
    const stages = document.querySelectorAll('.stage');
    const stageIndex = Math.floor((clampedPercentage / 100) * stages.length);
    stages.forEach((stage, idx) => {
      if (idx < stageIndex) {
        stage.classList.add('completed');
        stage.classList.remove('active');
      } else if (idx === stageIndex) {
        stage.classList.add('active');
        stage.classList.remove('completed');
      } else {
        stage.classList.remove('active', 'completed');
      }
    });
  }


  // Update progress steps for new dashboard modal
  function updateProgressSteps(percentage) {
    const progressSteps = document.querySelectorAll('.progress-step');
    if (!progressSteps.length) return;

    // Define step thresholds
    const stepThresholds = [10, 40, 80, 95]; // When each step becomes active

    progressSteps.forEach((step, index) => {
      step.classList.remove('active', 'completed');

      if (percentage >= stepThresholds[index]) {
        if (index === stepThresholds.length - 1 || percentage < stepThresholds[index + 1]) {
          step.classList.add('active'); // Current step
        } else {
          step.classList.add('completed'); // Completed step
        }
      }
    });
  }

  // Show progress container with initial animation
  function showProgress() {
    const progressContainer = document.getElementById('progress-container');
    const resultBox = document.getElementById('result-box');

    if (resultBox) {
      resultBox.style.display = 'none';
    }
    if (progressContainer) {
      progressContainer.style.display = 'block';
    }

    // Reset progress bar
    const progressFill = document.getElementById('progress-fill');
    const progressPercentage = document.getElementById('progress-percentage');
    if (progressFill) {
      progressFill.style.width = '0%';
    }
    if (progressPercentage) {
      progressPercentage.textContent = '0%';
    }

    // Reset stages
    const stages = document.querySelectorAll('.stage');
    stages.forEach((stage, idx) => {
      stage.classList.remove('active', 'completed');
      if (idx === 0) {
        stage.classList.add('active');
      }
    });

    // Start countdown with default estimate (will be updated when server responds)
    startCountdownTimer(30);

    setStatus('Processing', 'processing');
  }

  // Hide progress container
  function hideProgress() {
    // Stop any running intervals
    if (progressInterval) {
      clearInterval(progressInterval);
      progressInterval = null;
    }
    stopCountdownTimer();

    const progressContainer = document.getElementById('progress-container');
    const resultBox = document.getElementById('result-box');

    if (progressContainer) {
      progressContainer.style.display = 'none';
    }
    if (resultBox) {
      resultBox.style.display = 'block';
    }

    // Complete the progress bar
    const progressFill = document.getElementById('progress-fill');
    const progressPercentage = document.getElementById('progress-percentage');
    if (progressFill) {
      progressFill.style.width = '100%';
    }
    if (progressPercentage) {
      progressPercentage.textContent = '100%';
    }

    // Mark all stages as completed
    const stages = document.querySelectorAll('.stage');
    stages.forEach(stage => {
      stage.classList.add('completed');
      stage.classList.remove('active');
    });

    setStatus('Idle', 'idle');
  }

  // Time display update
  function updateTimeDisplay(minutes) {
    const timeElement = document.getElementById('progress-time');
    if (timeElement) {
      if (minutes <= 0) {
        timeElement.textContent = 'Almost done...';
      } else if (minutes < 1) {
        timeElement.textContent = 'Less than 1 minute';
      } else {
        timeElement.textContent = `Estimated time remaining: ${Math.round(minutes)} minute${Math.round(minutes) !== 1 ? 's' : ''}`;
      }
    }
  }

  // Start countdown timer
  function startCountdownTimer(initialMinutes) {
    stopCountdownTimer();
    currentTimeEstimate = initialMinutes;
    let remainingSeconds = Math.floor(initialMinutes * 60);

    updateTimeDisplay(initialMinutes);

    countdownInterval = setInterval(() => {
      remainingSeconds--;
      const minutes = Math.ceil(remainingSeconds / 60);
      updateTimeDisplay(minutes);

      if (remainingSeconds <= 0) {
        stopCountdownTimer();
        updateTimeDisplay(0);
      }
    }, 1000);
  }

  // Stop countdown timer
  function stopCountdownTimer() {
    if (countdownInterval) {
      clearInterval(countdownInterval);
      countdownInterval = null;
    }
  }

  // Download file helper
  function downloadFile(url, filename) {
    if (!url) {
      console.error('No URL provided for download');
      return;
    }

    const token = window.Auth.getAuthToken();
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // For HTTP URLs, use fetch and download
    fetch(url, { headers })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.blob();
      })
      .then(blob => {
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(downloadUrl);
      })
      .catch(err => {
        log(`Error downloading ${filename}: ${err.message}`);
        // Fallback: try opening in new window
        window.open(url, '_blank');
      });
  }

  // Simple toast notification system
  function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
      toastContainer = document.createElement('div');
      toastContainer.id = 'toast-container';
      toastContainer.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        pointer-events: none;
      `;
      document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.style.cssText = `
      background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : type === 'warning' ? '#f59e0b' : '#3b82f6'};
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      margin-bottom: 8px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      pointer-events: auto;
      max-width: 300px;
      word-wrap: break-word;
      font-family: 'Montserrat', sans-serif;
      font-size: 14px;
      font-weight: 500;
      opacity: 0;
      transform: translateX(100px);
      transition: all 0.3s ease;
    `;
    toast.textContent = message;

    toastContainer.appendChild(toast);

    // Animate in
    setTimeout(() => {
      toast.style.opacity = '1';
      toast.style.transform = 'translateX(0)';
    }, 10);

    // Auto remove after 5 seconds
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100px)';
      setTimeout(() => {
        if (toast.parentNode) {
          toast.parentNode.removeChild(toast);
        }
      }, 300);
    }, 5000);
  }

  // Export public API
  window.UI = {
    log,
    setStatus,
    updateProgress,
    showProgress,
    showToast,
    hideProgress,
    updateTimeDisplay,
    startCountdownTimer,
    stopCountdownTimer,
    downloadFile,
    getCurrentTimeEstimate: () => currentTimeEstimate
  };
})();

