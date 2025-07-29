# ml/ensemble_model.py

import numpy as np
from ml.lstm_model import load_lstm_model
from ml.xgb_model import load_xgb_model

class EnsembleModel:
    def __init__(self):
        self.lstm = load_lstm_model()
        self.xgb = load_xgb_model()

    def predict(self, features: np.ndarray):
        lstm_pred = self.lstm.predict(features)
        xgb_pred = self.xgb.predict(features)
        final = (0.5 * lstm_pred + 0.5 * xgb_pred)
        return int(final > 0.5)