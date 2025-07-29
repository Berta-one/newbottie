# ml/ensemble_model.py

import numpy as np
from keras.models import load_model
import joblib

class EnsembleModel:
    def __init__(self, lstm_path="models/lstm_model.h5", xgb_path="models/xgb_model.json"):
        self.lstm = load_model(lstm_path)
        self.xgb = joblib.load(xgb_path)

    def predict(self, X):
        lstm_pred = self.lstm.predict(X)
        xgb_pred = self.xgb.predict_proba(X)[:, 1]

        # Weighted average (LSTM = 60%, XGB = 40%)
        combined = 0.6 * lstm_pred.flatten() + 0.4 * xgb_pred
        return combined