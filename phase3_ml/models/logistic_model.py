"""
Logistic Regression Baseline
Simple baseline — if this performs similarly to complex models, ML complexity isn't justified.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logger.warning("scikit-learn not installed — LogisticModel will return neutral predictions")

try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False


class LogisticModel:
    """Logistic Regression with StandardScaler as a baseline classifier."""

    def __init__(self, max_iter: int = 1000):
        self.max_iter = max_iter
        self.pipeline = None
        self.is_fitted = False

    # ── train ─────────────────────────────────────────────────────────
    def train(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        if not HAS_SKLEARN:
            logger.warning("scikit-learn not available — skipping training")
            return {"status": "skipped", "reason": "scikit-learn not installed"}

        self.pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=self.max_iter, random_state=42)),
        ])
        self.pipeline.fit(X.values, y.values)
        self.is_fitted = True

        train_acc = (self.pipeline.predict(X.values) == y.values).mean()
        logger.info(f"Logistic Regression trained — train accuracy: {train_acc:.4f}")
        return {"status": "trained", "train_accuracy": float(train_acc)}

    # ── predict ───────────────────────────────────────────────────────
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted or self.pipeline is None:
            return np.full(len(X), 0.5)
        return self.pipeline.predict_proba(X.values)[:, 1]

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted or self.pipeline is None:
            return np.zeros(len(X), dtype=int)
        return self.pipeline.predict(X.values)

    # ── persistence ───────────────────────────────────────────────────
    def save(self, path: str) -> None:
        if not HAS_JOBLIB or self.pipeline is None:
            return
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, path)
        logger.info(f"Logistic model saved to {path}")

    def load(self, path: str) -> None:
        if not HAS_JOBLIB:
            return
        self.pipeline = joblib.load(path)
        self.is_fitted = True
        logger.info(f"Logistic model loaded from {path}")
