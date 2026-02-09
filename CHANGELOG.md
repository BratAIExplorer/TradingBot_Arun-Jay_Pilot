# Changelog

All notable changes to ARUN Trading Bot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
