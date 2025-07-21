import streamlit as st

st.set_page_config(page_title='Module Test', layout='wide')
st.title('🤖 Module Integration Test')

# Test imports
try:
    from auth import require_authentication
    st.success('✅ auth module loaded')
    
    from portfolio_manager import PortfolioManager
    st.success('✅ portfolio_manager loaded')
    
    from risk_manager import RiskManager
    st.success('✅ risk_manager loaded')
    
    from notifications import notify_system
    st.success('✅ notifications loaded')
    
    # Test basic functionality
    pm = PortfolioManager()
    balance = pm.get_balance()
    st.write(f'Portfolio balance: {balance}')
    
    rm = RiskManager()
    st.write(f'Risk profile: {rm.profile_name}')
    
except Exception as e:
    st.error(f'Error: {e}')
    import traceback
    st.code(traceback.format_exc())
