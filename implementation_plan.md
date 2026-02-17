# Implementation Plan - Smart Reconciliation & Reliability Upgrade

# Goal Description
Implement a "Smart Reconciliation" system to synchronize the Bot with the Broker (Source of Truth), alongside critical reliability fixes and "lean" codebase improvements.

## User Actions Required
> [!IMPORTANT]
> **Configuration Cleanup**: We will consolidate duplicate risk settings in `settings.json`. You may need to verify your risk parameters after this update.
> **Zerodha Removal**: The Zerodha option will be removed from the UI.

## 1. Smart Reconciliation System

I will implement a **Broker-First** Design Pattern where the bot constantly validates its state against the broker's reality.

### Logic (`kickstart.py`)

#### [NEW] `reconcile_with_broker()`
A new method in `kickstart.py` that compares `live_positions` (API) vs `bot_state` (DB).
- **Trigger Logic**:
    - **Reactive**: Called immediately upon any `SCRIP LIMIT INSUFFICIENT` or Order Failure error.
    - **Proactive**: Scheduled 3x daily (Market Open 09:15, Noon 12:00, Pre-Close 15:15).

#### State Management
We will introduce 3 clear states for handling mismatches:
1.  **CLOSED**: Position exists in DB but NOT in Broker.
    - *Action*: Mark as Closed in DB. Log "Manual Exit Detected".
2.  **RESTRICTED**: Position exists in Broker but is blocked (T1/Pledged).
    - *Action*: Flag as `RESTRICTED` in memory. Pause Selling.
3.  **ORPHANED**: Position exists in Broker but NOT in DB (Manual Buy).
    - *Action*: Show in Dashboard as "Manual/Orphaned". Do *not* auto-manage/sell.

#### Notification
- **No Silent Failures**: Any reconciliation action (closing a ghost position, finding an orphan) triggers a **Toast/Notification** to the user.

## 2. Reliability & Code Hygiene (High Impact)

### [MODIFY] `kickstart.py` & `settings_gui.py`
1.  **Remove Silent Failures**: Replace all `except: pass` with `except Exception as e: logging.warning(...)` to expose hidden bugs.
3.  **Consolidate Risk Config**: Merge `risk_controls` and `risk` sections in `settings.json` into a single canonical `risk` object.

## 3. Codebase Refactoring (Medium Impact)

### [NEW] `backend/broker_api.py`
To reduce `kickstart.py` code bloat and improve testability:
- Extract `perform_auto_login()`
- Extract `get_positions()` and `merge_positions_and_orders()`
- This reduces `kickstart.py` size by ~30% and isolates the complex API logic.

## 4. Deferred Items (Out of Scope for Now)
- **SQLite for Settings**: Current JSON implementation is stable enough.
- **Parallel Scanner**: Performance optimization deferred until after reliability is solidified.
- **Loading States**: Nice to have, but prioritizing functional reliability first.

## Verification Plan

### Automated Tests
- **Reconciliation Test**: Mock a "Ghost Position" in DB and run `reconcile_with_broker()`. Assert DB updates to CLOSED.
- **Reactive Test**: Simulate an Order Failure and assert `reconcile_with_broker()` is called.

### Manual Verification
- **Safety Test**: Manually sell a stock on mStock. Wait for the Next Schedule (or trigger an error). Verify Bot updates Dashboard to "Closed" and sends a notification.
