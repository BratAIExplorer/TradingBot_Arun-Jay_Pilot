# 📄 Conditions vs. Code Comparison

This document compares the requirements specified in **`Set of conditions.docx`** against the actual implementation in **`kickstart.py`** and **`config_table.csv`**.

---

## ⚠️ Configuration Discrepancies

The following values in `config_table.csv` do not match the requirements in the document.

| Feature | Document Requirement | Current Code / Config | Action Needed |
| :--- | :--- | :--- | :--- |
| **Buy RSI Trigger** | **≤ 30** | **35** | Update `Buy RSI` in `config_table.csv` to 30 |
| **Sell RSI Trigger** | **≥ 70** | **65** | Update `Sell RSI` in `config_table.csv` to 70 |
| **Profit Target** | **+5%** | **10%** | Update `Profit Target %` in `config_table.csv` to 10 |
| **Default Quantity** | **1** (unless higher) | **0** | Update `Quantity` in `config_table.csv` to ≥ 1 |

---

## ✅ Logic Matches

The core logic in `kickstart.py` correctly implements the strategic rules defined in the document.

### 1. Order Type
- **Document**: "Always CNC (Cash & Carry) — never MIS."
- **Code**: `place_order()` function explicitly sets `product='CNC'` and `validity='DAY'`.
- **Status**: ✅ **MATCH**

### 2. No Loss Selling
- **Document**: "Never sell below entry price." / "Sell triggered only if price ≥ entry price".
- **Code**: 
  ```python
  can_consider_sell = current_close > pos["price"]
  should_sell = (last_rsi >= sell_rsi and can_consider_sell) ...
  ```
- **Status**: ✅ **MATCH**

### 3. Re-Entry & Loops
- **Document**: "Once a sell is executed... active becomes False... allowing a fresh buy."
- **Code**: Position tracking relies on live broker data (`safe_get_live_positions_merged`). Once a sell order is executed and holdings update, the available quantity becomes 0, satisfying the "No Existing Position" check for a new buy.
- **Status**: ✅ **MATCH**

### 4. Carry Forward
- **Document**: "If sell conditions aren’t met, hold overnight."
- **Code**: The bot checks existing broker holdings on startup. It does not force-close positions at end of day, inherently "carrying forward" positions.
- **Status**: ✅ **MATCH**

### 5. Multi-Stock Tracking
- **Document**: "Independent Tracking: Each stock’s position... tracked separately."
- **Code**: The bot iterates through `SYMBOLS_TO_TRACK` and maintains separate state dictionaries (`portfolio_state`) and checks specific symbol holdings.
- **Status**: ✅ **MATCH**

---

## 📝 Recommendations

To fully align the bot with the `Set of conditions.docx`, applying the following updates to `config_table.csv` is recommended:

**Current Config (`config_table.csv`):**
```csv
Symbol,Broker,Enabled,Timeframe,Buy RSI,Sell RSI,Profit Target %,Quantity,Exchange
MICEL,mstock,TRUE,15T,35,65,10,0,BSE
MOSCHIP,mstock,TRUE,15T,35,65,10,0,NSE
...
```

**Recommended Config (to match Document):**
```csv
Symbol,Broker,Enabled,Timeframe,Buy RSI,Sell RSI,Profit Target %,Quantity,Exchange
MICEL,mstock,TRUE,15T,30,70,5,1,BSE
MOSCHIP,mstock,TRUE,15T,30,70,5,1,NSE
...
```
