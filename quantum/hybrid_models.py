# quantum/hybrid_models.py

from quantum.qml_models import QuantumPricePredictor
from ml.lstm_model import LSTMModel
from ml.xgb_model import XGBModel
import numpy as np

class HybridQuantumEnsemble:
    def __init__(self):
        self.lstm = LSTMModel()
        self.xgb = XGBModel()
        self.quantum = QuantumPricePredictor()
        self.weights = [0.4, 0.4, 0.2]  # Adjustable ensemble weights

    def train(self, X, y):
        self.lstm.train(X, y)
        self.xgb.train(X, y)
        self.quantum.train(X, y)

    def predict(self, X):
        lstm_pred = self.lstm.predict(X)
        xgb_pred = self.xgb.predict(X)
        quantum_pred = self.quantum.predict(X)

        # Weighted voting
        return np.round(self.weights[0]*lstm_pred +
                        self.weights[1]*xgb_pred +
                        self.weights[2]*quantum_pred)