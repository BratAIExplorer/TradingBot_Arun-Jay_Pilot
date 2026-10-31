---
# Orbit Trading - Market Selector Integration Guide

How to integrate the market selector into the existing dashboard.
---

## Quick Integration (5 steps)

### Step 1: Create UI Package
```bash
mkdir -p ui
touch ui/__init__.py
# Copy market_selector.py to ui/market_selector.py
```

### Step 2: Import in Dashboard
```python
# At top of sensei_v1_dashboard.py
from ui.market_selector import MarketSelector, MARKETS, MultiMarketPortfolioView
```

### Step 3: Add Market Selector to Top Nav
```python
# In DashboardV2.__init__(), after window setup:

self.nav_frame = ctk.CTkFrame(self.root, fg_color=COLOR_CARD, height=60)
self.nav_frame.pack(fill="x", pady=5, padx=5)

# Market selector
self.market_selector = MarketSelector(
    self.nav_frame,
    on_market_change=self._on_market_changed,
    current_market="IN"
)
self.market_selector.pack(side="left", padx=10, pady=10)

# Store for later access
self.current_market = "IN"
self.current_market_config = MARKETS["IN"]
```

### Step 4: Handle Market Changes
```python
# Add this method to DashboardV2 class:

def _on_market_changed(self, market: str):
    """Handle market selection change."""
    self.current_market = market
    self.current_market_config = MARKETS[market]
    
    # Reload portfolio for this market
    self._refresh_portfolio_for_market(market)
    
    # Update status
    self.write_log(f"📊 Switched to {self.current_market_config.name} market")

def _refresh_portfolio_for_market(self, market: str):
    """Reload portfolio data for the selected market."""
    # Query trades for this market
    trades = self.db.get_recent_trades(
        limit=100,
        market=market  # Filter by market
    )
    
    # Filter by source (BOT trades for this market)
    bot_trades = [t for t in trades if t["broker"] != "PAPER"]
    
    # Update UI
    self._update_portfolio_display(bot_trades)
```

### Step 5: Update Portfolio View
```python
# Modify portfolio display to show market currency:

def _update_portfolio_display(self, trades):
    """Display portfolio for current market."""
    currency = self.current_market_config.currency
    
    # Show trades with correct currency
    for trade in trades:
        # ₹ for India, $ for US
        price_str = f"{currency}{trade['price']:.2f}"
        pnl_str = f"{currency}{trade.get('pnl_net', 0):.2f}"
        
        # Add to UI (update your existing portfolio display)
```

---

## Optional: Dual-Market View

If user wants to see BOTH markets simultaneously:

```python
# In nav_frame, add a toggle button:

self.btn_view_mode = ctk.CTkButton(
    self.nav_frame,
    text="View Both Markets",
    command=self._toggle_dual_view,
    fg_color=COLOR_ACCENT,
    text_color="white",
    font=("Roboto", 11, "bold")
)
self.btn_view_mode.pack(side="left", padx=10, pady=10)

def _toggle_dual_view(self):
    """Toggle between single market and dual-market view."""
    if self.dual_view_mode:
        self.dual_view_mode = False
        self.btn_view_mode.configure(text="View Both Markets")
        self.market_selector.pack(side="left")  # Show market selector
        self._single_market_view()
    else:
        self.dual_view_mode = True
        self.btn_view_mode.configure(text="View India ↔ US")
        self.market_selector.pack_forget()  # Hide market selector
        self._dual_market_view()

def _dual_market_view(self):
    """Show both markets simultaneously."""
    # Create MultiMarketPortfolioView
    self.dual_portfolio = MultiMarketPortfolioView(self.main_frame)
    self.dual_portfolio.pack(fill="x", padx=10, pady=10)
    
    # Update with data
    india_pnl = self._get_market_pnl("IN")
    us_pnl = self._get_market_pnl("US")
    combined = self._calculate_combined_pnl(india_pnl, us_pnl)
    
    self.dual_portfolio.update_pnl(india_pnl, us_pnl, combined)

def _single_market_view(self):
    """Show single market."""
    if self.dual_portfolio:
        self.dual_portfolio.pack_forget()
```

