import os
from qiskit import IBMQ

def get_ibmq_provider():
    """Initializes IBMQ and returns a provider instance."""
    ibm_token = os.getenv("IBM_QUANTUM_TOKEN")

    if not ibm_token:
        raise ValueError("❌ Environment variable IBM_QUANTUM_TOKEN not found.")

    try:
        IBMQ.save_account(ibm_token, overwrite=True)
        IBMQ.load_account()
        provider = IBMQ.get_provider(hub='ibm-q')
        return provider
    except Exception as e:
        raise RuntimeError(f"❌ Failed to load IBMQ provider: {e}")