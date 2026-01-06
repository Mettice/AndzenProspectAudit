/**
 * Dashboard functionality for Andzen Audit Studio.
 * Handles data fetching, stats display, and navigation.
 */

class Dashboard {
  constructor() {
    this.stats = null;
    this.recentAudits = [];
    this.init();
  }

  async init() {
    this.setupEventListeners();
    await this.loadDashboardData();
    this.setupNavigation();
  }

  setupEventListeners() {
    // New Audit button
    const newAuditBtn = document.querySelector('.btn-new-audit');
    if (newAuditBtn) {
      newAuditBtn.addEventListener('click', () => {
        this.navigateToAuditLauncher();
      });
    }

    // Quick action buttons
    const quickActions = document.querySelectorAll('.action-card');
    quickActions.forEach(card => {
      card.addEventListener('click', (e) => {
        const action = e.currentTarget.querySelector('h3')?.textContent;
        this.handleQuickAction(action);
      });
    });

    // View All button
    const viewAllBtn = document.querySelector('.btn-view-all');
    if (viewAllBtn) {
      viewAllBtn.addEventListener('click', () => {
        this.showAllAudits();
      });
    }

    // Audit item actions
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('btn-view')) {
        const auditItem = e.target.closest('.audit-item');
        const auditId = auditItem?.dataset?.auditId;
        if (auditId) {
          this.viewAudit(parseInt(auditId));
        }
      }
      
