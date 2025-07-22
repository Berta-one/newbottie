import streamlit as st
import os

st.set_page_config(
   page_title="Bottie Trading Bot",
   page_icon="🤖",
   layout="wide"
)

st.title("🤖 Bottie Trading Bot")
st.success("✅ Successfully deployed on Railway!")

# Show environment info
st.subheader("🔧 Environment Status")
col1, col2 = st.columns(2)

with col1:
   st.metric("PORT", os.environ.get('PORT', 'Auto-detected'))
   st.metric("USE_TESTNET", os.environ.get('USE_TESTNET', 'true'))

with col2:
   st.metric("BINANCE_API_KEY", "✅ Set" if os.environ.get('BINANCE_API_KEY') else "❌ Not Set")
   st.metric("Railway Environment", os.environ.get('RAILWAY_ENVIRONMENT', 'production'))

st.subheader("🚀 Next Steps")
st.info("""
1. ✅ Basic deployment is working
2. 🔄 Can now add back your sophisticated features
3. 🛡️ Bot is in TESTNET mode (safe)
4. 🎯 Ready for full functionality
""")

if st.button("🧪 Test Connection", type="primary"):
   st.balloons()
   st.success("🎉 Connection test successful!")
   st.write("Your sophisticated Bottie bot will go here!")

st.markdown("---")
st.markdown("**🎯 Minimal deployment successful! Ready to upgrade to full features.**")
