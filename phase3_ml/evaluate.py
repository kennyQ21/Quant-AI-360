"""
Model Evaluation & Diagnostics
Feature importance, model comparison, classification metrics.
"""
import sys
from pathlib import Path
import logging
import numpy as np
import pandas as pd
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

from phase3_ml.ensemble import EnsemblePredictor

logger = logging.getLogger(__name__)

try:
    from sklearn.metrics import (
        accuracy_score,
        precision_score,
        recall_score,
        f1_score,
        classification_report,
        confusion_matrix,
    )
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


def evaluate_model(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    model_name: str,
    threshold: float = 0.5,
) -> Dict:
    """
    Compute classification metrics for a single model.

    Returns:
        Dict with accuracy, precision, recall, f1.
    """
    y_pred = (y_proba > threshold).astype(int)

    if not HAS_SKLEARN:
        acc = (y_pred == y_true).mean()
        return {"model": model_name, "accuracy": float(acc)}

    return {
        "model": model_name,
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0, average='weighted')),
        "recall": float(recall_score(y_true, y_pred, zero_division=0, average='weighted')),
        "f1": float(f1_score(y_true, y_pred, zero_division=0, average='weighted')),
    }


def compare_models(
    ensemble: EnsemblePredictor,
    X: pd.DataFrame,
    y: pd.Series,
) -> pd.DataFrame:
    """
    Compare all models (+ ensemble) on the same dataset.

    Returns:
        DataFrame with one row per model and summary metrics.
    """
    y_vals = y.values

    individual = ensemble.get_individual_probs(X)
    ensemble_probs = ensemble.predict_proba(X)

    rows = []
    for name, probs in individual.items():
        rows.append(evaluate_model(y_vals, probs, name))
    rows.append(evaluate_model(y_vals, ensemble_probs, "ensemble"))

    df = pd.DataFrame(rows).set_index("model")
    return df


def print_feature_importance(ensemble: EnsemblePredictor, top_n: int = 15) -> None:
    """Pretty-print XGBoost feature importances."""
    fi = ensemble.feature_importance()
    if not fi:
        print("No feature importances available (XGBoost not fitted).")
        return

    print(f"\n{'='*50}")
    print(f"TOP {top_n} FEATURE IMPORTANCES (XGBoost)")
    print(f"{'='*50}")
    for i, (feat, imp) in enumerate(list(fi.items())[:top_n], 1):
        bar = "█" * int(imp * 100)
        print(f"  {i:2d}. {feat:<20s}  {imp:.4f}  {bar}")
    print()


def print_classification_report(y_true: np.ndarray, y_proba: np.ndarray, name: str = "Ensemble") -> None:
    """Print sklearn classification report."""
    if not HAS_SKLEARN:
        print("scikit-learn not available for detailed report.")
        return

    # y_proba here is probability of class BUY (label 1).
    # Since we have -1, 0, 1, simple thresholding > 0.5 maps to binary.
    # To keep it generic without breaking everything, let's map labels cleanly.
    y_pred = np.where(y_proba > 0.6, 1, np.where(y_proba < 0.4, -1, 0))
    print(f"\n{'='*50}")
    print(f"CLASSIFICATION REPORT: {name}")
    print(f"{'='*50}")
    labels_present = np.unique(np.concatenate([y_true, y_pred]))
    target_names = []
    if -1 in labels_present: target_names.append("SELL")
    if 0 in labels_present: target_names.append("HOLD")
    if 1 in labels_present: target_names.append("BUY")
    
    print(classification_report(y_true, y_pred, labels=labels_present, target_names=target_names))

    cm = confusion_matrix(y_true, y_pred, labels=labels_present)
    print("Confusion Matrix:")
    print(cm)
    print()


# ── Main ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    from phase3_ml.dataset_builder import build_ml_dataset

    symbol = "RELIANCE.NS"
    print(f"\n{'='*70}")
    print(f"Phase 3 ML Evaluation — {symbol}")
    print(f"{'='*70}\n")

    # Build dataset
    X_train, y_train, X_val, y_val, X_test, y_test = build_ml_dataset(symbol)

    # Train ensemble
    ensemble = EnsemblePredictor()
    ensemble.train_all(X_train, y_train)

    # Compare models on test set
    print("\n📊 MODEL COMPARISON (Test Set):")
    comparison = compare_models(ensemble, X_test, y_test)
    print(comparison.to_string())

    # Feature importance
    print_feature_importance(ensemble)

    # Detailed report for ensemble
    ensemble_probs = ensemble.predict_proba(X_test)
    print_classification_report(y_test.values, ensemble_probs)
