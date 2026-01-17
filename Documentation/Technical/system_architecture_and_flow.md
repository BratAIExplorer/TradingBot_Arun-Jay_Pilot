# System Architecture & User Flow Map (Bird's Eye View)

This document maps the entire user journey from high-level goals down to the specific API execution.

| **Status** | **User Goal** | **Feature (GUI)** | **Logic / Security** | **UX Flow** |
| :--- | :--- | :--- | :--- | :--- |
| **🟢 LIVE** | **Protect Capital** | **Sentiment "Mood Meter"** | Monitor Nifty & VIX via `yfinance`. AI Reasoning logic. | User sees Meter + "Reasoning Box" explaining market conditions. |
| **🟢 LIVE** | **Sell Underperformers** | **Basket / Sector View** | Aggregate P&L by Sector (Bank, IT). | User views "Sector Cards". Click "Sell All" for a specific sector. |
| **🟢 LIVE** | **Emergency Exit** | **Panic Button** | Kill Switch Logic. Square off all positions instantly. | One-click "Panic Stop" on dashboard to exit all trades. |
| **🟡 ROADMAP** | **Manage Legacy Stocks**| **Portfolio "Hybrid" Toggle** | `average_price` sync + Manual vs Auto toggle. | User checks "Enable Bot for INFY". Type "CONFIRM" to hand over control. |
| **🟡 ROADMAP** | **Prevent Mistakes** | **Smart Order Suggestion** | Compare User Price vs. Best Ask. | User types price. Popup: "Save ₹5? Buy @ 1495". |
| **🟡 ROADMAP** | **Hardened Exit** | **2FA Panic (Blur)** | TOTP Verification on Panic Sell. | Screen Blurs on Panic click. Enter `123456` to execute. |


---

## Design Philosophy Inspiration
*   **"Bento Grids" (Apple/Google Style)**: Everything is a self-contained card. Information is dense but organized.
*   **"Progressive Disclosure"**: Show simple info first (Total P&L). Click to see complex info (Individual Trades).
*   **"Friction by Design"**: Make dangerous things (Selling All) hard to do accidentally. Make good things (Saving money/Limit Orders) easy to do.
