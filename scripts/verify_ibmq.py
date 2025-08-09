# scripts/verify_ibmq.py
"""
Verifies IBM Quantum access via:
  1) Qiskit Runtime (preferred, token starts with 'CR-')
  2) qiskit-ibm-provider (legacy)
Falls back to Aer simulator for local dev.

Usage (CI):
  export QISKIT_RUNTIME_TOKEN=CR-xxxxxxxx...
  python scripts/verify_ibmq.py --require-cloud
"""
from __future__ import annotations

import argparse
import os
import sys

def try_qiskit_runtime():
    from qiskit_ibm_runtime import QiskitRuntimeService
    token = os.getenv("QISKIT_RUNTIME_TOKEN") or os.getenv("IBMQ_API_KEY")
    if not token:
        print("[runtime] No QISKIT_RUNTIME_TOKEN/IBMQ_API_KEY set")
        return None

    try:
        svc = QiskitRuntimeService(channel="ibm_quantum", token=token)
        backends = svc.backends()
        names = [b.name for b in backends]
        print(f"[runtime] Connected. Backends: {names[:5]}{'...' if len(names) > 5 else ''}")
        return ("runtime", names)
    except Exception as e:
        print(f"[runtime] Failed: {e}")
        return None


def try_ibm_provider():
    from qiskit_ibm_provider import IBMProvider
    token = os.getenv("IBMQ_API_KEY")
    if not token:
        print("[provider] No IBMQ_API_KEY set")
        return None

    try:
        prov = IBMProvider(token=token)
        backends = prov.backends()
        names = [b.name for b in backends]
        print(f"[provider] Connected. Backends: {names[:5]}{'...' if len(names) > 5 else ''}")
        return ("provider", names)
    except Exception as e:
        print(f"[provider] Failed: {e}")
        return None


def try_aer():
    try:
        from qiskit_aer import Aer
    except Exception:
        # older qiskit ships Aer inside qiskit.providers.aer
        try:
            from qiskit import Aer  # type: ignore
        except Exception as e:
            print(f"[aer] Not available: {e}")
            return None

    try:
        be = Aer.get_backend("qasm_simulator")
        print(f"[aer] OK: {be.name() if hasattr(be, 'name') else 'qasm_simulator'}")
        return ("aer", ["qasm_simulator"])
    except Exception as e:
        print(f"[aer] Failed: {e}")
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--require-cloud", action="store_true", help="Exit non-zero if cloud connection fails.")
    args = ap.parse_args()

    res = try_qiskit_runtime() or try_ibm_provider()
    if res:
        print("[verify] Cloud access verified.")
        sys.exit(0)

    # Cloud failed
    if args.require_cloud:
        print("[verify] Cloud access required but not available.")
        sys.exit(2)

    # Try Aer as local fallback
    aer = try_aer()
    if aer:
        print("[verify] Aer available. Proceeding with local simulator.")
        sys.exit(0)

    print("[verify] No quantum backend available.")
    sys.exit(3)


if __name__ == "__main__":
    main()