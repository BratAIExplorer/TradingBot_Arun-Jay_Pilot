"""
Strategy #1 — Small-Cap Dry-Run (no stop-loss, on purpose).

This module currently holds the PURE SIGNAL RULES (offline, testable). The
Strategy class that wires them to scan/decide is added next, once these pass.

Rules (all thresholds come from config at call sites, defaults shown here):
  - entry trend filter : CMP > 200 EMA AND 50 EMA > 200 EMA + fresh MACD cross
                         (fundamentals gate is applied by the caller, not here)
  - exit               : trailing 2% profit rope, scale out in 2 halves; never
                         sell a half below entry +2% net (the +2% floor)
  - stop-loss          : none (hard_stop_pct knob exists, default OFF)

`bearish_rsi_divergence` and `swing_break_exit` below are unused by this
strategy now — kept for a possible future one.

RSI uses the same definition as scanner_engine.get_rsi (Wilder-style rolling
mean of gains/losses) so numbers match the rest of the bot.
"""
from __future__ import annotations

import os
import sys
from typing import Optional, Tuple

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scanner_engine import MACDScanner  # noqa: E402  (reused: MACD + crossover + RSI math)

from strategies.framework.base import Action, Position  # noqa: E402
from strategies.framework.costs import net_floor_price  # noqa: E402


def _not_after(cross_date: Optional[str], ref_date: str) -> bool:
    """True when cross_date is missing or not strictly later than ref_date.
    Both are the '%d-%b-%Y' strings fresh_macd_cross emits; parse leniently."""
    if not cross_date:
        return True
    try:
        return pd.to_datetime(cross_date) <= pd.to_datetime(ref_date)
    except (ValueError, TypeError):
        return False


def rsi_series(close: pd.Series, period: int = 14) -> pd.Series:
    """Full RSI series (same formula as scanner_engine.get_rsi, which returns only the last value)."""
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def above_ma(close: pd.Series, period: int = 50) -> bool:
    """True only if there are enough bars AND the last close is strictly above the MA."""
    if len(close) < period:
        return False
    return bool(close.iloc[-1] > close.tail(period).mean())


def uptrend_200(close: pd.Series) -> bool:
    """
    Primary trend filter: CMP > 200 EMA AND 50 EMA > 200 EMA. Stronger than a
    bare close > 50-SMA — needs the medium trend above the long trend too.
    EMAs are defined on <200 bars (just biased); require 50 bars as a floor.
    """
    if len(close) < 50:
        return False
    ema50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
    ema200 = close.ewm(span=200, adjust=False).mean().iloc[-1]
    return bool(close.iloc[-1] > ema200 and ema50 > ema200)


def bearish_rsi_divergence(close: pd.Series, lookback: int = 10, rsi_period: int = 14) -> bool:
    """
    True when today is a new `lookback`-bar closing high but today's RSI is below
    the best RSI of the prior `lookback-1` bars (momentum not confirming price).
    """
    if len(close) < rsi_period + lookback:
        return False

    window = close.iloc[-lookback:]
    price_new_high = close.iloc[-1] >= window.max()
    if not price_new_high:
        return False

    rsi = rsi_series(close, rsi_period)
    rsi_now = rsi.iloc[-1]
    rsi_prior_max = rsi.iloc[-lookback:-1].max()
    if pd.isna(rsi_now) or pd.isna(rsi_prior_max):
        return False
    return bool(rsi_now < rsi_prior_max)


def _latest_swing_low(low: pd.Series, fractal_bars: int) -> float | None:
    """
    Most recent confirmed swing low: a bar whose Low is strictly lower than the
    `half` bars on each side (half = fractal_bars // 2). Needs `half` bars after
    it to be confirmed, so the newest candidate index is len-1-half.
    """
    half = fractal_bars // 2
    if len(low) < 2 * half + 1:
        return None
    for i in range(len(low) - 1 - half, half - 1, -1):
        pivot = low.iloc[i]
        left = low.iloc[i - half:i]
        right = low.iloc[i + 1:i + 1 + half]
        if (pivot < left).all() and (pivot < right).all():
            return float(pivot)
    return None


