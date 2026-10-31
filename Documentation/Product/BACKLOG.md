# ARUN Trading Bot: Product Backlog

**Last Updated**: February 16, 2026 | **Current Version**: v2.5.1

---

## NEXT UP: Smart Reconciliation System (Recommended)

**Concept**: Broker-as-Source-of-Truth reconciliation — industry standard for lean trading systems.

### Features
- **Reactive Correction**: On order failure ("Insufficient Quantity"), immediately cross-check that symbol with broker holdings
  - Shares gone (manual sell) → mark position `CLOSED` in DB
  - Shares exist but blocked (T1/Pledged) → mark `RESTRICTED`, pause selling
  - Shares exist that bot didn't buy → mark `ORPHANED`, show but don't auto-sell
- **Proactive Sync**: Full holdings reconciliation 3x/day (market open 9:15, lunch 12:00, pre-close 15:15) — NOT every cycle
- **User Notification**: Toast in dashboard on every auto-correction ("RELIANCE: Detected manual sell — position marked Closed")
- **Implementation**: Single `reconcile_with_broker()` method in `kickstart.py` — no new files needed

### Design Principles
- Only 3 states: `CLOSED`, `RESTRICTED`, `ORPHANED` — don't over-engineer
- Never auto-correct silently (family-friendly = no surprises)
- Minimal API load (reactive + 3x proactive, not every 90s cycle)

---

## v2.6.0: GUI Modernization & Reliability Sprint

### P0 — Must Fix (Reliability)

- [ ] **Settings Input Validation**: Capital fields accept negative numbers, API fields accept garbage. Add:
  - Positive number validation for capital/percentages
  - Regex for API key format
  - YYYY-MM-DD enforcement for date fields
  - Min/max bounds on sliders (stop_loss 0.1-50%, profit_target 1-100%)
- [ ] **Remove Zerodha Dropdown**: Settings GUI shows "zerodha" broker option with zero backend. Remove it — one broker, own it.
- [ ] **Consolidate Duplicate Risk Config**: `settings.json` has both `risk_controls` (line 33) and `risk` (line 81) with overlapping `stop_loss_pct`. Pick one, migrate the other.
- [ ] **Replace Bare Excepts**: 20+ instances of `except: pass` across codebase. Change to `except Exception: logging.debug(...)` — silent failures are the #1 reliability killer.

### P1 — High Impact (Modern & Lean)

- [ ] **Unify Button Styling**: Main app uses `COLOR_ACCENT/SUCCESS/DANGER` constants but `settings_gui.py` uses hardcoded `"#3498DB"`, `"#2ECC71"`, `"green"`, `"darkgreen"`. Unify to shared constants.
- [ ] **Connection Status Indicator**: Small green/yellow/red dot in header showing broker API health. Currently user must start engine to know if connected.
- [ ] **Loading/Skeleton States**: When positions are loading, show shimmer or "Loading..." instead of empty cards.
- [ ] **Extract Hardcoded Strings**: ~15 scattered strings ("ARUN ADMIN", version labels, button text). Extract to constants file.
- [ ] **Strategies Tab Content**: Currently mostly placeholder cards with "Configure" buttons. Either build it out or remove the tab.

### P2 — Medium Effort (Architecture)

- [ ] **Extract `broker_api.py`**: Pull `perform_auto_login()`, `get_positions()`, `merge_positions_and_orders()`, `safe_request()` out of `kickstart.py` (~30% size reduction, testable).
- [ ] **Parallel Scanner**: `concurrent.futures.ThreadPoolExecutor(5)` in scanner_engine — cuts 1200-stock scan from 4+ min to under 1 min.
- [ ] **Consistent Font Usage**: Mix of `("Roboto", 11, "bold")`, `("Arial", 14, "bold")`, `("Roboto", 14, "bold")` across GUI. Standardize to Roboto family only.

### P3 — Polish (Customer-Friendly)

- [ ] **Emoji Rendering**: Heavy emoji use (fire, shield, arrows) may not render consistently on all Windows versions. Consider fallback text labels alongside emojis.
- [ ] **Color-Only Messaging**: Some status indicators rely on color alone (green=good, red=bad). Add text/icon labels for accessibility.
- [ ] **Input Masking**: API key/token fields should show `*` characters with a toggle eye icon to reveal.
- [ ] **Version from Constant**: "ARUN TITAN v2.0.3" hardcoded in dashboard header — should pull from a `VERSION` constant so it auto-updates.

---

## Existing Backlog (From Previous Sprints)

### Phase 4: Infrastructure
- [x] **Headless Core**: Extracted — `kickstart.py` runs independently
- [x] **VPS Deployment Guide**: Created at `Documentation/Technical/VPS_DEPLOYMENT_GUIDE.md`
- [x] **Hybrid Holding Management**: Butler mode implemented
- [ ] **Mobile Dashboard (Streamlit)**: Deferred — web frontend (Next.js) exists at `web-frontend/`
- [ ] **Smart Order Suggestions**: Bid/Ask validation — not started

### Phase 5: Intelligence
- [ ] **News Sentiment Engine**: RSS/Financial News integration
- [ ] **TOTP Hardened Panic**: Screen blur + 2FA for Sell All
- [ ] **Smart SIP Module**: Rules-based accumulation on dips
- [ ] **Advanced Performance Analytics**: Win Rate, Drawdown, Profit Factor tab
- [ ] **Auto-Update System**: Git-based version notification

### Phase 6: Polish
- [ ] **Multi-Strategy Library**: MACD, Bollinger, Supertrend selectable
- [ ] **Multi-Broker Integration**: Beyond mStock
- [ ] **Dark/Light Mode Toggle**: Theme switcher
- [ ] **Cloud Sync**: Settings + trades across machines
- [ ] **Interactive Charts**: RSI/Price plotting in Active Positions view

---

## Completed (v2.5.1)

- [x] Security audit — all P0-P3 fixes applied
- [x] Encryption bypass fixed
- [x] Secrets removed from logs
- [x] Singleton SettingsManager
- [x] Thread safety locks
- [x] Scanner stop propagation
- [x] Dead code cleanup (~134 lines)
- [x] REIT BSE fallback
- [x] Scanner key case fix
- [x] Trade CSV export
- [x] Panic stop mid-cycle
- [x] RMS cooldown

---

*For audit details see `Documentation/Technical/SECURITY_ARCHITECTURE_AUDIT_v2.5.0.md`*
*For fix details see `Documentation/Technical/ERROR_LOG_AND_FIXES.md`*
