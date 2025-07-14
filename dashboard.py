
import streamlit as st
import pandas as pd
from datetime import datetime
from utils import get_demo_portfolio, simulate_market_analysis

st.set_page_config(page_title="Bottie", layout="wide", initial_sidebar_state="expanded")

# Initialize session state defaults
if "selected_profile" not in st.session_state:
    st.session_state.selected_profile = "AUTO"

# Overview tab function
def render_overview_tab(portfolio, gbp_rate, market_condition, condition_score, avg_volatility):
    total_usd = sum(coin['usd_value'] for coin in portfolio.values())
    total_gbp = total_usd * gbp_rate

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💷 Portfolio Value", f"£{total_gbp:,.2f}")
    with col2:
        condition_color = "🟢" if condition_score > 0.6 else "🟡" if condition_score > 0.4 else "🔴"
        st.metric(f"{condition_color} Market", market_condition.replace('_', ' ').title())
    with col3:
        volatility_level = "High" if avg_volatility > 3 else "Medium" if avg_volatility > 1.5 else "Low"
        st.metric("📈 Volatility", f"{avg_volatility:.1f}%")
    with col4:
        if st.session_state.selected_profile != "AUTO":
            profile = st.session_state.selected_profile
        elif market_condition == "BULL_TRENDING":
            profile = "Aggressive" if avg_volatility > 2.5 else "Swing"
        elif market_condition == "BEAR_TRENDING":
            profile = "Conservative"
        elif market_condition == "HIGH_VOLATILITY":
            profile = "Scalping"
        else:
            profile = "Balanced"
        st.metric("🎯 Active Profile", profile)

# Portfolio tab function
def render_portfolio_tab(portfolio, gbp_rate, selected_pairs):
    st.subheader("💼 Portfolio Holdings")
    total_usd = sum(coin['usd_value'] for coin in portfolio.values())

    for category, assets in selected_pairs.items():
        st.markdown(f"### 📊 {category} Pairs")
        for asset in assets:
            if asset not in portfolio:
                continue
            data = portfolio[asset]
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            with col1: st.write(f"**{asset}**")
            with col2: st.write(f"{data['balance']:.4f}")
            with col3: st.write(f"${data['price_usd']:.4f}")
            with col4: st.write(f"${data['usd_value']:.2f}")
            with col5: st.write(f"£{data['gbp_value']:.2f}")
            with col6: st.write(f"{(data['usd_value'] / total_usd * 100):.1f}%")

# Risk profile tab
def render_risk_profile_tab():
    st.subheader("🛡️ Risk Profile Settings")
    selected = st.radio("Choose a Risk Profile Override", ["AUTO", "Aggressive", "Swing", "Balanced", "Conservative", "Scalping"])
    st.session_state.selected_profile = selected
    st.success(f"Active Profile: {selected}")

# Main layout with tabs
def main():
    portfolio, gbp_rate = get_demo_portfolio()
    market_condition, condition_score, avg_volatility = simulate_market_analysis(portfolio)

    from utils import SELECTED_PAIRS

    tab1, tab2, tab3 = st.tabs(["🏠 Overview", "💼 Portfolio", "🛡️ Risk Profiles"])
    with tab1:
        render_overview_tab(portfolio, gbp_rate, market_condition, condition_score, avg_volatility)
    with tab2:
        render_portfolio_tab(portfolio, gbp_rate, SELECTED_PAIRS)
    with tab3:
        render_risk_profile_tab()

if __name__ == "__main__":
    main()
