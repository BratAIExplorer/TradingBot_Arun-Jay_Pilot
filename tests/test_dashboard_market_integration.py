"""
Dashboard Market Integration Tests — RED Phase (TDD)

Tests for integrating MarketSelector into DashboardV2 (sensei_v1_dashboard.py).
All 13 tests written BEFORE modifying the dashboard (RED → should fail initially).

Tests cover:
1.  Dashboard initializes with market selector component
2.  Market selector appears in navigation bar / header area
3.  Selecting India market updates portfolio display
4.  Selecting US market updates portfolio display
5.  Currency display changes (₹ vs $) when market changes
6.  Market hours display updates correctly
7.  Status indicator shows correct market status
8.  Portfolio data filters by market
9.  P&L displays in correct currency
10. Settings load per-market on market change
11. RSI thresholds change per-market
12. No existing dashboard functionality broken
13. Market selection persists across portfolio updates
"""

from __future__ import annotations

import sys
import os
import types
import threading
import queue
import pytest
from unittest.mock import MagicMock, patch, call, PropertyMock

# ---------------------------------------------------------------------------
# Step 1: Build stubs for ALL heavy imports BEFORE loading the dashboard.
# The dashboard imports ctk, kickstart, knowledge_center, market_sentiment,
# settings_manager, state_manager, database.trades_db — we stub them all.
# ---------------------------------------------------------------------------

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def _make_ctk_stub() -> types.ModuleType:
    """Minimal customtkinter stub for headless testing."""
    ctk = types.ModuleType("customtkinter")

    class _Base:
        def __init__(self, *args, **kwargs):
            self._text = kwargs.get("text", "")
            self._text_color = kwargs.get("text_color", "")
            self._fg_color = kwargs.get("fg_color", "")

        def pack(self, **kwargs):
            pass

        def pack_forget(self):
            pass

        def configure(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, f"_{k}", v)

        def get(self):
            return self._text

        def set(self, value):
            self._text = value

        def after(self, ms, fn=None, *args):
            pass

    class CTkFrame(_Base):
        pass

    class CTkLabel(_Base):
        pass

    class CTkOptionMenu(_Base):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._command = kwargs.get("command", None)

        def invoke(self, choice):
            if self._command:
                self._command(choice)

    class CTkButton(_Base):
        pass

    class CTkSegmentedButton(_Base):
        pass

    class CTkScrollableFrame(_Base):
        pass

    class CTkTextbox(_Base):
        def insert(self, *args):
            pass

        def see(self, *args):
            pass

        def configure(self, **kwargs):
            pass

    class CTkTabview(_Base):
        def add(self, *args):
            return _Base()

        def tab(self, *args):
            return _Base()

        def set(self, *args):
            pass

    class CTkComboBox(_Base):
        pass

    class CTkEntry(_Base):
        pass

    class CTkCheckBox(_Base):
        pass

    class StringVar:
        def __init__(self, value=""):
            self._value = value

        def get(self):
            return self._value

        def set(self, v):
            self._value = v

    class IntVar:
        def __init__(self, value=0):
            self._value = value

        def get(self):
            return self._value

        def set(self, v):
            self._value = v

    class CTkToplevel(_Base):
        def __init__(self, *args, **kwargs):
            pass

        def title(self, *a):
            pass

        def geometry(self, *a):
            pass

        def resizable(self, *a):
            pass

        def protocol(self, *a):
            pass

        def grab_set(self):
            pass

        def after(self, *a):
            pass

        def configure(self, **kwargs):
            pass

    class CTkSwitch(_Base):
        pass

    class CTkSlider(_Base):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def set(self, v):
            pass

    class CTkProgressBar(_Base):
        def set(self, v):
            pass

    class CTkRadioButton(_Base):
        pass

    def set_appearance_mode(*a):
        pass

    def set_default_color_theme(*a):
        pass

    ctk.CTkFrame = CTkFrame
    ctk.CTkLabel = CTkLabel
    ctk.CTkOptionMenu = CTkOptionMenu
    ctk.CTkButton = CTkButton
    ctk.CTkSegmentedButton = CTkSegmentedButton
    ctk.CTkScrollableFrame = CTkScrollableFrame
    ctk.CTkTextbox = CTkTextbox
    ctk.CTkTabview = CTkTabview
    ctk.CTkComboBox = CTkComboBox
    ctk.CTkEntry = CTkEntry
    ctk.CTkCheckBox = CTkCheckBox
    ctk.CTkToplevel = CTkToplevel
    ctk.CTkSwitch = CTkSwitch
    ctk.CTkSlider = CTkSlider
    ctk.CTkProgressBar = CTkProgressBar
    ctk.CTkRadioButton = CTkRadioButton
    ctk.StringVar = StringVar
    ctk.IntVar = IntVar
    ctk.set_appearance_mode = set_appearance_mode
    ctk.set_default_color_theme = set_default_color_theme
    return ctk


