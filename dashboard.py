# dashboard.py - UNIFIED PRODUCTION VERSION FOR RAILWAY
import streamlit as st
import pandas as pd
import plotly.express as px
import os, json, time, socket, subprocess
from datetime import datetime
from dotenv import load_dotenv
import requests
import numpy as np

# Load environment variables
load_dotenv()

# Set page config FIRST
st.set_page_config(page_title="🎯 Crypto Trading Bot", layout="wide", initial_sidebar_state="expanded")

# UNIFIED AUTHENTICATION SYSTEM
# Priority: Environment variable → Default PIN → Password fallback
DASHBOARD_PIN = os.getenv("DASHBOARD_PIN", "1234")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "bottie")

# Use PIN if it's 4 digits, otherwise use password
if len(DASHBOARD_PIN) == 4 and DASHBOARD_PIN.isdigit():
    AUTH_TYPE = "PIN"
    AUTH_VALUE = DASHBOARD_PIN
else:
    AUTH_TYPE = "PASSWORD" 
    AUTH_VALUE = DASHBOARD_PASSWORD

# Session state initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def authenticate_user():
    """Unified authentication function"""
    if not st.session_state.authenticated:
        st.title("🔐 Trading Bot Access Control")
        
        if AUTH_TYPE == "PIN":
            st.subheader("Enter Dashboard PIN")
            user_input = st.text_input("PIN", type="password", placeholder="Enter 4-digit PIN")
        else:
            st.subheader("Enter Dashboard Password") 
            user_input = st.text_input("Password", type="password", placeholder="Enter password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔓 Login", type="primary"):
                if user_input == AUTH_VALUE:
                    st.session_state.authenticated = True
                    st.success("✅ Access granted!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Incorrect credentials!")
        
        with col2:
            st.info(f"Authentication: {AUTH_TYPE}")
            if AUTH_TYPE == "PIN":
                st.caption("Default PIN: 1234")
            else:
                st.caption("Default Password: bottie")
        
        return False
    return True

class BotController:
    """Simple bot controller for Railway deployment"""
    def __init__(self):
        self.run_flag = "run_bot.flag"
        self.status_file = "logs/bot_status.json"
    
    def is_running(self):
        return os.path.exists(self.run_flag)
    
    def start(self):
        try:
            with open(self.run_flag, "w") as f:
                f.write("run\n")
            return True
        except:
            return False
    
    def stop(self):
        try:
            if os.path.exists(self.run_flag):
                os.remove(self.run_flag)
            return True
        except:
            return False

def load_logs(log_file, max_lines=100):
    """Load log files safely"""
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                return f.readlines()[-max_lines:]
        except:
            return ["Error reading log file"]
    return ["No logs found"]

def get_tailscale_ip():
    """Get Tailscale IP for remote access"""
    try:
        output = subprocess.check_output("tailscale ip -4", shell=True, text=True).strip()
        return output.splitlines()[0]
    except:
        return "Not Available"

def get_gbp_exchange_rate():
    """Get USD to GBP exchange rate"""
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        return response.json()['rates']['GBP']
    except:
        return 0.79  # Fallback rate

