# dashboard/pages/quantum_metrics.py

import streamlit as st
import pandas as pd

def show_quantum_metrics(data):
    st.title("🧠 Quantum Metrics Dashboard")
    
    st.metric("Quantum Backend", data.get("backend", "Unavailable"))
    st.metric("Quantum Queue Time", f"{data.get('queue_time', 0)} sec")
    st.metric("Quantum Advantage", f"{data.get('quantum_advantage', 0):.2f}%")
    
    st.subheader("Prediction Confidence")
    st.bar_chart(pd.DataFrame(data.get("confidence", {"Classical": 0.6, "Quantum": 0.4})))

    st.subheader("Circuit Stats")
    st.json(data.get("circuit_info", {"depth": 10, "qubits": 4}))

    st.subheader("Fallback Status")
    if data.get("fallback_used", False):
        st.error("⚠️ Classical fallback active")
    else:
        st.success("✅ Quantum active")