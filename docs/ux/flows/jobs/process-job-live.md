# Process Job Live Flow

## Purpose

Describe the user experience while a job is processing.

---

## Flow

User clicks Process

↓

Job immediately becomes Queued

↓

Processing Queue drawer opens

↓

Frontend subscribes to SSE

↓

Status updates automatically

↓

Current workflow step changes

↓

Progress bar advances

↓

Execution completes

↓

Job card refreshes automatically

↓

Processing Queue removes completed execution

---

## User Experience

The page should never require manual refresh.

All updates arrive through SSE.
