"""
Orbit Trading - Market Selector UI Component Tests

TDD test suite for ui/market_selector.py
All tests written BEFORE implementation enhancements (RED phase).

Tests cover:
1. MarketConfig frozen dataclass (immutability)
2. MarketSelector initialization with callback
3. Market switching (IN → US → IN)
4. Currency display updates on market change
5. Hours display updates correctly
6. Status indicator (open/closed with emoji)
7. set_market_status() updates indicator
8. get_current_market() returns correct code
9. get_current_config() returns frozen config
10. on_market_change callback fires with correct market code
11. MultiMarketPortfolioView displays both markets
12. Portfolio view updates with new P&L values
13. Immutability: MarketConfig cannot be modified
"""

import sys
import os
import types
import pytest
from unittest.mock import MagicMock, patch, call
from dataclasses import FrozenInstanceError

# ---------------------------------------------------------------------------
# Step 1: Stub out customtkinter BEFORE loading ui.market_selector.
# This ensures the module never touches a real Tk display.
# ---------------------------------------------------------------------------

def _make_ctk_stub() -> types.ModuleType:
    """Create a minimal customtkinter stub for headless testing."""
    ctk = types.ModuleType("customtkinter")

    class _BaseWidget:
        def __init__(self, *args, **kwargs):
            self._text = kwargs.get("text", "")
            self._text_color = kwargs.get("text_color", "")
            self._configure_calls: list = []

        def pack(self, **kwargs):
            pass

        def configure(self, **kwargs):
            self._configure_calls.append(kwargs)
            if "text" in kwargs:
                self._text = kwargs["text"]
            if "text_color" in kwargs:
                self._text_color = kwargs["text_color"]

        def get(self) -> str:
            return self._text

        def set(self, value: str) -> None:
            self._text = value

    class CTkFrame(_BaseWidget):
        pass

    class CTkLabel(_BaseWidget):
        pass

    class CTkOptionMenu(_BaseWidget):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._command = kwargs.get("command", None)
            self._values = kwargs.get("values", [])

        def invoke(self, choice: str) -> None:
            if self._command:
                self._command(choice)

    ctk.CTkFrame = CTkFrame
    ctk.CTkLabel = CTkLabel
    ctk.CTkOptionMenu = CTkOptionMenu
    return ctk


# Install stub — force-replace so real customtkinter never loads
sys.modules["customtkinter"] = _make_ctk_stub()

# ---------------------------------------------------------------------------
# Step 2: Load ui.market_selector via importlib (Windows spaces-in-path fix).
# The stub is already in sys.modules so market_selector gets our fake ctk.
# ---------------------------------------------------------------------------

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_UI_DIR = os.path.join(_PROJECT_ROOT, "ui")
_UI_MODULE_PATH = os.path.join(_UI_DIR, "market_selector.py")


def _bootstrap_ui_package() -> None:
    """Register ui package and ui.market_selector into sys.modules."""
    import importlib.util as _ilu

    if "ui" not in sys.modules:
        _pkg_spec = _ilu.spec_from_file_location(
            "ui",
            os.path.join(_UI_DIR, "__init__.py"),
            submodule_search_locations=[_UI_DIR],
        )
        _pkg = _ilu.module_from_spec(_pkg_spec)
        sys.modules["ui"] = _pkg
        _pkg_spec.loader.exec_module(_pkg)

    if "ui.market_selector" not in sys.modules:
        _mod_spec = _ilu.spec_from_file_location("ui.market_selector", _UI_MODULE_PATH)
        _mod = _ilu.module_from_spec(_mod_spec)
        sys.modules["ui.market_selector"] = _mod
        _mod_spec.loader.exec_module(_mod)


_bootstrap_ui_package()

# Now import — sys.modules already has the module, so this is instant
from ui.market_selector import MarketConfig, MarketSelector, MultiMarketPortfolioView, MARKETS  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_selector(market: str = "IN", callback=None) -> MarketSelector:
    """Create a MarketSelector with a dummy parent (no Tk needed with stub)."""
    parent = MagicMock()
    return MarketSelector(parent, on_market_change=callback, current_market=market)


# ===========================================================================
# 1. MarketConfig frozen dataclass
# ===========================================================================

