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
    
    // PRIORITY 1: Check if window.API_URL is explicitly set (for Vercel -> Railway)
    // This is set in index.html or via environment variable
    if (window.API_URL && window.API_URL.trim() !== '' && !window.API_URL.includes('your-app.railway.app')) {
      console.log('Using window.API_URL:', window.API_URL);
      return window.API_URL;
    }
    
    // PRIORITY 2: Check if frontend and API are on same domain (Railway serves frontend from /ui)
    // This works for Railway deployments where frontend is served from /ui
    if (window.location.pathname.startsWith('/ui/') || window.location.pathname === '/ui') {
      // Use relative URLs - same domain
      console.log('Using relative URLs (same domain - Railway)');
      return '';
    }
    
    // PRIORITY 3: Check environment variable (for Vercel builds)
    // Vercel sets this during build via inject-api-url.js
    const envApiUrl = window.API_URL || '';
    if (envApiUrl && !envApiUrl.includes('your-app.railway.app')) {
      console.log('Using environment API_URL:', envApiUrl);
      return envApiUrl;
    }
    
    // FALLBACK: Default Railway URL (should be overridden by window.API_URL)
    console.warn('⚠️ No API URL configured, using default Railway URL');
    return 'https://web-production-2ce0.up.railway.app';
  })();

  console.log('API Base URL:', window.API_BASE_URL);
  console.log('Current location:', window.location.href);
})();

