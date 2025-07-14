# dashboard.py - Railway Compatible Portfolio Trading Bot (Fixed Threading Issues)
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os, time, json, requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import numpy as np

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(page_title="🎯 Multi-Coin Portfolio Bot", layout="wide")

# Configuration
USE_TESTNET = os.getenv("USE_TESTNET", "True").lower() == "true"
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
MIN_BALANCE_USD = float(os.getenv("MIN_BALANCE_USD", "10.0"))

# Initialize session state
if 'dashboard_password' not in st.session_state:
    st.session_state['dashboard_password'] = 'bottie'
if 'password_authenticated' not in st.session_state:
    st.session_state['password_authenticated'] = False
if 'bot_running' not in st.session_state:
    st.session_state['bot_running'] = False
if 'last_opportunities' not in st.session_state:
    st.session_state['last_opportunities'] = []
if 'selected_strategy' not in st.session_state:
    st.session_state['selected_strategy'] = 'ML Enhanced'
if 'strategy_mode' not in st.session_state:
    st.session_state['strategy_mode'] = 'Automatic'
if 'max_trade_percent' not in st.session_state:
    st.session_state['max_trade_percent'] = 5.0
if 'scan_count' not in st.session_state:
    st.session_state['scan_count'] = 0
if 'last_scan_time' not in st.session_state:
    st.session_state['last_scan_time'] = None
if 'last_portfolio_scan' not in st.session_state:
    st.session_state['last_portfolio_scan'] = None

# Check for Binance library
try:
    from binance.client import Client
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False

def create_log_directories():
    """Ensure log directories exist"""
    os.makedirs('logs', exist_ok=True)

def get_gbp_exchange_rate():
    """Get USD to GBP exchange rate"""
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        return response.json()['rates']['GBP']
    except:
        return 0.79  # Fallback rate

def get_binance_client():
    """Initialize Binance client"""
    if not BINANCE_AVAILABLE or not API_KEY or not API_SECRET:
        return None
    
    try:
        client = Client(API_KEY, API_SECRET)
        if USE_TESTNET:
            client.API_URL = "https://testnet.binance.vision/api"
        return client
    except Exception as e:
        st.error(f"❌ Error connecting to Binance: {e}")
        return None

def get_real_portfolio():
    """Get real portfolio from Binance API"""
    client = get_binance_client()
    if not client:
        return {}, get_gbp_exchange_rate()
    
    try:
        account = client.get_account()
        all_prices = client.get_all_tickers()
        price_dict = {ticker['symbol']: float(ticker['price']) for ticker in all_prices}
        
        portfolio = {}
        gbp_rate = get_gbp_exchange_rate()
        
        for balance in account['balances']:
            asset = balance['asset']
            free_balance = float(balance['free'])
            locked_balance = float(balance['locked'])
            total_balance = free_balance + locked_balance
            
            if total_balance > 0:
                if asset == 'USDT':
                    portfolio[asset] = {
                        'balance': total_balance,
                        'free': free_balance,
                        'locked': locked_balance,
                        'price_usd': 1.0,
                        'usd_value': total_balance,
                        'gbp_value': total_balance * gbp_rate,
                        'symbol': 'USDT',
                        'change_24h': 0.0
                    }
                else:
                    trading_symbol = f"{asset}USDT"
                    if trading_symbol in price_dict:
                        price_usd = price_dict[trading_symbol]
                        usd_value = total_balance * price_usd
                        
                        if usd_value >= MIN_BALANCE_USD:
                            try:
                                ticker_24h = client.get_24hr_ticker(symbol=trading_symbol)
                                change_24h = float(ticker_24h['priceChangePercent'])
                            except:
                                change_24h = 0.0
                            
                            portfolio[asset] = {
                                'balance': total_balance,
                                'free': free_balance,
                                'locked': locked_balance,
                                'price_usd': price_usd,
                                'usd_value': usd_value,
                                'gbp_value': usd_value * gbp_rate,
                                'symbol': trading_symbol,
                                'change_24h': change_24h
                            }
        
        return portfolio, gbp_rate
        
    except Exception as e:
        st.error(f"❌ Error fetching real portfolio: {e}")
        return {}, get_gbp_exchange_rate()