def swing_break_exit(df: pd.DataFrame, fractal_bars: int = 5, ma_period: int = 50) -> bool:
    """
    True when the last 2 closes are BOTH below the most recent swing low AND the
    last close is below the `ma_period` moving average. df needs Close + Low.
    """
    swing_low = _latest_swing_low(df["Low"], fractal_bars)
    if swing_low is None:
        return False

    last2 = df["Close"].iloc[-2:]
    both_below = bool((last2 < swing_low).all())

    close = df["Close"]
    if len(close) < 2:
        return False
    # partial MA when fewer than ma_period bars (synthetic/short frames); real
    # dry-run data always has 200+ bars so this only bites in tests.
    below_ma = bool(close.iloc[-1] < close.tail(ma_period).mean())

    return both_below and below_ma


_calc = MACDScanner()  # stateless helper: only its calculate_macd (plain EMA math) is reused


def fresh_macd_cross(df: pd.DataFrame, within_bars: int = 30) -> Tuple[bool, Optional[str]]:
    """
    (is_fresh, cross_date_str) for the most recent BULLISH MACD crossover in the
    last `within_bars` bars: MACD line moves from at-or-below the signal line to
    above it. Own implementation — scanner_engine.detect_macd_crossover calls
    `.tail()` on a DatetimeIndex (no such method) and silently returns nothing.
    MACD/signal values still come from _calc.calculate_macd so the math matches.
    """
    macd_line, signal_line, _ = _calc.calculate_macd(df["Close"])
    if macd_line is None:
        return False, None
    # within_bars + 1 values so `within_bars` bar-to-bar transitions are visible
    # (a cross printed on the very last bar needs the prior bar to compare against)
    diff = (macd_line - signal_line).tail(within_bars + 1)
    crossed = (diff.shift(1) <= 0) & (diff > 0)
    if not crossed.any():
        return False, None
    idx = crossed[crossed].index[-1]
    return True, idx.strftime("%d-%b-%Y") if hasattr(idx, "strftime") else str(idx)


def _frozen_lower_circuit(candles: pd.DataFrame, band_pct: float) -> bool:
    """
    True when today's whole range sits locked at/below (prev close - band_pct%)
    — a lower circuit with no bid, so any 'sell at the close' is a fiction.
    Needs >= 2 rows; a synthetic 1-bar frame is treated as not-frozen.
    """
    if len(candles) < 2 or band_pct <= 0:
        return False
    prev_close = float(candles["Close"].iloc[-2])
    hi = float(candles["High"].iloc[-1])
    lo = float(candles["Low"].iloc[-1])
    limit = prev_close * (1 - band_pct / 100.0)
    return hi <= limit * (1 + 1e-6) and (hi - lo) <= prev_close * 1e-4


