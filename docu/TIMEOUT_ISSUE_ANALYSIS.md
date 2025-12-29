# Timeout Issue Analysis & Solution

## 🔍 Problem Identified

**Issue**: Frontend receives `502 Bad Gateway` after 15 minutes, even though backend completes successfully.

**Root Cause**:
- Railway HTTP request timeout limit: **~15 minutes**
- Audit generation takes: **15-30 minutes**
- Frontend timeout set to: **1 hour** (but gateway closes connection first)
- Backend continues processing and completes, but frontend loses connection

**Evidence**:
- Network logs show: `POST /api/audit/generate 502 15m`
- Backend logs show: Report generated successfully after timeout
- Report file exists: `audit_Cherry_Collectables_20251229_190021.html`

## ✅ Solution: Async Job Pattern with Polling

### Architecture Change

**Current (Synchronous)**:
```
Frontend → POST /api/audit/generate → [Wait 15-30 min] → Response
                                    ↑
                              Railway timeout at 15min
```

**New (Asynchronous)**:
```
Frontend → POST /api/audit/generate → [Immediate response with job ID]
         → Poll GET /api/audit/status/{job_id} every 5s
         → Backend processes in background
         → Status updates: PROCESSING → COMPLETED
```

### Implementation Plan

1. **Backend Changes**:
   - Modify `/api/audit/generate` to:
     - Create Report record with `status=PROCESSING`
     - Return immediately with `report_id`
     - Process audit in background (BackgroundTasks)
   - Add `/api/audit/status/{report_id}` endpoint
   - Update report status when complete/failed

2. **Frontend Changes**:
   - Start job and get `report_id`
   - Poll status endpoint every 5 seconds
   - Show progress updates
   - Display result when `status=COMPLETED`

### Benefits

- ✅ No timeout issues (immediate response)
- ✅ Users see progress updates
- ✅ Can refresh page and check status later
- ✅ Works with Railway's 15-minute limit
- ✅ Better UX with real-time progress

## 📋 Implementation Steps

1. Refactor `generate_audit` to use BackgroundTasks
2. Add status polling endpoint
3. Update frontend to poll for status
4. Test with long-running audits

