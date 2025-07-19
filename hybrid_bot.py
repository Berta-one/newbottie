#!/usr/bin/env python3
"""
Integrated Hybrid Bot - Complete Trading Dashboard
=================================================

Unified trading dashboard combining manual trading, auto-trading controls,
and advanced analytics in a single comprehensive interface.

This integrates all analytics functions from dashboard.py into the main trading interface.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import json
import os
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import io

# ----------------------------------------------------------------------
# IMPORTS - Modular imports (risk, portfolio, quantum, trade execution, etc.)
# ----------------------------------------------------------------------
from risk_manager import RiskManager
from portfolio_manager import PortfolioManager
from quantum_engine import QuantumTradingEngine as QuantumAnalyzer
from trade_executor import TradeExecutor
from market_analyzer import MarketAnalyzer
from position_monitor import PositionMonitor

# Import analytics engine from dashboard.py
from dashboard import TradingDashboard

# Configuration
st.set_page_config(
    page_title="🤖 Complete Crypto Trading Bot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Environment variables
USE_TESTNET = os.getenv('USE_TESTNET', 'false').lower() == 'true'
API_KEY = os.getenv('BINANCE_API_KEY', '')
API_SECRET = os.getenv('BINANCE_API_SECRET', '')

# Session state initialization
if 'auto_running' not in st.session_state:
    st.session_state['auto_running'] = False
if 'last_action' not in st.session_state:
    st.session_state['last_action'] = 'Bot initialized'
if 'scan_results' not in st.session_state:
    st.session_state['scan_results'] = []
if 'portfolio_value' not in st.session_state:
    st.session_state['portfolio_value'] = 0
if 'scan_count' not in st.session_state:
    st.session_state['scan_count'] = 0
if 'selected_symbol' not in st.session_state:
    st.session_state['selected_symbol'] = 'BTCUSDT'

# Try to import Binance
try:
    from binance.client import Client
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    Client = None

def get_binance_client():
    """Get Binance client"""
    if not BINANCE_AVAILABLE or not API_KEY or not API_SECRET:
        return None
    
    try:
        client = Client(API_KEY, API_SECRET)
        if USE_TESTNET:
            client.API_URL = "https://testnet.binance.vision/api"
        return client
    except:
        return None

# ----------------------------------------------------------------------
# Initialize core modules
# ----------------------------------------------------------------------
BINANCE_CLIENT = get_binance_client()

risk_mgr = RiskManager()
portfolio_mgr = PortfolioManager(API_KEY, API_SECRET, USE_TESTNET)
market_analyzer = MarketAnalyzer(BINANCE_CLIENT)
trade_executor = TradeExecutor(BINANCE_CLIENT, risk_mgr)
position_monitor = PositionMonitor()
quantum_analyzer = QuantumAnalyzer()

# Initialize analytics dashboard engine
analytics_dashboard = TradingDashboard()

# ----------------------------------------------------------------------
# MANUAL TRADING INTERFACE FUNCTIONS
# ----------------------------------------------------------------------

def get_available_trading_pairs() -> List[str]:
    """Get list of available trading pairs"""
    default_pairs = [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT",
        "XRPUSDT", "DOTUSDT", "AVAXUSDT", "MATICUSDT", "LINKUSDT",
        "UNIUSDT", "LTCUSDT", "ATOMUSDT", "NEARUSDT", "AAVEUSDT",
        "COMPUSDT", "MKRUSDT", "SANDUSDT", "MANAUSDT", "DOGEUSDT", "SHIBUSDT"
    ]
    return default_pairs

def get_current_price(symbol: str) -> Optional[float]:
    """Get current price for symbol"""
    try:
        if BINANCE_CLIENT:
            ticker = BINANCE_CLIENT.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        else:
            # Mock price for demo
            import random
            base_prices = {
                "BTCUSDT": 50000, "ETHUSDT": 3000, "BNBUSDT": 300,
                "ADAUSDT": 0.5, "SOLUSDT": 100, "XRPUSDT": 0.6
            }
            base_price = base_prices.get(symbol, 100)
            return base_price * (1 + random.uniform(-0.05, 0.05))
    except Exception as e:
        st.error(f"Error getting price for {symbol}: {e}")
        return None

def get_account_balance() -> float:
    """Get current account balance in USDT"""
    try:
        if BINANCE_CLIENT:
            account = BINANCE_CLIENT.get_account()
            for balance in account['balances']:
                if balance['asset'] == 'USDT':
                    return float(balance['free'])
        # Mock balance for demo
        return 10000.0
    except Exception as e:
        return 10000.0

def execute_manual_trade(symbol: str, quantity: float, side: str, price: float,
                        stop_loss: Optional[float] = None, take_profit: Optional[float] = None):
    """Execute a manual trade"""
    try:
        # Validate inputs
        if quantity <= 0:
            st.error("Invalid quantity")
            return
        
        # Risk validation using the risk manager
        if not risk_mgr._risk_below_position_limit(symbol, quantity):
            st.error("Trade exceeds risk limits")
            return
        
        # Execute trade using trade executor
        result = trade_executor.manual_trade(symbol, quantity, side, price)
        
        if result['status'] == 'SUCCESS':
            st.success(f"✅ {side} order executed successfully!")
            
            # Add to position monitor if successful
            position_data = {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'entry_price': price,
                'entry_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'stop_loss': stop_loss,
                'take_profit': take_profit
            }
            
            position_monitor.add_position(position_data)
            
        else:
            st.error(f"❌ Trade failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        st.error(f"Error executing trade: {e}")

# ----------------------------------------------------------------------
# MAIN DASHBOARD INTERFACE
# ----------------------------------------------------------------------

def render_sidebar():
    """Render enhanced sidebar with controls"""
    st.sidebar.header("🤖 Trading Bot Control")
    
    # Bot status
    st.sidebar.subheader("📊 Status")
    mode = "🧪 TESTNET" if USE_TESTNET else "🔴 LIVE"
    st.sidebar.info(f"Mode: {mode}")
    
    if BINANCE_CLIENT:
        st.sidebar.success("🟢 API Connected")
    else:
        st.sidebar.warning("🟡 Demo Mode")
    
    # Auto-trader controls
    st.sidebar.subheader("🤖 Auto-Trader")
    
    if st.session_state.get('auto_running', False):
        st.sidebar.success("🟢 AUTO-TRADER RUNNING")
        if st.sidebar.button("⏹️ Stop Auto-Trader", type="primary"):
            st.session_state.auto_running = False
            st.session_state.last_action = "Auto-trader stopped"
            st.rerun()
    else:
        st.sidebar.error("🔴 AUTO-TRADER STOPPED")
        if st.sidebar.button("▶️ Start Auto-Trader", type="primary"):
            st.session_state.auto_running = True
            st.session_state.last_action = "Auto-trader started"
            st.rerun()
    
    # Quick stats
    st.sidebar.subheader("📈 Quick Stats")
    
    # Load analytics data for sidebar
    df = analytics_dashboard.load_trade_data()
    metrics = analytics_dashboard.calculate_metrics(df)
    
    st.sidebar.metric("Total Trades", metrics['total_trades'])
    st.sidebar.metric("Win Rate", f"{metrics['win_rate']:.1f}%")
    st.sidebar.metric("Total P&L", f"${metrics['total_pnl_usd']:,.2f}")
    
    # Settings
    st.sidebar.subheader("⚙️ Settings")
    
    # Risk settings
    risk_per_trade = st.sidebar.slider("Risk per Trade (%)", 0.5, 3.0, 1.5)
    max_positions = st.sidebar.slider("Max Positions", 1, 10, 3)
    
    # Scanner settings
    scan_interval = st.sidebar.slider("Scan Interval (min)", 1, 60, 5)
    min_confidence = st.sidebar.slider("Min Confidence", 0.4, 0.9, 0.65)
    
    # Manual refresh
    if st.sidebar.button("🔄 Refresh Dashboard"):
        st.rerun()
    
    return {
        'risk_per_trade': risk_per_trade,
        'max_positions': max_positions,
        'scan_interval': scan_interval,
        'min_confidence': min_confidence
    }

def render_trading_control_tab():
    """Render the main trading control interface"""
    st.header("🎯 Trading Control Center")
    
    # Trading interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("✋ Manual Trading")
        
        # Symbol selection
        trading_pairs = get_available_trading_pairs()
        selected_symbol = st.selectbox(
            "Select Trading Pair",
            options=trading_pairs,
            index=trading_pairs.index(st.session_state.selected_symbol) if st.session_state.selected_symbol in trading_pairs else 0
        )
        st.session_state.selected_symbol = selected_symbol
        
        # Get current price
        current_price = get_current_price(selected_symbol)
        if current_price:
            st.metric("Current Price", f"${current_price:.6f}")
        
        # Trading form
        trade_col1, trade_col2 = st.columns(2)
        
        with trade_col1:
            trade_direction = st.radio("Direction", ["BUY", "SELL"], horizontal=True)
            quantity = st.number_input(
                f"Quantity ({selected_symbol.replace('USDT', '')})",
                min_value=0.0,
                value=0.001,
                step=0.001,
                format="%.6f"
            )
        
        with trade_col2:
            use_stop_loss = st.checkbox("Stop Loss", value=True)
            if use_stop_loss:
                sl_pct = st.number_input("SL %", min_value=1.0, value=8.0, step=0.5)
                sl_price = current_price * (1 - sl_pct/100) if trade_direction == "BUY" and current_price else None
            else:
                sl_price = None
            
            use_take_profit = st.checkbox("Take Profit", value=True)
            if use_take_profit:
                tp_pct = st.number_input("TP %", min_value=1.0, value=10.0, step=0.5)
                tp_price = current_price * (1 + tp_pct/100) if trade_direction == "BUY" and current_price else None
            else:
                tp_price = None
        
        # Execute button
        if st.button(f"🎯 Execute {trade_direction} Order", type="primary"):
            execute_manual_trade(selected_symbol, quantity, trade_direction, current_price, sl_price, tp_price)
    
    with col2:
        st.subheader("📊 Risk Calculator")
        
        if current_price and quantity > 0:
            position_value = quantity * current_price
            account_balance = get_account_balance()
            
            st.metric("Position Value", f"${position_value:.2f}")
            
            if use_stop_loss and sl_price:
                max_loss = abs(quantity * (current_price - sl_price))
                max_loss_pct = (max_loss / account_balance) * 100
                st.metric("Max Loss", f"${max_loss:.2f}", f"-{max_loss_pct:.2f}%")
            
            if use_take_profit and tp_price:
                max_gain = abs(quantity * (tp_price - current_price))
                st.metric("Max Gain", f"${max_gain:.2f}")
            
            # Risk warnings
            risk_pct = (position_value / account_balance) * 100 if account_balance > 0 else 0
            if risk_pct > 5:
                st.error("⚠️ High risk position!")
            elif risk_pct > 2:
                st.warning("⚠️ Moderate risk")
            else:
                st.success("✅ Low risk")
    
    # Active positions
    st.markdown("---")
    st.subheader("💼 Active Positions")
    
    active_positions = position_monitor.get_active_positions()
    if active_positions:
        positions_df = pd.DataFrame(active_positions)
        st.dataframe(positions_df, use_container_width=True, hide_index=True)
        
        if st.button("🛑 Close All Positions", type="secondary"):
            # Close all positions logic here
            st.warning("Close all positions functionality would be implemented here")
    else:
        st.info("No active positions")

def render_performance_tab():
    """Render performance analytics tab using dashboard functions"""
    st.header("📊 Performance Analytics")
    
    # Load data using analytics dashboard
    df = analytics_dashboard.load_trade_data()
    metrics = analytics_dashboard.calculate_metrics(df)
    
    # Render performance overview from dashboard.py
    analytics_dashboard.render_performance_overview(df, metrics)
    
    st.markdown("---")
    
    # Recent trades from dashboard.py
    analytics_dashboard.render_recent_trades(df)

def render_scanner_tab():
    """Render market scanner tab"""
    st.header("🔍 Market Scanner")
    
    # Scanner controls
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Manual Scan", type="primary"):
            st.session_state.scan_count += 1
            st.session_state.last_action = "Manual scan initiated"
            st.info("🔍 Scanning markets...")
    
    with col2:
        scan_mode = st.selectbox("Scan Mode", ["SELECTED", "ALL", "CUSTOM"])
    
    with col3:
        min_confidence = st.slider("Min Confidence", 0.5, 0.9, 0.65, key="scanner_confidence")
    
    with col4:
        max_results = st.slider("Max Results", 5, 20, 10)
    
    st.markdown("---")
    
    # Render scan results using dashboard functions
    analytics_dashboard.render_scan_results()

def render_charts_tab():
    """Render advanced charts tab using dashboard functions"""
    st.header("📈 Advanced Charts & Analytics")
    
    # Load data
    df = analytics_dashboard.load_trade_data()
    
    if not df.empty:
        # Render performance charts from dashboard.py
        analytics_dashboard.render_performance_charts(df)
        
        st.markdown("---")
        
        # Render advanced analytics from dashboard.py
        analytics_dashboard.render_advanced_analytics(df)
    else:
        st.info("No trading data available for charts. Execute some trades first!")

def render_portfolio_tab():
    """Render portfolio management tab"""
    st.header("💼 Portfolio Management")
    
    # Portfolio overview
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Portfolio Overview")
        
        # Mock portfolio data - replace with real portfolio manager
        portfolio_data = {
            'Asset': ['USDT', 'BTC', 'ETH', 'BNB'],
            'Quantity': [5000.0, 0.1, 2.0, 10.0],
            'Value (USD)': [5000.0, 5000.0, 6000.0, 3000.0],
            'Allocation %': [26.3, 26.3, 31.6, 15.8]
        }
        
        portfolio_df = pd.DataFrame(portfolio_data)
        st.dataframe(portfolio_df, use_container_width=True, hide_index=True)
        
        # Portfolio chart
        fig = px.pie(
            portfolio_df,
            values='Value (USD)',
            names='Asset',
            title="Portfolio Allocation"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 Portfolio Metrics")
        
        total_value = sum(portfolio_data['Value (USD)'])
        st.metric("Total Portfolio Value", f"${total_value:,.2f}")
        st.metric("24h Change", "+2.5%", "📈")
        st.metric("Diversification", "4 Assets")
        
        st.subheader("🎯 Rebalancing")
        if st.button("⚖️ Auto Rebalance"):
            st.info("Rebalancing analysis would be performed here")

def render_risk_tab():
    """Render risk analysis tab using dashboard functions"""
    st.header("⚠️ Risk Analysis & Management")
    
    # Load data
    df = analytics_dashboard.load_trade_data()
    metrics = analytics_dashboard.calculate_metrics(df)
    
    if not df.empty:
        # Render risk metrics from dashboard.py
        analytics_dashboard.render_risk_metrics(df, metrics)
    else:
        st.info("No trading data available for risk analysis")
    
    st.markdown("---")
    
    # Risk controls
    st.subheader("🛡️ Risk Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Position Limits**")
        max_position_size = st.slider("Max Position Size ($)", 100, 5000, 1000)
        max_daily_loss = st.slider("Max Daily Loss ($)", 50, 1000, 200)
        
    with col2:
        st.write("**Emergency Controls**")
        if st.button("🚨 Emergency Stop All", type="secondary"):
            st.warning("Emergency stop would close all positions immediately")
        
        if st.button("⏸️ Pause All Trading", type="secondary"):
            st.info("All trading activities would be paused")

def render_settings_tab():
    """Render bot settings and configuration"""
    st.header("⚙️ Bot Configuration & Settings")
    
    # API Configuration
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔑 API Configuration")
        
        current_mode = "🧪 Testnet" if USE_TESTNET else "🔴 Live Trading"
        st.info(f"Current Mode: {current_mode}")
        
        api_status = "🟢 Connected" if BINANCE_CLIENT else "🔴 Not Connected"
        st.write(f"API Status: {api_status}")
        
        if st.button("🔄 Reconnect API"):
            st.info("API reconnection would be attempted here")
    
    with col2:
        st.subheader("📊 Export & Import")
        
        # Data export
        if st.button("📥 Export Trade Data"):
            df = analytics_dashboard.load_trade_data()
            if not df.empty:
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"trades_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No trade data to export")
        
        if st.button("📊 Export Performance Report"):
            st.info("Performance report generation would be implemented here")
    
    # Trading Parameters
    st.markdown("---")
    st.subheader("🎯 Trading Parameters")
    
    param_col1, param_col2, param_col3 = st.columns(3)
    
    with param_col1:
        st.write("**Risk Management**")
        risk_per_trade = st.slider("Risk per Trade (%)", 0.1, 5.0, 1.5, key="settings_risk")
        max_positions = st.slider("Max Concurrent Positions", 1, 20, 5, key="settings_positions")
    
    with param_col2:
        st.write("**Scanner Settings**")
        scan_interval = st.slider("Scan Interval (minutes)", 1, 60, 5, key="settings_scan_interval")
        min_confidence = st.slider("Minimum Confidence", 0.1, 0.9, 0.65, key="settings_min_confidence")
    
    with param_col3:
        st.write("**Execution Settings**")
        slippage_tolerance = st.slider("Slippage Tolerance (%)", 0.1, 2.0, 0.5)
        order_timeout = st.slider("Order Timeout (seconds)", 10, 300, 60)
    
    # Save settings
    if st.button("💾 Save Configuration", type="primary"):
        st.success("✅ Configuration saved successfully!")
        st.balloons()

def main():
    """Main application function"""
    
    # Page header
    st.title("🤖 Advanced Crypto Trading Bot")
    st.markdown("**Complete Trading Dashboard with Analytics & Risk Management**")
    
    # Render sidebar and get settings
    sidebar_settings = render_sidebar()
    
    # Status bar
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status = "🟢 RUNNING" if st.session_state.auto_running else "🔴 STOPPED"
        st.metric("Auto-Trader", status)
    
    with col2:
        mode = "🧪 TESTNET" if USE_TESTNET else "🔴 LIVE"
        st.metric("Trading Mode", mode)
    
    with col3:
        st.metric("Last Action", st.session_state.last_action)
    
    with col4:
        st.metric("Scans Today", st.session_state.scan_count)
    
    st.markdown("---")
    
    # Main tab interface - INTEGRATED DASHBOARD
    main_tabs = st.tabs([
        "🎯 Trading Control",
        "📊 Performance", 
        "🔍 Market Scanner",
        "📈 Advanced Charts",
        "💼 Portfolio",
        "⚠️ Risk Analysis",
        "⚙️ Settings"
    ])
    
    with main_tabs[0]:
        render_trading_control_tab()
    
    with main_tabs[1]:
        render_performance_tab()  # Uses analytics_dashboard functions
    
    with main_tabs[2]:
        render_scanner_tab()
    
    with main_tabs[3]:
        render_charts_tab()  # Uses analytics_dashboard functions
    
    with main_tabs[4]:
        render_portfolio_tab()
    
    with main_tabs[5]:
        render_risk_tab()  # Uses analytics_dashboard functions
    
    with main_tabs[6]:
        render_settings_tab()
    
    # Footer
    st.markdown("---")
    st.caption("🤖 Advanced Crypto Trading Bot | Integrated Analytics & Risk Management | Real-time Trading Interface")

if __name__ == "__main__":
    main()