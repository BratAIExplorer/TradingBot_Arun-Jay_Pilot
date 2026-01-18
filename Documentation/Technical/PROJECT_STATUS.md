# 🏗️ ARUN Project Status & Architecture (Titan V2)

**Last Updated:** January 18, 2026
**Version:** Titan V2 (Phase 2 Complete)

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
| `API_Reference.md` | **The Integration.** Detailed map of mStock Open API endpoints used by the bot. | ✅ Active |
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
*   **Crash Resilience**: Fixed race conditions in background threads and GUI initialization.
*   **Hot-Reloading**: Settings can now be saved and applied without restarting the entire bot.
*   **Source Tagging**: Every trade in the database is now marked as `BOT` or `MANUAL` for cleaner audits.
*   **Professional Installer**: Surfshark-style EXE installer for one-click setup on new machines.

---
*Note: For the next AI developer, please refer to `AI_HANDOVER.md` for deep technical context.*
