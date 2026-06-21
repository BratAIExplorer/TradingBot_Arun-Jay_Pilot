import sys
sys.path.append('/opt/zepp')
from database.trades_db import TradesDatabase
db = TradesDatabase('/opt/zepp/database/trades.db')
print("Database initialized successfully at /opt/zepp/database/trades.db")
