"""
Additional helper methods for TradingGUI class
Add these methods before the run() method in kickstart_gui.py (around line 420)
"""

def open_settings(self):
    """Open settings GUI"""
    try:
        import subprocess
        subprocess.Popen(["python", "settings_gui.py"], shell=False)
    except Exception as e:
        self.write_log(f"❌ Failed to open Settings: {e}\n")

def update_trades_table(self):
    """Update recent trades table from database"""
    if not DATABASE_AVAILABLE or not hasattr(self, 'trades_table'):
        return
    
    try:
        # Clear existing
        for item in self.trades_table.get_children():
            self.trades_table.delete(item)
        
        # Get recent trades (last 10)
        recent_trades = db.get_recent_trades(limit=10)
        
        for trade in recent_trades:
            # Format time
            timestamp = trade.get('timestamp', '')[:16]  # YYYY-MM-DD HH:MM
            symbol = trade.get('symbol', '')
            action = trade.get('action', '')
            qty = trade.get('quantity', 0)
            price = f"₹{trade.get('price', 0):,.2f}"
            gross = f"₹{trade.get('gross_amount', 0):,.2f}"
            fees = f"₹{trade.get('total_fees', 0):.2f}"
            net = f"₹{trade.get('net_amount', 0):,.2f}"
            
            # Color code by action
            tag = 'buy' if action == 'BUY' else 'sell'
            self.trades_table.insert("", "end", values=(
                timestamp, symbol, action, qty, price, gross, fees, net
            ), tags=(tag,))
        
        # Color coding
        self.trades_table.tag_configure('buy', foreground='green')
        self.trades_table.tag_configure('sell', foreground='red')
        
    except Exception as e:
        self.write_log(f"⚠️ Failed to update trades table: {e}\n")

def update_performance_summary(self):
    """Update performance summary cards"""
    if not DATABASE_AVAILABLE:
        return
    
    try:
        perf = db.get_performance_summary()
        
        # Update labels
        if hasattr(self, 'portfolio_value_label'):
            self.portfolio_value_label.configure(text=f"₹{perf.get('total_net_pnl', 0):,.0f}")
        
       if hasattr(self, 'today_pnl_label'):
            today_pnl = perf.get('total_net_pnl', 0)
            pnl_color = "green" if today_pnl >= 0 else "red"
            self.today_pnl_label.configure(
                text=f"₹{today_pnl:,.0f}",
                text_color=pnl_color
            )
        
        if hasattr(self, 'total_trades_label'):
            self.total_trades_label.configure(text=str(perf.get('total_trades', 0)))
        
        if hasattr(self, 'win_rate_label'):
            win_rate = perf.get('win_rate', 0)
            winrate_color = "green" if win_rate >= 50 else "orange"
            self.win_rate_label.configure(
                text=f"{win_rate:.1f}%",
                text_color=winrate_color
            )
        
        # Update trades table
        self.update_trades_table()
        
    except Exception as e:
        self.write_log(f"⚠️ Failed to update performance: {e}\n")
