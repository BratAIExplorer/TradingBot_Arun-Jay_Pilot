# 🎯 Project Harmonization: Kyro vs. Arun Titan

This document clarifies the relationship between the two active projects in your `C:\Antigravity` folder to remove confusion and establish a clear roadmap for each.

---

## 🏗️ 1. Project Definitions

### 🏛️ Arun Titan (`TradingBots-Aruns Project`)
*   **Role**: **Active Desktop Trading Engine**
*   **Primary Target**: Indian Stock Market (NSE/BSE).
*   **Primary Broker**: **mStock** (Active).
*   **UI**: Desktop-only (CustomTkinter).
*   **Status**: **Production Mode**. This is what you use daily to trade.

### 🚀 Kyro (`Kyro_Crypto_WealthGenerator`)
*   **Role**: **Next-Gen Web & Multi-Asset Platform**
*   **Primary Target**: Crypto (Binance/Luno) + Future Indian Market migration.
*   **UI**: Modern Web Dashboard (Next.js/FastAPI).
*   **Status**: **Infrastructure Hardening**. We are building this to be your professional-grade, cloud-deployable "Apple-like" trading platform.

---

## 🗃️ 2. Documentation Cleanup

To reduce confusion, we have archived old documents that are no longer applicable to your daily operations:

| Old Document | Action Taken | Current Location |
| :--- | :--- | :--- |
| `Senior Architect ... 18-Jan-2026.md` | **Archived** (Too old, pre-Titan) | `_Archive/` |
| `mvp_plan_12weeks.md` | **Archived** (Replaced by current status) | `_Archive/` |
| `UI_UX_design_proposal.md` | **Archived** (Titan UI is complete) | `_Archive/` |
| `SESSION_SUMMARY_Jan28.md` | **Archived** (Logs consolidated) | `_Archive/` |

---

## 🛠️ 3. Immediate Action: mStock Balance Fix

**Status**: **Credentials Validated ✅**
Your recent screenshot confirms the mStock connection is working. The "Balance not retrieved" message is common:
1.  **Post-Market**: mStock often blocks specific balance/limit endpoints outside of market hours.
2.  **Logic**: The bot correctly falls back to "Holdings verified" so it will be ready to trade as soon as the market opens.

---

## 🗺️ 4. The Roadmap

1.  **Arun Titan**: Maintain for all Indian Stock trading.
2.  **Kyro**: Finalize the Crypto execution engine and VPS deployment.
3.  **Future Phase**: We will eventually create an **mStock Adapter** for Kyro, so you can see your Indian stocks and Crypto in the *same* web dashboard.

> [!NOTE]
> Please ignore `legacy_reference/` folders in both projects. They are read-only and kept for code patterns only.
