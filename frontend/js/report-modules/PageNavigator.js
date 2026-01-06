/**
 * PageNavigator - Handles page navigation, controls, and sidebar navigation
 */
class PageNavigator {
  constructor() {
    this.currentPage = 1;
    this.totalPages = 1;
    this.sections = [];
    this.touchStartX = null;
    this.touchStartY = null;
  }

  /**
   * Initialize navigation system
   */
  init(totalPages, sections) {
    this.totalPages = totalPages;
    this.sections = sections || [];
    this.currentPage = 1;
    
    this.setupPageControls();
    this.setupSidebarNavigation();
    this.setupSwipeNavigation();
    this.setupKeyboardNavigation();
    this.updateSidebarNavigation();
    
    // Ensure we start on page 1 and scroll to top
    setTimeout(() => {
      this.goToPage(1);
      // Force visibility of navigation controls
      this.ensureNavigationVisible();
    }, 100);
  }

  /**
   * Setup page navigation controls
   */
  setupPageControls() {
    const prevBtn = document.querySelector('.btn-nav.prev');
    const nextBtn = document.querySelector('.btn-nav.next');

    if (prevBtn) {
      prevBtn.addEventListener('click', () => this.previousPage());
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', () => this.nextPage());
    }
  }

  /**
   * Setup sidebar navigation with event delegation
   */
  setupSidebarNavigation() {
    const navContainer = document.querySelector('.section-nav');
    if (!navContainer) return;
    
    navContainer.addEventListener('click', (e) => {
      const link = e.target.closest('.nav-link');
      if (!link) return;
      
      e.preventDefault();
      
      // Get page number from data attribute or href
      let pageNumber = parseInt(link.dataset.page);
      if (!pageNumber) {
        const href = link.getAttribute('href');
        const match = href?.match(/page-(\d+)/);
        if (match) {
          pageNumber = parseInt(match[1]);
        }
      }
      
      if (pageNumber && pageNumber >= 1 && pageNumber <= this.totalPages) {
        this.goToPage(pageNumber);
        
        // Update active state
        navContainer.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        link.classList.add('active');
      }
    });
  }

