"""Real IBKR broker — TWS API via ib_insync, socket connection to IB Gateway/TWS.

Why TWS API and not IBKR's Client Portal REST API: Project Vayu tried the Client
Portal / Flex Web Service route first and hit Malaysia-region API access restrictions
(see brokers/ibkr_alternative.md in Project Vayu) — their own documented workaround was
this exact path. Our VPS is also Malaysia-based, so this isn't a theoretical choice.

ib_insync is imported lazily (inside methods/__init__), never at module load, so this
file can be imported — and BrokerInterface Protocol conformance checked — even on a
machine that doesn't have ib_insync installed or a Gateway running. Nothing here
connects automatically; connect() is explicit.

NOT wired into kickstart.py. This is a standalone, testable class — rewiring the live
engine's order-placement path to use get_broker() is deferred until this has been
proven against a live paper account, per the handover doc's own "sequence last, run
paper-mode first" guidance.

Setup needed before this can be used for real (all human steps, not code):
  1. An IBKR account with API access confirmed enabled (Vayu's own history suggests
     this needs an explicit check — don't assume it's on by default).
  2. IB Gateway (not TWS — headless, meant for unattended bots) running and logged in,
     paper trading mode, on the same machine or network this code runs from.
  3. In Gateway: Configure > Settings > API > Enable ActiveX and Socket Clients, note
     the port (paper Gateway default 4002).
  4. pip install ib_insync
"""
from __future__ import annotations

import os
from typing import Any

# Paper-mode Gateway port by default — matches kickstart.py's own paper_trading_mode
# caution. Override via env vars once you're deliberately moving to live.
IBKR_HOST = os.environ.get("IBKR_HOST", "127.0.0.1")
IBKR_PORT = int(os.environ.get("IBKR_PORT", "4002"))  # 4002=Gateway paper, 4001=Gateway live
IBKR_CLIENT_ID = int(os.environ.get("IBKR_CLIENT_ID", "7"))
# Set IBKR_READONLY=1 where the Gateway login is read-only (VPS): skips the order queries that
# make Gateway pop a "needs write access" dialog and add ~4s to every connect. Default off.
IBKR_READONLY = os.environ.get("IBKR_READONLY", "").lower() in ("1", "true", "yes")


