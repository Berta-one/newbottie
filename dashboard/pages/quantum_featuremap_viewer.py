# dashboard/pages/quantum_featuremap_viewer.py

import streamlit as st
import numpy as np
from quantum.quantum_features import QuantumFeatureEncoder
from quantum.circuit_utils import render_circuit, simulate_circuit
from PIL import Image

st.title("🔬 Quantum Feature Map Visualizer")

feature_dim = st.slider("Feature Dimension", 2, 6, 4)
encoding = st.selectbox("Encoding Type", ["ZZ", "Pauli"])
reps = st.slider("Repetitions", 1, 4, 2)

encoder = QuantumFeatureEncoder(feature_dim=feature_dim, reps=reps, encoding_type=encoding)

input_vector = [st.slider(f"Input {i+1}", 0.0, 2*np.pi, np.pi/2) for i in range(feature_dim)]
qc = encoder.get_circuit(input_vector)

st.subheader("Quantum Circuit Diagram")
st.pyplot(render_circuit(qc))

if st.button("Simulate Circuit"):
    result = simulate_circuit(qc)
    st.bar_chart(result)