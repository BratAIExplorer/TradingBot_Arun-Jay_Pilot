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

## 🛠️ Implementation Plan for Option A

1.  **Refactor `getRSI.py`**: Stop using `yfinance` and create a handler for m.Stock's historical JSON format.
2.  **Update `kickstart.py`**:
    *   Modify initialization to query 200 bars.
    *   Implement a local `DataFrame` buffer to store these 200 bars.
    *   Update the loop to only fetch the *latest* single candle and append it to the buffer (Phase B logic).
3.  **Validation**: Compare local RSI values against m.Stock/TradingView web interfaces to confirm 0.01% precision.

---

> [!NOTE]
> *This log serves as the source of truth for the "Research Partner" strategy phase. Any changes to the chosen option must be recorded here with a rationale.*
