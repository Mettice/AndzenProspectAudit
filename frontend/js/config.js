/**
 * API Configuration Module
 * Handles API URL detection for local and production environments
 */

(function() {
  'use strict';

  // API URL configuration - supports both local development and production
  window.API_BASE_URL = (() => {
    // For local development
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      // Use the same port as the current page
      const port = window.location.port || (window.location.protocol === 'https:' ? '443' : '80');
      // If port is 8001, use 8001, otherwise default to 8000
      const apiPort = port === '8001' ? '8001' : '8000';
      return `http://${window.location.hostname}:${apiPort}`;
    }
    
    // For production: Use relative URLs if frontend and API are on same domain
    // This works for Railway deployments where frontend is served from /ui
    // Check if we're on the same domain (Railway serves frontend from /ui)
    if (window.location.pathname.startsWith('/ui/') || window.location.pathname === '/ui') {
      // Use relative URLs - same domain
      return '';
    }
    
    // Fallback: Check if window.API_URL is set and not a placeholder
    if (window.API_URL && !window.API_URL.includes('your-app.railway.app')) {
      return window.API_URL;
    }
    
    // Last resort: Use empty string for relative URLs (same domain)
    // This assumes frontend and API are on the same domain
    return '';
  })();

  console.log('API Base URL:', window.API_BASE_URL);
  console.log('Current location:', window.location.href);
})();

