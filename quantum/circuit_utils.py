# quantum/circuit_utils.py

from qiskit.circuit.library import ZZFeatureMap, RealAmplitudes
from qiskit.visualization import plot_circuit_layout, plot_histogram
from qiskit import QuantumCircuit
import matplotlib.pyplot as plt

def build_feature_map(num_qubits):
    return ZZFeatureMap(num_qubits, reps=2)

def build_ansatz(num_qubits):
    return RealAmplitudes(num_qubits, reps=2)

def visualize_circuit(circuit: QuantumCircuit, filename: str = None):
    if filename:
        circuit.draw(output='mpl', filename=filename)
    else:
        circuit.draw(output='mpl')
        plt.show()
