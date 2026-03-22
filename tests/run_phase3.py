#!/usr/bin/env python3
"""
Phase 3 / 3.5: ML Prediction System — Main Entry Point
Includes leakage-free backtesting, multi-stock testing, and randomization sanity check.

Usage:
    venv/bin/python run_phase3.py
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def download_stocks(symbols):
    """Download parquet data for stocks that don't exist yet."""
    from services.data_service.market_data import download_and_save_stock, load_data
    for sym in symbols:
        data = load_data(sym)
        if data.empty:
            logger.info(f"  Downloading {sym} ...")
            download_and_save_stock(sym)
        else:
            logger.info(f"  ✓ {sym} already available ({len(data)} rows)")


def run_randomization_test(symbol: str):
    """
    Randomization sanity check:
    Shuffle targets randomly and re-train. If Sharpe stays high → data leakage.
    If Sharpe collapses → model is real.
    """
    from phase3_ml.features import FEATURE_COLUMNS
    from phase3_ml.ensemble import EnsemblePredictor
    from services.data_service.market_data import load_data
    from services.feature_service.indicators import add_features_to_data

    print(f"\n{'='*70}")
    print(f"  RANDOMIZATION TEST: {symbol}")
    print("  (Shuffle targets → Sharpe should collapse if model is real)")
    print(f"{'='*70}")

    # Load and prepare data
    raw = load_data(symbol)
    if raw.empty:
        print(f"  No data for {symbol}")
        return

    data = add_features_to_data(raw)
    if isinstance(data.columns, __import__('pandas').MultiIndex):
        data.columns = data.columns.get_level_values(0)
    for col in data.columns:
        if hasattr(data[col], "ndim") and data[col].ndim > 1:
            data[col] = data[col].iloc[:, 0]

    # Import the strategy's feature adder
    from services.backtesting.strategies.ml_strategy import _add_extra_features
    featured = _add_extra_features(data)

    # Build target
    featured["future_return"] = featured["Close"].shift(-5) / featured["Close"] - 1
    featured["target"] = (featured["future_return"] > 0).astype(int)
    avail = [c for c in FEATURE_COLUMNS if c in featured.columns]
    clean = featured[avail + ["target"]].dropna()

    split_idx = int(len(clean) * 0.7)
    X_train = clean.iloc[:split_idx][avail]
    X_test = clean.iloc[split_idx:][avail]
    y_test_real = clean.iloc[split_idx:]["target"]

    # REAL model
    y_train_real = clean.iloc[:split_idx]["target"]
    ensemble_real = EnsemblePredictor()
    ensemble_real.train_all(X_train, y_train_real)
    probs_real = ensemble_real.predict_proba(X_test)
    acc_real = ((probs_real > 0.5).astype(int) == y_test_real.values).mean()

    # RANDOM model (shuffled targets)
    y_train_random = y_train_real.sample(frac=1, random_state=42).reset_index(drop=True)
    y_train_random.index = y_train_real.index  # restore index
    ensemble_random = EnsemblePredictor()
    ensemble_random.train_all(X_train, y_train_random)
    probs_random = ensemble_random.predict_proba(X_test)
    acc_random = ((probs_random > 0.5).astype(int) == y_test_real.values).mean()

    print(f"\n  Real model OOS accuracy:     {acc_real:.4f}")
    print(f"  Random model OOS accuracy:   {acc_random:.4f}")
    print(f"  Difference:                  {acc_real - acc_random:+.4f}")

    if acc_real > acc_random + 0.02:
        print("\n  ✅ PASS: Real model outperforms random → model has signal")
    elif acc_real > acc_random:
        print("\n  ⚠️  MARGINAL: Slight edge over random — use with caution")
    else:
        print("\n  ❌ FAIL: Random model matches or beats real → possible leakage")


def main():
    from services.backtesting import Backtester
    from services.backtesting.strategies.ml_strategy import ml_ensemble_strategy, reset_cache
    from phase3_ml.evaluate import compare_models, print_feature_importance, print_classification_report
    from phase3_ml.dataset_builder import build_ml_dataset
    from phase3_ml.train_pipeline import train_single, walk_forward_train

    test_symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
    primary = test_symbols[0]

    # ── Step 0: Ensure data is available ─────────────────────────────
    print("\n" + "=" * 70)
    print("  PHASE 3.5: ML PREDICTION SYSTEM (LEAK-FREE)")
    print("=" * 70)

    print("\n📥 Step 0: Ensuring market data is available\n")
    download_stocks(test_symbols)

    # ── Step 1: Train & Evaluate Models ──────────────────────────────
    print(f"\n📊 Step 1: Training ML Models ({primary})\n")
    ensemble, train_results = train_single(primary, save_models=True)

    # Feature importance
    print_feature_importance(ensemble)

    # Model comparison on test set
    print("📈 Step 2: Model Comparison (Test Set)\n")
    X_train, y_train, X_val, y_val, X_test, y_test = build_ml_dataset(primary)
    comparison = compare_models(ensemble, X_test, y_test)
    print(comparison.to_string())

    # Classification report
    ensemble_probs = ensemble.predict_proba(X_test)
    print_classification_report(y_test.values, ensemble_probs)

    # ── Step 2: Walk-Forward Training ────────────────────────────────
    print("\n🔬 Step 3: Walk-Forward Retraining\n")
    wf_results = walk_forward_train(primary)

    # ── Step 3: Backtest ML Strategy (LEAK-FREE) ─────────────────────
    print("\n" + "=" * 70)
    print("  BACKTESTING ML STRATEGY (LEAK-FREE)")
    print("  Safeguards: HOLD on training period + 1-day trade delay")
    print("=" * 70)

    backtester = Backtester(initial_capital=100000, transaction_cost=0.001)

    # ── Step 4: Multi-stock test ─────────────────────────────────────
    print(f"\n{'─'*70}")
    print(f"  {'Symbol':<15s}  {'Return':>8s}  {'Sharpe':>7s}  {'Win Rate':>9s}  "
          f"{'MaxDD':>7s}  {'PF':>6s}  {'Trades':>6s}")
    print(f"{'─'*70}")

    for sym in test_symbols:
        reset_cache()
        r = backtester.run(sym, ml_ensemble_strategy)
        if r:
            print(
                f"  {sym:<15s}  {r.metrics['total_return_pct']:>7.2f}%  "
                f"{r.metrics['sharpe_ratio']:>7.2f}  "
                f"{r.metrics['win_rate']:>8.1f}%  "
                f"{r.metrics['max_drawdown']:>6.1f}%  "
                f"{r.metrics['profit_factor']:>6.2f}  "
                f"{r.metrics['total_trades']:>6d}"
            )
        else:
            print(f"  {sym:<15s}  — no data —")

    print(f"{'─'*70}")

    # ── Step 5: Randomization sanity check ────────────────────────────
    print("\n🧪 Step 5: Randomization Sanity Check\n")
    run_randomization_test(primary)

    # ── Done ─────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  ✅ PHASE 3.5 COMPLETE (LEAK-FREE)")
    print("=" * 70)
    print("\nSafeguards applied:")
    print("  ✓ HOLD on entire training period (no in-sample signals)")
    print("  ✓ 1-day trade delay (signal at t → trade at t+1)")
    print("  ✓ Randomization test (validate model vs random)")
    print("  ✓ Multi-stock robustness test")
    print("\nPipeline:")
    print("  Market Data → Features → ML Models → Ensemble")
    print("  → Signal Generator (risk filters) → Backtester → Validation")


if __name__ == "__main__":
    main()
