# quantum/backends.py
import os
import logging
from typing import Optional, Tuple

from qiskit import qasm3
from qiskit_aer import Aer
from qiskit.providers.backend import BackendV2

log = logging.getLogger("QuantumBackends")

try:
    from qiskit_ibm_provider import IBMProvider
except ImportError:
    IBMProvider = None  # optional; Aer fallback always available


class QuantumBackend:
    """Container for a chosen backend and kind label."""
    def __init__(self, backend: BackendV2, kind: str):
        self.backend = backend
        self.kind = kind  # "ibm" or "aer"


def _resolve_backend_name(env_val: Optional[str]) -> Optional[str]:
    if not env_val:
        return None
    v = env_val.strip()
    return v or None


def get_backend() -> QuantumBackend:
    """
    Try IBM backends using IBMProvider (token via env), else fall back to Aer.
    Env:
      - QISKIT_RUNTIME_TOKEN (preferred, but we also use it for IBMProvider)
      - QUANTUM_BACKEND (e.g., 'ibmq_qasm_simulator' or 'aer_simulator')
    """
    desired = _resolve_backend_name(os.getenv("QUANTUM_BACKEND"))
    token = os.getenv("QISKIT_RUNTIME_TOKEN") or os.getenv("IBMQ_API_KEY") or os.getenv("IBMQ_TOKEN")

    # 1) IBMProvider path (optional package)
    if token and IBMProvider is not None:
        try:
            # Save and load account
            provider = IBMProvider(token=token)
            backends = provider.backends()
            log.info("IBMProvider available: %d backends", len(backends))
            chosen = None
            if desired and desired != "aer_simulator":
                # If user specified a device name
                try:
                    chosen = provider.get_backend(desired)
                except Exception as e:
                    log.warning("Requested IBM backend '%s' not found: %s; picking a simulator.", desired, e)
            if chosen is None:
                # Prefer an IBM simulator if available
                sims = [b for b in backends if "simulator" in b.name.lower()]
                chosen = sims[0] if sims else backends[0]
            log.info("Using IBM backend: %s", chosen.name)
            return QuantumBackend(backend=chosen, kind="ibm")
        except Exception as e:
            log.warning("IBMProvider init failed (%s). Falling back to Aer.", e)

    # 2) Aer fallback
    try:
        aer_backend = Aer.get_backend("aer_simulator")
        log.info("Using Aer simulator backend.")
        return QuantumBackend(backend=aer_backend, kind="aer")
    except Exception as e:
        log.error("Failed to get Aer simulator: %s", e)
        raise