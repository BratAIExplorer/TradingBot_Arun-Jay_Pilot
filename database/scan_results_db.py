"""
Scan Results Database - Daily history of scored candidates
═══════════════════════════════════════════════════════════════════════════════

WHAT THIS IS (plain terms):
The scanner scores stocks every day but forgets them the moment it finishes.
This file gives it a memory. Every scan writes its ranked list here so you can
look back later and ask "what did the scanner like on 3rd Sept, and what happened
to those stocks?".

This is a SEPARATE database file (database/scan_results.db). It does NOT touch
trades.db. Nothing here places orders. It only records what was scored.

Mirrors the style of database/order_attempts_db.py.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional


class ScanResultsDatabase:
    """Stores the scanner's ranked candidate list, one batch per scan."""

    def __init__(self, db_path: str = "database/scan_results.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        print(f"✅ Scan results DB ready: {db_path}")

    def _create_tables(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scan_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_date TEXT NOT NULL,          -- YYYY-MM-DD (grouping key)
                    timestamp TEXT NOT NULL,          -- full ISO time of the scan
                    strategy TEXT NOT NULL DEFAULT 'small_cap_dryrun',
                    scan_mode TEXT,                   -- FULL / QUICK / SMALLCAP
                    rank INTEGER,                     -- 1 = highest score in this batch

                    ticker TEXT NOT NULL,
                    company TEXT,
                    price REAL,
                    signal TEXT,                      -- STRONG BUY / BUY / WATCH
                    confluence_score INTEGER,
                    macd_cross_date TEXT,
                    days_ago INTEGER,
                    above_20ma TEXT,
                    above_50ma TEXT,
                    ma_20 REAL,
                    ma_50 REAL,
                    rsi REAL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scan_date ON scan_results(scan_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_strategy_date ON scan_results(strategy, scan_date)")
            self.conn.commit()
        finally:
            cursor.close()

    @staticmethod
    def _num(value):
        """'N/A' and blanks -> None, so numeric columns stay clean."""
        try:
            if value in (None, "", "N/A"):
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def log_scan_results(self,
                         results: List[Dict],
                         scan_date: Optional[str] = None,
                         strategy: str = "small_cap_dryrun",
                         scan_mode: str = "SMALLCAP") -> int:
        """
        Write one scan's worth of scored candidates.

        results: the list of dicts returned by MACDScanner.scan_market()
        Returns: number of rows written.
        Candidates are ranked by confluence_score (highest = rank 1).
        """
        if not results:
            return 0

        now = datetime.now()
        scan_date = scan_date or now.strftime("%Y-%m-%d")
        ts = now.isoformat()

        ranked = sorted(results, key=lambda r: r.get("confluence_score", 0), reverse=True)

        rows = [
            (
                scan_date, ts, strategy, scan_mode, i,
                r.get("ticker"), r.get("company"), self._num(r.get("price")),
                r.get("signal"), r.get("confluence_score"), r.get("macd_cross_date"),
                r.get("days_ago"), r.get("above_20ma"), r.get("above_50ma"),
                self._num(r.get("ma_20")), self._num(r.get("ma_50")), self._num(r.get("rsi")),
            )
            for i, r in enumerate(ranked, start=1)
        ]

        cursor = self.conn.cursor()
        try:
            cursor.executemany("""
                INSERT INTO scan_results (
                    scan_date, timestamp, strategy, scan_mode, rank,
                    ticker, company, price, signal, confluence_score, macd_cross_date,
                    days_ago, above_20ma, above_50ma, ma_20, ma_50, rsi
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)
            self.conn.commit()
            print(f"✅ Logged {len(rows)} scan candidates for {scan_date} ({strategy})")
            return len(rows)
        finally:
            cursor.close()

    def get_latest_scan_date(self, strategy: Optional[str] = None) -> Optional[str]:
        q = "SELECT MAX(scan_date) AS d FROM scan_results"
        params: list = []
        if strategy:
            q += " WHERE strategy = ?"
            params.append(strategy)
        cursor = self.conn.cursor()
        try:
            row = cursor.execute(q, params).fetchone()
            return row["d"] if row and row["d"] else None
        finally:
            cursor.close()

    def get_scan_results(self,
                         scan_date: Optional[str] = None,
                         strategy: Optional[str] = None,
                         limit: Optional[int] = None) -> List[Dict]:
        """
        Read back a day's candidates, already ordered by rank.
        scan_date defaults to the most recent scan on file.
        limit -> e.g. 10 for "top 10".
        """
        scan_date = scan_date or self.get_latest_scan_date(strategy)
        if not scan_date:
            return []

        q = "SELECT * FROM scan_results WHERE scan_date = ?"
        params: list = [scan_date]
        if strategy:
            q += " AND strategy = ?"
            params.append(strategy)
        q += " ORDER BY rank ASC"
        if limit:
            q += " LIMIT ?"
            params.append(limit)

        cursor = self.conn.cursor()
        try:
            return [dict(r) for r in cursor.execute(q, params).fetchall()]
        finally:
            cursor.close()

    def close(self):
        self.conn.close()


# Module-level singleton, same pattern as database/trades_db.py
scan_db = ScanResultsDatabase()


if __name__ == "__main__":
    # Self-check: write a fake batch, read it back, verify ranking + top-N.
    _test_path = "database/_test_scan_results.db"
    if os.path.exists(_test_path):
        os.remove(_test_path)  # start clean even if a prior run crashed
    test = ScanResultsDatabase(_test_path)
    sample = [
        {"ticker": "AAA.NS", "company": "Alpha", "price": 100, "signal": "BUY",
         "confluence_score": 65, "macd_cross_date": "01-Sep-2026", "days_ago": 3,
         "above_20ma": "Yes", "above_50ma": "No", "ma_20": 98, "ma_50": 95, "rsi": 55},
        {"ticker": "BBB.NS", "company": "Bravo", "price": 200, "signal": "STRONG BUY",
         "confluence_score": 82, "macd_cross_date": "02-Sep-2026", "days_ago": 1,
         "above_20ma": "Yes", "above_50ma": "Yes", "ma_20": 190, "ma_50": 180, "rsi": "N/A"},
        {"ticker": "CCC.NS", "company": "Charlie", "price": 50, "signal": "BUY",
         "confluence_score": 70, "macd_cross_date": "30-Aug-2026", "days_ago": 6,
         "above_20ma": "No", "above_50ma": "Yes", "ma_20": 51, "ma_50": 48, "rsi": 61},
    ]
    n = test.log_scan_results(sample, scan_date="2026-09-08", strategy="small_cap_dryrun")
    assert n == 3, n

    rows = test.get_scan_results(scan_date="2026-09-08", strategy="small_cap_dryrun")
    # ranked by score desc: BBB 82, CCC 70, AAA 65
    assert [r["ticker"] for r in rows] == ["BBB.NS", "CCC.NS", "AAA.NS"], rows
    assert rows[0]["rank"] == 1 and rows[0]["confluence_score"] == 82
    assert rows[0]["rsi"] is None  # BBB's 'N/A' cleaned to NULL

    top2 = test.get_scan_results(scan_date="2026-09-08", limit=2)
    assert len(top2) == 2 and top2[0]["ticker"] == "BBB.NS"
    assert test.get_latest_scan_date("small_cap_dryrun") == "2026-09-08"

    test.close()
    os.remove("database/_test_scan_results.db")
    print("✅ scan_results_db self-check passed")