  /**
   * Setup swipe navigation for mobile
   */
  setupSwipeNavigation() {
    const pageContainer = document.getElementById('page-container');
    
    pageContainer.addEventListener('touchstart', (e) => {
      this.touchStartX = e.touches[0].clientX;
      this.touchStartY = e.touches[0].clientY;
    }, { passive: true });

    pageContainer.addEventListener('touchend', (e) => {
      if (!this.touchStartX || !this.touchStartY) return;

      const touchEndX = e.changedTouches[0].clientX;
      const touchEndY = e.changedTouches[0].clientY;

      const diffX = this.touchStartX - touchEndX;
      const diffY = this.touchStartY - touchEndY;

      // Only trigger if horizontal swipe is more significant than vertical
      if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
        if (diffX > 0) {
          this.nextPage(); // Swipe left - next page
        } else {
          this.previousPage(); // Swipe right - previous page
        }
      }

      this.touchStartX = null;
      this.touchStartY = null;
    }, { passive: true });
  }

  /**
   * Setup keyboard navigation
   */
  setupKeyboardNavigation() {
    document.addEventListener('keydown', (e) => this.handleKeyboardNavigation(e));
  }

  /**
   * Handle keyboard navigation
   */
  handleKeyboardNavigation(e) {
    // Arrow key navigation
    if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      e.preventDefault();
      this.previousPage();
    } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      e.preventDefault();
      this.nextPage();
    }
    
    // Number key navigation (1-9)
    const pageNumber = parseInt(e.key);
    if (pageNumber >= 1 && pageNumber <= 9 && pageNumber <= this.totalPages) {
      this.goToPage(pageNumber);
    }
  }

  /**
   * Navigate to specific page
   */
  goToPage(pageNumber) {
    console.log(`Navigating to page ${pageNumber}/${this.totalPages}`);
    
    if (pageNumber < 1 || pageNumber > this.totalPages) {
      console.warn(`Invalid page number: ${pageNumber}. Valid range: 1-${this.totalPages}`);
      return;
    }

    // Hide current page
    const currentPageEl = document.querySelector('.report-page.active');
    if (currentPageEl) {
      console.log(`Hiding current page: ${currentPageEl.id}`);
      currentPageEl.classList.remove('active');
    }

    // Show new page
    const newPageEl = document.getElementById(`page-${pageNumber}`);
    if (newPageEl) {
      console.log(`Showing page: ${newPageEl.id}`);
      newPageEl.classList.add('active');
      this.currentPage = pageNumber;
    } else {
      console.warn(`Page element not found: page-${pageNumber}. Available pages:`, 
        Array.from(document.querySelectorAll('.report-page')).map(p => p.id));
      return;
    }

    this.updatePageIndicators();
    this.updateNavigationButtons();
    
    // Scroll to top after a brief delay to ensure DOM has updated
    setTimeout(() => {
      this.scrollPageToTop();
    }, 50);
  }

  /**
   * Navigate to next page
   */
  nextPage() {
    console.log(`Next page requested. Current: ${this.currentPage}, Total: ${this.totalPages}`);
    if (this.currentPage < this.totalPages) {
      this.goToPage(this.currentPage + 1);
    } else {
      console.log('Already on last page');
    }
  }

  /**
   * Navigate to previous page
   */
  previousPage() {
    console.log(`Previous page requested. Current: ${this.currentPage}, Total: ${this.totalPages}`);
    if (this.currentPage > 1) {
      this.goToPage(this.currentPage - 1);
    } else {
      console.log('Already on first page');
    }
  }

  /**
   * Update page indicators in UI
   */
  updatePageIndicators() {
    const currentPageEl = document.querySelector('.current-page');
    const totalPagesEl = document.querySelector('.total-pages');

    if (currentPageEl) currentPageEl.textContent = this.currentPage;
    if (totalPagesEl) totalPagesEl.textContent = this.totalPages;
  }

  /**
   * Update navigation button states
   */
  updateNavigationButtons() {
    const prevBtn = document.querySelector('.btn-nav.prev');
    const nextBtn = document.querySelector('.btn-nav.next');

    if (prevBtn) {
      prevBtn.disabled = this.currentPage === 1;
      // Always show buttons, just disable them
      prevBtn.style.visibility = 'visible';
      prevBtn.style.opacity = this.currentPage === 1 ? '0.4' : '1';
    }

    if (nextBtn) {
      nextBtn.disabled = this.currentPage === this.totalPages;
      // Always show buttons, just disable them
      nextBtn.style.visibility = 'visible';
      nextBtn.style.opacity = this.currentPage === this.totalPages ? '0.4' : '1';
    }
    
    console.log(`Navigation updated: Page ${this.currentPage}/${this.totalPages}, Prev: ${this.currentPage > 1}, Next: ${this.currentPage < this.totalPages}`);
  }

  /**
   * Update active navigation link
   */
  updateActiveNavLink(activeLink) {
    document.querySelectorAll('.nav-link').forEach(link => {
      link.classList.remove('active');
    });
    
    if (activeLink) {
      activeLink.classList.add('active');
    } else {
      // Auto-select based on current page
      const navLinks = document.querySelectorAll('.nav-link');
      if (navLinks[this.currentPage - 1]) {
        navLinks[this.currentPage - 1].classList.add('active');
      }
    }
  }

  /**
   * Scroll page to top
   */
  scrollPageToTop() {
    // Scroll the page container to top (smooth scroll)
    const pageContainer = document.getElementById('page-container');
    if (pageContainer) {
      pageContainer.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    // Also scroll the active page content to top
    const activePage = document.querySelector('.report-page.active');
    if (activePage) {
      activePage.scrollTo({ top: 0, behavior: 'smooth' });
      
      // Also scroll the page content within
      const pageContent = activePage.querySelector('.page-content');
      if (pageContent) {
        pageContent.scrollTo({ top: 0, behavior: 'smooth' });
      }
    }
    
    // Scroll the report content area to top
    const reportContent = document.querySelector('.report-content');
    if (reportContent) {
      reportContent.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  /**
   * Update sidebar navigation based on sections
   */
  updateSidebarNavigation() {
    const navContainer = document.querySelector('.section-nav');
    if (!navContainer) return;

    // Clear loading state
    navContainer.innerHTML = '';

    if (this.sections.length === 0) {
      navContainer.innerHTML = '<div class="nav-loading" style="padding: 20px; color: var(--text-muted); text-align: center;"><p>No sections available</p></div>';
      return;
    }

    // Group sections by their base section ID
    const sectionGroups = {};
    this.sections.forEach(section => {
      const baseId = section.sectionId;
      if (!sectionGroups[baseId]) {
        sectionGroups[baseId] = [];
      }
      sectionGroups[baseId].push(section);
    });

    // Create navigation structure
    let navHTML = '';
    
    // Main sections
    navHTML += '<div class="nav-section"><h3>Report Sections</h3><ul>';
    
    Object.entries(sectionGroups).forEach(([sectionId, sectionPages]) => {
      const firstPage = sectionPages[0];
      const baseTitle = firstPage.baseTitle || firstPage.title;
      
      if (sectionPages.length === 1) {
        // Single page section
        navHTML += `
          <li>
            <a href="#page-${firstPage.pageNumber}" class="nav-link" data-page="${firstPage.pageNumber}">
              ${baseTitle}
            </a>
          </li>
        `;
      } else {
        // Multi-page section with sub-pages
        navHTML += `
          <li>
            <a href="#page-${firstPage.pageNumber}" class="nav-link" data-page="${firstPage.pageNumber}">
              ${baseTitle}
            </a>
            <ul style="margin-left: 12px; margin-top: 4px;">
        `;
        
        sectionPages.forEach(subPage => {
          navHTML += `
            <li>
              <a href="#page-${subPage.pageNumber}" class="nav-link" data-page="${subPage.pageNumber}" style="font-size: 12px; color: var(--text-muted);">
                ${subPage.title}
              </a>
            </li>
          `;
        });
        
        navHTML += '</ul></li>';
      }
    });
    
    navHTML += '</ul></div>';
    
    navContainer.innerHTML = navHTML;
    
    // Set active link for current page
    this.updateActiveNavLink();
    
    console.log(`✓ Updated sidebar navigation with ${Object.keys(sectionGroups).length} sections`);
  }

  /**
   * Get current page number
   */
  getCurrentPage() {
    return this.currentPage;
  }

  /**
   * Get total pages
   */
  getTotalPages() {
    return this.totalPages;
  }

  /**
   * Set sections data
   */
  setSections(sections) {
    this.sections = sections;
    this.updateSidebarNavigation();
  }

  /**
   * Ensure navigation controls are visible
   */
  ensureNavigationVisible() {
    const pageControls = document.querySelector('.page-controls');
    const prevBtn = document.querySelector('.btn-nav.prev');
    const nextBtn = document.querySelector('.btn-nav.next');
    
    if (pageControls) {
      pageControls.style.display = 'flex';
      pageControls.style.visibility = 'visible';
    }
    
    if (prevBtn) {
      prevBtn.style.display = 'block';
    }
    
    if (nextBtn) {
      nextBtn.style.display = 'block';
    }
    
    console.log('✓ Navigation controls visibility enforced');
  }
}

// Export for use
window.PageNavigator = PageNavigator;