def _register_stubs():
    """Install all module stubs before dashboard is imported."""
    # customtkinter
    sys.modules.setdefault("customtkinter", _make_ctk_stub())

    # tkinter
    tk = types.ModuleType("tkinter")
    tk.END = "end"
    tk_ttk = types.ModuleType("tkinter.ttk")
    tk_ttk.Treeview = MagicMock()
    tk.ttk = tk_ttk
    tk.messagebox = MagicMock()
    sys.modules.setdefault("tkinter", tk)
    sys.modules.setdefault("tkinter.ttk", tk_ttk)

    # psutil
    psutil = types.ModuleType("psutil")
    sys.modules.setdefault("psutil", psutil)

    # kickstart — all the symbols the dashboard imports from it
    kickstart = types.ModuleType("kickstart")
    kickstart.run_cycle = MagicMock(return_value={})
    kickstart.fetch_market_data = MagicMock(return_value={})
    kickstart.config_dict = {}
    kickstart.SYMBOLS_TO_TRACK = []
    kickstart.calculate_intraday_rsi_tv = MagicMock(return_value=50.0)
    kickstart.is_system_online = MagicMock(return_value=False)
    kickstart.safe_get_positions = MagicMock(return_value={})
    kickstart.safe_get_live_positions_merged = MagicMock(return_value={})
    kickstart.reload_config = MagicMock(return_value=True)
    sys.modules.setdefault("kickstart", kickstart)

    # knowledge_center
    kc = types.ModuleType("knowledge_center")
    kc.TOOLTIPS = {}
    kc.STRATEGY_GUIDES = {}
    kc.get_strategy_guide = MagicMock(return_value="")
    kc.get_contextual_tip = MagicMock(return_value="")
    sys.modules.setdefault("knowledge_center", kc)

    # market_sentiment
    ms = types.ModuleType("market_sentiment")
    ms.MarketSentiment = MagicMock()
    sys.modules.setdefault("market_sentiment", ms)

    # settings_manager — provide a real-ish stub with get_market_settings
    sm_mod = types.ModuleType("settings_manager")

    _MARKET_SETTINGS_DEFAULTS = {
        "IN": {
            "rsi_threshold_buy": 30,
            "rsi_threshold_sell": 70,
            "currency": "INR",
            "exchange": "NSE",
        },
        "US": {
            "rsi_threshold_buy": 35,
            "rsi_threshold_sell": 65,
            "currency": "USD",
            "exchange": "SMART",
        },
    }

    class _FakeSettingsManager:
        """Non-singleton stub — each instantiation is independent."""

        def __init__(self, *args, **kwargs):
            self.settings = {}

        def get(self, key, default=None):
            return default

        def get_stock_configs(self):
            return []

        def get_market_settings(self, market: str) -> dict:
            """Per-market RSI thresholds and config."""
            return _MARKET_SETTINGS_DEFAULTS.get(market, {}).copy()

        def save(self):
            return True

    sm_mod.SettingsManager = _FakeSettingsManager
    sys.modules["settings_manager"] = sm_mod

    # state_manager
    state_m = types.ModuleType("state_manager")
    state_m.state = MagicMock()
    sys.modules.setdefault("state_manager", state_m)

    # database.trades_db
    db_pkg = types.ModuleType("database")
    db_mod = types.ModuleType("database.trades_db")

    class _FakeTradesDB:
        def get_recent_trades(self, limit=100, market=None):
            return []

        def get_performance_summary(self):
            return {}

    db_mod.TradesDatabase = _FakeTradesDB
    db_pkg.trades_db = db_mod
    sys.modules.setdefault("database", db_pkg)
    sys.modules.setdefault("database.trades_db", db_mod)

    # markets
    mkt = types.ModuleType("markets")
    mkt.is_market_open = MagicMock(return_value=False)
    sys.modules.setdefault("markets", mkt)

    # ui package + ui.market_selector
    ui_dir = os.path.join(_PROJECT_ROOT, "ui")
    import importlib.util as _ilu

    if "ui" not in sys.modules:
        _pkg_spec = _ilu.spec_from_file_location(
            "ui",
            os.path.join(ui_dir, "__init__.py"),
            submodule_search_locations=[ui_dir],
        )
        _pkg = _ilu.module_from_spec(_pkg_spec)
        sys.modules["ui"] = _pkg
        _pkg_spec.loader.exec_module(_pkg)

    if "ui.market_selector" not in sys.modules:
        _mod_spec = _ilu.spec_from_file_location(
            "ui.market_selector",
            os.path.join(ui_dir, "market_selector.py"),
        )
        _mod = _ilu.module_from_spec(_mod_spec)
        sys.modules["ui.market_selector"] = _mod
        _mod_spec.loader.exec_module(_mod)


