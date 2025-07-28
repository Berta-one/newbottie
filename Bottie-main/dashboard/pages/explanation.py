
import streamlit as st

st.title("📊 Strategy Justification")

st.write("This panel explains why each signal is being made.")

# Dummy data to demonstrate
explanation = [
    "LSTM predicts trend with confidence 0.76",
    "XGBoost suggests breakout (score: 0.63)",
    "News sentiment is positive (0.88)",
    "Final signal: BUY"
]

for e in explanation:
    st.success(e)