class TestMarketConfig:
    """MarketConfig is an immutable value object."""

    def test_market_config_fields_india(self):
        """MARKETS['IN'] has correct field values for India."""
        cfg = MARKETS["IN"]
        assert cfg.code == "IN"
        assert cfg.name == "India"
        assert cfg.currency == "₹"
        assert cfg.currency_code == "INR"
        assert cfg.exchange == "NSE"
        assert cfg.hours == "9:15-15:30 IST"
        assert cfg.timezone == "Asia/Kolkata"

    def test_market_config_fields_us(self):
        """MARKETS['US'] has correct field values for United States."""
        cfg = MARKETS["US"]
        assert cfg.code == "US"
        assert cfg.name == "United States"
        assert cfg.currency == "$"
        assert cfg.currency_code == "USD"
        assert cfg.exchange == "SMART"
        assert cfg.hours == "9:30-16:00 EST"
        assert cfg.timezone == "America/New_York"

    def test_market_config_is_frozen(self):
        """MarketConfig is a frozen dataclass — mutations raise FrozenInstanceError."""
        cfg = MARKETS["IN"]
        with pytest.raises(FrozenInstanceError):
            cfg.currency = "£"  # type: ignore[misc]

    def test_market_config_code_immutable(self):
        """Cannot reassign the code field."""
        cfg = MARKETS["US"]
        with pytest.raises(FrozenInstanceError):
            cfg.code = "XX"  # type: ignore[misc]

    def test_market_config_equality(self):
        """Two MarketConfig with identical fields are equal (value semantics)."""
        a = MarketConfig(
            code="IN", name="India", currency="₹", currency_code="INR",
            exchange="NSE", hours="9:15-15:30 IST", timezone="Asia/Kolkata",
        )
        b = MarketConfig(
            code="IN", name="India", currency="₹", currency_code="INR",
            exchange="NSE", hours="9:15-15:30 IST", timezone="Asia/Kolkata",
        )
        assert a == b

    def test_only_two_markets_defined(self):
        """MARKETS dict contains exactly IN and US."""
        assert set(MARKETS.keys()) == {"IN", "US"}


# ===========================================================================
# 2. MarketSelector initialization
# ===========================================================================

class TestMarketSelectorInit:
    """MarketSelector constructs correctly with various init arguments."""

    def test_default_market_is_india(self):
        """Default market is IN when no current_market given."""
        sel = _make_selector()
        assert sel.get_current_market() == "IN"

    def test_init_with_us_market(self):
        """Can initialize with US as starting market."""
        sel = _make_selector(market="US")
        assert sel.get_current_market() == "US"

    def test_init_with_callback_stored(self):
        """Callback is stored on instance."""
        cb = MagicMock()
        sel = _make_selector(callback=cb)
        assert sel.on_market_change is cb

    def test_init_without_callback_is_none(self):
        """on_market_change is None when not provided."""
        sel = _make_selector()
        assert sel.on_market_change is None

    def test_market_status_initializes_closed(self):
        """Both markets start with closed status (False)."""
        sel = _make_selector()
        assert sel._market_status["IN"] is False
        assert sel._market_status["US"] is False


# ===========================================================================
# 3. Market switching — IN → US → IN
# ===========================================================================

class TestMarketSwitching:
    """Market switching via internal _on_market_selected."""

    def test_switch_from_india_to_us(self):
        """Selecting 'United States (USD)' sets current_market to 'US'."""
        sel = _make_selector(market="IN")
        sel._on_market_selected("United States (USD)")
        assert sel.get_current_market() == "US"

    def test_switch_from_us_to_india(self):
        """Selecting 'India (INR)' sets current_market to 'IN'."""
        sel = _make_selector(market="US")
        sel._on_market_selected("India (INR)")
        assert sel.get_current_market() == "IN"

    def test_round_trip_switch(self):
        """Switching IN → US → IN restores original market."""
        sel = _make_selector(market="IN")
        sel._on_market_selected("United States (USD)")
        assert sel.get_current_market() == "US"
        sel._on_market_selected("India (INR)")
        assert sel.get_current_market() == "IN"

    def test_switch_with_full_label(self):
        """The label format 'India (INR)' (as produced by _update_selector_label) works."""
        sel = _make_selector(market="US")
        sel._on_market_selected("India (INR)")
        assert sel.get_current_market() == "IN"


# ===========================================================================
# 4. Currency display updates on market change
# ===========================================================================

