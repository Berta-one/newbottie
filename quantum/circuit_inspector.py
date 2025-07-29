"""Utility functions for inspecting and visualising quantum circuits used in the models."""

from pathlib import Path

import matplotlib.pyplot as plt
from qiskit import QuantumCircuit

from quantum.qml_models import QuantumPricePredictor


def visualize_quantum_circuit(model: QuantumPricePredictor, save_path: str | None = None):
    """Render the underlying circuit of a trained QuantumPricePredictor.

    Parameters
    ----------
    model : QuantumPricePredictor
        The trained model whose feature map + ansatz we wish to visualise.
    save_path : str | None
        If provided, the circuit will be saved as a PNG to this path; otherwise
        the diagram is shown inline (Matplotlib window).
    """
    if model.vqc is None:
        raise ValueError("Model must be trained or initialised with a circuit before visualisation.")

    qc: QuantumCircuit = model.vqc._feature_map.compose(model.vqc._ansatz)

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.figure(figsize=(8, 6))
        qc.draw(output="mpl")
        plt.savefig(save_path)
        plt.close()
        print(f"[CircuitInspector] Circuit saved to {save_path}")
    else:
        print(qc.draw(output="text"))