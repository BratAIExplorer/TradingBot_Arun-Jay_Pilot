# 🐛 Bugs & Defects Log
**Status**: Updated for V3.0.1 (Emergency Fixes)
**Date**: 2026-01-21

## ✅ Resolved Issues

| ID | Severity | Issue Description | Fix Implemented | Status |
|----|----------|-------------------|-----------------|--------|
| **CRIT-001** | 🔴 Critical | **Unstoppable Bot**: "STOP" button did not kill the engine; bot continued placing orders. | Implemented Global Kill Switch (`STOP_REQUESTED` flag) checked in main loop. Button now forces this flag. | **VERIFIED** |
| **CRIT-002** | 🔴 Critical | **State Saving Crash**: `Error saving state: keys must be str` caused by tuple keys (e.g. `('STOCK','NSE')`) in JSON. | Added defensive "Nuclear" Sanitization in `state_manager.py` to recursively convert all keys to strings before saving. | **VERIFIED** |
| **HIGH-003** | 🟠 High | **Incorrect Allocation**: Dashboard showed ₹50,000 default instead of actual user setting (₹10,000). | Updated `dashboard_v2.py` to hot-reload `max_capital` from `settings.json` on refresh. | **VERIFIED** |
| **HIGH-004** | 🟠 High | **Balance Sync**: Balance was reading 0.00 due to API response format change (Count vs List). | Updated `kickstart.py` to correctly parse `fundsummary` as a list. | **VERIFIED** |
| **MED-005** | 🟡 Medium | **Monitor Logs**: User unsure if Monitor started/stopped. | Added explicit `--- Monitor Initialized ---` and `--- Stopped ---` logs on button clicks. | **VERIFIED** |
| **MED-006** | 🟡 Medium | **Ticker Errors**: `Failed to get ticker ^INDIAVIX`. | Filtered indices in `kickstart.py`. (Log may persist harmlessly, but crash is prevented). | **RESOLVED** |
| **UI-007** | 🔵 Low | **Refresh Indicator**: No visual cue that positions were updating. | Added `(Last Check: HH:MM:SS)` timestamp to Positions table header. | **VERIFIED** |

---

## 🧪 Testing & Verification Guide

### 1. Verify Stop Button (The "Kill Switch")
1.  **Start** the bot.
2.  Wait for "Monitor Initialized" log.
3.  Click **STOP**.
4.  **Verify**: Log shows `--- Trade Execution Monitor Stopped ---`. No further "Running Cycle" logs appear.

### 2. Verify Allocation Display
1.  Go to **Settings > Capital**. Ensure Limit is ₹10,000.
2.  Restart Dashboard.
3.  **Verify**: "BOT ALLOCATION" card on left shows **₹10,000** (not ₹50,000).

### 3. Verify Refresh Indicators
1.  Go to **Dashboard** tab.
2.  Look at the "Live Positions" table header.
3.  **Verify**: It says `(Last Check: HH:MM:SS)` and the time updates every second.

### 4. Verify State Saving
1.  Run the bot for 1 minute.
2.  Check `logs/bot.log`.
3.  **Verify**: No red errors saying `keys must be str`.
