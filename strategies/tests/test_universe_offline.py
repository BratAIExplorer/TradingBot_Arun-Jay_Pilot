"""
TDD tests for the fetch seam in strategies.small_cap_universe.SmallCapScanner.

Passing `fetch=<stub>` makes the whole scan run offline and proves the scan no
longer delegates to the broken scanner_engine.detect_macd_crossover.

Run:  python -m pytest strategies/tests/test_universe_offline.py -q
"""
import pandas as pd

from strategies.small_cap_universe import SmallCapScanner


def _candles(closes):
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=len(closes))
    c = [float(x) for x in closes]
    return pd.DataFrame(
        {"Close": c, "High": [x * 1.01 for x in c], "Low": [x * 0.99 for x in c]},
        index=idx,
    )


# a long flat base then a sawtooth rally: fresh bullish MACD cross, price above
# both MAs, RSI still in the healthy band -> confluence score clears 60
_RALLY = [100] * 35 + [round(100 + 4 * i - (3 if i % 2 else 0), 2) for i in range(1, 20)]


def test_scan_market_offline_returns_the_candidate_and_no_network():
    frames = {"AAA.NS": _candles(_RALLY), "BBB.NS": _candles([100] * 54)}  # BBB flat -> no cross
    scanner = SmallCapScanner(tickers=list(frames), fetch=frames.get)
    results = scanner.scan_market(mode="SMALLCAP")
    assert [r["ticker"] for r in results] == ["AAA.NS"]
    assert results[0]["macd_cross_date"] is not None
    assert results[0]["days_ago"] >= 0


def test_dryrun_scan_accepts_an_injected_offline_scanner():
    from strategies.small_cap_dryrun import SmallCapDryRun
    from strategies.framework.config import StrategyConfig, BudgetConfig, RulesConfig

    scanner = SmallCapScanner(tickers=["AAA.NS"], fetch={"AAA.NS": _candles(_RALLY)}.get)
    cfg = StrategyConfig(
        name="small_cap_dryrun", enabled=True,
        budget=BudgetConfig(per_stock_amount=5000, total_budget=25000,
                            max_names_cap=5, pct_of_account_cap=2.0, max_names=5),
        rules=RulesConfig(), replay_stop_levels_pct=[5, 8, 10], universe="starter",
    )
    cands = SmallCapDryRun(cfg).scan(scanner=scanner)
    assert len(cands) == 1
    assert cands[0].ticker == "AAA.NS"
