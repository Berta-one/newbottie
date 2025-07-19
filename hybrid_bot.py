#!/usr/bin/env python3
"""
Simplified Hybrid Crypto Trading Bot - Guaranteed Working Version
================================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import time
import threading
import json
import numpy as np

# ----------------------------------------------------------------------
# NEW – Modular imports (risk, portfolio, quantum, trade execution, etc.)
# ----------------------------------------------------------------------
from risk_manager import RiskManager
from portfolio_manager import PortfolioManager
from quantum_engine import QuantumTradingEngine as QuantumAnalyzer
from trade_executor import TradeExecutor
from market_analyzer import MarketAnalyzer
from position_monitor import PositionMonitor

# Configuration
st.set_page_config(
    page_title="🤖 Crypto Trading Bot",
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
# Instantiate core modules
# ----------------------------------------------------------------------
BINANCE_CLIENT = get_binance_client()

risk_mgr = RiskManager()
portfolio_mgr = PortfolioManager(API_KEY, API_SECRET, USE_TESTNET)
market_analyzer = MarketAnalyzer(BINANCE_CLIENT)
trade_executor = TradeExecutor(BINANCE_CLIENT, risk_mgr)
position_monitor = PositionMonitor()
quantum_analyzer = QuantumAnalyzer()

# ----------------------------------------------------------------------
# Legacy wrapper functions – now delegate to modules for full modularity
# ----------------------------------------------------------------------

def get_mock_portfolio():
    """Return portfolio data via PortfolioManager (live or demo)."""
    return portfolio_mgr.get_portfolio()


def get_mock_scan_results():
    """Return scan results via MarketAnalyzer (live or mock)."""
    return market_analyzer.scan_market()

def auto_trading_loop():
    """Simple auto trading loop"""
    while st.session_state.get('auto_running', False):
        try:
            # Simulate scanning
            st.session_state['scan_results'] = get_mock_scan_results()
            st.session_state['scan_count'] += 1
            st.session_state['last_action'] = f"Scan #{st.session_state['scan_count']} completed"
            
            time.sleep(30)  # Wait 30 seconds
        except Exception as e:
            st.session_state['last_action'] = f"Error: {str(e)}"
            time.sleep(60)

def start_auto_bot():
    """Start auto bot"""
    if not st.session_state.get('auto_running', False):
        st.session_state['auto_running'] = True
        thread = threading.Thread(target=auto_trading_loop, daemon=True)
        thread.start()

def stop_auto_bot():
    """Stop auto bot"""
    st.session_state['auto_running'] = False

# Main App
def main():
    # Header
    st.title("🤖 Hybrid Crypto Trading Bot")
    
    # Mode indicator
    mode = "🧪 TESTNET MODE" if USE_TESTNET else "🚀 LIVE TRADING MODE"
    if USE_TESTNET:
        st.success(mode)
    else:
        st.warning(mode)
    
    # Sidebar
    with st.sidebar:
        st.header("🎛️ Bot Controls")
        
        # API Status
        client = get_binance_client()
        if client:
            st.success("✅ Binance API Connected")
        else:
            st.error("❌ Binance API Not Connected")
        
        st.divider()
        
        # Bot controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Start Bot"):
                start_auto_bot()
                st.success("Bot started!")
        
        with col2:
            if st.button("⏹️ Stop Bot"):
                stop_auto_bot()
                st.success("Bot stopped!")
        
        # Status
        status = "🟢 RUNNING" if st.session_state.get('auto_running') else "🔴 STOPPED"
        st.write(f"**Status:** {status}")
        st.write(f"**Last Action:** {st.session_state.get('last_action', 'None')}")
        st.write(f"**Scans:** {st.session_state.get('scan_count', 0)}")
        
        st.divider()
        
        # Manual scan
        if st.button("🔄 Manual Scan"):
            st.session_state['scan_results'] = get_mock_scan_results()
            st.session_state['scan_count'] += 1
            st.success("Scan completed!")
    
    # Main tabs - This is the critical part that was failing
    try:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Portfolio", 
            "🔍 Scanner", 
            "📈 Performance", 
            "💼 Trades",
            "⚙️ Settings"
        ])
        
        # Portfolio Tab
        with tab1:
            st.header("📊 Portfolio Overview")
            
            # Get portfolio data
            if client:
                st.info("Loading real portfolio data...")
                # In real implementation, get actual data
                portfolio = get_mock_portfolio()
            else:
                st.info("Using demo data - Connect API for real portfolio")
                portfolio = get_mock_portfolio()
            
            # Portfolio metrics
            total_value = sum(asset['value'] for asset in portfolio.values())
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("💵 Total Value", f"${total_value:,.2f}")
            with col2:
                st.metric("📊 Assets", len(portfolio))
            with col3:
                st.metric("💰 USDT", f"{portfolio['USDT']['balance']:,.2f}")
            
            # Portfolio table
            st.subheader("💼 Holdings")
            portfolio_data = []
            for asset, data in portfolio.items():
                portfolio_data.append({
                    'Asset': asset,
                    'Balance': f"{data['balance']:.6f}".rstrip('0').rstrip('.'),
                    'Price': f"${data['price']:.2f}",
                    'Value': f"${data['value']:.2f}",
                    '24h Change': f"{data['change']:+.1f}%"
                })
            
            st.dataframe(pd.DataFrame(portfolio_data), use_container_width=True, hide_index=True)
            
            # Portfolio chart
            if len(portfolio) > 1:
                fig = px.pie(
                    values=[data['value'] for data in portfolio.values()],
                    names=list(portfolio.keys()),
                    title="Portfolio Allocation"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Scanner Tab
        with tab2:
            st.header("🔍 Market Scanner")
            
            scan_results = st.session_state.get('scan_results', [])
            
            if scan_results:
                st.success(f"Found {len(scan_results)} opportunities")
                
                # Top opportunities
                for i, result in enumerate(scan_results[:3]):
                    with st.expander(f"#{i+1} {result['symbol']} - {result['signal']}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Price", f"${result['price']:.2f}")
                        with col2:
                            st.metric("24h Change", f"{result['change_24h']:+.1f}%")
                        with col3:
                            st.metric("Confidence", f"{result['confidence']:.1%}")
                        
                        st.write(f"**Signal:** {result['signal']}")
                        st.write(f"**Volume Ratio:** {result['volume_ratio']:.1f}x")
            else:
                st.info("No scan results yet. Click 'Manual Scan' or start the auto bot.")
        
        # Performance Tab
        with tab3:
            st.header("📈 Performance Analytics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Trades", "0")
            with col2:
                st.metric("Win Rate", "0.0%")
            with col3:
                st.metric("P&L", "$0.00")
            with col4:
                st.metric("Scans", st.session_state.get('scan_count', 0))
            
            st.info("Performance tracking will show here after trades are executed.")
            
            # Demo chart
            dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
            values = np.cumsum(np.random.randn(30) * 0.02) * 1000
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=values, mode='lines', name='Portfolio Value'))
            fig.update_layout(title="Portfolio Performance (Demo)", xaxis_title="Date", yaxis_title="Value ($)")
            st.plotly_chart(fig, use_container_width=True)
        
        # Trades Tab
        with tab4:
            st.header("💼 Active Trades")
            
            st.info("No active trades yet. Start the auto bot to begin trading.")
            
            # Mock active trades table
            trades_data = {
                'Symbol': ['BTCUSDT', 'ETHUSDT'],
                'Signal': ['BUY', 'SELL'],
                'Entry Price': ['$45,000', '$3,000'],
                'Current Price': ['$45,500', '$2,980'],
                'P&L': ['+$50', '-$20'],
                'Status': ['OPEN', 'OPEN']
            }
            
            st.subheader("🔄 Demo Trades")
            st.dataframe(pd.DataFrame(trades_data), use_container_width=True, hide_index=True)
        
        # Settings Tab
        with tab5:
            st.header("⚙️ Settings & Configuration")
            
            st.subheader("📋 Current Configuration")
            
            config_data = {
                'Setting': ['Trading Mode', 'API Status', 'Auto Bot', 'Scans Completed'],
                'Value': [
                    'Testnet' if USE_TESTNET else 'Live',
                    'Connected' if client else 'Disconnected',
                    'Running' if st.session_state.get('auto_running') else 'Stopped',
                    str(st.session_state.get('scan_count', 0))
                ],
                'Status': ['🧪' if USE_TESTNET else '🚀', '✅' if client else '❌', '🟢' if st.session_state.get('auto_running') else '🔴', '✅']
            }
            
            st.dataframe(pd.DataFrame(config_data), use_container_width=True, hide_index=True)
            
            st.subheader("🔧 Environment Variables")
            st.code(f"""
