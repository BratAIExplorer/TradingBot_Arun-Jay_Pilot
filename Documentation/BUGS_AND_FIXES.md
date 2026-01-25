# 🐛 Bugs & Defects Log
**Status**: Updated for V3.0.1 (Emergency Fixes)
**Date**: 2026-01-21

## ✅ Resolved Issues

| ID | Severity | Issue Description | Fix Implemented | Status |
|----|----------|-------------------|-----------------|--------|
| **BUG-002** | 🔴 Critical | **Thread Safety Concurrency**: UI and Engine were modifying global state (STOP/OFFLINE flags) simultaneously, causing "Race Conditions" and UI freezes. | Implemented `threading.Lock()` across all shared state accessors (`stop_lock`, `offline_lock`, `state_lock`). | **VERIFIED** |
| **BUG-005** | 🟠 High | **API Data Fragility**: Malformed or unexpected JSON from broker API caused bot crashes during order placement. | Implemented centralized `validate_api_response()` helper with schema-checking before processing trades. | **VERIFIED** |
| **BUG-004** | 🟠 High | **Silent Failures**: critical errors (e.g. stop-signal failure) were hidden by `except: pass` blocks, making debugging impossible. | Replaced silent suppressions with proper `log_ok()` reporting. All background failures now appear in the Dashboard. | **VERIFIED** |
| **GUI-101** | 🔴 Critical | **Settings GUI Crash**: Settings tab crashed with `AttributeError` when clicking Save. | Fixed missing `broker_var` attribute in `SettingsGUI` class used by the V2 dashboard. | **VERIFIED** |
| **POS-102** | 🟠 High | **P&L Sync Failure**: `TypeError` when fetching positions if the user's portfolio was empty. | Added type-guards to `get_daywise_positions` to handle string responses from the broker API. | **VERIFIED** |
| **RISK-103** | 🟡 Medium | **Outdated Risk Limits**: Risk Manager ignored GUI setting changes until manual restart. | Refactored RiskManager to fetch thresholds dynamically in every cycle. Bot now respects user sliders in real-time. | **VERIFIED** |

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
