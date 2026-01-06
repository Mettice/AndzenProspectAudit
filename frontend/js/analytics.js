/**
 * Analytics Dashboard - Charts and metrics visualization.
 */

class AnalyticsDashboard {
  constructor() {
    this.revenueChart = null;
    this.industryChart = null;
    this.currentPeriod = 'month';
    this.init();
  }

  async init() {
    this.setupPeriodSelector();
    await this.loadRevenueTrends();
    await this.loadClientPerformance();
    await this.loadIndustryStats();
  }

  setupPeriodSelector() {
    const periodBtns = document.querySelectorAll('.period-btn');
    periodBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        periodBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentPeriod = btn.dataset.period;
        this.loadRevenueTrends();
      });
    });
  }

  async loadRevenueTrends() {
    try {
      const response = await fetch(`/api/analytics/revenue-trends?period=${this.currentPeriod}&days=90`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      this.renderRevenueChart(data.trends);
    } catch (error) {
      console.error('Error loading revenue trends:', error);
      this.showError('Failed to load revenue trends.');
    }
  }

  renderRevenueChart(trends) {
    const ctx = document.getElementById('revenue-trends-chart');
    if (!ctx) return;

    // Destroy existing chart if it exists
    if (this.revenueChart) {
      this.revenueChart.destroy();
    }

    const labels = trends.map(t => {
      const date = new Date(t.date);
      if (this.currentPeriod === 'day') {
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      } else if (this.currentPeriod === 'week') {
        return `Week of ${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
      } else {
        return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
      }
    });

    this.revenueChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Total Revenue',
            data: trends.map(t => t.total_revenue),
            borderColor: '#6ED855',
            backgroundColor: 'rgba(110, 216, 85, 0.1)',
            tension: 0.4,
            fill: true
          },
          {
            label: 'Attributed Revenue',
            data: trends.map(t => t.attributed_revenue),
            borderColor: '#3B82F6',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            tension: 0.4,
            fill: true
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
          },
          title: {
            display: false
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: function(value) {
                return '$' + (value / 1000).toFixed(0) + 'K';
              }
            }
          }
        }
      }
    });
  }

  async loadClientPerformance() {
    try {
      const response = await fetch('/api/analytics/client-performance?limit=10');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const clients = await response.json();
      this.renderClientTable(clients);
    } catch (error) {
      console.error('Error loading client performance:', error);
      this.showError('Failed to load client performance.');
    }
  }

  renderClientTable(clients) {
    const tbody = document.getElementById('client-performance-table');
    if (!tbody) return;

    if (clients.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="empty">No client data available</td></tr>';
      return;
    }

    tbody.innerHTML = clients.map(client => {
      const lastAudit = client.last_audit_date ? new Date(client.last_audit_date).toLocaleDateString() : 'N/A';
      return `
        <tr>
          <td><strong>${this.escapeHtml(client.client_name)}</strong></td>
          <td>${client.audit_count}</td>
          <td>${this.formatCurrency(client.total_revenue)}</td>
          <td>${this.formatCurrency(client.attributed_revenue)}</td>
          <td>${this.formatCurrency(client.avg_revenue_per_audit)}</td>
          <td>${lastAudit}</td>
        </tr>
      `;
    }).join('');
  }

  async loadIndustryStats() {
    try {
      const response = await fetch('/api/analytics/industry-stats');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const industries = await response.json();
      this.renderIndustryChart(industries);
    } catch (error) {
      console.error('Error loading industry stats:', error);
      this.showError('Failed to load industry statistics.');
    }
  }

  renderIndustryChart(industries) {
    const ctx = document.getElementById('industry-chart');
    if (!ctx) return;

    // Destroy existing chart if it exists
    if (this.industryChart) {
      this.industryChart.destroy();
    }

    const labels = industries.map(i => i.industry.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()));
    const revenueData = industries.map(i => i.total_revenue);
    const auditData = industries.map(i => i.audit_count);

    this.industryChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Total Revenue',
            data: revenueData,
            backgroundColor: '#6ED855',
            yAxisID: 'y'
          },
          {
            label: 'Audit Count',
            data: auditData,
            type: 'line',
            borderColor: '#3B82F6',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            yAxisID: 'y1'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
          }
        },
        scales: {
          y: {
            type: 'linear',
            display: true,
            position: 'left',
            ticks: {
              callback: function(value) {
                return '$' + (value / 1000).toFixed(0) + 'K';
              }
            }
          },
          y1: {
            type: 'linear',
            display: true,
            position: 'right',
            grid: {
              drawOnChartArea: false
            }
          }
        }
      }
    });
  }

  formatCurrency(amount) {
    if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(1)}M`;
    } else if (amount >= 1000) {
      return `$${(amount / 1000).toFixed(0)}K`;
    }
    return `$${amount.toFixed(0)}`;
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  showError(message) {
    console.error(message);
    // Could use toast notification
    alert(message);
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.analytics = new AnalyticsDashboard();
  });
} else {
  window.analytics = new AnalyticsDashboard();
}

window.AnalyticsDashboard = AnalyticsDashboard;