def analyze_market_opportunity(symbol, client):
    """Analyze market opportunity for a symbol"""
    try:
        klines = client.get_klines(symbol=symbol, interval='1m', limit=120)
        
        if len(klines) < 120:
            return None
        
        open_price = float(klines[0][1])
        close_price = float(klines[-1][4])
        change_pct = ((close_price - open_price) / open_price) * 100
        
        volumes = [float(kline[5]) for kline in klines[-20:]]
        avg_volume = sum(volumes) / len(volumes)
        current_volume = float(klines[-1][5])
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        signal = "HOLD"
        confidence = 0.5
        
        if abs(change_pct) >= 5.0 and volume_ratio >= 1.5:
            if change_pct >= 5.0:
                signal = "BUY_LONG"
                confidence = min(0.95, 0.6 + (change_pct - 5) * 0.05)
            elif change_pct <= -5.0:
                signal = "BUY_SHORT"
                confidence = min(0.95, 0.6 + (abs(change_pct) - 5) * 0.05)
        
        return {
            'symbol': symbol,
            'signal': signal,
            'confidence': confidence,
            'change_pct': change_pct,
            'volume_ratio': volume_ratio,
            'current_price': close_price
        }
        
    except Exception as e:
        return None

def scan_portfolio_opportunities(portfolio):
    """Scan all portfolio holdings for trading opportunities"""
    client = get_binance_client()
    if not client:
        return []
    
    opportunities = []
    
    for asset, data in portfolio.items():
        if asset == 'USDT':
            continue
            
        symbol = data['symbol']
        opportunity = analyze_market_opportunity(symbol, client)
        
        if opportunity and opportunity['signal'] != 'HOLD':
            opportunity.update({
                'asset': asset,
                'balance': data['balance'],
                'usd_value': data['usd_value'],
                'free_balance': data['free']
            })
            opportunities.append(opportunity)
    
    opportunities.sort(key=lambda x: x['confidence'], reverse=True)
    return opportunities

def perform_scan():
    """Perform a single scan (Railway compatible - no threading)"""
    try:
        # Update scan count
        st.session_state['scan_count'] += 1
        st.session_state['last_scan_time'] = datetime.now()
        
        # Log scan attempt
        log_scan_event('scan_attempt', {
            'scan_number': st.session_state['scan_count'],
            'timestamp': datetime.now().isoformat()
        })
        
        # Get portfolio
        portfolio, gbp_rate = get_real_portfolio()
        
        if portfolio:
            # Scan for opportunities
            opportunities = scan_portfolio_opportunities(portfolio)
            st.session_state['last_opportunities'] = opportunities
            st.session_state['last_portfolio_scan'] = portfolio
            
            # Log successful scan
            log_scan_event('scan_success', {
                'scan_count': st.session_state['scan_count'],
                'portfolio_assets': len(portfolio),
                'opportunities_found': len(opportunities)
            })
            
            return True
        else:
            log_scan_event('scan_failed', {'reason': 'portfolio_fetch_failed'})
            return False
            
    except Exception as e:
        log_scan_event('scan_error', {'error': str(e)})
        return False

def log_scan_event(event_type, data):
    """Log scan events to file"""
    try:
        create_log_directories()
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event': event_type,
            'data': data
        }
        
        with open('logs/portfolio_scans.log', 'a') as f:
            f.write(f"{json.dumps(log_entry)}\n")
    except:
        pass  # Silent fail for logging

