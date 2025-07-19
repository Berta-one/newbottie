#!/usr/bin/env python3
"""
Complete Enhanced Crypto Trading Bot Dashboard - FIXED TABS VERSION
================================================================

Company: Rondanini Publishing Ltd.  
Website: https://www.rondanini.net

This version fixes the missing tabs issue with a simplified approach.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
import time
import threading
import subprocess
import sys
import signal
import requests
import random
import csv
import logging
import numpy as np

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Check for Binance
try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False

# Import existing trading modules
TRADING_MODULES_AVAILABLE = False
try:
    from strategy import check_breakout_enhanced, get_strategy_confidence, analyze_pair_strength
    from trader import calculate_dynamic_position_size, monitor_position_enhanced, execute_entry, execute_exit, get_account_balance
    from multi_pair_scanner import CryptoPairScanner
    from bot_controller import AdaptiveRiskManager
    TRADING_MODULES_AVAILABLE = True
except ImportError as e:
    pass

# Import quantum modules (optional)
try:
    from quantum_engine import QuantumTradingEngine
    from quantum_trading_integration import get_quantum_trader
    QUANTUM_AVAILABLE = True
except ImportError:
    QUANTUM_AVAILABLE = False

# Configuration
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')
USE_TESTNET = False  # ALWAYS LIVE TRADING
MIN_BALANCE_USD = 10.0

def get_binance_client():
    """Get live Binance client"""
    if not BINANCE_AVAILABLE or not API_KEY or not API_SECRET:
        return None
    try:
        return Client(API_KEY, API_SECRET)
    except Exception as e:
        st.error(f"Binance client error: {e}")
        return None

def get_gbp_exchange_rate():
    """Get USD to GBP exchange rate"""
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        return response.json()['rates']['GBP']
    except:
        return 0.79

def ensure_log_files():
    """Create required log files"""
    os.makedirs('logs', exist_ok=True)
    
    if not os.path.exists('logs/trades.csv'):
        with open('logs/trades.csv', 'w') as f:
            f.write('timestamp,symbol,direction,entry_price,exit_price,quantity,change_pct,status,strategy,confidence\n')
    
    log_files = ['logs/manual_trades.log', 'logs/portfolio_scans.log', 'logs/console_output.log']
    for log_file in log_files:
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                f.write(f"# Log created: {datetime.now()}\n")

def get_real_portfolio():
    """Get real portfolio from Binance with GBP conversion"""
    client = get_binance_client()
    if not client:
        return {}, 0, 0
    
    try:
        account = client.get_account()
        tickers = {t['symbol']: float(t['price']) for t in client.get_all_tickers()}
        
        portfolio = {}
        total_usd = 0
        
        for balance in account['balances']:
            asset = balance['asset']
            total_balance = float(balance['free']) + float(balance['locked'])
            
            if total_balance > 0:
                if asset in ['USDT', 'BUSD', 'USDC']:
                    price_usd = 1.0
                else:
                    pair = f"{asset}USDT"
                    price_usd = tickers.get(pair, 0)
                
                usd_value = total_balance * price_usd
                
                if usd_value >= MIN_BALANCE_USD:
                    try:
                        change_24h = float(client.get_ticker(symbol=f"{asset}USDT")['priceChangePercent'])
                    except:
                        change_24h = 0
                    
                    portfolio[asset] = {
                        'balance': total_balance,
                        'price_usd': price_usd,
                        'usd_value': usd_value,
                        'change_24h': change_24h
                    }
                    total_usd += usd_value
        
        gbp_rate = get_gbp_exchange_rate()
        total_gbp = total_usd * gbp_rate
        
        return portfolio, total_usd, total_gbp
    except Exception as e:
        st.error(f"Portfolio error: {e}")
        return {}, 0, 0

def get_open_positions():
    """Get current open positions"""
    client = get_binance_client()
    if not client:
        return []
    
    try:
        account = client.get_account()
        positions = []
        
        for balance in account['balances']:
            asset = balance['asset']
            total = float(balance['free']) + float(balance['locked'])
            
            if total > 0 and asset != 'USDT':
                try:
                    price = float(client.get_symbol_ticker(symbol=f"{asset}USDT")['price'])
                    usd_value = total * price
                    
                    if usd_value >= MIN_BALANCE_USD:
                        positions.append({
                            'Asset': asset,
                            'Total': total,
                            'USD Value': usd_value,
                            'Price': price
                        })
                except:
                    continue
        
        return positions
    except:
        return []

def initialize_session_state():
    """Initialize session state"""
    defaults = {
        'password_authenticated': False,
        'dashboard_password': 'bottie',
        'auto_trader_running': False,
        'selected_strategy': 'Breakout',
        'selected_risk_level': 'BALANCED',
        'current_tab': 'Overview'  # Track current tab
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# TAB RENDER FUNCTIONS
def render_overview_tab():
    """Overview tab content"""
    st.header("🎯 Live Trading Overview")
    st.caption("Real-time portfolio monitoring - LIVE TRADING MODE")
    
    portfolio, total_usd, total_gbp = get_real_portfolio()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Trading Mode", "🔴 LIVE", "Real Money")
    
    with col2:
        client = get_binance_client()
        if client and TRADING_MODULES_AVAILABLE:
            try:
                balance = get_account_balance(client, 'USDT')
                st.metric("USDT Balance", f"${balance:,.2f}")
            except:
                st.metric("USDT Balance", "Error")
        else:
            st.metric("USDT Balance", "N/A")
    
    with col3:
        st.metric("Portfolio USD", f"${total_usd:,.2f}")
    
    with col4:
        st.metric("Portfolio GBP", f"£{total_gbp:,.2f}")
    
    # Portfolio table
    st.subheader("📊 Current Portfolio")
    if portfolio:
        df_data = []
        gbp_rate = get_gbp_exchange_rate()
        
        for asset, data in portfolio.items():
            gbp_value = data['usd_value'] * gbp_rate
            df_data.append({
                'Asset': asset,
                'Balance': f"{data['balance']:.6f}",
                'Price USD': f"${data['price_usd']:.4f}",
                'USD Value': f"${data['usd_value']:.2f}",
                'GBP Value': f"£{gbp_value:.2f}",
                '24h Change': f"{data['change_24h']:+.2f}%"
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No significant positions found")
    
    # Trading controls
    st.subheader("🚀 Trading Controls")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Start Auto Trader", type="primary"):
            st.session_state['auto_trader_running'] = True
            st.success("Auto trader started!")
    
    with col2:
        if st.button("⏹️ Stop Auto Trader", type="secondary"):
            st.session_state['auto_trader_running'] = False
            st.warning("Auto trader stopped")
    
    with col3:
        if st.button("📊 Refresh Data"):
            st.rerun()

def render_strategy_tab():
    """Strategy configuration tab"""
    st.header("⚙️ Strategy & Risk Configuration")
    st.caption("Configure trading strategies and risk management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Strategy Selection")
        
        strategies = ['Breakout', 'ML Enhanced', 'Relaxed', 'Scalping', 'Swing', 'Conservative']
        selected = st.selectbox("Trading Strategy", strategies, key="strategy_select")
        st.session_state['selected_strategy'] = selected
        
        descriptions = {
            'Breakout': '5% breakout with volume and time filters',
            'ML Enhanced': 'Machine learning enhanced signals',
            'Relaxed': 'Multiple strategy ensemble approach',
            'Scalping': 'Quick 2-3% moves with high volume',
            'Swing': 'Longer-term 10-20% moves',
            'Conservative': 'Safe trading with reduced risk'
        }
        
        st.info(f"📝 **{selected}**: {descriptions.get(selected, 'Custom strategy')}")
    
    with col2:
        st.subheader("⚖️ Risk Management")
        
        risk_profiles = ['Conservative', 'Balanced', 'Aggressive', 'Scalping', 'Swing Trading']
        selected_risk = st.selectbox("Risk Profile", risk_profiles, key="risk_select")
        
        st.info(f"📊 Using {selected_risk} risk profile")
        
        # Risk settings display
        if selected_risk == 'Conservative':
            st.metric("Take Profit", "6.0%")
            st.metric("Stop Loss", "4.0%")
        elif selected_risk == 'Balanced':
            st.metric("Take Profit", "10.0%")
            st.metric("Stop Loss", "8.0%")
        elif selected_risk == 'Aggressive':
            st.metric("Take Profit", "15.0%")
            st.metric("Stop Loss", "12.0%")
        else:
            st.metric("Take Profit", "Variable")
            st.metric("Stop Loss", "Variable")
    
    # Trading parameters
    st.subheader("🔧 Trading Parameters")
    col3, col4, col5 = st.columns(3)
    
    with col3:
        max_pos = st.number_input("Max Positions", 1, 10, 3, key="max_pos")
    
    with col4:
        min_conf = st.slider("Min Confidence", 0.5, 0.95, 0.65, 0.05, key="min_conf")
    
    with col5:
        risk_pct = st.slider("Risk Per Trade (%)", 0.5, 5.0, 1.5, 0.1, key="risk_pct")

def render_manual_trading_tab():
    """Manual trading tab"""
    st.header("💹 Manual Trading")
    st.caption("Execute manual trades - LIVE TRADING MODE")
    
    client = get_binance_client()
    if not client:
        st.error("❌ Binance client not available")
        return
    
    # Symbol selection
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 'DOGEUSDT']
    symbol = st.selectbox("Trading Pair", symbols, key="trading_symbol")
    
    # Get live price
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        price = float(ticker['price'])
        st.success(f"💰 Live {symbol} Price: ${price:,.4f}")
    except Exception as e:
        st.error(f"❌ Price error: {e}")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        direction = st.selectbox("Direction", ["BUY_LONG", "BUY_SHORT"], key="trade_direction")
        order_type = st.selectbox("Order Type", ["MARKET", "LIMIT"], key="order_type")
        
        # Calculate quantity
        trade_amount = st.number_input("Trade Amount (USD)", 10.0, 1000.0, 50.0, key="trade_amount")
        quantity = trade_amount / price
        st.info(f"📊 Calculated Quantity: {quantity:.6f} {symbol[:-4]}")
    
    with col2:
        if order_type == "LIMIT":
            limit_price = st.number_input("Limit Price", value=price, format="%.6f", key="limit_price")
        
        stop_loss = st.slider("Stop Loss %", 2.0, 15.0, 8.0, key="stop_loss")
        take_profit = st.slider("Take Profit %", 3.0, 25.0, 12.0, key="take_profit")
    
    # Execute trade
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button(f"🚀 Execute {direction}", type="primary", key="execute_trade"):
            st.success("✅ Trade simulation executed!")
            st.json({
                "symbol": symbol,
                "direction": direction,
                "quantity": quantity,
                "price": price,
                "amount": trade_amount,
                "status": "Simulated"
            })
    
    with col4:
        if st.button("📊 Calculate Risk", key="calc_risk"):
            position_value = quantity * price
            sl_price = price * (1 - stop_loss/100) if direction == "BUY_LONG" else price * (1 + stop_loss/100)
            tp_price = price * (1 + take_profit/100) if direction == "BUY_LONG" else price * (1 - take_profit/100)
            
            st.info(f"""
            📊 **Position Analysis**
            - Value: ${position_value:.2f}
            - Stop Loss: ${sl_price:.6f}
            - Take Profit: ${tp_price:.6f}
            - Risk/Reward: 1:{take_profit/stop_loss:.2f}
            """)

def render_performance_tab():
    """Performance analytics tab"""
    st.header("📈 Performance Analytics")
    st.caption("Trading performance metrics and analysis")
    
    # Load trade data
    try:
        if os.path.exists('logs/trades.csv'):
            df = pd.read_csv('logs/trades.csv')
            
            if not df.empty:
                # Calculate metrics
                total_trades = len(df)
                closed_trades = df[df['status'] == 'CLOSED']
                
                if not closed_trades.empty:
                    wins = closed_trades[closed_trades['change_pct'] > 0]
                    win_rate = len(wins) / len(closed_trades) * 100
                    total_pnl = closed_trades['change_pct'].sum()
                else:
                    win_rate = 0
                    total_pnl = 0
                
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Trades", total_trades)
                with col2:
                    st.metric("Win Rate", f"{win_rate:.1f}%")
                with col3:
                    st.metric("Total P&L", f"{total_pnl:+.2f}%")
                with col4:
                    active_pos = len(get_open_positions())
                    st.metric("Active Positions", active_pos)
                
                # Recent trades
                st.subheader("📋 Recent Trades")
                recent = df.tail(10).sort_values('timestamp', ascending=False)
                st.dataframe(recent, use_container_width=True)
                
                # P&L Chart
                if not closed_trades.empty:
                    st.subheader("📈 Cumulative P&L Chart")
                    closed_trades['cumulative'] = closed_trades['change_pct'].cumsum()
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=closed_trades['timestamp'],
                        y=closed_trades['cumulative'],
                        mode='lines+markers',
                        name='Cumulative P&L %',
                        line=dict(color='green' if total_pnl > 0 else 'red')
                    ))
                    fig.update_layout(
                        title="Cumulative P&L Over Time",
                        xaxis_title="Time",
                        yaxis_title="P&L %"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 No trade data available")
        else:
            st.info("📊 No trade log found")
    except Exception as e:
        st.error(f"❌ Performance data error: {e}")

def render_logs_tab():
    """System logs tab"""
    st.header("📋 System Logs & Monitoring")
    st.caption("Real-time system monitoring and log analysis")
    
    if st.button("🔄 Refresh Logs", key="refresh_logs"):
        st.rerun()
    
    # Log file status
    st.subheader("📁 Log File Status")
    log_files = ['logs/trades.csv', 'logs/manual_trades.log', 'logs/portfolio_scans.log']
    
    status_data = []
    for log_file in log_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            modified = datetime.fromtimestamp(os.path.getmtime(log_file)).strftime("%H:%M:%S")
            status_data.append({
                'File': log_file, 
                'Status': '✅ Active', 
                'Size': f"{size} bytes", 
                'Modified': modified
            })
        else:
            status_data.append({
                'File': log_file, 
                'Status': '❌ Missing', 
                'Size': 'N/A', 
                'Modified': 'N/A'
            })
    
    st.dataframe(pd.DataFrame(status_data), use_container_width=True)
    
    # Recent log entries
    st.subheader("📜 Recent Log Entries")
    
    if os.path.exists('logs/trades.csv'):
        try:
            df = pd.read_csv('logs/trades.csv').tail(5)
            st.dataframe(df, use_container_width=True)
        except:
            st.info("No trade data to display")
    else:
        st.info("No log files found")
    
    # System info
    st.subheader("💻 System Information")
    st.text(f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.text(f"Trading Mode: LIVE")
    st.text(f"Bot Status: {'🟢 Running' if st.session_state.get('auto_trader_running') else '🔴 Stopped'}")

def main():
    """Main application with fixed tabs"""
    st.set_page_config(
        page_title="🤖 Crypto Bot - LIVE",
        page_icon="🤖",
        layout="wide"
    )
    
    # Initialize
    initialize_session_state()
    ensure_log_files()
    
    # Authentication
    if not st.session_state['password_authenticated']:
        st.title("🔒 Dashboard Login")
        st.warning("⚠️ **LIVE TRADING MODE** - Real money at risk")
        
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("🔓 Login", key="login_button"):
            if password == st.session_state['dashboard_password']:
                st.session_state['password_authenticated'] = True
                st.success("✅ Access granted!")
                st.rerun()
            else:
                st.error("❌ Incorrect password")
        
        st.stop()
    
    # Main header
    st.title("🤖 Crypto Trading Bot - LIVE MODE")
    st.caption("Professional cryptocurrency trading dashboard")
    
    # Status check
    if not BINANCE_AVAILABLE:
        st.error("⚠️ Binance library not available - install python-binance")
    elif not API_KEY or not API_SECRET:
        st.error("⚠️ API credentials not configured - set BINANCE_API_KEY and BINANCE_API_SECRET")
    elif not TRADING_MODULES_AVAILABLE:
        st.warning("⚠️ Limited functionality - some trading modules unavailable")
    else:
        st.success("✅ All systems operational - Live trading ready")
    
    # Sidebar controls
    with st.sidebar:
        st.title("🤖 Bot Control")
        st.markdown("### 🔴 LIVE TRADING")
        
        # Bot status
        auto_status = st.session_state.get('auto_trader_running', False)
        st.markdown(f"**Auto Trader:** {'🟢 Running' if auto_status else '🔴 Stopped'}")
        
        # Quick balance
        client = get_binance_client()
        if client and TRADING_MODULES_AVAILABLE:
            try:
                balance = get_account_balance(client, 'USDT')
                st.metric("USDT Balance", f"${balance:,.2f}")
                
                gbp_rate = get_gbp_exchange_rate()
                gbp_balance = balance * gbp_rate
                st.metric("GBP Equivalent", f"£{gbp_balance:,.2f}")
            except:
                st.metric("Balance", "Error")
        
        # Emergency stop
        st.markdown("---")
        if st.button("🚨 EMERGENCY STOP", type="primary", key="emergency_stop_sidebar"):
            st.session_state['auto_trader_running'] = False
            st.error("🛑 Emergency stop activated!")
    
    st.markdown("---")
    
    # MAIN TABS - This should work now
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Overview",
        "⚙️ Strategy", 
        "💹 Manual Trading",
        "📈 Performance",
        "📋 Logs"
    ])
    
    with tab1:
        render_overview_tab()
    
    with tab2:
        render_strategy_tab()
    
    with tab3:
        render_manual_trading_tab()
    
    with tab4:
        render_performance_tab()
    
    with tab5:
        render_logs_tab()
    
    # Footer
    st.markdown("---")
    st.markdown(
        f"<div style='text-align: center; color: #666;'>"
        f"🤖 Live Trading Dashboard | Last Updated: {datetime.now().strftime('%H:%M:%S')} | "
        f"⚠️ Real Money Trading Active</div>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()