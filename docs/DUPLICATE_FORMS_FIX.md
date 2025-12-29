# Duplicate Forms and client_name Error Fix

## Issues Fixed

### 1. client_name Error ✅
- **Error**: `local variable 'client_name' referenced before assignment`
- **Location**: `api/services/report/preparers/strategic_preparer.py`
- **Problem**: Variables `client_name`, `account_context`, and `industry` were being used on lines 44-48 before they were extracted from `audit_data` on lines 53-55
- **Fix**: Moved variable extraction to lines 30-32 (before the LLM service call)
- **Result**: Variables are now defined before use

### 2. Duplicate Forms ✅
- **Issue**: Duplicate form names appearing in the report (e.g., "Email Popup", "Sell To Form", "afterpay day access aug 24")
- **Location**: `api/services/report/preparers/data_capture_preparer.py`
- **Problem**: Forms from Klaviyo API may have duplicate names or IDs, causing the same form to appear multiple times
- **Fix**: Added deduplication logic:
  - Track seen form IDs in `seen_form_ids` set
  - Track seen form names in `seen_form_names` set
  - Skip forms that have already been seen (by ID first, then by name)
  - Log skipped duplicates for debugging
- **Result**: Each form will only appear once in the report

## Code Changes

### strategic_preparer.py
```python
# BEFORE (lines 32-55):
try:
    from ...llm import LLMService
    from ...llm.formatter import LLMDataFormatter
    
    llm_service = LLMService()
    
    formatted_data = LLMDataFormatter.format_for_generic_analysis(
        ...
        client_context={
            "client_name": client_name,  # ❌ Used before definition
            ...
        }
    )
    
    account_context = audit_data.get("account_context", {})  # ❌ Defined too late
    client_name = audit_data.get("client_name", "the client")
    industry = audit_data.get("industry", "retail")

# AFTER:
# Get context FIRST before using it
account_context = audit_data.get("account_context", {})
client_name = audit_data.get("client_name", "the client")
industry = audit_data.get("industry", "retail")

try:
    from ...llm import LLMService
    from ...llm.formatter import LLMDataFormatter
    
    llm_service = LLMService()
    
    formatted_data = LLMDataFormatter.format_for_generic_analysis(
        ...
        client_context={
            "client_name": client_name,  # ✅ Now defined
            ...
        }
    )
```

### data_capture_preparer.py
```python
# BEFORE:
forms = []
for form in forms_raw.get("forms", []):
    if form.get("impressions", 0) > 0:
        forms.append({...})

# AFTER:
forms = []
seen_form_ids = set()
seen_form_names = set()

for form in forms_raw.get("forms", []):
    form_id = form.get("id")
    form_name = form.get("name", "Unknown")
    
    # Deduplicate by ID first (most reliable)
    if form_id and form_id in seen_form_ids:
        logger.debug(f"Skipping duplicate form by ID: {form_name} (ID: {form_id})")
        continue
    
    # Also check for duplicate names (in case ID is missing)
    if form_name in seen_form_names:
        logger.debug(f"Skipping duplicate form by name: {form_name}")
        continue
    
    if form.get("impressions", 0) > 0:
        forms.append({...})
        
        # Track seen forms
        if form_id:
            seen_form_ids.add(form_id)
        seen_form_names.add(form_name)
```

## Testing

After these fixes:
1. ✅ Strategic recommendations should generate without `client_name` error
2. ✅ Forms should appear only once in the data capture section
3. ✅ Duplicate forms (by ID or name) will be filtered out
4. ✅ Debug logs will show which duplicates were skipped

## Next Steps

1. Run the test script again to verify:
   - No `client_name` error in strategic recommendations
   - No duplicate forms in the report
   - All forms appear only once

2. Check logs for deduplication messages:
   - Look for "Skipping duplicate form by ID" or "Skipping duplicate form by name" messages
   - These indicate which forms were filtered out

