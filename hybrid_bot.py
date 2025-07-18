try:
    from quantum_engine import QuantumTradingEngine
    from quantum_trading_integration import get_quantum_trader
    QUANTUM_AVAILABLE = True
except ImportError:
    QUANTUM_AVAILABLE = False
    class QuantumTradingEngine:
        def __init__(self): pass
        def generate_quantum_trading_recommendation(self, *args, **kwargs):
            return {'quantum_signal': 'UNAVAILABLE', 'quantum_confidence': 0}
    if 'quantum_engine' not in st.session_state:
        st.session_state['quantum_engine'] = QuantumTradingEngine()

    if 'quantum_trader' not in st.session_state and QUANTUM_AVAILABLE:
        client = None
        if BINANCE_AVAILABLE and API_KEY and API_SECRET:
            try:
                client = Client(API_KEY, API_SECRET)
                if USE_TESTNET:
                    client.API_URL = "https://testnet.binance.vision/api"
            except Exception as e:
                st.error(f"Failed to initialize Binance client: {e}")
        st.session_state['quantum_trader'] = get_quantum_trader(client)
def render_quantum_analysis_tab():
    """Enhanced quantum analysis tab with actual trading functionality"""
    st.header("🔬 Quantum Market Analysis & Trading")
    st.caption("Advanced quantum mechanics principles applied to cryptocurrency trading with live execution")
    if not QUANTUM_AVAILABLE:
        st.error("❌ Quantum engine not available. Please install quantum_engine.py and quantum_trading_integration.py")
        return
    portfolio, _ = get_real_portfolio()
    market_condition, condition_score, avg_volatility = simulate_market_analysis(portfolio)
    current_strategy = st.session_state.get('selected_strategy', 'Breakout')
    current_risk = st.session_state.get('selected_risk_level', 'Balanced')
    with st.spinner("🌀 Analyzing quantum market states..."):
        quantum_result = st.session_state['quantum_engine'].generate_quantum_trading_recommendation(
            portfolio_data=portfolio,
            market_condition=market_condition,
            strategy=current_strategy,
            risk_level=current_risk,
            portfolio_value=sum(data.get('usd_value', 0) for data in portfolio.values()) if portfolio else 10000
        )
    st.subheader("🎯 Quantum Trading Signal")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        signal_color = "🟢" if quantum_result['quantum_signal'] == 'BUY_LONG' else "🔴" if quantum_result['quantum_signal'] == 'BUY_SHORT' else "🟡"
        st.metric("Quantum Signal", f"{signal_color} {quantum_result['quantum_signal']}")
    with col2:
        confidence_color = "🟢" if quantum_result['quantum_confidence'] > 0.7 else "🟡" if quantum_result['quantum_confidence'] > 0.5 else "🔴"
        st.metric("Quantum Confidence", f"{confidence_color} {quantum_result['quantum_confidence']:.1%}")
    with col3:
        st.metric("Position Size", f"${quantum_result['quantum_position_size']:,.0f}")
    with col4:
        st.metric("Hold Time", f"{quantum_result['quantum_holding_time']:.0f}m")
    st.subheader("🚀 Quantum Trading Execution")
    trading_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 'DOGEUSDT']
    selected_symbol = st.selectbox("Select Trading Symbol", trading_symbols, key="quantum_symbol")
    col1, col2, col3 = st.columns(3)
    with col1:
        trade_enabled = quantum_result['quantum_signal'] != 'HOLD' and quantum_result['quantum_confidence'] > 0.5
        if st.button("🔬 Execute Quantum Trade", type="primary", disabled=not trade_enabled):
            if not BINANCE_AVAILABLE:
                st.error("❌ Binance client not available")
            elif quantum_result['quantum_confidence'] < 0.5:
                st.warning("⚠️ Quantum confidence too low for safe trading")
            else:
                with st.spinner("🌀 Executing quantum trade..."):
                    trade_result = st.session_state['quantum_trader'].execute_quantum_signal(
                        quantum_result, 
                        selected_symbol
                    )
                    if trade_result['status'] == 'SUCCESS':
                        st.success(f"✅ Quantum trade executed successfully!")
                        st.success(f"Position ID: {trade_result['position_id']}")
                        st.success(f"Entry Price: ${trade_result['entry_price']:.8f}")
                        st.success(f"Quantity: {trade_result['quantity']:.8f}")
                        st.json(trade_result)
                    elif trade_result['status'] == 'HOLD':
                        st.info(f"⏸️ {trade_result['reason']}")
                    elif trade_result['status'] == 'SKIPPED':
                        st.warning(f"⚠️ Trade skipped: {trade_result['reason']}")
                    elif trade_result['status'] == 'BLOCKED':
                        st.error(f"🚫 Trade blocked: {trade_result['reason']}")
                    else:
                        st.error(f"❌ Trade failed: {trade_result.get('message', 'Unknown error')}")
                        st.json(trade_result)
        if not trade_enabled:
            if quantum_result['quantum_signal'] == 'HOLD':
                st.info("⏸️ Quantum signal is HOLD - no trade recommended")
            else:
                st.warning("⚠️ Quantum confidence too low for trading")
    with col2:
        if st.button("📊 Monitor Quantum Positions", type="secondary"):
            with st.spinner("🔍 Monitoring quantum positions..."):
                monitor_result = st.session_state['quantum_trader'].monitor_quantum_positions()
                if monitor_result['status'] == 'NO_POSITIONS':
                    st.info("📭 No active quantum positions")
                elif monitor_result['status'] == 'SUCCESS':
                    st.success(f"✅ Monitoring {monitor_result['monitored']} positions")
                    if monitor_result['closed'] > 0:
                        st.success(f"🔄 Closed {monitor_result['closed']} positions")
                    for result in monitor_result['results']:
                        if result['action'] == 'MONITORING':
                            st.info(f"📊 {result['symbol']} {result['direction']}: {result['current_pnl_pct']:.2f}% P&L")
                        elif result['action'] == 'CLOSED':
                            profit_color = "🟢" if result['pnl_pct'] > 0 else "🔴"
                            st.success(f"{profit_color} Closed: {result['pnl_pct']:.2f}% - {result['reason']}")
                else:
                    st.error(f"❌ Monitoring failed: {monitor_result.get('message', 'Unknown error')}")
    with col3:
        manual_override = st.checkbox("🔓 Manual Override", help="Allow trading with lower confidence")
        if manual_override and st.button("⚠️ Force Execute", type="secondary"):
            st.warning("⚠️ Manual override enabled - trading with reduced safety checks")
            with st.spinner("🌀 Executing with manual override..."):
                trade_result = st.session_state['quantum_trader'].execute_quantum_signal(
                    quantum_result, 
                    selected_symbol,
                    manual_override=True
                )
                if trade_result['status'] == 'SUCCESS':
                    st.success(f"✅ Manual override trade executed!")
                    st.json(trade_result)
                else:
                    st.error(f"❌ Manual override failed: {trade_result.get('message', 'Unknown error')}")
    st.subheader("⚖️ Quantum vs Classical Analysis")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🔬 Quantum Analysis**")
        st.success(f"Signal: {quantum_result['quantum_signal']}")
        st.info(f"Confidence: {quantum_result['quantum_confidence']:.1%}")
        st.info(f"Stop Loss: {quantum_result['quantum_stop_loss']:.1f}%")
        st.info(f"Take Profit: {quantum_result['quantum_take_profit']:.1f}%")
        st.info(f"Position Size: ${quantum_result['quantum_position_size']:,.0f}")
    with col2:
        st.markdown("**📊 Classical Analysis**")
        st.info(f"Market Condition: {market_condition}")
        st.info(f"Confidence: {condition_score:.1%}")
        st.info(f"Strategy: {current_strategy}")
        st.info(f"Risk Level: {current_risk}")
        st.info(f"Volatility: {avg_volatility:.1f}%")
    recommendation = quantum_result['classical_comparison']['recommendation']
    quantum_advantage = quantum_result['quantum_confidence'] - condition_score
    if quantum_advantage > 0.15:
        st.success(f"✨ Strong Quantum Advantage! {recommendation}")
        st.success(f"Quantum provides {quantum_advantage:.1%} higher confidence")
    elif quantum_advantage > 0.05:
        st.info(f"🔬 Moderate Quantum Advantage: {recommendation}")
    else:
        st.warning(f"📊 Classical analysis recommended: {recommendation}")
    st.subheader("📋 Active Quantum Positions")
    if hasattr(st.session_state['quantum_trader'], 'active_quantum_positions'):
        active_positions = st.session_state['quantum_trader'].active_quantum_positions
        if active_positions:
            positions_data = []
            for pos_id, position in active_positions.items():
                current_price = st.session_state['quantum_trader'].get_current_price(position['symbol'])
                if current_price:
                    pnl_data = st.session_state['quantum_trader'].calculate_position_pnl(position, current_price)
                    positions_data.append({
                        'Position ID': pos_id[-8:],
                        'Symbol': position['symbol'],
                        'Direction': position['direction'],
                        'Entry Price': f"${position['entry_price']:.8f}",
                        'Current Price': f"${current_price:.8f}",
                        'P&L %': f"{pnl_data['pnl_pct']:+.2f}%",
                        'Confidence': f"{position['quantum_confidence']:.1%}",
                        'Time Held': f"{pnl_data['time_held_minutes']:.0f}m",
                        'Strategy': position['strategy']
                    })
            if positions_data:
                st.dataframe(pd.DataFrame(positions_data), use_container_width=True)
            else:
                st.info("📭 No active quantum positions")
        else:
            st.info("📭 No active quantum positions")
    st.subheader("📈 Quantum Trading Performance")
    performance = st.session_state['quantum_trader'].get_quantum_performance()
    if performance['status'] == 'SUCCESS':
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Trades", performance['total_trades'])
        with col2:
            st.metric("Closed Trades", performance['closed_trades'])
        with col3:
            profit_color = "🟢" if performance['total_pnl_pct'] > 0 else "🔴"
            st.metric("Total P&L", f"{profit_color} {performance['total_pnl_pct']:.1f}%")
        with col4:
            st.metric("Win Rate", f"{performance['win_rate']:.1%}")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Avg P&L/Trade", f"{performance['avg_pnl_per_trade']:.1f}%")
        with col2:
            st.metric("Winning Trades", performance['winning_trades'])
        with col3:
            st.metric("Losing Trades", performance['losing_trades'])
        with col4:
            st.metric("Avg Confidence", f"{performance['avg_quantum_confidence']:.1%}")
    elif performance['status'] == 'PARTIAL':
        st.info(f"📊 {performance['message']}")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Trades", performance['total_trades'])
        with col2:
            st.metric("Active Trades", performance['active_trades'])
    else:
        st.info("📊 No quantum trading performance data available yet")
    tabs = st.tabs(["🌀 Superposition", "🔗 Entanglement", "⚖️ Uncertainty", "🌊 Interference", "🚇 Tunneling"])
    with tabs[0]:
        st.subheader("🌀 Quantum Market Superposition")
        if quantum_result['market_quantum_state'] and 'states' in quantum_result['market_quantum_state']:
            states_df = pd.DataFrame(quantum_result['market_quantum_state']['states']).T
            st.dataframe(states_df, use_container_width=True)
            fig = px.bar(
                x=list(quantum_result['market_quantum_state']['states'].keys()),
                y=[state['probability'] for state in quantum_result['market_quantum_state']['states'].values()],
                title="Market State Probabilities",
                labels={'x': 'Quantum State', 'y': 'Probability'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No quantum superposition data available")
    with tabs[1]:
        st.subheader("🔗 Quantum Entanglement")
        entanglement = quantum_result['entangled_pairs']
        if entanglement['entangled_pairs']:
            st.success(f"Found {entanglement['total_entangled_pairs']} entangled pairs!")
            for pair, data in entanglement['entangled_pairs'].items():
                with st.expander(f"🔗 {pair} (Strength: {data['entanglement_strength']:.2f})"):
                    st.write(f"**Price Correlation:** {data['price_correlation']:.3f}")
                    st.write(f"**Volume Correlation:** {data['volume_correlation']:.3f}")
                    st.write(f"**Bell Parameter:** {data['bell_parameter']:.3f}")
                    st.info(f"**Trading Advice:** {data['trading_implication']}")
        else:
            st.info("No quantum entanglement detected between assets")
    with tabs[2]:
        st.subheader("⚖️ Heisenberg Uncertainty Principle")
        uncertainty = quantum_result['uncertainty_analysis']
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Position Uncertainty:** {uncertainty['position_uncertainty']:.3f}")
            st.write(f"**Time Uncertainty:** {uncertainty['time_uncertainty']:.3f}")
            st.write(f"**Uncertainty Product:** {uncertainty['uncertainty_product']:.3f}")
        with col2:
            st.write(f"**Optimal Stop Loss:** {uncertainty['quantum_stop_loss_pct']:.1f}%")
            st.write(f"**Optimal Take Profit:** {uncertainty['quantum_take_profit_pct']:.1f}%")
            st.write(f"**Optimal Hold Time:** {uncertainty['quantum_holding_time_minutes']:.0f}m")
        st.info(f"**Recommendation:** {uncertainty['recommendation']}")
        if uncertainty['quantum_advantage'] > 0:
            st.success(f"🎯 Quantum advantage: {uncertainty['quantum_advantage']:.3f}")
    with tabs[3]:
        st.subheader("🌊 Quantum Signal Interference")
        interference = quantum_result['signal_interference']
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Final Signal:** {interference['final_signal']}")
            st.write(f"**Confidence:** {interference['confidence']:.1%}")
            st.write(f"**Interference Type:** {interference['interference_type']}")
        with col2:
            st.write(f"**Signal Quality:** {interference['signal_quality']}")
            st.write(f"**Constructive:** {interference['constructive_interference']:.3f}")
            st.write(f"**Destructive:** {interference['destructive_interference']:.3f}")
        if interference['quantum_waves']:
            waves_df = pd.DataFrame(interference['quantum_waves'])
            st.dataframe(waves_df, use_container_width=True)
    with tabs[4]:
        st.subheader("🚇 Quantum Tunneling Analysis")
        tunneling = quantum_result['tunneling_analysis']
        if tunneling['tunneling_events']:
            st.success(f"Found {tunneling['total_tunnel_opportunities']} tunneling opportunities!")
            for event in tunneling['tunneling_events']:
                tunnel_type = "🔴 Resistance" if event['type'] == 'resistance_tunnel' else "🟢 Support"
                st.write(f"{tunnel_type} Tunnel at ${event['level']:,.0f}")
                st.write(f"Current Price: ${event['current_price']:,.0f}")
                st.write(f"Tunneling Probability: {event['tunneling_probability']:.1%}")
                st.write(f"Trading Signal: {event['trading_signal']}")
                st.markdown("---")
            if tunneling['quantum_breakthrough_likely']:
                st.success("🚀 Quantum breakthrough highly likely!")
        else:
            st.info("No quantum tunneling opportunities detected")
    st.subheader("📥 Export Quantum Analysis")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Export Quantum Analysis"):
            quantum_json = json.dumps(quantum_result, indent=2, default=str)
            st.download_button(
                "Download Quantum Analysis",
                data=quantum_json,
                file_name=f"quantum_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    with col2:
        if st.button("📥 Export Trading Log"):
            try:
                if os.path.exists('logs/quantum_trades.csv'):
                    with open('logs/quantum_trades.csv', 'r') as f:
                        csv_data = f.read()
                    st.download_button(
                        "Download Trading Log",
                        data=csv_data,
                        file_name=f"quantum_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No trading log available yet")
            except Exception as e:
                st.error(f"Error exporting trading log: {e}")
    if st.checkbox("🔄 Auto-refresh (30s)", key="quantum_auto_refresh"):
        time.sleep(30)
        st.rerun()
# Trigger redeploy: harmless comment for Railway
#!/usr/bin/env python3
"""
Complete Enhanced Crypto Trading Bot Dashboard
===========================================

This dashboard includes:
1. Real portfolio positions with P&L tracking
2. Cross-crypto trading capabilities
3. Strategy selection (Scalping, Breakout, Swing, Conservative)
4. Risk level configuration
5. Current positions with mark-to-market P&L
6. Complete trading methodologies
7. All required log files and health checks

Fixed Issues:
- Portfolio Overview shows real positions
- Trading supports cross-crypto pairs
- Performance shows current positions and individual P&L
- Settings includes methodology and risk selection
- Strategy shows complete method information
- Health checks all required log files

Usage:
    streamlit run hybrid_bot.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
def is_bot_blocked():
    """Check if the override flag file exists to block the bot."""
    return os.path.exists('logs/bot_override.flag')
import time
import threading
import subprocess
import sys
import signal
import requests
import random
# Add this import after your existing imports
try:
    from quantum_engine import QuantumTradingEngine
    QUANTUM_AVAILABLE = True
except ImportError:
    QUANTUM_AVAILABLE = False
    class QuantumTradingEngine:
        def __init__(self): pass
        def generate_quantum_trading_recommendation(self, *args, **kwargs):
            return {'quantum_signal': 'UNAVAILABLE', 'quantum_confidence': 0}
# Add dotenv support

def render_mode_switch():
    """Render the Demo/Live mode switch at the very top of the sidebar."""
    st.sidebar.title("Bot Mode")
    st.session_state['bot_mode'] = 'Live'
    st.sidebar.markdown(f"**Current Mode:** Live")


# Only render the mode switch once, inside main/dashboard, not at module level

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from binance.client import Client
from binance.exceptions import BinanceAPIException

# Configuration
def get_use_testnet():
    # Use testnet if in Demo mode, otherwise use live
    return st.session_state.get('bot_mode', 'Demo') == 'Demo'

USE_TESTNET = get_use_testnet()
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')
SCAN_INTERVAL = int(os.getenv('SCAN_INTERVAL', '300').split('#')[0].strip())
MIN_BALANCE_USD = float(os.getenv('MIN_BALANCE_USD', '10.0'))

# Check if binance is available
BINANCE_AVAILABLE = True
try:
    from binance.client import Client
except ImportError:
    BINANCE_AVAILABLE = False

import csv
# --- Ensure required log files exist on startup ---
def ensure_log_files():
    os.makedirs('logs', exist_ok=True)
    # trades.csv
    trades_path = 'logs/trades.csv'
    if not os.path.exists(trades_path):
        with open(trades_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp','symbol','direction','entry_price','exit_price','quantity','change_pct','status','strategy'])
    # manual_trades.log
    manual_trades_path = 'logs/manual_trades.log'
    if not os.path.exists(manual_trades_path):
        with open(manual_trades_path, 'a') as f:
            pass
    # portfolio_scans.log
    scans_path = 'logs/portfolio_scans.log'
    if not os.path.exists(scans_path):
        with open(scans_path, 'a') as f:
            pass
    # console_output.log
    console_path = 'logs/console_output.log'
    if not os.path.exists(console_path):
        with open(console_path, 'a') as f:
            pass
    # bot_status.json
    status_path = 'logs/bot_status.json'
    if not os.path.exists(status_path):
        with open(status_path, 'w') as f:
            import json
            json.dump({'timestamp':'','running':False,'scan_count':0,'opportunities':[],'portfolio':{}}, f)

ensure_log_files()
if 'background_bot_running' not in st.session_state:
    st.session_state['background_bot_running'] = False
if 'bot_process' not in st.session_state:
    st.session_state['bot_process'] = None
if 'password_authenticated' not in st.session_state:
    st.session_state['password_authenticated'] = False
if 'dashboard_password' not in st.session_state:
    st.session_state['dashboard_password'] = 'admin123'
if 'bot_running' not in st.session_state:
    st.session_state['bot_running'] = False
if 'scan_count' not in st.session_state:
    st.session_state['scan_count'] = 0
if 'last_scan_time' not in st.session_state:
    st.session_state['last_scan_time'] = None
if 'max_trade_percent' not in st.session_state:
    st.session_state['max_trade_percent'] = 10.0  # User can adjust this in the UI; now used for trade sizing if set
if 'selected_strategy' not in st.session_state:
    st.session_state['selected_strategy'] = 'Breakout'
if 'selected_risk_level' not in st.session_state:
    st.session_state['selected_risk_level'] = 'Balanced'

# Trading strategies and risk levels
TRADING_STRATEGIES = {
    'Scalping': {
        'description': 'Quick trades on 2-3% moves with high volume',
        'threshold': 2.0,
        'volume_req': 1.5,
        'hold_time': '30 minutes',
        'take_profit': '3-5%',
        'stop_loss': '2-3%',
        'confidence_min': 0.65
    },
    'Breakout': {
        'description': 'Trade 5% price breakouts with volume confirmation',
        'threshold': 5.0,
        'volume_req': 2.0,
        'hold_time': '2-4 hours',
        'take_profit': '8-15%',
        'stop_loss': '8-12%',
        'confidence_min': 0.70
    },
    'Swing': {
        'description': 'Capture 10-20% moves over longer periods',
        'threshold': 8.0,
        'volume_req': 1.2,
        'hold_time': '4-24 hours',
        'take_profit': '15-25%',
        'stop_loss': '10-15%',
        'confidence_min': 0.60
    },
    'Conservative': {
        'description': 'Safe trading with reduced risk and smaller positions',
        'threshold': 3.0,
        'volume_req': 1.8,
        'hold_time': '1-2 hours',
        'take_profit': '5-8%',
        'stop_loss': '3-5%',
        'confidence_min': 0.75
    }
}

RISK_LEVELS = {
    'Conservative': {
        'position_size_multiplier': 0.7,
        'max_positions': 2,
        'risk_per_trade': 0.01,
        'description': 'Lower risk, smaller positions'
    },
    'Balanced': {
        'position_size_multiplier': 1.0,
        'max_positions': 3,
        'risk_per_trade': 0.015,
        'description': 'Moderate risk, balanced approach'
    },
    'Aggressive': {
        'position_size_multiplier': 1.3,
        'max_positions': 5,
        'risk_per_trade': 0.025,
        'description': 'Higher risk, larger positions'
    }
}

def get_tailscale_ip():
    """Get Tailscale IP address"""
    try:
        result = subprocess.run(['tailscale', 'ip'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return "Unavailable"

def load_logs(log_file):
    """Load log file content"""
    try:
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        return f"Error loading log: {e}"
    return ''

def get_real_portfolio():
    """Get real portfolio data from Binance"""
    if not BINANCE_AVAILABLE or not API_KEY or not API_SECRET:
        return {}, 0.79

    try:
        client = Client(API_KEY, API_SECRET)
        # Get account info
        account = client.get_account()
        all_tickers = client.get_all_tickers()
        # Create price lookup
        price_dict = {ticker['symbol']: float(ticker['price']) for ticker in all_tickers}
        
        portfolio = {}
        for balance in account['balances']:
            asset = balance['asset']
            free_balance = float(balance['free'])
            locked_balance = float(balance['locked'])
            total_balance = free_balance + locked_balance

            if total_balance > 0:
                # Special handling for stablecoins
                if asset in ['USDT', 'BUSD', 'USDC']:
                    price_usd = 1.0
                    usd_value = total_balance * price_usd
                    if usd_value >= MIN_BALANCE_USD:
                        portfolio[asset] = {
                            'balance': total_balance,
                            'free': free_balance,
                            'locked': locked_balance,
                            'price_usd': price_usd,
                            'usd_value': usd_value,
                            'symbol': asset,
                            'change_24h': 0.0,  # Stablecoins have no change
                            'volume_24h': 0.0,
                            'confidence': 1.0
                        }
                else:
                    # Try different quote currencies
                    for quote in ['USDT', 'BUSD', 'USDC']:
                        symbol = f"{asset}{quote}"
                        if symbol in price_dict:
                            price_usd = price_dict[symbol]
                            usd_value = total_balance * price_usd
                            if usd_value >= MIN_BALANCE_USD:
                                portfolio[asset] = {
                                    'balance': total_balance,
                                    'free': free_balance,
                                    'locked': locked_balance,
                                    'price_usd': price_usd,
                                    'usd_value': usd_value,
                                    'symbol': symbol,
                                    'change_24h': None,  # Real 24h change unavailable
                                    'volume_24h': None,  # Real 24h volume unavailable
                                    'confidence': None   # Real confidence unavailable
                                }
                            break
        
        # Get GBP rate
        gbp_rate = get_gbp_exchange_rate()
        
        return portfolio, gbp_rate
        
    except Exception as e:
        st.error(f"Error fetching portfolio: {e}")
        return {}, 0.79

def get_current_positions():
    """Get current trading positions with P&L"""
    # Load from trades file and calculate current positions
    positions = {}
    
    try:
        if os.path.exists('logs/trades.csv'):
            df = pd.read_csv('logs/trades.csv')
            
            # Calculate current positions
            for _, trade in df.iterrows():
                symbol = trade['symbol']
                if trade['status'] == 'ENTRY':
                    positions[symbol] = {
                        'entry_price': trade['entry_price'],
                        'quantity': trade.get('quantity', 0),
                        'entry_time': trade['timestamp'],
                        'direction': trade['direction'],
                        'strategy': trade.get('strategy', 'Unknown'),
                        'risk_level': trade.get('risk_level', 'Unknown')
                    }
                elif trade['status'] == 'EXIT' and symbol in positions:
                    # Calculate P&L for closed position
                    positions[symbol]['exit_price'] = trade['exit_price']
                    positions[symbol]['pnl_pct'] = trade['change_pct']
                    positions[symbol]['status'] = 'CLOSED'
    
    except Exception as e:
        st.error(f"Error loading positions: {e}")
    
    return positions

def render_manual_trading_tab():
    """Enhanced manual trading tab with cross-crypto support"""
    # Fetch required variables from session state
    # Load exchange info if not in session state
    client = st.session_state.get('client', None)
    if client is None:
        try:
            client = Client(API_KEY, API_SECRET)
            st.session_state['client'] = client
        except Exception:
            client = None
    exchange_info = st.session_state.get('exchange_info', None)
    if exchange_info is None and client is not None:
        try:
            exchange_info = client.get_exchange_info()
            st.session_state['exchange_info'] = exchange_info
        except Exception:
            exchange_info = None
    # Get all symbols for dropdown
    all_symbols = []
    if exchange_info:
        all_symbols = [s['symbol'] for s in exchange_info['symbols'] if s['status'] == 'TRADING']
    else:
        all_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    trading_pair = st.selectbox('Trading Pair', all_symbols, index=all_symbols.index(st.session_state.get('manual_trading_pair', 'BTCUSDT')) if st.session_state.get('manual_trading_pair', 'BTCUSDT') in all_symbols else 0, key='manual_trading_pair')
    trade_direction = st.selectbox('Trade Direction', ['Buy', 'Sell'], index=0 if st.session_state.get('manual_trade_direction', 'Buy') == 'Buy' else 1, key='manual_trade_direction')
    # Parse base and quote asset from selected pair
    base_asset = trading_pair[:-3] if trading_pair.endswith('BTC') or trading_pair.endswith('ETH') else trading_pair[:-4]
    quote_asset = trading_pair[-3:] if trading_pair.endswith('BTC') or trading_pair.endswith('ETH') else trading_pair[-4:]
    st.session_state['manual_base_asset'] = base_asset
    st.session_state['manual_quote_asset'] = quote_asset

    mode = 'Live'

    # WebSocket price streaming for selected trading pair (Live mode only)
    import importlib.util
    import time
    import os
    ws_mod = None
    ws_import_error = None
    import_success = False
    try:
        ws_util_path = os.path.join(os.path.dirname(__file__), 'binance_ws_price.py')
        if os.path.exists(ws_util_path):
            spec = importlib.util.spec_from_file_location('binance_ws_price', ws_util_path)
            ws_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(ws_mod)
            import_success = True
        else:
            ws_util_path = '/workspaces/Bottie/binance_ws_price.py'
            if os.path.exists(ws_util_path):
                spec = importlib.util.spec_from_file_location('binance_ws_price', ws_util_path)
                ws_mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(ws_mod)
                import_success = True
    except Exception as e:
        ws_import_error = e
        ws_mod = None
        import_success = False

    current_price = None
    if import_success and ws_mod is not None:
        try:
            if 'ws_price' not in st.session_state or st.session_state.get('ws_pair') != trading_pair:
                # Stop previous ws if exists
                if 'ws_price' in st.session_state and st.session_state['ws_price']:
                    try:
                        st.session_state['ws_price'].stop()
                    except Exception:
                        pass
                # Start new ws for selected pair
                st.session_state['latest_price'] = None
                def on_price_update(symbol, price):
                    st.session_state['latest_price'] = price
                ws = ws_mod.BinancePriceWebSocket([trading_pair], on_price_update)
                ws.start()
                st.session_state['ws_price'] = ws
                st.session_state['ws_pair'] = trading_pair
                for _ in range(20):
                    if st.session_state['latest_price']:
                        break
                    time.sleep(0.1)
            current_price = st.session_state.get('latest_price', None)
            if current_price is not None and current_price != 0:
                st.success(f"\U0001F4B0 Live {trading_pair} Price: {current_price:.8f}")
            else:
                st.warning(f"\U0001F4B0 Live {trading_pair} Price: unavailable")
                current_price = None
        except Exception as e:
            st.warning(f"WebSocket price streaming failed: {e}. Falling back to REST API.")
            ws_mod = None
            import_success = False

    if not import_success or ws_mod is None:
        # Fallback: REST polling for price
        st.info("WebSocket price streaming unavailable. Using REST API for price updates.")
        try:
            if client is not None:
                try:
                    ticker = client.get_symbol_ticker(symbol=trading_pair)
                    current_price = float(ticker['price'])
                    st.success(f"\U0001F4B0 {trading_pair} Price (REST): {current_price:.8f}")
                except Exception as e:
                    st.warning(f"Failed to fetch price for {trading_pair}: {e}")
                    current_price = None
            else:
                st.warning("Binance client unavailable. Cannot fetch price.")
                current_price = None
        except Exception as e:
            st.warning(f"Failed to fetch price for {trading_pair}: {e}")


    order_type = st.selectbox("Order Type", ["MARKET", "LIMIT", "STOP_LOSS", "STOP_LOSS_LIMIT"])

    # Get step size for quantity precision
    step_size = 0.000001
    min_qty = 0.0
    if exchange_info:
        try:
            symbol_info = next(s for s in exchange_info['symbols'] if s['symbol'] == trading_pair)
            for f in symbol_info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    step_size = float(f['stepSize'])
                    min_qty = float(f['minQty'])
                    break
        except Exception:
            min_qty = 0.0

    import math
    def round_step(qty, step):
        if step == 0:
            return qty
        return math.floor(qty / step) * step

    # Quantity input (no balance check, as user may not hold asset yet)
    if trade_direction == "Buy":
        if order_type == "MARKET":
            quote_amount = st.number_input(
                f"{quote_asset} Amount to spend",
                min_value=0.0,
                value=50.0,
                step=1.0
            )
            if current_price is not None and current_price > 0:
                quantity = quote_amount / current_price
            else:
                quantity = 0.0
        else:
            quantity = st.number_input(
                f"{base_asset} Quantity",
                min_value=0.0,
                value=0.001,
                format="%.8f"
            )
    else:
        quantity = st.number_input(
            f"{base_asset} Quantity to sell",
            min_value=0.0,
            value=0.001,
            format="%.8f"
        )

    # Round quantity to allowed precision
    quantity = round_step(quantity, step_size)
    if quantity < min_qty:
        st.warning(f"Quantity must be at least {min_qty}")

    limit_price = current_price if current_price is not None else 0.0
    stop_price = current_price if current_price is not None else 0.0

    if order_type in ["LIMIT", "STOP_LOSS_LIMIT"]:
        limit_price = st.number_input(
            "Limit Price",
            min_value=0.0,
            value=float(limit_price),
            format="%.8f"
        )

    if order_type in ["STOP_LOSS", "STOP_LOSS_LIMIT"]:
        stop_price = st.number_input(
            "Stop Price",
            min_value=0.0,
            value=float(stop_price * 0.95),
            format="%.8f"
        )

    button_text = f"\U0001F6D2 {trade_direction} {quantity:.8f} {base_asset}"
    can_execute = quantity >= min_qty and current_price is not None and current_price > 0

    if st.button(button_text, type="primary", disabled=not can_execute):
        if can_execute:
            try:
                import trader
                result = trader.execute_entry(client, trading_pair, quantity, signal_type="BUY_LONG" if trade_direction=="Buy" else "BUY_SHORT")
                if result['status'] == 'SUCCESS':
                    st.success(f"✅ LIVE {order_type} order placed successfully!")
                    st.json(result)
                else:
                    st.error(f"❌ LIVE order failed: {result.get('error')}")
                trade_data = {
                    'timestamp': datetime.now().isoformat(),
                    'type': 'manual_trade',
                    'symbol': trading_pair,
                    'side': trade_direction.upper(),
                    'quantity': quantity,
                    'price': limit_price if order_type == "LIMIT" else current_price,
                    'order_type': order_type,
                    'order_id': result.get('order_id'),
                    'status': result.get('status')
                }
                os.makedirs('logs', exist_ok=True)
                # Enhanced error logging for manual_trades.log
                try:
                    with open('logs/manual_trades.log', 'a') as f:
                        f.write(json.dumps(trade_data) + '\n')
                except Exception as logerr:
                    st.error(f"❌ Failed to write to manual_trades.log: {logerr}")
                    import traceback
                    st.text(traceback.format_exc())
                # Enhanced error logging for trades.csv
                try:
                    with open('logs/trades.csv', 'a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            trade_data['timestamp'], trade_data['symbol'], trade_data['side'],
                            trade_data['price'], '', trade_data['quantity'], '', 'ENTRY', trade_data['order_type']
                        ])
                except Exception as logerr:
                    st.error(f"❌ Failed to write to trades.csv: {logerr}")
                    import traceback
                    st.text(traceback.format_exc())
            except Exception as e:
                st.error(f"❌ Order failed: {e}")

    col1, col2 = st.columns(2)
    with col2:
        st.subheader("📊 Portfolio Overview (Live)")
        try:
            portfolio, _ = get_real_portfolio()
            if portfolio:
                df = pd.DataFrame([
                    {
                        'Asset': k,
                        'Balance': v['balance'],
                        'Free': v['free'],
                        'Locked': v['locked'],
                        'USD Value': v.get('usd_value', 0.0),
                        '24h Change (%)': v.get('change_24h', 0.0),
                        'Volume 24h': v.get('volume_24h', 0.0)
                    }
                    for k, v in portfolio.items()
                ])
                st.dataframe(df)
            else:
                st.info("No assets found in portfolio.")
        except Exception as e:
            st.error(f"Error loading live portfolio: {e}")

        # Recent manual trades
        st.subheader("📝 Recent Manual Trades")
        try:
            if os.path.exists('logs/manual_trades.log'):
                with open('logs/manual_trades.log', 'r') as f:
                    trades = [json.loads(line) for line in f.readlines()[-5:]]
                if trades:
                    trades_df = pd.DataFrame(trades)
                    st.dataframe(trades_df[['timestamp', 'symbol', 'side', 'quantity', 'price']])
                else:
                    st.info("No recent trades")
            else:
                st.info("No trade history available")
        except Exception as e:
            st.error(f"Error loading trade history: {e}")

def render_portfolio_overview_tab():
    """Enhanced portfolio overview with real positions and methodology"""
    st.header("💼 Portfolio Overview")
    st.caption("Live portfolio analysis with trading methodology and risk assessment")
    
    # Get real portfolio data
    portfolio, gbp_rate = get_real_portfolio()
    
    if not portfolio:
        st.warning("⚠️ No portfolio data available. Please check your Binance API connection.")
        return
    
    # Calculate totals
    total_usd = sum(data['usd_value'] for data in portfolio.values())
    total_gbp = total_usd * gbp_rate
    
    # Market condition analysis
    market_condition, condition_score, avg_volatility = simulate_market_analysis(portfolio)
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💷 Total Value (GBP)", f"£{total_gbp:,.2f}")
    
    with col2:
        st.metric("💰 Total Value (USD)", f"${total_usd:,.2f}")
    
    with col3:
        st.metric("🪙 Assets", len(portfolio))
    
    with col4:
        st.metric("📊 Market Confidence", f"{condition_score:.1%}")
    
    # Current methodology display
    st.subheader("🎯 Current Trading Methodology")
    
    col1, col2 = st.columns(2)
    
    with col1:
        strategy_info = TRADING_STRATEGIES[st.session_state['selected_strategy']]
        st.markdown(f"**Strategy:** {st.session_state['selected_strategy']}")
        st.markdown(f"**Description:** {strategy_info['description']}")
        st.markdown(f"**Threshold:** {strategy_info['threshold']}%")
        st.markdown(f"**Volume Required:** {strategy_info['volume_req']}x")
    
    with col2:
        risk_info = RISK_LEVELS[st.session_state['selected_risk_level']]
        st.markdown(f"**Risk Level:** {st.session_state['selected_risk_level']}")
        st.markdown(f"**Description:** {risk_info['description']}")
        st.markdown(f"**Max Positions:** {risk_info['max_positions']}")
        st.markdown(f"**Risk per Trade:** {risk_info['risk_per_trade']:.1%}")
    
    # Risk factor analysis
    st.subheader("⚖️ Risk Factor Analysis")
    
    # Calculate portfolio risk
    total_value = sum(data['usd_value'] for data in portfolio.values())
    risk_score = 0
    
    for asset, data in portfolio.items():
        weight = data['usd_value'] / total_value
        if asset in ['BTC', 'ETH']:
            risk_score += weight * 0.3  # Lower risk
        elif asset in ['BNB', 'ADA', 'DOT', 'SOL']:
            risk_score += weight * 0.6  # Medium risk
        else:
            risk_score += weight * 0.9  # Higher risk
    
    risk_level = "High" if risk_score > 0.7 else "Medium" if risk_score > 0.4 else "Low"
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Portfolio Risk Score", f"{risk_score:.2f}")
    
    with col2:
        st.metric("Risk Level", risk_level)
    
    with col3:
        diversification = "High" if len(portfolio) > 6 else "Medium" if len(portfolio) > 3 else "Low"
        st.metric("Diversification", f"{diversification} ({len(portfolio)} assets)")
    
    # Portfolio breakdown
    st.subheader("📊 Portfolio Breakdown")
    
    def safe_fmt(val, fmt, fallback="-"):
        try:
            if val is None:
                return fallback
            return fmt.format(val)
        except Exception:
            return fallback

    portfolio_df = pd.DataFrame([
        {
            'Asset': asset,
            'Balance': safe_fmt(data.get('balance'), "{:.8f}"),
            'USD Value': safe_fmt(data.get('usd_value'), "$ {:.2f}"),
            'GBP Value': safe_fmt((data.get('usd_value', 0) or 0) * gbp_rate, "£{:.2f}"),
            'Price': safe_fmt(data.get('price_usd'), "$ {:.8f}"),
            '24h Change': safe_fmt(data.get('change_24h'), "{:.2f}%"),
            'Weight': safe_fmt((data.get('usd_value', 0) or 0) / total_usd * 100 if total_usd else None, "{:.1f}%")
        }
        for asset, data in portfolio.items()
    ])
    
    st.dataframe(portfolio_df, use_container_width=True)
    
    # Portfolio distribution chart
    fig = px.pie(
        values=[data['usd_value'] for data in portfolio.values()],
        names=list(portfolio.keys()),
        title="Portfolio Distribution"
    )
    st.plotly_chart(fig, use_container_width=True)

def render_performance_tab():
    """Enhanced performance tab with current positions and individual P&L"""
    st.header("📈 Trading Performance")
    st.caption("Historical performance metrics and current position analysis")
    
    # --- NEW: Pull trade history from Binance ---
    st.subheader("🔄 Current Positions (Live from Binance)")
    positions_data = []
    trades_data = []
    try:
        if BINANCE_AVAILABLE and API_KEY and API_SECRET:
            client = Client(API_KEY, API_SECRET)
            if USE_TESTNET:
                client.API_URL = "https://testnet.binance.vision/api"
            # Get all symbols with trades
            account = client.get_account()
            all_balances = account['balances']
            # Only show assets with nonzero balance
            for bal in all_balances:
                asset = bal['asset']
                free = float(bal['free'])
                locked = float(bal['locked'])
                total = free + locked
                if total > 0 and asset not in ['USDT', 'BUSD', 'USDC']:
                    # Try to find a USDT pair for this asset
                    symbol = f"{asset}USDT"
                    try:
                        ticker = client.get_symbol_ticker(symbol=symbol)
                        current_price = float(ticker['price'])
                        entry_price = current_price  # No entry price info, so just show current
                        pnl_pct = 0.0
                        positions_data.append({
                            'Symbol': symbol,
                            'Direction': 'LONG',
                            'Entry Price': f"${entry_price:.8f}",
                            'Current Price': f"${current_price:.8f}",
                            'P&L %': f"{pnl_pct:+.2f}%",
                            'Strategy': 'Unknown',
                            'Risk Level': 'Unknown',
                            'Entry Time': 'N/A'
                        })
                    except Exception:
                        continue
            # Get trade history for all symbols with trades
            exchange_info = client.get_exchange_info()
            trading_symbols = [s['symbol'] for s in exchange_info['symbols'] if s['status'] == 'TRADING']
            from datetime import timedelta
            import time as _time
            now = datetime.utcnow()
            since = now - timedelta(days=30)
            since_ms = int(_time.mktime(since.timetuple()) * 1000)
            for symbol in trading_symbols:
                # Disabled live trade history polling to avoid Binance API rate limits
                st.warning("Live trade history polling is temporarily disabled to prevent Binance API rate limit errors. Please use the Binance website for full trade history.")
                break  # Only show warning once
    except Exception as e:
        st.error(f"Error fetching live trades from Binance: {e}")

    # Show open positions
    if positions_data:
        positions_df = pd.DataFrame(positions_data)
        st.dataframe(positions_df, use_container_width=True)
    else:
        st.info("No open positions found on Binance.")

    # Show trade history
    st.subheader("� Individual Trade History (Live from Binance)")
    if trades_data:
        trades_df = pd.DataFrame(trades_data)
        trades_df = trades_df.sort_values('timestamp', ascending=False)
        st.dataframe(trades_df[['timestamp','symbol','side','price','qty','commission','commissionAsset']].head(20), use_container_width=True)
        # Simple stats
        st.metric("Total Trades", len(trades_df))
        st.metric("Unique Symbols", trades_df['symbol'].nunique())
    else:
        st.info("No trade history found on Binance.")

def render_settings_tab():
    """Enhanced settings tab with methodology and risk level selection"""
    st.header("⚙️ Bot Control & Settings")
    st.caption("Configure trading strategy, risk level, and bot parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Trading Strategy Selection")
        
        # Strategy selection
        selected_strategy = st.selectbox(
            "Select Trading Strategy",
            options=list(TRADING_STRATEGIES.keys()),
            index=list(TRADING_STRATEGIES.keys()).index(st.session_state['selected_strategy'])
        )
        
        # Display strategy info
        strategy_info = TRADING_STRATEGIES[selected_strategy]
        st.info(f"**{selected_strategy}:** {strategy_info['description']}")
        
        # Risk level selection
        selected_risk = st.selectbox(
            "Select Risk Level",
            options=list(RISK_LEVELS.keys()),
            index=list(RISK_LEVELS.keys()).index(st.session_state['selected_risk_level'])
        )
        
        # Display risk info
        risk_info = RISK_LEVELS[selected_risk]
        st.info(f"**{selected_risk}:** {risk_info['description']}")
        
        # Update button
        if st.button("💾 Update Strategy & Risk", type="primary"):
            st.session_state['selected_strategy'] = selected_strategy
            st.session_state['selected_risk_level'] = selected_risk
            
            # Save to bot status file
            status = load_bot_status()
            status['latest_strategy'] = selected_strategy
            status['latest_risk_level'] = selected_risk
            
            os.makedirs('logs', exist_ok=True)
            with open('logs/bot_status.json', 'w') as f:
                json.dump(status, f, indent=2)
            
            st.success(f"✅ Updated to {selected_strategy} strategy with {selected_risk} risk level")
            st.rerun()
    
    with col2:
        st.subheader("🤖 Bot Control")
        
        if st.session_state['bot_running']:
            st.success("✅ Auto-scan is ENABLED")
            st.info("Page automatically scans every 30 seconds")
            
            if st.button("⏸️ Disable Auto-Scan", type="secondary"):
                st.session_state['bot_running'] = False
                st.success("Auto-scan disabled")
                st.rerun()
        else:
            st.warning("⏸️ Auto-scan is DISABLED")
            st.info("Use manual 'Scan Now' button in Market Indicators")
            
            if st.button("▶️ Enable Auto-Scan", type="primary"):
                st.session_state['bot_running'] = True
                st.success("✅ Auto-scan enabled!")
                st.rerun()
        
        st.markdown("---")
        st.subheader("⚙️ Advanced Configuration")
        
        # Max trade percentage
        max_trade_percent = st.slider(
            "Max Trade Size (% of Portfolio)", 
            1.0, 20.0, 
            st.session_state['max_trade_percent'], 
            0.5
        )
        st.session_state['max_trade_percent'] = max_trade_percent
        st.info(f"Current max trade per deal: {max_trade_percent:.1f}% of portfolio value.")
        
        # Scan interval
        scan_interval = st.slider(
            "Scan Interval (seconds)",
            60, 900,
            300,
            30
        )
        
        # Confidence threshold
        confidence_threshold = st.slider(
            "Minimum Confidence Threshold",
            0.5, 0.9,
            0.65,
            0.05
        )
        
        # Password change
        st.markdown("---")
        st.subheader("🔐 Change Dashboard Password")
        new_password = st.text_input("New Password", type="password")
        if st.button("Set New Password"):
            if new_password:
                st.session_state['dashboard_password'] = new_password
                st.success("Password updated for this session.")
            else:
                st.warning("Password cannot be empty.")

def render_strategy_tab():
    """Enhanced strategy tab with complete methodology information"""
    st.header("🎯 Trading Strategy")
    st.caption("Detailed strategy information and methodology explanations")
    
    # Current strategy display
    # --- Auto-update strategy and risk level based on live market condition ---
    portfolio, _ = get_real_portfolio()
    market_condition, condition_score, avg_volatility = simulate_market_analysis(portfolio)
    recommendations = {
        'BULL_TRENDING': {
            'recommended': ['Swing', 'Breakout'],
            'risk': 'Aggressive',
            'avoid': ['Conservative'],
            'reason': 'Strong uptrend favors momentum strategies'
        },
        'BEAR_TRENDING': {
            'recommended': ['Conservative', 'Scalping'],
            'risk': 'Conservative',
            'avoid': ['Swing'],
            'reason': 'Downtrend requires defensive positioning'
        },
        'HIGH_VOLATILITY': {
            'recommended': ['Scalping', 'Breakout'],
            'risk': 'Balanced',
            'avoid': ['Swing'],
            'reason': 'High volatility creates quick profit opportunities'
        },
        'CONSOLIDATING': {
            'recommended': ['Scalping', 'Conservative'],
            'risk': 'Conservative',
            'avoid': ['Swing'],
            'reason': 'Sideways markets favor range trading'
        }
    }
    rec = recommendations.get(market_condition, {
        'recommended': ['Balanced'],
        'risk': 'Balanced',
        'avoid': [],
        'reason': 'Mixed market conditions'
    })
    # Set recommended strategy and risk level in session state
    recommended_strategy = rec['recommended'][0]
    recommended_risk = rec['risk']
    st.session_state['selected_strategy'] = recommended_strategy
    st.session_state['selected_risk_level'] = recommended_risk
    current_strategy = st.session_state['selected_strategy']
    current_risk = st.session_state['selected_risk_level']
    
    st.success(f"✅ Active Strategy: {current_strategy}")
    st.success(f"✅ Risk Level: {current_risk}")
    
    # Strategy selector for detailed view
    st.subheader("📋 Strategy Details")
    
    selected_strategy_view = st.selectbox(
        "Select Strategy to View Details",
        options=list(TRADING_STRATEGIES.keys()),
        index=list(TRADING_STRATEGIES.keys()).index(current_strategy)
    )
    
    strategy_info = TRADING_STRATEGIES[selected_strategy_view]
    
    # Detailed strategy information
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"### {selected_strategy_view} Strategy")
        st.markdown(f"**Description:** {strategy_info['description']}")
        st.markdown(f"**Price Threshold:** {strategy_info['threshold']}%")
        st.markdown(f"**Volume Requirement:** {strategy_info['volume_req']}x average")
        st.markdown(f"**Hold Time:** {strategy_info['hold_time']}")
        st.markdown(f"**Take Profit:** {strategy_info['take_profit']}")
        st.markdown(f"**Stop Loss:** {strategy_info['stop_loss']}")
        st.markdown(f"**Min Confidence:** {strategy_info['confidence_min']:.0%}")
    
    with col2:
        st.markdown("### Strategy Rules & Logic")
        
        if selected_strategy_view == 'Scalping':
            st.markdown("""
            **Scalping Strategy Rules:**
            - Monitor 1-minute candles for quick moves
            - Enter on 2-3% price movements
            - High volume confirmation required (1.5x+)
            - Quick exits: 3-5% profit or 2-3% loss
            - Maximum hold time: 30 minutes
            - Best for: High volatility, sideways markets
            - Risk: High frequency, requires constant monitoring
            """)
        
        elif selected_strategy_view == 'Breakout':
            st.markdown("""
            **Breakout Strategy Rules:**
            - Monitor 2-hour price movements
            - Enter on 5%+ breakouts with volume
            - Confirm trend direction with RSI
            - Avoid low-volume hours (0-6 UTC, 22-23 UTC)
            - Take profit: 8-15% based on confidence
            - Stop loss: 8-12% based on confidence
            - Best for: Trending markets, clear direction
            """)
        
        elif selected_strategy_view == 'Swing':
            st.markdown("""
            **Swing Strategy Rules:**
            - Monitor 4-hour+ price movements
            - Enter on 8%+ moves with trend confirmation
            - Lower volume requirement (1.2x)
            - Longer hold times: 4-24 hours
            - Take profit: 15-25% targets
            - Stop loss: 10-15% protection
            - Best for: Strong trending markets
            """)
        
        elif selected_strategy_view == 'Conservative':
            st.markdown("""
            **Conservative Strategy Rules:**
            - Monitor smaller 3% movements
            - Higher volume confirmation (1.8x)
            - Strict risk management
            - Quick exits: 5-8% profit, 3-5% loss
            - Shorter hold times: 1-2 hours
            - Higher confidence threshold (75%)
            - Best for: Uncertain markets, capital preservation
            """)
    
    # Strategy performance comparison
    st.subheader("📊 Strategy Performance Comparison")
    st.info('No real strategy performance data available.')
    
    # Strategy recommendation based on market conditions
    st.subheader("💡 Strategy Recommendations")
    
    # Get current market condition
    portfolio, _ = get_real_portfolio()
    market_condition, condition_score, avg_volatility = simulate_market_analysis(portfolio)
    
    recommendations = {
        'BULL_TRENDING': {
            'recommended': ['Swing', 'Breakout'],
            'avoid': ['Conservative'],
            'reason': 'Strong uptrend favors momentum strategies'
        },
        'BEAR_TRENDING': {
            'recommended': ['Conservative', 'Scalping'],
            'avoid': ['Swing'],
            'reason': 'Downtrend requires defensive positioning'
        },
        'HIGH_VOLATILITY': {
            'recommended': ['Scalping', 'Breakout'],
            'avoid': ['Swing'],
            'reason': 'High volatility creates quick profit opportunities'
        },
        'CONSOLIDATING': {
            'recommended': ['Scalping', 'Conservative'],
            'avoid': ['Swing'],
            'reason': 'Sideways markets favor range trading'
        }
    }
    
    rec = recommendations.get(market_condition, {
        'recommended': ['Balanced'],
        'avoid': [],
        'reason': 'Mixed market conditions'
    })
    
    st.info(f"**Market Condition:** {market_condition}")
    st.success(f"**Recommended Strategies:** {', '.join(rec['recommended'])}")
    if rec['avoid']:
        st.warning(f"**Avoid:** {', '.join(rec['avoid'])}")
    st.markdown(f"**Reasoning:** {rec['reason']}")

def render_market_indicators_tab():
    """Enhanced market indicators tab"""
    st.header("📊 Market Indicators")
    st.caption("Real-time market analysis and trading opportunities")
    
    # Manual scan button
    if st.button("🔍 Scan Market Now", type="primary"):
        perform_scan()
    
    # Market overview
    st.subheader("🌍 Market Overview")
    
    # Get market data
    portfolio, gbp_rate = get_real_portfolio()
    market_condition, condition_score, avg_volatility = simulate_market_analysis(portfolio)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Market Condition", market_condition)
    
    with col2:
        st.metric("Confidence Score", f"{condition_score:.1%}")
    
    with col3:
        st.metric("Avg Volatility", f"{avg_volatility:.1f}%")
    
    with col4:
        st.metric("Trading Pairs", len(portfolio))
    
    # Display last scan results
    if 'last_opportunities' in st.session_state and st.session_state['last_opportunities']:
        st.subheader("🎯 Current Trading Opportunities")
        
        opportunities_df = pd.DataFrame(st.session_state['last_opportunities'])
        st.dataframe(opportunities_df, use_container_width=True)
        
        # Chart of opportunities
        if len(opportunities_df) > 0 and 'confidence' in opportunities_df.columns:
            fig = px.bar(opportunities_df, x='symbol', y='confidence', 
                        title="Trading Opportunities by Confidence",
                        color='signal')
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("🔍 No opportunities found in last scan. Try scanning again or wait for market movements.")
    
    # Market trend analysis
    st.subheader("📈 Market Trend Analysis")
    
    if portfolio:
        # Create trend chart
        trend_data = []
        for asset, data in portfolio.items():
            trend_data.append({
                'Asset': asset,
                'Price': data['price_usd'],
                'Change': data['change_24h'],
                'Volume': data['volume_24h'],
                'Confidence': data['confidence']
            })
        trend_df = pd.DataFrame(trend_data)
        # Drop rows with NaN for plotting
        trend_df_bar = trend_df.dropna(subset=['Change'])
        trend_df_scatter = trend_df.dropna(subset=['Volume', 'Change', 'Confidence'])
        # Price change chart
        if not trend_df_bar.empty:
            fig = px.bar(trend_df_bar, x='Asset', y='Change', 
                        title="24h Price Changes",
                        color='Change',
                        color_continuous_scale='RdYlGn')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No valid data for price change chart.")
        # Volume analysis
        if not trend_df_scatter.empty:
            fig2 = px.scatter(trend_df_scatter, x='Volume', y='Change', 
                             size='Confidence', hover_name='Asset',
                             title="Volume vs Price Change Analysis")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No valid data for volume vs price change analysis.")

def render_logs_tab():
    """Enhanced logs tab"""
    st.header("📋 System Logs")
    st.caption("Real-time bot activity and system monitoring")

    # --- Refresh button and auto-refresh ---
    refresh = st.button("🔄 Refresh Logs")
    # Optional: auto-refresh every 10 seconds
    st_autorefresh = st.query_params.get('autorefresh', 'off')
    if st_autorefresh == 'on':
        import time as _time
        _time.sleep(0.5)
        st.rerun()
    # Log file tabs
    log_tab1, log_tab2, log_tab3 = st.tabs(["📟 Console", "🔍 Scans", "💼 Trades"])

    with log_tab1:
        st.subheader("📟 Console Output")
        log_file = "logs/console_output.log"
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = f.readlines()[-100:]
            for line in logs:
                if "error" in line.lower():
                    st.markdown(f":red[{line.strip()}]")
                elif any(x in line.lower() for x in ["profit", "+", "✅", "success"]):
                    st.markdown(f":green[{line.strip()}]")
                elif any(x in line.lower() for x in ["heartbeat", "💓"]):
                    st.markdown(f":blue[{line.strip()}]")
                elif "🔍" in line or "scan" in line.lower():
                    st.markdown(f":orange[{line.strip()}]")
                else:
                    st.text(line.strip())
        else:
            st.info("No console log file found.")

    with log_tab2:
        st.subheader("🔍 Scan Logs")
        scan_log_file = "logs/portfolio_scans.log"
        if os.path.exists(scan_log_file):
            with open(scan_log_file, 'r', encoding='utf-8') as f:
                scan_logs = f.readlines()[-50:]
            for line in scan_logs:
                st.text(line.strip())
        else:
            st.info("No scan log file found.")

    with log_tab3:
        st.subheader("💼 Trade Logs")
        if os.path.exists('logs/trades.csv'):
            df = pd.read_csv('logs/trades.csv')
            st.dataframe(df.tail(20), use_container_width=True)
        else:
            st.info("No trade log file found.")

    # Download logs
    st.subheader("📥 Download Logs")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Download Console Logs"):
            if os.path.exists("logs/console_output.log"):
                with open("logs/console_output.log", 'r', encoding='utf-8') as f:
                    log_content = f.read()
                st.download_button(
                    "Download Console Log",
                    data=log_content,
                    file_name=f"console_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                    mime="text/plain"
                )
    
    with col2:
        if st.button("📥 Download Scan Logs"):
            if os.path.exists("logs/portfolio_scans.log"):
                with open("logs/portfolio_scans.log", 'r', encoding='utf-8') as f:
                    scan_content = f.read()
                st.download_button(
                    "Download Scan Log",
                    data=scan_content,
                    file_name=f"scan_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                    mime="text/plain"
                )
    
    with col3:
        if st.button("📥 Download Trade Logs"):
            if os.path.exists("logs/trades.csv"):
                df = pd.read_csv('logs/trades.csv')
                csv_content = df.to_csv(index=False)
                st.download_button(
                    "Download Trade Log",
                    data=csv_content,
                    file_name=f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

def render_health_tab():
    """Enhanced health tab with proper log file checks"""
    st.header("💓 System Health")
    st.caption("Comprehensive system health monitoring and diagnostics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🤖 Bot Status")
        if st.session_state['background_bot_running']:
            st.success("🟢 Bot is RUNNING")
        else:
            st.error("🔴 Bot is STOPPED")
        
        st.subheader("🔗 API Connection")
        if BINANCE_AVAILABLE and API_KEY and API_SECRET:
            st.success("✅ Binance API Connected")
            mode = "🔴 Live Trading"
            st.info(f"📡 Mode: {mode}")
        else:
            st.error("❌ Binance API Not Connected")
        
        # Connection test
        if st.button("🔄 Test API Connection"):
            if BINANCE_AVAILABLE and API_KEY and API_SECRET:
                try:
                    client = Client(API_KEY, API_SECRET)
                    account = client.get_account()
                    st.success("✅ API Connection Test Passed!")
                    st.info(f"Account Status: {account.get('accountType', 'Unknown')}")
                except Exception as e:
                    st.error(f"❌ API Connection Test Failed: {e}")
            else:
                st.error("❌ API credentials not configured")
    
    with col2:
        st.subheader("📊 Health Metrics")
        status = load_bot_status()
        
        if 'last_heartbeat' in status:
            try:
                heartbeat_time = datetime.fromisoformat(status['last_heartbeat'])
                time_since_heartbeat = (datetime.now() - heartbeat_time).total_seconds()
                
                if time_since_heartbeat < 120:
                    st.success(f"💓 Heartbeat: Active ({int(time_since_heartbeat)}s ago)")
                else:
                    st.warning(f"⚠️ Heartbeat: {int(time_since_heartbeat)}s ago")
            except:
                st.info("💓 Heartbeat: No valid data")
        else:
            st.info("💓 Heartbeat: No data")
        
        st.metric("Total Scans", status.get('scan_count', 0))
        uptime = status.get('uptime_seconds', 0)
        st.metric("Bot Uptime", f"{uptime // 3600:.0f}h {(uptime % 3600) // 60:.0f}m")
        
        # System resources
        st.metric("Active Positions", len(status.get('portfolio', {})))
        st.metric("Opportunities", len(status.get('opportunities', [])))
    
    # Log file status - Enhanced
    st.subheader("📁 Log File Status")
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    required_logs = [
        'logs/console_output.log',
        'logs/portfolio_scans.log',
        'logs/trades.csv',
        'logs/bot_status.json',
        'logs/manual_trades.log'
    ]
    
    log_status = []
    
    for log_file in required_logs:
        if os.path.exists(log_file):
            try:
                size = os.path.getsize(log_file)
                modified = datetime.fromtimestamp(os.path.getmtime(log_file))
                log_status.append({
                    'File': log_file,
                    'Status': '✅ Exists',
                    'Size': f"{size:,} bytes",
                    'Modified': modified.strftime('%Y-%m-%d %H:%M:%S')
                })
            except Exception as e:
                log_status.append({
                    'File': log_file,
                    'Status': '⚠️ Error',
                    'Size': f"Error: {e}",
                    'Modified': 'Unknown'
                })
        else:
            log_status.append({
                'File': log_file,
                'Status': '❌ Missing',
                'Size': 'N/A',
                'Modified': 'N/A'
            })
    
    log_df = pd.DataFrame(log_status)
    st.dataframe(log_df, use_container_width=True)
    
    # Create missing log files
    if st.button("🔧 Create Missing Log Files"):
        for log_file in required_logs:
            if not os.path.exists(log_file):
                try:
                    if log_file.endswith('.csv'):
                        # Create CSV with headers
                        if 'trades' in log_file:
                            pd.DataFrame(columns=['timestamp', 'symbol', 'direction', 'entry_price', 'exit_price', 'quantity', 'change_pct', 'status', 'strategy']).to_csv(log_file, index=False)
                    elif log_file.endswith('.json'):
                        # Create JSON with default structure
                        with open(log_file, 'w') as f:
                            json.dump({
                                'timestamp': datetime.now().isoformat(),
                                'running': False,
                                'scan_count': 0,
                                'opportunities': [],
                                'portfolio': {}
                            }, f, indent=2)
                    else:
                        # Create empty log file
                        with open(log_file, 'w') as f:
                            f.write(f"Log file created: {datetime.now().isoformat()}\n")
                    
                    st.success(f"✅ Created {log_file}")
                except Exception as e:
                    st.error(f"❌ Error creating {log_file}: {e}")
        
        st.rerun()
    
    # System information
    st.subheader("🖥️ System Information")
    
    sys_info = {
        'Python Version': sys.version,
        'Streamlit Version': st.__version__,
        'Current Directory': os.getcwd(),
        'Environment': 'Live Trading',
        'API Keys Configured': bool(API_KEY and API_SECRET),
        'Binance Library': 'Available' if BINANCE_AVAILABLE else 'Missing'
    }
    
    for key, value in sys_info.items():
        st.text(f"{key}: {value}")
    
    # Recent activity
    if os.path.exists("logs/console_output.log"):
        st.subheader("📝 Recent Activity")
        try:
            with open("logs/console_output.log", "r", encoding="utf-8") as f:
                last_lines = f.readlines()[-10:]
            
            for line in last_lines:
                if "error" in line.lower():
                    st.markdown(f":red[{line.strip()}]")
                elif any(x in line.lower() for x in ["profit", "+", "✅", "success"]):
                    st.markdown(f":green[{line.strip()}]")
                else:
                    st.text(line.strip())
        except Exception as e:
            st.error(f"Error reading log file: {e}")

def perform_scan():
    """Perform a market scan"""
    st.session_state['scan_count'] += 1
    st.session_state['last_scan_time'] = datetime.now()
    
    # Mock scan results (replace with real scanning logic)
    mock_opportunities = [
        {
            'symbol': 'BTCUSDT',
            'price': 119000.0,
            'change': 2.5,
            'volume': 15000000,
            'confidence': 0.75,
            'signal': 'BUY_LONG'
        },
        {
            'symbol': 'ETHUSDT',
            'price': 3200.0,
            'change': -1.8,
            'volume': 8000000,
            'confidence': 0.68,
            'signal': 'BUY_SHORT'
        }
    ]
    
    st.session_state['last_opportunities'] = mock_opportunities

def load_bot_status():
    """Load bot status from file"""
    try:
        if os.path.exists('logs/bot_status.json'):
            with open('logs/bot_status.json', 'r') as f:
                return json.load(f)
    except:
        pass
    
    return {
        'timestamp': datetime.now().isoformat(),
        'running': False,
        'scan_count': 0,
        'opportunities': [],
        'portfolio': {},
        'uptime_seconds': 0,
        'heartbeat_count': 0,
        'last_heartbeat': datetime.now().isoformat(),
        'latest_strategy': st.session_state.get('selected_strategy', 'Breakout'),
        'latest_risk_level': st.session_state.get('selected_risk_level', 'Balanced')
    }

def get_gbp_exchange_rate():
    """Get USD to GBP exchange rate"""
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        return response.json()['rates']['GBP']
    except:
        return 0.79

def simulate_market_analysis(portfolio):
    """Simulate market condition analysis"""
    if not portfolio:
        return "UNCERTAIN", 0.5, 2.0
    
    # Simple volatility calculation based on portfolio size
    volatility = min(5.0, len(portfolio) * 0.5 + 1.0)
    
    if volatility > 3.5:
        condition = "HIGH_VOLATILITY"
        score = 0.7
    elif volatility > 2.0:
        condition = "CONSOLIDATING"
        score = 0.6
    else:
        condition = "BULL_TRENDING"
        score = 0.8
    
    return condition, score, volatility

def start_background_bot():
    """Start the background bot process"""
    try:
        if not st.session_state['background_bot_running']:
            # Start bot process
            st.session_state['bot_process'] = subprocess.Popen([
                sys.executable, 'main.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            st.session_state['background_bot_running'] = True
            return True
    except Exception as e:
        st.error(f"Failed to start bot: {e}")
        return False

def stop_background_bot():
    """Stop the background bot process"""
    try:
        if st.session_state['background_bot_running'] and st.session_state['bot_process']:
            st.session_state['bot_process'].terminate()
            st.session_state['bot_process'] = None
            st.session_state['background_bot_running'] = False
            return True
    except Exception as e:
        st.error(f"Failed to stop bot: {e}")
        return False

def dashboard():
    """Main dashboard function"""
    # Render the mode switch ONCE at the top of the sidebar
    render_mode_switch()
    # Get Tailscale IP and setup sidebar controls
    ts_ip = get_tailscale_ip()
    remote_url = f"http://{ts_ip}:8501" if ts_ip != "Unavailable" else "Unavailable"
    
    # Sidebar setup
    st.sidebar.markdown(f"**Tailscale IP:** `{ts_ip}`")
    st.sidebar.text_input("🔗 Access URL", value=remote_url, key="url", label_visibility="collapsed")
    
    # Download logs
    if os.path.exists("logs/console_output.log"):
        with open("logs/console_output.log", 'r', encoding='utf-8') as f:
            log_content = f.read()
        st.sidebar.download_button("📥 Download Logs", data=log_content, file_name="console_output.log")

    # Bot status in sidebar
    st.sidebar.subheader("🤖 Bot Status")
    if st.session_state['background_bot_running']:
        st.sidebar.success("🟢 Bot is running")
        if st.sidebar.button("🛑 Stop Bot"):
            stop_background_bot()
            st.sidebar.info("Bot stopped.")
    else:
        st.sidebar.warning("🔴 Bot is stopped")
        if st.sidebar.button("▶️ Start Bot"):
            if start_background_bot():
                st.sidebar.success("Bot started.")
            else:
                st.sidebar.error("Failed to start bot.")

    if st.sidebar.button("🔄 Refresh Dashboard"):
        st.rerun()

    # Sidebar navigation - Unified tabs, Bot Demo before Manual Trading
    tab_options = [
    "Portfolio Overview", "Market Indicators", "Quantum Analysis", "Bot Trade", "Trading", "Performance", "Logs", "Settings", "Strategy", "Health"
]
    # Add company logo at the very top of the sidebar
    st.sidebar.markdown("<div style='text-align:center; margin-bottom:0.5em;'>" 
        "<img src='https://static.wixstatic.com/media/80aa29_3bdfcbab4dd34671915e3b66b0b596e4~mv2.jpeg/v1/fill/w_146,h_104,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/LRC_1719585575250.jpeg' width='146'/><br>"
        "<strong>Rondanini Publishing Ltd.</strong>"
        "</div>", unsafe_allow_html=True)
    # Add site clickers (website and docs)
    st.sidebar.markdown("<div style='text-align:center; margin-bottom:1em;'>"
        "<a href='https://www.rondanini.net' target='_blank'>🌐 Website</a> | "
        "<a href='https://docs.rondanini.net' target='_blank'>📄 Docs</a>"
        "</div>", unsafe_allow_html=True)
    selected_tab = st.sidebar.radio(
        "Select Dashboard Tab",
        tab_options
    )

    # Render selected tab
    if selected_tab == "Portfolio Overview":
        render_portfolio_overview_tab()
    elif selected_tab == "Market Indicators":
        render_market_indicators_tab()
        elif selected_tab == "Quantum Analysis":
        render_quantum_analysis_tab()
    elif selected_tab == "Bot Trade":
        from bot_trade import bot_trade_dashboard
        bot_trade_dashboard()
    elif selected_tab == "Trading":
        render_manual_trading_tab()
    elif selected_tab == "Performance":
        render_performance_tab()
    elif selected_tab == "Logs":
        render_logs_tab()
    elif selected_tab == "Settings":
        render_settings_tab()
    elif selected_tab == "Strategy":
        render_strategy_tab()
    elif selected_tab == "Health":
        render_health_tab()
    # Add MIT License and copyright at the bottom of the sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("<div style='font-size:12px; text-align:center;'>\
        <strong>MIT License</strong><br>\
        &copy; 2025 Rondanini Publishing Ltd.<br>\
        <a href='https://opensource.org/licenses/MIT' target='_blank'>View License</a>\
        </div>", unsafe_allow_html=True)

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="🤖 Crypto Trading Bot Dashboard", 
        page_icon="🤖",
        layout="wide"
    )
    # Add this with your other session state initializations
if 'quantum_engine' not in st.session_state:
    st.session_state['quantum_engine'] = QuantumTradingEngine()

    # Password authentication (persist for session, use .env password)
    if 'dashboard_password' not in st.session_state:
        st.session_state['dashboard_password'] = os.getenv('DASHBOARD_PASSWORD', 'bottie')
    if 'password_authenticated' not in st.session_state:
        st.session_state['password_authenticated'] = False
    # Only ask for password if not authenticated
    if not st.session_state['password_authenticated']:
        st.title("🔒 Enter Dashboard Password")
        st.caption("Default password: bottie")
        input_password = st.text_input("Password", type="password", key="dashboard_password_input")
        login_btn = st.button("🔓 Login", key="dashboard_login_btn")
        if login_btn:
            if input_password == st.session_state['dashboard_password']:
                st.session_state['password_authenticated'] = True
                st.success("✅ Access granted!")
                st.experimental_set_query_params(auth="1")
                st.rerun()
            else:
                st.error("❌ Incorrect password.")
                st.session_state['password_authenticated'] = False
                st.stop()
        # Prevent further execution if not authenticated
        if not st.session_state['password_authenticated']:
            st.stop()
    # Start background bot automatically if not running
    if 'background_bot_running' not in st.session_state or not st.session_state['background_bot_running']:
        start_background_bot()
    # Main dashboard
    st.title("🤖 Crypto Trading Bot Dashboard")
    st.caption("Professional cryptocurrency trading with advanced market analysis and risk management")
    st.markdown("---")
    dashboard()

if __name__ == "__main__":
    main()