import streamlit as st

st.title('🧪 Basic Streamlit Test')
st.write('If you see this, Streamlit is working!')

if st.button('Test'):
    st.success('Button clicked!')
