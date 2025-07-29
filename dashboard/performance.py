import pandas as pd
import streamlit as st

def show_performance(trades_df):
    st.title("Live Performance")
    st.line_chart(trades_df['equity_curve'])
    st.write(trades_df.tail())
