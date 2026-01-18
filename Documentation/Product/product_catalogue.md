# ARUN Trading Bot - Product Catalogue & Technical Specifications (Titan V2)

**Version:** 2.0 (Titan)
**Date:** January 18, 2026
**Confidentiality:** Internal Use Only

---

## 1. Executive Summary
The **ARUN Trading Bot (Titan V2)** is a sophisticated, automated algorithmic trading system designed for the Indian Stock Market (NSE/BSE). It leverages the **mStock (Mirae Asset)** API to execute high-frequency and swing trading strategies with precision.

Unlike standard trading scripts, Titan V2 features a **"Human-First" Bento Grid Interface**, a **Market Sentiment Engine**, and an **Smart Knowledge Center** that educates the user while trading. It bridges the gap between complex algorithmic execution and user-friendly investment management.

---

## 2. Key Features & Capabilities

### 🧠 Intelligent Trading & Analysis
*   **Market Sentiment Engine:** Real-time analysis of NIFTY 50 trends and India VIX volatility to determine the "Market Mood" (Fear, Greed, Neutral).
*   **RSI Mean Reversion Strategy:** Automatically identifies overbought (>65) and oversold (<35) conditions to execute mean reversion trades.
*   **Smart SIP (Systematic Investment Plan):** (Optional) Dollar-cost averaging module for long-term wealth building, triggered by specific technical dips.
*   **Paper Trading Mode:** A fully simulated environment to test strategies with zero financial risk before going live.

### 🛡️ Risk Management (The "Safety Net")
*   **Circuit Breaker:** Automatically halts all trading if daily losses exceed a predefined limit (e.g., 10%).
*   **Panic Button (Emergency Exit):** One-click execution to square off all open positions and cancel pending orders in milliseconds.
*   **Capital Protection:** "Funds" card visualizes Real vs. Allocated capital, ensuring you never over-leverage.
*   **NIFTY 50 Filter:** Strictly limits trading to India's top 50 blue-chip companies to avoid low-liquidity "penny stock" traps.

### 🖥️ Next-Gen User Interface (Titan V2)
*   **Bento Grid Layout:** A modern, card-based dashboard inspired by Apple/linear.app design principles.
*   **Glassmorphism & Dark Mode:** Reduces eye strain and provides a premium, professional aesthetic.
*   **Contextual "Smart Tips":** The bot explains *why* it's taking an action (e.g., *"Market is Fearful; buying quality dips is historically profitable"*).
*   **Live Performance Tracking:** Real-time P&L, Win Rate metrics, and Active Position monitoring.

### 🔐 Enterprise-Grade Security
*   **TOTP 2FA Auto-Login:** Secure, automated daily login using Time-based One-Time Passwords (like Google Authenticator). No manual token entry required.
*   **Credential Encryption:** Sensitive API keys and passwords are encrypted using local key management (`settings_manager.py`).
*   **Single Instance Locking:** Prevents accidental double-launching of the bot, which could lead to duplicate orders.

---

## 3. Technical Specifications

| Component | Specification |
| :--- | :--- |
| **Language** | Python 3.10+ |
| **GUI Framework** | CustomTkinter (Modernized Tkinter Wrapper) |
| **Broker API** | mStock (Mirae Asset) Open API (Type A) |
| **Data Source** | Live Socket / REST Polling (1-second intervals) |
| **Database** | SQLite3 (Local storage for trade history & paper trading) |
| **Concurrency** | Multi-threaded (Background Data Fetching, Main UI Thread) |
| **Security** | `fernet` encryption for config, `pyotp` for 2FA |
| **OS Compatibility** | Windows 10/11 (Primary), capable of Linux/VPS deployment |

---

## 4. Configuration & Bot Settings
The bot is fully configurable via the **Settings Tab** or `settings.json`. Below are the critical parameters available for the fund manager/user.

### 💰 Capital Management
*   **`Total Capital`**: The maximum amount (in ₹) the bot is allowed to utilize.
*   **`Max Per Stock`**: Cap exposure per single stock (e.g., 10% of total capital) to ensure diversification.
*   **`Daily Loss Limit`**: The "Stop Trading" threshold (e.g., 5% loss in a single day).

### ⚙️ Strategy Settings (RSI)
*   **`Timeframe`**: The candle interval for analysis (e.g., `15T` for 15-min, `1D` for Daily).
*   **`Buy Threshold`**: RSI value to trigger a BUY signal (Default: `< 35`).
*   **`Sell Threshold`**: RSI value to trigger a SELL signal (Default: `> 65`).
*   **`Stop Loss %`**: Automatic exit percentage if trade goes against prediction (Default: 5%).
*   **`Profit Target %`**: Automatic take-profit percentage (Default: 10%).

### 🔔 Notifications (Optional)
*   **telegram/email**: Can be configured to send instant alerts for:
    *   Trade Execution (Buy/Sell)
    *   Daily P&L Summary
    *   Emergency Errors

---

## 5. Workflow & Architecture

1.  **Launch**: User starts `LAUNCH_ARUN.bat`.
2.  **Authentication**: Bot auto-logs in using API Key + TOTP.
3.  **Data Stream**: Bot subscribes to real-time quotes for watchlist symbols.
4.  **Signal Generation**:
    *   *Input*: Price & Volume Data.
    *   *Process*: Calculate Indicators (RSI, VIX).
    *   *Decision*: If (RSI < Buy_Threshold) AND (Sentiment != Extreme Fear), then BUY.
5.  **Execution**: Order sent to mStock API.
6.  **Monitoring**: Position tracked in real-time for Stop-Loss/Target hits.
7.  **Reporting**: Trade logged to `database/trades.db` and displayed on Dashboard.

---

## 6. Future Roadmap (Preview)
*   **Mobile Companion App**: View-only mode for checking P&L on the go.
*   **AI News Sentiment**: Integrating LLMs to read financial news and filter stocks.
*   **Option Selling Module**: For advanced delta-neutral strategies.

---
*Generated by Antigravity Feature Development Team*
