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

def add_target(df: pd.DataFrame, horizon: int = 5) -> pd.DataFrame:
    """
    Add binary target column.

    target = 1  if Close shifts up over the next `horizon` days
    target = 0  otherwise

    The last `horizon` rows will have NaN targets and are dropped.
    """
    df = df.copy()
    df["future_return"] = df["Close"].shift(-horizon) / df["Close"] - 1
    df["target"] = (df["future_return"] > 0).astype(int)
    df = df.dropna(subset=["target"])
    logger.info(
        f"Target distribution (horizon={horizon}d): "
        f"UP={int(df['target'].sum())}  DOWN={int((1 - df['target']).sum())}"
    )
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
    featured = build_ml_features(raw)

    # Target
    featured = add_target(featured, horizon=horizon)

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
