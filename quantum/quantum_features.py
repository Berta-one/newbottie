# quantum/quantum_features.py

import numpy as np
from sklearn.preprocessing import StandardScaler

class QuantumFeatureEncoder:
    def __init__(self):
        self.scaler = StandardScaler()

    def encode(self, X):
        X_scaled = self.scaler.fit_transform(X)
        return np.pi * (X_scaled - X_scaled.min()) / (X_scaled.max() - X_scaled.min() + 1e-8)

    def quantum_bitstring_encode(self, x, num_qubits=4):
        return [format(int(val * 15), f'0{num_qubits}b') for val in x]
