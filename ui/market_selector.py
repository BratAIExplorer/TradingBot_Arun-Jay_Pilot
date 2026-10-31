"""
Orbit Trading - Market Selector Component

Provides a clean, minimal market switcher for the dashboard.
Allows seamless switching between India (INR/NSE) and US (USD/SMART) markets.

Design Principles:
  SIMPLE   — Clean UI layout, readable callbacks, no hidden state.
  SMART    — Structured for future AI confidence / signal display per market.
  SECURE   — No hardcoded credentials or environment-sensitive values.
  RESPECTFUL — Respects per-market settings; never overrides user preferences.
"""

from __future__ import annotations

import customtkinter as ctk
from dataclasses import dataclass
from typing import Callable, Optional


# ---------------------------------------------------------------------------
# Value object: immutable market configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MarketConfig:
    """
    Immutable configuration for a single trading market.

    Frozen dataclass — all fields are read-only after creation.
    Use the module-level ``MARKETS`` dict to access standard configs.

    Attributes:
        code:          Short ISO-like code used internally ('IN' | 'US').
        name:          Human-readable market name ('India', 'United States').
        currency:      Currency symbol displayed in the UI ('₹' | '$').
        currency_code: ISO-4217 currency code ('INR' | 'USD').
        exchange:      Default exchange for order routing ('NSE' | 'SMART').
        hours:         Trading hours string shown in the status bar.
        timezone:      IANA timezone identifier for the market's local time.
    """

    code: str           # 'IN' or 'US'
    name: str           # "India" or "United States"
    currency: str       # "₹" or "$"
    currency_code: str  # "INR" or "USD"
    exchange: str       # "NSE" or "SMART"
    hours: str          # "9:15-15:30 IST" or "9:30-16:00 EST"
    timezone: str       # "Asia/Kolkata" or "America/New_York"


# ---------------------------------------------------------------------------
# Canonical market definitions — extend here to add new markets
# ---------------------------------------------------------------------------

MARKETS: dict[str, MarketConfig] = {
    "IN": MarketConfig(
        code="IN",
        name="India",
        currency="₹",
        currency_code="INR",
        exchange="NSE",
        hours="9:15-15:30 IST",
        timezone="Asia/Kolkata",
    ),
    "US": MarketConfig(
        code="US",
        name="United States",
        currency="$",
        currency_code="USD",
        exchange="SMART",
        hours="9:30-16:00 EST",
        timezone="America/New_York",
    ),
}

# Display label → market code mapping (keeps _on_market_selected readable)
_LABEL_TO_CODE: dict[str, str] = {
    f"{cfg.name} ({cfg.currency_code})": code
    for code, cfg in MARKETS.items()
}


# ---------------------------------------------------------------------------
# MarketSelector widget
# ---------------------------------------------------------------------------

