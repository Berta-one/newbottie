import os
import time
import streamlit as st
from datetime import datetime
import pandas as pd
import json

# Simulate Binance connection (will add real API later)
class MockBinanceClient:
    def __init__(self):
        self.base_price = 65000
        self.price_drift = 0
        
    def get_klines(self, symbol, interval, limit):
        # Generate realistic-looking price data
        import random
        klines = []
        current_price = self.base_price
        
        for i in range(120):  # 2 hours of 1-minute data
            # Simulate price movement
            change = random.uniform(-0.005, 0.005)  # Increased volatility
            current_price *= (1 + change)
            
            klines.append([
                int(time.time()) * 1000,  # timestamp
                str(current_price),       # open
                str(current_price * 1.001),  # high
                str(current_price * 0.999),  # low
                str(current_price),       # close
                str(random.uniform(100, 1000)),  # volume
                0, 0, 0, 0, 0, 0  # padding
            ])
        
        return klines
    
    def get_symbol_ticker(self, symbol):
        import random
        price = self.base_price + random.uniform(-1000, 1000)
        return {'price': str(price)}
    
    def get_account(self):
        return {
            'balances': [
                {'asset': 'USDT', 'free': '10000.00', 'locked': '0.00'},
                {'asset': 'BTC', 'free': '0.15234', 'locked': '0.00'}
            ]
        }

# Simple strategy simulation
def analyze_market(klines):
    # Calculate 2-hour price change
    if len(klines) < 120:
        return "HOLD", 0.5
    
    start_price = float(klines[0][4])  # close price 2 hours ago
    current_price = float(klines[-1][4])  # current close price
    
    change_pct = ((current_price - start_price) / start_price) * 100
    
    # Relaxed breakout strategy
    if change_pct >= 2.0:
        return "BUY_LONG", 0.75
    elif change_pct <= -2.0:
        return "BUY_SHORT", 0.70
    else:
        return "HOLD", 0.60