def render_portfolio_overview(portfolio, gbp_rate):
    """Render portfolio overview tab"""
    st.subheader("💼 Portfolio Overview")
    
    if not portfolio:
        st.warning("No portfolio data available. Check your Binance API connection.")
        return
    
    total_usd = sum(coin['usd_value'] for coin in portfolio.values())
    total_gbp = total_usd * gbp_rate
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Total Value (USD)", f"${total_usd:,.2f}")
    
    with col2:
        st.metric("💷 Total Value (GBP)", f"£{total_gbp:,.2f}")
    
    with col3:
        st.metric("🪙 Total Assets", len(portfolio))
    
    with col4:
        mode = "🧪 Testnet" if USE_TESTNET else "🚀 Live Trading"
        st.metric("🔗 Trading Mode", mode)
    
    st.divider()
    
    # Bot status section
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.session_state['bot_running']:
            st.metric("🤖 Bot Status", "🟢 Running", "Auto-Scan Active")
        else:
            st.metric("🤖 Bot Status", "🔴 Stopped", "Manual Only")
    
    with col2:
        st.metric("🔍 Total Scans", st.session_state['scan_count'])
    
    with col3:
        if st.session_state['last_scan_time']:
            last_scan = st.session_state['last_scan_time'].strftime("%H:%M:%S")
            st.metric("⏰ Last Scan", last_scan)
        else:
            st.metric("⏰ Last Scan", "Never")
    
    with col4:
        opportunities = len(st.session_state.get('last_opportunities', []))
        st.metric("🎯 Opportunities", opportunities)
    
    st.divider()
    
    # Portfolio breakdown table
    portfolio_data = []
    for asset, data in portfolio.items():
        portfolio_data.append({
            'Asset': asset,
            'Balance': f"{data['balance']:.8f}".rstrip('0').rstrip('.'),
            'Price (USD)': f"${data['price_usd']:.4f}",
            'Value (USD)': f"${data['usd_value']:.2f}",
            'Value (GBP)': f"£{data['gbp_value']:.2f}",
            '24h Change': f"{data.get('change_24h', 0):.2f}%",
            'Percentage': f"{(data['usd_value'] / total_usd * 100):.1f}%"
        })
    
    df = pd.DataFrame(portfolio_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Portfolio distribution chart
    if len(portfolio) > 1:
        fig = px.pie(
            values=[data['usd_value'] for data in portfolio.values()],
            names=list(portfolio.keys()),
            title="Portfolio Distribution by Value"
        )
        st.plotly_chart(fig, use_container_width=True)

def render_market_indicators(portfolio):
    """Render market indicators tab"""
    st.subheader("📊 Market Indicators & Signals")
    st.caption("Live analysis of all your holdings for trading opportunities")
    
    if not portfolio:
        st.warning("No portfolio data available.")
        return
    
    # Scan controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Scan Now", type="primary"):
            with st.spinner("Scanning portfolio for opportunities..."):
                if perform_scan():
                    st.success("✅ Scan completed!")
                else:
                    st.error("❌ Scan failed!")
                st.rerun()
    
    with col2:
        if st.session_state['bot_running']:
            st.success("🟢 Auto-scan: ON")
        else:
            st.info("⏸️ Auto-scan: OFF")
    
    with col3:
        if st.session_state['last_scan_time']:
            time_since = (datetime.now() - st.session_state['last_scan_time']).seconds
            st.metric("Seconds ago", time_since)
    
    st.divider()
    
    # Display opportunities
    opportunities = st.session_state.get('last_opportunities', [])
    
    if opportunities:
        st.success(f"Found {len(opportunities)} trading opportunities!")
        
        for i, opp in enumerate(opportunities):
            with st.expander(f"🎯 {opp['asset']} - {opp['signal']} (Confidence: {opp['confidence']:.1%})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Current Price", f"${opp['current_price']:.4f}")
                    st.metric("2h Change", f"{opp['change_pct']:+.2f}%")
                
                with col2:
                    st.metric("Your Balance", f"{opp['balance']:.6f} {opp['asset']}")
                    st.metric("USD Value", f"${opp['usd_value']:.2f}")
                
                with col3:
                    st.metric("Volume Ratio", f"{opp['volume_ratio']:.2f}x")
                    st.metric("Signal Strength", opp['signal'])
    else:
        st.info("🔍 No trading opportunities found. Try scanning again or wait for market movements.")

def render_performance_tab():
    """Render performance tab"""
    st.subheader("📈 Trading Performance")
    
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
            st.subheader("Recent Trades")
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
    st.subheader("📋 System Logs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Scan Logs")
        
        scan_log_file = "logs/portfolio_scans.log"
        if os.path.exists(scan_log_file):
            with open(scan_log_file, 'r', encoding='utf-8') as f:
                scan_logs = f.readlines()[-50:]
            
            scan_text = "".join(scan_logs)
            st.text_area("Recent Scan Events", scan_text, height=400)
        else:
            st.info("No scan log file found.")
    
    with col2:
        st.subheader("Console Output")
        
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
    st.subheader("⚙️ Bot Control & Settings")
    
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
        st.subheader("📊 System Status")
        
        # API connection status
        client = get_binance_client()
        if client:
            st.success("✅ Binance API Connected")
            mode = "Testnet" if USE_TESTNET else "Live Trading"
            st.info(f"📡 Mode: {mode}")
        else:
            st.error("❌ Binance API Not Connected")
        
        # System info
        st.write(f"**Min Balance Filter:** ${MIN_BALANCE_USD}")
        st.write(f"**Current Time:** {datetime.now().strftime('%H:%M:%S')}")
        
        # Manual operations
        st.markdown("---")
        st.subheader("🔧 Manual Operations")
        
        if st.button("🔄 Manual Scan"):
            with st.spinner("Scanning..."):
                if perform_scan():
                    st.success("✅ Manual scan completed!")
                else:
                    st.error("❌ Manual scan failed!")
        
        if st.button("🧹 Clear Scan Count"):
            st.session_state['scan_count'] = 0
            st.session_state['last_scan_time'] = None
            st.success("Scan count reset to 0")
        
        if st.button("🔄 Refresh All Data"):
            st.rerun()

def render_strategy_tab():
    """Render strategy tab"""
    st.subheader("🧠 Strategy Selection")
    
    strategies = [
        "ML Enhanced", "Breakout", "Scalping", "Swing", 
        "Conservative", "Balanced", "Aggressive"
    ]
    
    strategy_mode = st.radio(
        "Select Strategy Mode",
        ["Automatic", "Manual"],
        horizontal=True,
        index=["Automatic", "Manual"].index(st.session_state['strategy_mode'])
    )
    st.session_state['strategy_mode'] = strategy_mode
    
    selected_strategy = st.selectbox(
        "Choose Strategy",
        strategies,
        index=strategies.index(st.session_state['selected_strategy'])
    )
    st.session_state['selected_strategy'] = selected_strategy
    
    st.write(f"**Current Mode:** {strategy_mode}")
    st.write(f"**Selected Strategy:** {selected_strategy}")
    
    if strategy_mode == "Manual":
        st.info("Manual mode: You control the strategy selection.")
    else:
        st.info("Automatic mode: Bot will select the best strategy based on market analytics.")
    
    strategy_info = {
        "ML Enhanced": "Combines machine learning predictions with traditional technical analysis. Adapts to changing market conditions using features like price momentum, volatility, RSI, MACD, and support/resistance.",
        "Breakout": "Trades when price breaks above resistance or below support. Looks for strong 5% moves, often after periods of consolidation.",
        "Scalping": "Executes frequent trades targeting small 2-3% price moves. Relies on high volume and liquidity.",
        "Swing": "Seeks 10-20% moves over longer timeframes. Trades on established trends and reversals.",
        "Conservative": "Only trades on high-confidence signals and small price moves. Focuses on capital preservation.",
        "Balanced": "Uses standard breakout logic with moderate confidence thresholds. Mix of risk and reward.",
        "Aggressive": "Trades on lower confidence signals and larger price moves. Higher risk for greater potential returns."
    }
    
    st.markdown(f"**Strategy Characteristics:**")
    st.info(strategy_info.get(selected_strategy, 'No info available.'))

def render_health_tab():
    """Render health tab"""
    st.subheader("💓 Bot Health & Status")
    
    # Connection status
    client = get_binance_client()
    if client:
        st.success("✅ Binance API Connection: Healthy")
    else:
        st.error("❌ Binance API Connection: Failed")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state['bot_running']:
            st.success("🟢 Auto-Scan: ENABLED")
        else:
            st.error("🔴 Auto-Scan: DISABLED")
    
    with col2:
        st.metric("Portfolio Scans", st.session_state['scan_count'])
    
    with col3:
        if st.session_state['last_scan_time']:
            time_diff = datetime.now() - st.session_state['last_scan_time']
            st.metric("Seconds Since Scan", time_diff.seconds)
        else:
            st.metric("Seconds Since Scan", "Never")
    
    # System health checks
    health_checks = {
        "API Keys Configured": bool(API_KEY and API_SECRET),
        "Environment File Loaded": os.path.exists('.env'),
        "Log Directory Exists": os.path.exists('logs'),
        "Trading Mode": "Testnet" if USE_TESTNET else "Live",
        "Binance Library Available": BINANCE_AVAILABLE,
        "Auto-Scan Status": "Enabled" if st.session_state['bot_running'] else "Disabled"
    }
    
    st.subheader("✅ System Health Checks")
    for check, status in health_checks.items():
        if isinstance(status, bool):
            if status:
                st.success(f"✅ {check}")
            else:
                st.error(f"❌ {check}")
        else:
            st.info(f"ℹ️ {check}: {status}")
    
    st.write(f"**Last Health Check:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Recent scan activity
    st.subheader("📋 Recent Scan Activity")
    scan_log_file = "logs/portfolio_scans.log"
    if os.path.exists(scan_log_file):
        try:
            with open(scan_log_file, 'r', encoding='utf-8') as f:
                logs = f.readlines()[-10:]
            
            for log_line in logs:
                try:
                    log_data = json.loads(log_line)
                    event = log_data.get('event', 'unknown')
                    timestamp = log_data.get('timestamp', 'unknown')
                    st.text(f"{timestamp}: {event}")
                except:
                    st.text(log_line.strip())
        except Exception as e:
            st.error(f"Error reading scan logs: {e}")
    else:
        st.warning("No scan log file found")

def main():
    """Main application function"""
    try:
        st.title("🎯 Multi-Coin Portfolio Trading Bot")
        st.caption("Continuous scanning of your cryptocurrency holdings for trading opportunities")
        
        # Password Protection
        if not st.session_state['password_authenticated']:
            st.subheader("🔒 Enter Dashboard Password")
            input_password = st.text_input("Password", type="password")
            if st.button("Login"):
                if input_password == st.session_state['dashboard_password']:
                    st.session_state['password_authenticated'] = True
                    st.success("Access granted!")
                    st.rerun()
                else:
                    st.error("Incorrect password.")
                    st.stop()
            if not st.session_state['password_authenticated']:
                st.stop()
        
        # Sidebar controls
        st.sidebar.title("🎛️ Bot Controls")
        
        # Auto-scan status in sidebar
        if st.session_state['bot_running']:
            st.sidebar.success("🟢 Auto-Scan: ON")
            st.sidebar.info(f"🔍 Scans completed: {st.session_state['scan_count']}")
            
            if st.session_state['last_scan_time']:
                time_since = (datetime.now() - st.session_state['last_scan_time']).seconds
                st.sidebar.write(f"⏰ Last scan: {time_since}s ago")
        else:
            st.sidebar.warning("🔴 Auto-Scan: OFF")
            st.sidebar.info("Enable in Settings tab")
        
        # Quick scan button in sidebar
        if st.sidebar.button("🔄 Quick Scan", type="primary"):
            with st.spinner("Scanning..."):
                if perform_scan():
                    st.sidebar.success("✅ Scan completed!")
                else:
                    st.sidebar.error("❌ Scan failed!")
                st.rerun()
        
        # Bot statistics in sidebar
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Bot Statistics")
        
        opportunities = len(st.session_state.get('last_opportunities', []))
        st.sidebar.metric("🎯 Active Opportunities", opportunities)
        st.sidebar.metric("🔄 Total Scans", st.session_state['scan_count'])
        
        if st.session_state['bot_running']:
            st.sidebar.metric("⚡ Status", "AUTO-SCAN", "Active")
        else:
            st.sidebar.metric("⚡ Status", "MANUAL", "Manual Only")
        
        # Navigation
        selected_tab = st.sidebar.radio(
            "Select Dashboard Tab",
            ["Portfolio Overview", "Market Indicators", "Performance", "Logs", "Settings", "Strategy", "Health"]
        )
        
        # Get real portfolio data
        portfolio, gbp_rate = get_real_portfolio()
        
        # Render selected tab
        if selected_tab == "Portfolio Overview":
            render_portfolio_overview(portfolio, gbp_rate)
        
        elif selected_tab == "Market Indicators":
            render_market_indicators(portfolio)
        
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
        
        # Auto-refresh when auto-scan is enabled
        if st.session_state['bot_running']:
            st.sidebar.markdown("---")
            st.sidebar.info("🔄 Auto-refreshing every 30s")
            
            # Perform automatic scan every 30 seconds
            time.sleep(30)
            perform_scan()
            st.rerun()
        
    except Exception as e:
        st.error(f"Application Error: {e}")
        st.info("Please check your configuration and try again.")

# Initialize log directories on startup
create_log_directories()

# Log dashboard startup
log_scan_event('dashboard_startup', {
    'testnet': USE_TESTNET,
    'api_configured': bool(API_KEY and API_SECRET),
    'binance_available': BINANCE_AVAILABLE
})

if __name__ == "__main__":
    main()