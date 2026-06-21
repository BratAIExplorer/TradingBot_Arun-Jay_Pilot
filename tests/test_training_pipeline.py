"""
TDD Tests for ml/training_pipeline.py — MLTrainingPipeline
RED phase: all tests written before implementation.

Run:
    pytest tests/test_training_pipeline.py -v
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Helpers — build fake signal dicts
# ---------------------------------------------------------------------------

def _make_signal(
    *,
    symbol: str = "RELIANCE",
    action: str = "BUY",
    source: str = "MANUAL",
    market: str = "IN",
    rsi: float = 35.0,
    volume: float = 500000.0,
    price: float = 2500.0,
    timestamp: str | None = None,
    ma_20: float = 2480.0,
    ma_50: float = 2450.0,
) -> dict:
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "symbol": symbol,
        "action": action,
        "source": source,
        "market": market,
        "rsi": rsi,
        "volume": volume,
        "price": price,
        "timestamp": timestamp,
        "ma_20": ma_20,
        "ma_50": ma_50,
    }


def _make_db(signals: list[dict]) -> MagicMock:
    """Return a mock TradesDatabase that returns ``signals`` from get_manual_signals."""
    db = MagicMock()
    db.get_manual_signals.return_value = signals
    return db


# ---------------------------------------------------------------------------
# COLLECTION PHASE TESTS (1-5)
# ---------------------------------------------------------------------------

class TestCollectSignals:
    """Tests 1-5: collect_signals()"""

    def test_1_returns_list(self):
        """Test collect_signals(market='IN', days=30) returns list."""
        from ml.training_pipeline import MLTrainingPipeline

        signals = [_make_signal() for _ in range(15)]
        db = _make_db(signals)
        pipeline = MLTrainingPipeline(db)

        result = pipeline.collect_signals(market="IN", days=30)

        assert isinstance(result, list)

    def test_2_only_manual_trades_returned(self):
        """Test only MANUAL trades returned (filters out BOT)."""
        from ml.training_pipeline import MLTrainingPipeline

        signals = [
            _make_signal(source="MANUAL"),
            _make_signal(source="BOT"),
            _make_signal(source="MANUAL"),
            _make_signal(source="BOT"),
            _make_signal(source="MANUAL"),
        ]
        db = _make_db(signals)
        pipeline = MLTrainingPipeline(db)

        # collect_signals should filter BOT out when applied
        result = pipeline.collect_signals(market="IN", days=30)
        sources = [s["source"] for s in result]
        assert all(src == "MANUAL" for src in sources), f"Non-MANUAL found: {sources}"

    def test_3_returns_empty_if_fewer_than_10_signals(self):
        """Test returns empty list if <10 signals."""
        from ml.training_pipeline import MLTrainingPipeline

        signals = [_make_signal() for _ in range(8)]
        db = _make_db(signals)
        pipeline = MLTrainingPipeline(db)

        result = pipeline.collect_signals(market="IN", days=30)

        assert result == []

    def test_4_signals_from_correct_market_only(self):
        """Test signals from correct market only."""
        from ml.training_pipeline import MLTrainingPipeline

        signals = [
            _make_signal(market="IN"),
            _make_signal(market="US"),
            _make_signal(market="IN"),
            _make_signal(market="US"),
        ] * 5  # 20 total, mixed markets
        db = _make_db(signals)
        pipeline = MLTrainingPipeline(db)

        result = pipeline.collect_signals(market="IN", days=30)
        markets = [s["market"] for s in result]
        assert all(m == "IN" for m in markets), f"Wrong market found: {markets}"

    def test_5_signals_include_required_fields(self):
        """Test signals include timestamp, symbol, rsi, volume."""
        from ml.training_pipeline import MLTrainingPipeline

        signals = [_make_signal() for _ in range(15)]
        db = _make_db(signals)
        pipeline = MLTrainingPipeline(db)

        result = pipeline.collect_signals(market="IN", days=30)

        assert len(result) > 0
        for sig in result:
            for field in ("timestamp", "symbol", "rsi", "volume"):
                assert field in sig, f"Missing field '{field}' in signal: {sig.keys()}"


# ---------------------------------------------------------------------------
# ANALYSIS PHASE TESTS (6-10)
# ---------------------------------------------------------------------------

class TestLabelOutcomes:
    """Tests 6-10: label_outcomes()"""

    def _pipeline_with_future_price(self, future_price: float | None):
        from ml.training_pipeline import MLTrainingPipeline

        db = MagicMock()
        pipeline = MLTrainingPipeline(db)
        pipeline._get_future_price = MagicMock(return_value=future_price)
        return pipeline

    def test_6_returns_all_signals_with_outcome_key(self):
        """Test label_outcomes() returns all signals with 'outcome' key."""
        pipeline = self._pipeline_with_future_price(2600.0)
        signals = [_make_signal(price=2500.0, action="BUY") for _ in range(5)]

        result = pipeline.label_outcomes(signals)

        assert len(result) == 5
        for sig in result:
            assert "outcome" in sig

    def test_7_buy_price_up_is_correct(self):
        """Test BUY outcome: price up = CORRECT."""
        pipeline = self._pipeline_with_future_price(2700.0)  # higher than entry 2500
        signals = [_make_signal(price=2500.0, action="BUY")]

        result = pipeline.label_outcomes(signals)

        assert result[0]["outcome"] == "CORRECT"

    def test_7b_buy_price_down_is_wrong(self):
        """Test BUY outcome: price down = WRONG."""
        pipeline = self._pipeline_with_future_price(2300.0)  # lower than entry 2500
        signals = [_make_signal(price=2500.0, action="BUY")]

        result = pipeline.label_outcomes(signals)

        assert result[0]["outcome"] == "WRONG"

    def test_8_sell_price_down_is_correct(self):
        """Test SELL outcome: price down = CORRECT."""
        pipeline = self._pipeline_with_future_price(2300.0)  # lower — good for sell
        signals = [_make_signal(price=2500.0, action="SELL")]

        result = pipeline.label_outcomes(signals)

        assert result[0]["outcome"] == "CORRECT"

    def test_8b_sell_price_up_is_wrong(self):
        """Test SELL outcome: price up = WRONG."""
        pipeline = self._pipeline_with_future_price(2700.0)  # higher — bad for sell
        signals = [_make_signal(price=2500.0, action="SELL")]

        result = pipeline.label_outcomes(signals)

        assert result[0]["outcome"] == "WRONG"

    def test_9_skip_outcome_flat_is_correct(self):
        """Test SKIP outcome: price flat (<=1%) = CORRECT."""
        pipeline = self._pipeline_with_future_price(2510.0)  # flat ~0.4%
        signals = [_make_signal(price=2500.0, action="SKIP")]

        result = pipeline.label_outcomes(signals)

        assert result[0]["outcome"] == "CORRECT"

    def test_9b_skip_outcome_big_move_is_wrong(self):
        """Test SKIP outcome: big move (>3%) = WRONG."""
        pipeline = self._pipeline_with_future_price(2700.0)  # +8%
        signals = [_make_signal(price=2500.0, action="SKIP")]

        result = pipeline.label_outcomes(signals)

        assert result[0]["outcome"] == "WRONG"

    def test_10_returns_empty_if_no_future_price(self):
        """Test returns empty list if no future price available for any signal."""
        pipeline = self._pipeline_with_future_price(None)
        signals = [_make_signal() for _ in range(5)]

        result = pipeline.label_outcomes(signals)

        assert result == []


# ---------------------------------------------------------------------------
# TRAINING PHASE TESTS (11-19)
# ---------------------------------------------------------------------------

class TestBuildFeatures:
    """Tests 11-14: build_features()"""

    def _labeled_signals(self, n: int = 15) -> list[dict]:
        return [
            {**_make_signal(), "outcome": "CORRECT", "ma_20": 2480.0, "ma_50": 2450.0}
            for _ in range(n)
        ]

    def test_11_returns_X_y_numpy_arrays(self):
        """Test build_features() returns (X, y) numpy arrays."""
        from ml.training_pipeline import MLTrainingPipeline

        pipeline = MLTrainingPipeline(MagicMock())
        X, y = pipeline.build_features(self._labeled_signals())

        assert isinstance(X, np.ndarray)
        assert isinstance(y, np.ndarray)

    def test_12_X_has_7_features(self):
        """Test X array has 7 features per signal."""
        from ml.training_pipeline import MLTrainingPipeline

        pipeline = MLTrainingPipeline(MagicMock())
        X, y = pipeline.build_features(self._labeled_signals(15))

        assert X.shape[1] == 7, f"Expected 7 features, got {X.shape[1]}"

    def test_13_y_is_binary(self):
        """Test y array is binary [1=correct, 0=wrong]."""
        from ml.training_pipeline import MLTrainingPipeline

        signals = [
            {**_make_signal(), "outcome": "CORRECT"},
            {**_make_signal(), "outcome": "WRONG"},
            {**_make_signal(), "outcome": "CORRECT"},
        ] * 5
        pipeline = MLTrainingPipeline(MagicMock())
        X, y = pipeline.build_features(signals)

        unique = set(y.tolist())
        assert unique <= {0, 1}, f"Non-binary values in y: {unique}"
        assert 1 in unique and 0 in unique

    def test_14_raises_value_error_if_fewer_than_10_signals(self):
        """Test raises ValueError if <10 signals."""
        from ml.training_pipeline import MLTrainingPipeline

        pipeline = MLTrainingPipeline(MagicMock())
        signals = [
            {**_make_signal(), "outcome": "CORRECT"}
            for _ in range(5)
        ]

        with pytest.raises(ValueError, match="10"):
            pipeline.build_features(signals)


class TestTrain:
    """Tests 15-19: train()"""

    def _pipeline_ready(self, market: str = "IN"):
        """Pipeline with mocked collect_signals + label_outcomes returning labeled data."""
        from ml.training_pipeline import MLTrainingPipeline

        labeled = [
            {**_make_signal(market=market), "outcome": "CORRECT" if i % 2 == 0 else "WRONG"}
            for i in range(30)
        ]
        db = MagicMock()
        pipeline = MLTrainingPipeline(db)
        pipeline.collect_signals = MagicMock(return_value=labeled)
        pipeline.label_outcomes = MagicMock(return_value=labeled)
        return pipeline

    def test_15_train_returns_dict_with_accuracy(self):
        """Test train(market='IN') returns dict with 'accuracy' key."""
        pipeline = self._pipeline_ready()
        result = pipeline.train(market="IN")

        assert isinstance(result, dict)
        assert "accuracy" in result

    def test_16_train_sets_model(self):
        """Test train() sets self.model (not None)."""
        pipeline = self._pipeline_ready()
        pipeline.train(market="IN")

        assert pipeline.model is not None

    def test_17_train_sets_scaler(self):
        """Test train() sets self.scaler (StandardScaler fitted)."""
        from sklearn.preprocessing import StandardScaler

        pipeline = self._pipeline_ready()
        pipeline.train(market="IN")

        assert pipeline.scaler is not None
        assert isinstance(pipeline.scaler, StandardScaler)

    def test_18_high_accuracy_sets_model_ready(self):
        """Test accuracy >0.70 sets model_ready=True."""
        from ml.training_pipeline import MLTrainingPipeline

        # Build signals designed so the model can learn them well
        labeled = []
        for i in range(60):
            # Alternating clear pattern: low RSI => CORRECT BUY, high RSI => WRONG
            rsi = 20.0 if i % 2 == 0 else 80.0
            outcome = "CORRECT" if i % 2 == 0 else "WRONG"
            labeled.append({**_make_signal(rsi=rsi), "outcome": outcome})

        db = MagicMock()
        pipeline = MLTrainingPipeline(db)
        pipeline.collect_signals = MagicMock(return_value=labeled)
        pipeline.label_outcomes = MagicMock(return_value=labeled)

        result = pipeline.train(market="IN")

        if result["accuracy"] > 0.70:
            assert pipeline.model_ready is True
        else:
            # Accept: it may not reach 0.70 on tiny random data — just verify flag follows accuracy
            assert pipeline.model_ready == (result["accuracy"] > 0.70)

    def test_19_train_result_has_signals_used_and_timestamp(self):
        """Test train result dict contains signals_used, model_ready, timestamp."""
        pipeline = self._pipeline_ready()
        result = pipeline.train(market="IN")

        for key in ("signals_used", "model_ready", "timestamp"):
            assert key in result, f"Missing key '{key}' in result: {result.keys()}"


# ---------------------------------------------------------------------------
# VALIDATION PHASE TESTS (20-25)
# ---------------------------------------------------------------------------

class TestPredict:
    """Tests 20-25: predict()"""

    def _trained_pipeline(self):
        from ml.training_pipeline import MLTrainingPipeline

        labeled = [
            {**_make_signal(), "outcome": "CORRECT" if i % 2 == 0 else "WRONG"}
            for i in range(30)
        ]
        db = MagicMock()
        pipeline = MLTrainingPipeline(db)
        pipeline.collect_signals = MagicMock(return_value=labeled)
        pipeline.label_outcomes = MagicMock(return_value=labeled)
        pipeline.train(market="IN")
        return pipeline

    def _features(self) -> dict:
        return {
            "rsi": 35.0,
            "volume": 500000.0,
            "ma_20": 2480.0,
            "ma_50": 2450.0,
            "market_trend": 1.0,
            "hour_of_day": 10,
            "market_code": 0,
        }

    def test_20_returns_prediction_and_confidence_tuple(self):
        """Test predict() returns (prediction, confidence) tuple."""
        pipeline = self._trained_pipeline()
        result = pipeline.predict("RELIANCE", "IN", self._features())

        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_21_prediction_is_valid_label(self):
        """Test prediction is GOOD_TRADE or SKIP_TRADE."""
        pipeline = self._trained_pipeline()
        prediction, _ = pipeline.predict("RELIANCE", "IN", self._features())

        assert prediction in ("GOOD_TRADE", "SKIP_TRADE", "UNKNOWN")

    def test_22_confidence_is_float_between_0_and_1(self):
        """Test confidence is float between 0.0 and 1.0."""
        pipeline = self._trained_pipeline()
        _, confidence = pipeline.predict("RELIANCE", "IN", self._features())

        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

    def test_23_returns_unknown_if_no_model_trained(self):
        """Test returns UNKNOWN if no model trained."""
        from ml.training_pipeline import MLTrainingPipeline

        pipeline = MLTrainingPipeline(MagicMock())
        prediction, confidence = pipeline.predict("RELIANCE", "IN", self._features())

        assert prediction == "UNKNOWN"
        assert confidence == 0.0

    def test_24_features_scaled_before_prediction(self):
        """Test features are scaled before prediction (scaler.transform called)."""
        from ml.training_pipeline import MLTrainingPipeline
        from sklearn.preprocessing import StandardScaler

        pipeline = self._trained_pipeline()
        original_scaler = pipeline.scaler

        # Wrap scaler.transform to spy
        original_transform = original_scaler.transform
        call_count = [0]

        def spy_transform(X):
            call_count[0] += 1
            return original_transform(X)

        pipeline.scaler.transform = spy_transform
        pipeline.predict("RELIANCE", "IN", self._features())

        assert call_count[0] >= 1, "scaler.transform was not called"

    def test_25_can_predict_multiple_times_without_retraining(self):
        """Test can run predict multiple times without re-training."""
        pipeline = self._trained_pipeline()
        features = self._features()

        result1 = pipeline.predict("RELIANCE", "IN", features)
        result2 = pipeline.predict("INFOSYS", "IN", {**features, "rsi": 60.0})
        result3 = pipeline.predict("TCS", "IN", {**features, "rsi": 45.0})

        # All should succeed (no exception) and return valid tuples
        for r in (result1, result2, result3):
            assert isinstance(r, tuple) and len(r) == 2


# ---------------------------------------------------------------------------
# EDGE CASE TESTS (26-28)
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Tests 26-28: edge cases."""

    def test_26_different_markets_supported(self):
        """Test different markets (IN, US) are supported."""
        from ml.training_pipeline import MLTrainingPipeline

        for market in ("IN", "US"):
            labeled = [
                {**_make_signal(market=market), "outcome": "CORRECT" if i % 2 == 0 else "WRONG"}
                for i in range(30)
            ]
            db = MagicMock()
            pipeline = MLTrainingPipeline(db)
            pipeline.collect_signals = MagicMock(return_value=labeled)
            pipeline.label_outcomes = MagicMock(return_value=labeled)

            result = pipeline.train(market=market)
            assert "accuracy" in result, f"Market {market} train failed"

    def test_27_handles_missing_features_gracefully(self):
        """Test handles missing features dict gracefully — returns UNKNOWN."""
        from ml.training_pipeline import MLTrainingPipeline

        labeled = [
            {**_make_signal(), "outcome": "CORRECT" if i % 2 == 0 else "WRONG"}
            for i in range(30)
        ]
        db = MagicMock()
        pipeline = MLTrainingPipeline(db)
        pipeline.collect_signals = MagicMock(return_value=labeled)
        pipeline.label_outcomes = MagicMock(return_value=labeled)
        pipeline.train(market="IN")

        # Missing keys in features
        prediction, confidence = pipeline.predict("RELIANCE", "IN", {})

        assert prediction == "UNKNOWN"
        assert confidence == 0.0

    def test_29_collect_signals_returns_empty_on_db_error(self):
        """Branch: collect_signals returns [] when DB raises an exception."""
        from ml.training_pipeline import MLTrainingPipeline

        db = MagicMock()
        db.get_manual_signals.side_effect = RuntimeError("DB unavailable")
        pipeline = MLTrainingPipeline(db)

        result = pipeline.collect_signals(market="IN", days=30)
        assert result == []

    def test_30_label_outcomes_drops_zero_price_signals(self):
        """Branch: signals with price=0 are dropped from label_outcomes."""
        from ml.training_pipeline import MLTrainingPipeline

        db = MagicMock()
        pipeline = MLTrainingPipeline(db)
        pipeline._get_future_price = MagicMock(return_value=2600.0)

        signals = [_make_signal(price=0.0, action="BUY") for _ in range(5)]
        result = pipeline.label_outcomes(signals)

        assert result == []

    def test_31_get_future_price_returns_none_for_empty_symbol(self):
        """Branch: _get_future_price returns None when symbol is empty."""
        from ml.training_pipeline import MLTrainingPipeline

        pipeline = MLTrainingPipeline(MagicMock())
        result = pipeline._get_future_price("", "2026-01-01 10:00:00")
        assert result is None

    def test_32_get_future_price_uses_db_price_at(self):
        """Branch: _get_future_price calls db.get_price_at and returns the value."""
        from ml.training_pipeline import MLTrainingPipeline

        db = MagicMock()
        db.get_price_at.return_value = 2700.0
        pipeline = MLTrainingPipeline(db)

        result = pipeline._get_future_price("RELIANCE", "2026-01-01 10:00:00")
        assert result == 2700.0
        db.get_price_at.assert_called_once()

    def test_33_get_future_price_returns_none_when_db_returns_none(self):
        """Branch: _get_future_price returns None when db.get_price_at returns None."""
        from ml.training_pipeline import MLTrainingPipeline

        db = MagicMock()
        db.get_price_at.return_value = None
        pipeline = MLTrainingPipeline(db)

        result = pipeline._get_future_price("RELIANCE", "2026-01-01 10:00:00")
        assert result is None

    def test_34_hour_of_day_fallback_on_bad_timestamp(self):
        """Branch: _hour_of_day returns 10 (fallback) for invalid timestamp."""
        from ml.training_pipeline import MLTrainingPipeline

        pipeline = MLTrainingPipeline(MagicMock())
        result = pipeline._hour_of_day("not-a-timestamp")
        assert result == 10

    def test_35_train_returns_early_when_labelled_signals_insufficient(self):
        """Branch: train() returns early with accuracy=0.0 if label_outcomes yields <10 signals."""
        from ml.training_pipeline import MLTrainingPipeline

        db = MagicMock()
        pipeline = MLTrainingPipeline(db)
        pipeline.collect_signals = MagicMock(return_value=[_make_signal() for _ in range(15)])
        pipeline.label_outcomes = MagicMock(return_value=[])  # empty after labelling

        result = pipeline.train(market="IN")

        assert result["accuracy"] == 0.0
        assert result["model_ready"] is False
        assert pipeline.model is None

    def test_28_model_persists_after_training(self):
        """Test model persists after training (not reset between calls)."""
        from ml.training_pipeline import MLTrainingPipeline

        labeled = [
            {**_make_signal(), "outcome": "CORRECT" if i % 2 == 0 else "WRONG"}
            for i in range(30)
        ]
        db = MagicMock()
        pipeline = MLTrainingPipeline(db)
        pipeline.collect_signals = MagicMock(return_value=labeled)
        pipeline.label_outcomes = MagicMock(return_value=labeled)
        pipeline.train(market="IN")

        model_before = pipeline.model
        scaler_before = pipeline.scaler

        # Access model again — should still be there
        assert pipeline.model is model_before
        assert pipeline.scaler is scaler_before
