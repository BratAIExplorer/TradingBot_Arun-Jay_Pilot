"""
Pure cost model for Zerodha delivery (CNC) fills.

One model runs on every simulated fill, both legs. The net-of-cost +N% floor in
small_cap_dryrun._rope_action is expressed as a *price* through net_floor_price()
so the signal layer needs no per-fill loop.

With a zero CostsConfig (the default) every function here reduces to the plain
gross number, so an unconfigured strategy behaves exactly as before.
"""
from __future__ import annotations


def net_buy_cost(price: float, qty: int, c) -> float:
    """Rupees actually leaving the account to buy `qty` at quoted `price`."""
    gross = price * qty
    after_slip = gross * (1 + c.entry_slippage_bps / 10_000.0)   # fills worse (higher)
    stt = after_slip * c.stt_pct / 100.0
    return after_slip + stt + c.brokerage_flat


def net_sell_proceeds(price: float, qty: int, c, thin: bool = True) -> float:
    """Rupees actually received for selling `qty` at quoted `price`."""
    slip_bps = c.exit_slippage_bps_thin if thin else 0.0
    gross = price * qty
    after_slip = gross * (1 - slip_bps / 10_000.0)               # fills worse (lower)
    stt = after_slip * c.stt_pct / 100.0
    return after_slip - stt - c.brokerage_flat


def net_floor_price(qty: int, avg_entry: float, floor_pct: float, c, thin: bool = True) -> float:
    """
    The quoted price at which selling `qty` returns net proceeds equal to the
    net cost of the position grown by `floor_pct` — i.e. "up floor_pct% after all
    charges, both ways". A tranche must not sell below this.

    net_sell_proceeds(p) is linear in p:
        p * qty * (1 - slip) * (1 - stt) - brokerage_flat
    so invert it directly.
    """
    target = net_buy_cost(avg_entry, qty, c) * (1 + floor_pct / 100.0)
    slip = (c.exit_slippage_bps_thin if thin else 0.0) / 10_000.0
    stt = c.stt_pct / 100.0
    denom = qty * (1 - slip) * (1 - stt)
    return (target + c.brokerage_flat) / denom


if __name__ == "__main__":
    from strategies.framework.config import CostsConfig

    zero = CostsConfig()
    assert net_buy_cost(100, 10, zero) == 1000
    assert net_sell_proceeds(100, 10, zero) == 1000
    assert abs(net_floor_price(10, 100.0, 2.0, zero) - 102.0) < 1e-9  # reduces to gross

    real = CostsConfig(stt_pct=0.1, entry_slippage_bps=40, exit_slippage_bps_thin=300)
    fp = net_floor_price(10, 100.0, 2.0, real)
    assert fp > 105.0, fp   # costs push the break-even sell price well above the gross 102
    print("costs self-check ok; realistic +2% floor price =", round(fp, 2))
