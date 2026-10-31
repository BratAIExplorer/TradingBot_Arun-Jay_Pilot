"""
ml/training_pipeline.py — MLTrainingPipeline

AI Training Pipeline for Orbit Trading.
Learns from manually-labelled human trades to predict trade quality.

Principles:
- SIMPLE:    5 public methods, clear names, no magic
- SMART:     GradientBoostingClassifier + StandardScaler, probability confidence
- SECURE:    Zero credentials; reads only from TradesDatabase
- RESPECTFUL: Returns ("UNKNOWN", 0.0) on any error — never crashes the caller
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler

if TYPE_CHECKING:
    from database.trades_db import TradesDatabase

logger = logging.getLogger(__name__)

# Feature names — order matters for build_features() and predict()
FEATURE_NAMES = ["rsi", "volume", "ma_20", "ma_50", "market_trend", "hour_of_day", "market_code"]

# Market code mapping for numeric encoding
MARKET_CODES: dict[str, int] = {"IN": 0, "US": 1}

# Thresholds
SKIP_MOVE_THRESHOLD = 0.03   # 3%: price move that makes a SKIP "WRONG"
SKIP_FLAT_THRESHOLD = 0.01   # 1%: price move that keeps a SKIP "CORRECT"
ACCURACY_THRESHOLD = 0.70    # minimum accuracy for model_ready=True
MIN_SIGNALS = 10             # minimum signals required


class MLTrainingPipeline:
    """
    End-to-end ML pipeline: collect → label → build features → train → predict.

    Usage:
        pipeline = MLTrainingPipeline(db)
        pipeline.train(market='IN')
        prediction, confidence = pipeline.predict('RELIANCE', 'IN', features)
    """

    def __init__(self, db: "TradesDatabase") -> None:
        self.db = db
        self.model: GradientBoostingClassifier | None = None
        self.scaler: StandardScaler | None = None
        self.model_ready: bool = False

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def collect_signals(
        self,
        market: str = "IN",
        days: int = 30,
        limit: int = 10_000,
    ) -> list[dict]:
        """
        Fetch MANUAL human trades for ``market`` from the last ``days`` days.

        Returns empty list if fewer than MIN_SIGNALS remain after filtering.
        """
        try:
            cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            raw: list[dict] = self.db.get_manual_signals(
                since=cutoff, limit=limit
            )
        except Exception as exc:
            logger.error("collect_signals: DB error — %s", exc)
            return []

        filtered = [
            s for s in raw
            if s.get("source") == "MANUAL" and s.get("market") == market
        ]

        if len(filtered) < MIN_SIGNALS:
            logger.info(
                "collect_signals: only %d signals after filtering (need %d) — returning []",
                len(filtered),
                MIN_SIGNALS,
            )
            return []

        return filtered

    def label_outcomes(self, signals: list[dict]) -> list[dict]:
        """
        Attach an ``outcome`` key ('CORRECT' | 'WRONG') to each signal by
        comparing entry price to the price ~1 day later.

        Signals whose future price cannot be determined are dropped.
        Returns [] if no signal can be labelled.
        """
        labelled: list[dict] = []

        for sig in signals:
            future_price = self._get_future_price(sig.get("symbol", ""), sig.get("timestamp", ""))
            if future_price is None:
                continue

            entry_price: float = float(sig.get("price", 0) or 0)
            if entry_price == 0:
                continue

            action: str = (sig.get("action") or "BUY").upper()
            outcome = self._label_one(action, entry_price, future_price)
            labelled.append({**sig, "outcome": outcome})

        return labelled

    def build_features(self, signals: list[dict]) -> tuple[np.ndarray, np.ndarray]:
        """
        Convert labelled signals into sklearn-ready (X, y) arrays.

        X shape: (n, 7)  — features per FEATURE_NAMES
        y shape: (n,)    — 1 = CORRECT, 0 = WRONG

        Raises ValueError if fewer than MIN_SIGNALS provided.
        """
        if len(signals) < MIN_SIGNALS:
            raise ValueError(
                f"Need at least {MIN_SIGNALS} signals to build features, got {len(signals)}"
            )

        rows: list[list[float]] = []
        labels: list[int] = []

        for sig in signals:
            row = self._extract_feature_row(sig)
            rows.append(row)
            labels.append(1 if sig.get("outcome") == "CORRECT" else 0)

        return np.array(rows, dtype=np.float64), np.array(labels, dtype=np.int32)

    def train(self, market: str = "IN") -> dict:
        """
        Full training cycle for ``market``.

        1. collect_signals
        2. label_outcomes
        3. build_features
        4. fit GradientBoostingClassifier + StandardScaler
        5. evaluate accuracy on training set

        Returns dict with keys: accuracy, signals_used, model_ready, timestamp.
        """
        signals = self.collect_signals(market=market)
        labelled = self.label_outcomes(signals)

        if len(labelled) < MIN_SIGNALS:
            logger.warning("train: not enough labelled signals (%d) for market=%s", len(labelled), market)
            return {
                "accuracy": 0.0,
                "signals_used": 0,
                "model_ready": False,
                "timestamp": datetime.now().isoformat(),
            }

        try:
            X, y = self.build_features(labelled)
        except ValueError as exc:
            logger.warning("train: build_features error — %s", exc)
            return {
                "accuracy": 0.0,
                "signals_used": len(labelled),
                "model_ready": False,
                "timestamp": datetime.now().isoformat(),
            }

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.1,
            random_state=42,
        )
        model.fit(X_scaled, y)

        # Training-set accuracy (used as proxy; for small datasets cross-val is too slow)
        accuracy: float = float(model.score(X_scaled, y))
        model_ready = accuracy > ACCURACY_THRESHOLD

        self.model = model
        self.scaler = scaler
        self.model_ready = model_ready

        logger.info(
            "train: market=%s signals=%d accuracy=%.2f model_ready=%s",
            market,
            len(labelled),
            accuracy,
            model_ready,
        )

        return {
            "accuracy": round(accuracy, 4),
            "signals_used": len(labelled),
            "model_ready": model_ready,
            "timestamp": datetime.now().isoformat(),
        }

    def predict(
        self,
        symbol: str,
        market: str,
        features: dict,
    ) -> tuple[str, float]:
        """
        Predict trade quality for a given symbol + feature dict.

        Returns:
            ("GOOD_TRADE", confidence)  — model says take the trade
            ("SKIP_TRADE", confidence)  — model says skip
            ("UNKNOWN", 0.0)            — model not trained or features incomplete
        """
        if self.model is None or self.scaler is None:
            return ("UNKNOWN", 0.0)

        try:
            row = self._extract_feature_row(features)
        except (KeyError, TypeError, ValueError):
            return ("UNKNOWN", 0.0)

        # Check all features present (row should have exactly 7 numeric values)
        if any(v is None for v in row):
            return ("UNKNOWN", 0.0)

        try:
            X = np.array([row], dtype=np.float64)
            X_scaled = self.scaler.transform(X)
            proba = self.model.predict_proba(X_scaled)[0]  # [p_wrong, p_correct]
            confidence = float(proba[1])  # probability of class 1 (CORRECT)
            prediction = "GOOD_TRADE" if confidence >= 0.5 else "SKIP_TRADE"
            return (prediction, round(confidence, 4))
        except Exception as exc:
            logger.error("predict: error for symbol=%s — %s", symbol, exc)
            return ("UNKNOWN", 0.0)

    # ------------------------------------------------------------------
    # HELPER METHODS
    # ------------------------------------------------------------------

    def _get_future_price(self, symbol: str, timestamp_str: str) -> float | None:
        """
        Look up the price of ``symbol`` approximately 1 trading day after ``timestamp_str``.

        In production this queries the DB or a price cache.
        Returns None if unavailable.
        """
        if not symbol or not timestamp_str:
            return None

        try:
            ts = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            future_ts = ts + timedelta(days=1)
            future_str = future_ts.strftime("%Y-%m-%d %H:%M:%S")

            # Ask the database for the close price at that time
            result = self.db.get_price_at(symbol=symbol, timestamp=future_str)
            if result is None:
                return None
            return float(result)
        except Exception as exc:
            logger.debug("_get_future_price: %s — %s", symbol, exc)
            return None

    def _hour_of_day(self, timestamp_str: str) -> int:
        """Extract hour (0-23) from a 'YYYY-MM-DD HH:MM:SS' string."""
        try:
            return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").hour
        except (ValueError, TypeError):
            return 10  # market open fallback

    def _label_one(self, action: str, entry_price: float, future_price: float) -> str:
        """
        Assign CORRECT / WRONG label for a single trade.

        BUY:  future > entry → CORRECT
        SELL: future < entry → CORRECT
        SKIP: |move| <= SKIP_FLAT_THRESHOLD → CORRECT,
              |move| > SKIP_MOVE_THRESHOLD  → WRONG
        """
        pct_change = (future_price - entry_price) / entry_price

        if action == "BUY":
            return "CORRECT" if pct_change > 0 else "WRONG"

        if action == "SELL":
            return "CORRECT" if pct_change < 0 else "WRONG"

        # SKIP
        abs_change = abs(pct_change)
        if abs_change <= SKIP_FLAT_THRESHOLD:
            return "CORRECT"
        if abs_change > SKIP_MOVE_THRESHOLD:
            return "WRONG"
        # between thresholds — call it WRONG (missed opportunity)
        return "WRONG"

    def _extract_feature_row(self, sig: dict) -> list[float]:
        """
        Build a 7-element feature vector from a signal/features dict.

        Order matches FEATURE_NAMES:
          [rsi, volume, ma_20, ma_50, market_trend, hour_of_day, market_code]

        Raises KeyError if any required feature is missing from ``sig``
        when called from predict() with an incomplete dict.
        """
        required = {"rsi", "volume", "ma_20", "ma_50"}
        if not required.issubset(sig.keys()):
            raise KeyError(f"Missing required features: {required - sig.keys()}")

        rsi = float(sig["rsi"])
        volume = float(sig["volume"])
        ma_20 = float(sig.get("ma_20", sig.get("ma20", 0)) or 0)
        ma_50 = float(sig.get("ma_50", sig.get("ma50", 0)) or 0)

        # market_trend: ratio of ma_20/ma_50 (>1 = uptrend, <1 = downtrend)
        market_trend = (ma_20 / ma_50) if ma_50 != 0 else 1.0
        if "market_trend" in sig:
            market_trend = float(sig["market_trend"])

        hour = self._hour_of_day(sig.get("timestamp", ""))
        if "hour_of_day" in sig:
            hour = int(sig["hour_of_day"])

        market = sig.get("market", "IN")
        market_code = float(MARKET_CODES.get(market, 0))
        if "market_code" in sig:
            market_code = float(sig["market_code"])

        return [rsi, volume, ma_20, ma_50, market_trend, float(hour), market_code]