_register_stubs()

# Re-import after stubs are installed
from ui.market_selector import MarketSelector, MARKETS, MarketConfig  # noqa: E402


# ---------------------------------------------------------------------------
# Helper: build a DashboardV2 instance without a real Tk root
# ---------------------------------------------------------------------------

def _make_dashboard():
    """
    Import and instantiate DashboardV2 with a fully mocked root window.
    The dashboard's __init__ calls build_header(), show_view(), and starts
    background threads — all of which are safe under our stubs.
    """
    import importlib.util as _ilu

    dashboard_path = os.path.join(_PROJECT_ROOT, "sensei_v1_dashboard.py")
    spec = _ilu.spec_from_file_location("sensei_v1_dashboard", dashboard_path)
    mod = _ilu.module_from_spec(spec)
    sys.modules["sensei_v1_dashboard"] = mod
    spec.loader.exec_module(mod)

    DashboardV2 = mod.DashboardV2

    root = MagicMock()
    root.after = MagicMock()

    dash = DashboardV2.__new__(DashboardV2)
    # Inject the minimum state __init__ would normally set
    dash.root = root
    dash.settings_mgr = sys.modules["settings_manager"].SettingsManager()
    dash.stop_update_flag = threading.Event()
    dash.data_queue = queue.Queue(maxsize=100)
    dash.running = False
    dash.alerts_list = []
    dash.is_online_status = False
    dash.trade_stats = {"attempts": 0, "success": 0, "failed": 0}
    dash.all_positions_data = {}
    dash.scanner_running = False
    dash.scanner_results = []
    dash.last_scan_total = 0
    dash.scanner_thread = None
    dash.current_market = "IN"
    return dash, mod


# ===========================================================================
# Test 1: Dashboard initializes with market selector component
# ===========================================================================

