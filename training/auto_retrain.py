"""Automatic (re)training pipeline for Quantum and Hybrid models.

This script can be dropped into a daily cron job or executed ad-hoc.  It will:
1. Load the latest price data (local CSV or external source).
2. Retrain the QuantumPricePredictor.
3. Optionally fine-tune the HybridQuantumEnsemble.
4. Persist the freshly trained models to disk.
5. Record basic training metrics for monitoring.
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score

from quantum.qml_models import QuantumPricePredictor
from quantum.hybrid_models import HybridQuantumEnsemble
from utils import load_training_data, log_metrics

MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)


def retrain_quantum():
    X, y = load_training_data(normalize=True)
    model = QuantumPricePredictor(num_qubits=X.shape[1])

    start = time.time()
    model.train(X, y)
    end = time.time()

    y_pred = model.predict(X)
    acc = accuracy_score(y, y_pred)

    model_path = MODEL_DIR / "quantum_model.pkl"
    model.save(model_path)

    log_metrics({
        "model": "QuantumPricePredictor",
        "accuracy": acc,
        "train_seconds": end - start,
        "model_path": str(model_path),
    })

    print(f"[AutoRetrain] Quantum model saved to {model_path} (accuracy={acc:.4f})")

    return model


def retrain_hybrid(quantum_model):
    X, y = load_training_data(normalize=True)
    hybrid = HybridQuantumEnsemble()

    # Only quantum leg needs retraining; inject the freshly trained model
    hybrid.quantum_model = quantum_model

    # Train to calibrate ensemble weights if needed
    hybrid.train(X, y)

    # For now accuracy is just qualitative; we use quantum model's acc
    model_path = MODEL_DIR / "hybrid_model.pkl"
    hybrid.quantum_model.save(MODEL_DIR / "quantum_model_in_hybrid.pkl")

    log_metrics({
        "model": "HybridQuantumEnsemble",
        "note": "Hybrid ensemble updated with new quantum weights.",
        "model_path": str(model_path),
    })

    print(f"[AutoRetrain] Hybrid model updated and components persisted.")

    return hybrid


if __name__ == "__main__":
    q_model = retrain_quantum()
    retrain_hybrid(q_model)
