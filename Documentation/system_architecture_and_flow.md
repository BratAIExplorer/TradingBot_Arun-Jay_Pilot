# System Architecture & User Flow Map (Bird's Eye View)

This document maps the entire user journey from high-level goals down to the specific API execution.

| **User Goal** | **Feature (GUI)** | **Logic / Security** | **MStock API Endpoint** | **UX Flow** |
| :--- | :--- | :--- | :--- | :--- |
| **Protect Capital** | **Sentiment "Mood Meter"** | Monitor Market Breadth & VIX.<br>If < 30 (Fear) -> Tighten Stop Loss. | `GET /market/sentiment`<br>(or derived locally) | User sees RED meter + "Reasoning Box".<br>Bot logs: "Switched to Safe Mode". |
| **Manage Legacy Stocks** | **Portfolio "Hybrid" Toggle** | Check `average_price`.<br>Calculate P&L based on historical buy.<br>Req. user confirm for "AUTO". | `GET /portfolio/holdings` | User checks "Enable Bot for INFY".<br>Type "CONFIRM".<br>Bot takes over. |
| **Sell Underperformers** | **Basket / Sector View** | Aggregate P&L by Tag (Bank, IT).<br>Identify "Weakest Link". | `GET /portfolio/holdings`<br>`POST /orders/bulk` | User views "IT Sector Card (-5%)".<br>Clicks "Sell Basket".<br>Bot sells INFY, TCS, etc. |
| **Prevent Mistakes** | **Smart Order Suggestion** | Compare User Price vs. Best Ask.<br>If Diff > Threshold -> Alert. | `GET /quote/ltp`<br>(Order Book Depth) | User types 1500.<br>Popup: "Save ₹5? Buy @ 1495".<br>User clicks "Yes". |
| **Emergency Exit** | **Panic Button (2FA)** | **TOTP Verification** (Google Auth).<br>No SMS dependency.<br>Kill Switch Logic. | `POST /orders/cancelall`<br>`POST /orders` (Market Sell) | Click Panic.<br>Screen Blurs.<br>Enter `123456`.<br>All Positions Closed. |

---

## Design Philosophy Inspiration
*   **"Bento Grids" (Apple/Google Style)**: Everything is a self-contained card. Information is dense but organized.
*   **"Progressive Disclosure"**: Show simple info first (Total P&L). Click to see complex info (Individual Trades).
*   **"Friction by Design"**: Make dangerous things (Selling All) hard to do accidentally. Make good things (Saving money/Limit Orders) easy to do.