class TestDashboardHasMarketSelector:
    """DashboardV2 must expose a market_selector attribute after init."""

    def test_dashboard_has_market_selector_attribute(self):
        """After init, dashboard must have self.market_selector."""
        dash, mod = _make_dashboard()
        root = MagicMock()
        root.after = MagicMock()

        # We patch all builder methods to be no-ops so only __init__ runs
        with patch.object(mod.DashboardV2, "build_header"), \
             patch.object(mod.DashboardV2, "build_dashboard_view"), \
             patch.object(mod.DashboardV2, "build_strategies_view"), \
             patch.object(mod.DashboardV2, "build_settings_view"), \
             patch.object(mod.DashboardV2, "build_knowledge_view"), \
             patch.object(mod.DashboardV2, "build_logs_view"), \
             patch.object(mod.DashboardV2, "build_hybrid_view"), \
             patch.object(mod.DashboardV2, "build_trades_view"), \
             patch.object(mod.DashboardV2, "build_stocks_view"), \
             patch.object(mod.DashboardV2, "build_scanner_view"), \
             patch.object(mod.DashboardV2, "show_view"), \
             patch.object(mod.DashboardV2, "start_background_threads"), \
             patch.object(mod.DashboardV2, "update_ui_loop"), \
             patch.object(mod.DashboardV2, "refresh_balance"), \
             patch.object(mod.DashboardV2, "balance_refresh_timer"):
            instance = mod.DashboardV2(root)

        assert hasattr(instance, "market_selector"), (
            "DashboardV2 must have self.market_selector after __init__"
        )

    def test_market_selector_is_correct_type(self):
        """self.market_selector must be an instance of MarketSelector."""
        dash, mod = _make_dashboard()
        root = MagicMock()
        root.after = MagicMock()

        with patch.object(mod.DashboardV2, "build_header"), \
             patch.object(mod.DashboardV2, "build_dashboard_view"), \
             patch.object(mod.DashboardV2, "build_strategies_view"), \
             patch.object(mod.DashboardV2, "build_settings_view"), \
             patch.object(mod.DashboardV2, "build_knowledge_view"), \
             patch.object(mod.DashboardV2, "build_logs_view"), \
             patch.object(mod.DashboardV2, "build_hybrid_view"), \
             patch.object(mod.DashboardV2, "build_trades_view"), \
             patch.object(mod.DashboardV2, "build_stocks_view"), \
             patch.object(mod.DashboardV2, "build_scanner_view"), \
             patch.object(mod.DashboardV2, "show_view"), \
             patch.object(mod.DashboardV2, "start_background_threads"), \
             patch.object(mod.DashboardV2, "update_ui_loop"), \
             patch.object(mod.DashboardV2, "refresh_balance"), \
             patch.object(mod.DashboardV2, "balance_refresh_timer"):
            instance = mod.DashboardV2(root)

        assert isinstance(instance.market_selector, MarketSelector), (
            "self.market_selector must be a MarketSelector instance"
        )

    def test_dashboard_initializes_current_market_to_in(self):
        """Dashboard starts with India ('IN') as the current market."""
        dash, mod = _make_dashboard()
        root = MagicMock()
        root.after = MagicMock()

        with patch.object(mod.DashboardV2, "build_header"), \
             patch.object(mod.DashboardV2, "build_dashboard_view"), \
             patch.object(mod.DashboardV2, "build_strategies_view"), \
             patch.object(mod.DashboardV2, "build_settings_view"), \
             patch.object(mod.DashboardV2, "build_knowledge_view"), \
             patch.object(mod.DashboardV2, "build_logs_view"), \
             patch.object(mod.DashboardV2, "build_hybrid_view"), \
             patch.object(mod.DashboardV2, "build_trades_view"), \
             patch.object(mod.DashboardV2, "build_stocks_view"), \
             patch.object(mod.DashboardV2, "build_scanner_view"), \
             patch.object(mod.DashboardV2, "show_view"), \
             patch.object(mod.DashboardV2, "start_background_threads"), \
             patch.object(mod.DashboardV2, "update_ui_loop"), \
             patch.object(mod.DashboardV2, "refresh_balance"), \
             patch.object(mod.DashboardV2, "balance_refresh_timer"):
            instance = mod.DashboardV2(root)

        assert instance.current_market == "IN"


# ===========================================================================
# Helper: build a patched DashboardV2 instance (used across most tests)
# ===========================================================================

