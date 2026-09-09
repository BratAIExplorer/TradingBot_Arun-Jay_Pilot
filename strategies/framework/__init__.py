"""
Strategy framework for the ARUN bot.

A small plug-in layer so new trading strategies can be added as one file each,
sharing one isolated database, one runner loop, and one dashboard — without ever
touching the live RSI bot (kickstart.py / risk_manager.py / trades.db).

Public pieces:
  base       - Candidate / Position / Action / Strategy protocol
  config     - per-strategy JSON -> frozen dataclass
  store      - database/strategies.db (scan_results, positions, fills, daily_snapshot)
  registry   - name -> Strategy instance
  broker     - Zerodha CNC orders + account value (log-only until enabled)
  fundamentals - yfinance fundamentals, cached one row/day
"""
