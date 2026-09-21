import pytest

from brokers import dip_engine as de

RULE = {"symbol": "X", "dip_pct": 10, "sell_pct": 15, "usd": 100, "lookback_days": 20, "enabled": True,
        "manage_existing": False}
EMPTY = {"owned": {}, "pending_buy": {}, "prev_held": []}


class FakeBroker:
    def __init__(self, held=None, resting=None, price=89.0, high=100.0, account_error=None):
        self.held, self.resting, self.price, self.high = held or {}, resting or {}, price, high
        self.account_error, self.orders = account_error, []

    def get_portfolio(self):
        if self.account_error:
            raise RuntimeError(self.account_error)
        return self.held

    def get_open_orders(self):
        return self.resting

    def get_quote(self, sym):
        return {"last_price": self.price}

    def get_reference_high(self, sym, days):
        return self.high

    def place_order(self, *a, **k):
        self.orders.append((a, k))


# ---- decide() unchanged behaviour
def test_decide_buy_and_sell_cases():
    assert de.decide(RULE, 89, 100, None, set())["side"] == "BUY"
    assert de.decide(RULE, 95, 100, None, set()) is None
    assert de.decide(RULE, 500, 600, None, set()) is None  # can't afford a whole share
    s = de.decide(RULE, 50, 100, {"qty": 3, "avg_cost": 20}, set())
    assert (s["side"], s["qty"], s["price"]) == ("SELL", 3, 23.0)
    assert de.decide(RULE, 50, 100, {"qty": 3, "avg_cost": 20}, {"SELL"}) is None


# ---- safety: never trade on missing account data
def test_live_cycle_skipped_when_account_unreadable():
    b = FakeBroker(account_error="boom")
    with pytest.raises(RuntimeError):
        de.run_once(b, [RULE], live=True, state=EMPTY)
    assert b.orders == []


def test_preview_degrades_to_empty_account():
    rows = de.run_once(FakeBroker(account_error="boom"), [RULE], live=False, state=EMPTY, preview=True)
    assert rows[0]["account_ok"] is False and rows[0]["stage"] == "armed"


def test_readonly_env(monkeypatch):
    monkeypatch.setenv("IBKR_READONLY", "1")
    assert de.readonly()
    monkeypatch.delenv("IBKR_READONLY")
    assert not de.readonly()


# ---- safety: only manage shares the engine bought
def test_existing_shares_left_alone_unless_owned_or_opted_in():
    held = {"X": {"qty": 5, "avg_cost": 20}}
    b = FakeBroker(held=held)
    row = de.run_once(b, [RULE], live=True, state=EMPTY)[0]
    assert row["stage"] == "unmanaged" and b.orders == []
    row = de.run_once(b, [{**RULE, "manage_existing": True}], live=True, state=EMPTY)[0]
    assert row["stage"] == "holding" and row["sent"] and b.orders[0][0][3] == "SELL"
    b2 = FakeBroker(held=held)
    owned = {**EMPTY, "owned": {"X": 1.0}}
    assert de.run_once(b2, [RULE], live=True, state=owned)[0]["sent"]


# ---- safety: no double-buy while a BUY is unfilled
def test_pending_buy_blocks_rebuy():
    b = FakeBroker()
    st = {**EMPTY, "pending_buy": {"X": 1000.0}}
    row = de.run_once(b, [RULE], live=True, state=st, now=1100.0)[0]
    assert row["stage"] == "pending" and b.orders == []
    row = de.run_once(b, [RULE], live=True, state=st, now=1000.0 + de.PENDING_BUY_SECS + 1)[0]
    assert row["sent"]  # expired -> allowed again


def test_next_dip_state_tracks_owned_and_pending():
    sent = {"symbol": "X", "sent": True, "action": {"side": "BUY"}, "held_qty": 0}
    st = de.next_dip_state(EMPTY, [sent], 1000.0)
    assert st["pending_buy"] == {"X": 1000.0} and "X" in st["owned"]
    filled = {"symbol": "X", "sent": False, "action": None, "held_qty": 4}
    st2 = de.next_dip_state(st, [filled], 1100.0)
    assert st2["pending_buy"] == {} and "X" in st2["owned"] and st2["prev_held"] == ["X"]
    st3 = de.next_dip_state(st2, [{"symbol": "X", "sent": False, "action": None, "held_qty": 0}], 1200.0)
    assert st3["owned"] == {}  # position closed -> no longer engine-owned


# ---- state file
def test_state_roundtrip_and_health(tmp_path):
    p = str(tmp_path / "s.json")
    assert de.read_state(p) is None and de.engine_health(None) == "none"
    de.write_state("dry-run", [{"symbol": "X"}], 15, now=1000.0, path=p)
    st = de.read_state(p)
    assert st["mode"] == "dry-run" and st["rows"] == [{"symbol": "X"}]
    assert de.engine_health(st, now=1000.0 + 60) == "running"
    assert de.engine_health(st, now=1000.0 + 2 * 15 * 60 + 121) == "stale"
    de.write_state("dry-run", [], 15, running=False, now=1000.0, path=p)
    assert de.engine_health(de.read_state(p), now=1001.0) == "stopped"


def test_clean_rules_backfills_and_validates():
    r = de.clean_rules([{"symbol": "aapl"}])[0]
    assert r["symbol"] == "AAPL" and r["manage_existing"] is False and r["enabled"] is True
    for bad in ([{"symbol": "A B"}], [{"symbol": "A"}, {"symbol": "A"}], [{"symbol": "A", "dip_pct": 0}]):
        with pytest.raises(ValueError):
            de.clean_rules(bad)
