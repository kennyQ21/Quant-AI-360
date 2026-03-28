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
    """XGBoost multiclass classifier for price direction prediction (BUY/HOLD/SELL)."""

    def __init__(
        self,
        n_estimators: int = 300,
        max_depth: int = 5,
        learning_rate: float = 0.05,
        subsample: float = 0.8,
        colsample_bytree: float = 0.7,
        min_child_weight: int = 5,
        reg_lambda: float = 2.0,
        # Feature selection thresholds
        min_variance: float = 0.001,
        max_corr: float = 0.92,
    ):
        self.base_params = dict(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=subsample,
            colsample_bytree=colsample_bytree,
            min_child_weight=min_child_weight,
            reg_lambda=reg_lambda,
            eval_metric="mlogloss",
            random_state=42,
            use_label_encoder=False,
        )
        self.min_variance = min_variance
        self.max_corr = max_corr
        self.model = None
        self.is_fitted = False
        self.feature_names: list = []
        self.selected_features: list = []  # after feature selection
        from sklearn.preprocessing import LabelEncoder
        self.le = LabelEncoder()

    # ── feature selection ─────────────────────────────────────────────
    def _select_features(self, X: pd.DataFrame) -> list:
        """Drop near-zero-variance and one of any highly-correlated pair."""
        variances = X.var()
        ok_var = variances[variances >= self.min_variance].index.tolist()
        X_filtered = X[ok_var]
        if len(ok_var) > 1:
            corr = X_filtered.corr().abs()
            upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
            to_drop = [col for col in upper.columns if any(upper[col] > self.max_corr)]
            selected = [c for c in ok_var if c not in to_drop]
        else:
            selected = ok_var
        logger.info(f"Feature selection: kept {len(selected)}/{len(X.columns)} features")
        return selected

    # ── train ─────────────────────────────────────────────────────────
    def train(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """
        Train XGBoost with automatic feature selection and class balancing.

        Returns:
            Dict with training summary.
        """
        if not HAS_XGBOOST:
            logger.warning("XGBoost not available — skipping training")
            return {"status": "skipped", "reason": "xgboost not installed"}

        self.feature_names = list(X.columns)
        self.selected_features = self._select_features(X)
        X_sel = X[self.selected_features]

        # Class-weight balancing via sample_weight for multiclass
        y_mapped = self.le.fit_transform(y.values)
        from sklearn.utils.class_weight import compute_sample_weight
        sample_weights = compute_sample_weight('balanced', y_mapped)

        params = {**self.base_params}
        if "scale_pos_weight" in params:
            del params["scale_pos_weight"]
            
        self.model = XGBClassifier(**params)
        self.model.fit(X_sel.values, y_mapped, sample_weight=sample_weights)
        self.is_fitted = True

        train_acc = float((self.model.predict(X_sel.values) == y_mapped).mean())
        logger.info(
            f"XGBoost trained — features={len(self.selected_features)} | "
            f"train_acc={train_acc:.4f} | class_balanced=True"
        )
        return {
            "status": "trained",
            "train_accuracy": train_acc,
            "features_selected": len(self.selected_features),
            "class_balanced": True,
        }

    # ── predict ───────────────────────────────────────────────────────
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Return probability of class 1 (BUY)."""
        if not self.is_fitted or self.model is None:
            return np.full(len(X), 0.5)
        X_sel = X[self.selected_features] if self.selected_features else X
        preds = self.model.predict_proba(X_sel.values)
        if 1 in self.le.classes_:
            buy_idx = list(self.le.classes_).index(1)
            return preds[:, buy_idx]
        return preds[:, -1]

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Return hard class predictions (original labels: -1, 0, 1)."""
        if not self.is_fitted or self.model is None:
            return np.zeros(len(X), dtype=int)
        X_sel = X[self.selected_features] if self.selected_features else X
        y_pred = self.model.predict(X_sel.values)
        return self.le.inverse_transform(y_pred)

    # ── feature importance ────────────────────────────────────────────
    def feature_importance(self) -> Dict[str, float]:
        """Return feature importance as {feature_name: importance}."""
        if not self.is_fitted or self.model is None:
            return {}
        feat_names = self.selected_features if self.selected_features else self.feature_names
        importances = self.model.feature_importances_
        fi = dict(zip(feat_names, importances))
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
