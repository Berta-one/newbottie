# quantum/fallback_manager.py

import logging
from ml.lstm_model import LSTMModel
from ml.xgb_model import XGBModel

logger = logging.getLogger(__name__)

class FallbackManager:
    def __init__(self):
        self.lstm = LSTMModel()
        self.xgb = XGBModel()
        self.available = True

    def handle_failure(self, error):
        logger.warning(f"[Quantum Failure] Switching to classical fallback: {error}")
        self.available = False

    def predict(self, X):
        pred_lstm = self.lstm.predict(X)
        pred_xgb = self.xgb.predict(X)
        return (pred_lstm + pred_xgb) / 2  # Simple average fallback
