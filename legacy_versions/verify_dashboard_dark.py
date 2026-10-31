
import customtkinter as ctk
import sys
import os
import threading
import time

# Mock dependencies to allow running without full bot backend
sys.modules['kickstart'] = type('kickstart', (), {
    'run_cycle': lambda: None, 
    'fetch_market_data': lambda: {}, 
    'config_dict': {}, 
    'SYMBOLS_TO_TRACK': [], 
    'calculate_intraday_rsi_tv': lambda: {},
    'is_system_online': lambda: True,
    'safe_get_positions': lambda: {},
    'safe_get_live_positions_merged': lambda: {
        'TATASTEEL': {'source': 'BOT', 'qty': 100, 'avg_price': 150.0, 'ltp': 155.0, 'pnl': 500.0},
        'INFY': {'source': 'MANUAL', 'qty': 10, 'avg_price': 1400.0, 'ltp': 1380.0, 'pnl': -200.0}
    },
    'reload_config': lambda: None,
    'fetch_funds': lambda: 50000.0,
    'reset_stop_flag': lambda: None,
    'set_log_callback': lambda x: None,
    'initialize_from_csv': lambda: None,
    'request_stop': lambda: None,
    'panic_button': lambda: None
})

sys.modules['market_sentiment'] = type('market_sentiment', (), {
    'MarketSentiment': type('MarketSentiment', (), {'fetch_sentiment': lambda self: {'sentiment': 'BULLISH'}})
})

sys.modules['settings_manager'] = type('settings_manager', (), {
    'SettingsManager': type('SettingsManager', (), {
        'get': lambda self, k, d: 100000.0 if k == 'capital.allocated_limit' else d,
        'load': lambda self: True
    })
})

sys.modules['state_manager'] = type('state_manager', (), {
    'StateManager': type('StateManager', (), {
        'state': {},
        'get_trade_counters': lambda self: {'attempts': 5, 'success': 3, 'failed': 0}
    })
})

sys.modules['database.trades_db'] = type('trades_db', (), {
    'TradesDatabase': type('TradesDatabase', (), {
        'get_performance_summary': lambda self, days: {'net_profit': 1250.50, 'total_trades': 5, 'win_rate': 60},
        'get_recent_trades': lambda self, limit: []
    })
})

sys.modules['knowledge_center'] = type('knowledge_center', (), {
    'TOOLTIPS': {}, 'STRATEGY_GUIDES': {}, 'get_strategy_guide': lambda x: "", 'get_contextual_tip': lambda x: ""
})

# Now import the actual dashboard
from dashboard_v2 import DashboardV2

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    root = ctk.CTk()
    app = DashboardV2(root)
    
    # Simulate some log activity
    def simulate_logs():
        time.sleep(2)
        app.write_log("ℹ System initialized in Dark Neon mode\n")
        time.sleep(1)
        app.write_log("🚀 Engine started monitoring TATASTEEL, INFY\n")
        time.sleep(1)
        app.write_log("✅ Connection established with broker\n")
        
    threading.Thread(target=simulate_logs, daemon=True).start()
    
    root.mainloop()
