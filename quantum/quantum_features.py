# quantum/quantum_features.py

from qiskit.circuit.library import ZZFeatureMap, PauliFeatureMap
from qiskit.utils import algorithm_globals
import numpy as np

class QuantumFeatureEncoder:
    def __init__(self, feature_dim=4, reps=2, encoding_type="ZZ"):
        self.feature_dim = feature_dim
        self.reps = reps
        self.encoding_type = encoding_type
        self.map = self._create_feature_map()

    def _create_feature_map(self):
        if self.encoding_type == "ZZ":
            return ZZFeatureMap(feature_dimension=self.feature_dim, reps=self.reps, entanglement='linear')
        elif self.encoding_type == "Pauli":
            return PauliFeatureMap(feature_dimension=self.feature_dim, reps=self.reps, paulis=['X', 'Y', 'Z'])
        else:
            raise ValueError("Unsupported encoding_type. Use 'ZZ' or 'Pauli'.")

    def get_circuit(self, input_vector):
        if len(input_vector) != self.feature_dim:
            raise ValueError(f"Input must be of length {self.feature_dim}")
        return self.map.bind_parameters(input_vector)

    def get_feature_map(self):
        return self.map