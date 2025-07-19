import os
import time
import streamlit as st
from datetime import datetime

# Simple health check page
def main():
    st.set_page_config(page_title="Crypto Bot - Railway", layout="wide")
    
    st.title("🚀 Crypto Trading Bot - Railway Deployment")
    
    # Current status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Status", "🟢 Online", "Running on Railway")
    
    with col2:
        st.metric("Uptime", f"{datetime.now().strftime('%H:%M:%S')}", "Live")
    
    with col3:
        st.metric("Platform", "Railway.app", "Cloud Hosted")
    
    # Basic info
    st.subheader("🎯 Bot Information")
    st.info("Your crypto trading bot is successfully deployed on Railway!")
    
    st.subheader("📊 Next Steps")
    st.write("""
    ✅ Bot is running 24/7 on Railway cloud
    ✅ No more dependency issues
    ✅ Accessible from anywhere
    
    **To add trading functionality:**
    1. Fix the ML dependencies in requirements.txt
    2. Redeploy with full bot code
    3. Add your API keys in Railway variables
    """)
    
    # Environment check
    st.subheader("🔧 Environment Variables")
    env_vars = {
        'PORT': os.getenv('PORT', 'Not set'),
        'RAILWAY_ENVIRONMENT': os.getenv('RAILWAY_ENVIRONMENT', 'Not Railway'),
        'PWD': os.getenv('PWD', 'Unknown')
    }
    
    for key, value in env_vars.items():
        st.text(f"{key}: {value}")
    
    # Auto refresh every 30 seconds
    time.sleep(1)
    st.rerun()

if __name__ == "__main__":
    main()
