/**
 * Authentication Module
 * Handles login, logout, token management, and user state
 */

(function() {
  'use strict';

  // Authentication State Management
  let authToken = null;
  let currentUser = null;

  // Get token from localStorage
  function getAuthToken() {
    return localStorage.getItem('auth_token');
  }

  // Save token to localStorage
  function setAuthToken(token) {
    localStorage.setItem('auth_token', token);
    authToken = token;
  }

  // Remove token from localStorage
  function clearAuthToken() {
    localStorage.removeItem('auth_token');
    authToken = null;
    currentUser = null;
  }

  // Get current user info
  async function getCurrentUser() {
    const token = getAuthToken();
    if (!token) return null;

    try {
      const res = await fetch(`${window.API_BASE_URL}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (res.ok) {
        const user = await res.json();
        currentUser = user;
        return user;
      } else {
        clearAuthToken();
        return null;
      }
    } catch (err) {
      console.error('Error fetching user:', err);
      clearAuthToken();
      return null;
    }
  }

  // Check authentication status on page load
  async function checkAuth() {
    const token = getAuthToken();
    if (token) {
      authToken = token;
      const user = await getCurrentUser();
      if (user) {
        window.Auth.showApp();
        window.Auth.updateUserInfo(user);
        return true;
      }
    }
    window.Auth.showLogin();
    return false;
  }

  // Show login form
  function showLogin() {
    // Hide all sections
    const sections = document.querySelectorAll('main[id$="-section"]');
    sections.forEach(section => {
      section.style.display = 'none';
    });
    
    // Show login section
    const loginSection = document.getElementById('login-section');
    if (loginSection) {
      loginSection.style.display = 'flex';
    }
    
    // Hide user info
    const userInfo = document.getElementById('user-info');
    if (userInfo) {
      userInfo.style.display = 'none';
    }
  }

  // Show main application (dashboard)
  function showApp() {
    // Hide login
    const loginSection = document.getElementById('login-section');
    if (loginSection) {
      loginSection.style.display = 'none';
    }
    
    // Show dashboard by default
    const dashboardSection = document.getElementById('dashboard-section');
    if (dashboardSection) {
      dashboardSection.style.display = 'block';
    }
    
    // Show user info
    const userInfo = document.getElementById('user-info');
    if (userInfo) {
      userInfo.style.display = 'flex';
    }
    
    // Set dashboard nav as active
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(nav => nav.classList.remove('active'));
    const dashboardNav = document.querySelector('[data-section="dashboard"]');
    if (dashboardNav) {
      dashboardNav.classList.add('active');
    }
  }

  // Update user info in header
  function updateUserInfo(user) {
    const userNameEl = document.getElementById('user-name');
    const userRoleEl = document.getElementById('user-role');
    const userInitialEl = document.getElementById('user-initial');
    
    if (userNameEl) {
      userNameEl.textContent = user.username;
    }
    
    if (userRoleEl) {
      userRoleEl.textContent = user.role.toUpperCase();
    }
    
    if (userInitialEl) {
      userInitialEl.textContent = user.username.charAt(0).toUpperCase();
    }
    
    currentUser = user;
  }

  // Check if user is authenticated
  function isAuthenticated() {
    return !!getAuthToken();
  }

  // Login handler
  async function handleLogin(username, password) {
    try {
      // OAuth2PasswordRequestForm expects form-urlencoded data
      const params = new URLSearchParams();
      params.append('username', username);
      params.append('password', password);

      const loginUrl = `${window.API_BASE_URL}/api/auth/login`;
      console.log('Login URL:', loginUrl);
      
      const res = await fetch(loginUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: params.toString(),
        credentials: 'include' // Include cookies for CORS
      }).catch(err => {
        // Handle network errors (CORS, connection refused, etc.)
        console.error('Fetch error:', err);
        if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
          throw new Error('Cannot connect to server. Please check:\n1. Backend is running\n2. CORS is configured correctly\n3. Network connection');
        }
        throw err;
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: `HTTP ${res.status}: ${res.statusText}` }));
        throw new Error(errorData.detail || `Login failed: ${res.status} ${res.statusText}`);
      }

      const data = await res.json();

      if (res.ok && data.access_token) {
        setAuthToken(data.access_token);
        updateUserInfo(data.user);
        showApp();
        return { success: true };
      } else {
        return { success: false, error: data.detail || 'Login failed. Please check your credentials.' };
      }
    } catch (err) {
      console.error('Login error:', err);
      return { success: false, error: err.message || 'Network error. Please try again.' };
    }
  }

  // Export public API
  window.Auth = {
    getAuthToken,
    setAuthToken,
    clearAuthToken,
    getCurrentUser,
    checkAuth,
    showLogin,
    showApp,
    updateUserInfo,
    handleLogin,
    isAuthenticated,
    getCurrentUserData: () => currentUser
  };

  // Initialize on load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      checkAuth();
    });
  } else {
    checkAuth();
  }
})();