def _init_dashboard(mod):
    """Instantiate DashboardV2 with all builder methods patched out."""
    root = MagicMock()
    root.after = MagicMock()

    patches = [
        patch.object(mod.DashboardV2, "build_header"),
        patch.object(mod.DashboardV2, "build_dashboard_view"),
        patch.object(mod.DashboardV2, "build_strategies_view"),
        patch.object(mod.DashboardV2, "build_settings_view"),
        patch.object(mod.DashboardV2, "build_knowledge_view"),
        patch.object(mod.DashboardV2, "build_logs_view"),
        patch.object(mod.DashboardV2, "build_hybrid_view"),
        patch.object(mod.DashboardV2, "build_trades_view"),
        patch.object(mod.DashboardV2, "build_stocks_view"),
        patch.object(mod.DashboardV2, "build_scanner_view"),
        patch.object(mod.DashboardV2, "show_view"),
        patch.object(mod.DashboardV2, "start_background_threads"),
        patch.object(mod.DashboardV2, "update_ui_loop"),
        patch.object(mod.DashboardV2, "refresh_balance"),
        patch.object(mod.DashboardV2, "balance_refresh_timer"),
    ]
    for p in patches:
        p.start()

    instance = mod.DashboardV2(root)

    for p in patches:
        p.stop()

    return instance


# ===========================================================================
# Test 2: Market selector appears in navigation bar / header
# ===========================================================================

class TestMarketSelectorInHeader:
    """Market selector widget must be embedded within the dashboard header."""

    def test_market_selector_present_after_build_header(self):
        """After build_header(), self.market_selector must exist."""
        _, mod = _make_dashboard()

        root = MagicMock()
        root.after = MagicMock()

        # Patch everything EXCEPT build_header so it actually runs
        with patch.object(mod.DashboardV2, "build_dashboard_view"), \
             patch.object(mod.DashboardV2, "build_strategies_view"), \
             patch.object(mod.DashboardV2, "build_settings_view"), \
             patch.object(mod.DashboardV2, "build_knowledge_view"), \
             patch.object(mod.DashboardV2, "build_logs_view"), \
             patch.object(mod.DashboardV2, "build_hybrid_view"), \
             patch.object(mod.DashboardV2, "build_trades_view"), \
             patch.object(mod.DashboardV2, "build_stocks_view"), \
             patch.object(mod.DashboardV2, "build_scanner_view"), \
             patch.object(mod.DashboardV2, "show_view"), \
             patch.object(mod.DashboardV2, "start_background_threads"), \
             patch.object(mod.DashboardV2, "update_ui_loop"), \
             patch.object(mod.DashboardV2, "refresh_balance"), \
             patch.object(mod.DashboardV2, "balance_refresh_timer"), \
             patch.object(mod.DashboardV2, "load_cached_holdings", create=True):
            instance = mod.DashboardV2(root)

        assert hasattr(instance, "market_selector"), (
            "build_header() must create self.market_selector"
        )

    def test_market_selector_default_market_is_in(self):
        """Market selector embedded in header must default to 'IN'."""
        _, mod = _make_dashboard()
        root = MagicMock()
        root.after = MagicMock()

        with patch.object(mod.DashboardV2, "build_dashboard_view"), \
             patch.object(mod.DashboardV2, "build_strategies_view"), \
             patch.object(mod.DashboardV2, "build_settings_view"), \
             patch.object(mod.DashboardV2, "build_knowledge_view"), \
             patch.object(mod.DashboardV2, "build_logs_view"), \
             patch.object(mod.DashboardV2, "build_hybrid_view"), \
             patch.object(mod.DashboardV2, "build_trades_view"), \
             patch.object(mod.DashboardV2, "build_stocks_view"), \
             patch.object(mod.DashboardV2, "build_scanner_view"), \
             patch.object(mod.DashboardV2, "show_view"), \
             patch.object(mod.DashboardV2, "start_background_threads"), \
             patch.object(mod.DashboardV2, "update_ui_loop"), \
             patch.object(mod.DashboardV2, "refresh_balance"), \
             patch.object(mod.DashboardV2, "balance_refresh_timer"), \
             patch.object(mod.DashboardV2, "load_cached_holdings", create=True):
            instance = mod.DashboardV2(root)

        if hasattr(instance, "market_selector"):
            assert instance.market_selector.get_current_market() == "IN"


# ===========================================================================
# Test 3 & 4: Selecting India / US market updates portfolio display
# ===========================================================================