# Trading bot dashboard
def trading_dashboard():
    st.set_page_config(page_title="🤖 Live Crypto Trading Bot", layout="wide")
    st.title("🤖 Live Crypto Trading Bot - Railway Deployment")
    st.caption("Real-time market analysis and trading simulation")

    # Initialize mock client
    if 'client' not in st.session_state:
        st.session_state.client = MockBinanceClient()
        st.session_state.trades = []
        st.session_state.positions = {}
        st.session_state.selected_symbol = "BTCUSDT"

    client = st.session_state.client

    # Symbol selection UI
    available_symbols = [
        "BTCUSDT", "ETHUSDT", "DOGEUSDT", "SHIBUSDT", "PEPEUSDT", "FLOKIUSDT",
        "SOLUSDT", "AVAXUSDT", "LTCUSDT", "XRPUSDT", "BNBUSDT", "ADAUSDT",
        "MATICUSDT", "ARBUSDT", "OPUSDT", "SUIUSDT", "INJUSDT", "JUPUSDT",
        "ETHBTC", "SOLBNB", "BNBBTC", "ADAETH", "LTCBTC"
    ]
    st.session_state.selected_symbol = st.selectbox("Select Trading Pair", available_symbols, index=available_symbols.index(st.session_state.selected_symbol) if st.session_state.selected_symbol in available_symbols else 0)
    symbol = st.session_state.selected_symbol

    # Real-time status
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🟢 Status", "LIVE", "24/7 Active")
    with col2:
        st.metric("☁️ Platform", "Railway", "Cloud Hosted")
    with col3:
        account = client.get_account()
        # Show all balances
        balances = {b['asset']: float(b['free']) for b in account['balances']}
        balance_str = ", ".join([f"{asset}: {amount}" for asset, amount in balances.items()])
        st.metric("💰 Balances", balance_str)
    with col4:
        st.metric("⏰ Server Time", datetime.now().strftime("%H:%M:%S"), "Live")

    # Market analysis section
    st.subheader(f"📈 Real-Time Market Analysis for {symbol}")
    klines = client.get_klines(symbol, "1m", 120)
    ticker = client.get_symbol_ticker(symbol)
    current_price = float(ticker['price'])
    signal, confidence = analyze_market(klines)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"💰 {symbol}", f"{current_price:,.6f}", f"{((current_price - 65000) / 65000 * 100):+.2f}%")
    with col2:
        signal_color = "🟢" if signal == "BUY_LONG" else "🔴" if signal == "BUY_SHORT" else "🟡"
        st.metric(f"{signal_color} Signal", signal, f"Confidence: {confidence:.1%}")
    with col3:
        start_price = float(klines[0][4])
        change_2h = ((current_price - start_price) / start_price) * 100
        st.metric("📊 2h Change", f"{change_2h:+.2f}%", "Breakout Threshold: ±2% (Relaxed)")
    
    # Trading simulation
    st.subheader("🎯 Trading Simulation")
    
    # Auto-execute trades based on signals
    if signal != "HOLD" and signal not in st.session_state.positions:
        # Simulate trade execution
        trade = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "action": signal,
            "price": current_price,
            "confidence": confidence,
            "status": "EXECUTED"
        }
        st.session_state.trades.append(trade)
        st.session_state.positions[signal] = {
            "entry_price": current_price,
            "entry_time": datetime.now(),
            "signal": signal
        }
        
        st.success(f"🎯 Trade Executed: {signal} at ${current_price:,.2f}")
    
    # Monitor open positions
    for signal, position in list(st.session_state.positions.items()):
        entry_price = position["entry_price"]
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        
        # Auto-close positions at ±10%
        if abs(pnl_pct) >= 10:
            exit_trade = {
                "time": datetime.now().strftime("%H:%M:%S"),
                "action": f"CLOSE_{signal}",
                "price": current_price,
                "pnl": pnl_pct,
                "status": "CLOSED"
            }
            st.session_state.trades.append(exit_trade)
            del st.session_state.positions[signal]
            
            if pnl_pct > 0:
                st.success(f"💰 Position Closed: {pnl_pct:+.2f}% PROFIT")
            else:
                st.error(f"📉 Position Closed: {pnl_pct:+.2f}% LOSS")
    
    # Display open positions
    if st.session_state.positions:
        st.subheader("📊 Open Positions")
        for signal, position in st.session_state.positions.items():
            entry_price = position["entry_price"]
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
            time_held = (datetime.now() - position["entry_time"]).total_seconds() / 60
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.text(f"Signal: {signal}")
            with col2:
                st.text(f"Entry: ${entry_price:,.2f}")
            with col3:
                color = "green" if pnl_pct > 0 else "red"
                st.markdown(f"P&L: <span style='color:{color}'>{pnl_pct:+.2f}%</span>", 
                           unsafe_allow_html=True)
            with col4:
                st.text(f"Time: {time_held:.0f}m")
    
    # Trading history
    st.subheader("📋 Recent Trading Activity")
    
    if st.session_state.trades:
        # Show last 10 trades
        recent_trades = st.session_state.trades[-10:]
        trade_df = pd.DataFrame(recent_trades)
        st.dataframe(trade_df, use_container_width=True)
        
        # Calculate performance
        closed_trades = [t for t in st.session_state.trades if 'pnl' in t]
        if closed_trades:
            total_pnl = sum(t['pnl'] for t in closed_trades)
            win_rate = len([t for t in closed_trades if t['pnl'] > 0]) / len(closed_trades) * 100
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🎯 Total Trades", len(closed_trades))
            with col2:
                st.metric("📈 Win Rate", f"{win_rate:.1f}%")
            with col3:
                color = "green" if total_pnl > 0 else "red"
                st.markdown(f"💰 Total P&L: <span style='color:{color}'>{total_pnl:+.2f}%</span>", 
                           unsafe_allow_html=True)
    else:
        st.info("🕐 Waiting for trading signals... The bot scans every minute for 5% breakouts.")
    
    # Configuration display
    with st.expander("⚙️ Bot Configuration"):
        st.json({
            "Strategy": "5% Breakout Detection",
            "Timeframe": "2 hours (120 x 1-minute candles)",
            "Take Profit": "10%",
            "Stop Loss": "10%",
            "Risk per Trade": "1.5%",
            "Mode": "Paper Trading (Simulation)",
            "Exchange": "Binance (Simulated)",
            "Auto Refresh": "Every 5 seconds"
        })
    
    # Auto-refresh every 5 seconds
    time.sleep(1)
    st.rerun()

if __name__ == "__main__":
    trading_dashboard()
