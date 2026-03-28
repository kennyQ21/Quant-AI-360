"""
ML Dataset Builder
Constructs supervised-learning datasets from historical market data.
Target: binary classification — will price increase in the next N days?
"""
import sys
from pathlib import Path
import pandas as pd
import logging
from typing import Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.data_service.market_data import load_data
from phase3_ml.features import build_ml_features, FEATURE_COLUMNS

logger = logging.getLogger(__name__)


# ── Target construction ────────────────────────────────────────────────────

def add_target(df: pd.DataFrame, horizons: list = [5, 10, 15], buy_threshold: float = 0.02, sell_threshold: float = -0.02, target_horizon: int = 5) -> pd.DataFrame:
    """
    Add multiple ternary target columns.
    
    Creates:
    - 'future_return_Nd'
    - 'target_Nd' (1 for BUY, -1 for SELL, 0 for HOLD)
    
    For ML compatibility with existing functions, 'target' will default to 'target_{target_horizon}d'.
    """
    df = df.copy()
    
    for h in horizons:
        ret_col = f"future_return_{h}d"
        tgt_col = f"target_{h}d"
        
        # Calculate forward return
        # Use Open of next day to avoid overnight gap leakage
        df[ret_col] = (df["Close"].shift(-h) - df["Open"].shift(-1)) / df["Open"].shift(-1)
        
        # Convert to classification
        df[tgt_col] = 0 # HOLD
        df.loc[df[ret_col] > buy_threshold, tgt_col] = 1 # BUY
        df.loc[df[ret_col] < sell_threshold, tgt_col] = -1 # SELL
        
        logger.info(f"Target distribution ({h}d): BUY={int((df[tgt_col]==1).sum())} SELL={int((df[tgt_col]==-1).sum())} HOLD={int((df[tgt_col]==0).sum())}")
    
    # Set default target
    if f"target_{target_horizon}d" in df.columns:
        df["target"] = df[f"target_{target_horizon}d"]
        
    df = df.dropna(subset=[f"target_{h}d" for h in horizons])
    return df


# ── Time-series split ──────────────────────────────────────────────────────

