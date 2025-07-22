import streamlit as st
import os
import socket

st.set_page_config(
   page_title="Bottie Trading Bot",
   page_icon="🤖",
   layout="wide"
)

st.title("🤖 Bottie Trading Bot - Railway Deployment")

# Show deployment status
if os.environ.get('RAILWAY_ENVIRONMENT'):
   st.success("✅ Running on Railway!")
else:
   st.info("🏠 Running locally")

# Debug information
st.subheader("🔧 Connection Debug")
col1, col2 = st.columns(2)

with col1:
   st.metric("Railway PORT", os.environ.get('PORT', 'Not Set'))
   st.metric("Streamlit Port", os.environ.get('STREAMLIT_SERVER_PORT', 'Not Set'))
   
with col2:
   st.metric("Environment", os.environ.get('RAILWAY_ENVIRONMENT', 'Local'))
   st.metric("Service", os.environ.get('RAILWAY_SERVICE_NAME', 'Unknown'))

# Test connectivity
if st.button("🧪 Test Connection", type="primary"):
   st.balloons()
   st.success("🎉 Connection successful!")
   st.write(f"App is responding on Railway!")

# Show all environment variables for debugging
with st.expander("🔍 All Environment Variables"):
   env_vars = {k: v for k, v in os.environ.items() if 'RAILWAY' in k or 'PORT' in k or 'STREAMLIT' in k}
   st.json(env_vars)

st.markdown("---")
st.markdown("**🚀 Ready to add your sophisticated Bottie features!**")
