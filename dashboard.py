
# Updated dashboard.py with integrated overview, portfolio, manual override, and dedicated risk profile tab

import streamlit as st
import pandas as pd
import plotly.express as px
import os, json, time, socket, subprocess
from datetime import datetime
from dotenv import load_dotenv
from bot_controller import BotController
import requests
import numpy as np

try:
    from binance.client import Client
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False

load_dotenv()
PIN_REQUIRED = os.getenv("DASHBOARD_PIN", "1234")

if "controller" not in st.session_state:
    st.session_state.controller = BotController()
controller = st.session_state.controller

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if 'override_profile' not in st.session_state:
    st.session_state.override_profile = "Auto"

class AdaptiveRiskManager:
    def __init__(self):
        self.risk_profiles = {
            "CONSERVATIVE": {
                "name": "Conservative",
                "take_profit": 6.0,
                "stop_loss": 4.0,
                "trailing_stop": 2.5,
                "max_hold_hours": 6,
                "confidence_threshold": 0.8,
                "description": "Low volatility, high confidence trades"
            },
            "BALANCED": {
                "name": "Balanced", 
                "take_profit": 10.0,
                "stop_loss": 8.0,
                "trailing_stop": 3.5,
                "max_hold_hours": 4,
                "confidence_threshold": 0.7,
                "description": "Standard institutional approach"
            },
            "AGGRESSIVE": {
                "name": "Aggressive",
                "take_profit": 15.0,
                "stop_loss": 12.0,
                "trailing_stop": 5.0,
                "max_hold_hours": 8,
                "confidence_threshold": 0.6,
                "description": "High volatility, trend-following"
            },
            "SCALPING": {
                "name": "Scalping",
                "take_profit": 3.0,
                "stop_loss": 2.0,
                "trailing_stop": 1.0,
                "max_hold_hours": 1,
                "confidence_threshold": 0.85,
                "description": "Quick profits, minimal risk"
            },
            "SWING": {
                "name": "Swing Trading",
                "take_profit": 20.0,
                "stop_loss": 15.0,
                "trailing_stop": 8.0,
                "max_hold_hours": 24,
                "confidence_threshold": 0.75,
                "description": "Multi-day position holding"
            }
        }

if 'risk_manager' not in st.session_state:
    st.session_state.risk_manager = AdaptiveRiskManager()
risk_manager = st.session_state.risk_manager

