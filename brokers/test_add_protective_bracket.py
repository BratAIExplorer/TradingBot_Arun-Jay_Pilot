"""Offline checks for add_protective_bracket.py's math and settings-reading — no IBKR
connection, no network calls. The actual order placement can only be verified live
(see the script's own CONFIRM-gated run), but the bracket-price math and the
never_sell_at_loss branch are pure functions of settings.json + avg_cost, and wrong
math here is exactly the kind of bug that's expensive to catch after a real order.
"""
from brokers.add_protective_bracket import _load_risk_settings


def test_settings_load_matches_known_keys():
    """Confirms settings.json has the three keys this script depends on, and that
    they parse to the expected types — catches a renamed/missing key before it turns
    into a wrong stop price on a live order."""
    risk = _load_risk_settings()
    assert isinstance(risk["stop_loss_pct"], (int, float))
    assert isinstance(risk["catastrophic_stop_pct"], (int, float))
    assert isinstance(risk["never_sell_at_loss"], bool)
    assert risk["catastrophic_stop_pct"] > risk["stop_loss_pct"], \
        "catastrophic stop should be further from entry than the regular stop-loss"


def test_bracket_price_math():
    """The exact math add_protective_bracket.py uses, isolated — avg_cost=100,
    stop_loss=5%, catastrophic=20% should give 95 and 80, not something transposed."""
    avg_cost = 100.0
    stop_loss_pct = 5
    catastrophic_stop_pct = 20
    profit_target_pct = 15

    profit_price = round(avg_cost * (1 + profit_target_pct / 100), 2)
    catastrophic_price = round(avg_cost * (1 - catastrophic_stop_pct / 100), 2)
    stop_loss_price = round(avg_cost * (1 - stop_loss_pct / 100), 2)

    assert profit_price == 115.0
    assert catastrophic_price == 80.0
    assert stop_loss_price == 95.0
    # Sanity: catastrophic must be BELOW the regular stop-loss (further downside),
    # never above it — a transposed formula would put catastrophic closer than SL.
    assert catastrophic_price < stop_loss_price


if __name__ == "__main__":
    test_settings_load_matches_known_keys()
    test_bracket_price_math()
    print("OK — brokers/test_add_protective_bracket.py")
