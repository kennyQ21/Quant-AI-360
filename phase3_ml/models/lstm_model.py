"""
LSTM Model for temporal price pattern learning.
Sequence input: last N days of features → sigmoid probability of price increase.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    HAS_TF = True
    # Suppress TF info logs
    tf.get_logger().setLevel("ERROR")
except ImportError:
    HAS_TF = False
    logger.warning("tensorflow not installed — LSTMModel will return neutral predictions")


class LSTMModel:
    """
    LSTM binary classifier for price direction prediction.
    Consumes a 3-D array: (samples, lookback_days, num_features).
    """

    def __init__(self, lookback: int = 30, lstm_units: int = 64, dense_units: int = 32):
        self.lookback = lookback
        self.lstm_units = lstm_units
        self.dense_units = dense_units
        self.model = None
        self.is_fitted = False

    # ── helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _create_sequences(X: np.ndarray, y: np.ndarray, lookback: int):
        """
        Convert 2-D feature matrix + 1-D target into 3-D sequences.
        Returns (X_seq, y_seq) where X_seq.shape = (n_samples, lookback, n_features).
        """
        X_seq, y_seq = [], []
        for i in range(lookback, len(X)):
            X_seq.append(X[i - lookback : i])
            y_seq.append(y[i])
        return np.array(X_seq), np.array(y_seq)

    def _build_model(self, num_features: int):
        """Build Keras LSTM model."""
        model = Sequential([
            LSTM(self.lstm_units, input_shape=(self.lookback, num_features)),
            Dropout(0.2),
            Dense(self.dense_units, activation="relu"),
            Dropout(0.2),
            Dense(1, activation="sigmoid"),
        ])
        model.compile(
            optimizer="adam",
            loss="binary_crossentropy",
            metrics=["accuracy"],
        )
        return model

    # ── train ─────────────────────────────────────────────────────────

    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        epochs: int = 20,
        batch_size: int = 32,
        validation_split: float = 0.15,
    ) -> Dict:
        """
        Train the LSTM model.

        Args:
            X: 2-D feature DataFrame (rows = days).
            y: Binary target Series.

        Returns:
            Training summary dict.
        """
        if not HAS_TF:
            logger.warning("TensorFlow not available — skipping LSTM training")
            return {"status": "skipped", "reason": "tensorflow not installed"}

        X_vals = X.values.astype("float32")
        y_vals = y.values.astype("float32")

        # Normalise features (per-column z-score on training set)
        self._mean = X_vals.mean(axis=0)
        self._std = X_vals.std(axis=0) + 1e-8
        X_vals = (X_vals - self._mean) / self._std

        X_seq, y_seq = self._create_sequences(X_vals, y_vals, self.lookback)

        if len(X_seq) == 0:
            logger.warning("Not enough data for LSTM lookback window")
            return {"status": "skipped", "reason": "insufficient data"}

        self.model = self._build_model(X_seq.shape[2])

        early_stop = EarlyStopping(
            monitor="val_loss", patience=3, restore_best_weights=True
        )

        history = self.model.fit(
            X_seq, y_seq,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=[early_stop],
            verbose=0,
        )

        self.is_fitted = True
        final_acc = history.history["accuracy"][-1]
        logger.info(f"LSTM trained — final train accuracy: {final_acc:.4f}")
        return {"status": "trained", "train_accuracy": float(final_acc)}

    # ── predict ───────────────────────────────────────────────────────

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Return probability of class 1 (price up).
        Handles alignment: first `lookback` rows get 0.5 (neutral).
        """
        if not self.is_fitted or self.model is None:
            return np.full(len(X), 0.5)

        X_vals = X.values.astype("float32")
        X_vals = (X_vals - self._mean) / self._std

        X_seq, _ = self._create_sequences(X_vals, np.zeros(len(X_vals)), self.lookback)

        if len(X_seq) == 0:
            return np.full(len(X), 0.5)

        preds = self.model.predict(X_seq, verbose=0).flatten()

        # Pad the first `lookback` entries with 0.5
        full_preds = np.full(len(X), 0.5)
        full_preds[self.lookback :] = preds
        return full_preds

    # ── persistence ───────────────────────────────────────────────────

    def save(self, path: str) -> None:
        """Save Keras model + scaling params."""
        if self.model is None:
            return
        Path(path).mkdir(parents=True, exist_ok=True)
        self.model.save(Path(path) / "lstm_model.keras")
        np.savez(Path(path) / "scaler.npz", mean=self._mean, std=self._std)
        logger.info(f"LSTM model saved to {path}")

    def load(self, path: str) -> None:
        """Load Keras model + scaling params."""
        if not HAS_TF:
            return
        self.model = tf.keras.models.load_model(Path(path) / "lstm_model.keras")
        scaler = np.load(Path(path) / "scaler.npz")
        self._mean = scaler["mean"]
        self._std = scaler["std"]
        self.is_fitted = True
        logger.info(f"LSTM model loaded from {path}")
