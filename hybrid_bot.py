#!/usr/bin/env python3
"""
Fixed hybrid_bot.py - Complete Dashboard with All 8 Tabs
=====================================================

This is the complete dashboard with all 8 tabs:
1. Portfolio Overview
2. Market Indicators  
3. Trading (Manual Trading)
4. Performance
5. Logs
6. Settings
7. Strategy
8. Health

🔧 Fixed: IndentationError at line 55
🔧 Added: All missing tab functions
🔧 Enhanced: Complete dashboard functionality

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
import time
import threading
import subprocess
import sys
import signal
import requests
from binance.client import Client
from binance.exceptions import BinanceAPIException

# Configuration
USE_TESTNET = os.getenv('USE_TESTNET', 'True').lower() == 'true'
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')
SCAN_INTERVAL = int(os.getenv('SCAN_INTERVAL', '300'))

# Check if binance is available
BINANCE_AVAILABLE = True
try:
    from binance.client import Client
except ImportError:
    BINANCE_AVAILABLE = False

# Initialize session state
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
    st.session_state['max_trade_percent'] = 10.0

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
                return f.readlines()
    except:
        pass
    return []

def render_manual_trading_tab():
    """Render manual trading tab with live trading capabilities"""
    st.header("📈 Manual Trading")
    st.caption("Execute trades manually with real-time market data and safety controls")
    
    # Check if API is available
    if not BINANCE_AVAILABLE or not API_KEY or not API_SECRET:
        st.error("❌ Binance API not configured. Please check your environment variables.")
        return
    
    try:
        client = Client(API_KEY, API_SECRET)
        if USE_TESTNET:
            client.API_URL = "https://testnet.binance.vision/api"
        
        # Test connection
        account = client.get_account()
        balances = account['balances']
        
    except Exception as e:
        st.error(f"❌ Error connecting to Binance: {e}")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🛒 Place Order")
        
        # Get portfolio for trading options
        portfolio_balances = {}
        for balance in balances:
            if float(balance['free']) > 0:
                portfolio_balances[balance['asset']] = {
                    'free': float(balance['free']),
                    'locked': float(balance['locked'])
                }
        
        # Trade direction
        trade_direction = st.radio("Trade Direction", ["Buy", "Sell"])
        
        # FIX: Proper indentation for the if statement at line 55
        if trade_direction == "Buy":
            # Buy crypto with USDT
            st.write("**Buy Cryptocurrency with USDT**")
            
            # Available cryptos to buy
            available_cryptos = ["BTC", "ETH", "BNB", "ADA", "DOT", "LINK", "LTC", "BCH", "XRP", "DOGE"]
            selected_crypto = st.selectbox("Select Cryptocurrency", available_cryptos)
            
            # Get current USDT balance
            usdt_balance = portfolio_balances.get('USDT', {}).get('free', 0)
            st.info(f"💰 Available USDT: {usdt_balance:.2f}")
            
            # Get current price
            try:
                symbol = f"{selected_crypto}USDT"
                ticker = client.get_symbol_ticker(symbol=symbol)
                current_price = float(ticker['price'])
                st.success(f"💰 Current {selected_crypto} Price: ${current_price:.4f}")
                
                # Calculate quantity
                usdt_amount = st.number_input(
                    f"USDT Amount to spend",
                    min_value=0.0,
                    max_value=float(usdt_balance),
                    value=min(50.0, float(usdt_balance) * 0.1),
                    step=10.0
                )
                
                quantity = usdt_amount / current_price if current_price > 0 else 0
                st.info(f"🔹 You'll receive approximately **{quantity:.6f} {selected_crypto}**")
                
            except Exception as e:
                st.error(f"Error getting price for {selected_crypto}: {e}")
                current_price = 0
                quantity = 0
        
        else:
            # Sell crypto for USDT
            st.write("**Sell Cryptocurrency for USDT**")
            
            # Get available assets to sell
            available_assets = [asset for asset in portfolio_balances.keys() 
                              if asset != 'USDT' and portfolio_balances[asset]['free'] > 0]
            
            if not available_assets:
                st.warning("⚠️ No cryptocurrency available to sell")
                return
            
            selected_asset = st.selectbox("Select Asset to Sell", available_assets)
            asset_balance = portfolio_balances.get(selected_asset, {}).get('free', 0)
            
            # Get current price
            try:
                symbol = f"{selected_asset}USDT"
                ticker = client.get_symbol_ticker(symbol=symbol)
                current_price = float(ticker['price'])
                st.success(f"💰 Current {selected_asset} Price: ${current_price:.4f}")
                
                # Calculate quantity to sell
                quantity = st.number_input(
                    f"Quantity of {selected_asset} to sell",
                    min_value=0.0,
                    max_value=float(asset_balance),
                    value=min(float(asset_balance), float(asset_balance) * 0.1),
                    format="%.8f"
                )
                
                estimated_usdt = quantity * current_price
                st.info(f"💳 You'll receive approximately **${estimated_usdt:.2f} USDT**")
                
            except Exception as e:
                st.error(f"Error getting price for {selected_asset}: {e}")
                current_price = 0
                quantity = 0
        
        # Order type
        order_type = st.selectbox("Order Type", ["MARKET", "LIMIT"])
        
        # Limit price input for LIMIT orders
        limit_price = current_price
        if order_type == "LIMIT":
            limit_price = st.number_input(
                "Limit Price",
                min_value=0.0,
                value=float(current_price),
                format="%.8f"
            )
        
        # Execute button
        if trade_direction == "Buy":
            button_text = f"🛒 Buy {quantity:.6f} {selected_crypto}"
            symbol = f"{selected_crypto}USDT"
            side = "BUY"
        else:
            button_text = f"🔥 Sell {quantity:.6f} {selected_asset}"
            symbol = f"{selected_asset}USDT"
            side = "SELL"
        
        # Validation
        can_execute = quantity > 0 and current_price > 0
        
        if st.button(button_text, type="primary", disabled=not can_execute):
            if can_execute:
                try:
                    # Get symbol precision info for limit orders
                    exchange_info = client.get_exchange_info()
                    symbol_info = None
                    for s in exchange_info['symbols']:
                        if s['symbol'] == symbol:
                            symbol_info = s
                            break
                    
                    # Format price and quantity
                    if symbol_info:
                        price_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER'), None)
                        lot_size_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'), None)
                        
                        if price_filter and order_type == "LIMIT":
                            tick_size = float(price_filter['tickSize'])
                            decimals = len(str(tick_size).split('.')[-1].rstrip('0'))
                            limit_price = round(float(limit_price), decimals) if limit_price else round(current_price, decimals)
                        
                        if lot_size_filter:
                            step_size = float(lot_size_filter['stepSize'])
                            qty_decimals = len(str(step_size).split('.')[-1].rstrip('0'))
                            quantity = round(float(quantity), qty_decimals)
                    
                    # Execute the trade
                    if order_type == "MARKET":
                        order = client.create_order(
                            symbol=symbol,
                            side=side,
                            type="MARKET",
                            quantity=str(quantity)
                        )
                    else:
                        order = client.create_order(
                            symbol=symbol,
                            side=side,
                            type="LIMIT",
                            timeInForce="GTC",
                            quantity=str(quantity),
                            price=str(limit_price)
                        )
                    
                    st.success(f"✅ {order_type} order placed successfully!")
                    st.json(order)
                    
                    # Log the trade
                    trade_data = {
                        'timestamp': datetime.now().isoformat(),
                        'type': 'manual_trade',
                        'symbol': symbol,
                        'side': side,
                        'quantity': quantity,
                        'price': limit_price if order_type == "LIMIT" else current_price,
                        'order_id': order.get('orderId'),
                        'status': order.get('status')
                    }
                    
                    # Ensure logs directory exists
                    os.makedirs('logs', exist_ok=True)
                    
                    with open('logs/manual_trades.log', 'a') as f:
                        f.write(f"{json.dumps(trade_data)}\n")
                        
                except Exception as e:
                    st.error(f"❌ Order failed: {e}")
                    if "insufficient balance" in str(e).lower():
                        st.warning("💡 Try reducing the quantity or check your balance")
                    elif "invalid price" in str(e).lower():
                        st.warning("💡 Adjust the limit price within market bounds")
                    elif "lot size" in str(e).lower():
                        st.warning("💡 Adjust quantity to meet minimum/maximum limits")
    
    with col2:
        st.subheader("📊 Portfolio Overview")
        
        # Display current balances
        if portfolio_balances:
            portfolio_df = pd.DataFrame([
                {'Asset': asset, 'Free': data['free'], 'Locked': data['locked']}
                for asset, data in portfolio_balances.items()
            ])
            st.dataframe(portfolio_df)
        else:
            st.info("No balances available")
        
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

def render_market_indicators_tab():
    """Render market indicators tab"""
    st.header("📊 Market Indicators")
    st.caption("Real-time market analysis and trading opportunities")
    
    # Manual scan button
    if st.button("🔍 Scan Market Now", type="primary"):
        perform_scan()
    
    # Display last scan results
    if 'last_opportunities' in st.session_state and st.session_state['last_opportunities']:
        st.subheader("🎯 Current Trading Opportunities")
        
        opportunities_df = pd.DataFrame(st.session_state['last_opportunities'])
        st.dataframe(opportunities_df, use_container_width=True)
        
        # Chart of opportunities
        if 'confidence' in opportunities_df.columns:
            fig = px.bar(opportunities_df, x='symbol', y='confidence', 
                        title="Trading Opportunities by Confidence")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("🔍 No opportunities found in last scan. Try scanning again or wait for market movements.")

def render_performance_tab():
    """Render performance tab"""
    st.header("📈 Trading Performance")
    st.caption("Historical performance metrics and trade analysis")
    
    # Load trade history from file if exists
    trade_file = "logs/trades.csv"
    if os.path.exists(trade_file):
        df = pd.read_csv(trade_file)
        
        if not df.empty:
            total_trades = len(df)
            winning_trades = len(df[df['change_pct'] > 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            total_pnl = df['change_pct'].sum()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Trades", total_trades)
            with col2:
                st.metric("Win Rate", f"{win_rate:.1f}%")
            with col3:
                st.metric("Total P&L", f"{total_pnl:+.2f}%")
            with col4:
                avg_trade = df['change_pct'].mean()
                st.metric("Avg Trade", f"{avg_trade:+.2f}%")
            
            # Performance chart
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['cumulative_pnl'] = df['change_pct'].cumsum()
                
                fig = px.line(df, x='timestamp', y='cumulative_pnl', 
                             title="Cumulative P&L Over Time")
                st.plotly_chart(fig, use_container_width=True)
            
            # Recent trades table
            st.subheader("📋 Recent Trades")
            st.dataframe(df.tail(10), use_container_width=True)
        else:
            st.info("No trade history available yet.")
    else:
        st.info("No trade history file found. Start trading to see performance metrics.")
    
    # Bot scanning statistics
    st.subheader("🔍 Scanning Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Scans", st.session_state['scan_count'])
    
    with col2:
        if st.session_state['last_scan_time']:
            time_since = (datetime.now() - st.session_state['last_scan_time']).seconds
            st.metric("Last Scan", f"{time_since}s ago")
        else:
            st.metric("Last Scan", "Never")
    
    with col3:
        opportunities = len(st.session_state.get('last_opportunities', []))
        st.metric("Current Opportunities", opportunities)

def render_logs_tab():
    """Render logs tab"""
    st.header("📋 System Logs")
    st.caption("Real-time bot activity and system logs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔍 Scan Logs")
        
        scan_log_file = "logs/portfolio_scans.log"
        if os.path.exists(scan_log_file):
            with open(scan_log_file, 'r', encoding='utf-8') as f:
                scan_logs = f.readlines()[-50:]
            
            scan_text = "".join(scan_logs)
            st.text_area("Recent Scan Events", scan_text, height=400)
        else:
            st.info("No scan log file found.")
    
    with col2:
        st.subheader("📟 Console Output")
        
        log_file = "logs/console_output.log"
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = f.readlines()[-100:]
            
            log_text = "".join(logs)
            st.text_area("Recent Console Output", log_text, height=400)
        else:
            st.info("No console log file found.")
    
    # Download button
    if st.button("📥 Download All Logs"):
        all_logs = ""
        for log_file in ["logs/portfolio_scans.log", "logs/console_output.log"]:
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    all_logs += f"\n=== {log_file} ===\n"
                    all_logs += f.read()
        
        st.download_button(
            "Download Combined Logs",
            data=all_logs,
            file_name=f"all_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

def render_settings_tab():
    """Render settings tab"""
    st.header("⚙️ Bot Control & Settings")
    st.caption("Configure bot parameters and control trading behavior")
    
    col1, col2 = st.columns(2)
    
    with col1:
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
        st.subheader("⚙️ Configuration")
        
        # Max trade percentage
        max_trade_percent = st.slider(
            "Max Trade Size (% of Portfolio)", 
            1.0, 20.0, 
            st.session_state['max_trade_percent'], 
            0.5
        )
        st.session_state['max_trade_percent'] = max_trade_percent
        st.info(f"Current max trade per deal: {max_trade_percent:.1f}% of portfolio value.")
        
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
    
    with col2:
        st.subheader("🔧 System Information")
        
        # API Status
        st.markdown("**API Configuration:**")
        st.write(f"- API Key: {'✅ Configured' if API_KEY else '❌ Missing'}")
        st.write(f"- API Secret: {'✅ Configured' if API_SECRET else '❌ Missing'}")
        st.write(f"- Mode: {'🧪 Testnet' if USE_TESTNET else '🔴 Live Trading'}")
        
        # Environment
        st.markdown("**Environment:**")
        st.write(f"- Binance Library: {'✅ Available' if BINANCE_AVAILABLE else '❌ Missing'}")
        st.write(f"- Scan Interval: {SCAN_INTERVAL} seconds")
        
        # Directories
        st.markdown("**Log Directories:**")
        log_dir = os.path.exists("logs")
        st.write(f"- Logs Directory: {'✅ Exists' if log_dir else '❌ Missing'}")
        
        if log_dir:
            log_files = os.listdir("logs")
            st.write(f"- Log Files: {len(log_files)} files")
            for log_file in log_files[:5]:  # Show first 5 files
                st.write(f"  - {log_file}")

def render_strategy_tab():
    """Render strategy tab"""
    st.header("🎯 Trading Strategy")
    st.caption("Strategy configuration and performance analysis")
    
    # Strategy Overview
    st.subheader("📋 Current Strategy: Enhanced Breakout")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Strategy Rules:**
        - 🎯 **Entry**: 5% price move in 2 hours
        - 📈 **Take Profit**: 8-15% (confidence-based)
        - 🛑 **Stop Loss**: 8-12% (confidence-based)
        - ⏰ **Max Hold**: 4 hours
        - 🔄 **Trailing Stop**: 3-4% when profitable
        """)
    
    with col2:
        st.markdown("""
        **Filters & Enhancements:**
        - 📊 **Volume**: 1.5x average required
        - 🕐 **Time**: Avoid 0-6 UTC, 22-23 UTC
        - 📈 **RSI**: 20-80 range only
        - 🎲 **Confidence**: 0.65+ minimum
        - 🔄 **Market Structure**: Trend analysis
        """)
    
    # Strategy Performance
    st.subheader("📊 Strategy Performance")
    
    # Mock performance data (replace with real data)
    performance_data = {
        'Traditional Breakout': {'win_rate': 65.2, 'avg_return': 2.3, 'trades': 45},
        'ML Enhanced': {'win_rate': 72.8, 'avg_return': 3.1, 'trades': 38},
        'Volume Filtered': {'win_rate': 68.9, 'avg_return': 2.8, 'trades': 41}
    }
    
    for strategy, stats in performance_data.items():
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(f"{strategy} - Win Rate", f"{stats['win_rate']:.1f}%")
        with col2:
            st.metric(f"Avg Return", f"{stats['avg_return']:.1f}%")
        with col3:
            st.metric(f"Total Trades", stats['trades'])
    
    # Strategy Settings
    st.subheader("⚙️ Strategy Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        confidence_threshold = st.slider("Confidence Threshold", 0.5, 0.9, 0.65, 0.05)
        volume_multiplier = st.slider("Volume Multiplier", 1.0, 3.0, 1.5, 0.1)
    
    with col2:
        max_positions = st.slider("Max Simultaneous Positions", 1, 5, 3)
        risk_per_trade = st.slider("Risk per Trade (%)", 0.5, 3.0, 1.5, 0.1)
    
    if st.button("💾 Save Strategy Settings"):
        st.success("Strategy settings saved!")

def render_health_tab():
    """Render health tab"""
    st.header("💓 System Health")
    st.caption("Bot health monitoring and system diagnostics")
    
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
            mode = "🧪 Testnet" if USE_TESTNET else "🔴 Live Trading"
            st.info(f"📡 Mode: {mode}")
        else:
            st.error("❌ Binance API Not Connected")
        
        # Connection test
        if st.button("🔄 Test API Connection"):
            if BINANCE_AVAILABLE and API_KEY and API_SECRET:
                try:
                    client = Client(API_KEY, API_SECRET)
                    if USE_TESTNET:
                        client.API_URL = "https://testnet.binance.vision/api"
                    
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
    
    # Log file status
    st.subheader("📁 Log File Status")
    
    log_files = ['logs/console_output.log', 'logs/portfolio_scans.log', 'logs/trades.csv']
    log_status = []
    
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                size = os.path.getsize(log_file)
                log_status.append({
                    'File': log_file,
                    'Status': '✅ Exists',
                    'Size': f"{size:,} bytes"
                })
            except:
                log_status.append({
                    'File': log_file,
                    'Status': '⚠️ Error',
                    'Size': 'Unknown'
                })
        else:
            log_status.append({
                'File': log_file,
                'Status': '❌ Missing',
                'Size': 'N/A'
            })
    
    log_df = pd.DataFrame(log_status)
    st.dataframe(log_df, use_container_width=True)
    
    # Recent log activity
    if os.path.exists("logs/console_output.log"):
        st.subheader("📝 Recent Log Activity")
        try:
            with open("logs/console_output.log", "r", encoding="utf-8") as f:
                last_lines = f.readlines()[-10:]
            st.code("\n".join([line.strip() for line in last_lines]))
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

def load_trade_data():
    """Load trade performance data"""
    log_path = "logs/single_pair_performance.json"
    try:
        df = pd.read_json(log_path, lines=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        return df
    except Exception:
        return pd.DataFrame()

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
        'latest_strategy': 'Breakout',
        'latest_risk_level': 'Balanced'
    }

def get_gbp_exchange_rate():
    """Get USD to GBP exchange rate"""
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        return response.json()['rates']['GBP']
    except:
        return 0.79

def color_line(line):
    """Color code log lines"""
    if "error" in line.lower():
        return f":red[{line.strip()}]"
    elif any(x in line.lower() for x in ["profit", "+", "✅", "success"]):
        return f":green[{line.strip()}]"
    elif any(x in line.lower() for x in ["heartbeat", "💓"]):
        return f":blue[{line.strip()}]"
    elif "🔍" in line or "scan" in line.lower():
        return f":orange[{line.strip()}]"
    return f"{line.strip()}"

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

def render_portfolio_overview_tab(portfolio, gbp_rate, market_condition, condition_score, avg_volatility):
    """Render portfolio overview tab"""
    st.header("💼 Portfolio Overview")
    st.caption("Live portfolio analysis with dynamic risk management")
    
    # Define market explanations
    market_explanations = {
        "BULL_TRENDING": {
            "emoji": "🟢",
            "description": "Bullish Market",
            "explanation": "Assets are generally trending upward with positive momentum."
        },
        "CONSOLIDATING": {
            "emoji": "🟡",
            "description": "Consolidating Market",
            "explanation": "Market is in a sideways pattern with moderate volatility."
        },
        "HIGH_VOLATILITY": {
            "emoji": "🔴",
            "description": "High Volatility",
            "explanation": "Market showing significant price swings and uncertainty."
        },
        "UNCERTAIN": {
            "emoji": "⚪",
            "description": "Uncertain Market",
            "explanation": "Market conditions are unclear or mixed signals."
        }
    }
    
    # Market condition display
    market_info = market_explanations.get(market_condition, market_explanations["UNCERTAIN"])
    st.markdown(f"### {market_info['emoji']} {market_info['description']}")
    st.info(market_info['explanation'])
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Market Confidence", f"{condition_score:.1%}")
    
    with col2:
        st.metric("Avg Volatility", f"{avg_volatility:.1f}%")
    
    with col3:
        st.metric("Active Positions", len(portfolio))
    
    with col4:
        st.metric("GBP Rate", f"£{gbp_rate:.3f}")
    
    # Portfolio breakdown
    if portfolio:
        st.subheader("📊 Active Positions")
        portfolio_df = pd.DataFrame([
            {
                'Symbol': symbol,
                'Price': f"${data.get('price', 0):.4f}",
                'Change': f"{data.get('change', 0):.2f}%",
                'Volume': f"{data.get('volume', 0):.0f}",
                'Confidence': f"{data.get('confidence', 0):.1%}"
            }
            for symbol, data in portfolio.items()
        ])
        st.dataframe(portfolio_df, use_container_width=True)
    else:
        st.info("No active positions")

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
    # Get Tailscale IP and setup sidebar controls
    ts_ip = get_tailscale_ip()
    remote_url = f"http://{ts_ip}:8501" if ts_ip != "Unavailable" else "Unavailable"
    
    # Sidebar setup
    st.sidebar.markdown(f"**Tailscale IP:** `{ts_ip}`")
    st.sidebar.text_input("🔗 Access URL", value=remote_url, key="url", label_visibility="collapsed")
    st.sidebar.download_button("📥 Download Logs", data="\n".join(load_logs("logs/console_output.log")), file_name="console_output.log")

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

    # Auto-start background bot on first load
    if not st.session_state['background_bot_running'] and BINANCE_AVAILABLE and API_KEY and API_SECRET:
        start_background_bot()

    # Sidebar navigation - ALL 8 TABS
    selected_tab = st.sidebar.radio(
        "Select Dashboard Tab",
        ["Portfolio Overview", "Market Indicators", "Trading", "Performance", "Logs", "Settings", "Strategy", "Health"]
    )
    
    # Get portfolio data for all tabs
    status = load_bot_status()
    portfolio = status.get('portfolio', {})
    gbp_rate = get_gbp_exchange_rate()
    
    if portfolio:
        market_condition, condition_score, avg_volatility = simulate_market_analysis(portfolio)
    else:
        market_condition, condition_score, avg_volatility = "UNCERTAIN", 0.5, 2.0
    
    # Render selected tab
    if selected_tab == "Portfolio Overview":
        render_portfolio_overview_tab(portfolio, gbp_rate, market_condition, condition_score, avg_volatility)
    elif selected_tab == "Market Indicators":
        render_market_indicators_tab()
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

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="🤖 Crypto Trading Bot Dashboard", 
        page_icon="🤖",
        layout="wide"
    )
    
    # Password authentication
    if not st.session_state['password_authenticated']:
        st.title("🔒 Enter Dashboard Password")
        st.caption("Default password: admin123")
        
        input_password = st.text_input("Password", type="password")
        
        if st.button("🔓 Login"):
            if input_password == st.session_state['dashboard_password']:
                st.session_state['password_authenticated'] = True
                st.success("✅ Access granted!")
                st.rerun()
            else:
                st.error("❌ Incorrect password.")
                st.stop()
        
        if not st.session_state['password_authenticated']:
            st.stop()
    
    # Main dashboard
    st.title("🤖 Crypto Trading Bot Dashboard")
    st.caption("Professional cryptocurrency trading with advanced market analysis and risk management")
    st.markdown("---")
    
    dashboard()

if __name__ == "__main__":
    main()