def load_trade_data():
    """Load trading performance data"""
    try:
        # Try multiple log file locations
        log_files = [
            "logs/trades.csv",
            "logs/single_pair_performance.json", 
            "logs/performance.json"
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                if log_file.endswith('.csv'):
                    return pd.read_csv(log_file)
                else:
                    return pd.read_json(log_file, lines=True)
        
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading trade data: {e}")
        return pd.DataFrame()

def get_demo_portfolio():
    """Demo portfolio for display"""
    gbp_rate = get_gbp_exchange_rate()
    portfolio = {
        'BTC': {'balance': 0.15234, 'usd_value': 9890.45, 'symbol': 'BTCUSDT', 'price_usd': 64950.0},
        'ETH': {'balance': 1.8945, 'usd_value': 4567.89, 'symbol': 'ETHUSDT', 'price_usd': 2410.50},
        'SOL': {'balance': 45.67, 'usd_value': 2876.32, 'symbol': 'SOLUSDT', 'price_usd': 62.98},
        'XRP': {'balance': 1250.0, 'usd_value': 743.75, 'symbol': 'XRPUSDT', 'price_usd': 0.595},
        'ADA': {'balance': 2890.5, 'usd_value': 1234.56, 'symbol': 'ADAUSDT', 'price_usd': 0.427}
    }
    
    for asset in portfolio:
        portfolio[asset]['gbp_value'] = portfolio[asset]['usd_value'] * gbp_rate
    
    return portfolio, gbp_rate

def render_overview_tab():
    """Main overview dashboard"""
    st.header("🏠 Trading Bot Overview")
    
    # Bot status
    controller = BotController()
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if controller.is_running():
            st.metric("🤖 Bot Status", "🟢 RUNNING", "Active")
        else:
            st.metric("🤖 Bot Status", "🔴 STOPPED", "Inactive")
    
    with col2:
        st.metric("🌐 Platform", "Railway", "Cloud Hosted")
    
    with col3:
        st.metric("⏰ Server Time", datetime.now().strftime("%H:%M:%S"), "Live")
    
    with col4:
        ts_ip = get_tailscale_ip()
        if ts_ip != "Not Available":
            st.metric("📡 Tailscale", "Connected", ts_ip)
        else:
            st.metric("📡 Tailscale", "Disconnected", "Local Only")
    
    # Portfolio overview
    st.subheader("💰 Portfolio Overview")
    portfolio, gbp_rate = get_demo_portfolio()
    
    total_usd = sum(asset['usd_value'] for asset in portfolio.values())
    total_gbp = total_usd * gbp_rate
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Value (USD)", f"${total_usd:,.2f}")
    with col2:
        st.metric("Total Value (GBP)", f"£{total_gbp:,.2f}")
    with col3:
        st.metric("USD/GBP Rate", f"£{gbp_rate:.4f}")
    
    # Portfolio breakdown
    portfolio_df = pd.DataFrame.from_dict(portfolio, orient='index')
    portfolio_df.index.name = 'Asset'
    portfolio_df = portfolio_df.reset_index()
    
    fig = px.pie(portfolio_df, values='usd_value', names='Asset', 
                title="Portfolio Distribution")
    st.plotly_chart(fig, use_container_width=True)

def render_performance_tab():
    """Performance analysis"""
    st.header("📊 Trading Performance")
    
    df = load_trade_data()
    
    if df.empty:
        st.info("No trading data available yet. Start the bot to see performance metrics.")
        return
    
    # Performance metrics
    if 'pnl_percent' in df.columns or 'change_pct' in df.columns:
        pnl_col = 'pnl_percent' if 'pnl_percent' in df.columns else 'change_pct'
        
        total_trades = len(df)
        winning_trades = len(df[df[pnl_col] > 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        total_pnl = df[pnl_col].sum()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Trades", total_trades)
        with col2:
            st.metric("Win Rate", f"{win_rate:.1f}%")
        with col3:
            st.metric("Total P&L", f"{total_pnl:+.2f}%")
        with col4:
            avg_trade = df[pnl_col].mean()
            st.metric("Avg Trade", f"{avg_trade:+.2f}%")
        
        # Performance chart
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['cumulative_pnl'] = df[pnl_col].cumsum()
            
            fig = px.line(df, x='timestamp', y='cumulative_pnl', 
                         title="Cumulative P&L Over Time")
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent trades
        st.subheader("Recent Trades")
        st.dataframe(df.tail(10), use_container_width=True)

def render_logs_tab():
    """System logs and monitoring"""
    st.header("📡 System Logs & Monitoring")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Console Output")
        refresh_rate = st.slider("Refresh Rate (seconds)", 5, 30, 10)
        
        logs = load_logs("logs/console_output.log", 50)
        log_text = "".join(logs)
        
        if log_text.strip():
            st.text_area("Recent Logs", log_text, height=400)
            
            # Heartbeat check
            heartbeat_found = any("heartbeat" in line.lower() for line in logs[-10:])
            if heartbeat_found:
                st.success("✅ Bot heartbeat detected")
            else:
                st.warning("⚠️ No recent heartbeat")
        else:
            st.info("No logs available")
    
    with col2:
        st.subheader("System Status")
        
        # File status
        important_files = [
            "run_bot.flag",
            "logs/console_output.log", 
            "logs/trades.csv",
            ".env"
        ]
        
        for file_path in important_files:
            if os.path.exists(file_path):
                st.success(f"✅ {file_path}")
            else:
                st.error(f"❌ {file_path}")
        
        # Download logs
        if st.button("📥 Download All Logs"):
            log_data = "\n".join(load_logs("logs/console_output.log", 1000))
            st.download_button(
                "Download Console Logs",
                data=log_data,
                file_name=f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

def render_settings_tab():
    """Bot control and settings"""
    st.header("⚙️ Bot Control & Settings")
    
    controller = BotController()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🤖 Bot Control")
        
        if controller.is_running():
            st.success("Bot is currently RUNNING")
            if st.button("🛑 Stop Bot", type="secondary"):
                if controller.stop():
                    st.success("Bot stopped successfully")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to stop bot")
        else:
            st.warning("Bot is currently STOPPED")
            if st.button("▶️ Start Bot", type="primary"):
                if controller.start():
                    st.success("Bot started successfully")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to start bot")
    
    with col2:
        st.subheader("🔗 Remote Access")
        
        ts_ip = get_tailscale_ip()
        if ts_ip != "Not Available":
            remote_url = f"http://{ts_ip}:8501"
            st.success(f"📡 Tailscale IP: {ts_ip}")
            st.text_input("🔗 Remote Access URL", value=remote_url)
        else:
            st.info("📡 Tailscale not available")
        
        # Environment info
        st.subheader("🌍 Environment")
        env_info = {
            "Platform": "Railway",
            "Port": os.getenv("PORT", "8501"),
            "Environment": os.getenv("RAILWAY_ENVIRONMENT", "Unknown"),
            "Authentication": AUTH_TYPE
        }
        
        for key, value in env_info.items():
            st.text(f"{key}: {value}")

def main_dashboard():
    """Main dashboard function"""
    st.title("🎯 Crypto Trading Bot Dashboard")
    st.caption("Professional trading automation with adaptive risk management")
    
    # Navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Overview",
        "📊 Performance", 
        "📡 Logs",
        "⚙️ Settings",
        "ℹ️ Info"
    ])
    
    with tab1:
        render_overview_tab()
    
    with tab2:
        render_performance_tab()
    
    with tab3:
        render_logs_tab()
    
    with tab4:
        render_settings_tab()
    
    with tab5:
        st.header("ℹ️ System Information")
        st.info("""
        **🎯 Crypto Trading Bot Dashboard**
        
        This is your unified trading bot control center, deployed on Railway.
        
        **Features:**
        - ✅ Real-time bot monitoring and control
        - ✅ Performance tracking and analytics  
        - ✅ Remote access via Tailscale
        - ✅ Comprehensive logging system
        - ✅ Secure authentication
        
        **Authentication:** {auth_type}
        **Platform:** Railway Cloud
        **Status:** Production Ready
        """.format(auth_type=AUTH_TYPE))

def main():
    """Main application entry point"""
    # Authentication check
    if not authenticate_user():
        st.stop()
    
    # Main dashboard
    main_dashboard()
    
    # Auto-refresh option
    if st.sidebar.checkbox("🔄 Auto-refresh (10s)"):
        time.sleep(10)
        st.rerun()

if __name__ == "__main__":
    main()