class TestCurrencyDisplay:
    """Currency label reflects current market."""

    def test_currency_label_shows_inr_initially(self):
        """On init with IN market, currency label shows INR."""
        sel = _make_selector(market="IN")
        assert "INR" in sel.lbl_currency._text
        assert "₹" in sel.lbl_currency._text

    def test_currency_label_shows_usd_initially(self):
        """On init with US market, currency label shows USD."""
        sel = _make_selector(market="US")
        assert "USD" in sel.lbl_currency._text
        assert "$" in sel.lbl_currency._text

    def test_currency_label_updates_on_switch_to_us(self):
        """Switching to US updates currency label to USD."""
        sel = _make_selector(market="IN")
        sel._on_market_selected("United States (USD)")
        assert "USD" in sel.lbl_currency._text
        assert "$" in sel.lbl_currency._text

    def test_currency_label_updates_on_switch_to_in(self):
        """Switching to IN updates currency label to INR."""
        sel = _make_selector(market="US")
        sel._on_market_selected("India (INR)")
        assert "INR" in sel.lbl_currency._text
        assert "₹" in sel.lbl_currency._text


# ===========================================================================
# 5. Hours display updates on market change
# ===========================================================================

class TestHoursDisplay:
    """Hours label reflects current market trading hours."""

    def test_hours_label_shows_india_hours_initially(self):
        """India hours '9:15-15:30 IST' shown on init with IN."""
        sel = _make_selector(market="IN")
        assert "9:15-15:30 IST" in sel.lbl_hours._text

    def test_hours_label_shows_us_hours_initially(self):
        """US hours '9:30-16:00 EST' shown on init with US."""
        sel = _make_selector(market="US")
        assert "9:30-16:00 EST" in sel.lbl_hours._text

    def test_hours_label_updates_on_switch_to_us(self):
        """Switching to US updates hours to US trading hours."""
        sel = _make_selector(market="IN")
        sel._on_market_selected("United States (USD)")
        assert "9:30-16:00 EST" in sel.lbl_hours._text

    def test_hours_label_updates_on_switch_to_in(self):
        """Switching to IN updates hours to India trading hours."""
        sel = _make_selector(market="US")
        sel._on_market_selected("India (INR)")
        assert "9:15-15:30 IST" in sel.lbl_hours._text


# ===========================================================================
# 6. Status indicator (open/closed with emoji)
# ===========================================================================

class TestStatusIndicator:
    """Status label shows correct open/closed state."""

    def test_status_shows_closed_initially(self):
        """On init, status shows '🔴 Closed' (both markets start closed)."""
        sel = _make_selector(market="IN")
        assert "🔴" in sel.lbl_status._text
        assert "Closed" in sel.lbl_status._text

    def test_status_shows_open_when_market_open(self):
        """After set_market_status(IN, True), status shows '🟢 OPEN'."""
        sel = _make_selector(market="IN")
        sel.set_market_status("IN", True)
        assert "🟢" in sel.lbl_status._text
        assert "OPEN" in sel.lbl_status._text

    def test_status_reverts_to_closed_when_closed(self):
        """After open then closed, status shows '🔴 Closed' again."""
        sel = _make_selector(market="IN")
        sel.set_market_status("IN", True)
        sel.set_market_status("IN", False)
        assert "🔴" in sel.lbl_status._text

    def test_status_open_color_is_green(self):
        """Open status uses green color (#10B981)."""
        sel = _make_selector(market="IN")
        sel.set_market_status("IN", True)
        assert sel.lbl_status._text_color == "#10B981"

    def test_status_closed_color_is_red(self):
        """Closed status uses red color (#EF4444)."""
        sel = _make_selector(market="IN")
        # Default is closed — check color
        assert sel.lbl_status._text_color == "#EF4444"


# ===========================================================================
# 7. set_market_status() — cross-market status tracking
# ===========================================================================

class TestSetMarketStatus:
    """set_market_status correctly tracks per-market open/closed state."""

    def test_set_other_market_open_does_not_change_indicator(self):
        """Setting US open while viewing IN does not change indicator."""
        sel = _make_selector(market="IN")
        sel.set_market_status("US", True)
        # Still on IN market, which is closed
        assert "🔴" in sel.lbl_status._text

    def test_switch_to_open_market_shows_open(self):
        """After US is set open, switching to US shows OPEN."""
        sel = _make_selector(market="IN")
        sel.set_market_status("US", True)
        sel._on_market_selected("United States (USD)")
        assert "🟢" in sel.lbl_status._text

    def test_set_current_market_open_updates_immediately(self):
        """set_market_status on current market updates indicator immediately."""
        sel = _make_selector(market="IN")
        sel.set_market_status("IN", True)
        assert "🟢" in sel.lbl_status._text

    def test_market_status_stored_in_dict(self):
        """_market_status dict is updated by set_market_status."""
        sel = _make_selector(market="IN")
        sel.set_market_status("IN", True)
        sel.set_market_status("US", True)
        assert sel._market_status["IN"] is True
        assert sel._market_status["US"] is True


