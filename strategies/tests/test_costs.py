"""
Tests for framework/costs.py — the Zerodha delivery cost model and the
net-of-cost floor price used by the trailing rope.

Run:  python -m pytest strategies/tests/test_costs.py -q
"""
from strategies.framework.config import CostsConfig
from strategies.framework.costs import net_buy_cost, net_sell_proceeds, net_floor_price

ZERO = CostsConfig()
REAL = CostsConfig(stt_pct=0.1, entry_slippage_bps=40, exit_slippage_bps_thin=300, brokerage_flat=0)


def test_zero_config_is_pure_gross():
    assert net_buy_cost(100, 10, ZERO) == 1000
    assert net_sell_proceeds(100, 10, ZERO) == 1000
    assert abs(net_floor_price(10, 100.0, 2.0, ZERO) - 102.0) < 1e-9


def test_buy_costs_more_than_quoted():
    # 40 bps slippage + 0.1% STT on 1000 -> ~1005.4
    c = net_buy_cost(100, 10, REAL)
    assert 1005 < c < 1006


def test_sell_returns_less_than_quoted():
    # 300 bps slippage + 0.1% STT -> ~1000 * 0.97 * 0.999
    p = net_sell_proceeds(100, 10, REAL)
    assert 966 < p < 970


def test_net_floor_price_is_well_above_the_gross_floor():
    # with real charges the true break-even +2% sell price is > 105, not 102
    fp = net_floor_price(10, 100.0, 2.0, REAL)
    assert fp > 105.0
    # and selling exactly at fp yields >= entry-cost * 1.02
    proceeds = net_sell_proceeds(fp, 10, REAL)
    target = net_buy_cost(100.0, 10, REAL) * 1.02
    assert abs(proceeds - target) < 1e-6


def test_floor_scales_with_the_floor_pct():
    lo = net_floor_price(10, 100.0, 2.0, REAL)
    hi = net_floor_price(10, 100.0, 5.0, REAL)
    assert hi > lo
