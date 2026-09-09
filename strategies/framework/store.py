"""
The framework's own database — database/strategies.db.

Five strategy-tagged tables: scan_results, fills, positions, daily_snapshot,
position_ohlc.
Completely separate from database/trades.db; the live RSI bot never reads this.

Style mirrors database/scan_results_db.py (cursor in try/finally, Row factory).
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from typing import Optional


class Store:
    def __init__(self, db_path: str = "database/strategies.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create()

    def _create(self):
        cur = self.conn.cursor()
        try:
            cur.executescript(
                """
                CREATE TABLE IF NOT EXISTS scan_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy TEXT NOT NULL,
                    scan_date TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    scan_mode TEXT,
                    rank INTEGER,
                    ticker TEXT NOT NULL,
                    exchange TEXT,
                    price REAL,
                    score INTEGER,
                    signal TEXT,
                    reason TEXT,
                    extra TEXT
                );
                CREATE INDEX IF NOT EXISTS ix_scan ON scan_results(strategy, scan_date, rank);

                CREATE TABLE IF NOT EXISTS fills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    exchange TEXT,
                    side TEXT NOT NULL CHECK(side IN ('BUY','SELL')),
                    qty INTEGER NOT NULL,
                    price REAL NOT NULL,
                    reason TEXT,
                    orders_enabled INTEGER NOT NULL DEFAULT 0,
                    order_value REAL,
                    qty_after INTEGER,
                    realised_pnl REAL,
                    fee_estimate REAL
                );
                CREATE INDEX IF NOT EXISTS ix_fills ON fills(strategy, timestamp);

                CREATE TABLE IF NOT EXISTS positions (
                    strategy TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    exchange TEXT,
                    qty INTEGER NOT NULL,
                    avg_entry REAL NOT NULL,
                    tranches INTEGER NOT NULL,
                    entry_cross_date TEXT,
                    opened_at TEXT,
                    first_red_date TEXT,
                    status TEXT NOT NULL DEFAULT 'OPEN',
                    closed_at TEXT,
                    high_water_mark REAL,
                    trailing_floor REAL,
                    profit_pct REAL,
                    mae_pct REAL,
                    exit_drawdown_pct REAL,
                    days_held INTEGER NOT NULL DEFAULT 0,
                    days_red INTEGER NOT NULL DEFAULT 0,
                    days_green INTEGER NOT NULL DEFAULT 0,
                    stranded INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (strategy, ticker)
                );

                CREATE TABLE IF NOT EXISTS position_ohlc (
                    strategy TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    ohlc_date TEXT NOT NULL,
                    open REAL, high REAL, low REAL, close REAL,
                    PRIMARY KEY (strategy, ticker, ohlc_date)
                );

                CREATE TABLE IF NOT EXISTS daily_snapshot (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy TEXT NOT NULL,
                    snap_date TEXT NOT NULL,
                    account_value REAL,
                    deployed REAL,
                    free REAL,
                    n_red INTEGER,
                    n_green INTEGER,
                    n_blocked INTEGER
                );
                CREATE INDEX IF NOT EXISTS ix_snap ON daily_snapshot(strategy, snap_date);
                """
            )
            self.conn.commit()
        finally:
            cur.close()

    # ---- scan_results --------------------------------------------------- #
    def save_scan(self, strategy: str, candidates: list, scan_date: Optional[str] = None,
                  scan_mode: str = "SMALLCAP") -> int:
        if not candidates:
            return 0
        now = datetime.now()
        scan_date = scan_date or now.strftime("%Y-%m-%d")
        ts = now.isoformat()
        ranked = sorted(candidates, key=lambda c: c.get("score", 0), reverse=True)
        rows = [
            (strategy, scan_date, ts, scan_mode, i,
             c.get("ticker"), c.get("exchange"), c.get("price"), c.get("score"),
             c.get("signal"), c.get("reason"), json.dumps(c.get("extra", {})))
            for i, c in enumerate(ranked, start=1)
        ]
        cur = self.conn.cursor()
        try:
            cur.executemany(
                """INSERT INTO scan_results
                   (strategy, scan_date, timestamp, scan_mode, rank,
                    ticker, exchange, price, score, signal, reason, extra)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                rows,
            )
            self.conn.commit()
            return len(rows)
        finally:
            cur.close()

    def latest_scan_date(self, strategy: str) -> Optional[str]:
        cur = self.conn.cursor()
        try:
            row = cur.execute(
                "SELECT MAX(scan_date) AS d FROM scan_results WHERE strategy = ?", (strategy,)
            ).fetchone()
            return row["d"] if row and row["d"] else None
        finally:
            cur.close()

    def get_scan(self, strategy: str, scan_date: Optional[str] = None,
                 limit: Optional[int] = None) -> list:
        scan_date = scan_date or self.latest_scan_date(strategy)
        if not scan_date:
            return []
        q = "SELECT * FROM scan_results WHERE strategy = ? AND scan_date = ? ORDER BY rank ASC"
        params: list = [strategy, scan_date]
        if limit:
            q += " LIMIT ?"
            params.append(limit)
        cur = self.conn.cursor()
        try:
            return [dict(r) for r in cur.execute(q, params).fetchall()]
        finally:
            cur.close()

    # ---- fills -------------------------------------------------------- #
    def record_fill(self, strategy: str, ticker: str, exchange: str, side: str,
                    qty: int, price: float, reason: str, orders_enabled: bool,
                    order_value: Optional[float] = None, qty_after: Optional[int] = None,
                    realised_pnl: Optional[float] = None,
                    fee_estimate: Optional[float] = None) -> int:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """INSERT INTO fills
                   (strategy, timestamp, ticker, exchange, side, qty, price, reason, orders_enabled,
                    order_value, qty_after, realised_pnl, fee_estimate)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (strategy, datetime.now().isoformat(), ticker, exchange, side.upper(),
                 int(qty), float(price), reason, 1 if orders_enabled else 0,
                 order_value if order_value is not None else round(int(qty) * float(price), 2),
                 qty_after, realised_pnl, fee_estimate),
            )
            self.conn.commit()
            return cur.lastrowid
        finally:
            cur.close()

    def get_fills(self, strategy: str, since: Optional[str] = None) -> list:
        q = "SELECT * FROM fills WHERE strategy = ?"
        params: list = [strategy]
        if since:
            q += " AND timestamp >= ?"
            params.append(since)
        q += " ORDER BY timestamp ASC"
        cur = self.conn.cursor()
        try:
            return [dict(r) for r in cur.execute(q, params).fetchall()]
        finally:
            cur.close()

    # ---- positions ------------------------------------------------- #
    def upsert_position(self, strategy: str, ticker: str, exchange: str, qty: int,
                        avg_entry: float, tranches: int, entry_cross_date: str,
                        opened_at: str, first_red_date: Optional[str] = None) -> None:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """INSERT INTO positions
                   (strategy, ticker, exchange, qty, avg_entry, tranches,
                    entry_cross_date, opened_at, first_red_date, status, closed_at)
                   VALUES (?,?,?,?,?,?,?,?,?, 'OPEN', NULL)
                   ON CONFLICT(strategy, ticker) DO UPDATE SET
                     exchange=excluded.exchange, qty=excluded.qty, avg_entry=excluded.avg_entry,
                     tranches=excluded.tranches, entry_cross_date=excluded.entry_cross_date,
                     first_red_date=COALESCE(positions.first_red_date, excluded.first_red_date),
                     status='OPEN', closed_at=NULL""",
                (strategy, ticker, exchange, int(qty), float(avg_entry), int(tranches),
                 entry_cross_date, opened_at, first_red_date),
            )
            self.conn.commit()
        finally:
            cur.close()

    def get_position(self, strategy: str, ticker: str) -> Optional[dict]:
        cur = self.conn.cursor()
        try:
            row = cur.execute(
                "SELECT * FROM positions WHERE strategy = ? AND ticker = ?", (strategy, ticker)
            ).fetchone()
            return dict(row) if row else None
        finally:
            cur.close()

    def open_positions(self, strategy: str) -> list:
        cur = self.conn.cursor()
        try:
            return [
                dict(r) for r in cur.execute(
                    "SELECT * FROM positions WHERE strategy = ? AND status = 'OPEN' ORDER BY ticker",
                    (strategy,),
                ).fetchall()
            ]
        finally:
            cur.close()

    def close_position(self, strategy: str, ticker: str, closed_at: str) -> None:
        cur = self.conn.cursor()
        try:
            cur.execute(
                "UPDATE positions SET status='CLOSED', closed_at=? WHERE strategy=? AND ticker=?",
                (closed_at, strategy, ticker),
            )
            self.conn.commit()
        finally:
            cur.close()

    # per-cycle metric refresh: rope, drawdown, day counters, stranded flag.
    # Kept separate from upsert_position (which owns entry/qty/tranche identity).
    _METRIC_COLS = frozenset({
        "high_water_mark", "trailing_floor", "profit_pct", "mae_pct",
        "exit_drawdown_pct", "days_held", "days_red", "days_green", "stranded",
    })

    def update_position_metrics(self, strategy: str, ticker: str, **fields) -> None:
        cols = {k: v for k, v in fields.items() if k in self._METRIC_COLS}
        if not cols:
            return
        if "stranded" in cols:
            cols["stranded"] = 1 if cols["stranded"] else 0
        sets = ", ".join(f"{k}=?" for k in cols)
        cur = self.conn.cursor()
        try:
            cur.execute(
                f"UPDATE positions SET {sets} WHERE strategy=? AND ticker=?",
                (*cols.values(), strategy, ticker),
            )
            self.conn.commit()
        finally:
            cur.close()

    # ---- position_ohlc (captured live; feeds the day-14 realistic replay) --- #
    def record_ohlc(self, strategy: str, ticker: str, ohlc_date: str,
                    o: float, h: float, l: float, c: float) -> None:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """INSERT INTO position_ohlc (strategy, ticker, ohlc_date, open, high, low, close)
                   VALUES (?,?,?,?,?,?,?)
                   ON CONFLICT(strategy, ticker, ohlc_date) DO UPDATE SET
                     open=excluded.open, high=excluded.high, low=excluded.low, close=excluded.close""",
                (strategy, ticker, ohlc_date, o, h, l, c),
            )
            self.conn.commit()
        finally:
            cur.close()

    def get_ohlc(self, strategy: str, ticker: str) -> list:
        cur = self.conn.cursor()
        try:
            return [
                dict(r) for r in cur.execute(
                    "SELECT * FROM position_ohlc WHERE strategy=? AND ticker=? ORDER BY ohlc_date ASC",
                    (strategy, ticker),
                ).fetchall()
            ]
        finally:
            cur.close()

    # ---- daily snapshot ------------------------------------------ #
    def save_snapshot(self, strategy: str, snap_date: str, account_value: float,
                      deployed: float, free: float, n_red: int, n_green: int, n_blocked: int) -> None:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """INSERT INTO daily_snapshot
                   (strategy, snap_date, account_value, deployed, free, n_red, n_green, n_blocked)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (strategy, snap_date, account_value, deployed, free, n_red, n_green, n_blocked),
            )
            self.conn.commit()
        finally:
            cur.close()

    def get_snapshots(self, strategy: str) -> list:
        cur = self.conn.cursor()
        try:
            return [
                dict(r) for r in cur.execute(
                    "SELECT * FROM daily_snapshot WHERE strategy = ? ORDER BY snap_date ASC",
                    (strategy,),
                ).fetchall()
            ]
        finally:
            cur.close()

    def close(self):
        self.conn.close()