def _rope_action(cfg_exit, position: Position, close: float, cfg_costs) -> Action:
    """
    Trailing profit rope with a 2-tranche scale-out and a +N% net-of-cost floor.

    Pure. `close` is today's close; `position` carries the persisted rope state
    (high_water_mark, exit_tranches_remaining, locked_half2_price). The runner
    ratchets and stores those between cycles — here we only pick today's Action.

    The floor is the price at which the tranche's post-cost proceeds clear
    entry +min_profit_floor_pct% after `cfg_costs` (both legs). With a zero
    CostsConfig this is exactly entry * (1 + floor_pct/100).
    """
    entry = position.avg_entry
    hwm = max(position.high_water_mark or entry, close)          # ratchet on the close
    floor = net_floor_price(position.qty, entry, cfg_exit.min_profit_floor_pct, cfg_costs)

    if cfg_exit.hard_stop_pct is not None:
        stop = entry * (1 - cfg_exit.hard_stop_pct / 100.0)
        if close <= stop:
            return Action("SCALE_OUT", f"hard stop hit at {stop:.2f}", fraction=1.0)

    rope = hwm * (1 - cfg_exit.trail_giveback_pct / 100.0)
    if rope < floor:
        return Action("HOLD", f"rope inactive — {rope:.2f} is below the "
                              f"+{cfg_exit.min_profit_floor_pct:g}% net floor {floor:.2f}")

    if position.exit_tranches_remaining >= 2:
        if close <= rope:
            return Action("SCALE_OUT",
                          f"price {close:.2f} hit the rope {rope:.2f} — sell first half",
                          fraction=0.5)
        return Action("HOLD", f"above the rope {rope:.2f}")

    trigger2 = position.locked_half2_price
    if trigger2 is None:
        trigger2 = rope * (1 - cfg_exit.scale_out_step_pct / 100.0)
    if trigger2 < floor and cfg_exit.never_sell_at_loss and cfg_exit.strand_final_half:
        return Action("HOLD", f"STRANDED HALF — second trigger {trigger2:.2f} is below the "
                              f"net floor {floor:.2f}; manual sell?")
    if close <= trigger2:
        return Action("SCALE_OUT",
                      f"price {close:.2f} hit the second trigger {trigger2:.2f} — sell the rest",
                      fraction=1.0)
    return Action("HOLD", f"above the second trigger {trigger2:.2f}")


def advance_rope(position: Position, action: Action, close: float, low: float, cfg_exit) -> dict:
    """
    Next-state contract for the trailing rope. Pure. The runner calls this once
    per cycle *after* decide(), and persists the returned fields onto the
    Position row — this is the only place rope state transitions.

      high_water_mark : ratchets up on a higher close, never down
      trailing_floor  : the rope level for that HWM
      mae_pct         : worst (day-low vs entry) drawdown ever seen, in %
      SCALE_OUT 0.5   : exit_tranches_remaining -> 1, locked_half2_price set
      SCALE_OUT 1.0   : exit_tranches_remaining -> 0
    """
    entry = position.avg_entry
    hwm = max(position.high_water_mark or entry, close)
    rope = hwm * (1 - cfg_exit.trail_giveback_pct / 100.0)

    dd_pct = round((low / entry - 1.0) * 100.0, 4)
    prior_mae = position.mae_pct if position.mae_pct is not None else 0.0

    upd = {"high_water_mark": hwm, "trailing_floor": rope, "mae_pct": min(prior_mae, dd_pct)}
    if action.kind == "SCALE_OUT" and action.fraction == 0.5:
        upd["exit_tranches_remaining"] = 1
        upd["locked_half2_price"] = rope * (1 - cfg_exit.scale_out_step_pct / 100.0)
    elif action.kind == "SCALE_OUT" and action.fraction == 1.0:
        upd["exit_tranches_remaining"] = 0
    return upd