class IBKRBroker:
    def __init__(self, host: str = IBKR_HOST, port: int = IBKR_PORT, client_id: int = IBKR_CLIENT_ID):
        self.host = host
        self.port = port
        self.client_id = client_id
        self._ib = None

    def _require_ib_insync(self):
        try:
            from ib_insync import IB
        except ImportError as e:
            raise ImportError(
                "ib_insync is not installed — pip install ib_insync (see module docstring)"
            ) from e
        return IB

    def connect(self):
        """
        Explicit connect — nothing in this class connects automatically.

        ib_insync is asyncio-based and needs an event loop in whatever thread it runs
        in. The standalone scripts (check_ibkr_connection.py etc.) work fine because
        the main thread always has one. Called from a FastAPI request instead (as the
        dashboard's /api/ibkr/summary does), it runs in a worker thread with no event
        loop, and asyncio.get_event_loop() raises there — this creates one if missing,
        so connect() works the same regardless of which thread calls it.
        """
        import asyncio
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        IB = self._require_ib_insync()
        if self._ib is not None and self._ib.isConnected():
            return
        self._ib = IB()
        self._ib.connect(self.host, self.port, clientId=self.client_id, readonly=IBKR_READONLY)

    def disconnect(self):
        if self._ib is not None and self._ib.isConnected():
            self._ib.disconnect()

    def _ensure_connected(self):
        if self._ib is None or not self._ib.isConnected():
            self.connect()

    def get_funds(self) -> float | None:
        self._ensure_connected()
        for row in self._ib.accountSummary():
            if row.tag == "TotalCashValue" and row.currency == "USD":
                return float(row.value)
        return None

    def get_portfolio(self) -> dict:
        """
        Richer than get_positions() — uses ib.portfolio() instead of ib.positions(),
        which additionally carries live market price/value and IBKR's own unrealized/
        realized P&L per position (computed server-side, not derived here).

        Also attaches a best-effort "first purchase date" per symbol, from the
        earliest BUY execution found in today's connection's execution history. This
        is an approximation for anything bought in more than one lot over time — IBKR
        doesn't expose a single "purchase date" field on a position, only individual
        fills. Good enough for a recently-opened position, not a precise cost-basis
        record for a position built up gradually.
        """
        self._ensure_connected()
        out: dict = {}
        for item in self._ib.portfolio():
            sym = item.contract.symbol
            out[sym] = {
                "qty": item.position,
                "avg_cost": item.averageCost,
                "market_price": item.marketPrice,
                "market_value": item.marketValue,
                "unrealized_pnl": item.unrealizedPNL,
                "realized_pnl": item.realizedPNL,
                "exchange": item.contract.exchange or "SMART",
                "currency": item.contract.currency,
                "first_purchase_date": None,
            }

        try:
            fills = self._ib.reqExecutions()
            earliest: dict = {}
            for f in fills:
                sym = f.contract.symbol
                if f.execution.side != "BOT":  # BOT = bought
                    continue
                t = f.execution.time
                if sym not in earliest or t < earliest[sym]:
                    earliest[sym] = t
            for sym, t in earliest.items():
                if sym in out:
                    out[sym]["first_purchase_date"] = t.isoformat() if hasattr(t, "isoformat") else str(t)
        except Exception:
            pass  # execution history is best-effort — never let it break the portfolio view

        return out

    def get_positions(self) -> dict[Any, dict[str, Any]]:
        self._ensure_connected()
        out: dict[Any, dict[str, Any]] = {}
        for p in self._ib.positions():
            out[p.contract.symbol] = {
                "qty": p.position,
                "price": p.avgCost,
                "exchange": p.contract.exchange or "SMART",
                "currency": p.contract.currency,
            }
        return out

    def get_quote(self, symbol: str, exchange: str = "SMART", currency: str = "USD"):
        """
        Uses delayed market data (type 3) by default — real-time needs a paid IBKR
        market data subscription per exchange, which this account doesn't have. Delayed
        is free and always available, ~15-20 min behind, fine for validating the code
        path; swap to reqMarketDataType(1) once/if a live subscription is added.

        currency defaults to USD for backward compat with plain US-stock callers, but
        the same ticker can resolve to different contracts on different exchanges in
        different currencies (confirmed via lookup_symbol.py on real tickers) — always
        pass the currency you actually mean for anything non-US.
        """
        self._ensure_connected()
        from ib_insync import Stock
        self._ib.reqMarketDataType(3)  # 1=live, 2=frozen, 3=delayed, 4=delayed-frozen
        contract = Stock(symbol, exchange, currency)
        tickers = self._ib.reqTickers(contract)
        if not tickers:
            return None
        t = tickers[0]

        def _clean(v):
            return None if v != v else v  # NaN != NaN — cheapest NaN check, avoids a math import

        return {"last_price": _clean(t.last), "bid": _clean(t.bid), "ask": _clean(t.ask)}

    def place_order(self, symbol, exchange, qty, side, instrument_token=None, price=0,
                     use_amo=False, currency: str = "USD", tif: str = "DAY",
                     order_type: str = "LMT_OR_MKT", stop_price: float | None = None,
                     oca_group: str | None = None, oca_type: int = 1):
        """
        Returns an ib_insync Trade object — NOT the same shape as mStock's
        requests.Response. Callers routing through get_broker() must branch on
        market/broker type until a normalization layer exists (documented gap,
        matches the note already in brokers/interface.py).

        currency defaults to USD — pass explicitly for anything non-US, same reasoning
        as get_quote(). Getting this wrong risks the order resolving to a different
        contract than intended; confirm exchange+currency via lookup_symbol.py first.

        tif="GTC" (good-till-cancelled) for orders that need to stay resting past today
        — e.g. a profit-target sell. Default "DAY" expires at market close, same as a
        normal order.

        order_type: "LMT_OR_MKT" (default) picks Market if price=0 else Limit, same as
        before this param existed. Pass "STP" with stop_price set for a stop order
        (triggers a market sell once price crosses stop_price — used for stop-loss).

        oca_group/oca_type: link this order to others in the same "one cancels all"
        group — e.g. a profit-target sell and a stop-loss sell for the same position,
        where filling one should cancel the other. oca_type=1 = cancel remaining orders
        with no block; IBKR's other oca_type values relate to partial-fill accounting
        that doesn't apply to whole-share sells here.
        """
        self._ensure_connected()
        from ib_insync import Stock, MarketOrder, LimitOrder, StopOrder
        contract = Stock(symbol, exchange or "SMART", currency)
        side = side.upper()
        if order_type == "STP":
            order = StopOrder(side, qty, stop_price)
        else:
            order = MarketOrder(side, qty) if not price else LimitOrder(side, qty, price)
        order.tif = tif
        if oca_group:
            order.ocaGroup = oca_group
            order.ocaType = oca_type
        return self._ib.placeOrder(contract, order)

    def get_reference_high(self, symbol: str, days: int, exchange: str = "SMART", currency: str = "USD"):
        """Highest daily high over the last `days` calendar days (delayed data is fine). None if no bars."""
        self._ensure_connected()
        from ib_insync import Stock
        self._ib.reqMarketDataType(3)
        contract = Stock(symbol, exchange, currency)
        self._ib.qualifyContracts(contract)
        bars = self._ib.reqHistoricalData(contract, endDateTime="", durationStr=f"{int(days)} D",
                                          barSizeSetting="1 day", whatToShow="TRADES", useRTH=True)
        return max(b.high for b in bars) if bars else None

    def get_open_orders(self) -> dict[str, set[str]]:
        """symbol -> set of sides ('BUY'/'SELL') with a live resting order."""
        self._ensure_connected()
        out: dict[str, set[str]] = {}
        for t in self._ib.openTrades():
            out.setdefault(t.contract.symbol, set()).add(t.order.action.upper())
        return out
