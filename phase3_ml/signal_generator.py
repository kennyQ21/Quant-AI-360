"""
ML Signal Generator
Converts ensemble probabilities → BUY / SELL / HOLD with risk filters.
Output is compatible with the existing Backtester strategy interface.
"""
import logging
import numpy as np
import pandas as pd
from typing import List

logger = logging.getLogger(__name__)


def generate_ml_signals(
    df: pd.DataFrame,
    probabilities: np.ndarray,
    buy_threshold: float = 0.6,
    sell_threshold: float = 0.4,
    use_trend_filter: bool = True,
    use_volatility_filter: bool = True,
    atr_extreme_mult: float = 2.0,
) -> List[str]:
    """
    Convert ML probabilities into trading signals with risk filters.

    Args:
        df: DataFrame with OHLCV + indicators (must include SMA_200, ATR_14, Close).
        probabilities: Array of P(price goes up) from ensemble model.
        buy_threshold: Probability above which to signal BUY.
        sell_threshold: Probability below which to signal SELL.
        use_trend_filter: If True, suppress BUY when price < SMA_200.
        use_volatility_filter: If True, go HOLD during extreme ATR periods.
        atr_extreme_mult: Multiplier over rolling-mean ATR to flag extreme volatility.

    Returns:
        List[str] of 'BUY', 'SELL', 'HOLD' — one per row in `df`.
    """
    n = len(df)

    # Ensure probabilities align with dataframe length
    if len(probabilities) < n:
        # Pad front with 0.5 (neutral)
        pad = np.full(n - len(probabilities), 0.5)
        probabilities = np.concatenate([pad, probabilities])
    elif len(probabilities) > n:
        probabilities = probabilities[:n]

    # Pre-compute filter columns
    close = df["Close"].values if "Close" in df.columns else np.zeros(n)
    sma_200 = df["SMA_200"].values if "SMA_200" in df.columns else close
    atr = df["ATR_14"].values if "ATR_14" in df.columns else np.zeros(n)
    atr_mean = pd.Series(atr).rolling(50, min_periods=1).mean().values

    signals: List[str] = []
    for i in range(n):
        prob = probabilities[i]

        # Base signal from probability
        if prob > buy_threshold:
            signal = "BUY"
        elif prob < sell_threshold:
            signal = "SELL"
        else:
            signal = "HOLD"

        # ── Risk Filter 1: Trend ──────────────────────────────────────
        if use_trend_filter and signal == "BUY":
            if not np.isnan(sma_200[i]) and close[i] < sma_200[i]:
                signal = "HOLD"  # don't buy against the trend

        # ── Risk Filter 2: Volatility ────────────────────────────────
        if use_volatility_filter and signal != "HOLD":
            if atr_mean[i] > 0 and atr[i] > atr_extreme_mult * atr_mean[i]:
                signal = "HOLD"  # avoid extreme volatility periods

        signals.append(signal)

    # Stats
    buy_count = signals.count("BUY")
    sell_count = signals.count("SELL")
    hold_count = signals.count("HOLD")
    logger.info(
        f"ML Signals: BUY={buy_count} SELL={sell_count} HOLD={hold_count} "
        f"(total={n})"
    )

    return signals
