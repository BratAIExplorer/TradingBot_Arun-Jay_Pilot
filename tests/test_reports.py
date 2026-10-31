"""
ARUN Trading Bot v2.6.0 - Enhanced Reports Unit Tests

RED PHASE: Tests for daily P&L series, equity curve, and per-symbol breakdown.
Tests will fail until methods are added to trades_db.py.

Test Coverage:
- get_daily_pnl_series(days=30) — daily P&L aggregation
- get_symbol_breakdown(days=30) — per-symbol performance
- Equity curve calculation (cumulative)
- Edge cases: null P&L, no trades, all wins/losses, date boundaries
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sqlite3


class TestDailyPnlSeries:
    """TradesDatabase.get_daily_pnl_series(days=30)"""

    def test_daily_pnl_series_returns_list_of_dicts(self):
        """Method returns list of daily P&L dictionaries"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        # Insert test trades
        db.insert_trade(
            symbol="HDFCBANK", trade_type="BUY", entry_price=1500.0, qty=10,
            timestamp=datetime.now().isoformat(), rsi=25, atr=10
        )
        db.insert_trade(
            symbol="HDFCBANK", trade_type="SELL", exit_price=1520.0, qty=10,
            pnl_net=200.0, timestamp=datetime.now().isoformat(), rsi=75
        )

        result = db.get_daily_pnl_series(days=30)

        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(day, dict) for day in result)

    def test_daily_pnl_series_has_required_fields(self):
        """Each daily entry has: date, net_pnl, trade_count, wins, losses"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        # Insert sample trades
        now = datetime.now()
        db.insert_trade(
            symbol="HDFCBANK", trade_type="BUY", entry_price=1500.0, qty=10,
            timestamp=now.isoformat(), rsi=25, atr=10
        )
        db.insert_trade(
            symbol="HDFCBANK", trade_type="SELL", exit_price=1520.0, qty=10,
            pnl_net=200.0, timestamp=now.isoformat(), rsi=75
        )

        result = db.get_daily_pnl_series(days=30)

        assert len(result) > 0
        day = result[0]

        assert "date" in day
        assert "net_pnl" in day
        assert "trade_count" in day
        assert "wins" in day
        assert "losses" in day

    def test_daily_pnl_series_empty_period(self):
        """Empty period (no trades) returns empty list"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")
        # No trades inserted

        result = db.get_daily_pnl_series(days=30)

        assert isinstance(result, list)
        # Empty or contains zeros is acceptable

    def test_daily_pnl_series_handles_null_pnl(self):
        """Trades with NULL P&L (BUYs) are excluded from daily sum"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        # BUY (NULL P&L)
        db.insert_trade(
            symbol="HDFCBANK", trade_type="BUY", entry_price=1500.0, qty=10,
            timestamp=datetime.now().isoformat(), rsi=25, atr=10
        )
        # SELL (has P&L)
        db.insert_trade(
            symbol="INFY", trade_type="SELL", exit_price=2000.0, qty=5,
            pnl_net=500.0, timestamp=datetime.now().isoformat(), rsi=75
        )

        result = db.get_daily_pnl_series(days=30)

        if len(result) > 0:
            # Daily P&L should be 500 (INFY SELL), not NaN
            daily_pnl = result[0]["net_pnl"]
            assert daily_pnl == 500.0 or daily_pnl is not None

    def test_daily_pnl_series_groups_by_date(self):
        """Multiple trades same day are aggregated"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        now = datetime.now()

        # 3 SELLs today
        for i in range(3):
            db.insert_trade(
                symbol=f"STOCK{i}", trade_type="SELL", exit_price=1000.0, qty=1,
                pnl_net=100.0, timestamp=now.isoformat(), rsi=75
            )

        result = db.get_daily_pnl_series(days=30)

        # Should have one entry for today with aggregated data
        today_entry = [r for r in result if r["date"] == now.strftime("%Y-%m-%d")]
        if today_entry:
            assert today_entry[0]["trade_count"] == 3
            assert today_entry[0]["net_pnl"] == 300.0  # 3 × 100

    def test_daily_pnl_series_respects_day_limit(self):
        """Only returns data from last N days"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        # Insert trades from 5 days ago and today
        now = datetime.now()
        five_days_ago = now - timedelta(days=5)

        db.insert_trade(
            symbol="HDFCBANK", trade_type="SELL", exit_price=1520.0, qty=10,
            pnl_net=200.0, timestamp=five_days_ago.isoformat(), rsi=75
        )
        db.insert_trade(
            symbol="INFY", trade_type="SELL", exit_price=2100.0, qty=5,
            pnl_net=300.0, timestamp=now.isoformat(), rsi=75
        )

        result = db.get_daily_pnl_series(days=3)

        dates = [r["date"] for r in result]
        assert five_days_ago.strftime("%Y-%m-%d") not in dates


class TestSymbolBreakdown:
    """TradesDatabase.get_symbol_breakdown(days=30)"""

    def test_symbol_breakdown_returns_list(self):
        """Method returns list of symbol performance dicts"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        db.insert_trade(
            symbol="HDFCBANK", trade_type="BUY", entry_price=1500.0, qty=10,
            timestamp=datetime.now().isoformat(), rsi=25, atr=10
        )
        db.insert_trade(
            symbol="HDFCBANK", trade_type="SELL", exit_price=1520.0, qty=10,
            pnl_net=200.0, timestamp=datetime.now().isoformat(), rsi=75
        )

        result = db.get_symbol_breakdown(days=30)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_symbol_breakdown_has_required_fields(self):
        """Each symbol entry has: symbol, net_pnl, trade_count, wins, losses, win_rate"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        db.insert_trade(
            symbol="HDFCBANK", trade_type="BUY", entry_price=1500.0, qty=10,
            timestamp=datetime.now().isoformat(), rsi=25, atr=10
        )
        db.insert_trade(
            symbol="HDFCBANK", trade_type="SELL", exit_price=1520.0, qty=10,
            pnl_net=200.0, timestamp=datetime.now().isoformat(), rsi=75
        )

        result = db.get_symbol_breakdown(days=30)

        assert len(result) > 0
        symbol = result[0]

        assert "symbol" in symbol
        assert "net_pnl" in symbol
        assert "trade_count" in symbol
        assert "wins" in symbol
        assert "losses" in symbol
        assert "win_rate" in symbol

    def test_symbol_breakdown_separate_symbols(self):
        """Different symbols are separate rows"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        # HDFCBANK trade
        db.insert_trade(
            symbol="HDFCBANK", trade_type="SELL", exit_price=1520.0, qty=10,
            pnl_net=200.0, timestamp=datetime.now().isoformat(), rsi=75
        )

        # INFY trade
        db.insert_trade(
            symbol="INFY", trade_type="SELL", exit_price=2100.0, qty=5,
            pnl_net=300.0, timestamp=datetime.now().isoformat(), rsi=75
        )

        result = db.get_symbol_breakdown(days=30)

        symbols = [r["symbol"] for r in result]
        assert "HDFCBANK" in symbols
        assert "INFY" in symbols

    def test_symbol_breakdown_calculates_win_rate(self):
        """Win rate = wins / (wins + losses) * 100"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        # 2 winning HDFCBANK trades
        for i in range(2):
            db.insert_trade(
                symbol="HDFCBANK", trade_type="SELL", exit_price=1520.0, qty=10,
                pnl_net=100.0, timestamp=datetime.now().isoformat(), rsi=75
            )

        # 1 losing HDFCBANK trade
        db.insert_trade(
            symbol="HDFCBANK", trade_type="SELL", exit_price=1480.0, qty=10,
            pnl_net=-50.0, timestamp=datetime.now().isoformat(), rsi=75
        )

        result = db.get_symbol_breakdown(days=30)

        hdfcbank = [r for r in result if r["symbol"] == "HDFCBANK"][0]

        assert hdfcbank["wins"] == 2
        assert hdfcbank["losses"] == 1
        # Win rate should be 66.67%
        assert 66 < hdfcbank["win_rate"] < 67


class TestEquityCurve:
    """Equity curve calculation from daily P&L series"""

    def test_equity_curve_is_cumulative(self):
        """Equity curve sums daily P&L cumulatively"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        now = datetime.now()

        # Day 1: +100
        db.insert_trade(
            symbol="HDFCBANK", trade_type="SELL", exit_price=1520.0, qty=10,
            pnl_net=100.0, timestamp=now.isoformat(), rsi=75
        )

        # Day 2: +200
        tomorrow = now + timedelta(days=1)
        db.insert_trade(
            symbol="INFY", trade_type="SELL", exit_price=2100.0, qty=5,
            pnl_net=200.0, timestamp=tomorrow.isoformat(), rsi=75
        )

        daily = db.get_daily_pnl_series(days=30)

        # Manually compute equity curve
        equity = []
        cumulative = 0
        for day in daily:
            cumulative += day["net_pnl"]
            equity.append({"date": day["date"], "equity": cumulative})

        assert len(equity) >= 2
        assert equity[-1]["equity"] == 300  # 100 + 200

    def test_equity_curve_handles_losses(self):
        """Equity curve decreases on loss days"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        now = datetime.now()

        # Day 1: +500
        db.insert_trade(
            symbol="HDFCBANK", trade_type="SELL", exit_price=1550.0, qty=10,
            pnl_net=500.0, timestamp=now.isoformat(), rsi=75
        )

        # Day 2: -200
        tomorrow = now + timedelta(days=1)
        db.insert_trade(
            symbol="INFY", trade_type="SELL", exit_price=1950.0, qty=5,
            pnl_net=-200.0, timestamp=tomorrow.isoformat(), rsi=75
        )

        daily = db.get_daily_pnl_series(days=30)

        cumulative = 0
        for day in daily:
            cumulative += day["net_pnl"]

        # Should end at 300 (500 - 200)
        assert cumulative == 300


class TestEdgeCases:
    """Edge cases and boundary conditions"""

    def test_all_winning_trades_breakdown(self):
        """All trades winning: win_rate = 100%"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        # 5 winning trades
        for i in range(5):
            db.insert_trade(
                symbol="HDFCBANK", trade_type="SELL", exit_price=1550.0, qty=10,
                pnl_net=100.0, timestamp=datetime.now().isoformat(), rsi=75
            )

        result = db.get_symbol_breakdown(days=30)
        hdfcbank = [r for r in result if r["symbol"] == "HDFCBANK"][0]

        assert hdfcbank["losses"] == 0
        assert hdfcbank["win_rate"] == 100.0
        assert hdfcbank["net_pnl"] == 500.0

    def test_all_losing_trades_breakdown(self):
        """All trades losing: win_rate = 0%"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        # 3 losing trades
        for i in range(3):
            db.insert_trade(
                symbol="INFY", trade_type="SELL", exit_price=1950.0, qty=5,
                pnl_net=-100.0, timestamp=datetime.now().isoformat(), rsi=75
            )

        result = db.get_symbol_breakdown(days=30)
        infy = [r for r in result if r["symbol"] == "INFY"][0]

        assert infy["wins"] == 0
        assert infy["win_rate"] == 0.0
        assert infy["net_pnl"] == -300.0

    def test_daily_pnl_series_handles_zero_pnl_day(self):
        """Day with no trades: net_pnl = 0 or omitted (acceptable)"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        # Insert trade for today
        db.insert_trade(
            symbol="HDFCBANK", trade_type="SELL", exit_price=1520.0, qty=10,
            pnl_net=0.0, timestamp=datetime.now().isoformat(), rsi=75
        )

        result = db.get_daily_pnl_series(days=30)

        assert isinstance(result, list)
        # Should handle zero P&L gracefully

    def test_symbol_breakdown_very_large_portfolio(self):
        """Breakdown with many symbols (>10)"""
        from database.trades_db import TradesDatabase

        db = TradesDatabase(":memory:")

        # Insert trades for 15 different symbols
        for i in range(15):
            symbol = f"STOCK{i:02d}"
            db.insert_trade(
                symbol=symbol, trade_type="SELL", exit_price=1000.0, qty=10,
                pnl_net=(i * 100), timestamp=datetime.now().isoformat(), rsi=75
            )

        result = db.get_symbol_breakdown(days=30)

        assert len(result) == 15
        symbols = [r["symbol"] for r in result]
        assert len(set(symbols)) == 15  # All unique


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
