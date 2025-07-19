#!/usr/bin/env python3
"""
Complete Hybrid Crypto Trading Bot Dashboard
==========================================
Self-contained with all trading logic included
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json, os, time, threading, requests
import numpy as np

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from binance.client import Client
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False

# Configuration
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')
MIN_BALANCE_USD = float(os.getenv('MIN_BALANCE_USD', '10.0'))
SCAN_INTERVAL = int(os.getenv('SCAN_INTERVAL', '300'))
MIN_CONFIDENCE = float(os.getenv('MIN_CONFIDENCE', '0.65'))
RISK_PERCENTAGE = float(os.getenv('RISK_PERCENTAGE', '0.015'))

# Session State
if 'auto_running' not in st.session_state:
    st.session_state['auto_running'] = False
if 'last_action' not in st.session_state:
    st.session_state['last_action'] = 'None'
if 'scan_results' not in st.session_state:
    st.session_state['scan_results'] = []
if 'risk_override' not in st.session_state:
    st.session_state['risk_override'] = RISK_PERCENTAGE

def get_binance_client():
    """Get authenticated Binance client"""
    if not BINANCE_AVAILABLE or not API_KEY or not API_SECRET:
        return None
    return Client(API_KEY, API_SECRET)

def get_gbp_exchange_rate():
    """Get USD to GBP exchange rate"""
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        return r.json()['rates']['GBP']
    except:
        return 0.79

def ensure_log_files():
    """Create necessary log files"""
    os.makedirs('logs', exist_ok=True)
    
    # Create trades CSV with headers
    if not os.path.exists('logs/trades.csv'):
        with open('logs/trades.csv', 'w') as f:
            f.write('timestamp,symbol,direction,entry_price,exit_price,quantity,change_pct,status,strategy,confidence,pnl_usd,pnl_gbp\n')
    
    # Create other log files
    for log_file in ['logs/manual_trades.log', 'logs/scan_results.json', 'logs/bot_activity.log']:
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                f.write('')

def safe_read_csv(path):
    """Safely read CSV file"""
    try:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return pd.read_csv(path)
    except:
        pass
    return pd.DataFrame()

def log_activity(message):
    """Log bot activity"""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {message}\n"
    
    try:
        with open('logs/bot_activity.log', 'a') as f:
            f.write(log_entry)
    except:
        pass
    
    print(log_entry.strip())

def analyze_symbol(symbol, client):
    """Analyze a trading symbol for opportunities"""
    try:
        # Get recent klines (5-minute intervals, last 24 hours)
        klines = client.get_klines(symbol=symbol, interval='5m', limit=288)
        
        if len(klines) < 50:
            return None
        
        # Convert to price data
        closes = [float(k[4]) for k in klines]
        volumes = [float(k[5]) for k in klines]
        
        # Calculate indicators
        sma_20 = np.mean(closes[-20:])
        sma_50 = np.mean(closes[-50:])
        current_price = closes[-1]
        
        # Price change analysis
        price_change_1h = (closes[-1] - closes[-12]) / closes[-12] * 100  # 12 * 5min = 1 hour
        price_change_4h = (closes[-1] - closes[-48]) / closes[-48] * 100  # 48 * 5min = 4 hours
        
        # Volume analysis
        avg_volume = np.mean(volumes[-20:])
        current_volume = volumes[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # RSI calculation (simplified)
        changes = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [c if c > 0 else 0 for c in changes[-14:]]
        losses = [abs(c) if c < 0 else 0 for c in changes[-14:]]
        avg_gain = np.mean(gains) if gains else 0
        avg_loss = np.mean(losses) if losses else 0
        rs = avg_gain / avg_loss if avg_loss > 0 else 100
        rsi = 100 - (100 / (1 + rs))
        
        # Generate signal
        confidence = 0.5
        decision = "HOLD"
        
        # Breakout strategy
        if current_price > sma_20 and sma_20 > sma_50 and volume_ratio > 1.5:
            if price_change_1h > 2 and rsi < 70:
                decision = "BUY"
                confidence = min(0.9, 0.6 + abs(price_change_1h) / 20)
        
        # Oversold bounce strategy
        elif rsi < 30 and price_change_1h < -3 and volume_ratio > 1.2:
            decision = "BUY"
            confidence = min(0.8, 0.5 + abs(price_change_1h) / 30)
        
        # Momentum sell strategy
        elif rsi > 70 and price_change_1h > 5:
            decision = "SELL"
            confidence = min(0.8, 0.5 + price_change_1h / 25)
        
        return {
            'symbol': symbol,
            'decision': decision,
            'confidence': confidence,
            'current_price': current_price,
            'price_change_1h': price_change_1h,
            'price_change_4h': price_change_4h,
            'volume_ratio': volume_ratio,
            'rsi': rsi,
            'sma_trend': "BULLISH" if sma_20 > sma_50 else "BEARISH",
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        log_activity(f"Error analyzing {symbol}: {e}")
        return None

def scan_markets():
    """Scan multiple markets for opportunities"""
    client = get_binance_client()
    if not client:
        return []
    
    # Popular trading pairs
    symbols = [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT',
        'DOGEUSDT', 'SOLUSDT', 'DOTUSDT', 'LINKUSDT', 'LTCUSDT',
        'BCHUSDT', 'XLMUSDT', 'EOSUSDT', 'TRXUSDT', 'ETCUSDT'
    ]
    
    results = []
    
    for symbol in symbols:
        try:
            result = analyze_symbol(symbol, client)
            if result and result['confidence'] > 0.6:
                results.append(result)
            time.sleep(0.1)  # Rate limiting
        except Exception as e:
            log_activity(f"Error scanning {symbol}: {e}")
            continue
    
    # Sort by confidence
    results.sort(key=lambda x: x['confidence'], reverse=True)
    
    # Save results
    try:
        with open('logs/scan_results.json', 'w') as f:
            json.dump(results, f, indent=2)
    except:
        pass
    
    return results

def get_portfolio():
    """Get portfolio information"""
    client = get_binance_client()
    if not client:
        return {}, 0, 0
    
    try:
        account = client.get_account()
        tickers = {t['symbol']: float(t['price']) for t in client.get_all_tickers()}
        
        portfolio = {}
        total_usd = 0
        
        for balance in account['balances']:
            total = float(balance['free']) + float(balance['locked'])
            if total > 0:
                asset = balance['asset']
                
                if asset in ['USDT', 'BUSD', 'USDC', 'FDUSD']:
                    price = 1.0
                else:
                    symbol = f"{asset}USDT"
                    price = tickers.get(symbol, 0)
                
                usd_value = total * price
                
                if usd_value >= MIN_BALANCE_USD:
                    portfolio[asset] = {
                        'balance': total,
                        'free': float(balance['free']),
                        'locked': float(balance['locked']),
                        'price_usd': price,
                        'usd_value': usd_value
                    }
                    total_usd += usd_value
        
        return portfolio, total_usd, total_usd * get_gbp_exchange_rate()
        
    except Exception as e:
        log_activity(f"Error getting portfolio: {e}")
        return {}, 0, 0

def execute_trade(symbol, side, quantity):
    """Execute a trade"""
    client = get_binance_client()
    if not client:
        return False, "No Binance client"
    
    try:
        order = client.create_order(
            symbol=symbol,
            side=side,
            type='MARKET',
            quantity=quantity
        )
        
        # Log the trade
        trade_data = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'order_id': order['orderId'],
            'status': order['status']
        }
        
        with open('logs/manual_trades.log', 'a') as f:
            f.write(json.dumps(trade_data) + '\n')
        
        log_activity(f"Trade executed: {side} {quantity} {symbol}")
        return True, f"Order placed: {order['orderId']}"
        
    except Exception as e:
        error_msg = f"Trade failed: {e}"
        log_activity(error_msg)
        return False, error_msg

def auto_trading_loop():
    """Background auto trading loop"""
    while st.session_state.get('auto_running', False):
        try:
            log_activity("Auto bot scan cycle starting")
            
            # Scan for opportunities
            results = scan_markets()
            
            if results:
                best_opportunity = results[0]
                
                if best_opportunity['confidence'] > MIN_CONFIDENCE:
                    symbol = best_opportunity['symbol']
                    decision = best_opportunity['decision']
                    
                    # Get portfolio to check if we can trade
                    portfolio, total_usd, _ = get_portfolio()
                    
                    if decision == "BUY" and total_usd > 50:  # Have USDT to buy
                        # Calculate position size (risk management)
                        risk_amount = total_usd * st.session_state.get('risk_override', RISK_PERCENTAGE)
                        quantity = risk_amount / best_opportunity['current_price']
                        
                        # Execute trade
                        success, msg = execute_trade(symbol, "BUY", quantity)
                        
                        if success:
                            st.session_state['last_action'] = f"BUY {quantity:.6f} {symbol}"
                            log_activity(f"Auto trade executed: {st.session_state['last_action']}")
                        else:
                            st.session_state['last_action'] = f"Trade failed: {msg}"
                    
                    elif decision == "SELL":
                        # Check if we own this asset
                        asset = symbol.replace('USDT', '')
                        if asset in portfolio:
                            quantity = portfolio[asset]['free'] * 0.5  # Sell 50%
                            
                            success, msg = execute_trade(symbol, "SELL", quantity)
                            
                            if success:
                                st.session_state['last_action'] = f"SELL {quantity:.6f} {symbol}"
                                log_activity(f"Auto trade executed: {st.session_state['last_action']}")
                            else:
                                st.session_state['last_action'] = f"Trade failed: {msg}"
            
            # Wait before next cycle
            time.sleep(SCAN_INTERVAL)
            
        except Exception as e:
            log_activity(f"Auto trading error: {e}")
            time.sleep(60)  # Wait 1 minute on error

def start_auto_bot():
    """Start the auto trading bot"""
    if not st.session_state.get('auto_running', False):
        st.session_state['auto_running'] = True
        thread = threading.Thread(target=auto_trading_loop, daemon=True)
        thread.start()
        log_activity("Auto trading bot started")

def stop_auto_bot():
    """Stop the auto trading bot"""
    st.session_state['auto_running'] = False
    log_activity("Auto trading bot stopped")

# Main UI
st.set_page_config(page_title="🧠 Hybrid Crypto Bot", layout="wide")
ensure_log_files()

st.title("🧠 Hybrid Crypto Trading Bot")
st.caption("Professional crypto trading with automated scanning and execution")

# Create tabs
tabs = st.tabs(["📊 Portfolio", "🔍 Scanner", "✋ Manual Trade", "🤖 Auto Bot", "📈 Performance", "⚙️ Settings", "💓 Health"])

# Portfolio Tab
with tabs[0]:
    st.header("📊 Portfolio Overview")
    
    with st.spinner("Loading portfolio..."):
        portfolio, total_usd, total_gbp = get_portfolio()
    
    if portfolio:
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("💵 Total USD", f"${total_usd:,.2f}")
        
        with col2:
            st.metric("💷 Total GBP", f"£{total_gbp:,.2f}")
        
        # Portfolio breakdown
        portfolio_data = []
        for asset, data in portfolio.items():
            portfolio_data.append({
                'Asset': asset,
                'Balance': f"{data['balance']:.6f}".rstrip('0').rstrip('.'),
                'Price (USD)': f"${data['price_usd']:.4f}",
                'Value (USD)': f"${data['usd_value']:.2f}",
                'Value (GBP)': f"£{data['usd_value'] * get_gbp_exchange_rate():.2f}",
                'Percentage': f"{(data['usd_value'] / total_usd * 100):.1f}%"
            })
        
        df = pd.DataFrame(portfolio_data)
        st.dataframe(df, use_container_width=True)
        
        # Portfolio pie chart
        values = [data['usd_value'] for data in portfolio.values()]
        labels = list(portfolio.keys())
        
        fig = px.pie(values=values, names=labels, title="Portfolio Distribution")
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.warning("⚠️ No portfolio data available. Check your API keys and connection.")

# Scanner Tab
with tabs[1]:
    st.header("🔍 Market Scanner")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Run Market Scan", type="primary"):
            with st.spinner("Scanning markets..."):
                results = scan_markets()
                st.session_state['scan_results'] = results
                st.success(f"✅ Scan complete! Found {len(results)} opportunities")
    
    with col2:
        if st.button("🔄 Refresh Results"):
            st.rerun()
    
    # Display scan results
    if st.session_state.get('scan_results'):
        st.subheader("📊 Scan Results")
        
        for i, result in enumerate(st.session_state['scan_results'][:10]):  # Show top 10
            with st.expander(f"#{i+1} {result['symbol']} - {result['decision']} (Confidence: {result['confidence']:.1%})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Current Price", f"${result['current_price']:.4f}")
                    st.metric("1H Change", f"{result['price_change_1h']:+.2f}%")
                
                with col2:
                    st.metric("4H Change", f"{result['price_change_4h']:+.2f}%")
                    st.metric("Volume Ratio", f"{result['volume_ratio']:.2f}x")
                
                with col3:
                    st.metric("RSI", f"{result['rsi']:.1f}")
                    st.metric("SMA Trend", result['sma_trend'])
    else:
        st.info("👆 Click 'Run Market Scan' to analyze markets for trading opportunities")

# Manual Trade Tab
with tabs[2]:
    st.header("✋ Manual Trading")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 Place Order")
        
        symbol = st.text_input("Trading Pair", value="ETHUSDT", help="e.g., ETHUSDT, BTCUSDT")
        side = st.selectbox("Order Type", ["BUY", "SELL"])
        quantity = st.number_input("Quantity", min_value=0.000001, value=0.01, format="%.6f")
        
        if st.button("🚀 Execute Trade", type="primary"):
            if symbol and quantity > 0:
                with st.spinner("Executing trade..."):
                    success, message = execute_trade(symbol, side, quantity)
                
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
            else:
                st.error("Please enter valid symbol and quantity")
    
    with col2:
        st.subheader("📊 Recent Manual Trades")
        
        try:
            if os.path.exists('logs/manual_trades.log') and os.path.getsize('logs/manual_trades.log') > 0:
                with open('logs/manual_trades.log', 'r') as f:
                    lines = f.readlines()[-5:]  # Last 5 trades
                
                for line in reversed(lines):
                    try:
                        trade = json.loads(line)
                        st.write(f"🔹 {trade['side']} {trade['quantity']} {trade['symbol']}")
                        st.caption(f"Time: {trade['timestamp'][:19]} | Status: {trade['status']}")
                    except:
                        continue
            else:
                st.info("No manual trades yet")
        except:
            st.info("No trade history available")

# Auto Bot Tab
with tabs[3]:
    st.header("🤖 Auto Trading Bot")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎛️ Bot Control")
        
        is_running = st.session_state.get('auto_running', False)
        
        if is_running:
            st.success("🟢 Auto bot is RUNNING")
            if st.button("🛑 Stop Auto Bot", type="secondary"):
                stop_auto_bot()
                st.rerun()
        else:
            st.warning("🔴 Auto bot is STOPPED")
            if st.button("▶️ Start Auto Bot", type="primary"):
                start_auto_bot()
                st.rerun()
        
        st.info(f"**Last Action:** {st.session_state.get('last_action', 'None')}")
    
    with col2:
        st.subheader("⚙️ Bot Settings")
        
        st.slider(
            "Risk Percentage",
            min_value=0.001,
            max_value=0.05,
            value=st.session_state.get('risk_override', RISK_PERCENTAGE),
            step=0.001,
            key='risk_override',
            help="Percentage of portfolio to risk per trade"
        )
        
        st.number_input(
            "Min Confidence",
            min_value=0.5,
            max_value=0.9,
            value=MIN_CONFIDENCE,
            step=0.05,
            help="Minimum confidence required for auto trades"
        )

# Performance Tab
with tabs[4]:
    st.header("📈 Performance Metrics")
    
    # Load trade data
    trades_df = safe_read_csv('logs/trades.csv')
    
    if not trades_df.empty:
        # Ensure required columns exist
        if 'change_pct' not in trades_df.columns:
            trades_df['change_pct'] = 0
        if 'pnl_usd' not in trades_df.columns:
            trades_df['pnl_usd'] = 0
        
        # Calculate metrics
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['change_pct'] > 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        total_pnl = trades_df['pnl_usd'].sum()
        
        # Metrics display
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Trades", total_trades)
        
        with col2:
            st.metric("Win Rate", f"{win_rate:.1f}%")
        
        with col3:
            st.metric("Total P&L", f"${total_pnl:.2f}")
        
        with col4:
            st.metric("Avg P&L", f"${total_pnl/total_trades:.2f}" if total_trades > 0 else "$0.00")
        
        # P&L Chart
        if 'timestamp' in trades_df.columns:
            trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
            trades_df = trades_df.sort_values('timestamp')
            trades_df['cumulative_pnl'] = trades_df['pnl_usd'].cumsum()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=trades_df['timestamp'],
                y=trades_df['cumulative_pnl'],
                mode='lines+markers',
                name='Cumulative P&L'
            ))
            fig.update_layout(title="Cumulative P&L Over Time", xaxis_title="Time", yaxis_title="P&L (USD)")
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent trades table
        st.subheader("📊 Recent Trades")
        recent_trades = trades_df.tail(10)
        st.dataframe(recent_trades[['timestamp', 'symbol', 'direction', 'entry_price', 'change_pct', 'strategy']], use_container_width=True)
        
    else:
        st.info("📊 No performance data available yet. Start trading to see metrics!")

# Settings Tab
with tabs[5]:
    st.header("⚙️ Trading Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Strategy Settings")
        
        st.slider("Minimum Balance (USD)", 1, 100, int(MIN_BALANCE_USD), key="min_balance")
        st.slider("Scan Interval (seconds)", 60, 900, SCAN_INTERVAL, key="scan_interval")
        
        st.subheader("📊 API Status")
        
        if BINANCE_AVAILABLE and API_KEY and API_SECRET:
            st.success("✅ Binance API configured")
            
            client = get_binance_client()
            if client:
                try:
                    client.get_account()
                    st.success("✅ API connection successful")
                except:
                    st.error("❌ API connection failed")
            else:
                st.error("❌ Could not create Binance client")
        else:
            st.error("❌ Binance API not configured")
            st.info("Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables")
    
    with col2:
        st.subheader("📁 Log Files")
        
        log_files = [
            'logs/trades.csv',
            'logs/manual_trades.log',
            'logs/scan_results.json',
            'logs/bot_activity.log'
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                size = os.path.getsize(log_file)
                st.write(f"✅ {log_file} ({size} bytes)")
            else:
                st.write(f"❌ {log_file} (missing)")

# Health Tab
with tabs[6]:
    st.header("💓 System Health")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🖥️ System Resources")
        
        if PSUTIL_AVAILABLE:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            st.metric("CPU Usage", f"{cpu_percent}%")
            st.metric("Memory Usage", f"{memory.percent}%")
            st.metric("Available Memory", f"{memory.available / (1024**3):.1f} GB")
        else:
            st.warning("⚠️ psutil not installed")
            st.info("Run: pip install psutil")
        
        st.metric("Active Threads", threading.active_count())
    
    with col2:
        st.subheader("📡 Connection Status")
        
        # Test internet connection
        try:
            requests.get("https://api.binance.com/api/v3/ping", timeout=5)
            st.success("✅ Internet connection OK")
        except:
            st.error("❌ Internet connection failed")
        
        # Test Binance API
        client = get_binance_client()
        if client:
            try:
                client.ping()
                st.success("✅ Binance API reachable")
            except:
                st.error("❌ Binance API unreachable")
        else:
            st.error("❌ No Binance client")
        
        st.subheader("📊 Recent Activity")
        
        try:
            if os.path.exists('logs/bot_activity.log'):
                with open('logs/bot_activity.log', 'r') as f:
                    lines = f.readlines()[-5:]
                
                for line in reversed(lines):
                    st.text(line.strip())
            else:
                st.info("No activity logs yet")
        except:
            st.info("Could not read activity logs")

# Auto-refresh for running bot
if st.session_state.get('auto_running', False):
    time.sleep(5)  # Refresh every 5 seconds when bot is running
    st.rerun()
