# quantum/qml_models.py

from qiskit_machine_learning.algorithms import VQC
from qiskit_machine_learning.kernels import QuantumKernel
from qiskit.circuit.library import RealAmplitudes
from qiskit.utils import algorithm_globals
from qiskit import Aer
from sklearn.preprocessing import MinMaxScaler
import numpy as np

class QuantumPricePredictor:
    def __init__(self, num_qubits=4, layers=2, seed=42):
        self.num_qubits = num_qubits
        self.layers = layers
        self.seed = seed
        algorithm_globals.random_seed = seed
        self.scaler = MinMaxScaler()
        self._build_vqc()

    def _build_vqc(self):
        self.feature_map = RealAmplitudes(self.num_qubits, reps=self.layers)
        self.ansatz = RealAmplitudes(self.num_qubits, reps=self.layers)
        self.vqc = VQC(
            feature_map=self.feature_map,
            ansatz=self.ansatz,
            optimizer='COBYLA',
            quantum_instance=Aer.get_backend('aer_simulator')
        )

    def fit(self, X, y):
        X_scaled = self.scaler.fit_transform(X)
        self.vqc.fit(X_scaled, y)

    def predict(self, X):
        X_scaled = self.scaler.transform(X)
        return self.vqc.predict(X_scaled)