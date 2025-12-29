# Modularization Plan

## Overview
This document outlines the plan to modularize large files in the codebase to improve maintainability, testability, and code organization.

## Files to Modularize

### 1. `api/services/klaviyo/orchestrator.py` (915 lines)

**Current Structure:**
- `DataExtractionOrchestrator` class with:
  - `__init__()` - Initialization
  - `extract_all_data()` - Main extraction method (~300 lines)
  - `format_audit_data()` - Data formatting method (~300 lines)
  - `_calculate_campaign_performance_summary()` - Helper method
  - `_prepare_browse_abandonment_data()` - Helper method
  - `_prepare_abandoned_cart_data()` - Helper method

**Proposed Structure:**

```
api/services/klaviyo/
├── orchestrator.py (main class, ~200 lines)
├── extraction/
│   ├── __init__.py
│   ├── revenue_extractor.py (extract revenue data)
│   ├── campaign_extractor.py (extract campaign data)
│   ├── flow_extractor.py (extract flow data)
│   ├── list_extractor.py (extract list growth data)
│   ├── form_extractor.py (extract form performance data)
│   └── kav_extractor.py (extract KAV time series data)
└── formatters/
    ├── __init__.py
    ├── audit_formatter.py (format_audit_data logic)
    ├── campaign_formatter.py (_calculate_campaign_performance_summary)
    ├── flow_formatter.py (_prepare_browse_abandonment_data, _prepare_abandoned_cart_data)
    └── period_comparison.py (previous period comparison logic)
```

**Benefits:**
- Each extractor handles one data type
- Formatters are separated from extraction logic
- Easier to test individual components
- Clearer separation of concerns

---

### 2. `api/services/report/data_preparers.py` (1224 lines)

**Current Structure:**
- 12 `prepare_*` async functions:
  - `prepare_kav_data()`
  - `prepare_list_growth_data()`
  - `prepare_data_capture_data()`
  - `prepare_automation_data()`
  - `prepare_flow_data()`
  - `prepare_browse_abandonment_data()`
  - `prepare_post_purchase_data()`
  - `prepare_abandoned_cart_data()`
  - `prepare_campaign_performance_data()`
  - `prepare_strategic_recommendations()`
- 2 helper functions:
  - `generate_flow_strategic_summary()`
  - `create_flow_implementation_roadmap()`

**Proposed Structure:**

```
api/services/report/
├── data_preparers.py (main facade, ~100 lines)
└── preparers/
    ├── __init__.py
    ├── kav_preparer.py (prepare_kav_data)
    ├── list_growth_preparer.py (prepare_list_growth_data)
    ├── data_capture_preparer.py (prepare_data_capture_data)
    ├── automation_preparer.py (prepare_automation_data)
    ├── flow_preparer.py (prepare_flow_data, generate_flow_strategic_summary)
    ├── browse_abandonment_preparer.py (prepare_browse_abandonment_data)
    ├── post_purchase_preparer.py (prepare_post_purchase_data)
    ├── abandoned_cart_preparer.py (prepare_abandoned_cart_data)
    ├── campaign_preparer.py (prepare_campaign_performance_data)
    ├── strategic_preparer.py (prepare_strategic_recommendations)
    └── helpers.py (create_flow_implementation_roadmap, other shared helpers)
```

**Benefits:**
- Each preparer handles one report section
- Easier to locate and modify section-specific logic
- Better organization for LLM integration per section
- Clearer dependencies

---

### 3. Other Large Files to Consider

**`api/services/multi_agent_framework.py` (506 lines)**
- May need modularization if it grows
- Currently manageable but monitor

**`api/services/strategic_decision_engine.py` (625 lines)**
- May need modularization if it grows
- Currently manageable but monitor

**`api/services/narrative.py` (421 lines)**
- Currently manageable
- Monitor for growth

---

## Implementation Steps

### Phase 1: Orchestrator Modularization

1. **Create extraction modules:**
   - Create `api/services/klaviyo/extraction/` directory
   - Extract revenue extraction logic → `revenue_extractor.py`
   - Extract campaign extraction logic → `campaign_extractor.py`
   - Extract flow extraction logic → `flow_extractor.py`
   - Extract list extraction logic → `list_extractor.py`
   - Extract form extraction logic → `form_extractor.py`
   - Extract KAV extraction logic → `kav_extractor.py`

2. **Create formatter modules:**
   - Create `api/services/klaviyo/formatters/` directory
   - Extract `format_audit_data` logic → `audit_formatter.py`
   - Extract campaign formatting → `campaign_formatter.py`
   - Extract flow formatting → `flow_formatter.py`
   - Extract period comparison → `period_comparison.py`

3. **Refactor orchestrator:**
   - Keep `DataExtractionOrchestrator` as facade
   - Delegate to extractors and formatters
   - Maintain backward compatibility

### Phase 2: Data Preparers Modularization

1. **Create preparer modules:**
   - Create `api/services/report/preparers/` directory
   - Extract each `prepare_*` function to its own module
   - Extract helper functions to `helpers.py`

2. **Refactor data_preparers.py:**
   - Keep as facade that imports from preparers
   - Maintain backward compatibility
   - Export all functions for existing imports

### Phase 3: Testing & Validation

1. **Run existing tests:**
   - Ensure all tests pass
   - Fix any import issues

2. **Generate test report:**
   - Run full audit generation
   - Verify all sections work correctly
   - Check for any regressions

---

## Backward Compatibility

**Critical:** All changes must maintain backward compatibility:

1. **Import paths:**
   - Keep existing imports working
   - Use `__init__.py` to re-export functions/classes

2. **API contracts:**
   - Maintain same function signatures
   - Keep same return types
   - Preserve error handling behavior

3. **Gradual migration:**
   - New code can use new modules directly
   - Old code continues to work via facade

---

## File Size Targets

After modularization:
- **orchestrator.py**: ~200 lines (facade only)
- **data_preparers.py**: ~100 lines (facade only)
- **Individual modules**: 100-300 lines each
- **Helper modules**: 50-150 lines each

---

## Next Steps

1. ✅ Create modularization plan (this document)
2. ⏳ Review plan with team/user
3. ⏳ Implement Phase 1 (Orchestrator)
4. ⏳ Implement Phase 2 (Data Preparers)
5. ⏳ Testing & validation
6. ⏳ Update documentation

