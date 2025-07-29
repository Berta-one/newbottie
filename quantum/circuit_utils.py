# quantum/circuit_utils.py

from qiskit import Aer, transpile
from qiskit.visualization import plot_bloch_multivector, plot_histogram
import matplotlib.pyplot as plt

def render_circuit(circuit):
    return circuit.draw(output="mpl")

def simulate_circuit(circuit, shots=1024):
    backend = Aer.get_backend('qasm_simulator')
    transpiled = transpile(circuit, backend)
    job = backend.run(transpiled, shots=shots)
    result = job.result()
    return result.get_counts()