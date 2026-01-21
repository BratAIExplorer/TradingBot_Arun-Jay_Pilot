# 📄 RSI Strategy Implementation - Decision Log

This document records the technical decisions and architectural options for the **ARUN Trading Bot's** RSI-based mean reversion strategy.

---

## 🕒 Current Decision (Active)

### **Option A: The "Deep Historical Seed" (Phase A)**
*   **Action**: On bot startup (configuration load), the bot will fetch precisely **200 candles** of historical data from the **m.Stock API** (`/instruments/historical`).
*   **Status**: ✅ **SELECTED**
*   **Rationale**: 
    *   **Mathematical Stability**: RSI-14 requires a "warm-up" period to stabilize. While 14 bars technically allows a calculation, 200 bars ensures the local value exactly matches professional terminals like TradingView or Interactive Brokers.
    *   **Data Integrity**: By fetching data directly from the executing broker (m.Stock) instead of a third party, we eliminate "price drift" errors.
    *   **"Buffett-Approved"**: Prioritizes precision and quality over speed.

---

## 📈 Alternative Options (Under Consideration)

The following options are documented for potential future implementation based on live performance data.

### **Option B: The "15-Minute Anchor"**
*   **Concept**: Shift from 1-minute or 5-minute intervals to a **15-Minute Timeframe**.
*   **Pros**: Reduces market noise and "jitter." Prevents the bot from buying a "falling knife" that is only oversold for a brief moment.
*   **When to Pivot**: If the bot is taking too many losing trades due to intraday volatility or "price wicks."

### **Option C: The "Smart Trigger & Margin Cushion"**
*   **Concept**: Add sophisticated risk-based entry logic.
*   **Logic**: Before placing an order, the bot checks not just "Available Cash," but ensures the trade consumes no more than **10% of total portfolio value**.
*   **When to Pivot**: If the bot is over-leveraging or concentrating too much capital in a single stock.

---

### **Phase B: Smart Polling & Memory Buffer**
*   **Action**: Instead of fetching 365 days of data every cycle, the bot maintains a **local buffer (CANDLE_CACHE)**. It seeds once and then performs **Incremental Updates (2-day lookback)** to bridge gaps, saving bandwidth and improving speed.
*   **Status**: ✅ **IMPLEMENTED**
*   **Implementation**: Logic merged into `get_stabilized_rsi` in `kickstart.py`.

### **Phase C: Smart Trigger & Portfolio Risk**
*   **Action**: Integrated a "Double Safety" check before entry:
    1.  **Bot Capital Check**: Ensures trade fits within `ALLOCATED_CAPITAL`.
    2.  **10% Risk Rule**: Rejects trades exceeding 10% of total portfolio value to prevent over-concentration.
*   **Status**: ✅ **IMPLEMENTED**
*   **Implementation**: Logic integrated into `process_market_data` in `kickstart.py`.

---

## 🛠️ Implementation Progress

1.  **Refactor `getRSI.py`**: [DONE] Created `calculate_rsi_from_df` for broker-integrated DataFrames.
2.  **Update `kickstart.py`**: [DONE] 
    *   Initialize `CANDLE_CACHE`.
    *   Implemented Phase B (Incremental updates with deduplication).
    *   Implemented Phase C (Capital check + 10% concentration limit).
3.  **Setup Wizard**: [DONE] Created `SETUP_ENVIRONMENT.bat` for founder onboarding.
4.  **Validation**: [DONE] Dry-run verify code structure and logic stability.

---

> [!NOTE]
> *This log serves as the source of truth for the "Research Partner" strategy phase. Any changes to the chosen option must be recorded here with a rationale.*
