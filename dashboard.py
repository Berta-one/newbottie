# dashboard.py - Complete Trading Bot Dashboard
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import json
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(page_title="🎯 Crypto Trading Bot Dashboard", layout="wide")

# Check if we have Binance library
try:
    from binance.client import Client
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False

# Configuration
PIN_REQUIRED = os.getenv("DASHBOARD_PIN", "1234")

# Session state initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "selected_profile" not in st.session_state:
    st.session_state.selected_profile = "AUTO"

# Risk Management Profiles
RISK_PROFILES = {
    "AUTO": {
        "name": "Auto-Select",
        "description": "Automatically selects best profile based on market conditions",
        "take_profit": "Dynamic",
        "stop_loss": "Dynamic",
        "max_hold_hours": "Variable"
    },
    "CONSERVATIVE": {
        "name": "Conservative",
        "description": "Low risk, high confidence trades only",
        "take_profit": 6.0,
        "stop_loss": 4.0,
        "max_hold_hours": 6
    },
    "BALANCED": {
        "name": "Balanced",
        "description": "Standard institutional approach",
        "take_profit": 10.0,
        "stop_loss": 8.0,
        "max_hold_hours": 4
    },
    "AGGRESSIVE": {
        "name": "Aggressive",
        "description": "Higher risk, trend-following strategy",
        "take_profit": 15.0,
        "stop_loss": 12.0,
        "max_hold_hours": 8
    },
    "SCALPING": {
        "name": "Scalping",
        "description": "Quick trades, minimal exposure",
        "take_profit": 3.0,
        "stop_loss": 2.0,
        "max_hold_hours": 1
    }
}

@st.cache_resource
def get_binance_client():
    """Initialize Binance client"""
    if not BINANCE_AVAILABLE:
        return None
    
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    use_testnet = os.getenv("USE_TESTNET", "True").lower() == "true"
    
    if not api_key or not api_secret:
        return None
    
    try:
        client = Client(api_key, api_secret)
        if use_testnet:
            client.API_URL = "https://testnet.binance.vision/api"
        
        # Test connection
        client.get_server_time()
        return client
    except Exception as e:
        st.error(f"❌ Binance connection failed: {e}")
        return None

