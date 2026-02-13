# 🏗️ ARUN Project Status & Architecture (Titan V2)

**Last Updated:** February 13, 2026
**Version:** Titan V2.4.2 (Risk UI Mode & Cross-Exchange Fix)

---

## 📂 File Structure & Functionality Map

Here is the updated breakdown of the Titan V2 codebase.

### 🟢 Core Trading Logic & UI
| File | Purpose | Status |
|------|---------|--------|
| `kickstart.py` | **The Brain.** Headless trading engine. Handles API calls, RSI logic, and trade execution. | ✅ Active |
| `dashboard_v2.py` | **The Face.** Titan V2 UI (Bento Grid). Dark mode, real-time metrics, and sector-based control. | ✅ Active |
| `market_sentiment.py`| **The Mood.** Fear/Greed index calculation with live reasoning engine. | ✅ Active |
| `settings_gui.py` | **The Control Room.** Embedded 5-tab settings panel for broker, risk, and stock config. | ✅ Active |
| `settings_manager.py`| Handles encrypted config storage and TOTP-based auto-login. | ✅ Active |

### 🔧 Utilities & Database
| File | Purpose | Status |
|------|---------|--------|
| `database/trades_db.py`| **The Ledger.** SQLite database for trade history (tagged BOT vs MANUAL). | ✅ Active |
| `risk_manager.py` | Enforces circuit breakers, stop-losses, and "Safety Box" capital limits. | ✅ Active |
| `strategies/` | Folder containing `sector_map.py` and `trading_tips.json` for the Knowledge Tab. | ✅ Active |

---

## 🚦 Feature Status Matrix

### ✅ Phase 2: UX Intelligence (Delivered)
- **Titan Bento UI**: Strategy grouping by Sector (Financials, IT, etc.) with panic exit buttons.
- **Smart Knowledge Tab**: Integrated trading library and "Tip of the Day" system.
- **Sentiment Meter**: Semi-circle widget with AI-driven reasoning (e.g., "VIX Spiking").
- **Capital Safety Box**: Precise slider-based fund allocation to protect your primary bankroll.
- **Realistic Simulation**: Refined Paper Trading mode with dynamic random-walk pricing.

### 🚧 Works in Progress / Deferred
1. **Mobile Companion (Phase 4)**: Architecture defined for a Headless + Streamlit web dashboard.
2. **Smart Order Suggestions**: "Grammarly for Trading" validation (Planned).
3. **Hybrid Holding Management**: Logic to allow the bot to manage existing manual stocks.

---

## 🛠 Recent Engineering Improvements
*   **Risk UI Modernization (v2.4.2)**: Redesigned Settings > Risk Controls with grouped cards, visual sliders, and improved safety toggles. Added `COLOR_DANGER` constants.
*   **Duplicate Buy Fix (v2.4.2)**: Made `check_existing_orders` symbol-aware across all exchanges. Prevents buying `ABC` on NSE if `ABC` is already held/ordered on BSE.
*   **Config Self-Healing (v2.4.2)**: Fixed corrupted `settings.json` where strategies were stuck as `NaN`, defaulting them to `TRADE`.
*   **REIT OHLC Fix (v2.3.1)**: Fixed REIT OHLC API 400 errors. Numeric token mapping (`NSE:9383`) was wrong - OHLC API expects scrip names. Now tries BSE exchange first for REITs (where they're listed as regular equity), eliminating log spam.
*   **Scanner Key Case Fix (v2.3.1)**: Fixed `scanner_complete()` using lowercase `r['signal']` vs scanner engine's uppercase `r['SIGNAL']`, which prevented STRONG BUY/BUY summary counts from displaying.
*   **REIT Mapping & Fallback**: Resolved mStock OHLC API errors for `EMBASSY` and `BIRET` by implementing scrip token mapping and a holdings-based price fallback.
*   **Balance Accuracy**: Fixed "Used" capital inflation by strictly summing only `BOT` tagged positions and correctly tagging manual holdings as `BUTLER`.
*   **Connectivity Hardening**: Standardized browser-like headers and refined offline detection to prevent engine pauses during transient API issues.
*   **Hot-Reloading**: Settings can now be saved and applied without restarting the entire bot.
*   **Professional Installer**: Surfshark-style EXE installer for one-click setup on new machines.

---
*Note: For the next AI developer, please refer to `AI_HANDOVER.md` for deep technical context.*
