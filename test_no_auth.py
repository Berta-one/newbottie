import streamlit as st
import os
import sys

# Skip authentication for testing
st.set_page_config(page_title='No Auth Test', layout='wide')
st.title('🤖 Bot Test (No Auth)')

try:
    from portfolio_manager import PortfolioManager
    from risk_manager import RiskManager
    
    st.success('✅ All modules imported successfully!')
    
    # Test basic functionality
    pm = PortfolioManager()
    rm = RiskManager()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader('Portfolio')
        balance = pm.get_balance()
        st.json(balance)
    
    with col2:
        st.subheader('Risk Manager')
        st.write(f'Current Profile: {rm.profile_name}')
        st.write(f'Max Positions: {rm.current_profile.max_open_positions}')
    
    if st.button('Test Trade Validation'):
        validation = rm.validate_trade('BTCUSDT', 0.001, 45000, 1000, 0)
        st.write(f'Trade Valid: {validation.is_valid}')
        st.write(f'Reason: {validation.reason}')

except Exception as e:
    st.error(f'❌ Error: {e}')
    import traceback
    st.code(traceback.format_exc())
