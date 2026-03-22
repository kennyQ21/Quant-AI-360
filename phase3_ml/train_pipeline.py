"""
Training Pipeline
End-to-end: data → features → train → predict → evaluate.
Supports walk-forward retraining for realistic simulation.
"""
import sys
from pathlib import Path
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.data_service.market_data import load_data
from phase3_ml.features import build_ml_features, FEATURE_COLUMNS
from phase3_ml.dataset_builder import add_target, build_ml_dataset
from phase3_ml.ensemble import EnsemblePredictor

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent.parent / "storage" / "ml_models"


# ── Single-window training ────────────────────────────────────────────────

def train_single(
    symbol: str,
    horizon: int = 5,
    train_end: str = "2020-12-31",
    val_end: str = "2022-12-31",
    save_models: bool = True,
) -> Tuple[EnsemblePredictor, Dict]:
    """
    Train all models for one symbol on a single window.

    Returns:
        (ensemble, results_dict)
    """

    X_train, y_train, X_val, y_val, X_test, y_test = build_ml_dataset(
        symbol, horizon=horizon, train_end=train_end, val_end=val_end
    )

    ensemble = EnsemblePredictor()
    train_results = ensemble.train_all(X_train, y_train)

    # Evaluate on validation set
    val_probs = ensemble.predict_proba(X_val)
    val_preds = (val_probs > 0.5).astype(int)
    val_acc = (val_preds == y_val.values).mean() if len(y_val) > 0 else 0.0

    # Evaluate on test set
    test_probs = ensemble.predict_proba(X_test)
    test_preds = (test_probs > 0.5).astype(int)
    test_acc = (test_preds == y_test.values).mean() if len(y_test) > 0 else 0.0

    results = {
        "symbol": symbol,
        "train_size": len(X_train),
        "val_size": len(X_val),
        "test_size": len(X_test),
        "val_accuracy": float(val_acc),
        "test_accuracy": float(test_acc),
        "train_results": train_results,
    }

    logger.info(
        f"✓ {symbol}: val_acc={val_acc:.4f}  test_acc={test_acc:.4f}  "
        f"(train={len(X_train)} val={len(X_val)} test={len(X_test)})"
    )

    # Save models
    if save_models:
        save_dir = MODEL_DIR / symbol.replace(".", "_")
        ensemble.save_all(str(save_dir))

    return ensemble, results


# ── Walk-forward retraining ───────────────────────────────────────────────

def walk_forward_train(
    symbol: str,
    horizon: int = 5,
    train_years: int = 4,
    test_years: int = 1,
) -> List[Dict]:
    """
    Walk-forward training: slide the training window forward each year.

    Example:
        Train 2014–2018 → Test 2019
        Train 2015–2019 → Test 2020
        Train 2016–2020 → Test 2021
        ...

    Returns:
        List of per-window result dicts.
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"WALK-FORWARD ML TRAINING: {symbol}")
    logger.info(f"Train window: {train_years}y  |  Test window: {test_years}y")
    logger.info(f"{'='*70}")

    # Load full data to determine date range
    raw = load_data(symbol)
    if raw.empty:
        logger.error(f"No data for {symbol}")
        return []

    if "Date" not in raw.columns:
        raw = raw.reset_index()
        if "index" in raw.columns:
            raw = raw.rename(columns={"index": "Date"})
    raw["Date"] = pd.to_datetime(raw["Date"])
    start_year = raw["Date"].min().year
    end_year = raw["Date"].max().year

    results = []
    window_start = start_year

    while window_start + train_years + test_years <= end_year + 1:
        train_end = f"{window_start + train_years - 1}-12-31"
        val_end = train_end  # no separate val in walk-forward; use test as OOS
        test_start_year = window_start + train_years
        test_end = f"{test_start_year + test_years - 1}-12-31"

        logger.info(
            f"\n[Window] Train: {window_start}–{window_start + train_years - 1} | "
            f"Test: {test_start_year}–{test_start_year + test_years - 1}"
        )

        try:
            # Build features + target for full range
            featured = build_ml_features(raw.copy())
            featured = add_target(featured, horizon=horizon)

            # Ensure Date column exists
            if "Date" not in featured.columns:
                if isinstance(featured.index, pd.DatetimeIndex):
                    featured = featured.reset_index(names="Date")
                else:
                    featured = featured.reset_index()
                    if "index" in featured.columns:
                        featured = featured.rename(columns={"index": "Date"})
            featured["Date"] = pd.to_datetime(featured["Date"])

            # Split using proper Timestamp comparison
            train_end_ts = pd.Timestamp(train_end)
            test_end_ts = pd.Timestamp(test_end)
            avail = [c for c in FEATURE_COLUMNS if c in featured.columns]
            train_mask = featured["Date"] <= train_end_ts
            test_mask = (featured["Date"] > train_end_ts) & (featured["Date"] <= test_end_ts)

            train_df = featured[train_mask]
            test_df = featured[test_mask]

            if len(train_df) < 100 or len(test_df) < 20:
                logger.warning("Insufficient data for window — skipping")
                window_start += 1
                continue

            X_train = train_df[avail].dropna()
            y_train = train_df.loc[X_train.index, "target"]
            X_test = test_df[avail].dropna()
            y_test = test_df.loc[X_test.index, "target"]

            # Train ensemble
            ensemble = EnsemblePredictor()
            ensemble.train_all(X_train, y_train)

            # Evaluate
            test_probs = ensemble.predict_proba(X_test)
            test_preds = (test_probs > 0.5).astype(int)
            acc = (test_preds == y_test.values).mean()

            window_result = {
                "train_period": f"{window_start}–{window_start + train_years - 1}",
                "test_period": f"{test_start_year}–{test_start_year + test_years - 1}",
                "train_size": len(X_train),
                "test_size": len(X_test),
                "test_accuracy": float(acc),
            }
            results.append(window_result)

            logger.info(f"  → test_accuracy={acc:.4f} (n={len(X_test)})")

        except Exception as e:
            logger.error(f"  → Error in window: {e}")

        window_start += 1

    # Summary
    if results:
        accs = [r["test_accuracy"] for r in results]
        logger.info(f"\n{'─'*70}")
        logger.info(f"Walk-Forward Summary ({len(results)} windows):")
        logger.info(f"  Avg accuracy : {np.mean(accs):.4f}")
        logger.info(f"  Std accuracy : {np.std(accs):.4f}")
        logger.info(f"  Min accuracy : {np.min(accs):.4f}")
        logger.info(f"  Max accuracy : {np.max(accs):.4f}")
        logger.info(f"{'─'*70}")

    return results


# ── Main ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    symbol = "RELIANCE.NS"
    print(f"\n{'='*70}")
    print(f"Phase 3 ML Training Pipeline — {symbol}")
    print(f"{'='*70}\n")

    # Single window training
    ensemble, results = train_single(symbol)
    print(f"\nResults: {results}")

    # Feature importance
    fi = ensemble.feature_importance()
    if fi:
        print("\nTop 10 Feature Importances (XGBoost):")
        for i, (feat, imp) in enumerate(list(fi.items())[:10], 1):
            print(f"  {i:2d}. {feat:<20s} {imp:.4f}")

    # Walk-forward
    print("\n")
    wf_results = walk_forward_train(symbol)