# ===========================================================================
# 8. get_current_market() returns correct code
# ===========================================================================

class TestGetCurrentMarket:
    """get_current_market() always returns the active market code."""

    def test_returns_in_initially(self):
        sel = _make_selector(market="IN")
        assert sel.get_current_market() == "IN"

    def test_returns_us_after_switch(self):
        sel = _make_selector(market="IN")
        sel._on_market_selected("United States (USD)")
        assert sel.get_current_market() == "US"

    def test_returns_string_not_config(self):
        """Returns a plain string, not a MarketConfig object."""
        sel = _make_selector(market="IN")
        result = sel.get_current_market()
        assert isinstance(result, str)

    def test_returns_in_after_round_trip(self):
        sel = _make_selector(market="IN")
        sel._on_market_selected("United States (USD)")
        sel._on_market_selected("India (INR)")
        assert sel.get_current_market() == "IN"


# ===========================================================================
# 9. get_current_config() returns frozen MarketConfig
# ===========================================================================

class TestGetCurrentConfig:
    """get_current_config() returns the correct MarketConfig."""

    def test_returns_india_config_initially(self):
        sel = _make_selector(market="IN")
        cfg = sel.get_current_config()
        assert cfg.code == "IN"
        assert cfg.currency_code == "INR"

    def test_returns_us_config_after_switch(self):
        sel = _make_selector(market="IN")
        sel._on_market_selected("United States (USD)")
        cfg = sel.get_current_config()
        assert cfg.code == "US"
        assert cfg.currency_code == "USD"

    def test_returned_config_is_frozen(self):
        """Config returned by get_current_config() is immutable."""
        sel = _make_selector(market="IN")
        cfg = sel.get_current_config()
        with pytest.raises(FrozenInstanceError):
            cfg.name = "Hacked"  # type: ignore[misc]

    def test_returned_config_is_marketconfig_instance(self):
        """get_current_config() returns a MarketConfig instance."""
        sel = _make_selector(market="US")
        cfg = sel.get_current_config()
        assert isinstance(cfg, MarketConfig)


# ===========================================================================
# 10. on_market_change callback fires with correct market code
# ===========================================================================

class TestCallback:
    """Callback fires correctly on market changes."""

    def test_callback_fires_on_switch_to_us(self):
        """Callback receives 'US' when switching to United States."""
        cb = MagicMock()
        sel = _make_selector(market="IN", callback=cb)
        sel._on_market_selected("United States (USD)")
        cb.assert_called_once_with("US")

    def test_callback_fires_on_switch_to_in(self):
        """Callback receives 'IN' when switching to India."""
        cb = MagicMock()
        sel = _make_selector(market="US", callback=cb)
        sel._on_market_selected("India (INR)")
        cb.assert_called_once_with("IN")

    def test_callback_fires_on_each_switch(self):
        """Callback fires each time market changes (not just once)."""
        cb = MagicMock()
        sel = _make_selector(market="IN", callback=cb)
        sel._on_market_selected("United States (USD)")
        sel._on_market_selected("India (INR)")
        assert cb.call_count == 2
        assert cb.call_args_list == [call("US"), call("IN")]

    def test_no_callback_does_not_raise(self):
        """If no callback provided, market switch does not raise."""
        sel = _make_selector(market="IN", callback=None)
        # Should not raise
        sel._on_market_selected("United States (USD)")
        assert sel.get_current_market() == "US"

    def test_callback_receives_string_code(self):
        """Callback receives a plain string market code, not a MarketConfig."""
        received = []
        sel = _make_selector(market="IN", callback=lambda code: received.append(code))
        sel._on_market_selected("United States (USD)")
        assert len(received) == 1
        assert isinstance(received[0], str)
        assert received[0] == "US"


# ===========================================================================
# 11. MultiMarketPortfolioView — displays both markets
# ===========================================================================

