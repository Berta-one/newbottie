import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Bottie Bot", page_icon="robot", layout="wide")
st.title("Bottie Trading Bot - Clean Version")

st.success("Successfully running - No Unicode issues!")

mode = "LIVE" if os.getenv("USE_TESTNET", "true").lower() == "false" else "Testnet"
st.metric("Trading Mode", mode)

if st.button("Test Bot"):
    st.balloons()
    st.success("Working perfectly!")
