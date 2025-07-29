# dashboard/pages/quantum_metrics.py

import streamlit as st
import pandas as pd
from monitoring.performance_metrics import PerformanceTracker
from quantum.hybrid_models import HybridQuantumEnsemble
from ml.lstm_model import LSTMModel
from ml.xgb_model import XGBModel
import numpy as np
import time

st.title("🧠 Quantum vs Classical Model Metrics")

# Mock sample data
X_sample = np.random.rand(50, 4)
y_sample = np.random.randint(0, 2, 50)

models = {
    "LSTM": LSTMModel(),
    "XGB": XGBModel(),
    "HybridQuantum": HybridQuantumEnsemble()
}

results = []

for name, model in models.items():
    tracker = PerformanceTracker(name)

    start = time.time()
    model.fit(X_sample, y_sample)
    preds = model.predict(X_sample)
    end = time.time()

    metrics = tracker.track(y_sample, preds, start, end)
    results.append(metrics)

df = pd.DataFrame(results).set_index("model")
st.dataframe(df.style.highlight_max(axis=0))
st.bar_chart(df[["accuracy", "precision", "recall", "f1"]])
st.caption("Latency measured in seconds (lower is better)")