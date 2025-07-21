import streamlit as st

st.title('🤖 Crypto Trading Bot')
st.write('Bot dashboard is loading...')

try:
    from portfolio_manager import PortfolioManager
    st.success('✅ Portfolio manager loaded')
    
    pm = PortfolioManager()
    balance = pm.get_balance()
    st.json(balance)
    
except Exception as e:
    st.error(f'Error: {e}')
    import traceback
    st.code(traceback.format_exc())
