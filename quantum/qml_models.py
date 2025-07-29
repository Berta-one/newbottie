# quantum/qml_models.py

import numpy as np

# Optional heavy dependencies ------------------------------------------------
try:
    from qiskit.circuit.library import RealAmplitudes  # type: ignore
    from qiskit_machine_learning.algorithms import VQC  # type: ignore
    from qiskit_machine_learning.utils.loss_functions import CrossEntropyLoss  # type: ignore
    from quantum.backends import get_quantum_instance
    _QISKIT_ML_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover – allow running without Qiskit
    _QISKIT_ML_AVAILABLE = False

    # Provide lightweight stubs so core logic/test-suite can execute.
    class RealAmplitudes:  # noqa: D101 – stub
        def __init__(self, *_, **__):
            pass

    class _DummyVQC:  # noqa: D101 – stub
        def fit(self, *_):
            pass

        def predict(self, X):
            # Return neutral probability 0.5 for each sample
            return np.full(len(X), 0.5)

    VQC = _DummyVQC  # type: ignore

    def CrossEntropyLoss(*_, **__):  # type: ignore
        return None

    def get_quantum_instance(*_, **__):  # type: ignore
        return None

from sklearn.preprocessing import MinMaxScaler
from quantum.quantum_features import QuantumFeatureEncoder
import pickle


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
        # When the full Qiskit Machine Learning stack is available we build an
        # actual ``VQC``; otherwise we fall back to a dummy, zero-argument
        # placeholder that provides the same ``fit``/``predict`` surface.
        if _QISKIT_ML_AVAILABLE:
            feature_map = self.encoder.map
            ansatz = RealAmplitudes(num_qubits=self.encoder.feature_dim, reps=1)
            return VQC(
                feature_map=feature_map,
                ansatz=ansatz,
                loss=CrossEntropyLoss(),
                optimizer="SPSA",
                quantum_instance=self.quantum_instance,
            )
        # Stub path --------------------------------------------------------
        return VQC()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def save(self, path: str = "models/quantum_model.pkl"):
        """Serialize the trained predictor to *path* using pickle."""
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def load(path: str = "models/quantum_model.pkl") -> "QuantumPricePredictor":
        """Deserialize a predictor from *path*."""
        with open(path, "rb") as f:
            return pickle.load(f)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def train(self, X: np.ndarray, y: np.ndarray):
        """Fit the VQC on scaled data."""
        X_scaled = self.scaler.fit_transform(X)
        self.vqc = self._build_vqc()
        self.vqc.fit(X_scaled, y)

    # ------------------------------------------------------------------
    # scikit-learn compatibility helpers
    # ------------------------------------------------------------------
    def fit(self, X: np.ndarray, y: np.ndarray):
        """Alias for :py:meth:`train` to preserve backward-compatibility with earlier API versions."""
        # The legacy test-suite still invokes ``fit``.  Delegate to the modern
        # ``train`` method so we don't break user code while keeping a clear
        # preferred public interface.
        return self.train(X, y)

    def predict(self, X: np.ndarray):
        if self.vqc is None:
            raise ValueError("Model not trained")
        X_scaled = self.scaler.transform(X)
        prediction = self.vqc.predict(X_scaled)
        # VQC returns array-like; convert first element to float
        return float(prediction[0])