# quantum/backends.py

import os
from qiskit import IBMQ
from qiskit.providers.ibmq import IBMQProvider
from qiskit.exceptions import QiskitError

def get_ibmq_provider(hub: str = 'ibm-q') -> IBMQProvider:
    """
    Loads the IBM Quantum account using a token from environment variables,
    and returns the default provider.

    Raises:
        ValueError: If the token is missing.
        QiskitError: If account loading fails.
    """
    ibm_token = os.getenv("IBM_QUANTUM_TOKEN")

    if not ibm_token:
        raise ValueError("❌ IBM_QUANTUM_TOKEN not found in environment")

    try:
        # Save and load IBM account
        IBMQ.save_account(ibm_token, overwrite=True)
        IBMQ.load_account()
        provider = IBMQ.get_provider(hub=hub)
        print(f"✅ Connected to IBM Quantum provider: {hub}")
        return provider
    except QiskitError as e:
        raise QiskitError(f"❌ Failed to connect to IBM Quantum: {str(e)}")