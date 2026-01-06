/**
 * Client Management - List and manage clients.
 */

class ClientManager {
  constructor() {
    this.clients = [];
    this.currentPage = 1;
    this.pageSize = 20;
    this.currentIndustry = '';
    this.searchQuery = '';
    this.init();
  }

  async init() {
    await this.loadIndustries();
    this.setupEventListeners();
    await this.loadClients();
  }

  setupEventListeners() {
    // Search
    const searchInput = document.getElementById('client-search');
    const searchBtn = document.querySelector('.search-btn');
    
    if (searchInput) {
      searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          this.searchQuery = searchInput.value.trim();
          this.currentPage = 1;
          this.loadClients();
        }
      });
    }
    
    if (searchBtn) {
      searchBtn.addEventListener('click', () => {
        this.searchQuery = searchInput?.value.trim() || '';
        this.currentPage = 1;
        this.loadClients();
      });
    }

    // Industry filter
    const industryFilter = document.getElementById('industry-filter');
    if (industryFilter) {
      industryFilter.addEventListener('change', (e) => {
        this.currentIndustry = e.target.value;
        this.currentPage = 1;
        this.loadClients();
      });
    }
  }

  async loadIndustries() {
    try {
      const response = await fetch('/api/clients/industries/list');
      if (!response.ok) return;

      const industries = await response.json();
      const filter = document.getElementById('industry-filter');
      if (filter) {
        industries.forEach(industry => {
          const option = document.createElement('option');
          option.value = industry;
          option.textContent = industry.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
          filter.appendChild(option);
        });
      }
    } catch (error) {
      console.error('Error loading industries:', error);
    }
  }

  async loadClients() {
    try {
      let url = `/api/clients?limit=${this.pageSize}&offset=${(this.currentPage - 1) * this.pageSize}`;
      if (this.currentIndustry) {
        url += `&industry=${encodeURIComponent(this.currentIndustry)}`;
      }

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const clients = await response.json();
      
      // Filter by search query if provided
      if (this.searchQuery) {
        this.clients = clients.filter(c => 
          c.client_name.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
          (c.client_code && c.client_code.toLowerCase().includes(this.searchQuery.toLowerCase()))
        );
      } else {
        this.clients = clients;
      }

      this.renderClients();
      this.updateClientCount();
    } catch (error) {
      console.error('Error loading clients:', error);
      this.showError('Failed to load clients.');
    }
  }

  renderClients() {
    const tbody = document.getElementById('clients-table');
    if (!tbody) return;

    if (this.clients.length === 0) {
      tbody.innerHTML = '<tr><td colspan="9" class="empty">No clients found</td></tr>';
      return;
    }

    tbody.innerHTML = this.clients.map(client => {
      const lastAudit = client.last_audit_date ? new Date(client.last_audit_date).toLocaleDateString() : 'N/A';
      const statusBadge = client.status === 'active' ? 
        '<span class="status-badge active">Active</span>' : 
        '<span class="status-badge inactive">Inactive</span>';
      
      return `
        <tr>
          <td><strong>${this.escapeHtml(client.client_name)}</strong></td>
          <td>${client.client_code || '—'}</td>
          <td>${client.industry ? this.formatIndustry(client.industry) : '—'}</td>
          <td>${client.audit_count}</td>
          <td>${this.formatCurrency(client.total_revenue)}</td>
          <td>${this.formatCurrency(client.attributed_revenue)}</td>
          <td>${lastAudit}</td>
          <td>${statusBadge}</td>
          <td>
            <button class="btn-view-client" data-client="${this.escapeHtml(client.client_name)}">View</button>
          </td>
        </tr>
      `;
    }).join('');

    // Add click handlers for view buttons
    document.querySelectorAll('.btn-view-client').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const clientName = e.target.dataset.client;
        this.viewClientDetail(clientName);
      });
    });
  }

  async viewClientDetail(clientName) {
    try {
      const response = await fetch(`/api/clients/${encodeURIComponent(clientName)}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const client = await response.json();
      this.showClientModal(client);
    } catch (error) {
      console.error('Error loading client detail:', error);
      this.showError('Failed to load client details.');
    }
  }

  showClientModal(client) {
    // Create modal for client details
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
      <div class="modal-content">
        <div class="modal-header">
          <h2>${this.escapeHtml(client.client_name)}</h2>
          <button class="modal-close">×</button>
        </div>
        <div class="modal-body">
          <div class="client-info">
            <p><strong>Industry:</strong> ${client.industry ? this.formatIndustry(client.industry) : 'N/A'}</p>
            <p><strong>Client Code:</strong> ${client.client_code || 'N/A'}</p>
            <p><strong>Total Audits:</strong> ${client.audit_count}</p>
            <p><strong>Total Revenue:</strong> ${this.formatCurrency(client.total_revenue)}</p>
            <p><strong>Attributed Revenue:</strong> ${this.formatCurrency(client.attributed_revenue)}</p>
            <p><strong>First Audit:</strong> ${client.first_audit_date ? new Date(client.first_audit_date).toLocaleDateString() : 'N/A'}</p>
            <p><strong>Last Audit:</strong> ${client.last_audit_date ? new Date(client.last_audit_date).toLocaleDateString() : 'N/A'}</p>
          </div>
          <div class="client-audits">
            <h3>Audit History</h3>
            <ul>
              ${client.audits.map(audit => `
                <li>
                  <a href="report-viewer.html?reportId=${audit.id}">
                    ${audit.filename} - ${new Date(audit.created_at).toLocaleDateString()}
                  </a>
                </li>
              `).join('')}
            </ul>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    // Close modal handlers
    modal.querySelector('.modal-close').addEventListener('click', () => modal.remove());
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.remove();
      }
    });
  }

  updateClientCount() {
    const countEl = document.getElementById('client-count');
    if (countEl) {
      countEl.textContent = `${this.clients.length} client${this.clients.length !== 1 ? 's' : ''}`;
    }
  }

  formatCurrency(amount) {
    if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(1)}M`;
    } else if (amount >= 1000) {
      return `$${(amount / 1000).toFixed(0)}K`;
    }
    return `$${amount.toFixed(0)}`;
  }

  formatIndustry(industry) {
    return industry.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  showError(message) {
    console.error(message);
    alert(message);
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.clientManager = new ClientManager();
  });
} else {
  window.clientManager = new ClientManager();
}

window.ClientManager = ClientManager;

