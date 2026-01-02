/**
 * UI Helper Module
 * Handles progress bars, status updates, logging, and UI state management
 */

(function() {
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
  function updateProgress(percentage) {
    const progressFill = document.getElementById('progress-fill');
    const progressPercentage = document.getElementById('progress-percentage');
    
    if (progressFill && progressPercentage) {
      const clampedPercentage = Math.max(0, Math.min(100, percentage));
      progressFill.style.width = `${clampedPercentage}%`;
      progressPercentage.textContent = `${Math.floor(clampedPercentage)}%`;
      
      // Update stages based on progress
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

  // Export public API
  window.UI = {
    log,
    setStatus,
    updateProgress,
    showProgress,
    hideProgress,
    updateTimeDisplay,
    startCountdownTimer,
    stopCountdownTimer,
    downloadFile,
    getCurrentTimeEstimate: () => currentTimeEstimate
  };
})();

