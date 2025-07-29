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