      if (e.target.classList.contains('btn-quote')) {
        const auditItem = e.target.closest('.audit-item');
        const auditId = auditItem?.dataset?.auditId;
        if (auditId) {
          this.generateQuote(parseInt(auditId));
        }
      }
    });

    // Search functionality
    const searchInput = document.querySelector('.search-bar input');
    const searchBtn = document.querySelector('.search-btn');
    if (searchInput) {
      searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          this.handleSearch(searchInput.value);
        }
      });
    }
    if (searchBtn) {
      searchBtn.addEventListener('click', () => {
        const searchValue = searchInput?.value;
        if (searchValue) {
          this.handleSearch(searchValue);
        }
      });
    }
  }

  async loadDashboardData() {
    try {
      await Promise.all([
        this.loadStats(),
        this.loadRecentAudits()
      ]);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      this.showError('Failed to load dashboard data. Please refresh the page.');
    }
  }

  async loadStats() {
    try {
      const response = await fetch('/api/dashboard/stats');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const stats = await response.json();
      this.stats = stats;
      this.updateStatsDisplay(stats);
    } catch (error) {
      console.error('Error loading stats:', error);
      // Show placeholder stats on error
      this.updateStatsDisplay({
        audits_this_month: 0,
        audits_change_percent: 0,
        total_revenue_analyzed: 0,
        revenue_change_percent: 0,
        active_clients: 0,
        new_clients_this_week: 0,
        quotes_generated: 0,
        quotes_total_value: 0
      });
    }
  }

  updateStatsDisplay(stats) {
    // Update audits count
    const auditsNumber = document.querySelector('.stat-card .stat-number');
    if (auditsNumber && stats.audits_this_month !== undefined) {
      auditsNumber.textContent = stats.audits_this_month;
    }
    
    // Update audits change
    const auditsChange = document.querySelector('.stat-card .stat-change');
    if (auditsChange) {
      const isPositive = stats.audits_change_percent >= 0;
      auditsChange.textContent = `${isPositive ? '+' : ''}${stats.audits_change_percent.toFixed(1)}% from last month`;
      auditsChange.className = `stat-change ${isPositive ? 'positive' : 'negative'}`;
    }

    // Update revenue
    const revenueNumber = document.querySelectorAll('.stat-card .stat-number')[1];
    if (revenueNumber && stats.total_revenue_analyzed !== undefined) {
      revenueNumber.textContent = this.formatCurrency(stats.total_revenue_analyzed);
    }
    
    const revenueChange = document.querySelectorAll('.stat-card .stat-change')[1];
    if (revenueChange) {
      const isPositive = stats.revenue_change_percent >= 0;
      revenueChange.textContent = `${isPositive ? '+' : ''}${stats.revenue_change_percent.toFixed(1)}% avg growth`;
      revenueChange.className = `stat-change ${isPositive ? 'positive' : 'negative'}`;
    }

    // Update clients
    const clientsNumber = document.querySelectorAll('.stat-card .stat-number')[2];
    if (clientsNumber && stats.active_clients !== undefined) {
      clientsNumber.textContent = stats.active_clients;
    }
    
    const clientsChange = document.querySelectorAll('.stat-card .stat-change')[2];
    if (clientsChange) {
      clientsChange.textContent = `${stats.new_clients_this_week} new this week`;
      clientsChange.className = 'stat-change neutral';
    }

    // Update quotes
    const quotesNumber = document.querySelectorAll('.stat-card .stat-number')[3];
    if (quotesNumber && stats.quotes_generated !== undefined) {
      quotesNumber.textContent = stats.quotes_generated;
    }
    
    const quotesChange = document.querySelectorAll('.stat-card .stat-change')[3];
    if (quotesChange) {
      quotesChange.textContent = this.formatCurrency(stats.quotes_total_value) + ' total value';
      quotesChange.className = 'stat-change positive';
    }
  }

  async loadRecentAudits() {
    try {
      const response = await fetch('/api/dashboard/recent-audits?limit=5');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      this.recentAudits = data.audits;
      this.updateRecentAuditsDisplay(data.audits);
    } catch (error) {
      console.error('Error loading recent audits:', error);
      this.showError('Failed to load recent audits.');
    }
  }

  updateRecentAuditsDisplay(audits) {
    const auditList = document.querySelector('.audit-list');
    if (!auditList) return;

    // Clear existing items (except template if exists)
    auditList.innerHTML = '';

    if (audits.length === 0) {
      auditList.innerHTML = `
        <div class="empty-state">
          <p>No audits yet. Create your first audit to get started!</p>
          <button class="btn-new-audit">Create New Audit</button>
        </div>
      `;
      return;
    }

    audits.forEach(audit => {
      const auditItem = this.createAuditItem(audit);
      auditList.appendChild(auditItem);
    });
  }

  createAuditItem(audit) {
    const item = document.createElement('div');
    item.className = 'audit-item';
    item.dataset.auditId = audit.id;

    const statusClass = audit.status === 'completed' ? 'completed' : 
                       audit.status === 'processing' ? 'in-progress' : 'failed';
    
    const statusText = audit.status === 'completed' ? 'Completed' :
                      audit.status === 'processing' ? 'Processing...' : 'Failed';
    
    const timeAgo = this.formatTimeAgo(new Date(audit.created_at));
    const revenue = audit.revenue ? this.formatCurrency(audit.revenue) : '—';
    const flowCount = audit.flow_count || '—';

    item.innerHTML = `
      <div class="audit-status ${statusClass}"></div>
      <div class="audit-info">
        <h3>${this.escapeHtml(audit.client_name)}</h3>
        <p>${audit.industry || 'Unknown'} • ${statusText} ${timeAgo}</p>
      </div>
      <div class="audit-metrics">
        <span class="metric">${revenue} Revenue</span>
        <span class="metric">${flowCount} Flows</span>
      </div>
      <div class="audit-actions">
        ${audit.status === 'completed' ? `
          <button class="btn-view">View</button>
          <button class="btn-quote">Quote</button>
        ` : `
          <button class="btn-view" disabled>${statusText}</button>
        `}
      </div>
    `;

    return item;
  }

  formatCurrency(amount) {
    if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(1)}M`;
    } else if (amount >= 1000) {
      return `$${(amount / 1000).toFixed(0)}K`;
    }
    return `$${amount.toFixed(0)}`;
  }

  formatTimeAgo(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    return date.toLocaleDateString();
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  handleQuickAction(action) {
    switch (action) {
      case 'Start New Audit':
        this.navigateToAuditLauncher();
        break;
      case 'Generate Quote':
        // Show quote generation modal or navigate
        console.log('Generate Quote clicked');
        break;
      case 'View Analytics':
        // Show analytics page
        console.log('View Analytics clicked');
        break;
      case 'Manage Clients':
        // Show clients page
        console.log('Manage Clients clicked');
        break;
    }
  }

  navigateToAuditLauncher() {
    // Navigate to audit launcher page
    if (window.location.pathname.includes('dashboard.html')) {
      window.location.href = 'audit-launcher.html';
    } else {
      // If using single-page app, show audit launcher section
      const event = new CustomEvent('navigate', { detail: { page: 'audit-launcher' } });
      window.dispatchEvent(event);
    }
  }

  viewAudit(auditId) {
    // Navigate to report viewer
    if (window.location.pathname.includes('dashboard.html')) {
      window.location.href = `report-viewer.html?reportId=${auditId}`;
    } else {
      const event = new CustomEvent('navigate', { detail: { page: 'report-viewer', reportId } });
      window.dispatchEvent(event);
    }
  }

  async generateQuote(auditId) {
    try {
      // Navigate to report viewer with quote tab open
      if (window.location.pathname.includes('dashboard.html')) {
        window.location.href = `report-viewer.html?reportId=${auditId}&tab=quotes`;
      } else {
        const event = new CustomEvent('navigate', { 
          detail: { page: 'report-viewer', reportId, tab: 'quotes' } 
        });
        window.dispatchEvent(event);
      }
    } catch (error) {
      console.error('Error generating quote:', error);
      this.showError('Failed to generate quote.');
    }
  }

  async handleSearch(query) {
    if (!query || query.trim().length < 1) {
      return;
    }

    try {
      const response = await fetch(`/api/search/audits?q=${encodeURIComponent(query)}&limit=20`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Update recent audits display with search results
      if (data.results && data.results.length > 0) {
        this.updateRecentAuditsDisplay(data.results.map(r => ({
          id: r.id,
          client_name: r.client_name,
          industry: r.industry,
          status: r.status,
          created_at: r.created_at,
          revenue: r.revenue,
          flow_count: null,
          filename: r.filename
        })));
        
        // Show search results indicator
        const auditList = document.querySelector('.audit-list');
        if (auditList) {
          const header = document.querySelector('.recent-audits .section-header h2');
          if (header) {
            header.textContent = `Search Results (${data.total} found)`;
          }
        }
      } else {
        this.showError('No audits found matching your search.');
      }
    } catch (error) {
      console.error('Search error:', error);
      this.showError('Search failed. Please try again.');
    }
  }

  showAllAudits() {
    console.log('Show all audits');
    // Navigate to full audits list page
  }

  setupNavigation() {
    // Handle navigation events if using single-page app
    window.addEventListener('navigate', (e) => {
      const { page, reportId, tab } = e.detail;
      // Handle navigation logic
    });
  }

  showError(message) {
    // Show error notification
    console.error(message);
    // Could use a toast notification library or custom implementation
    alert(message); // Placeholder
  }
}

// Initialize dashboard when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
  });
} else {
  window.dashboard = new Dashboard();
}

// Export for use in other modules
window.Dashboard = Dashboard;

