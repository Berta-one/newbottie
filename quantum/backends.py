# quantum/backends.py

from qiskit import Aer, IBMQ
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_PRIORITY = [
    'ibmq_qasm_simulator',
    'aer_simulator',
    'classical_fallback'
]

def get_best_backend():
    try:
        IBMQ.load_account()
        provider = IBMQ.get_provider(hub='ibm-q')
        for name in BACKEND_PRIORITY:
            if name in provider.backends():
                return provider.get_backend(name)
    except Exception as e:
        logger.warning(f"Falling back to Aer due to error: {e}")
        return Aer.get_backend('aer_simulator')

    return 'classical_fallback'