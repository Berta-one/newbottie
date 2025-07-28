
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Trading Dashboard", layout="wide")
st.title("📈 Exotic Trading Strategy Dashboard")

df = pd.read_csv("sample_data/historical_data.csv")

st.subheader("📊 Historical Close Prices")
st.line_chart(df['close'])

st.subheader("🧠 Strategy Explanation")
st.markdown("""
- **Model Used**: EMA Crossover
- **Signal Triggered**: BUY
- **Confidence Score**: 0.91
- **Justification**:
  - Short EMA crossed above Long EMA
  - Positive momentum observed
""")