class SmallCapDryRun:
    """Strategy #1. Pure signal logic; sizing/persistence/orders live in the framework."""

    name = "small_cap_dryrun"

    def __init__(self, config):
        self.cfg = config

    def describe(self) -> str:
        r, e = self.cfg.rules, self.cfg.exit
        return (
            "Small-Cap Dry-Run — a deliberate no-stop-loss experiment.\n\n"
            "BUY one full position when price is above its 200-day EMA, the 50-day "
            "EMA is above the 200-day EMA, and a fresh bullish MACD crossover has "
            "printed — and the stock clears the fundamentals gate. No adds.\n"
            f"EXIT by a trailing profit rope: the rope sits {e.trail_giveback_pct:g}% below the "
            "highest close seen since entry and only ratchets up. When price closes at or "
            "below the rope, sell half; sell the rest when price closes another "
            f"{e.scale_out_step_pct:g}% lower.\n"
            f"A half is NEVER sold for less than entry +{e.min_profit_floor_pct:g}% net of costs. "
            "If the rope is below that floor, nothing sells — the position is simply held "
            "('rope inactive'). A stranded final half is flagged for a manual sell.\n"
            "There is NO stop-loss, on purpose: this run exists to measure whether a "
            "stop-loss would have helped or just locked in losses that later recovered.\n"
            f"Budget: Rs {self.cfg.budget.per_stock_amount:g} per stock, one position "
            f"per name, up to {self.cfg.budget.max_names} stocks, hard-capped at "
            f"{self.cfg.budget.pct_of_account_cap:g}% of the account."
        )

    def scan(self, scanner=None):
        """Ranked candidates from the small-cap universe. Hits the network unless
        a pre-built scanner (with a fetch stub) is passed — that path is offline."""
        from strategies.small_cap_universe import SmallCapScanner
        from strategies.framework.base import Candidate

        scanner = scanner or SmallCapScanner()
        out = []
        for r in scanner.scan_market(mode="SMALLCAP"):
            out.append(
                Candidate(
                    ticker=r["ticker"],
                    exchange="NSE" if r["ticker"].endswith(".NS") else "BSE",
                    price=r["price"],
                    score=r["confluence_score"],
                    signal=r["signal"],
                    reason=(f"MACD cross {r['macd_cross_date']} ({r['days_ago']}d ago); "
                            f">20MA={r['above_20ma']} >50MA={r['above_50ma']} RSI={r['rsi']}"),
                    extra={k: r[k] for k in ("macd_cross_date", "days_ago", "above_20ma",
                                             "above_50ma", "ma_20", "ma_50", "rsi")},
                )
            )
        return out

    def decide(self, ticker: str, candles: pd.DataFrame, position: Optional[Position],
               *, avg_daily_value_cr: Optional[float] = None, fundamentals=None,
               last_exit_cross_date: Optional[str] = None) -> Action:
        """
        The keyword-only screens are enforced only when the runner supplies them
        (a value of None = "not my job here, the caller checks"):
          avg_daily_value_cr   -> liquidity gate  (cfg.liquidity)
          fundamentals         -> fundamentals gate (cfg.fundamentals, via passes_gate)
          last_exit_cross_date -> re-entry cooldown: the fresh cross must post-date it
        """
        r = self.cfg.rules
        close = candles["Close"]

        if position is None:
            en = self.cfg.entry
            fresh, cross_date = fresh_macd_cross(candles, within_bars=en.fresh_cross_max_age_days)
            trend_ok = uptrend_200(close) if en.require_200ema_uptrend else above_ma(close, r.ma_period)
            if not (trend_ok and fresh):
                return Action("HOLD", "no entry signal")

            lq = self.cfg.liquidity
            if lq.enabled and avg_daily_value_cr is not None and avg_daily_value_cr < lq.min_avg_daily_value_cr:
                return Action("HOLD", f"skipped — traded only Rs {avg_daily_value_cr:.2f}cr/day, "
                                      f"below the Rs {lq.min_avg_daily_value_cr:g}cr liquidity floor")

            if fundamentals is not None:
                from strategies.framework.fundamentals import passes_gate
                ok, why = passes_gate(fundamentals, self.cfg.fundamentals,
                                      self.cfg.min_market_cap_cr, self.cfg.max_market_cap_cr)
                if not ok:
                    return Action("HOLD", f"failed health check — {why}")

            if last_exit_cross_date and _not_after(cross_date, last_exit_cross_date):
                return Action("HOLD", f"waiting for a fresh signal after the last exit "
                                      f"({cross_date} is not newer than {last_exit_cross_date})")

            return Action("BUY", f"trend ok + fresh MACD cross {cross_date}")

        # managing an open position — the trailing rope, no adds, no stop-loss
        if _frozen_lower_circuit(candles, r.circuit_band_pct):
            return Action("HOLD", "can't sell — the stock is frozen at its lower price limit today")
        return _rope_action(self.cfg.exit, position, float(close.iloc[-1]), self.cfg.costs)
