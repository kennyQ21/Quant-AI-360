"""
XGBoost Classifier for price direction prediction.
Primary model in the ensemble — strong on tabular financial features.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    logger.warning("xgboost not installed — XGBoostModel will return neutral predictions")

try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False


class XGBoostModel:
    """XGBoost binary classifier wrapper for price direction prediction."""

    def __init__(
        self,
        n_estimators: int = 300,
        max_depth: int = 5,
        learning_rate: float = 0.05,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
    ):
        self.params = dict(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=subsample,
            colsample_bytree=colsample_bytree,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=42,
        )
        self.model = None
        self.is_fitted = False
        self.feature_names: list = []

    # ── train ─────────────────────────────────────────────────────────
    def train(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """
        Train the XGBoost model.

        Returns:
            Dict with training summary (accuracy on training set).
        """
        if not HAS_XGBOOST:
            logger.warning("XGBoost not available — skipping training")
            return {"status": "skipped", "reason": "xgboost not installed"}

        self.feature_names = list(X.columns)
        self.model = XGBClassifier(**self.params)
        self.model.fit(X.values, y.values)
        self.is_fitted = True

        train_acc = (self.model.predict(X.values) == y.values).mean()
        logger.info(f"XGBoost trained — train accuracy: {train_acc:.4f}")
        return {"status": "trained", "train_accuracy": float(train_acc)}

    # ── predict ───────────────────────────────────────────────────────
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Return probability of class 1 (price going up)."""
        if not self.is_fitted or self.model is None:
            return np.full(len(X), 0.5)
        return self.model.predict_proba(X.values)[:, 1]

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Return hard class predictions (0 or 1)."""
        if not self.is_fitted or self.model is None:
            return np.zeros(len(X), dtype=int)
        return self.model.predict(X.values)

    # ── feature importance ────────────────────────────────────────────
    def feature_importance(self) -> Dict[str, float]:
        """Return feature importance as {feature_name: importance}."""
        if not self.is_fitted or self.model is None:
            return {}
        importances = self.model.feature_importances_
        fi = dict(zip(self.feature_names, importances))
        return dict(sorted(fi.items(), key=lambda x: x[1], reverse=True))

    # ── persistence ───────────────────────────────────────────────────
    def save(self, path: str) -> None:
        """Save model to disk."""
        if not HAS_JOBLIB:
            logger.warning("joblib not available — cannot save model")
            return
        if self.model is not None:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            joblib.dump({"model": self.model, "features": self.feature_names}, path)
            logger.info(f"XGBoost model saved to {path}")

    def load(self, path: str) -> None:
        """Load model from disk."""
        if not HAS_JOBLIB:
            logger.warning("joblib not available — cannot load model")
            return
        data = joblib.load(path)
        self.model = data["model"]
        self.feature_names = data["features"]
        self.is_fitted = True
        logger.info(f"XGBoost model loaded from {path}")
