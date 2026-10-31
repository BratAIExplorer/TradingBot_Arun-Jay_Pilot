# Changelog

All notable changes to ARUN Trading Bot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.5.4] - 2026-02-19 - Managed Holdings Fix

### Fixed
- **Managed Holdings Fallback** (`kickstart.py`)
  - Fixed logic to apply global default settings (RSI 30/70, 15m) for "Hybrid/Butler" positions that are tracked in state but missing from `settings.json`.
  - Prevents valid held positions from being skipped with "Not in config" errors.

## [2.5.3] - 2026-02-17 - Reliability & Analytics Overhaul

### Fixed
- **Offline Mode Bug** (`kickstart.py`, `sensei_v1_dashboard.py`)
  - Fixed issue where bot would get stuck in "Offline" state after transient network failures.
  - Implemented robust background connectivity monitor.
  - Dashboard now correctly launches monitor on startup.

### Added
- **Enhanced Trade Analytics** (`trades_db.py`, `kickstart.py`)
  - Added Market Context: Nifty 50 % Change captured at moment of trade.
  - Added Technical Indicators: MACD (Value, Signal, Histogram), ATR (Volatility), ADX (Trend Strength).
  - Updated CSV Export to include all new analytics columns automatically.

## [2.5.2] - 2026-02-16 - Never Sell at Loss Hardening

### Fixed
- **Never Sell at Loss Hardening** (`kickstart.py`, `risk_manager.py`)
  - **3-Layer Defense-in-Depth**: Added multiple safety gates to prevent selling at a loss when `never_sell_at_loss` is enabled.
  - **Layer 1 (Hardcoded Gate)**: `kickstart.py` blocks ALL sell orders if LTP < Entry Price.
  - **Layer 2 (Catastrophic Stop)**: `risk_manager.py` now respects `never_sell_at_loss`.
  - **Layer 3 (Risk Execution)**: `kickstart.py` risk loop rejects negative P&L actions early.

### Changed
- **Documentation**: Updated `ERROR_LOG_AND_FIXES.md` and `AI_HANDOVER.md` with full details.

---

## [2.5.1] - 2026-02-16 - Security & Architecture Audit Fixes

### Security
- **Credential Removal**: Removed `settings.json` from git tracking and rotated credentials.
- **Encryption Fix**: Fixed `save_settings()` in `settings_gui.py` to properly encrypt sensitive fields.
- **Secret Logging**: Stopped logging TOTP codes and API tokens in `kickstart.py`.

### Fixed
- **Operator Precedence Bug** (`kickstart.py`): Fixed logic error in exception handling (`if "TokenException" or ...`).
- **Singleton Settings**: Enforced singleton pattern for `SettingsManager` to prevent state desync.
- **Thread Safety**: Added locks for shared global variables in `kickstart.py`.
- **Scanner Stop**: Fixed scanner stop propagation in `sensei_v1_dashboard.py`.

---

## [2.5.0] - 2026-02-16 - Stability & UI Accuracy Update

### Added
- **RMS Cooldown System** (`kickstart.py`)
  - Automatic 1-hour cooldown for symbols with "Insufficient Quantity" rejections.
  - Prevents infinite failure loops when broker data isn't synchronized.
  
- **P&L Fallback Calculation** (`trades_db.py`)
  - Added support for calculating P&L using the last known entry price if the original BUY record is missing in the database.
  - Improves accuracy for positions held across bot restarts.

### Changed
- **Immediate Panic Stop** (`kickstart.py`)
  - Refactored `run_cycle` to check `STOP_REQUESTED` mid-cycle.
  - Bot now halts immediately between symbol processing instead of waiting for full cycle completion.
  
- **Real-time Failure Counter** (`sensei_v1_dashboard.py`)
  - The "FAILED" counter on the dashboard now reflects actual order execution failures from the broker.
  - Disconnected from purely negative P&L trades to separate execution health from market performance.

### Fixed
- **Missing RSI/P&L in History**: Improved data pipeline to ensure RSI and P&L are consistently populated in the 'Trades' tab.
- **Duplicate Order Protection**: Added `ACCEPTED` and `SUBMITTED` statuses to order blocking logic.

---

## [2.4.0] - 2026-02-09 - Family-Ready UX Sprint

### Added
- **First-Run Wizard** (`first_run_wizard.py`)
  - 3-step guided setup for new users
  - Step 1: mStock API credential entry with connection test
  - Step 2: Risk level selection (Conservative/Moderate/Aggressive)
  - Step 3: Stock picker with suggested packs + risk disclaimers
  - Auto-launches on first run when stocks list is empty
  
- **Telegram Notifications** (`notifications.py`)
  - `send_engine_started()` - Alerts when bot starts with capital and stock count
  - `send_engine_stopped()` - Alerts when bot stops with P&L summary
  - `send_daily_summary()` - Daily P&L report at market close (3:35 PM IST)
  - Includes win rate, trade count, and portfolio value
  
- **Panic Button** (`sensei_v1_dashboard.py`)
  - "🛑 STOP EVERYTHING" button in ENGINE card
  - User-friendly confirmation dialog explaining what happens
  - Clear messaging: "Your money is safe, positions remain open"
  - Wired to `kickstart.request_stop()`

- **Friendly Error Messages** (`kickstart.py`)
  - Replaced technical errors with reassuring user-friendly messages
  - Example: "⏳ Connection paused - server took too long. Your money is safe."
  - Removed scary technical jargon (403, timeout, etc.)

### Changed
- **Default Stock List** (`settings_default.json`)
  - `stocks` array now empty by default
  - Users must explicitly add stocks via wizard or settings
  - Promotes user ownership and understanding
  
- **Settings Structure** (`settings_default.json`)
  - Added `first_run_completed: false` flag for wizard detection

### Fixed
- Improved error handling for network timeouts with reassuring messages
- Better balance fetch error messaging

---

## [2.0.3] - 2026-02-03 - REIT Symbol Support

### Added
- Support for REIT symbols (EMBASSY, BIRET) with correct token mapping
- Enhanced symbol validation for special asset types

### Fixed
- Invalid REIT symbol handling in mStock API
- Balance calculation for bot vs manually managed capital

---

## [2.0.2] - 2026-02-01 - Titan V2 UI Launch

### Added
- Complete UI overhaul with "Titan" theme
- Light mode with soft cream background
- Top navigation bar with segmented buttons
- Enhanced Quick Monitor card
- Live execution stream

### Changed
- Increased font sizes for better readability
- Improved card layouts and spacing

---

## Previous Versions

See git history for earlier versions (v1.x, v0.x development)
