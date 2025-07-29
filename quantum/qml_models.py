# quantum/qml_models.py

import numpy as np
from qiskit.circuit.library import RealAmplitudes
from qiskit_machine_learning.algorithms import VQC
from qiskit_machine_learning.utils.loss_functions import CrossEntropyLoss
from sklearn.preprocessing import MinMaxScaler
from quantum.backends import get_quantum_instance
from quantum.quantum_features import QuantumFeatureEncoder


class QuantumPricePredictor:
    """Variational Quantum Classifier wrapper for price direction prediction."""

    def __init__(self, num_qubits: int = 4):
        self.scaler = MinMaxScaler()
        self.encoder = QuantumFeatureEncoder(feature_dim=num_qubits)
        self.quantum_instance = get_quantum_instance()
        self.vqc = None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _build_vqc(self):
        feature_map = self.encoder.map
        ansatz = RealAmplitudes(num_qubits=self.encoder.feature_dim, reps=1)
        return VQC(
            feature_map=feature_map,
            ansatz=ansatz,
            loss=CrossEntropyLoss(),
            optimizer='SPSA',
            quantum_instance=self.quantum_instance,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def train(self, X: np.ndarray, y: np.ndarray):
        """Fit the VQC on scaled data."""
        X_scaled = self.scaler.fit_transform(X)
        self.vqc = self._build_vqc()
        self.vqc.fit(X_scaled, y)

    def predict(self, X: np.ndarray):
        if self.vqc is None:
            raise ValueError("Model not trained")
        X_scaled = self.scaler.transform(X)
        prediction = self.vqc.predict(X_scaled)
        # VQC returns array-like; convert first element to float
        return float(prediction[0])