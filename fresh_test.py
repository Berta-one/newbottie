 -*- coding: utf-8 -*-
import streamlit as st

st.title("ðŸ§ª Fresh Start Test")
st.write("This should work after restart!")
st.success("✔️ Streamlit is working!")

if st.button("Test Button"):
    st.balloons()