---

## Market Status Updates

Update market status indicator in real-time:

```python
# In run_cycle (or background thread):

from markets import is_market_open

def _update_market_status(self):
    """Update market status indicators."""
    for market in ['IN', 'US']:
        is_open = is_market_open(market)
        self.market_selector.set_market_status(market, is_open)

# Call this periodically (e.g., every minute)
def _start_status_update_loop(self):
    """Background thread to update market status."""
    import threading
    
    def update_loop():
        while self.running:
            self._update_market_status()
            time.sleep(60)  # Update every minute
    
    thread = threading.Thread(target=update_loop, daemon=True)
    thread.start()
```

---

## Database Changes

Ensure trades table has `market` column:

```python
# In trades_db.py migration (already done in Phase 1):

ALTER TABLE trades ADD COLUMN market TEXT DEFAULT 'IN';

# Create index for fast filtering
CREATE INDEX idx_trades_market ON trades(market);
```

---

## Settings Integration

Load per-market settings when market changes:

```python
# In _on_market_changed:

def _on_market_changed(self, market: str):
    """Handle market selection change."""
    self.current_market = market
    self.current_market_config = MARKETS[market]
    
    # Load market-specific settings
    self.market_settings = self.settings_mgr.get_market_settings(market)
    
    # Apply RSI thresholds for this market
    self.rsi_threshold_buy = self.market_settings.get('rsi_threshold_buy', 30)
    self.rsi_threshold_sell = self.market_settings.get('rsi_threshold_sell', 70)
    self.min_volume = self.market_settings.get('min_volume', 100000)
    
    self._refresh_portfolio_for_market(market)
```

---

## Testing the Integration

```python
# Test script: test_market_selector.py

import customtkinter as ctk
from ui.market_selector import MarketSelector, MARKETS

root = ctk.CTk()
root.title("Market Selector Test")
root.geometry("800x200")

def on_change(market):
    print(f"Market changed to: {market}")
    config = MARKETS[market]
    print(f"  Currency: {config.currency}")
    print(f"  Exchange: {config.exchange}")
    print(f"  Hours: {config.hours}")

selector = MarketSelector(root, on_market_change=on_change, current_market="IN")
selector.pack(fill="x", padx=10, pady=10)

# Test status updates
selector.set_market_status("IN", True)
selector.set_market_status("US", False)

root.mainloop()
```

**Run with:**
```bash
python test_market_selector.py
```

Expected output:
```
Market changed to: IN
  Currency: ₹
  Exchange: NSE
  Hours: 9:15-15:30 IST
```

---

## Full Integration Checklist

- [ ] Create `ui/` package with `market_selector.py`
- [ ] Import `MarketSelector` in dashboard
- [ ] Add `MarketSelector` to nav frame
- [ ] Implement `_on_market_changed()` callback
- [ ] Implement `_refresh_portfolio_for_market()`
- [ ] Update portfolio display to use `current_market_config.currency`
- [ ] Add market status update loop (every 60 seconds)
- [ ] Verify `trades` table has `market` column
- [ ] Load market-specific settings on market change
- [ ] (Optional) Add dual-market view toggle
- [ ] Test with both India and US market data
- [ ] Verify P&L displays correct currency (₹ vs $)

---

## Result

**Before Integration:**
```
ARUN TITAN V2 - Single market view
└─ Only NSE (India)
└─ All prices in ₹
└─ No market selector
```

**After Integration:**
```
ORBIT TRADING - Multi-market ready
├─ Market Selector [India ▼] [₹ INR] [Hours: 9:15-15:30]
├─ Portfolio (India or US, switchable)
├─ Correct currency display (₹ or $)
├─ Market status indicator (🟢 Open / 🔴 Closed)
└─ Optional: Dual-market view
```

---

Done! The dashboard now supports both India and US markets with clean, simple market selection.
