# dashboard/pages/quantum_metrics.py

import streamlit as st
from quantum.backends import get_active_backend
from engine.portfolio_manager import HybridPortfolioManager
import pandas as pd

st.title("🧠 Quantum Metrics & Portfolio Optimization")

# Active backend
backend_name, backend_type = get_active_backend(return_type=True)
st.success(f"✅ Active Quantum Backend: `{backend_name}` ({backend_type})")

# Display fallback status
if backend_type == "classical":
    st.warning("⚠️ Quantum backend unavailable — using classical fallback.")

# Show example portfolio optimization result
st.subheader("📈 Optimized Portfolio Weights (Sample)")

# Simulate input (replace with live data in production)
example_returns = [0.03, 0.06, 0.02]
example_cov = [
    [0.001, 0.0002, 0.0001],
    [0.0002, 0.002, 0.0003],
    [0.0001, 0.0003, 0.0015]
]

optimizer = HybridPortfolioManager(num_assets=3)
weights = optimizer.rebalance(example_returns, example_cov)

# Render results
df = pd.DataFrame({
    "Asset": [f"Asset {i+1}" for i in range(len(weights))],
    "Weight": weights
})
st.dataframe(df.set_index("Asset"), use_container_width=True)

st.caption("🎛️ This panel simulates optimization results for test purposes.")