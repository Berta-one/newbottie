# quantum/hybrid_models.py

import numpy as np
from quantum.qml_models import QuantumPricePredictor
from ml.lstm_model import LSTMPricePredictor
from ml.xgb_model import XGBoostPricePredictor


class HybridQuantumEnsemble:
    """Hybrid ensemble combining LSTM, XGBoost, and Quantum VQC models.

    Each sub-model produces a probability (0-1) that the *next* price will move
    up.  The ensemble aggregates these probabilities using user-defined
    weights.  If the Quantum model fails (e.g., backend issues), it
    automatically falls back to the classical components and re-normalises the
    weights.
    """

    def __init__(self, lstm_weight: float = 0.35, xgb_weight: float = 0.35, quantum_weight: float = 0.30):
        self.lstm_model = LSTMPricePredictor()
        self.xgb_model = XGBoostPricePredictor()
        self.quantum_model = QuantumPricePredictor()

        self.weights = {
            'lstm': lstm_weight,
            'xgb': xgb_weight,
            'quantum': quantum_weight
        }

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def train(self, X, y):
        """Train sub-models where applicable.

        Currently only the Quantum VQC requires in-session training; the LSTM
        and XGBoost models are assumed to be pre-trained and deserialised from
        disk.  This method therefore delegates training solely to the Quantum
        model, but keeps the hook open for future extensions.
        """
        self.quantum_model.train(X, y)

    def predict(self, X):
        """Generate a trading signal and confidence score.

        Parameters
        ----------
        X : np.ndarray
            Feature matrix with shape ``(n_samples, n_features)``.

        Returns
        -------
        Tuple[str, float]
            *signal* ∈ {"buy", "sell", "hold"} and *confidence* ∈ [0, 1].
        """
        self._normalize_weights()

        lstm_pred = float(self.lstm_model.predict(X))
        xgb_pred = float(self.xgb_model.predict(X))

        try:
            quantum_pred = float(self.quantum_model.predict(X))
        except Exception as e:
            print(f"[Quantum Model Error] {e} — Falling back to classical")
            quantum_pred = 0.5  # Neutral probability
            self.weights['quantum'] = 0.0
            self._normalize_weights()

        weighted_output = (
            self.weights['lstm'] * lstm_pred +
            self.weights['xgb'] * xgb_pred +
            self.weights['quantum'] * quantum_pred
        )

        # Interpret weighted output into discrete signals
        if weighted_output > 0.6:
            signal = "buy"
        elif weighted_output < 0.4:
            signal = "sell"
        else:
            signal = "hold"

        return signal, round(weighted_output, 3)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _normalize_weights(self):
        total = sum(self.weights.values())
        if total == 0:
            # Edge case: all weights zero (should not happen, but guard anyway)
            self.weights = {'lstm': 0.5, 'xgb': 0.5, 'quantum': 0.0}
            total = 1.0
        for key in self.weights:
            self.weights[key] /= total