def get_gbp_exchange_rate():
    try:
        apis = [
            "https://api.exchangerate-api.com/v4/latest/USD",
            "https://api.fxratesapi.com/latest?base=USD"
        ]
        for api_url in apis:
            try:
                response = requests.get(api_url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if 'rates' in data and 'GBP' in data['rates']:
                        return data['rates']['GBP']
            except:
                continue
        return 0.79
    except:
        return 0.79

def get_demo_portfolio():
    gbp_rate = get_gbp_exchange_rate()
    portfolio = {
        'XRP': {'balance': 500.00000023, 'usd_value': 1482.85, 'symbol': 'XRPUSDT', 'price_usd': 2.98},
        'SOL': {'balance': 7.69637064, 'usd_value': 1285.99, 'symbol': 'SOLUSDT', 'price_usd': 167.70},
        'ETHW': {'balance': 0.74740045, 'usd_value': 1.15, 'symbol': 'ETHWUSDT', 'price_usd': 1.54},
    }
    for asset in portfolio:
        portfolio[asset]['gbp_value'] = portfolio[asset]['usd_value'] * gbp_rate
        portfolio[asset]['pnl_gbp'] = np.random.uniform(-20, 20)  # Simulated daily PnL in GBP
    return portfolio, gbp_rate

def simulate_market_analysis(portfolio):
    avg_volatility = np.random.uniform(1.5, 3.5)
    conditions = ["BULL_TRENDING", "BEAR_TRENDING", "CONSOLIDATING", "HIGH_VOLATILITY", "UNCERTAIN"]
    market_condition = np.random.choice(conditions)
    condition_score = np.random.uniform(0.3, 0.9)
    return market_condition, condition_score, avg_volatility

def render_dashboard_section(portfolio, gbp_rate, market_condition, condition_score, avg_volatility):
    total_usd = sum(coin['usd_value'] for coin in portfolio.values())
    total_gbp = total_usd * gbp_rate

    st.subheader("📊 Market Overview")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💷 Portfolio Value", f"£{total_gbp:,.2f}")
    with col2:
        condition_color = "🟢" if condition_score > 0.6 else "🟡" if condition_score > 0.4 else "🔴"
        st.metric(f"{condition_color} Market", market_condition.replace('_', ' ').title())
    with col3:
        st.metric("📈 Volatility", f"{avg_volatility:.1f}%")
    with col4:
        if st.session_state.override_profile != "Auto":
            profile = st.session_state.override_profile
        else:
            if market_condition == "BULL_TRENDING":
                profile = "Aggressive" if avg_volatility > 2.5 else "Swing"
            elif market_condition == "BEAR_TRENDING":
                profile = "Conservative"
            elif market_condition == "HIGH_VOLATILITY":
                profile = "Scalping"
            else:
                profile = "Balanced"
        st.metric("🎯 Active Profile", profile)

    st.divider()
    st.subheader("💼 Portfolio Holdings")
    df_data = []
    total_usd = sum(coin['usd_value'] for coin in portfolio.values())
    for asset, data in portfolio.items():
        df_data.append({
            "Asset": asset,
            "Amount": f"{data['balance']:.6f}",
            "Coin Price": f"${data['price_usd']:.2f}",
            "Value (USD)": f"${data['usd_value']:.2f}",
            "Value (GBP)": f"£{data['gbp_value']:.2f}",
            "Today's PnL": f"{'+' if data['pnl_gbp'] >= 0 else '-'}£{abs(data['pnl_gbp']):.2f}"
        })
    st.dataframe(pd.DataFrame(df_data), use_container_width=True)

def render_risk_profiles_tab():
    st.subheader("🛡️ Professional Risk Profiles")
    for key, profile in risk_manager.risk_profiles.items():
        with st.expander(f"{profile['name']}"):
            st.markdown(f"**Description:** {profile['description']}")
            st.markdown(f"- **Take Profit:** {profile['take_profit']}%")
            st.markdown(f"- **Stop Loss:** {profile['stop_loss']}%")
            st.markdown(f"- **Trailing Stop:** {profile['trailing_stop']}%")
            st.markdown(f"- **Max Hold:** {profile['max_hold_hours']} hours")
            st.markdown(f"- **Confidence Threshold:** {profile['confidence_threshold']:.0%}")

def render_settings_tab():
    st.subheader("⚙️ Settings")
    profile_names = ["Auto"] + [p["name"] for p in risk_manager.risk_profiles.values()]
    selection = st.selectbox("🎯 Override Risk Profile", profile_names, index=0)
    st.session_state.override_profile = selection

def dashboard():
    portfolio, gbp_rate = get_demo_portfolio()
    market_condition, condition_score, avg_volatility = simulate_market_analysis(portfolio)
    tab1, tab2 = st.tabs(["📋 Dashboard", "🧠 Risk Profiles"])
    with tab1:
        render_dashboard_section(portfolio, gbp_rate, market_condition, condition_score, avg_volatility)
    with tab2:
        render_risk_profiles_tab()
        render_settings_tab()

def main():
    st.set_page_config(page_title="Adaptive Bot", layout="wide")
    if not st.session_state.authenticated:
        st.title("🔐 Enter PIN")
        user_pin = st.text_input("PIN", type="password")
        if user_pin == PIN_REQUIRED:
            st.session_state.authenticated = True
            st.success("Access granted")
            st.rerun()
        elif user_pin:
            st.error("Incorrect PIN")
    else:
        st.title("📈 Adaptive Risk Management Bot")
        dashboard()

if __name__ == "__main__":
    main()
