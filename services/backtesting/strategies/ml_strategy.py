"""
ML Ensemble Strategy (v3 — Phase 3.6 with advanced alpha factors)
Leak-free: HOLD on training period + 1-day trade delay.
Uses the centralized feature builder for ~50 features.
"""
import sys
from pathlib import Path
import logging
import pandas as pd
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from phase3_ml.features import build_ml_features, FEATURE_COLUMNS
from phase3_ml.ensemble import EnsemblePredictor
from phase3_ml.signal_generator import generate_ml_signals

logger = logging.getLogger(__name__)

# Module-level cache
_cached_ensemble: EnsemblePredictor = None
_cached_train_end_idx: int = 0


def _ensure_trained(df: pd.DataFrame, train_ratio: float = 0.7) -> EnsemblePredictor:
    """
    Train ensemble on first `train_ratio` of data.
    Records train_end_idx so we know where OOS starts.
    """
    global _cached_ensemble, _cached_train_end_idx
    if _cached_ensemble is not None:
        return _cached_ensemble

    # Build full feature set (Phase 1 + 3 + 3.6)
    featured = build_ml_features(df)

    # Build target
    featured["future_return"] = featured["Close"].shift(-5) / featured["Close"] - 1
    featured["target"] = (featured["future_return"] > 0).astype(int)

    avail = [c for c in FEATURE_COLUMNS if c in featured.columns]
    clean = featured[avail + ["target"]].dropna()

    if len(clean) < 50:
        logger.warning(f"Only {len(clean)} clean rows — using minimal split")
        split_idx = max(1, len(clean) - 10)
    else:
        split_idx = int(len(clean) * train_ratio)

    X_train = clean.iloc[:split_idx][avail]
    y_train = clean.iloc[:split_idx]["target"]

    # Record training boundary
    _cached_train_end_idx = clean.index[split_idx - 1] if split_idx > 0 else 0

    logger.info(
        f"ML Strategy: training on {len(X_train)} rows, "
        f"OOS starts at index {_cached_train_end_idx} "
        f"({len(avail)} features)"
    )

    ensemble = EnsemblePredictor()
    ensemble.train_all(X_train, y_train)
    _cached_ensemble = ensemble
    return ensemble


def ml_ensemble_strategy(df: pd.DataFrame) -> List[str]:
    """
    ML Ensemble strategy — leak-free, with trade delay, ~50 features.

    Safeguards:
      1. HOLD on entire training period (no in-sample signals)
      2. 1-day trade delay: signal at t → execution at t+1
      3. Only OOS predictions used for trading

    Args:
        df: DataFrame with OHLCV + indicator columns.

    Returns:
        List[str] of 'BUY', 'SELL', 'HOLD' — one per row.
    """
    ensemble = _ensure_trained(df)

    # Build features for the full dataset
    featured = build_ml_features(df)
    avail = [c for c in FEATURE_COLUMNS if c in featured.columns]
    X_full = featured[avail].fillna(0)

    # Predict probabilities
    probs = ensemble.predict_proba(X_full)

    # Generate raw signals with risk filters
    raw_signals = generate_ml_signals(
        featured, probs,
        buy_threshold=0.6,
        sell_threshold=0.4,
        use_trend_filter=True,
        use_volatility_filter=True,
    )

    # ── Safeguard 1: HOLD on training period ─────────────────────────
    for i in range(len(raw_signals)):
        idx = df.index[i] if i < len(df) else i
        if idx <= _cached_train_end_idx:
            raw_signals[i] = "HOLD"

    # ── Safeguard 2: 1-day trade delay ───────────────────────────────
    delayed_signals = ["HOLD"] + raw_signals[:-1]

    # Ensure output length matches input
    if len(delayed_signals) < len(df):
        delayed_signals = ["HOLD"] * (len(df) - len(delayed_signals)) + delayed_signals
    elif len(delayed_signals) > len(df):
        delayed_signals = delayed_signals[:len(df)]

    # Stats
    oos_signals = delayed_signals[_cached_train_end_idx + 1:] if _cached_train_end_idx < len(delayed_signals) else delayed_signals
    buy_count = oos_signals.count("BUY")
    sell_count = oos_signals.count("SELL")
    hold_count = oos_signals.count("HOLD")
    logger.info(
        f"ML Strategy (OOS only): BUY={buy_count} SELL={sell_count} HOLD={hold_count} "
        f"(training period={_cached_train_end_idx + 1} rows → HOLD)"
    )

    return delayed_signals


def reset_cache():
    """Reset the cached ensemble (use when switching symbols)."""
    global _cached_ensemble, _cached_train_end_idx
    _cached_ensemble = None
    _cached_train_end_idx = 0
