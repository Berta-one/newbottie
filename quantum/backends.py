# quantum/backends.py

import logging

BACKEND_PRIORITY = [
    'ibmq_montreal',
    'ibmq_qasm_simulator',
    'aer_simulator',
    'classical_fallback'
]

class BackendManager:
    def __init__(self, prefer_simulator=True):
        self.active_backend = None
        self.prefer_simulator = prefer_simulator

    def select_backend(self):
        if self.prefer_simulator:
            self.active_backend = 'aer_simulator'
        else:
            self.active_backend = 'ibmq_qasm_simulator'
        logging.info(f"[Quantum] Selected backend: {self.active_backend}")
        return self.active_backend

    def log_fallback(self, reason):
        logging.warning(f"[Quantum] Fallback triggered: {reason}")

# ---------------------------------------------------------------------------
# Dynamic QuantumInstance factory
# ---------------------------------------------------------------------------
# Optional Qiskit imports ----------------------------------------------------
try:
    from qiskit import Aer  # type: ignore
    from qiskit.utils import QuantumInstance  # type: ignore

    try:
        # Qiskit >= 0.45 uses the external provider package
        from qiskit_ibm_provider import IBMProvider  # type: ignore
    except ImportError:  # pragma: no cover – provider package optional
        IBMProvider = None  # pyright: ignore

except ModuleNotFoundError:  # pragma: no cover – allow running w/o Qiskit
    # Provide lightweight shims so other modules can reference the names.
    class _Shim:
        """Minimal dummy class used as a stand-in for missing Qiskit objects."""

        def __init__(self, *_, **__):
            pass

        def __getattr__(self, _):
            return self

        def __call__(self, *_, **__):  # noqa: D401 – dummy callable
            return self

    Aer = _Shim()  # type: ignore
    QuantumInstance = _Shim  # type: ignore
    IBMProvider = None  # type: ignore


def get_quantum_instance(preferred_backend: str = "ibmq_qasm_simulator", shots: int = 1024) -> QuantumInstance:
    """Return a QuantumInstance, preferring IBM Cloud backends when available.

    The helper first tries to instantiate an ``IBMProvider`` (modern API).  If
    that fails (e.g., missing package or no credentials), it falls back to the
    local Aer simulator bundled with Qiskit.  This ensures the rest of the
    codebase can run in CI environments that lack IBM Quantum credentials.
    """
    try:
        if IBMProvider is not None:
            try:
                provider = IBMProvider()  # credentials sourced from env if configured
                backend = provider.get_backend(preferred_backend)
            except Exception as exc:  # noqa: BLE001 – broad for robustness
                logging.warning(f"[QuantumBackend] Falling back to local simulator: {exc}")
                backend = Aer.get_backend("aer_simulator")
        else:
            backend = Aer.get_backend("aer_simulator")

        return QuantumInstance(backend=backend, shots=shots)

    except Exception:  # pragma: no cover – running with stubbed qiskit
        # When Qiskit is not available we return a dummy object implementing
        # the bare minimum API surface expected by callers.

        class _DummyInstance:  # noqa: D401 – stub
            def __init__(self, *_, **__):
                pass

        return _DummyInstance()