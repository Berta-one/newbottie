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

def get_tailscale_ip():
    try:
        output = subprocess.check_output("tailscale ip -4", shell=True, text=True).strip()
        return output.splitlines()[0]
    except:
        return "Unavailable"

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
        'BTC': {'balance': 0.15234, 'usd_value': 9890.45, 'symbol': 'BTCUSDT', 'price_usd': 64950.0},
        'ETH': {'balance': 1.8945, 'usd_value': 4567.89, 'symbol': 'ETHUSDT', 'price_usd': 2410.50},
        'SOL': {'balance': 45.67, 'usd_value': 2876.32, 'symbol': 'SOLUSDT', 'price_usd': 62.98},
        'XRP': {'balance': 1250.0, 'usd_value': 743.75, 'symbol': 'XRPUSDT', 'price_usd': 0.595},
        'ADA': {'balance': 2890.5, 'usd_value': 1234.56, 'symbol': 'ADAUSDT', 'price_usd': 0.427}
    }
    for asset in portfolio:
        portfolio[asset]['gbp_value'] = portfolio[asset]['usd_value'] * gbp_rate
    return portfolio, gbp_rate

def simulate_market_analysis(portfolio):
    market_data = []
    for asset, data in portfolio.items():
        simulated_klines = []
        base_price = data['price_usd']
        for i in range(120):
            change = np.random.uniform(-0.002, 0.002)
            base_price *= (1 + change)
            simulated_klines.append([
                0, str(base_price), str(base_price * 1.001), 
                str(base_price * 0.999), str(base_price), str(np.random.uniform(100, 1000)),
                0, 0, 0, 0, 0, 0
            ])
        market_data.append({
            'asset': asset,
            'klines': simulated_klines,
            'symbol': data['symbol']
        })
    avg_volatility = np.random.uniform(1.5, 3.5)
    conditions = ["BULL_TRENDING", "BEAR_TRENDING", "CONSOLIDATING", "HIGH_VOLATILITY", "UNCERTAIN"]
    market_condition = np.random.choice(conditions)
    condition_score = np.random.uniform(0.3, 0.9)
    return market_condition, condition_score, avg_volatility

def load_logs(log_file, max_lines=200):
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            return f.readlines()[-max_lines:]
    return ["No logs found."]

def load_trade_data():
    log_path = "logs/single_pair_performance.json"
    try:
        df = pd.read_json(log_path, lines=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        return df
    except:
        demo_data = []
        for i in range(20):
            demo_data.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': 'BTCUSDT',
                'pnl_percent': np.random.uniform(-3, 8),
                'reason': np.random.choice(['Take Profit', 'Stop Loss', 'Time Limit']),
                'confidence': np.random.uniform(0.6, 0.9)
            })
        return pd.DataFrame(demo_data)

def render_overview_tab(portfolio, gbp_rate, market_condition, condition_score, avg_volatility):
    """Render the main overview tab"""
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
    st.info("See the Portfolio tab for detailed holdings.")

def render_portfolio_tab(portfolio, gbp_rate):
    st.subheader("💼 Portfolio Holdings")
    total_usd = sum(coin['usd_value'] for coin in portfolio.values())
    portfolio_data = []
    for asset, data in portfolio.items():
        portfolio_data.append({
            'Asset': asset,
            'Balance': f"{data['balance']:.4f}",
            'Price (USD)': f"${data['price_usd']:.4f}",
            'Value (USD)': f"${data['usd_value']:.2f}",
            'Value (GBP)': f"£{data['gbp_value']:.2f}",
            'Percentage': f"{(data['usd_value'] / total_usd * 100):.1f}%"
        })
    df = pd.DataFrame(portfolio_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

# All other render_ functions remain unchanged...

def dashboard():
    """Main dashboard function"""
    portfolio, gbp_rate = get_demo_portfolio()
    market_condition, condition_score, avg_volatility = simulate_market_analysis(portfolio)
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏠 Overview",
        "💼 Portfolio",
        "📊 Performance", 
        "🛡️ Risk Profiles",
        "📡 Logs",
        "⚙️ Settings"
    ])
    with tab1:
        render_overview_tab(portfolio, gbp_rate, market_condition, condition_score, avg_volatility)
    with tab2:
        render_portfolio_tab(portfolio, gbp_rate)
    with tab3:
        render_performance_tab()
    with tab4:
        render_risk_profiles_tab()
    with tab5:
        render_logs_tab()
    with tab6:
        render_settings_tab()

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
        dashboard()

if __name__ == "__main__":
    main()
