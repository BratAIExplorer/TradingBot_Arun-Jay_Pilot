"""
Shared shapes every strategy speaks in.

A Strategy is pure signal logic: it scans for candidates and, given a name's
candles and current position, returns one Action. Sizing, budget, persistence,
and order routing are the framework's job (see sizing.py / store.py / broker.py).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional, Protocol

import pandas as pd

ActionKind = Literal["BUY", "SCALE_OUT", "HOLD"]


@dataclass(frozen=True)
class Candidate:
    ticker: str
    exchange: str
    price: float
    score: int
    signal: str                       # "STRONG BUY" / "BUY" / "WATCH"
    reason: str                       # plain-English, shown on the dashboard
    extra: dict = field(default_factory=dict)   # score breakdown, macd date, rsi, MAs...


@dataclass(frozen=True)
class Position:
    ticker: str
    exchange: str
    qty: int
    avg_entry: float
    tranches: int                     # always 1 (kept for the DB column; no adds)
    entry_cross_date: str             # MACD cross date that opened it
    opened_at: str                    # ISO
    first_red_date: Optional[str] = None
    # trailing-rope exit state — persisted, never recomputed from scratch
    high_water_mark: Optional[float] = None      # highest close seen since entry
    trailing_floor: Optional[float] = None       # current rope level
    exit_tranches_remaining: int = 2             # halves left to sell on the way down
    locked_half2_price: Optional[float] = None   # trigger for the second half, once set
    stranded: bool = False                       # second half can't clear the +2% net floor
    mae_pct: Optional[float] = None              # worst drawdown seen live (cannot be backfilled)
    last_quote_date: Optional[str] = None        # date of the close that last fed the rope


@dataclass(frozen=True)
class Action:
    kind: ActionKind
    reason: str
    fraction: float = 1.0            # SCALE_OUT first half = 0.5; "sell the rest" = 1.0


class Strategy(Protocol):
    name: str

    def describe(self) -> str:
        """Plain-English rules, rendered verbatim in the dashboard 'How it works' panel."""
        ...

    def scan(self) -> list[Candidate]:
        """Today's ranked candidates (may hit the network)."""
        ...

    def decide(self, ticker: str, candles: pd.DataFrame, position: Optional[Position]) -> Action:
        """
        One decision for one name. `position` is None when the name is not held
        (considering entry) and set when it is (managing the trailing rope).
        Pure: no I/O.
        """
        ...