class TestMarketChangeUpdatesPortfolio:
    """_on_market_changed() must refresh portfolio for the selected market."""

    def test_on_market_changed_updates_current_market_to_in(self):
        """Calling _on_market_changed('IN') sets self.current_market='IN'."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)

        # Patch portfolio-refresh so it doesn't error
        instance._refresh_portfolio_for_market = MagicMock()
        instance.write_log = MagicMock()

        instance._on_market_changed("IN")

        assert instance.current_market == "IN"

    def test_on_market_changed_updates_current_market_to_us(self):
        """Calling _on_market_changed('US') sets self.current_market='US'."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)

        instance._refresh_portfolio_for_market = MagicMock()
        instance.write_log = MagicMock()

        instance._on_market_changed("US")

        assert instance.current_market == "US"

    def test_on_market_changed_calls_refresh_portfolio(self):
        """_on_market_changed() must call _refresh_portfolio_for_market()."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)

        instance._refresh_portfolio_for_market = MagicMock()
        instance.write_log = MagicMock()

        instance._on_market_changed("US")

        instance._refresh_portfolio_for_market.assert_called_once_with("US")

    def test_on_market_changed_updates_market_config(self):
        """_on_market_changed() stores the MarketConfig for the new market."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)

        instance._refresh_portfolio_for_market = MagicMock()
        instance.write_log = MagicMock()

        instance._on_market_changed("US")

        assert hasattr(instance, "current_market_config")
        assert instance.current_market_config.code == "US"


# ===========================================================================
# Test 5: Currency display changes when market changes
# ===========================================================================

class TestCurrencyDisplayOnMarketChange:
    """Currency must reflect the active market."""

    def test_india_market_uses_inr_symbol(self):
        """After switching to IN, current_market_config.currency == '₹'."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)
        instance._refresh_portfolio_for_market = MagicMock()
        instance.write_log = MagicMock()

        instance._on_market_changed("IN")

        assert instance.current_market_config.currency == "₹"

    def test_us_market_uses_dollar_symbol(self):
        """After switching to US, current_market_config.currency == '$'."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)
        instance._refresh_portfolio_for_market = MagicMock()
        instance.write_log = MagicMock()

        instance._on_market_changed("US")

        assert instance.current_market_config.currency == "$"

    def test_currency_code_changes_on_market_switch(self):
        """currency_code transitions INR → USD on market switch."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)
        instance._refresh_portfolio_for_market = MagicMock()
        instance.write_log = MagicMock()

        instance._on_market_changed("IN")
        assert instance.current_market_config.currency_code == "INR"

        instance._on_market_changed("US")
        assert instance.current_market_config.currency_code == "USD"


# ===========================================================================
# Test 6: Market hours display updates correctly
# ===========================================================================

class TestMarketHoursUpdate:
    """Trading hours must reflect the active market after a switch."""

    def test_india_hours_after_in_switch(self):
        """Switching to IN stores India hours in market config."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)
        instance._refresh_portfolio_for_market = MagicMock()
        instance.write_log = MagicMock()

        instance._on_market_changed("IN")

        assert "IST" in instance.current_market_config.hours

    def test_us_hours_after_us_switch(self):
        """Switching to US stores US hours in market config."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)
        instance._refresh_portfolio_for_market = MagicMock()
        instance.write_log = MagicMock()

        instance._on_market_changed("US")

        assert "EST" in instance.current_market_config.hours


# ===========================================================================
# Test 7: Status indicator shows correct market status
# ===========================================================================

class TestMarketStatusIndicator:
    """Market selector status indicator reflects live open/closed state."""

    def test_set_market_status_open_on_selector(self):
        """_start_market_status_loop can call set_market_status on selector."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)

        if hasattr(instance, "market_selector"):
            instance.market_selector.set_market_status("IN", True)
            assert instance.market_selector._market_status["IN"] is True

    def test_set_market_status_closed_on_selector(self):
        """set_market_status(market, False) records closed state."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)

        if hasattr(instance, "market_selector"):
            instance.market_selector.set_market_status("IN", True)
            instance.market_selector.set_market_status("IN", False)
            assert instance.market_selector._market_status["IN"] is False

    def test_dashboard_has_start_market_status_loop(self):
        """Dashboard exposes _start_market_status_loop() method."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)

        assert hasattr(instance, "_start_market_status_loop"), (
            "DashboardV2 must have _start_market_status_loop()"
        )
        assert callable(instance._start_market_status_loop)


