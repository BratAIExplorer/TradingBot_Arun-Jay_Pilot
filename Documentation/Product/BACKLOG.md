# 📋 ARUN Trading Bot: Product Backlog

This document tracks all pending features, enhancements, and long-term vision items for the ARUN Titan project.

## 🔴 Phase 4: High Priority (The "Infrastructure" Sprint)
*Goal: Move from Local Desktop to 24/7 Cloud/Mobile Presence.*

**✅ COMPLETE (Jan 18, 2026):**
- [✅] **Headless Core**: Extract `run_cycle` from GUI dependency to allow VPS deployment.
  - Delivered: `bot_daemon.py` (441 lines) - standalone headless runner
  - Features: start/stop/restart/status commands, PID management, logging with rotation
  - Agent: Claude AI

- [✅] **Mobile Dashboard (Streamlit)**: Read-only web UI for P&L and status monitoring.
  - Delivered: `mobile_dashboard.py` (614 lines) - real-time monitoring UI
  - Features: P&L, positions, trades, logs viewer, password-protected
  - Agent: Claude AI

- [✅] **VPS Deployment Guide**: Documentation for setting up on AWS/DigitalOcean.
  - Delivered: `Documentation/VPS_DEPLOYMENT.md` (650 lines)
  - Features: 13-step setup, systemd config, security, troubleshooting
  - Agent: Claude AI

**✅ COMPLETE - Google AI Parallel Work (Jan 18, 2026):**
- [✅] **Enhanced Settings GUI Tabs** (1,018 lines total):
  - `gui/settings_tabs/__init__.py` (16 lines)
  - `gui/settings_tabs/regime_tab.py` (243 lines) - Market regime settings
  - `gui/settings_tabs/stop_loss_tab.py` (278 lines) - Risk management
  - `gui/settings_tabs/paper_live_tab.py` (278 lines) - Trading mode toggle
  - `gui/settings_tabs/api_test_tab.py` (203 lines) - Broker API testing
  - Branch: `google/enhanced-settings-gui`
  - Agent: Google AI

- [✅] **Symbol Validator Fix**:
  - Fixed: `symbol_validator.py` - Now properly validates NSE stocks
  - Agent: Google AI

**📋 BACKLOG:**
- [ ] **Hybrid Holding Management**: Logic to manage existing user stocks with "Take Over" toggle.
- [ ] **Smart Order Suggestions**: Real-time Bid/Ask validation to optimize entry prices ("Grammarly for Trading").

## 🟡 Phase 5: Medium Priority (The "Intelligence" Sprint)
*Goal: Enhance the bot's reasoning and safety capabilities.*

- [ ] **News Sentiment Engine**: Integrate RSS/Financial News feeds into the AI Reasoning box.
- [ ] **TOTP Hardened Panic**: Screen blur + mandatory 2FA check before executing a "Sell All" command.
- [ ] **Smart SIP Module**: Rules-based accumulation for Blue-chips/ETFs on technical dips.
- [ ] **Advanced Performance Analytics**: Integrated stats tab (Win Rate, Drawdown, Profit Factor).
- [ ] **Auto-Update System**: In-app notification when a new version is pushed to Git.

## 🟢 Good to Have (The "Polish" Sprint)
*Goal: User experience refinements and multi-strategy support.*

- [ ] **Multi-Strategy library**: Selectable strategies (MACD, Bollinger, Supertrend) in Settings.
- [ ] **Multi-Broker Integration**: Expand beyond mStock to other Indian brokers.
- [ ] **Dark/Light Mode Toggle**: Built-in theme switcher for the Titan UI.
- [ ] **Cloud Sync**: Securely sync `settings.json` and `trades.db` across multiple machines.
- [ ] **Interactive Charts**: Lightweight plotting of RSI/Price directly in the "Active Positions" view.

---
**Status**: Titan V2 (Phase 2) + Phase 4 Infrastructure Sprint ✅ **COMPLETE** (Jan 18, 2026).

**Recent Completion**:
- Claude AI: VPS deployment suite (bot_daemon.py, mobile_dashboard.py, VPS guide)
- Google AI: Enhanced settings GUI tabs (4 new tabs + validator fix)

**Next Sprint**: Phase 4.1 or Phase 5 (pending decision)
