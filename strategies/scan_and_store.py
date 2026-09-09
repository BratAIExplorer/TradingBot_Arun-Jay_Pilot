"""
Run the small-cap scan and keep the result — read-only, no orders, no positions.

This is the safe half of the daily loop: it proves the scan works and the top
picks land in database/strategies.db where the dashboard (and you) can review
them. Run it every trading day well before the runner exists.

    python -m strategies.scan_and_store                 # uses the curated list
    python -m strategies.scan_and_store --check-caps    # + slow ₹500-5,000cr filter

Ranking and the rank column are done inside Store.save_scan; top-5 / top-10 are
just Store.get_scan(limit=N) on read.
"""
from __future__ import annotations

import os
import sys


def scan_and_store(strategy, store, *, scanner=None) -> list:
    """Scan, persist every candidate (ranked) to `store`, return them score-desc."""
    candidates = strategy.scan(scanner=scanner)
    rows = [
        {"ticker": c.ticker, "exchange": c.exchange, "price": c.price,
         "score": c.score, "signal": c.signal, "reason": c.reason, "extra": c.extra}
        for c in candidates
    ]
    store.save_scan(strategy.name, rows)
    return sorted(rows, key=lambda r: r["score"], reverse=True)


def _default_config_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "configs", "small_cap_dryrun.json")


def _default_db_path() -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "database", "strategies.db")


def _print_table(rows: list, n: int) -> None:
    print(f"\nTop {n}:")
    print(f"  {'#':>2}  {'ticker':<14}{'score':>6}  {'signal':<11}{'price':>10}  why")
    for i, r in enumerate(rows[:n], start=1):
        print(f"  {i:>2}  {r['ticker']:<14}{r['score']:>6}  {r['signal']:<11}"
              f"{r['price']:>10}  {r['reason'][:60]}")


if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from strategies.framework.registry import load
    from strategies.framework.store import Store
    from strategies.small_cap_universe import SmallCapScanner

    cfg_path = _default_config_path()
    if not os.path.exists(cfg_path):
        sys.exit(f"no config at {cfg_path} — copy configs/small_cap_dryrun.json into place first")

    strat = load(cfg_path)
    store = Store(_default_db_path())
    store._create()

    check_caps = "--check-caps" in sys.argv
    scanner = SmallCapScanner(apply_cap_filter=check_caps)
    print(f"scanning {len(scanner.get_stock_list())} names"
          f"{' (with ₹500-5,000cr filter)' if check_caps else ''} ...")
    ranked = scan_and_store(strat, store, scanner=scanner)
    print(f"stored {len(ranked)} candidates -> {_default_db_path()}  (scan_date today)")
    _print_table(ranked, 5)
    _print_table(ranked, 10)
    store.close()
