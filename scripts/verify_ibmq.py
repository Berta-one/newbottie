# scripts/verify_ibmq.py

import os
from qiskit_ibm_provider import IBMProvider
from qiskit_ibm_provider.exceptions import IBMProviderError

# Try common env var names
api_key = (
    os.getenv("IBMQ_API_KEY")
    or os.getenv("QISKIT_IBM_TOKEN")
    or os.getenv("IBMQ_TOKEN")
)

if not api_key:
    raise ValueError("❌ No IBMQ API key found in environment variables.")

try:
    print("🔍 Attempting to authenticate with IBM Quantum using provided API key...")
    provider = IBMProvider(token=api_key)
    backends = provider.backends()
    print("✅ IBMQ Access Successful. Available backends:")
    for backend in backends:
        print(f"  • {backend.name}")
except IBMProviderError as e:
    print("❌ IBMQ access failed:", str(e))
    raise