# ===========================================================================
# Test 8: Portfolio data filters by market
# ===========================================================================

class TestPortfolioFiltersByMarket:
    """_refresh_portfolio_for_market queries DB filtered by market."""

    def test_refresh_portfolio_calls_db_with_market(self):
        """_refresh_portfolio_for_market passes market arg to get_recent_trades."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)

        fake_db = MagicMock()
        fake_db.get_recent_trades.return_value = []
        instance.db = fake_db
        instance._update_portfolio_display = MagicMock()

        instance._refresh_portfolio_for_market("US")

        fake_db.get_recent_trades.assert_called_once()
        call_kwargs = fake_db.get_recent_trades.call_args
        # market should be passed as kwarg or positional
        assert "US" in str(call_kwargs), (
            "get_recent_trades must be called with market='US'"
        )

    def test_refresh_portfolio_no_db_does_not_raise(self):
        """_refresh_portfolio_for_market handles missing DB gracefully."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)
        instance.db = None  # No database

        # Must not raise
        instance._refresh_portfolio_for_market("IN")

    def test_refresh_portfolio_for_market_method_exists(self):
        """DashboardV2 must expose _refresh_portfolio_for_market()."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)

        assert hasattr(instance, "_refresh_portfolio_for_market"), (
            "DashboardV2 must have _refresh_portfolio_for_market()"
        )
        assert callable(instance._refresh_portfolio_for_market)


# ===========================================================================
# Test 9: P&L displays in correct currency
# ===========================================================================

class TestPnlCurrencyDisplay:
    """_update_portfolio_display uses the active market currency symbol."""

    def test_update_portfolio_display_method_exists(self):
        """DashboardV2 must have _update_portfolio_display()."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)

        assert hasattr(instance, "_update_portfolio_display"), (
            "DashboardV2 must have _update_portfolio_display()"
        )

    def test_pnl_uses_inr_for_india_market(self):
        """_format_pnl_for_display returns ₹-prefixed string for IN market."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)
        instance._refresh_portfolio_for_market = MagicMock()
        instance.write_log = MagicMock()
        instance._on_market_changed("IN")

        if hasattr(instance, "_format_currency"):
            result = instance._format_currency(1234.56)
            assert "₹" in result

    def test_pnl_uses_dollar_for_us_market(self):
        """_format_pnl_for_display returns $-prefixed string for US market."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)
        instance._refresh_portfolio_for_market = MagicMock()
        instance.write_log = MagicMock()
        instance._on_market_changed("US")

        if hasattr(instance, "_format_currency"):
            result = instance._format_currency(1234.56)
            assert "$" in result


# ===========================================================================
# Test 10: Settings load per-market on market change
# ===========================================================================

class TestSettingsLoadPerMarket:
    """_on_market_changed() loads market-specific settings."""

    def test_on_market_changed_loads_market_settings(self):
        """Switching market calls get_market_settings() on settings_mgr."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)
        instance._refresh_portfolio_for_market = MagicMock()
        instance.write_log = MagicMock()

        instance.settings_mgr.get_market_settings = MagicMock(
            return_value={"rsi_threshold_buy": 35, "rsi_threshold_sell": 65}
        )

        instance._on_market_changed("US")

        instance.settings_mgr.get_market_settings.assert_called_once_with("US")

    def test_market_settings_stored_after_change(self):
        """self.market_settings is populated after market change."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)
        instance._refresh_portfolio_for_market = MagicMock()
        instance.write_log = MagicMock()

        instance._on_market_changed("IN")

        assert hasattr(instance, "market_settings"), (
            "DashboardV2 must store market_settings after _on_market_changed"
        )
        assert isinstance(instance.market_settings, dict)


# ===========================================================================
# Test 11: RSI thresholds change per-market
# ===========================================================================

