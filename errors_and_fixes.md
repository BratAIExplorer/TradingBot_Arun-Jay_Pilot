# Error Log & Fixes

## Incident: 2026-02-16 - Order Failure (SCRIP LIMIT INSUFFICIENT)

**Timestamp:** 2026-02-16 17:36:26

**Error Message:**
> ❌ Order failed for HINDCOPPER: RMS:22412602161252:NSE EQUITY 17939 HINDCOPPER CNC EQ MA8224736 S 60 C 585.55 **SCRIP LIMIT INSUFFICIENT BY-60 AND AVAILABLE QTY IS - 0**

**Affected Symbols:**
- HINDCOPPER (Qty: 60)
- TATASTEEL (Qty: 5)

### Root Cause Analysis
The error `SCRIP LIMIT INSUFFICIENT` with `AVAILABLE QTY IS - 0` indicates a synchronization mismatch between the Bot's internal state and the Broker's actual holdings.

1.  **Bot State**: The bot believes it holds these positions. This "phantom" state is likely being restored from the local database (`trades_db.py`) or a stale cache during the `merge_positions_and_orders` process. The bot sees a high profit (e.g., TATASTEEL +10.2%) and attempts to trigger a valid Profit Target Sell.
2.  **Broker State**: The broker (mStock) rejects the order because the actual CNC (Delivery) holdings for these symbols are 0.
3.  **Conflict**: The bot tries to sell what it thinks it has, but the broker says "You don't own this."

**Possible Reasons:**
- **Manual Intervention**: These positions might have been sold manually via the broker's app/website, but the bot was not aware of this sale.
- **Settlement Delays (T1)**: Stocks bought recently might be in the T1 settlement phase. While usually sellable, specific broker restrictions or "Trade to Trade" segments might block CNC selling until delivery.
- **Pledged Shares**: If shares are pledged for margin, they cannot be sold directly without unpledging.

### Current Behavior & Auto-Fix
The bot has a built-in safety mechanism for this specific error:
- It detects the `SCRIP LIMIT INSUFFICIENT` or `AVAILABLE QTY IS - 0` string in the error message.
- It automatically adds the symbol to a **Cooldown List** (`RMS_FAILURES`).
- **Result**: The bot will stop trying to sell this symbol for **1 hour** to prevent log spam and API rate limit issues.

### Recommended Actions
1.  **Verify Holdings**: Check your mStock app. Do you actually hold HINDCOPPER (60) and TATASTEEL (5)?
2.  **If Sold Manually**: The bot's database is out of sync. You may need to manually mark these trades as closed in the database or ignore the alerts until the position clears from the bot's memory (if based on T+1 logic).
3.  **Code Enhancement (Planned)**: Update the bot to automatically "Right-Size" or "invalidate" positions in its local database when this specific error occurs, efficiently syncing with the broker's reality.