class MarketSelector(ctk.CTkFrame):
    """
    Market selector component for the Orbit Trading dashboard.

    Renders a compact, horizontal bar containing:
      - A dropdown to switch between available markets.
      - A currency label (e.g. "Currency: ₹ INR").
      - A trading-hours label (e.g. "Hours: 9:15-15:30 IST").
      - A live open/closed status indicator (🟢 / 🔴).

    Usage::

        def on_change(code: str) -> None:
            print(f"Switched to {code}")

        selector = MarketSelector(parent, on_market_change=on_change)

    SMART extension point:
        Future versions can call ``set_ai_confidence(market, score)`` to
        overlay AI signal confidence next to the status indicator without
        changing any existing API.
    """

    def __init__(
        self,
        parent: ctk.CTkFrame,
        on_market_change: Optional[Callable[[str], None]] = None,
        current_market: str = "IN",
        **kwargs,
    ) -> None:
        """
        Initialise the market selector widget.

        Args:
            parent:           Parent CTk widget to attach this frame to.
            on_market_change: Optional callback invoked with the new market
                              code ('IN' | 'US') whenever the user switches.
            current_market:   Initial market code. Defaults to 'IN' (India).
            **kwargs:         Forwarded to ``ctk.CTkFrame.__init__``.
        """
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.on_market_change: Optional[Callable[[str], None]] = on_market_change
        self.current_market: str = current_market

        # Per-market open/closed tracking; updated by set_market_status()
        self._market_status: dict[str, bool] = {code: False for code in MARKETS}

        self._build_ui()

    # ------------------------------------------------------------------
    # Private — UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Build and pack all child widgets.  Called once from __init__."""
        # Dropdown: "India (INR)" / "United States (USD)"
        dropdown_values = [f"{cfg.name} ({cfg.currency_code})" for cfg in MARKETS.values()]
        self.market_selector = ctk.CTkOptionMenu(
            self,
            values=dropdown_values,
            command=self._on_market_selected,
            fg_color="#479FB6",
            button_color="#479FB6",
            text_color="white",
            font=("Roboto", 12, "bold"),
        )
        self.market_selector.pack(side="left", padx=10, pady=5)
        self._update_selector_label()

        # Currency display
        cfg = self._get_current_market()
        self.lbl_currency = ctk.CTkLabel(
            self,
            text=f"Currency: {cfg.currency} {cfg.currency_code}",
            font=("Roboto", 11),
            text_color="#666",
        )
        self.lbl_currency.pack(side="left", padx=10, pady=5)

        # Market hours
        self.lbl_hours = ctk.CTkLabel(
            self,
            text=f"Hours: {cfg.hours}",
            font=("Roboto", 10),
            text_color="#999",
        )
        self.lbl_hours.pack(side="left", padx=10, pady=5)

        # Open/closed status indicator
        self.lbl_status = ctk.CTkLabel(
            self,
            text="🔴 Closed",
            font=("Roboto", 11, "bold"),
            text_color="#EF4444",
        )
        self.lbl_status.pack(side="left", padx=10, pady=5)

    # ------------------------------------------------------------------
    # Private — internal helpers
    # ------------------------------------------------------------------

    def _get_current_market(self) -> MarketConfig:
        """Return the ``MarketConfig`` for the currently active market."""
        return MARKETS[self.current_market]

    def _on_market_selected(self, choice: str) -> None:
        """
        Handle a new selection from the dropdown.

        Parses ``choice`` (e.g. "United States (USD)") into a market code,
        updates all labels, then fires ``on_market_change`` if set.

        Args:
            choice: The dropdown label that the user selected.
        """
        new_code = _LABEL_TO_CODE.get(choice)
        if new_code is None:
            # Fallback: legacy string parsing for resilience
            if "India" in choice:
                new_code = "IN"
            elif "United States" in choice:
                new_code = "US"
            else:
                return  # Unknown market — ignore silently

        self.current_market = new_code
        cfg = self._get_current_market()

        self._update_selector_label()
        self.lbl_currency.configure(
            text=f"Currency: {cfg.currency} {cfg.currency_code}"
        )
        self.lbl_hours.configure(text=f"Hours: {cfg.hours}")
        self._update_status_indicator()

        if self.on_market_change is not None:
            self.on_market_change(self.current_market)

    def _update_selector_label(self) -> None:
        """Sync the dropdown label to match the current market."""
        cfg = self._get_current_market()
        self.market_selector.set(f"{cfg.name} ({cfg.currency_code})")

    def _update_status_indicator(self) -> None:
        """Refresh the 🟢/🔴 indicator based on the current market's status."""
        is_open = self._market_status.get(self.current_market, False)
        if is_open:
            self.lbl_status.configure(text="🟢 OPEN", text_color="#10B981")
        else:
            self.lbl_status.configure(text="🔴 Closed", text_color="#EF4444")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_market_status(self, market: str, is_open: bool) -> None:
        """
        Update whether a given market is currently open.

        Called by the dashboard on a schedule (e.g. every minute) so the
        status indicator stays accurate without any polling inside this widget.

        Args:
            market:  Market code to update ('IN' | 'US').
            is_open: ``True`` if the market is currently open for trading.
        """
        self._market_status[market] = is_open
        if market == self.current_market:
            self._update_status_indicator()

    def get_current_market(self) -> str:
        """
        Return the active market code.

        Returns:
            'IN' for India, 'US' for United States.
        """
        return self.current_market

    def get_current_config(self) -> MarketConfig:
        """
        Return the immutable ``MarketConfig`` for the active market.

        The returned object is frozen — callers must not attempt mutation.

        Returns:
            ``MarketConfig`` instance for the current market.
        """
        return self._get_current_market()


