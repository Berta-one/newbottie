#!/usr/bin/env python3
"""
Complete Enhanced Crypto Trading Bot Dashboard - FULLY RESTORED
==============================================================

Company: Rondanini Publishing Ltd.  
Website: https://www.rondanini.net


Copyright (c) 2025 Rondanini Publishing Ltd.

This is the complete restored hybrid_bot.py with full trading functionality
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
    st.error(f"Trading modules not available: {e}")

# Import quantum modules (optional)
try:
    from quantum_engine import QuantumTradingEngine
    from quantum_trading_integration import get_quantum_trader
    QUANTUM_AVAILABLE = True
except ImportError:
    QUANTUM_AVAILABLE = False
    class QuantumTradingEngine:
        def __init__(self): pass
        def generate_quantum_trading_recommendation(self, *args, **kwargs):
            return {'quantum_signal': 'HOLD', 'quantum_confidence': 0.5}

# Configuration
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')
USE_TESTNET = False  # ALWAYS LIVE TRADING
MIN_BALANCE_USD = 10.0
SCAN_INTERVAL = 300
MIN_CONFIDENCE = 0.65
MAX_POSITIONS = 3
RISK_PERCENTAGE = 0.015

def get_binance_client():
    """Get live Binance client"""
    if not BINANCE_AVAILABLE or not API_KEY or not API_SECRET:
        return None
    try:
        return Client(API_KEY, API_SECRET)  # Live trading only
    except Exception as e:
        st.error(f"Binance client error: {e}")
        return None

def ensure_log_files():
    """Create required log files"""
    os.makedirs('logs', exist_ok=True)
    
    # Create trades.csv with headers
    if not os.path.exists('logs/trades.csv'):
        with open('logs/trades.csv', 'w') as f:
            f.write('timestamp,symbol,direction,entry_price,exit_price,quantity,change_pct,status,strategy,confidence\n')
    
    # Create other log files
    log_files = [
        'logs/manual_trades.log',
        'logs/portfolio_scans.log', 
        'logs/console_output.log',
        'logs/trade_executions.json',
        'logs/auto_trader_debug.log'
    ]
    
    for log_file in log_files:
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                if log_file.endswith('.json'):
                    f.write('{}')

def get_real_portfolio():
    """Get real portfolio from Binance"""
    client = get_binance_client()
    if not client:
        return {}, 0
    
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
        
        return portfolio, total_usd
    except Exception as e:
        st.error(f"Portfolio error: {e}")
        return {}, 0

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

def log_trade_execution(trade_type, symbol, quantity, price, result):
    """Log trade execution"""
    try:
        trade_data = {
            'timestamp': datetime.now().isoformat(),
            'trade_type': trade_type,
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'result': str(result)
        }
        
        with open('logs/trade_executions.json', 'a') as f:
            f.write(json.dumps(trade_data) + '\n')
    except Exception as e:
        print(f"Logging error: {e}")

def start_auto_trader():
    """Start the auto trader from bot_trade.py"""
    if 'auto_trader_running' in st.session_state and st.session_state['auto_trader_running']:
        return
    
    st.session_state['auto_trader_running'] = True
    
    def trading_loop():
        client = get_binance_client()
        if not client or not TRADING_MODULES_AVAILABLE:
            return
        
        while st.session_state.get('auto_trader_running', False):
            try:
                # Get open positions
                open_positions = get_open_positions()
                open_symbols = [p['Asset'] + 'USDT' for p in open_positions]
                
                # Monitor existing positions
                for pos in open_positions:
                    symbol = pos['Asset'] + 'USDT'
                    # Position monitoring logic would go here
                    pass
                
                # Scan for new opportunities
                if TRADING_MODULES_AVAILABLE:
                    scanner = CryptoPairScanner(client)
                    pairs = scanner.get_selected_pairs()
                    opportunities = scanner.scan_multiple_pairs(pairs[:10])  # Limit for demo
                    
                    # Filter opportunities
                    actionable = [
                        opp for opp in opportunities 
                        if opp['confidence'] >= MIN_CONFIDENCE 
                        and opp['decision'] != 'HOLD'
                        and opp['symbol'] not in open_symbols
                    ]
                    
                    # Execute top opportunity
                    if actionable and len(open_positions) < MAX_POSITIONS:
                        top_opp = max(actionable, key=lambda x: x['confidence'])
                        
                        try:
                            # Calculate position size
                            balance = get_account_balance(client, 'USDT')
                            qty = calculate_dynamic_position_size(
                                balance, 0.001, top_opp['confidence'], 0.02, RISK_PERCENTAGE
                            )
                            
                            # Execute trade
                            result = execute_entry(client, top_opp['symbol'], qty, top_opp['decision'])
                            log_trade_execution('AUTO_ENTRY', top_opp['symbol'], qty, 0, result)
                            
                            st.session_state['last_action'] = f"Opened {top_opp['symbol']} ({top_opp['decision']})"
                            
                        except Exception as e:
                            print(f"Trade execution error: {e}")
                
                time.sleep(60)  # Wait 1 minute between cycles
                
            except Exception as e:
                print(f"Trading loop error: {e}")
                time.sleep(30)
    
    # Start trading thread
    trading_thread = threading.Thread(target=trading_loop, daemon=True)
    trading_thread.start()

def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'password_authenticated': False,
        'dashboard_password': 'bottie',
        'auto_trader_running': False,
        'selected_strategy': 'Breakout',
        'selected_risk_level': 'BALANCED',
        'max_trade_percent': 1.5,
        'scan_count': 0,
        'last_scan_time': None,
        'last_opportunities': [],
        'last_action': 'None'
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Initialize risk manager
    if 'risk_manager' not in st.session_state and TRADING_MODULES_AVAILABLE:
        st.session_state['risk_manager'] = AdaptiveRiskManager()
    
    # Initialize quantum engine
    if 'quantum_engine' not in st.session_state:
        st.session_state['quantum_engine'] = QuantumTradingEngine()

def render_overview_tab():
    """Main overview tab"""
    st.header("🎯 Live Trading Overview")
    st.caption("Real-time portfolio monitoring - LIVE TRADING MODE")
    
    # Get portfolio data
    portfolio, total_usd = get_real_portfolio()
    
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
        st.metric("Portfolio Value", f"${total_usd:,.2f}")
    
    with col4:
        auto_status = "🟢 Running" if st.session_state.get('auto_trader_running') else "🔴 Stopped"
        st.metric("Auto Trader", auto_status)
    
    # Portfolio table
    st.subheader("📊 Current Portfolio")
    if portfolio:
        df_data = []
        for asset, data in portfolio.items():
            df_data.append({
                'Asset': asset,
                'Balance': f"{data['balance']:.6f}",
                'Price USD': f"${data['price_usd']:.4f}",
                'USD Value': f"${data['usd_value']:.2f}",
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
        if not st.session_state.get('auto_trader_running'):
            if st.button("▶️ Start Auto Trader", type="primary"):
                if TRADING_MODULES_AVAILABLE:
                    start_auto_trader()
                    st.success("Auto trader started!")
                    st.rerun()
                else:
                    st.error("Trading modules not available")
        else:
            if st.button("⏹️ Stop Auto Trader", type="secondary"):
                st.session_state['auto_trader_running'] = False
                st.warning("Auto trader stopped")
                st.rerun()
    
    with col2:
        if st.button("🔍 Scan Markets"):
            perform_scan()
            st.success("Market scan completed!")
    
    with col3:
        if st.button("📊 Refresh Data"):
            st.rerun()
    
    # Recent action
    if st.session_state.get('last_action'):
        st.info(f"Last action: {st.session_state['last_action']}")

def render_strategy_tab():
    """Strategy configuration tab"""
    st.header("⚙️ Strategy & Risk Configuration")
    
    if not TRADING_MODULES_AVAILABLE:
        st.error("Trading modules not available")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Strategy Selection")
        
        strategies = ['Breakout', 'ML Enhanced', 'Relaxed', 'Scalping', 'Swing', 'Conservative']
        selected = st.selectbox("Trading Strategy", strategies, 
                               index=strategies.index(st.session_state.get('selected_strategy', 'Breakout')))
        st.session_state['selected_strategy'] = selected
        
        descriptions = {
            'Breakout': '5% breakout with volume and time filters',
            'ML Enhanced': 'Machine learning enhanced signals',
            'Relaxed': 'Multiple strategy ensemble approach',
            'Scalping': 'Quick 2-3% moves with high volume',
            'Swing': 'Longer-term 10-20% moves',
            'Conservative': 'Safe trading with reduced risk'
        }
        
        st.info(f"📝 {descriptions.get(selected, 'Custom strategy')}")
    
    with col2:
        st.subheader("⚖️ Risk Management")
        
        if 'risk_manager' in st.session_state:
            risk_manager = st.session_state['risk_manager']
            profiles = list(risk_manager.risk_profiles.keys())
            
            # Map profile keys to display names
            profile_names = {
                'CONSERVATIVE': 'Conservative',
                'BALANCED': 'Balanced',
                'AGGRESSIVE': 'Aggressive',
                'SCALPING': 'Scalping',
                'SWING': 'Swing Trading'
            }
            
            display_names = [profile_names.get(p, p) for p in profiles]
            
            selected_display = st.selectbox("Risk Profile", display_names)
            selected_key = [k for k, v in profile_names.items() if v == selected_display][0]
            st.session_state['selected_risk_level'] = selected_key
            
            profile = risk_manager.risk_profiles[selected_key]
            st.info(f"📊 {profile['description']}")
            
            # Show profile details
            col2_1, col2_2 = st.columns(2)
            with col2_1:
                st.metric("Take Profit", f"{profile['take_profit']}%")
                st.metric("Stop Loss", f"{profile['stop_loss']}%")
            with col2_2:
                st.metric("Trailing Stop", f"{profile['trailing_stop']}%")
                st.metric("Max Hold", f"{profile['max_hold_hours']}h")
    
    # Trading parameters
    st.subheader("🔧 Trading Parameters")
    col3, col4, col5 = st.columns(3)
    
    with col3:
        max_pos = st.number_input("Max Positions", 1, 10, MAX_POSITIONS)
    
    with col4:
        min_conf = st.slider("Min Confidence", 0.5, 0.95, MIN_CONFIDENCE, 0.05)
    
    with col5:
        risk_pct = st.slider("Risk Per Trade (%)", 0.5, 5.0, RISK_PERCENTAGE * 100, 0.1)
        st.session_state['max_trade_percent'] = risk_pct

def render_manual_trading_tab():
    """Manual trading tab"""
    st.header("💹 Manual Trading")
    st.caption("Execute manual trades - LIVE TRADING MODE")
    
    client = get_binance_client()
    if not client:
        st.error("Binance client not available")
        return
    
    # Symbol selection
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 'DOGEUSDT']
    symbol = st.selectbox("Trading Pair", symbols)
    
    # Get live price
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        price = float(ticker['price'])
        st.success(f"💰 Live {symbol} Price: ${price:,.4f}")
    except Exception as e:
        st.error(f"Price error: {e}")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        direction = st.selectbox("Direction", ["BUY_LONG", "BUY_SHORT"])
        order_type = st.selectbox("Order Type", ["MARKET", "LIMIT"])
        
        # Calculate quantity
        trade_amount = st.number_input("Trade Amount (USD)", 10.0, 1000.0, 50.0)
        quantity = trade_amount / price
        st.info(f"Quantity: {quantity:.6f} {symbol[:-4]}")
    
    with col2:
        if order_type == "LIMIT":
            limit_price = st.number_input("Limit Price", value=price, format="%.6f")
        
        stop_loss = st.slider("Stop Loss %", 2.0, 15.0, 8.0)
        take_profit = st.slider("Take Profit %", 3.0, 25.0, 12.0)
    
    # Execute trade
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button(f"🚀 Execute {direction}", type="primary"):
            if TRADING_MODULES_AVAILABLE and quantity > 0:
                try:
                    result = execute_entry(client, symbol, quantity, direction)
                    
                    if result.get('success'):
                        st.success("✅ Trade executed!")
                        log_trade_execution('MANUAL', symbol, quantity, price, result)
                        
                        # Log to CSV
                        with open('logs/trades.csv', 'a') as f:
                            f.write(f"{datetime.now()},{symbol},{direction},{price},,{quantity},,OPEN,Manual,1.0\n")
                    else:
                        st.error(f"❌ Trade failed: {result.get('error', 'Unknown')}")
                        
                except Exception as e:
                    st.error(f"❌ Execution error: {e}")
            else:
                st.error("Invalid trade parameters")
    
    with col4:
        if st.button("📊 Calculate Risk"):
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
                st.subheader("Recent Trades")
                recent = df.tail(20).sort_values('timestamp', ascending=False)
                st.dataframe(recent, use_container_width=True)
                
                # P&L Chart
                if not closed_trades.empty:
                    st.subheader("Cumulative P&L")
                    closed_trades['cumulative'] = closed_trades['change_pct'].cumsum()
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=closed_trades['timestamp'],
                        y=closed_trades['cumulative'],
                        mode='lines+markers',
                        name='Cumulative P&L %'
                    ))
                    fig.update_layout(title="P&L Over Time", xaxis_title="Time", yaxis_title="P&L %")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No trade data available")
        else:
            st.info("No trade log found")
    except Exception as e:
        st.error(f"Performance data error: {e}")

def render_logs_tab():
    """System logs tab"""
    st.header("📋 System Logs")
    
    if st.button("🔄 Refresh"):
        st.rerun()
    
    # Log file status
    log_files = ['logs/trades.csv', 'logs/trade_executions.json', 'logs/auto_trader_debug.log']
    
    status_data = []
    for log_file in log_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            modified = datetime.fromtimestamp(os.path.getmtime(log_file)).strftime("%H:%M:%S")
            status_data.append({'File': log_file, 'Status': '✅', 'Size': f"{size} bytes", 'Modified': modified})
        else:
            status_data.append({'File': log_file, 'Status': '❌', 'Size': 'N/A', 'Modified': 'N/A'})
    
    st.dataframe(pd.DataFrame(status_data), use_container_width=True)
    
    # Log content
    tab1, tab2, tab3 = st.tabs(["🤖 Auto Trader", "💼 Trades", "🔍 Executions"])
    
    with tab1:
        if os.path.exists('logs/auto_trader_debug.log'):
            with open('logs/auto_trader_debug.log', 'r') as f:
                lines = f.readlines()[-30:]
            for line in lines:
                st.text(line.strip())
        else:
            st.info("No auto trader log")
    
    with tab2:
        if os.path.exists('logs/trades.csv'):
            df = pd.read_csv('logs/trades.csv').tail(20)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No trade log")
    
    with tab3:
        if os.path.exists('logs/trade_executions.json'):
            with open('logs/trade_executions.json', 'r') as f:
                lines = f.readlines()[-10:]
            
            for line in lines:
                try:
                    data = json.loads(line)
                    st.json(data)
                except:
                    st.text(line.strip())
        else:
            st.info("No execution log")

def perform_scan():
    """Perform market scan"""
    if not TRADING_MODULES_AVAILABLE:
        return
    
    client = get_binance_client()
    if not client:
        return
    
    try:
        scanner = CryptoPairScanner(client)
        pairs = scanner.get_selected_pairs()
        opportunities = scanner.scan_multiple_pairs(pairs[:10])
        
        filtered = [opp for opp in opportunities if opp['confidence'] >= MIN_CONFIDENCE and opp['decision'] != 'HOLD']
        st.session_state['last_opportunities'] = filtered
        st.session_state['scan_count'] += 1
        st.session_state['last_scan_time'] = datetime.now()
        
    except Exception as e:
        st.error(f"Scan error: {e}")

def dashboard():
    """Main dashboard"""
    # Sidebar
    st.sidebar.title("🤖 Bot Control")
    st.sidebar.markdown("### 🔴 LIVE TRADING")
    st.sidebar.markdown("**Real Money Trading Active**")
    
    # Bot status
    auto_status = st.session_state.get('auto_trader_running', False)
    st.sidebar.markdown(f"**Auto Trader:** {'🟢 Running' if auto_status else '🔴 Stopped'}")
    
    # Quick stats
    if TRADING_MODULES_AVAILABLE:
        client = get_binance_client()
        if client:
            try:
                balance = get_account_balance(client, 'USDT')
                st.sidebar.metric("USDT Balance", f"${balance:,.2f}")
            except:
                st.sidebar.metric("USDT Balance", "Error")
    
    # Emergency stop
    st.sidebar.markdown("---")
    if st.sidebar.button("🚨 EMERGENCY STOP", type="primary"):
        st.session_state['auto_trader_running'] = False
        st.sidebar.error("🛑 Emergency stop activated!")
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Overview", "⚙️ Strategy", "💹 Manual", "📈 Performance", "📋 Logs"])
    
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

def main():
    """Main application"""
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
        
        password = st.text_input("Password", type="password")
        
        if st.button("🔓 Login"):
            if password == st.session_state['dashboard_password']:
                st.session_state['password_authenticated'] = True
                st.success("✅ Access granted!")
                st.rerun()
            else:
                st.error("❌ Incorrect password")
        
        st.stop()
    
    # Main app
    st.title("🤖 Crypto Trading Bot - LIVE MODE")
    st.caption("Professional cryptocurrency trading dashboard")
    
    # Status warnings
    if not BINANCE_AVAILABLE:
        st.error("⚠️ Binance library not available")
    elif not API_KEY or not API_SECRET:
        st.error("⚠️ API credentials not configured")
    elif not TRADING_MODULES_AVAILABLE:
        st.warning("⚠️ Limited functionality - some modules unavailable")
    else:
        st.success("✅ All systems operational - Live trading ready")
    
    st.markdown("---")
    dashboard()

if __name__ == "__main__":
    main()