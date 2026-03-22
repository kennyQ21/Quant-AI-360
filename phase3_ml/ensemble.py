"""
Ensemble Predictor
Combines predictions from XGBoost, LSTM, and Logistic Regression models.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict

from phase3_ml.models.xgboost_model import XGBoostModel
from phase3_ml.models.lstm_model import LSTMModel
from phase3_ml.models.logistic_model import LogisticModel

logger = logging.getLogger(__name__)


class EnsemblePredictor:
    """
    Weighted ensemble of ML models.

    Default weights:
        0.5 × XGBoost  +  0.3 × LSTM  +  0.2 × Logistic Regression

    If a model is unavailable, its weight is redistributed proportionally.
    """

    def __init__(
        self,
        xgb_weight: float = 0.5,
        lstm_weight: float = 0.3,
        logistic_weight: float = 0.2,
    ):
        self.weights = {
            "xgboost": xgb_weight,
            "lstm": lstm_weight,
            "logistic": logistic_weight,
        }
        self.xgb = XGBoostModel()
        self.lstm = LSTMModel()
        self.logistic = LogisticModel()

    # ── train all ─────────────────────────────────────────────────────

    def train_all(self, X_train: pd.DataFrame, y_train: pd.Series) -> Dict:
        """Train all three models on the same data."""
        results = {}
        results["xgboost"] = self.xgb.train(X_train, y_train)
        results["logistic"] = self.logistic.train(X_train, y_train)
        results["lstm"] = self.lstm.train(X_train, y_train)
        logger.info(f"Ensemble training complete: {results}")
        return results

    # ── predict ───────────────────────────────────────────────────────

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Return ensemble probability of price going up.

        Handles missing models by re-normalising weights among fitted models.
        """
        preds: Dict[str, np.ndarray] = {}
        active_weights: Dict[str, float] = {}

        if self.xgb.is_fitted:
            preds["xgboost"] = self.xgb.predict_proba(X)
            active_weights["xgboost"] = self.weights["xgboost"]

        if self.lstm.is_fitted:
            preds["lstm"] = self.lstm.predict_proba(X)
            active_weights["lstm"] = self.weights["lstm"]

        if self.logistic.is_fitted:
            preds["logistic"] = self.logistic.predict_proba(X)
            active_weights["logistic"] = self.weights["logistic"]

        if not preds:
            logger.warning("No fitted models — returning 0.5 for all rows")
            return np.full(len(X), 0.5)

        # Re-normalise weights
        total_w = sum(active_weights.values())
        combined = np.zeros(len(X))
        for name, prob in preds.items():
            w = active_weights[name] / total_w
            combined += w * prob

        return combined

    # ── individual probabilities ──────────────────────────────────────

    def get_individual_probs(self, X: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Return per-model probabilities for analysis."""
        return {
            "xgboost": self.xgb.predict_proba(X),
            "lstm": self.lstm.predict_proba(X),
            "logistic": self.logistic.predict_proba(X),
        }

    # ── feature importance (XGBoost) ──────────────────────────────────

    def feature_importance(self) -> Dict[str, float]:
        """Delegate to XGBoost feature importance."""
        return self.xgb.feature_importance()

    # ── persistence ───────────────────────────────────────────────────

    def save_all(self, directory: str) -> None:
        """Save all models to a directory."""
        from pathlib import Path
        d = Path(directory)
        d.mkdir(parents=True, exist_ok=True)
        self.xgb.save(str(d / "xgboost.joblib"))
        self.logistic.save(str(d / "logistic.joblib"))
        self.lstm.save(str(d / "lstm"))
        logger.info(f"All models saved to {directory}")

    def load_all(self, directory: str) -> None:
        """Load all models from a directory."""
        from pathlib import Path
        d = Path(directory)
        xgb_path = d / "xgboost.joblib"
        log_path = d / "logistic.joblib"
        lstm_path = d / "lstm"
        if xgb_path.exists():
            self.xgb.load(str(xgb_path))
        if log_path.exists():
            self.logistic.load(str(log_path))
        if lstm_path.exists():
            self.lstm.load(str(lstm_path))
        logger.info(f"Models loaded from {directory}")