@st.cache_data(ttl=60)
def get_gbp_exchange_rate():
    """Get live USD to GBP exchange rate"""
    try:
        apis = [
            "https://api.exchangerate-api.com/v4/latest/USD",
            "https://api.fxratesapi.com/latest?base=USD"
        ]
        
        for api_url in apis:
            try:
                response = requests.get(api_url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if 'rates' in data and 'GBP' in data['rates']:
                        return data['rates']['GBP']
            except:
                continue
        
        return 0.79  # Fallback rate
    except:
        return 0.79

@st.cache_data(ttl=120)
def get_real_portfolio():
    """Get real portfolio from Binance API"""
    client = get_binance_client()
    if not client:
        return get_demo_portfolio()
    
    try:
        account = client.get_account()
        tickers = client.get_all_tickers()
        price_map = {ticker['symbol']: float(ticker['price']) for ticker in tickers}
        gbp_rate = get_gbp_exchange_rate()
        
        portfolio = {}
        total_usd = 0.0
        
        for balance in account['balances']:
            asset = balance['asset']
            free = float(balance['free'])
            locked = float(balance['locked'])
            total_balance = free + locked
            
            if total_balance > 0:
                usd_value = 0.0
                price_usd = 0.0
                trading_symbol = None
                
                if asset in ['USDT', 'BUSD', 'USDC']:
                    usd_value = total_balance
                    price_usd = 1.0
                    trading_symbol = f"{asset}USDT"
                else:
                    for quote in ['USDT', 'BUSD', 'USDC']:
                        symbol = f"{asset}{quote}"
                        if symbol in price_map:
                            price_usd = price_map[symbol]
                            usd_value = total_balance * price_usd
                            trading_symbol = symbol
                            break
                
                if usd_value >= 1.0:  # Only show assets worth more than $1
                    # Get 24h price change
                    change_24h = 0.0
                    try:
                        if trading_symbol and trading_symbol in price_map:
                            ticker_24h = client.get_24hr_ticker(symbol=trading_symbol)
                            change_24h = float(ticker_24h['priceChangePercent'])
                    except:
                        pass
                    
                    portfolio[asset] = {
                        'balance': total_balance,
                        'free': free,
                        'locked': locked,
                        'price_usd': price_usd,
                        'usd_value': usd_value,
                        'gbp_value': usd_value * gbp_rate,
                        'change_24h': change_24h,
                        'symbol': trading_symbol
                    }
                    total_usd += usd_value
        
        # Calculate percentages
        for asset in portfolio:
            portfolio[asset]['percentage'] = (portfolio[asset]['usd_value'] / total_usd) * 100 if total_usd > 0 else 0
        
        return portfolio, total_usd, total_usd * gbp_rate
        
    except Exception as e:
        st.error(f"❌ Error fetching real portfolio: {e}")
        return get_demo_portfolio()

def get_demo_portfolio():
    """Demo portfolio for testing"""
    gbp_rate = get_gbp_exchange_rate()
    
    portfolio = {
        'BTC': {
            'balance': 0.15234, 'price_usd': 64950.0, 'usd_value': 9890.45,
            'change_24h': 2.34, 'symbol': 'BTCUSDT', 'free': 0.15234, 'locked': 0.0
        },
        'ETH': {
            'balance': 1.8945, 'price_usd': 2410.50, 'usd_value': 4567.89,
            'change_24h': -1.23, 'symbol': 'ETHUSDT', 'free': 1.8945, 'locked': 0.0
        },
        'SOL': {
            'balance': 45.67, 'price_usd': 62.98, 'usd_value': 2876.32,
            'change_24h': 5.67, 'symbol': 'SOLUSDT', 'free': 45.67, 'locked': 0.0
        },
        'USDT': {
            'balance': 1234.56, 'price_usd': 1.0, 'usd_value': 1234.56,
            'change_24h': 0.0, 'symbol': 'USDT', 'free': 1234.56, 'locked': 0.0
        }
    }
    
    total_usd = sum(p['usd_value'] for p in portfolio.values())
    
    for asset in portfolio:
        portfolio[asset]['gbp_value'] = portfolio[asset]['usd_value'] * gbp_rate
        portfolio[asset]['percentage'] = (portfolio[asset]['usd_value'] / total_usd) * 100
    
    return portfolio, total_usd, total_usd * gbp_rate

def load_bot_status():
    """Load bot status from file"""
    try:
        with open("logs/bot_status.json", "r") as f:
            return json.load(f)
    except:
        return {"status": "unknown", "timestamp": "No data", "details": "Status file not found"}

def load_trade_data():
    """Load real trade performance data"""
    try:
        trades = []
        if os.path.exists("logs/single_pair_performance.json"):
            with open("logs/single_pair_performance.json", "r") as f:
                for line in f:
                    if line.strip():
                        trade = json.loads(line)
                        # Filter out simulation trades
                        if trade.get('mode') != 'SIMULATION':
                            trades.append(trade)
        
        return pd.DataFrame(trades)
    except Exception as e:
        st.error(f"❌ Error loading trade data: {e}")
        return pd.DataFrame()

def load_console_logs():
    """Load recent console logs"""
    try:
        with open("logs/console_output.log", "r", encoding="utf-8") as f:
            lines = f.readlines()
            return lines[-50:]  # Last 50 lines
    except:
        return ["No logs found"]

def render_portfolio_tab():
    """Render the portfolio overview tab"""
    st.header("💼 Portfolio Overview")
    
    # Get portfolio data
    use_testnet = os.getenv("USE_TESTNET", "True").lower() == "true"
    
    if use_testnet:
        st.info("🧪 **TESTNET MODE** - Using demo portfolio data")
        portfolio, total_usd, total_gbp = get_demo_portfolio()
    else:
        st.success("💰 **LIVE MODE** - Real Binance portfolio")
        portfolio, total_usd, total_gbp = get_real_portfolio()
    
    # Portfolio summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💷 Total Value (GBP)", f"£{total_gbp:,.2f}")
    
    with col2:
        st.metric("💰 Total Value (USD)", f"${total_usd:,.2f}")
    
    with col3:
        st.metric("🪙 Assets", len(portfolio))
    
    with col4:
        # Calculate 24h portfolio change
        total_24h_change = 0
        for asset, data in portfolio.items():
            weight = data['percentage'] / 100
            total_24h_change += data['change_24h'] * weight
        
        change_color = "🟢" if total_24h_change > 0 else "🔴" if total_24h_change < 0 else "⚪"
        st.metric(f"{change_color} 24h Change", f"{total_24h_change:+.2f}%")
    
    # Portfolio allocation chart
    if portfolio:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Pie chart
            assets = list(portfolio.keys())
            values = [portfolio[asset]['usd_value'] for asset in assets]
            
            fig = px.pie(
                values=values,
                names=assets,
                title="Portfolio Allocation",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 🏆 Top Holdings")
            sorted_assets = sorted(portfolio.items(), key=lambda x: x[1]['usd_value'], reverse=True)
            
            for i, (asset, data) in enumerate(sorted_assets[:5]):
                percentage = data['percentage']
                usd_value = data['usd_value']
                change_24h = data['change_24h']
                change_color = "🟢" if change_24h > 0 else "🔴" if change_24h < 0 else "⚪"
                
                st.write(f"**{i+1}. {asset}:** {percentage:.1f}% (${usd_value:,.2f}) {change_color}{change_24h:+.2f}%")
    
    # Detailed holdings table
    st.subheader("📊 Detailed Holdings")
    
    if portfolio:
        portfolio_data = []
        for asset, data in portfolio.items():
            portfolio_data.append({
                'Asset': asset,
                'Balance': f"{data['balance']:.6f}".rstrip('0').rstrip('.'),
                'Price (USD)': f"${data['price_usd']:.6f}".rstrip('0').rstrip('.'),
                'Value (USD)': f"${data['usd_value']:.2f}",
                'Value (GBP)': f"£{data['gbp_value']:.2f}",
                '24h Change': f"{data['change_24h']:+.2f}%",
                'Portfolio %': f"{data['percentage']:.1f}%",
                'Free': f"{data['free']:.6f}".rstrip('0').rstrip('.'),
                'Locked': f"{data['locked']:.6f}".rstrip('0').rstrip('.') if data['locked'] > 0 else "0"
            })
        
        df = pd.DataFrame(portfolio_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("📭 No portfolio data available")

def render_performance_tab():
    """Render trading performance tab"""
    st.header("📈 Trading Performance")
    
    df = load_trade_data()
    
    if not df.empty:
        # Performance metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📈 Total Trades", len(df))
        
        with col2:
            winning_trades = (df['pnl_percent'] > 0).sum()
            win_rate = (winning_trades / len(df)) * 100
            st.metric("🏆 Win Rate", f"{win_rate:.1f}%")
        
        with col3:
            total_pnl = df['pnl_percent'].sum()
            st.metric("💰 Total P&L", f"{total_pnl:+.2f}%")
        
        with col4:
            avg_pnl = df['pnl_percent'].mean()
            st.metric("📊 Avg P&L", f"{avg_pnl:+.2f}%")
        
        # Performance chart
        if len(df) > 1:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            df['cumulative_pnl'] = df['pnl_percent'].cumsum()
            
            fig = px.line(df, x='timestamp', y='cumulative_pnl',
                         title="📈 Cumulative Trading Performance",
                         labels={'cumulative_pnl': 'Cumulative P&L (%)'})
            
            fig.update_traces(line_color='#00ff88', line_width=3)
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent trades table
        st.subheader("📋 Recent Trades")
        recent_trades = df.tail(10).copy()
        if not recent_trades.empty:
            recent_trades['timestamp'] = pd.to_datetime(recent_trades['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
            display_cols = ['timestamp', 'symbol', 'action', 'price', 'pnl_percent', 'confidence']
            available_cols = [col for col in display_cols if col in recent_trades.columns]
            display_trades = recent_trades[available_cols].copy()
            display_trades.columns = [col.replace('_', ' ').title() for col in available_cols]
            
            st.dataframe(display_trades, use_container_width=True, hide_index=True)
        
        # Performance by symbol
        if 'symbol' in df.columns and len(df) > 1:
            st.subheader("📊 Performance by Symbol")
            
            symbol_performance = df.groupby('symbol').agg({
                'pnl_percent': ['count', 'sum', 'mean']
            }).round(2)
            
            symbol_performance.columns = ['Trades', 'Total P&L %', 'Avg P&L %']
            symbol_performance = symbol_performance.sort_values('Total P&L %', ascending=False)
            
            st.dataframe(symbol_performance, use_container_width=True)
    
    else:
        st.info("📊 No trading performance data available yet")
        st.markdown("""
        **Note:** Only real trades are shown here. Simulated trades are filtered out.
        
        Start the bot to begin generating real trading data!
        """)

def render_logs_tab():
    """Render logs monitoring tab"""
    st.header("📡 Bot Monitoring & Logs")
    
    # Bot status
    bot_status = load_bot_status()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status = bot_status.get("status", "unknown")
        if status.lower() == "running":
            st.success("🟢 Bot is RUNNING")
        elif status.lower() == "stopped":
            st.error("🔴 Bot is STOPPED")
        else:
            st.warning("⚪ Bot status UNKNOWN")
    
    with col2:
        timestamp = bot_status.get("timestamp", "Unknown")
        st.info(f"⏰ Last update: {timestamp}")
    
    with col3:
        details = bot_status.get("details", "No details")
        st.info(f"📋 Status: {details}")
    
    # Log controls
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🔄 Refresh Logs"):
            st.rerun()
    
    # Display logs
    st.subheader("📄 Recent Bot Activity")
    
    logs = load_console_logs()
    
    if logs and len(logs) > 1:
        # Filter and format logs
        formatted_logs = []
        for line in logs:
            line = line.strip()
            if "ERROR" in line.upper():
                formatted_logs.append(f"🔴 {line}")
            elif "WARNING" in line.upper():
                formatted_logs.append(f"🟡 {line}")
            elif any(x in line for x in ["BUY", "SELL", "PROFIT", "SIGNAL"]):
                formatted_logs.append(f"🟢 {line}")
            elif "HOLD" in line:
                formatted_logs.append(f"⚪ {line}")
            else:
                formatted_logs.append(f"ℹ️ {line}")
        
        log_text = "\n".join(formatted_logs)
        st.text_area("Console Output", log_text, height=400)
        
        # Log statistics
        st.subheader("📊 Log Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        error_count = sum(1 for line in logs if "ERROR" in line.upper())
        warning_count = sum(1 for line in logs if "WARNING" in line.upper())
        info_count = sum(1 for line in logs if "INFO" in line.upper())
        signal_count = sum(1 for line in logs if any(x in line for x in ["BUY", "SELL"]))
        
        with col1:
            st.metric("ℹ️ Info", info_count)
        with col2:
            st.metric("⚠️ Warnings", warning_count)
        with col3:
            st.metric("❌ Errors", error_count)
        with col4:
            st.metric("🎯 Signals", signal_count)
    
    else:
        st.warning("📭 No logs found. Bot may not be running.")

def render_settings_tab():
    """Render settings and controls tab"""
    st.header("⚙️ Bot Settings & Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎛️ Bot Controls")
        
        # Bot control buttons
        run_flag_exists = os.path.exists("run_bot.flag")
        
        if run_flag_exists:
            st.success("🟢 Bot is currently running")
            if st.button("🛑 Stop Bot", type="primary", use_container_width=True):
                try:
                    os.remove("run_bot.flag")
                    st.success("✅ Stop signal sent to bot")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to stop bot: {e}")
        else:
            st.warning("🔴 Bot is currently stopped")
            if st.button("▶️ Start Bot", type="primary", use_container_width=True):
                try:
                    with open("run_bot.flag", "w") as f:
                        f.write("run\n")
                    st.success("✅ Start signal sent to bot")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to start bot: {e}")
        
        st.divider()
        
        # Risk Profile Selection
        st.subheader("🛡️ Risk Management Profile")
        
        current_profile = st.session_state.selected_profile
        
        profile_options = list(RISK_PROFILES.keys())
        profile_names = [RISK_PROFILES[key]['name'] for key in profile_options]
        
        selected_index = profile_options.index(current_profile) if current_profile in profile_options else 0
        
        new_profile = st.selectbox(
            "Select Trading Profile:",
            options=profile_options,
            format_func=lambda x: RISK_PROFILES[x]['name'],
            index=selected_index,
            key="profile_selector"
        )
        
        if new_profile != current_profile:
            st.session_state.selected_profile = new_profile
            # Save profile selection to file for bot to read
            try:
                with open("logs/selected_profile.json", "w") as f:
                    json.dump({"profile": new_profile, "timestamp": datetime.now().isoformat()}, f)
                st.success(f"✅ Profile changed to: {RISK_PROFILES[new_profile]['name']}")
            except Exception as e:
                st.error(f"❌ Failed to save profile: {e}")
        
        # Display selected profile details
        profile_info = RISK_PROFILES[new_profile]
        st.info(f"**{profile_info['name']}**: {profile_info['description']}")
        
        if new_profile != "AUTO":
            st.write(f"**Take Profit:** {profile_info['take_profit']}%")
            st.write(f"**Stop Loss:** {profile_info['stop_loss']}%")
            st.write(f"**Max Hold Time:** {profile_info['max_hold_hours']} hours")
    
    with col2:
        st.subheader("📊 System Configuration")
        
        # Current configuration
        config = {
            "Trading Mode": "🧪 TESTNET" if os.getenv("USE_TESTNET", "True").lower() == "true" else "💰 LIVE",
            "Trade Symbol": os.getenv("TRADE_SYMBOL", "BTCUSDT"),
            "Scan Interval": f"{os.getenv('SCAN_INTERVAL', '300')} seconds",
            "Risk Percentage": f"{float(os.getenv('RISK_PERCENTAGE', '0.015'))*100:.1f}%",
            "Min Confidence": os.getenv("MIN_CONFIDENCE", "0.65"),
            "Max Positions": os.getenv("MAX_POSITIONS", "3")
        }
        
        for key, value in config.items():
            st.write(f"**{key}:** {value}")
        
        st.divider()
        
        # File system status
        st.subheader("📁 System Status")
        
        files_status = {
            "🏃 Bot Running": "✅" if os.path.exists("run_bot.flag") else "❌",
            "📊 Bot Status": "✅" if os.path.exists("logs/bot_status.json") else "❌",
            "📝 Console Logs": "✅" if os.path.exists("logs/console_output.log") else "❌",
            "💹 Trade Data": "✅" if os.path.exists("logs/single_pair_performance.json") else "❌",
            "⚙️ Environment": "✅" if os.path.exists(".env") else "❌"
        }
        
        for item, status in files_status.items():
            st.write(f"{item}: {status}")
        
        st.divider()
        
        # Data export
        st.subheader("📥 Data Export")
        
        # Export logs
        logs = load_console_logs()
        if logs:
            log_data = "".join(logs)
            st.download_button(
                "📄 Download Logs",
                data=log_data,
                file_name=f"bot_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        # Export trade data
        df = load_trade_data()
        if not df.empty:
            csv_data = df.to_csv(index=False)
            st.download_button(
                "📊 Download Trades",
                data=csv_data,
                file_name=f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

def main():
    """Main dashboard function"""
    
    # PIN Protection
    if not st.session_state.authenticated:
        st.title("🔐 Dashboard Access")
        st.caption("Enter your PIN to access the trading dashboard")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            user_pin = st.text_input("Enter PIN:", type="password", placeholder="Enter 4-digit PIN")
            
            if st.button("🔓 Access Dashboard", use_container_width=True):
                if user_pin == PIN_REQUIRED:
                    st.session_state.authenticated = True
                    st.success("✅ Access granted!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Incorrect PIN. Please try again.")
        
        st.info("💡 Default PIN is **1234** (configurable in .env file)")
        return
    
    # Main Dashboard
    st.title("🎯 Crypto Trading Bot Dashboard")
    st.caption("Professional cryptocurrency trading with real-time portfolio monitoring")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "💼 Portfolio & Currencies",
        "📈 Performance",
        "📡 Logs & Monitoring",
        "⚙️ Settings & Controls"
    ])
    
    with tab1:
        render_portfolio_tab()
    
    with tab2:
        render_performance_tab()
    
    with tab3:
        render_logs_tab()
    
    with tab4:
        render_settings_tab()
    
    # Footer
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption("🔄 Auto-refresh: Every 30 seconds")
    
    with col2:
        gbp_rate = get_gbp_exchange_rate()
        st.caption(f"💱 Exchange Rate: 1 USD = {gbp_rate:.4f} GBP")
    
    with col3:
        st.caption(f"⏰ Last Updated: {datetime.now().strftime('%H:%M:%S')}")
    
    # Auto-refresh
    time.sleep(2)
    st.rerun()

if __name__ == "__main__":
    main()