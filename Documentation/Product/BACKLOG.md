# 📋 ARUN Trading Bot: Product Backlog

This document tracks all pending features, enhancements, and long-term vision items for the ARUN Titan project.

## 🔴 Phase 4: High Priority (The "Infrastructure" Sprint)
*Goal: Move from Local Desktop to 24/7 Cloud/Mobile Presence.*

- [ ] **Headless Core**: Extract `run_cycle` from GUI dependency to allow VPS deployment.
- [ ] **Mobile Dashboard (Streamlit)**: Read-only web UI for P&L and status monitoring.
- [ ] **Hybrid Holding Management**: Logic to manage existing user stocks with "Take Over" toggle.
- [ ] **Smart Order Suggestions**: Real-time Bid/Ask validation to optimize entry prices ("Grammarly for Trading").
- [ ] **VPS Deployment Guide**: Documentation for setting up on AWS/DigitalOcean.

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
**Status**: Titan V2 (Phase 2) is currently **LIVE**. Backlog items are scheduled for Phase 4.
