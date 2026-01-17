# MStock API & Bot Enhancement Proposal (Living Document)

**Status**: DRAFT v1.3 (Added Reasoning & Bird's Eye View)
**Last Updated**: 2026-01-17
**Owner**: ARUN Project Team (Architect, Financial Expert, PO, Dev)

---

## 1. Portfolio Management Enhancements

### A. Existing Stock Management (Hybrid Mode)
The goal is to allow the BOT to manage *existing* user holdings without purely assuming a "cash" start, while keeping "Human in the Loop" by default.

#### Features
1.  **Per-Stock Toggle**:
    *   **Description**: A granular list of current holdings where users check specific stocks the BOT is allowed to touch.
    *   **Default**: Unchecked (Safe Mode).
2.  **Separate Profit/Loss Settings**:
    *   **Description**: Distinct configuration for "Inherited Positions" vs "Bot-Initiated Positions".
    *   **Data Source**: Uses `average_price` from `GET /portfolio/holdings` as the cost basis.
3.  **Watchlist vs. Auto Mode**:
    *   **Watchlist (Default)**: Bot monitors price/logic. If Signal = SELL, Bot sends **Alert/Notification**. User manually clicks "Execute" to confirm.
    *   **Auto**: Bot monitors price/logic. If Signal = SELL, Bot executes order immediately.
4.  **Confirmations**:
    *   **Safety**: Explicit "Type 'CONFIRM'" text dialog required to switch a stock from Manual -> Auto.

### B. Portfolio API Gaps
| Feature | Problem | Solution |
| :--- | :--- | :--- |
| **Pagination** | >50 stocks truncation. | Client implements `while` loop pagination logic (Page 1, 2, 3...) to aggregate full list seamlessly. |
| **History** | Limited to 1000 bars. | Add `from/to` date batching logic. |

---

## 2. Advanced GUI/UX Features (Modern Card-Based Design)

### A. Market Sentiment "Mood Meter" + Reasoning Engine
*   **Visual**: "Speedometer" Widget (Top Right of Dashboard).
    *   **Zones**: Red (Fear), Amber (Neutral), Green (Greed).
*   **NEW: Live Reasoning Box**:
    *   Right below the meter, a scrolling "News Ticker" or specific text box explains **WHY**:
    *   *Example*: "Sentiment is **RED** because: NIFTY down 2% today AND VIX (Volatility) rose by 15%."
    *   *Value*: Builds trust. User understands it's not random.
*   **Hybrid Control**:
    *   **Option 1 (Info)**: Alerts only.
    *   **Option 2 (Auto-Protect)**: If Fear > 80%, stricter Stop Losses apply automatically.

### B. Basket Performance (Thematic View)
*   **Visual**: "Bento Grid" style cards.
*   **Card UI**:
    *   **Header**: Banking Sector (Icon)
    *   **Body**: Mini-sparkline graph showing trend.
    *   **Footer**: "Sell All" button (Red) | "Rebalance" button (Blue).

### C. Smart Order Suggestions ("Grammarly for Trading")
*   **Concept**: Real-time validation of user inputs.
*   **Flow**:
    *   User clicks "Buy @ 1500".
    *   System checks Order Book (Best Ask @ 1495).
    *   **Intervention**: "Save ₹5? Click to Adjust Price."
    *   **Config**: "Always optimize price" checkbox available in settings.

---

## 3. Security & Infrastructure

### A. Connectivity
*   **Webhooks**: Push notifications for Order Fills.
*   **Compression**: Gzip for speed.

### B. 2FA (The "Nuclear Option")
*   **Triggers**: "Panic Sell All", "Change Withdrawal Bank", "Delete Strategy".
*   **Mechanism**: TOTP (Google Authenticator).
*   **Experience**:
    *   User Action -> Screen Blur -> "Enter 6-digit Code" -> Execution.
    *   Zero reliance on SMS delivery.

---

## 4. Technical Q&A Log
*   **Purchase Price**: API `average_price`.
*   **Pagination**: Loop logic.
*   **2FA**: Google Auth (Offline, Fast).
