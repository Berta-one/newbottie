# quantum/hybrid_models.py

from ml.lstm_model import LSTMModel
from ml.xgb_model import XGBModel
from quantum.qml_models import QuantumPricePredictor
import numpy as np

class HybridQuantumEnsemble:
    def __init__(self, weights=[0.4, 0.4, 0.2]):
        self.lstm = LSTMModel()
        self.xgb = XGBModel()
        self.quantum = QuantumPricePredictor()
        self.weights = weights

    def fit(self, X, y):
        self.lstm.fit(X, y)
        self.xgb.fit(X, y)
        self.quantum.fit(X, y)

    def predict(self, X):
        preds = np.array([
            self.lstm.predict(X),
            self.xgb.predict(X),
            self.quantum.predict(X)
        ])
        return np.average(preds, axis=0, weights=self.weights)