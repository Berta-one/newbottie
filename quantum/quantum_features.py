# quantum/quantum_features.py

from qiskit.circuit import QuantumCircuit
from qiskit.circuit.library import ZZFeatureMap
import numpy as np


class QuantumFeatureEncoder:
    def __init__(self, feature_dim, reps: int = 2, entanglement: str = 'full'):
        """Quantum feature encoder using a ZZFeatureMap.

        Parameters
        ----------
        feature_dim : int
            Number of classical input features (== number of qubits).
        reps : int, optional
            Repetitions/depth of the feature map.
        entanglement : str, optional
            Entanglement pattern passed to ``ZZFeatureMap`` (e.g., 'linear', 'full').
        """
        self.feature_dim = feature_dim
        self.reps = reps
        self.entanglement = entanglement

        # Build underlying feature map
        self.feature_map = ZZFeatureMap(
            feature_dimension=feature_dim,
            reps=reps,
            entanglement=entanglement,
        )

        # Alias for backward-compatibility with earlier code (`encoder.map`).
        self.map = self.feature_map

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _safe_normalize(vector: np.ndarray) -> np.ndarray:
        """Scale an input vector to the [0, π] range, avoiding division by 0."""
        vmin, vmax = np.min(vector), np.max(vector)
        denom = vmax - vmin + 1e-8  # avoid zero-division
        return (vector - vmin) / denom * np.pi

    def normalize(self, vector):
        """Public alias that converts *vector* to the encoded angle range."""
        return self._safe_normalize(np.asarray(vector))

    def get_circuit(self, vector):
        """Return a QuantumCircuit encoding *vector* with the feature map."""
        if len(vector) != self.feature_dim:
            raise ValueError(f"Expected input of length {self.feature_dim}, got {len(vector)}")

        theta = self.normalize(vector)
        return self.feature_map.assign_parameters(theta)

    def visualize(self, vector):
        """Print an ASCII diagram of the encoded circuit (for quick debugging)."""
        circuit = self.get_circuit(vector)
        print(circuit.draw(output='text'))