def time_series_split(
    df: pd.DataFrame,
    train_end: str = "2020-12-31",
    val_end: str = "2022-12-31",
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split into train / validation / test respecting temporal order.

    Args:
        df: DataFrame with a DatetimeIndex or 'Date' column.
        train_end: Last date in training set (inclusive).
        val_end: Last date in validation set (inclusive).

    Returns:
        (train_df, val_df, test_df)
    """
    # Ensure we have a datetime index
    if "Date" in df.columns:
        df = df.set_index("Date")
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    train = df[df.index <= train_end]
    val = df[(df.index > train_end) & (df.index <= val_end)]
    test = df[df.index > val_end]

    logger.info(
        f"Split → train={len(train)} val={len(val)} test={len(test)}  "
        f"[..{train_end} | ..{val_end} | rest]"
    )
    return train, val, test


# ── Full dataset builder ──────────────────────────────────────────────────

def build_ml_dataset(
    symbol: str,
    horizon: int = 5,
    train_end: str = "2020-12-31",
    val_end: str = "2022-12-31",
) -> Tuple[
    pd.DataFrame, pd.Series,
    pd.DataFrame, pd.Series,
    pd.DataFrame, pd.Series,
]:
    """
    End-to-end dataset construction for one stock.

    Returns:
        (X_train, y_train, X_val, y_val, X_test, y_test)
        Feature DataFrames contain only FEATURE_COLUMNS.
    """
    logger.info(f"Building ML dataset for {symbol} ...")

    # Load raw OHLCV
    raw = load_data(symbol)
    if raw.empty:
        raise ValueError(f"No data found for {symbol}")

    # Ensure Date is accessible
    if "Date" not in raw.columns and raw.index.name != "Date":
        raw = raw.reset_index()
        if "index" in raw.columns:
            raw = raw.rename(columns={"index": "Date"})

    # Features
    featured = build_ml_features(raw, symbol=symbol)

    # Target
    featured = add_target(featured, target_horizon=horizon)


    # Keep only available feature columns + target + Date
    keep_cols = [c for c in FEATURE_COLUMNS if c in featured.columns]
    extra = ["target"]
    if "Date" in featured.columns:
        extra.append("Date")
    featured = featured[keep_cols + extra].dropna()

    # Split
    train, val, test = time_series_split(featured, train_end, val_end)

    def _xy(part: pd.DataFrame):
        avail = [c for c in FEATURE_COLUMNS if c in part.columns]
        X = part[avail]
        y = part["target"]
        return X, y

    X_train, y_train = _xy(train)
    X_val, y_val = _xy(val)
    X_test, y_test = _xy(test)

    logger.info(
        f"Dataset ready — features={len(keep_cols)} | "
        f"train={len(X_train)} val={len(X_val)} test={len(X_test)}"
    )
    return X_train, y_train, X_val, y_val, X_test, y_test


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    X_tr, y_tr, X_v, y_v, X_te, y_te = build_ml_dataset("RELIANCE.NS")
    print(f"\nFeatures: {list(X_tr.columns)}")
    print(f"Train shape: {X_tr.shape}")
    print(f"Target balance (train): {y_tr.value_counts().to_dict()}")


# ── Multi-horizon label comparison ────────────────────────────────────────

def label_comparison_report(df: pd.DataFrame, horizons: list = None) -> pd.DataFrame:
    """
    Compare class balance and average forward return for each holding horizon.

    Returns a DataFrame with BUY/HOLD/SELL counts and avg returns for each
    horizon so you can empirically pick the best target_horizon before training.
    """
    if horizons is None:
        horizons = [5, 10, 15]

    df = df.copy()
    rows = []
    for h in horizons:
        ret_col = f"future_return_{h}d"
        tgt_col = f"target_{h}d"
        df[ret_col] = df["Close"].shift(-h) / df["Close"] - 1
        df[tgt_col] = 0
        df.loc[df[ret_col] > 0.02, tgt_col] = 1
        df.loc[df[ret_col] < -0.02, tgt_col] = -1
        clean = df.dropna(subset=[ret_col])
        total = len(clean)
        for cls, name in [(-1, "SELL"), (0, "HOLD"), (1, "BUY")]:
            mask = clean[tgt_col] == cls
            cnt = int(mask.sum())
            avg_ret = float(clean.loc[mask, ret_col].mean()) if cnt > 0 else 0.0
            rows.append({
                "horizon": h, "class": name, "count": cnt,
                "pct": round(cnt / total * 100, 1) if total > 0 else 0.0,
                "avg_return_pct": round(avg_ret * 100, 3),
            })

    report = pd.DataFrame(rows)
    logger.info(f"\nLabel comparison:\n{report.to_string()}")
    return report


# ── Trade-outcome labels ──────────────────────────────────────────────────

def add_trade_outcome_target(
    df: pd.DataFrame,
    atr_col: str = "ATR_14",
    atr_multiplier_sl: float = 1.5,
    rr_ratio: float = 2.0,
    max_bars: int = 15,
) -> pd.DataFrame:
    """
    Simulate the actual trade (T+1 entry, ATR stop, 2R target) and label
    each row based on whether TP or SL was hit first within max_bars.

    Labels: 1 = TP hit (BUY), -1 = SL hit (SELL), 0 = expired (HOLD).
    Column added: 'trade_outcome'
    """
    df = df.copy()
    n = len(df)
    labels = [0] * n

    close_arr = df["Close"].to_numpy()
    high_arr = df["High"].to_numpy()
    low_arr = df["Low"].to_numpy()
    open_arr = df["Open"].to_numpy()
    atr_arr = df[atr_col].to_numpy() if atr_col in df.columns else None

    for i in range(n - 1):
        entry = float(open_arr[i + 1])
        atr_val = (float(atr_arr[i]) if atr_arr is not None and not pd.isna(atr_arr[i])
                   else entry * 0.02)
        stop_dist = atr_val * atr_multiplier_sl
        sl = entry - stop_dist
        tp = entry + stop_dist * rr_ratio

        outcome = 0
        for j in range(i + 1, min(i + 1 + max_bars, n)):
            h = float(high_arr[j])
            l = float(low_arr[j])
            if h >= tp and l > sl:
                outcome = 1      # TP hit before SL
                break
            elif l <= sl:
                outcome = -1     # SL hit (or both hit same bar → conservative)
                break

        labels[i] = outcome

    df["trade_outcome"] = labels
    buy = int((df["trade_outcome"] == 1).sum())
    sell = int((df["trade_outcome"] == -1).sum())
    hold = int((df["trade_outcome"] == 0).sum())
    logger.info(f"Trade-outcome labels: BUY={buy} SELL={sell} HOLD={hold}")
    return df

