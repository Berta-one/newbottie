import streamlit as st
import pandas as pd
from datetime import datetime
from trader import get_account_balance
from binance.client import Client
import os

# --- Helper: Get current signal, confidence, and price (live) ---
from strategy import check_breakout_enhanced, get_strategy_confidence
def get_current_signal(symbol='BTCUSDT', interval='5m', lookback=120):
    client = get_binance_client()
    try:
        klines = client.get_klines(symbol=symbol, interval=interval, limit=lookback)
        signal = check_breakout_enhanced(klines)
        confidence = get_strategy_confidence(klines)
        price = float(klines[-1][4])
        # Map signal to BUY/SELL/HOLD for dashboard
        if signal == 'BUY_LONG':
            signal_out = 'BUY'
        elif signal == 'BUY_SHORT':
            signal_out = 'SELL'
        else:
            signal_out = 'HOLD'
        return signal_out, confidence, price
    except Exception as e:
        st.error(f"Error loading market signal: {e}")
        return 'HOLD', 0.0, 0.0

# --- Helper: Get Binance client ---
def get_binance_client():
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    return Client(api_key, api_secret)

# --- Helper: Get open positions (live) ---
def get_open_positions():
    client = get_binance_client()
    try:
        account = client.get_account()
        positions = []
        for bal in account['balances']:
            free = float(bal['free'])
            locked = float(bal['locked'])
            if (free + locked) > 0 and bal['asset'] not in ['USDT', 'BUSD', 'USDC']:
                positions.append({
                    'Asset': bal['asset'],
                    'Free': free,
                    'Locked': locked,
                    'Total': free + locked
                })
        return positions
    except Exception as e:
        st.error(f"Error loading open positions: {e}")
        return []

# --- Helper: Get trade history (from logs) ---
def get_trade_history():
    try:
        df = pd.read_csv('logs/trades.csv')
        return df.to_dict('records')
    except Exception:
        return []
from strategy import get_current_signal

# --- Bot Trade Dashboard (Live Data) ---
def bot_trade_dashboard():
    st.title("🤖 Bot Trade (Live)")
    st.caption("Live trading dashboard with real Binance data and signals")

    # --- Status indicators ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Status", "🟢 Online", "24/7 Active")
    with col2:
        st.metric("Platform", "Binance", "Live")
    with col3:
        client = get_binance_client()
        balance = get_account_balance(client, 'USDT')
        st.metric("USDT Balance", f"${balance:,.2f}")
    with col4:
        st.metric("Time", datetime.now().strftime("%H:%M:%S"), "Live")

    # --- Market Signal ---
    st.subheader("📈 Market Signal")
    signal, confidence, price = get_current_signal()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("BTC/USDT", f"${price:,.2f}")
    with col2:
        signal_color = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "🟡"
        st.metric(f"{signal_color} Signal", signal, f"Conf: {confidence:.1%}")
    with col3:
        st.metric("Strategy", "Live ML/Breakout", "Auto")

    # --- Open Positions ---
    st.subheader("📊 Open Positions")
    positions = get_open_positions()
    if positions:
        df = pd.DataFrame(positions)
        st.dataframe(df)
    else:
        st.info("No open positions.")

    # --- Trade History ---
    st.subheader("📋 Trade History")
    trades = get_trade_history()
    if trades:
        df = pd.DataFrame(trades)
        st.dataframe(df)
    else:
        st.info("No trade history yet.")

    # --- Configuration ---
    with st.expander("⚙️ Bot Configuration"):
        st.json({
            "Strategy": "Live ML/Breakout",
            "Risk": st.session_state.get('risk', 0.015),
            "Max Positions": st.session_state.get('max_positions', 3),
            "Scan Interval": st.session_state.get('scan_interval', 60),
            "Mode": "Live"
        })

    # --- Next steps/help ---
    st.subheader("🚀 Next Steps")
    st.info("""
    **Current Status:** ✅ Live trading enabled with real Binance data.
    - Monitor open positions and trade history above.
    - All trades and signals are based on live market data.
    """)
