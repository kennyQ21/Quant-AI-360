"""
Phase 3: Machine Learning Prediction System
Plugs ML models into the existing backtesting + validation pipeline.
"""
from .features import build_ml_features
from .dataset_builder import build_ml_dataset, time_series_split
from .ensemble import EnsemblePredictor
from .signal_generator import generate_ml_signals

__all__ = [
    "build_ml_features",
    "build_ml_dataset",
    "time_series_split",
    "EnsemblePredictor",
    "generate_ml_signals",
]
