# scripts/verify_ibmq.py
import os
from qiskit_ibm_provider import IBMProvider
from qiskit_ibm_provider.exceptions import IBMProviderError

api_key = os.getenv("IBMQ_API_KEY") or os.getenv("QISKIT_IBM_TOKEN") or os.getenv("IBMQ_TOKEN")

if not api_key:
    raise ValueError("No IBMQ API key found in environment variables.")

try:
    provider = IBMProvider(token=api_key)
    backends = provider.backends()
    print("✅ IBMQ Access Successful. Backends:")
    for backend in backends:
        print(f" - {backend.name}")
except IBMProviderError as e:
    print("❌ IBMQ access failed:", str(e))
    raise
