# Time Countdown Investigation Report

## Overview
Previously, there was a smooth countdown from 30 minutes down to completion. Now it's misbehaving. This report investigates all time-related code.

## Files Involved

### 1. Backend: `api/routes/audit.py`
- **Line 518-581**: Calculates `estimated_remaining_minutes` using stage-based estimates
- **Line 578**: Returns `estimated_remaining_minutes` in `report_data`

### 2. Frontend: `frontend/index.html`
Multiple places calculate/update time:

#### A. `showProgress()` function (Line 687-750)
- **Line 707-749**: Animation interval (runs every 100ms)
- **Line 739-747**: Updates time ONLY if `progress < 5%`
- **Logic**: `remaining = ESTIMATED_TIME_MS - elapsed` (counts down from 27.5 minutes)
- **Problem**: This only works when progress < 5%, but gets overridden by other code

#### B. `updateProgress()` function (Line 752-806)
- **Line 764-805**: Updates time based on progress percentage
- **Line 773**: Only calculates if `clampedPercentage >= 20 && elapsed > 10000`
- **Logic**: Linear calculation `remaining = (100 - progress) / rate`
- **Problem**: Uses linear assumption, doesn't account for non-linear progress stages

#### C. Polling Status Update (Line 1008-1077)
- **Line 1030-1077**: Updates time when polling receives status
- **Line 1039**: Only calculates if `currentProgress >= 20`
- **Line 1046-1066**: Linear calculation based on progress rate
- **Problem**: Ignores server's `estimated_remaining_minutes` and recalculates

#### D. Real-time Countdown Timer (Line 1079-1188)
- **Line 1086**: `setInterval` runs every second (1000ms)
- **Line 1091-1137**: First tries to use server estimate, but recalculates
- **Line 1139-1188**: Fallback calculation using client time
- **Problem**: Multiple competing calculations, no single source of truth

## Problems Identified

### 1. **Multiple Competing Time Updates**
- `showProgress()` animation (100ms interval) - only for < 5% progress
- `updateProgress()` - called on each poll response
- Polling status update - recalculates time
- Real-time countdown timer (1s interval) - recalculates time
- **Result**: Time jumps around as different calculations override each other

### 2. **Server Estimate Ignored**
- Backend calculates `estimated_remaining_minutes` using stage-based logic (more accurate)
- Frontend receives it in `reportData.estimated_remaining_minutes`
- **BUT**: Frontend ignores it and recalculates using linear formula
- **Result**: Server's better estimate is thrown away

### 3. **No Smooth Countdown**
- Previous system: Started at 30 minutes, counted down smoothly
- Current system: 
  - Shows "25-30 minutes" until 20% progress
  - Then jumps to calculated value (could be 2 min, 15 min, etc.)
  - No smooth transition
- **Result**: Jarring user experience

### 4. **20% Threshold Too High**
- Before 20%: Shows static "25-30 minutes"
- After 20%: Jumps to calculated value
- **Problem**: User sees no countdown for first 20% of progress (could be 5+ minutes)

### 5. **Linear Calculation Assumption**
- Formula: `remaining = (100 - progress) / (progress / elapsed)`
- Assumes progress is linear
- **Reality**: Progress is NOT linear:
  - 0-20% (Extraction): Fast (2-5 min)
  - 25-60% (AI Analysis): Slow (10-20 min)
  - 60-80% (Formatting): Fast (1-2 min)
  - 80-100% (Report Gen): Fast (2-5 min)
- **Result**: Estimates are inaccurate, especially early on

### 6. **Variable Name Conflicts**
- `window.lastEstimatedMinutes` - used in multiple places
- `window.lastEstimatedMinutesFromPoll` - separate variable
- `window.lastEstimatedMinutesFromUpdate` - separate variable
- **Result**: Different calculations don't share state, causing jumps

### 7. **No Countdown Mechanism**
- Previous: Counted down from 30 minutes smoothly
- Current: Recalculates each time, doesn't count down
- **Missing**: A timer that decrements the estimate every minute/second

## What Should Happen (Based on Previous Behavior)

1. **Start**: Show "30 minutes remaining" (or use server estimate)
2. **Countdown**: Decrement by 1 minute every minute (or adjust based on actual progress)
3. **Update**: When new estimate comes from server, smoothly transition
4. **Smooth**: No jumps, just smooth countdown

## Current Flow Issues

```
1. showProgress() starts → Sets time to "25-30 minutes"
2. Polling starts → Receives progress, calls updateProgress()
3. updateProgress() → Recalculates (if > 20%), overwrites time
4. Polling response → Recalculates again, overwrites time
5. setInterval timer → Recalculates every second, overwrites time
6. Next poll → Recalculates again, overwrites time
```

**Result**: Time jumps around, no smooth countdown

## Recommended Fix Strategy

1. **Use Server Estimate as Primary Source**
   - Trust the backend's stage-based calculation
   - Only recalculate if server estimate is missing

2. **Implement Smooth Countdown**
   - Start with server estimate (or 30 min default)
   - Decrement by 1 minute every minute
   - Update estimate when new server data arrives

3. **Single Source of Truth**
   - One variable to track current estimate
   - One function to update the display
   - One timer to count down

4. **Remove Competing Calculations**
   - Remove linear calculations from frontend
   - Use server's stage-based estimates
   - Only do client-side countdown, not recalculation

5. **Show Countdown from Start**
   - Don't wait for 20% progress
   - Use server estimate or default 30 minutes
   - Count down smoothly from the start

## Key Code Locations to Fix

1. **Line 1030-1077**: Polling status update - Should use server estimate
2. **Line 1079-1188**: Countdown timer - Should count down, not recalculate
3. **Line 752-806**: updateProgress() - Should not calculate time, just update display
4. **Line 687-750**: showProgress() - Should start countdown from server estimate

## Next Steps

1. Restructure to have ONE time calculation (backend)
2. ONE time display update function (frontend)
3. ONE countdown timer that decrements smoothly
4. Remove all competing calculations

