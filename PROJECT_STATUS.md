# 🏗️ ARUN Project Status & Architecture

**Last Updated:** January 11, 2026
**Version:** Pilot Release v1

---

## 📂 File Structure & Functionality Map

Here is a detailed breakdown of every file in the codebase and its specific role.

### 🟢 Core Trading Logic
| File | Purpose | Status |
|------|---------|--------|
| `kickstart.py` | **The Brain.** Main trading loop. Fetches data, calculates RSI, executes trades, and manages the bot's lifecycle. | ✅ Active |
| `kickstart_gui.py` | **The Face.** CustomTkinter GUI that launches `kickstart.py` in a thread. Displays dashboard, logs, and controls. | ✅ Active |
| `risk_manager.py` | **The Shield.** Enforces stop-loss, profit targets, and daily loss limits. Called by the trading loop. | ✅ Active |
| `state_manager.py` | **The Memory.** Manages persistent state (e.g., "Bot is Running", "Offline Mode") to survive restarts. | ✅ Active |
| `symbol_validator.py` | **The Gatekeeper.** Validates stock symbols with the exchange before allowing them into the config. | ✅ Active |

### 🔧 Utilities & Helpers
| File | Purpose | Status |
|------|---------|--------|
| `utils.py` | Helper functions for date/time, logging, and common formatting tasks. | ✅ Active |
| `getRSI.py` | Dedicated module for calculating RSI using the TradingView methodology (Wilder's Smoothing). | ✅ Active |
| `nifty50.py` | **NIFTY 50 Filter.** Whitelist of top 50 Indian stocks for safe filtering. (Previously confused with "Regime Monitor") | ✅ Active |
| `notifications.py` | System for sending email and Telegram alerts for trades and errors. | ✅ Active |

### ⚙️ Configuration & Data
| File | Purpose | Status |
|------|---------|--------|
| `config_table.csv` | **User Rules.** The main input for users to define stocks, RSI thresholds, and quantities. | ✅ Active |
| `settings.json` | **App Config.** Stores global settings (API keys, themes, notification toggles, risk limits). | ✅ Active |
| `settings_manager.py` | Handles reading/writing `settings.json` and encrypting sensitive data (passwords/keys). | ✅ Active |
| `settings_gui.py` | GUI window for editing `settings.json` user-friendly way. | ✅ Active |
| `database/` | Folder containing `trades.db` (SQLite) for storing trade history and paper trading records. | ✅ Active |

### 🚀 Build & Deployment
| File | Purpose | Status |
|------|---------|--------|
| `START_HERE.bat` | **Smart Installer (Batch).** Auto-detects Python, creates venv, installs dependencies. For advanced users. | ✅ Active |
| `installer_gui.py` | **Professional GUI Installer.** Surfshark-style windowed installer with progress bars and animations. | ✅ MVP 3 |
| `build_installer.bat` | **Installer Builder.** Compiles `installer_gui.py` into standalone EXE using PyInstaller. | ✅ MVP 3 |
| `setup_wizard.py` | **First-Run Config.** GUI wizard for entering API credentials on first launch. | ✅ Active |
| `create_shortcut.py` | Python script to create desktop shortcuts (venv-aware, OneDrive compatible). | ✅ Active |
| `requirements.txt` | List of Python libraries (relaxed versions for Python 3.13 compatibility). | ✅ Active |
| `_dev_tools/build_release.bat` | **EXE Builder (Legacy).** Builds full app EXE. Archived for advanced use. | 🗄️ Archived |

---

## 🚦 Feature Status Matrix

### ✅ Implemented Features (MVP1 Week 1)
- **RSI Mean Reversion**: Fully functional in `kickstart.py`.
- **Sell Presets**: RSI Only, Profit Only, and Hybrid modes available in Settings.
- **Position Sizing**: Supports Fixed Quantity, Fixed Capital, and Portfolio % methods.
- **Nifty SIP**: Automated weekly accumulation strategy for ETFs.
- **Backtesting Setup**: Simulation tab added to GUI (uses `backtesting.py` + `yfinance`).
- **Knowledge Center**: Educational guides integrated into the GUI.
1.  **RSI Mean Reversion Strategy:** Buying on dips (RSI < 30/35), selling on highs (RSI > 65/70).
2.  **Paper Trading Mode:** Simulate trades without real money to test strategies.
3.  **GUI Dashboard:** Real-time P&L, active positions, and log console.
4.  **Risk Management:**
    *   Stop-Loss (Fixed %)
    *   Profit Targets (Fixed %)
    *   Daily Loss Limit (Circuit Breaker)
5.  **Notifications:** Email and Telegram alerts for filled orders.
6.  **Robust Build System:** One-click `.exe` generation for non-technical users.
7.  **Crash Recovery:** Auto-restart on minor errors, persistent state.
8.  **Smart Batch Installer (MVP 2):** `START_HERE.bat` with auto-Python detection, logging, Quick Start mode.
9.  **Professional GUI Installer (MVP 3):** Surfshark-style windowed installer with animated progress bars, step tracking, and error handling.

### 🚧 Works in Progress / Partially Complete
1.  **Regime Filter:** Logic exists to check NIFTY 50 trend, but currently disabled/experimental in `kickstart.py`.
2.  **Advanced Charts:** Basic RSI plotting is planned but not fully integrated into the main GUI.

### ❌ Not Started / Roadmap
1.  **Mobile App:** Currently Desktop only.
2.  **Multi-Strategy:** Adding MACD, Bollinger Bands, etc.
3.  **Cloud Sync:** Syncing settings between different computers.

---

## 🛠 Recent Fixes (in this update)
*   **Crash Fix:** Downgraded `yfinance` to `0.2.40` to resolve the "TypeError: unsupported operand type(s)" error on launch.
*   **Shortcut Fix:** Replaced the broken "VBScript" shortcut creator with a Python-native solution (`create_shortcut.py`) that handles OneDrive paths correctly.
*   **Build Unified:** Merged `install_and_build.bat` logic to ensure a clean, consistent build every time.
