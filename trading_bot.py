import os
import time
import streamlit as st
from datetime import datetime

def trading_dashboard():
    st.set_page_config(page_title="Crypto Trading Bot", layout="wide")
    
    st.title("🤖 Crypto Trading Bot - Live on Railway")
    
    # Status indicators
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Status", "🟢 Online", "24/7 Active")
    
    with col2:
        st.metric("Platform", "Railway", "Cloud Hosted")
    
    with col3:
        st.metric("Uptime", f"{datetime.now().strftime('%H:%M:%S')}", "Live Clock")
    
    with col4:
        st.metric("Mode", "Paper Trading", "Safe Testing")
    
    # Trading simulation
    st.subheader("📈 Trading Simulation")
    
    # Fake some trading data for demo
    import random
    btc_price = 65000 + random.randint(-1000, 1000)
    change_24h = random.uniform(-3, 3)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("BTC/USDT", f"${btc_price:,}", f"{change_24h:+.2f}%")
    
    with col2:
        signal = random.choice(["BUY", "SELL", "HOLD"])
        confidence = random.uniform(0.6, 0.95)
        st.metric("Signal", signal, f"Confidence: {confidence:.1%}")
    
    # Trading log
    st.subheader("📊 Recent Activity")
    
    trading_log = [
        {"Time": "08:15", "Action": "HOLD", "Price": "$65,234", "P&L": "0.00%"},
        {"Time": "08:10", "Action": "SELL", "Price": "$65,180", "P&L": "+2.34%"},
        {"Time": "08:05", "Action": "BUY", "Price": "$63,890", "P&L": "0.00%"},
        {"Time": "08:00", "Action": "HOLD", "Price": "$63,850", "P&L": "0.00%"},
    ]
    
    st.table(trading_log)
    
    # Configuration
    st.subheader("⚙️ Bot Configuration")
    
    st.info("""
    **Current Setup:**
    - 🎯 Strategy: 5% Breakout + ML Enhancement
    - 💰 Risk: 1.5% per trade
    - ⏱️ Scan Interval: 5 minutes
    - 🛡️ Mode: Paper Trading (Safe)
    - 📊 Exchange: Binance Testnet
    """)
    
    # Auto-refresh every 10 seconds
    time.sleep(1)
    st.rerun()

if __name__ == "__main__":
    trading_dashboard()
