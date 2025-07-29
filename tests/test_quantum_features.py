# tests/test_quantum_features.py

from quantum.quantum_features import QuantumFeatureEncoder

def test_encoding_shape():
    encoder = QuantumFeatureEncoder(feature_dim=4, reps=2)
    circuit = encoder.get_circuit([0.1, 0.2, 0.3, 0.4])
    assert circuit.num_qubits == 4