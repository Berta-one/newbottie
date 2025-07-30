# scripts/verify_ibmq.py

import os
from qiskit import IBMQ

token = (
    os.getenv("IBMQ_API_KEY") or
    os.getenv("QISKIT_IBM_TOKEN") or
    os.getenv("IBM_QUANTUM_TOKEN")
)

if not token:
    raise ValueError("❌ IBMQ token not found in environment variables.")

try:
    IBMQ.save_account(token, overwrite=True)
    IBMQ.load_account()
    provider = IBMQ.get_provider(hub='ibm-q')
    print("✅ IBMQ provider found:", provider.backends())
except Exception as e:
    print("❌ Failed to verify IBMQ access:", str(e))
    raise
