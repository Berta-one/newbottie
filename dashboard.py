def get_demo_portfolio():
    """Get demo portfolio data"""
    gbp_rate = get_gbp_exchange_rate()
    portfolio = {
        'BTC': {'balance': 0.15234, 'usd_value': 9890.45, 'symbol': 'BTCUSDT', 'price_usd': 64950.0},
        'ETH': {'balance': 1.8945, 'usd_value': 4567.89, 'symbol': 'ETHUSDT', 'price_usd': 2410.50},
        'SOL': {'balance': 45.67, 'usd_value': 2876.32, 'symbol': 'SOLUSDT', 'price_usd': 62.98},
        'XRP': {'balance': 1250.0, 'usd_value': 743.75, 'symbol': 'XRPUSDT', 'price_usd': 0.595},
        'ADA': {'balance': 2890.5, 'usd_value': 1234.56, 'symbol': 'ADAUSDT', 'price_usd': 0.427}
    }
    # Add GBP values
    for asset in portfolio:
        portfolio[asset]['gbp_value'] = portfolio[asset]['usd_value'] * gbp_rate
    return portfolio, gbp_rate

# dashboard.py - Updated with Clean Tabbed Interface and Adaptive Risk Management
import streamlit as st
import pandas as pd
import plotly.express as px
import os, json, time, socket, subprocess
from datetime import datetime
from dotenv import load_dotenv
from bot_controller import BotController
from binance_client import client as binance_client
import requests
import numpy as np

# Check if we have Binance library
try:
    from binance.client import Client
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False

load_dotenv()
PIN_REQUIRED = os.getenv("DASHBOARD_PIN", "1234")

# Session state controller
if "controller" not in st.session_state:
    st.session_state.controller = BotController()
controller = st.session_state.controller

# PIN protection
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

class AdaptiveRiskManager:
    def __init__(self):
        # Professional risk management rulesets
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

# Initialize risk manager globally
if 'risk_manager' not in st.session_state:
    st.session_state.risk_manager = AdaptiveRiskManager()
risk_manager = st.session_state.risk_manager

def get_tailscale_ip():
    try:
        output = subprocess.check_output("tailscale ip -4", shell=True, text=True).strip()
        return output.splitlines()[0]
    except:
        return "Unavailable"

def get_gbp_exchange_rate():
    """Get live USD to GBP exchange rate"""
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
        
        # Fallback rate
        return 0.79
    except:
        return 0.79

def main():
    st.set_page_config(page_title="🎯 Adaptive Risk Management Bot", layout="wide")
    
    if not st.session_state.authenticated:
        st.title("🔐 Enter Dashboard PIN")
        user_pin = st.text_input("PIN", type="password")

        if user_pin == PIN_REQUIRED:
            st.session_state.authenticated = True
            st.success("Access granted")
            st.rerun()
        elif user_pin:
            st.error("Incorrect PIN")
    else:
        st.title("🎯 Adaptive Risk Management Trading Bot")
        st.caption("Professional, emotion-free trading with dynamic risk adjustment")
        
        # Use real or demo portfolio based on USE_TESTNET
        use_testnet = os.getenv("USE_TESTNET", "True").lower() == "true"
        portfolio, gbp_rate = get_demo_portfolio()
        
        # Simple status display
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💷 Portfolio Value", f"£{sum(p['gbp_value'] for p in portfolio.values()):,.2f}")
        
        with col2:
            st.metric("🎯 Mode", "TESTNET" if use_testnet else "LIVE")
        
        with col3:
            st.metric("🪙 Assets", len(portfolio))
        
        with col4:
            st.metric("⏰ Time", datetime.now().strftime("%H:%M:%S"))
        
        # Portfolio overview
        st.subheader("💼 Portfolio Overview")
        
        portfolio_data = []
        for asset, data in portfolio.items():
            portfolio_data.append({
                'Asset': asset,
                'Balance': f"{data['balance']:.4f}",
                'USD Value': f"${data['usd_value']:.2f}",
                'GBP Value': f"£{data['gbp_value']:.2f}",
            })
        
        df = pd.DataFrame(portfolio_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()