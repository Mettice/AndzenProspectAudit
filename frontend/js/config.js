/**
 * API Configuration Module
 * Handles API URL detection for local and production environments
 */

(function() {
  'use strict';

  // API URL configuration - supports both local development and production
  window.API_BASE_URL = (() => {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      // Use the same port as the current page
      const port = window.location.port || (window.location.protocol === 'https:' ? '443' : '80');
      // If port is 8001, use 8001, otherwise default to 8000
      const apiPort = port === '8001' ? '8001' : '8000';
      return `http://${window.location.hostname}:${apiPort}`;
    }
    // For production:
    // Check if window.API_URL is set and not a placeholder
    if (window.API_URL && !window.API_URL.includes('your-app.railway.app')) {
      return window.API_URL;
    }
    // Default to Railway deployment URL
    return 'https://web-production-2ce0.up.railway.app';
  })();

  console.log('API Base URL:', window.API_BASE_URL);
  console.log('Current location:', window.location.href);
})();