class TestMultiMarketPortfolioView:
    """MultiMarketPortfolioView shows India and US portfolio data."""

    def _make_view(self) -> MultiMarketPortfolioView:
        parent = MagicMock()
        return MultiMarketPortfolioView(parent)

    def test_view_creates_india_pnl_label(self):
        """India P&L label exists after init."""
        view = self._make_view()
        assert hasattr(view, "lbl_india_pnl")

    def test_view_creates_us_pnl_label(self):
        """US P&L label exists after init."""
        view = self._make_view()
        assert hasattr(view, "lbl_us_pnl")

    def test_view_creates_combined_label(self):
        """Combined label exists after init."""
        view = self._make_view()
        assert hasattr(view, "lbl_combined")

    def test_india_pnl_shows_inr_symbol(self):
        """Default India P&L text contains ₹ symbol."""
        view = self._make_view()
        assert "₹" in view.lbl_india_pnl._text

    def test_us_pnl_shows_dollar_symbol(self):
        """Default US P&L text contains $ symbol."""
        view = self._make_view()
        assert "$" in view.lbl_us_pnl._text

    def test_has_update_pnl_method(self):
        """MultiMarketPortfolioView exposes update_pnl() method."""
        view = self._make_view()
        assert callable(getattr(view, "update_pnl", None))


# ===========================================================================
# 12. Portfolio view updates with new P&L values
# ===========================================================================

class TestPortfolioViewUpdate:
    """update_pnl() correctly updates all three labels."""

    def _make_view(self) -> MultiMarketPortfolioView:
        parent = MagicMock()
        return MultiMarketPortfolioView(parent)

    def test_update_pnl_changes_india_label(self):
        """update_pnl sets India P&L label text."""
        view = self._make_view()
        view.update_pnl("P&L: ₹+1,200 | Positions: 5", "$+300", "combined")
        assert "₹+1,200" in view.lbl_india_pnl._text

    def test_update_pnl_changes_us_label(self):
        """update_pnl sets US P&L label text."""
        view = self._make_view()
        view.update_pnl("india", "P&L: $+500 | Positions: 3", "combined")
        assert "$+500" in view.lbl_us_pnl._text

    def test_update_pnl_changes_combined_label(self):
        """update_pnl sets combined label text."""
        view = self._make_view()
        view.update_pnl("india", "us", "₹+1,200 + $+300 ≈ ₹+26,100 | Return: +2.5%")
        assert "₹+1,200" in view.lbl_combined._text

    def test_update_pnl_with_negative_values(self):
        """update_pnl handles negative P&L strings."""
        view = self._make_view()
        view.update_pnl("P&L: ₹-500", "P&L: $-200", "Loss day")
        assert "₹-500" in view.lbl_india_pnl._text
        assert "$-200" in view.lbl_us_pnl._text

    def test_update_pnl_with_zero_values(self):
        """update_pnl handles zero P&L strings."""
        view = self._make_view()
        view.update_pnl("P&L: ₹0", "P&L: $0", "Break even")
        assert "₹0" in view.lbl_india_pnl._text

    def test_update_pnl_accepts_empty_strings(self):
        """update_pnl does not raise on empty strings."""
        view = self._make_view()
        view.update_pnl("", "", "")  # Should not raise
        assert view.lbl_india_pnl._text == ""


# ===========================================================================
# 13. Immutability — MarketConfig cannot be modified (additional edge cases)
# ===========================================================================

class TestImmutability:
    """MarketConfig is strictly immutable in all scenarios."""

    def test_cannot_add_new_attribute(self):
        """Cannot set a new attribute on frozen MarketConfig."""
        cfg = MARKETS["IN"]
        with pytest.raises((FrozenInstanceError, AttributeError)):
            cfg.new_field = "something"  # type: ignore[misc]

    def test_cannot_delete_attribute(self):
        """Cannot delete an attribute on frozen MarketConfig."""
        cfg = MARKETS["IN"]
        with pytest.raises((FrozenInstanceError, AttributeError)):
            del cfg.code  # type: ignore[misc]

    def test_config_returned_from_get_current_config_is_immutable(self):
        """Config from get_current_config() cannot be mutated."""
        sel = _make_selector(market="US")
        cfg = sel.get_current_config()
        with pytest.raises(FrozenInstanceError):
            cfg.exchange = "NYSE"  # type: ignore[misc]

    def test_markets_dict_values_are_all_frozen(self):
        """Every value in MARKETS dict is a frozen MarketConfig."""
        for code, cfg in MARKETS.items():
            assert isinstance(cfg, MarketConfig)
            with pytest.raises(FrozenInstanceError):
                cfg.code = "HACKED"  # type: ignore[misc]

    def test_market_selector_internal_state_changes_not_config(self):
        """Switching market on selector does not mutate any MarketConfig."""
        original_in = MARKETS["IN"]
        original_us = MARKETS["US"]
        sel = _make_selector(market="IN")
        sel._on_market_selected("United States (USD)")
        sel._on_market_selected("India (INR)")
        # MARKETS dict must be unchanged after switching
        assert MARKETS["IN"] == original_in
        assert MARKETS["US"] == original_us
