# Next Steps - Implementation Roadmap

## ✅ Completed
- Dashboard API endpoints
- Dashboard JavaScript with real data fetching
- Audit Launcher JavaScript with multi-step form
- Report Viewer API integration (chat & quotes)
- Security module integration
- Navigation between pages

## 🔧 Critical Next Steps (Priority 1)

### 1. **Report Content Rendering** ⚠️ HIGH PRIORITY
**Status:** Placeholder only - needs implementation
**Location:** `frontend/report-viewer.js` - `renderReportContent()` method

**What's needed:**
- Parse HTML report content into page-by-page structure
- Extract sections and create navigation
- Render content into the page container
- Handle images, charts, and embedded content

**Implementation:**
```javascript
renderReportContent(htmlContent) {
  // Parse HTML using DOMParser
  // Extract sections by data-section attributes
  // Create page elements for each section
  // Populate sidebar navigation
  // Render first page
}
```

### 2. **Fix Audit Launcher Script Path** ⚠️ HIGH PRIORITY
**Status:** Script path incorrect
**Location:** `frontend/audit-launcher.html` line 403

**Issue:** Script references `audit-launcher.js` but file is at `js/audit-launcher.js`

**Fix:** Update script tag to `js/audit-launcher.js`

### 3. **Dashboard Revenue Calculation** ⚠️ MEDIUM PRIORITY
**Status:** Using placeholder calculation
**Location:** `api/routes/dashboard.py` line 88

**Current:** `total_revenue_analyzed = audits_this_month * 50000.0`

**What's needed:**
- Extract revenue from report HTML content or metadata
- Store revenue in database when report is generated
- Query actual revenue from reports

**Options:**
1. Add `total_revenue` column to `reports` table
2. Extract revenue from HTML content on-the-fly
3. Store revenue in report metadata JSON field

### 4. **Report Viewer Page-by-Page Rendering** ⚠️ HIGH PRIORITY
**Status:** Static placeholder pages only
**Location:** `frontend/report-viewer.html` and `report-viewer.js`

**What's needed:**
- Dynamically generate pages from report HTML
- Extract sections and create page structure
- Implement smooth page transitions
- Handle page numbering and navigation

## 🎯 Enhancement Priorities (Priority 2)

### 5. **Export Functionality**
**Status:** Partially implemented
**Location:** `frontend/report-viewer.html` - Export buttons

**What's needed:**
- Connect PDF export button to `/api/audit/{id}/export?format=pdf`
- Connect Word export button to `/api/audit/{id}/export?format=word`
- Connect HTML export button to download current HTML

### 6. **Search Functionality**
**Status:** UI exists, needs backend
**Location:** `frontend/dashboard.html` - Search bar

**What's needed:**
- Create search API endpoint: `GET /api/dashboard/search?q=query`
- Implement full-text search on client names, industries
- Return filtered audit list

### 7. **Error Handling & Loading States**
**Status:** Basic implementation
**Location:** All JavaScript files

**What's needed:**
- Consistent error toast notifications
- Loading spinners for async operations
- Retry mechanisms for failed API calls
- Offline detection and messaging

### 8. **Quote Builder Enhancement**
**Status:** Basic implementation
**Location:** `frontend/report-viewer.js`

**What's needed:**
- Better quote item management (drag & drop)
- Quote templates
- Quote preview before generation
- Save draft quotes

## 🚀 Future Enhancements (Priority 3)

### 9. **Analytics Dashboard**
- Revenue trends over time
- Client performance metrics
- Flow performance comparisons
- Industry benchmarks visualization

### 10. **Client Management**
- Client database with history
- Re-audit functionality
- Client notes and tags
- Bulk operations

### 11. **Report Templates**
- Customizable report templates
- Brand-specific styling
- Section ordering preferences
- Custom sections

### 12. **Collaboration Features**
- Share reports with clients
- Comments and annotations
- Version history
- Approval workflows

## 📋 Immediate Action Items

1. **Fix script path** in `audit-launcher.html` (5 min)
2. **Implement `renderReportContent()`** in `report-viewer.js` (30 min)
3. **Add revenue extraction** to dashboard API (20 min)
4. **Test end-to-end flow** (15 min)

## 🔍 Testing Checklist

- [ ] Dashboard loads and displays real stats
- [ ] New Audit form works end-to-end
- [ ] Report viewer displays report content
- [ ] Chat interface works with real API
- [ ] Quote generation works
- [ ] Navigation between pages works
- [ ] Export buttons work
- [ ] Error handling displays properly

## 📝 Notes

- The report viewer currently has placeholder pages - need to dynamically generate from HTML
- Revenue calculation is a placeholder - need to extract from actual reports
- Some script paths may need adjustment based on deployment structure
- Consider adding loading states for better UX


