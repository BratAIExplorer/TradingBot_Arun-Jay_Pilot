"""
Zerodha CNC broker for the strategy framework — LOG-ONLY until the last step.

Ported in shape from Equity_The-Final-chapter/zerodha_client.py (KiteConnect
place_order CNC market, generate_session, kite.margins() as the liveness check).
`kiteconnect` is imported lazily so the framework and its tests never need it.

Nothing here trades until BOTH:
  - the strategy config has  orders_enabled: true
  - a real Kite session is attached (api_key/secret in strategies/.env + the
    morning request-token login)

Until then place_order() returns a simulated fill priced through costs.py so the
runner, the DB and the dashboard all see realistic numbers.
"""
from __future__ import annotations

import os

from strategies.framework.costs import net_buy_cost, net_sell_proceeds


class Broker:
    def __init__(self, *, orders_enabled: bool, costs, kite=None,
                 api_key: str | None = None, api_secret: str | None = None):
        self.orders_enabled = bool(orders_enabled)
        self.costs = costs
        self.kite = kite                       # a live KiteConnect, or None
        self.api_key = api_key or os.environ.get("ZERODHA_API_KEY") or ""
        self.api_secret = api_secret or os.environ.get("ZERODHA_API_SECRET") or ""

    # --- session -------------------------------------------------------- #
    def get_login_url(self) -> str | None:
        return self.kite.login_url() if self.kite else None

    def validate_session(self) -> tuple[bool, str]:
        """Fast read-only liveness check (kite.margins()). Never raises."""
        if not self.api_key or not self.api_secret:
            return False, ("no Zerodha credentials configured — add ZERODHA_API_KEY / "
                           "ZERODHA_API_SECRET to strategies/.env (last step)")
        if not self.kite or not getattr(self.kite, "access_token", None):
            return False, "no live Kite session — do the morning request-token login"
        try:
            self.kite.margins()
            return True, "session live"
        except Exception as exc:                       # noqa: BLE001 — report, don't crash the loop
            return False, f"Kite session check failed: {exc}"

    # --- orders ------------------------------------------------------- #
    def place_order(self, ticker: str, exchange: str, side: str, qty: int, price: float) -> dict:
        """
        Returns a fill record. mode is:
          LOGGED  — orders_enabled False: simulated fill, nothing sent
          ERROR   — orders_enabled True but no live session: nothing sent
          LIVE    — real order placed (needs a Kite session)
        """
        side = side.upper()
        base = {"ticker": ticker, "exchange": exchange, "side": side, "qty": qty,
                "quoted_price": round(price, 2), "orders_enabled": self.orders_enabled}

        fill_price, fee = self._simulate(side, qty, price)
        sim = {**base, "fill_price": fill_price, "fee_estimate": fee,
               "order_value": round(fill_price * qty, 2)}

        if not self.orders_enabled:
            return {**sim, "mode": "LOGGED",
                    "reason": "orders_enabled is false — logged, not sent"}

        ok, why = self.validate_session()
        if not ok:
            return {**sim, "mode": "ERROR",
                    "reason": f"orders_enabled but no usable session — {why}"}

        order_id = self.kite.place_order(
            variety=self.kite.VARIETY_REGULAR,
            exchange=self.kite.EXCHANGE_NSE if exchange.upper() == "NSE" else exchange,
            tradingsymbol=ticker.replace(".NS", ""),
            transaction_type=(self.kite.TRANSACTION_TYPE_BUY if side == "BUY"
                              else self.kite.TRANSACTION_TYPE_SELL),
            quantity=qty,
            product=self.kite.PRODUCT_CNC,
            order_type=self.kite.ORDER_TYPE_MARKET,
        )
        return {**sim, "mode": "LIVE", "order_id": order_id,
                "reason": "market CNC order placed"}

    def _simulate(self, side: str, qty: int, price: float) -> tuple[float, float]:
        c = self.costs
        if side == "BUY":
            fill = price * (1 + c.entry_slippage_bps / 10_000.0)
            total_out = net_buy_cost(price, qty, c)
            fee = round(total_out - fill * qty, 2)
        else:
            fill = price * (1 - c.exit_slippage_bps_thin / 10_000.0)
            proceeds = net_sell_proceeds(price, qty, c)
            fee = round(fill * qty - proceeds, 2)
        return round(fill, 2), fee
