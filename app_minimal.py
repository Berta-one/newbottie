import streamlit as st
import os

# Handle PORT properly in Python
port = int(os.environ.get('PORT', 8080))

st.set_page_config(
   page_title="Bottie Trading Bot",
   page_icon="🤖",
   layout="wide"
)

st.title("🤖 Bottie Trading Bot - RAILWAY DEPLOYED!")
st.success("✅ Successfully deployed on Railway!")

st.subheader("🔧 Environment Debug")
st.write(f"PORT: {os.environ.get('PORT', 'Not Set')}")
st.write(f"STREAMLIT_SERVER_PORT: {os.environ.get('STREAMLIT_SERVER_PORT', 'Not Set')}")
st.write(f"USE_TESTNET: {os.environ.get('USE_TESTNET', 'true')}")
st.write(f"Python calculated port: {port}")

if st.button("🧪 Test Connection", type="primary"):
   st.balloons()
   st.success("🎉 Connection successful! Your bot is working on Railway!")

st.markdown("---")
st.markdown("**Ready to add your sophisticated trading features!**")
