import streamlit as st

# Clear all session state
for key in list(st.session_state.keys()):
    del st.session_state[key]

st.success('Session state cleared! Refresh the page.')
st.button('Refresh Page', key='refresh')
