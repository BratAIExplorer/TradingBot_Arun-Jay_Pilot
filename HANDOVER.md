# 🤝 ARUN Bot - Technical Handover Document

**Version:** V1.0 (Desktop Product Release)
**Date:** January 2026
**Target Audience:** Developers, AI Agents, Technical Reviewers

---

## 🏗️ Architecture Overview

ARUN has evolved from a simple script into a productized desktop application. It follows a decoupled architecture where the logic engine runs independently of the UI.

### Key Components

1.  **Engine (`kickstart.py`):**
    *   The core brain. Handles market data fetching, signal processing (RSI), and order execution.
    *   **New in V1:** Contains logic for "Paper Trading" (routing to DB) and "Investment Mode" (skipping sells).
    *   **Dependencies:** `database/trades_db.py`, `risk_manager.py`, `settings_manager.py`.

2.  **GUI (`kickstart_gui.py` & `settings_gui.py`):**
    *   Built with `customtkinter`.
    *   **kickstart_gui.py:** The Dashboard. Polling-based update loop (`update_dashboard`) that reads from `database/trades_db.py` and an internal queue.
    *   **settings_gui.py:** Configuration manager. Reads/Writes to `settings.json` and `config_table.csv`.

3.  **Database (`database/trades_db.py`):**
    *   **SQLite** based storage.
    *   **Schema:** `trades` table.
    *   **Critical Update:** Added `broker` column.
        *   `broker='mstock'` -> Real Trade.
        *   `broker='PAPER'` -> Simulated Trade.
    *   **Migration:** Automatic migration logic in `_run_migrations` adds this column to existing DBs.

---

## 🚀 New V1 Features (Technical Logic)

### 1. Paper Trading Mode
*   **Toggle:** Controlled by `app_settings.paper_trading_mode` in `settings.json`.
*   **Logic:** In `kickstart.place_order`, if enabled:
    *   Does **NOT** call mStock API.
    *   Calls `db.insert_trade(..., broker='PAPER')`.
    *   Returns `True` to simulate success.
*   **UI:** `get_positions` now queries the DB for paper trades and tags them as `is_paper=True`. The Dashboard renders these rows in **Blue**.

### 2. Investment Mode (Accumulation)
*   **Config:** `config_table.csv` has a new column: `Strategy`.
    *   Values: `TRADE` (Standard RSI Buy/Sell) or `INVEST` (Buy Only).
*   **Logic:** In `kickstart.process_market_data`:
    *   If `Strategy == 'INVEST'` AND Signal is SELL: The bot logs "HODLing" and skips the sell order *unless* a Profit Target is hit (optional safety).

### 3. Nifty 50 Filter
*   **Config:** `app_settings.nifty_50_only` in `settings.json`.
*   **Source:** `nifty50.py` set.
*   **Logic:** Filter is applied in the main loop of `kickstart.py`. Non-Nifty stocks are skipped if enabled.

---

## 🛠️ Build & Deployment

The project is configured for **PyInstaller** to generate a standalone Windows Executable.

*   **Spec File:** `build.spec` (Includes all hidden imports like `PIL`, `sqlite3`, `pandas`).
*   **Build Script:** `build_release.bat`.
*   **Output:** `dist/ARUN_Bot.exe`.

### How to Build
```cmd
build_release.bat
```

---

## 🔮 Future Roadmap (For Next Dev)

1.  **Web Migration:**
    *   The current `kickstart.py` is ready for a web backend.
    *   **Task:** Replace `kickstart_gui.py` with a FastApi/Flask server. Use `kickstart.py` as a background worker (Celery/Redis).

2.  **Advanced Risk:**
    *   Implement "Friday Liquidation" logic.
    *   Add Portfolio-level stop loss (currently only per-position).

3.  **License Server:**
    *   If monetizing beyond "Friends & Family", implement a remote check in `license_manager.py` (currently stubbed/removed).

---

## ⚠️ Known Issues / Notes
*   **mStock Token:** The bot still requires a valid mStock session for *Market Data* even in Paper Mode. Paper Mode simulates *Execution*, not Data Feed.
*   **Database Lock:** SQLite can occasionally lock if the GUI and Engine try to write simultaneously. `check_same_thread=False` is enabled, but consider migrating to PostgreSQL for high-scale Web V2.