# ---------------------------------------------------------------------------
# MultiMarketPortfolioView widget
# ---------------------------------------------------------------------------

class MultiMarketPortfolioView(ctk.CTkFrame):
    """
    Dual-market portfolio summary panel (optional "View Both Markets" mode).

    Displays:
      - India section  — P&L and open positions in INR (₹).
      - US section     — P&L and open positions in USD ($).
      - Combined row   — Approximate total converted to a single currency.

    Call ``update_pnl()`` to refresh all three sections at once.

    Example::

        view = MultiMarketPortfolioView(parent)
        view.update_pnl(
            india_pnl="P&L: ₹+400 | Positions: 3",
            us_pnl="P&L: $+250 | Positions: 2",
            combined="₹+21,000 total | Return: +2.1%",
        )
    """

    def __init__(self, parent: ctk.CTkFrame, **kwargs) -> None:
        """
        Initialise the portfolio view with placeholder values.

        Args:
            parent:   Parent CTk widget.
            **kwargs: Forwarded to ``ctk.CTkFrame.__init__``.
        """
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._build_ui()

    # ------------------------------------------------------------------
    # Private — UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Construct all labelled sections.  Called once from ``__init__``."""
        # --- Title ---
        ctk.CTkLabel(
            self,
            text="PORTFOLIO SUMMARY (Both Markets)",
            font=("Roboto", 14, "bold"),
            text_color="#1a1a1a",
        ).pack(anchor="w", padx=10, pady=(10, 5))

        # --- India section ---
        india_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=8)
        india_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            india_frame,
            text="🇮🇳 INDIA (INR)",
            font=("Roboto", 12, "bold"),
            text_color="#479FB6",
        ).pack(anchor="w", padx=10, pady=(10, 0))

        self.lbl_india_pnl = ctk.CTkLabel(
            india_frame,
            text="P&L: ₹+400 | Positions: 3",
            font=("Roboto", 11),
            text_color="#10B981",
        )
        self.lbl_india_pnl.pack(anchor="w", padx=10, pady=(5, 10))

        # --- US section ---
        us_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=8)
        us_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            us_frame,
            text="🇺🇸 UNITED STATES (USD)",
            font=("Roboto", 12, "bold"),
            text_color="#479FB6",
        ).pack(anchor="w", padx=10, pady=(10, 0))

        self.lbl_us_pnl = ctk.CTkLabel(
            us_frame,
            text="P&L: $+250 | Positions: 2",
            font=("Roboto", 11),
            text_color="#10B981",
        )
        self.lbl_us_pnl.pack(anchor="w", padx=10, pady=(5, 10))

        # --- Combined section ---
        combined_frame = ctk.CTkFrame(self, fg_color="#EFEBE3", corner_radius=8)
        combined_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            combined_frame,
            text="COMBINED",
            font=("Roboto", 12, "bold"),
            text_color="#1a1a1a",
        ).pack(anchor="w", padx=10, pady=(10, 0))

        self.lbl_combined = ctk.CTkLabel(
            combined_frame,
            text="₹+400 + $+250 ≈ ₹+21,000 total | Return: +2.1%",
            font=("Roboto", 11, "bold"),
            text_color="#479FB6",
        )
        self.lbl_combined.pack(anchor="w", padx=10, pady=(5, 10))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_pnl(self, india_pnl: str, us_pnl: str, combined: str) -> None:
        """
        Refresh all three P&L labels simultaneously.

        Args:
            india_pnl: Full text for the India P&L row
                       (e.g. "P&L: ₹+1,200 | Positions: 5").
            us_pnl:    Full text for the US P&L row
                       (e.g. "P&L: $+300 | Positions: 2").
            combined:  Full text for the combined summary row
                       (e.g. "₹+21,000 total | Return: +2.1%").
        """
        self.lbl_india_pnl.configure(text=india_pnl)
        self.lbl_us_pnl.configure(text=us_pnl)
        self.lbl_combined.configure(text=combined)
