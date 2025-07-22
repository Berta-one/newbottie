import streamlit as st
import os

st.set_page_config(
   page_title="Bottie Trading Bot",
   page_icon="🤖",
   layout="wide"
)

st.title("🤖 Bottie Trading Bot")
st.success("✅ Successfully deployed on Railway!")

# Debug info
st.subheader("🔧 Debug Information")
st.json({
   "PORT": os.environ.get('PORT', 'Not Set'),
   "STREAMLIT_SERVER_PORT": os.environ.get('STREAMLIT_SERVER_PORT', 'Not Set'),
   "Railway Environment": os.environ.get('RAILWAY_ENVIRONMENT', 'Not Set')
})

if st.button("🧪 Test Connection"):
   st.balloons()
   st.success("🎉 Railway deployment successful!")

st.markdown("---")
st.markdown("**Ready for your sophisticated trading bot!**")
