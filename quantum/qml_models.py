# quantum/qml_models.py

from qiskit.circuit.library import RealAmplitudes
from qiskit_machine_learning.algorithms import VQC
from qiskit_machine_learning.kernels import FidelityQuantumKernel
from qiskit.utils import algorithm_globals
from qiskit.algorithms.optimizers import COBYLA
from qiskit import Aer
from sklearn.preprocessing import MinMaxScaler
import numpy as np

class QuantumPricePredictor:
    def __init__(self, num_qubits=4):
        self.num_qubits = num_qubits
        self.scaler = MinMaxScaler()
        algorithm_globals.random_seed = 42
        self.backend = Aer.get_backend("aer_simulator_statevector")
        self.vqc = self.build_vqc()

    def build_vqc(self):
        feature_map = RealAmplitudes(self.num_qubits, reps=2)
        ansatz = RealAmplitudes(self.num_qubits, reps=2)
        optimizer = COBYLA(maxiter=50)
        return VQC(optimizer=optimizer,
                   feature_map=feature_map,
                   ansatz=ansatz,
                   quantum_instance=self.backend)

    def train(self, X, y):
        X_scaled = self.scaler.fit_transform(X)
        self.vqc.fit(X_scaled, y)

    def predict(self, X):
        X_scaled = self.scaler.transform(X)
        return self.vqc.predict(X_scaled)