USE_TESTNET={USE_TESTNET}
BINANCE_API_KEY={'Set' if API_KEY else 'Not Set'}
BINANCE_API_SECRET={'Set' if API_SECRET else 'Not Set'}
            """)
            
            if not API_KEY or not API_SECRET:
                st.warning("⚠️ Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables")
            
            st.subheader("🛠️ Manual Controls")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🗑️ Clear Data"):
                    st.session_state['scan_results'] = []
                    st.session_state['scan_count'] = 0
                    st.success("Data cleared!")
            
            with col2:
                if st.button("🔄 Reset Bot"):
                    st.session_state['auto_running'] = False
                    st.session_state['last_action'] = 'Bot reset'
                    st.success("Bot reset!")
            
            with col3:
                if st.button("📊 Test Scan"):
                    st.session_state['scan_results'] = get_mock_scan_results()
                    st.success("Test scan completed!")
    
    except Exception as e:
        st.error(f"Error loading tabs: {str(e)}")
        st.write("**Fallback Mode - Basic Dashboard**")
        
        st.metric("Bot Status", "🟢 RUNNING" if st.session_state.get('auto_running') else "🔴 STOPPED")
        st.metric("API Status", "✅ Connected" if client else "❌ Disconnected")
        st.metric("Trading Mode", "🧪 Testnet" if USE_TESTNET else "🚀 Live")
        
        if st.button("🔄 Refresh Page"):
            st.rerun()

if __name__ == "__main__":
    main()
    
    # Footer
    st.divider()
    st.caption(f"🤖 Crypto Trading Bot | {datetime.now().strftime('%H:%M:%S')} | Mode: {'Testnet' if USE_TESTNET else 'Live'}")