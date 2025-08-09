# ml/model_loader.py
import os
import joblib
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("ModelLoader")

# --- Built-in dummy model ---
class _StubModel:
    def predict(self, X):
        return ["BUY"] * len(X)
    def predict_proba(self, X):
        return [[0.1, 0.8, 0.1] for _ in range(len(X))]

def _load_joblib_or_stub(path: Path) -> Any:
    if path.exists():
        try:
            model = joblib.load(path)
            logger.info("Loaded model from %s", path)
            return model
        except Exception as e:
            logger.warning("Failed to load %s, using stub: %s", path, e)
    else:
        logger.warning("Model file not found: %s. Using stub model.", path)
    return _StubModel()

# --- Public loaders ---
def load_lstm():
    """Loads the LSTM model or returns a stub."""
    return _load_joblib_or_stub(Path("models/lstm_model.pkl"))

def load_xgb():
    """Loads the XGBoost model or returns a stub."""
    return _load_joblib_or_stub(Path("models/xgb_model.pkl"))