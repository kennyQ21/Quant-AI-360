"""
ML Feature Engineering (Phase 3.6 — Advanced Alpha Factors)
~50 features: base indicators + momentum + volatility + volume + mean reversion
+ market context (NIFTY, India VIX) + cross-sectional ranks + trend factors.
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))
from services.feature_service.indicators import (
    add_features_to_data,
)

logger = logging.getLogger(__name__)

# ── Master feature list ───────────────────────────────────────────────────
# Phase 1 core indicators
_PHASE1_FEATURES = [
    "RSI_14", "MACD", "MACD_Signal", "MACD_Hist", "ATR_14",
    "BB_Upper", "BB_Lower", "SMA_20", "SMA_50", "EMA_12", "EMA_26", "Returns",
]

# Phase 3 expanded features
_PHASE3_FEATURES = [
    "Returns_5d", "Returns_10d", "Momentum_10", "Momentum_20",
    "Volatility_20", "Volume_Ratio", "BB_Pct_B", "RSI_Norm",
    "SMA_200", "EMA_20", "Price_to_SMA20", "Price_to_SMA50", "Price_to_SMA200",
    "MACD_Hist_Norm", "ATR_Pct",
]

# Phase 3.6 — hedge fund alpha factors
_MOMENTUM_FEATURES = [
    "Mom_1m", "Mom_3m", "Mom_6m", "Mom_12m", "Rev_5d",
]
_VOLATILITY_FEATURES = [
    "Vol_20", "Vol_Ratio", # ATR_Pct already in Phase 3
]
_VOLUME_FEATURES = [
    # Volume_Ratio already in Phase 3
    "Vol_Mom_5d", "PVT",
]
_MEAN_REVERSION_FEATURES = [
    "Dist_SMA50", "BB_Width", "ZScore_20",
]
_MARKET_CONTEXT_FEATURES = [
    "Nifty_Mom_1m", "India_VIX", "Market_Trend",
]
_CROSS_SECTIONAL_FEATURES = [
    # These are computed across stocks — added during portfolio building
    # Included here so the ensemble can use them if available
    "Rank_Mom_3m", "Rank_Vol_20", "Rank_Volume", "Rank_RSI", "Rank_ATR",
]
_TREND_FEATURES = [
    "MA_Slope_50", "Trend_Strength", "Price_Accel",
]
_STRATEGY_FEATURES = [
    "liquidity_sweep_detected", "sweep_direction",
    "fvg_present", "fvg_direction", "price_inside_fvg",
    "structure_trend", "bos_detected",
    "amd_phase", "vcp_detected", "vcp_contraction_count",
    "breakout_detected", "base_length_days", "confluence_score"
]

# Phase 4 interaction features (SMC combo signals)
_INTERACTION_FEATURES = [
    "sweep_and_fvg",       # core Tier1 combo
    "vcp_and_bullish",     # VCP in confirmed uptrend
    "bos_and_sweep",       # BOS confirmed by sweep = high conviction
    "fvg_aligned",         # FVG direction matches market structure
    "tier1_full_setup",    # complete Tier1 triforce
    "confluence_high",     # binary: score >= 75
    "Mom_3m_rank_zscore",  # z-scored 3-month momentum
    "ATR_regime",          # 1 if ATR > 30d median (high-vol regime)
]

# Full list (order matters for consistent training)
FEATURE_COLUMNS = (
    _PHASE1_FEATURES
    + _PHASE3_FEATURES
    + _MOMENTUM_FEATURES
    + _VOLATILITY_FEATURES
    + _VOLUME_FEATURES
    + _MEAN_REVERSION_FEATURES
    + _MARKET_CONTEXT_FEATURES
    + _TREND_FEATURES
    + _CROSS_SECTIONAL_FEATURES
    + _STRATEGY_FEATURES
    + _INTERACTION_FEATURES
)


# ── Market data cache ────────────────────────────────────────────────────
_market_cache: dict = {}


def _load_market_data() -> dict:
    """Load and cache NIFTY 50 + India VIX for market context features."""
    global _market_cache
    if _market_cache:
        return _market_cache

    try:
        import yfinance as yf

        nifty = yf.download("^NSEI", period="10y", interval="1d", progress=False)
        if isinstance(nifty.columns, pd.MultiIndex):
            nifty.columns = nifty.columns.get_level_values(0)
        if not nifty.empty:
            _market_cache["nifty_close"] = nifty["Close"].squeeze()
            logger.info(f"Loaded NIFTY data: {len(nifty)} rows")

        vix = yf.download("^INDIAVIX", period="10y", interval="1d", progress=False)
        if isinstance(vix.columns, pd.MultiIndex):
            vix.columns = vix.columns.get_level_values(0)
        if not vix.empty:
            _market_cache["vix_close"] = vix["Close"].squeeze()
            logger.info(f"Loaded India VIX data: {len(vix)} rows")

    except Exception as e:
        logger.warning(f"Could not load market context data: {e}")

    return _market_cache


# ── Flatten helper ────────────────────────────────────────────────────────

def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Flatten MultiIndex columns from yfinance."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    for col in df.columns:
        if hasattr(df[col], "ndim") and df[col].ndim > 1:
            df[col] = df[col].iloc[:, 0]
    return df


# ── Main feature builder ─────────────────────────────────────────────────

def build_ml_features(df: pd.DataFrame, symbol: str = None, add_market_context: bool = True) -> pd.DataFrame:
    """
    Build ~50 ML features from OHLCV data.

    Categories:
        1. Phase-1 core indicators (12)
        2. Phase-3 expanded features (15)
        3. Momentum factors (5)
        4. Volatility factors (2)
        5. Volume factors (2)
        6. Mean reversion signals (3)
        7. Market context (3) — NIFTY + India VIX
        8. Trend factors (3)
        9. Cross-sectional ranks (5) — stub, populated during portfolio building
        10. Strategy features (13) — SMC, AMD, VCP, etc.
    """
    df = df.copy()

    # ── Phase 1 indicators ────────────────────────────────────────────
    df = add_features_to_data(df)
    df = _flatten_columns(df)

    close = df["Close"]
    returns = df.get("Returns", close.pct_change())
    if "Returns" not in df.columns:
        df["Returns"] = returns

    # ── Phase 3 expanded ──────────────────────────────────────────────
    df["Returns_5d"] = close.pct_change(5)
    df["Returns_10d"] = close.pct_change(10)
    df["Momentum_10"] = close - close.shift(10)
    df["Momentum_20"] = close - close.shift(20)
    df["Volatility_20"] = returns.rolling(window=20).std()

    if "Volume" in df.columns:
        vol_ma = df["Volume"].rolling(window=20).mean()
        df["Volume_Ratio"] = df["Volume"] / vol_ma
    else:
        df["Volume_Ratio"] = 1.0

    bb_range = df["BB_Upper"] - df["BB_Lower"]
    df["BB_Pct_B"] = np.where(bb_range != 0, (close - df["BB_Lower"]) / bb_range, 0.5)
    df["RSI_Norm"] = df["RSI_14"] / 100.0
    df["SMA_200"] = close.rolling(200).mean()
    df["EMA_20"] = close.ewm(span=20, adjust=False).mean()
    df["Price_to_SMA20"] = close / df["SMA_20"]
    df["Price_to_SMA50"] = close / df["SMA_50"]
    df["Price_to_SMA200"] = close / df["SMA_200"]

    macd_abs_max = df["MACD_Hist"].abs().rolling(20).max()
    df["MACD_Hist_Norm"] = np.where(macd_abs_max != 0, df["MACD_Hist"] / macd_abs_max, 0.0)
    df["ATR_Pct"] = df["ATR_14"] / close

    # ── Phase 3.6: Momentum factors ───────────────────────────────────
    df["Mom_1m"] = close.pct_change(21)        # 1-month momentum
    df["Mom_3m"] = close.pct_change(63)        # 3-month momentum
    df["Mom_6m"] = close.pct_change(126)       # 6-month momentum
    df["Mom_12m"] = close.pct_change(252)      # 12-month momentum
    df["Rev_5d"] = -close.pct_change(5)        # 5-day reversal (mean reversion)

    # ── Volatility factors ────────────────────────────────────────────
    df["Vol_20"] = returns.rolling(20).std()    # realized vol (same as Volatility_20 but kept for naming)
    vol_long = returns.rolling(100).std()
    df["Vol_Ratio"] = np.where(vol_long != 0, df["Vol_20"] / vol_long, 1.0)

    # ── Volume factors ────────────────────────────────────────────────
    if "Volume" in df.columns:
        df["Vol_Mom_5d"] = df["Volume"].pct_change(5)
        # PVT as rolling z-score to avoid unbounded cumsum
        pvt_raw = (returns * df["Volume"]).cumsum()
        pvt_mean = pvt_raw.rolling(50, min_periods=1).mean()
        pvt_std = pvt_raw.rolling(50, min_periods=1).std()
        df["PVT"] = np.where(pvt_std != 0, (pvt_raw - pvt_mean) / pvt_std, 0.0)
    else:
        df["Vol_Mom_5d"] = 0.0
        df["PVT"] = 0.0

    # ── Mean reversion factors ────────────────────────────────────────
    df["Dist_SMA50"] = (close - df["SMA_50"]) / df["SMA_50"]
    df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / close
    rolling_mean_20 = close.rolling(20).mean()
    rolling_std_20 = close.rolling(20).std()
    df["ZScore_20"] = np.where(rolling_std_20 != 0, (close - rolling_mean_20) / rolling_std_20, 0.0)

    # ── Trend factors ─────────────────────────────────────────────────
    df["MA_Slope_50"] = df["SMA_50"].diff(5)
    sma_100 = close.rolling(100).mean()
    df["Trend_Strength"] = np.where(sma_100 != 0, (df["SMA_20"] - sma_100) / sma_100, 0.0)
    df["Price_Accel"] = df["Returns_5d"] - df["Returns_10d"]

    # ── Market context factors ────────────────────────────────────────
    if add_market_context:
        _add_market_context(df)
    else:
        df["Nifty_Mom_1m"] = 0.0
        df["India_VIX"] = 0.0
        df["Market_Trend"] = 1.0

    # ── Cross-sectional placeholders (populated in portfolio mode) ────
    for col in _CROSS_SECTIONAL_FEATURES:
        if col not in df.columns:
            df[col] = 0.5  # neutral rank until computed across stocks

    # ── Phase 4: Interaction features ─────────────────────────────────
    # These require the _STRATEGY_FEATURES columns to exist first.
    # If strategy features weren't generated (symbol=None path), they
    # default to 0, so the interaction features also default to 0.
    def _col(name: str, default=0) -> "pd.Series":
        return df[name].fillna(default) if name in df.columns else pd.Series(default, index=df.index)

    df["sweep_and_fvg"] = (_col("liquidity_sweep_detected") * _col("fvg_present")).astype(int)
    df["vcp_and_bullish"] = (_col("vcp_detected") * (_col("structure_trend") == 1)).astype(int)
    df["bos_and_sweep"] = (_col("bos_detected") * _col("liquidity_sweep_detected")).astype(int)
    df["fvg_aligned"] = (_col("fvg_direction") == _col("structure_trend")).astype(int)
    df["tier1_full_setup"] = (df["sweep_and_fvg"] & _col("bos_detected")).astype(int)
    df["confluence_high"] = (_col("confluence_score") >= 75).astype(int)

    # Z-scored 3m momentum (60-day rolling window)
    mom3 = df["Mom_3m"] if "Mom_3m" in df.columns else pd.Series(0.0, index=df.index)
    mom3_mean = mom3.rolling(60, min_periods=10).mean()
    mom3_std = mom3.rolling(60, min_periods=10).std()
    df["Mom_3m_rank_zscore"] = np.where(mom3_std != 0, (mom3 - mom3_mean) / mom3_std, 0.0)

    # ATR regime: 1 if current ATR > 30-day median
    if "ATR_14" in df.columns:
        atr_series = df["ATR_14"]
        atr_med = atr_series.rolling(30, min_periods=5).median()
        df["ATR_regime"] = (atr_series > atr_med).astype(float)
    else:
        df["ATR_regime"] = 0.0

    # ── Sanitize: replace inf and clip extreme values ─────────────────
    feature_cols = [c for c in FEATURE_COLUMNS if c in df.columns]
    for col in feature_cols:
        df[col] = df[col].replace([np.inf, -np.inf], np.nan)
        df[col] = df[col].clip(-10, 10)  # clip z-scores / ratios to sane range
    df[feature_cols] = df[feature_cols].fillna(0.0)

    total = len(feature_cols)
    logger.info(f"Built {total}/{len(FEATURE_COLUMNS)} ML features, shape={df.shape}")
    return df


def _add_market_context(df: pd.DataFrame) -> None:
    """Add NIFTY momentum, India VIX level, and market trend to df (in-place)."""
    market = _load_market_data()

    # Try to get a DatetimeIndex for alignment
    if isinstance(df.index, pd.DatetimeIndex):
        date_idx = df.index
    elif "Date" in df.columns:
        date_idx = pd.to_datetime(df["Date"])
    else:
        # Can't align — use defaults
        df["Nifty_Mom_1m"] = 0.0
        df["India_VIX"] = 0.0
        df["Market_Trend"] = 1.0
        return

    if "nifty_close" in market:
        nifty = market["nifty_close"].reindex(date_idx, method="ffill")
        df["Nifty_Mom_1m"] = nifty.pct_change(21).values
        nifty_sma200 = nifty.rolling(200).mean()
        df["Market_Trend"] = (nifty > nifty_sma200).astype(float).values
    else:
        df["Nifty_Mom_1m"] = 0.0
        df["Market_Trend"] = 1.0

    if "vix_close" in market:
        vix = market["vix_close"].reindex(date_idx, method="ffill")
        df["India_VIX"] = vix.values
    else:
        df["India_VIX"] = 0.0


def add_cross_sectional_ranks(all_stocks_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute cross-sectional ranks across stocks for each date.

    Args:
        all_stocks_df: DataFrame with 'symbol' column and all features.
                       Must have multiple stocks.

    Returns:
        DataFrame with Rank_* columns filled (0 to 1).
    """
    df = all_stocks_df.copy()

    rank_mappings = {
        "Rank_Mom_3m": "Mom_3m",
        "Rank_Vol_20": "Vol_20",
        "Rank_Volume": "Volume",
        "Rank_RSI": "RSI_14",
        "Rank_ATR": "ATR_14",
    }

    for rank_col, source_col in rank_mappings.items():
        if source_col in df.columns:
            df[rank_col] = df.groupby("Date")[source_col].rank(pct=True)
        else:
            df[rank_col] = 0.5
            
    # ── Strategy features ──────────────────────────────────────────────
    if symbol:
        try:
            from phase3_ml.strategy_features import generate_strategy_features
            strategy_feat_df = generate_strategy_features(df, symbol)
            
            # fill na with 0 just in case
            for col in _STRATEGY_FEATURES:
                if col in strategy_feat_df.columns:
                    df[col] = strategy_feat_df[col].fillna(0)
                else:
                    df[col] = 0
        except Exception as e:
            logger.warning(f"Failed to generate strategy features for {symbol}: {e}")
            for col in _STRATEGY_FEATURES:
                df[col] = 0
    else:
        for col in _STRATEGY_FEATURES:
            df[col] = 0

    return df


def get_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Extract only available feature columns, dropping NaN rows."""
    available = [c for c in FEATURE_COLUMNS if c in df.columns]
    missing = set(FEATURE_COLUMNS) - set(available)
    if missing:
        logger.warning(f"Missing feature columns ({len(missing)}): {missing}")
    return df[available].dropna()