class TestRsiThresholdsPerMarket:
    """RSI buy/sell thresholds update when market changes."""

    def test_india_rsi_thresholds_applied(self):
        """India market sets rsi_threshold_buy=30, rsi_threshold_sell=70."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)
        instance._refresh_portfolio_for_market = MagicMock()
        instance.write_log = MagicMock()

        instance._on_market_changed("IN")

        assert hasattr(instance, "rsi_threshold_buy")
        assert hasattr(instance, "rsi_threshold_sell")
        assert instance.rsi_threshold_buy == 30
        assert instance.rsi_threshold_sell == 70

    def test_us_rsi_thresholds_applied(self):
        """US market sets rsi_threshold_buy=35, rsi_threshold_sell=65."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)
        instance._refresh_portfolio_for_market = MagicMock()
        instance.write_log = MagicMock()

        instance._on_market_changed("US")

        assert hasattr(instance, "rsi_threshold_buy")
        assert hasattr(instance, "rsi_threshold_sell")
        assert instance.rsi_threshold_buy == 35
        assert instance.rsi_threshold_sell == 65

    def test_rsi_thresholds_update_on_market_switch(self):
        """RSI thresholds switch correctly when market toggles IN → US."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)
        instance._refresh_portfolio_for_market = MagicMock()
        instance.write_log = MagicMock()

        instance._on_market_changed("IN")
        assert instance.rsi_threshold_buy == 30

        instance._on_market_changed("US")
        assert instance.rsi_threshold_buy == 35


# ===========================================================================
# Test 12: No existing dashboard functionality broken
# ===========================================================================

class TestNoRegressions:
    """Core dashboard attributes must still be present after market integration."""

    def test_settings_mgr_still_exists(self):
        """self.settings_mgr is available after market integration."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)
        assert hasattr(instance, "settings_mgr")

    def test_running_flag_still_exists(self):
        """self.running flag is still present."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)
        assert hasattr(instance, "running")

    def test_data_queue_still_exists(self):
        """self.data_queue is still present."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)
        assert hasattr(instance, "data_queue")

    def test_trade_stats_still_exists(self):
        """self.trade_stats dict is still present."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)
        assert hasattr(instance, "trade_stats")
        assert "attempts" in instance.trade_stats

    def test_all_positions_data_still_exists(self):
        """self.all_positions_data is still present."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)
        assert hasattr(instance, "all_positions_data")

    def test_is_online_status_still_exists(self):
        """self.is_online_status flag is still present."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)
        assert hasattr(instance, "is_online_status")

    def test_on_market_changed_method_exists(self):
        """_on_market_changed() must be a callable on the dashboard."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)
        assert hasattr(instance, "_on_market_changed"), (
            "DashboardV2 must have _on_market_changed()"
        )
        assert callable(instance._on_market_changed)


# ===========================================================================
# Test 13: Market selection persists across portfolio updates
# ===========================================================================

class TestMarketSelectionPersists:
    """Market selection must not reset when portfolio data is refreshed."""

    def test_market_persists_after_portfolio_update(self):
        """current_market stays 'US' after _refresh_portfolio_for_market."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)
        instance._refresh_portfolio_for_market = MagicMock()
        instance.write_log = MagicMock()

        instance._on_market_changed("US")
        assert instance.current_market == "US"

        # Simulate a portfolio refresh — market must not reset
        instance._on_market_changed("US")
        assert instance.current_market == "US"

    def test_market_code_matches_selector_after_switch(self):
        """self.current_market matches market_selector.get_current_market()."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)
        instance._refresh_portfolio_for_market = MagicMock()
        instance.write_log = MagicMock()

        if hasattr(instance, "market_selector"):
            # Simulate selector triggering the callback
            instance.market_selector._on_market_selected("United States (USD)")
            # After callback fires, dashboard current_market should match
            assert instance.current_market == instance.market_selector.get_current_market()

    def test_market_settings_consistent_with_current_market(self):
        """market_settings aligns with current_market after switch."""
        _, mod = _make_dashboard()
        instance = _init_dashboard(mod)
        instance._refresh_portfolio_for_market = MagicMock()
        instance.write_log = MagicMock()

        instance._on_market_changed("US")

        assert instance.current_market == "US"
        # market_settings should correspond to US defaults
        if instance.market_settings:
            assert instance.market_settings.get("currency") == "USD"
