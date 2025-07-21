#!/usr/bin/env python3
"""
Hybrid Quantum Crypto Trading Bot Dashboard
-------------------------------------------
Streamlit App for:
- Portfolio Overview
- Manual Trading
- Auto-Trader Control
- Multi-Strategy Analysis
- Risk Management Settings
- System Health
- Logs
- Advanced Analytics
"""
import os
import sys
import time
import hashlib
import threading
from datetime import datetime, timedelta
import traceback
from auth import require_authentication
from notifications import (
    get_notification_system, 
    notify_system, 
    notify_error, 
    notify_trade,
    notify_trade_close,
    notify_signal,
    send_test_notification,
    get_notification_status
)

# Fix Railway port issue
if 'streamlit' in sys.argv[0] or 'RAILWAY_ENVIRONMENT' in os.environ:
    os.environ.pop('STREAMLIT_SERVER_PORT', None)
    os.environ.pop('STREAMLIT_SERVER_ADDRESS', None)
    
    if 'PORT' in os.environ:
        os.environ['STREAMLIT_SERVER_PORT'] = os.environ['PORT']
        os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psutil
import streamlit as st
import numpy as np

# ✅ Streamlit Config
st.set_page_config(page_title="Hybrid Quantum Trading Bot", layout="wide")

# 🔐 Require authentication
auth = require_authentication()

# Notify system on dashboard access (only once per session)
if 'system_notified' not in st.session_state:
    notify_system("started", f"Dashboard accessed by {auth.admin_username}")
    st.session_state.system_notified = True 
# Add these imports after your existing imports
try:
    from notifications import (
        get_notification_status,
        send_test_notification,
        notify_system,
        notify_error
    )
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    def get_notification_status():
        return {'enabled': False, 'configured': False}
    def send_test_notification():
        return False

# -------------------------
# Enhanced Module Import System
# -------------------------
modules = {}

print("🔄 Starting enhanced module imports...")

# Try to import each module safely
module_imports = [
    ('portfolio_manager', 'PortfolioManager'),
    ('trade_executor', 'TradeExecutor'),
    ('risk_manager', 'RiskManager'),
    ('position_monitor', 'PositionMonitor'),
    ('market_analyzer', 'MarketAnalyzer'),
    ('quantum_trading_integration', 'QuantumTrader'),
    ('quantum_engine', 'QuantumAnalyzer'),
    ('dashboard', 'TradingDashboard'),
    ('ensemble_signal_engine', 'EnsembleSignalEngine'),
    ('binance.client', 'Client')
]

for module_path, class_name in module_imports:
    try:
        if module_path == 'binance.client':
            from binance.client import Client
            modules[class_name] = Client
        else:
            module = __import__(module_path, fromlist=[class_name])
            modules[class_name] = getattr(module, class_name)
        print(f"✅ {class_name} imported successfully")
    except Exception as e:
        modules[class_name] = None
        print(f"⚠️ {class_name} not available: {e}")

print(f"📦 Loaded {sum(1 for v in modules.values() if v is not None)}/{len(modules)} modules")

# -------------------------
# Enhanced Fallback Classes
# -------------------------
class FallbackPortfolioManager:
    def __init__(self):
        self.portfolio = {
            'USDT': {'balance': 10000.0, 'free': 10000.0, 'locked': 0.0, 'price': 1.0, 'value': 10000.0, 'change': 0.0},
            'BTC': {'balance': 0.02, 'free': 0.02, 'locked': 0.0, 'price': 117000.0, 'value': 2340.0, 'change': 2.5},
            'ETH': {'balance': 0.5, 'free': 0.5, 'locked': 0.0, 'price': 4000.0, 'value': 2000.0, 'change': 1.8}
        }
        self._live = False
        self._last_update = None
    
    def get_portfolio(self):
        return self.portfolio
    
    def total_value(self):
        return sum(asset['value'] for asset in self.portfolio.values())
    
    def last_updated(self):
        return datetime.now().strftime("%H:%M:%S")
    
    def refresh_portfolio(self):
        return self.get_portfolio()
    
    def is_live(self):
        return False
    
    def get_connection_status(self):
        return "❌ Using demo data - Portfolio Manager not available"
    
    def get_trade_history(self, symbol=None, limit=10):
        return [
            {"symbol": "BTCUSDT", "side": "BUY", "quantity": 0.0001, "price": 117858.4, "value": 11.79, "commission": 0.01, "time": "11:33:06"},
            {"symbol": "BTCUSDT", "side": "BUY", "quantity": 0.0001, "price": 117861.97, "value": 11.79, "commission": 0.01, "time": "11:31:58"},
            {"symbol": "BTCUSDT", "side": "BUY", "quantity": 0.0001, "price": 117850.01, "value": 11.79, "commission": 0.01, "time": "11:31:58"}
        ]

class FallbackMarketAnalyzer:
    def __init__(self, client=None):
        self.client = client
    
    def get_trading_pairs(self):
        return ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT', 'LINKUSDT', 'AVAXUSDT', 'MATICUSDT']
    
    def get_price(self, symbol):
        prices = {
            'BTCUSDT': 117000.0, 'ETHUSDT': 4000.0, 'BNBUSDT': 600.0, 
            'XRPUSDT': 2.5, 'ADAUSDT': 1.2, 'SOLUSDT': 200.0, 'DOTUSDT': 15.0,
            'LINKUSDT': 25.0, 'AVAXUSDT': 45.0, 'MATICUSDT': 1.1
        }
        return prices.get(symbol, 100.0)
    
    def get_latest_rsi(self, symbol):
        return np.random.uniform(30, 70)
    
    def get_latest_momentum(self, symbol):
        return np.random.uniform(-5, 5)
    
    def get_volatility(self, symbol):
        return np.random.uniform(0.02, 0.08)
    
    def analyze_market_signals(self, symbols):
        signals = {}
        for symbol in symbols:
            signals[symbol] = {
                'signal': np.random.choice(['BUY', 'SELL', 'HOLD']),
                'confidence': np.random.uniform(0.5, 0.9),
                'rsi': self.get_latest_rsi(symbol),
                'price': self.get_price(symbol)
            }
        return signals

class FallbackQuantumAnalyzer:
    def generate_quantum_signal(self, market_data):
        return {
            'decision': np.random.choice(['BUY', 'SELL', 'HOLD']),
            'confidence': np.random.uniform(0.5, 0.8),
            'distribution': {'BUY': 0.4, 'SELL': 0.3, 'HOLD': 0.3}
        }

class FallbackTradeExecutor:
    def __init__(self, client=None, risk_mgr=None, log_callback=None):
        self.active_orders = {}
        self.log_callback = log_callback or (lambda msg: print(msg))
        self.client = client
        self.mock_balance = 1000.0
    
    def manual_trade(self, symbol, qty=None, sl_mult=1.5, tp_mult=3.0, trade_amount_usd=None):
        try:
            mock_prices = {
                'BTCUSDT': 117000.0, 'ETHUSDT': 4000.0, 'BNBUSDT': 600.0,
                'ADAUSDT': 0.45, 'SOLUSDT': 200.0
            }
            
            price = mock_prices.get(symbol, 100.0)
            
            if trade_amount_usd:
                amount = min(trade_amount_usd, self.mock_balance * 0.1)
                qty = amount / price
            else:
                amount = min(50.0, self.mock_balance * 0.05)
                qty = amount / price
            
            self.log_callback(f"📝 DEMO: Would buy {qty:.8f} {symbol} for ${amount:.2f}")
            self.mock_balance -= amount
            
            return f"📝 Demo trade: {qty:.8f} {symbol} for ${amount:.2f}"
            
        except Exception as e:
            return f"📝 Demo trade failed: {e}"
    
    def auto_execute(self, signal, total_balance=None, open_positions=0, sl_mult=1.5, tp_mult=3.0):
        symbol = signal.get("symbol", "BTCUSDT")
        return self.manual_trade(symbol, trade_amount_usd=25.0)
    
    def get_active_orders(self):
        return {}
    
    def cancel_order(self, symbol):
        return f"📝 Demo: Would cancel {symbol}"
    
    def get_connection_status(self):
        return f"📝 Demo mode - Balance: ${self.mock_balance:.2f}"
    
    def get_account_summary(self):
        return {
            'total_usdt': self.mock_balance,
            'tradeable_usdt': self.mock_balance * 0.9,
            'can_trade': True,
            'demo_mode': True
        }

# -------------------------
# Auto-Scanner Class
# -------------------------
class AutoScanner:
    def __init__(self, market_analyzer, scan_interval=300):
        self.market_analyzer = market_analyzer
        self.scan_interval = scan_interval
        self.running = False
        self.thread = None
        self.last_scan_results = {}
        self.scan_count = 0
    
    def start_scanning(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._scan_loop, daemon=True)
            self.thread.start()
    
    def stop_scanning(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def _scan_loop(self):
        while self.running:
            try:
                self.scan_count += 1
                symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT']
                signals = self.market_analyzer.analyze_market_signals(symbols)
                
                strong_signals = {
                    symbol: data for symbol, data in signals.items()
                    if data.get('confidence', 0) > 0.6 and data.get('signal') != 'HOLD'
                }
                
                self.last_scan_results = {
                    'timestamp': datetime.now(),
                    'total_scanned': len(symbols),
                    'signals_found': len(strong_signals),
                    'strong_signals': strong_signals,
                    'scan_number': self.scan_count
                }
                
                time.sleep(self.scan_interval)
                
            except Exception as e:
                print(f"Scanner error: {e}")
                time.sleep(30)
    
    def get_latest_results(self):
        return self.last_scan_results
    
    def is_running(self):
        return self.running

# -------------------------
# Setup Components
# -------------------------
def setup_binance_client():
    """Setup Binance client"""
    if not modules.get('Client'):
        return None, "❌ Binance client not available"
    
    api_key = os.getenv("BINANCE_API_KEY") or os.getenv("BINANCE_TESTNET_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET") or os.getenv("BINANCE_TESTNET_API_SECRET")
    
    if not api_key or not api_secret:
        return None, "⚠️ API keys not configured - using demo mode"
    
    try:
        client = modules['Client'](api_key, api_secret)
        use_testnet = os.getenv("USE_TESTNET", "false").lower() == "true"
        
        if use_testnet:
            client.API_URL = 'https://testnet.binance.vision/api'
        
        client.get_server_time()
        mode = "🧪 TESTNET" if use_testnet else "🚀 LIVE"
        return client, f"✅ Connected to Binance {mode}"
        
    except Exception as e:
        return None, f"❌ Connection failed: {str(e)}"

def initialize_components():
    """Initialize components safely with better error handling"""
    components = {}
    
    # Binance client
    client, client_status = setup_binance_client()
    
    # Check force live mode settings
    force_live = os.getenv("FORCE_LIVE_MODE", "false").lower() == "true"
    has_api_keys = os.getenv("BINANCE_API_KEY") and os.getenv("BINANCE_API_SECRET")
    use_testnet = os.getenv("USE_TESTNET", "false").lower() == "true"
    
    print(f"🔧 Force Live Mode: {force_live}")
    print(f"🔑 Has API Keys: {bool(has_api_keys)}")
    print(f"🧪 Use Testnet: {use_testnet}")
    print(f"📦 Available modules: {[k for k, v in modules.items() if v is not None]}")
    
    # If force live mode but missing requirements, disable it
    if force_live and (not has_api_keys or not client):
        print("⚠️ FORCE_LIVE_MODE=true but missing requirements. Switching to mixed mode.")
        force_live = False
    
    # Risk Manager
    if modules.get('RiskManager'):
        try:
            components['risk_mgr'] = modules['RiskManager'](
                max_risk_percent=0.02, 
                max_positions=5
            )
            print("✅ Risk Manager initialized")
        except Exception as e:
            print(f"⚠️ Risk Manager failed: {e}")
            components['risk_mgr'] = None
    else:
        components['risk_mgr'] = None
    
    # Portfolio Manager - Multiple fallback attempts
    portfolio_mgr = None
    
    # Try Method 1: modules dictionary
    if modules.get('PortfolioManager') and client:
        try:
            portfolio_mgr = modules['PortfolioManager'](
                api_key=os.getenv("BINANCE_API_KEY"),
                api_secret=os.getenv("BINANCE_API_SECRET")
            )
            print("✅ Portfolio Manager (modules) initialized")
        except Exception as e:
            print(f"⚠️ Portfolio Manager (modules) failed: {e}")
    
    # Try Method 2: Direct import
    if not portfolio_mgr and client:
        try:
            from portfolio_manager import PortfolioManager
            portfolio_mgr = PortfolioManager(
                api_key=os.getenv("BINANCE_API_KEY"),
                api_secret=os.getenv("BINANCE_API_SECRET")
            )
            print("✅ Portfolio Manager (direct import) initialized")
        except Exception as e:
            print(f"⚠️ Portfolio Manager (direct import) failed: {e}")
    
    # Try Method 3: Advanced Portfolio Manager
    if not portfolio_mgr:
        try:
            from advanced_portfolio_manager import AdvancedPortfolioManager
            portfolio_mgr = AdvancedPortfolioManager(total_capital=10000.0)
            print("✅ Advanced Portfolio Manager initialized")
        except Exception as e:
            print(f"⚠️ Advanced Portfolio Manager failed: {e}")
    
    # Assign portfolio manager or fallback
    if portfolio_mgr:
        components['portfolio_mgr'] = portfolio_mgr
    else:
        if force_live:
            print("❌ FORCE_LIVE_MODE requires Portfolio Manager but none available")
            print("🔄 Switching to mixed mode...")
            force_live = False
        
        print("📝 Using Fallback Portfolio Manager")
        components['portfolio_mgr'] = FallbackPortfolioManager()
    
    # Market Analyzer - Similar approach
    market_analyzer = None
    
    # Try modules dictionary first
    if modules.get('MarketAnalyzer') and client:
        try:
            market_analyzer = modules['MarketAnalyzer'](client)
            print("✅ Market Analyzer (modules) initialized")
        except Exception as e:
            print(f"⚠️ Market Analyzer (modules) failed: {e}")
    
    # Try direct import
    if not market_analyzer and client:
        try:
            from market_analyzer import MarketAnalyzer
            market_analyzer = MarketAnalyzer(client)
            print("✅ Market Analyzer (direct import) initialized")
        except Exception as e:
            print(f"⚠️ Market Analyzer (direct import) failed: {e}")
    
    # Assign market analyzer or fallback
    if market_analyzer:
        components['market_analyzer'] = market_analyzer
    else:
        if force_live:
            print("❌ FORCE_LIVE_MODE requires Market Analyzer but none available")
            print("🔄 Switching to mixed mode...")
            force_live = False
        
        print("📝 Using Fallback Market Analyzer")
        components['market_analyzer'] = FallbackMarketAnalyzer(client)
    
    # Trade Executor - Multiple attempts
    trade_executor = None
    
    # Try balance-aware executor first
    try:
        from balance_aware_trade_executor import create_balance_aware_executor
        trade_executor = create_balance_aware_executor(
            client, 
            components.get('risk_mgr'),
            log_callback=lambda msg: st.session_state.setdefault("logs", []).append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        )
        print("✅ Balance-Aware Trade Executor initialized")
    except ImportError:
        print("⚠️ Balance-aware executor not found, trying standard...")
        
        # Try standard trade executor
        if modules.get('TradeExecutor'):
            try:
                trade_executor = modules['TradeExecutor'](
                    client, 
                    components.get('risk_mgr'),
                    log_callback=lambda msg: st.session_state.setdefault("logs", []).append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
                )
                print("✅ Standard Trade Executor initialized")
            except Exception as e:
                print(f"⚠️ Standard Trade Executor failed: {e}")
        
        # Try direct import
        if not trade_executor:
            try:
                from trade_executor import TradeExecutor
                trade_executor = TradeExecutor(
                    client, 
                    components.get('risk_mgr'),
                    log_callback=lambda msg: st.session_state.setdefault("logs", []).append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
                )
                print("✅ Trade Executor (direct import) initialized")
            except Exception as e:
                print(f"⚠️ Trade Executor (direct import) failed: {e}")
    
    except Exception as e:
        print(f"⚠️ Balance-aware executor failed: {e}")
    
    # Assign trade executor or fallback
    if trade_executor:
        components['trade_exec'] = trade_executor
    else:
        if force_live:
            print("❌ FORCE_LIVE_MODE requires Trade Executor but none available")
            print("🔄 Switching to mixed mode...")
            force_live = False
        
        print("📝 Using Fallback Trade Executor")
        components['trade_exec'] = FallbackTradeExecutor(
            client, 
            components.get('risk_mgr'),
            log_callback=lambda msg: st.session_state.setdefault("logs", []).append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        )
    
    # Quantum Components (optional)
    if modules.get('QuantumTrader') and client:
        try:
            components['quantum_trader'] = modules['QuantumTrader'](client)
            print("✅ Quantum Trader initialized")
        except Exception as e:
            print(f"⚠️ Quantum Trader failed: {e}")
            components['quantum_trader'] = None
    else:
        components['quantum_trader'] = None
    
    if modules.get('QuantumAnalyzer'):
        try:
            components['quantum_analyzer'] = modules['QuantumAnalyzer']()
            print("✅ Quantum Analyzer initialized")
        except Exception as e:
            print(f"⚠️ Quantum Analyzer failed: {e}")
            components['quantum_analyzer'] = FallbackQuantumAnalyzer()
    else:
        components['quantum_analyzer'] = FallbackQuantumAnalyzer()
    
    # Other components (optional)
    components['position_monitor'] = None
    components['analytics_dashboard'] = None
    components['ensemble_engine'] = None
    
    # Final status report
    live_components = []
    fallback_components = []
    
    for name, component in components.items():
        if component is None:
            continue
        elif 'Fallback' in str(type(component)):
            fallback_components.append(name)
        else:
            live_components.append(name)
    
    print(f"🎯 Component Status:")
    print(f"  ✅ Live components: {len(live_components)} - {live_components}")
    print(f"  📝 Fallback components: {len(fallback_components)} - {fallback_components}")
    
    if force_live and len(live_components) >= 3:  # Need at least 3 core components
        print("🚀 LIVE MODE: All required components initialized successfully")
    elif len(live_components) > 0:
        print("🔄 MIXED MODE: Using combination of live and fallback components")
        print("💡 This allows live API trading with demo backup features")
    else:
        print("📝 DEMO MODE: Using fallback components")
    
    return components, client, client_status

# ✅ CRITICAL FIX #1: ADD COMPONENT INITIALIZATION
print("🚀 Initializing all components...")
components, client, client_status = initialize_components()

# ✅ CRITICAL FIX #2: MOVE SESSION STATE INITIALIZATION AFTER COMPONENTS
if "sl_mult" not in st.session_state:
    st.session_state["sl_mult"] = 1.5
if "tp_mult" not in st.session_state:
    st.session_state["tp_mult"] = 3.0
if "logs" not in st.session_state:
    st.session_state["logs"] = [
        f"[{datetime.now().strftime('%H:%M:%S')}] Bot initialized successfully",
        f"[{datetime.now().strftime('%H:%M:%S')}] {client_status}",
        f"[{datetime.now().strftime('%H:%M:%S')}] Dashboard loaded"
    ]
if "auto_scanner" not in st.session_state:
    st.session_state["auto_scanner"] = AutoScanner(components['market_analyzer'])

# -------------------------
# Helper Functions
# -------------------------
def get_system_health():
    return {
        "CPU": f"{psutil.cpu_percent()}%",
        "Memory": f"{psutil.virtual_memory().percent}%",
        "Threads": threading.active_count()
    }

def display_scanner_results():
    """Display auto-scanner results"""
    auto_scanner = st.session_state["auto_scanner"]
    
    st.subheader("🔍 Auto-Scanner Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if auto_scanner.is_running():
            st.success("🟢 Scanner Running")
        else:
            st.error("🔴 Scanner Stopped")
    
    with col2:
        results = auto_scanner.get_latest_results()
        if results:
            st.metric("Signals Found", results.get('signals_found', 0))
        else:
            st.metric("Signals Found", 0)
    
    with col3:
        if results:
            st.metric("Last Scan", f"#{results.get('scan_number', 0)}")
        else:
            st.metric("Last Scan", "None")
    
    # Scanner controls
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("▶️ Start Scanner" if not auto_scanner.is_running() else "🛑 Stop Scanner", key="scanner_toggle"):
            if auto_scanner.is_running():
                auto_scanner.stop_scanning()
                st.success("Scanner stopped")
            else:
                auto_scanner.start_scanning()
                st.success("Scanner started")
            st.rerun()
    
    with col2:
        if st.button("🔄 Manual Scan", key="manual_scan"):
            symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
            signals = components['market_analyzer'].analyze_market_signals(symbols)
            st.json(signals)

    # Display recent signals
    results = auto_scanner.get_latest_results()
    if results and results.get('strong_signals'):
        st.subheader("📊 Latest Strong Signals")
        
        signals_df = []
        for symbol, data in results['strong_signals'].items():
            signals_df.append({
                'Symbol': symbol,
                'Signal': data.get('signal', 'HOLD'),
                'Confidence': f"{data.get('confidence', 0):.2f}",
                'RSI': f"{data.get('rsi', 50):.1f}",
                'Price': f"${data.get('price', 0):.2f}"
            })
        
        if signals_df:
            df = pd.DataFrame(signals_df)
            st.dataframe(df, use_container_width=True)
    else:
        st.info("🔍 No strong signals detected. Scanner will update automatically.")

# -------------------------
# Company Branding Sidebar
# -------------------------
with st.sidebar:
    st.markdown(
        """
        <div style='text-align: center; margin-bottom: 20px;'>
            <img src='https://static.wixstatic.com/media/80aa29_3bdfcbab4dd34671915e3b66b0b596e4~mv2.jpeg/v1/fill/w_146,h_104,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/LRC_1719585575250.jpeg' 
                 width='120' style='border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'/>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    st.markdown(
        """
        <div style='text-align: center; padding: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 10px; margin-bottom: 20px; color: white;'>
            <h3 style='color: white; margin: 0;'>🧠 Quantum Trading Bot</h3>
            <p style='color: #f0f0f0; margin: 5px 0; font-size: 14px;'>Advanced AI Trading Platform</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    st.markdown(
        """
        <div style='background: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid #667eea;'>
            <h4 style='margin-top: 0; color: #333;'>📊 Rondanini Publishing Ltd.</h4>
            <p style='margin: 5px 0; font-size: 12px; color: #666;'>© 2025 All Rights Reserved</p>
            <p style='margin: 5px 0; font-size: 11px; color: #888;'>Quantum-Enhanced Trading Solutions</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    
    # Quick Stats
    st.subheader("📈 Quick Stats")
    
    if client:
        st.success("🟢 API Connected")
    else:
        st.error("🔴 API Disconnected")
    
    mode = "🧪 TESTNET" if os.getenv("USE_TESTNET", "false").lower() == "true" else "🚀 LIVE"
    if "TESTNET" in mode:
        st.info(f"Mode: {mode}")
    else:
        st.warning(f"Mode: {mode}")
    
    try:
        total_value = components['portfolio_mgr'].total_value()
        st.metric("Portfolio Value", f"${total_value:,.2f}")
    except:
        st.metric("Portfolio Value", "Loading...")
    
    # Active Scanner
    scanner = st.session_state.get("auto_scanner")
    if scanner and scanner.is_running():
        st.success("🟢 Scanner Active")
        results = scanner.get_latest_results()
        if results:
            st.metric("Signals Found", results.get('signals_found', 0))
    else:
        st.warning("🟡 Scanner Inactive")
    
    st.markdown("---")
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    
    if st.button("🔄 Refresh Portfolio", help="Update portfolio data", key="sidebar_refresh_portfolio"):
        try:
            with st.spinner("Refreshing..."):
                components['portfolio_mgr'].refresh_portfolio()
            st.success("✅ Refreshed!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error: {e}")
    
    # Scanner Toggle
    scanner = st.session_state.get("auto_scanner")
    if scanner:
        if scanner.is_running():
            if st.button("🛑 Stop Scanner", help="Stop the market scanner", key="sidebar_stop_scanner"):
                scanner.stop_scanning()
                st.success("Scanner stopped")
                st.rerun()
        else:
            if st.button("▶️ Start Scanner", help="Start the market scanner", key="sidebar_start_scanner"):
                scanner.start_scanning()
                st.success("Scanner started")
                st.rerun()
    
    st.markdown("---")
    
    # System Info
    st.subheader("🔧 System Info")
    try:
        health = get_system_health()
        st.metric("CPU", health["CPU"])
        st.metric("Memory", health["Memory"])
        st.metric("Threads", health["Threads"])
    except:
        st.error("System info unavailable")
    
    st.markdown("---")
    
    # Footer in Sidebar
    st.markdown(
        """
        <div style='text-align: center; padding: 10px; font-size: 10px; color: #888;'>
            <p>⚠️ Trading involves risk<br>
            Use at your own discretion</p>
            <p style='margin-top: 10px;'>
                <strong>Rondanini Publishing Ltd.</strong><br>
                Advanced Trading Solutions<br>
                Est. 2025
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )

# -------------------------
# Main Header
# -------------------------
st.markdown(
    """
    <div style='text-align: center; padding: 20px 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border-radius: 15px; margin-bottom: 20px; color: white;'>
        <h1 style='color: white; margin: 0; font-size: 2.5em;'>
            🧠 Hybrid Quantum Crypto Trading Bot
        </h1>
        <p style='color: #f0f0f0; margin: 10px 0; font-size: 1.2em;'>
            Advanced Crypto Trading with Technical, ML & Quantum Strategies
        </p>
        <div style='margin-top: 15px;'>
            <span style='background: rgba(255,255,255,0.2); padding: 5px 15px; border-radius: 20px; margin: 0 5px;'>
                ⚛️ Quantum Analytics
            </span>
            <span style='background: rgba(255,255,255,0.2); padding: 5px 15px; border-radius: 20px; margin: 0 5px;'>
                🤖 AI Trading
            </span>
            <span style='background: rgba(255,255,255,0.2); padding: 5px 15px; border-radius: 20px; margin: 0 5px;'>
                📊 Advanced Analytics
            </span>
        </div>
        <p style='margin-top: 15px; font-size: 0.9em; color: #e0e0e0;'>
            Powered by <strong>Rondanini Publishing Ltd.</strong> • © 2025
        </p>
    </div>
    """, 
    unsafe_allow_html=True
)

# Connection Status
col1, col2 = st.columns([3, 1])
with col1:
    st.info(client_status)
with col2:
    if st.button("🔄 Refresh", key="main_refresh"):
        st.rerun()

# -------------------------
# Main Tabs
# -------------------------
tabs = st.tabs([
    "📊 Portfolio", "✋ Manual Trading", "🤖 Auto-Trader",
    "⚛ Multi-Strategy", "🛠 Settings", "🩺 Health", "📜 Logs", "📈 Analytics"
])

# -------------------------
# Enhanced Portfolio Tab
# -------------------------
with tabs[0]:
    st.header("📊 Portfolio Overview")
    
    # Add refresh button and connection status
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.info(components['portfolio_mgr'].get_connection_status())
    with col2:
        if st.button("🔄 Refresh Portfolio", key="portfolio_refresh"):
            with st.spinner("Refreshing..."):
                components['portfolio_mgr'].refresh_portfolio()
            st.success("Portfolio refreshed!")
            st.rerun()
    with col3:
        st.caption(f"Last updated: {components['portfolio_mgr'].last_updated()}")
    
    try:
        portfolio = components['portfolio_mgr'].get_portfolio()
        if portfolio:
            total_usd = sum(v["value"] for v in portfolio.values())
            
            # Main metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Value (USD)", f"${total_usd:,.2f}")
            with col2:
                mode = "🧪 TESTNET" if os.getenv("USE_TESTNET", "false").lower() == "true" else "🚀 LIVE"
                st.metric("Trading Mode", mode)
            with col3:
                assets_count = len([k for k, v in portfolio.items() if v['balance'] > 0])
                st.metric("Active Assets", assets_count)
            with col4:
                live_status = "🟢 Live" if hasattr(components['portfolio_mgr'], 'is_live') and components['portfolio_mgr'].is_live() else "🔴 Demo"
                st.metric("Data Source", live_status)

            # Enhanced portfolio table
            portfolio_data = []
            for asset, data in portfolio.items():
                portfolio_data.append({
                    "Asset": asset,
                    "Balance": f"{data['balance']:.8f}".rstrip('0').rstrip('.'),
                    "Free": f"{data.get('free', data['balance']):.8f}".rstrip('0').rstrip('.'),
                    "Locked": f"{data.get('locked', 0):.8f}".rstrip('0').rstrip('.'),
                    "Price (USD)": f"${data['price']:.4f}",
                    "Value (USD)": f"${data['value']:.2f}",
                    "24h Change": f"{data.get('change_24h', 0):.2f}%"
                })
            
            df = pd.DataFrame(portfolio_data)
            
            # Color code the dataframe
            def color_change(val):
                if '%' in str(val):
                    try:
                        num_val = float(val.replace('%', ''))
                        if num_val > 0:
                            return 'background-color: #90EE90'  # Light green
                        elif num_val < 0:
                            return 'background-color: #FFB6C1'  # Light red
                    except:
                        pass
                return ''
            
            styled_df = df.style.applymap(color_change, subset=['24h Change'])
            st.dataframe(styled_df, use_container_width=True)
            
            # Portfolio allocation chart (only for assets with significant value)
            significant_assets = {k: v for k, v in portfolio.items() if v['value'] > 1.0}
            if len(significant_assets) > 1:
                fig = px.pie(
                    values=[data['value'] for data in significant_assets.values()],
                    names=list(significant_assets.keys()),
                    title="Portfolio Allocation (Assets > $1)"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Recent trade history
            if hasattr(components['portfolio_mgr'], 'get_trade_history'):
                st.subheader("📈 Recent Trade History")
                trades = components['portfolio_mgr'].get_trade_history(limit=10)
                
                if trades:
                    trade_df = pd.DataFrame(trades)
                    
                    # Color code trades
                    def color_trades(val):
                        if val == 'BUY':
                            return 'background-color: #90EE90'
                        elif val == 'SELL':
                            return 'background-color: #FFB6C1'
                        return ''
                    
                    if 'side' in trade_df.columns:
                        styled_trade_df = trade_df.style.applymap(color_trades, subset=['side'])
                        st.dataframe(styled_trade_df, use_container_width=True)
                    else:
                        st.dataframe(trade_df, use_container_width=True)
                else:
                    st.info("No recent trades found")
            
        else:
            st.warning("⚠️ No portfolio data available.")
            
    except Exception as e:
        st.error(f"Portfolio fetch error: {e}")
        st.code(traceback.format_exc())

# -------------------------
# Manual Trading Tab
# -------------------------
with tabs[1]:
    st.header("✋ Manual Trading")
    
    if components['market_analyzer']:
        col1, col2 = st.columns(2)
        
        with col1:
            pairs = components['market_analyzer'].get_trading_pairs()
            symbol = st.selectbox("Select Trading Pair", pairs, key="manual_symbol_select")
            
            # Get current price and additional info
            current_price = components['market_analyzer'].get_price(symbol)
            rsi = components['market_analyzer'].get_latest_rsi(symbol)
            momentum = components['market_analyzer'].get_latest_momentum(symbol)
            
            st.info(f"Current Price: ${current_price:,.4f}")
            
            # Technical indicators
            col_rsi, col_mom = st.columns(2)
            with col_rsi:
                st.metric("RSI", f"{rsi:.1f}", 
                         delta="Oversold" if rsi < 30 else "Overbought" if rsi > 70 else "Neutral")
            with col_mom:
                st.metric("Momentum", f"{momentum:.2f}%", 
                         delta="Bullish" if momentum > 0 else "Bearish")
        
        with col2:
            qty = st.number_input("Quantity", min_value=0.0001, step=0.0001, format="%.6f", key="manual_quantity")
            
            # Calculate trade value and fees
            if qty > 0:
                trade_value = qty * current_price
                est_fee = trade_value * 0.001  # 0.1% fee estimate
                st.info(f"Trade Value: ${trade_value:.2f}")
                st.caption(f"Est. Fee: ${est_fee:.4f}")
            else:
                st.warning("⚠️ Enter quantity")
            
            # Risk management
            use_sl_tp = st.checkbox("Use Stop Loss / Take Profit", value=True, key="manual_sl_tp")
            if use_sl_tp:
                col_sl, col_tp = st.columns(2)
                with col_sl:
                    sl_pct = st.number_input("Stop Loss %", min_value=1.0, value=5.0, max_value=20.0, key="manual_sl")
                with col_tp:
                    tp_pct = st.number_input("Take Profit %", min_value=1.0, value=10.0, max_value=50.0, key="manual_tp")
        
        # Enhanced trade execution with notifications
        def execute_manual_trade_with_notifications(symbol, quantity, side, price):
            try:
                result = components['trade_exec'].manual_trade(symbol, quantity, st.session_state["sl_mult"], st.session_state["tp_mult"])
                if "✅" in result or "Demo" in result:
                    trade_data = {
                        'symbol': symbol,
                        'side': side,
                        'quantity': quantity,
                        'price': price,
                        'value': quantity * price,
                        'timestamp': datetime.now().isoformat(),
                        'execution_type': 'manual'
                    }
                    notify_trade(trade_data)
                    st.success("✅ Trade executed and notification sent!")
                return result
            except Exception as e:
                notify_error("Manual Trade Execution", str(e), {'symbol': symbol, 'quantity': quantity, 'side': side})
                return f"❌ Trade failed: {e}"

        # Trade execution
        if st.button("🚀 Execute Trade", type="primary", key="manual_execute"):
            if qty > 0:
                try:
                    total_balance = components['portfolio_mgr'].total_value()
                    open_positions = 0  # Fallback
                    
                    if components['risk_mgr']:
                        validation = components['risk_mgr'].validate_trade(symbol, qty, current_price, total_balance, open_positions)
                        if validation["status"]:
                            result = execute_manual_trade_with_notifications(symbol, qty, "BUY", current_price)
                            st.success(f"✅ {result}")
                        else:
                            st.error(f"❌ Trade blocked: {validation['reason']}")
                    else:
                        result = execute_manual_trade_with_notifications(symbol, qty, "BUY", current_price)
                        st.success(f"✅ {result}")
                        
                except Exception as e:
                    st.error(f"❌ Trade execution failed: {e}")
            else:
                st.warning("⚠️ Please enter a valid quantity")
    else:
        st.error("❌ Market analyzer not available. Manual trading disabled.")

# -------------------------
# Auto-Trader Tab
# -------------------------
with tabs[2]:
    st.header("🤖 Auto-Trader Control")
    
    # Auto-trading status
    auto_trade_enabled = os.getenv("AUTO_TRADE_ENABLED", "false").lower() == "true"
    
    col1, col2 = st.columns(2)
    with col1:
        if auto_trade_enabled:
            st.success("✅ Auto-trading is ENABLED in environment")
        else:
            st.warning("⚠️ Auto-trading is DISABLED in environment")
    
    with col2:
        # Auto-trade toggle (for demo)
        if st.button("🔄 Toggle Auto-Trading (Demo)", key="auto_trade_toggle"):
            st.info("Auto-trading toggle activated (demo mode)")
    
    # Scanner interface
    display_scanner_results()
    
    # Active orders display
    st.subheader("📋 Active Orders")
    if hasattr(components['trade_exec'], 'active_orders'):
        if components['trade_exec'].active_orders:
            orders_df = pd.DataFrame(components['trade_exec'].active_orders)
            st.dataframe(orders_df, use_container_width=True)
        else:
            st.info("No active orders")
    else:
        st.info("Order tracking not available in demo mode")

# -------------------------
# Multi-Strategy Tab (FIXED - No Session State Conflicts)
# -------------------------
with tabs[3]:
    st.header("⚛ Multi-Strategy Market Scanner")
    st.caption("Quantum + ML + Technical Analysis for ALL Trading Pairs")
    
    # -------------------------------------------------
    # Session-state init (runs once) - NO REASSIGNMENT IN WIDGET CALLBACKS
    # -------------------------------------------------
    if 'weight_quantum' not in st.session_state:
        st.session_state['weight_quantum'] = 30
    if 'weight_ml' not in st.session_state:
        st.session_state['weight_ml'] = 30
    if 'weight_technical' not in st.session_state:
        st.session_state['weight_technical'] = 40
    if 'multi_min_conf' not in st.session_state:
        st.session_state['multi_min_conf'] = 0.65
    if 'multi_max_pairs' not in st.session_state:
        st.session_state['multi_max_pairs'] = 20
    if 'multi_scan_mode' not in st.session_state:
        st.session_state['multi_scan_mode'] = "Top Volume Pairs"
    if 'multi_show_only_signals' not in st.session_state:
        st.session_state['multi_show_only_signals'] = True
    if 'latest_signals' not in st.session_state:
        st.session_state['latest_signals'] = []
    if 'last_scan_time' not in st.session_state:
        st.session_state['last_scan_time'] = None
    if 'manual_scan_requested' not in st.session_state:
        st.session_state['manual_scan_requested'] = False
    
    # -------------------------------------------------
    # Configuration Section - Using widget return values, NOT session_state assignment
    # -------------------------------------------------
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("**Strategy Weights (Auto-balanced to 100%)**")
        
        subcol1, subcol2, subcol3 = st.columns(3)
        with subcol1:
            quantum_weight = st.slider(
                "Quantum Weight", 0, 100, st.session_state['weight_quantum'],
                key="multi_quantum_weight_slider"
            )
        with subcol2:
            ml_weight = st.slider(
                "ML Weight", 0, 100, st.session_state['weight_ml'],
                key="multi_ml_weight_slider"
            )
        with subcol3:
            technical_weight = st.slider(
                "Technical Weight", 0, 100, st.session_state['weight_technical'],
                key="multi_technical_weight_slider"
            )
        
        # Auto-balance weights to exactly 100
        total = quantum_weight + ml_weight + technical_weight
        if total <= 0:
            quantum_weight, ml_weight, technical_weight = 0, 0, 100
        else:
            quantum_weight = int((quantum_weight / total) * 100)
            ml_weight = int((ml_weight / total) * 100)
            technical_weight = 100 - quantum_weight - ml_weight
        
        # Update session state ONLY when values actually change
        if st.session_state['weight_quantum'] != quantum_weight:
            st.session_state['weight_quantum'] = quantum_weight
        if st.session_state['weight_ml'] != ml_weight:
            st.session_state['weight_ml'] = ml_weight
        if st.session_state['weight_technical'] != technical_weight:
            st.session_state['weight_technical'] = technical_weight
        
        # Visual weight display
        weight_col1, weight_col2, weight_col3 = st.columns(3)
        with weight_col1:
            st.metric("Quantum", f"{quantum_weight}%")
            st.progress(quantum_weight / 100)
        with weight_col2:
            st.metric("ML", f"{ml_weight}%")
            st.progress(ml_weight / 100)
        with weight_col3:
            st.metric("Technical", f"{technical_weight}%")
            st.progress(technical_weight / 100)
        
        # Presets - Use callbacks to update session state
        preset_col1, preset_col2, preset_col3, preset_col4 = st.columns(4)
        with preset_col1:
            if st.button("⚛️ Quantum Focus", key="preset_quantum_focus"):
                st.session_state['weight_quantum'] = 60
                st.session_state['weight_ml'] = 20
                st.session_state['weight_technical'] = 20
                st.rerun()
        with preset_col2:
            if st.button("🤖 ML Focus", key="preset_ml_focus"):
                st.session_state['weight_quantum'] = 20
                st.session_state['weight_ml'] = 60
                st.session_state['weight_technical'] = 20
                st.rerun()
        with preset_col3:
            if st.button("📊 Technical Focus", key="preset_technical_focus"):
                st.session_state['weight_quantum'] = 20
                st.session_state['weight_ml'] = 20
                st.session_state['weight_technical'] = 60
                st.rerun()
        with preset_col4:
            if st.button("⚖️ Balanced", key="preset_balanced_weights"):
                st.session_state['weight_quantum'] = 33
                st.session_state['weight_ml'] = 33
                st.session_state['weight_technical'] = 34
                st.rerun()
    
    with col2:
        # ✅ CRITICAL FIX: Use widget return values and update session state conditionally
        min_confidence = st.slider(
            "Min Confidence", 0.5, 1.0, float(st.session_state['multi_min_conf']),
            0.01, key="multi_min_confidence_slider"
        )
        
        max_pairs = st.slider(
            "Max Pairs to Scan", 5, 50, int(st.session_state['multi_max_pairs']),
            5, key="multi_max_pairs_slider"
        )
        
        scan_mode = st.selectbox(
            "Scan Mode",
            ["Top Volume Pairs", "Portfolio + Major Pairs", "All USDT Pairs", "Custom Selection"],
            key="multi_scan_mode_select",
            index=[
                "Top Volume Pairs",
                "Portfolio + Major Pairs", 
                "All USDT Pairs",
                "Custom Selection"
            ].index(st.session_state['multi_scan_mode'])
        )
        
        # Update session state only when values change
        if st.session_state['multi_min_conf'] != min_confidence:
            st.session_state['multi_min_conf'] = min_confidence
        if st.session_state['multi_max_pairs'] != max_pairs:
            st.session_state['multi_max_pairs'] = max_pairs
        if st.session_state['multi_scan_mode'] != scan_mode:
            st.session_state['multi_scan_mode'] = scan_mode
    
    # -------------------------------------------------
    # Pair Selection Logic
    # -------------------------------------------------
    all_pairs = components['market_analyzer'].get_trading_pairs()
    max_pairs_to_scan = st.session_state['multi_max_pairs']
    scan_mode_selected = st.session_state['multi_scan_mode']
    
    if scan_mode_selected == "Top Volume Pairs":
        trading_pairs = all_pairs[:max_pairs_to_scan]
    elif scan_mode_selected == "Portfolio + Major Pairs":
        try:
            portfolio = components['portfolio_mgr'].get_portfolio()
            portfolio_pairs = [
                f"{asset}USDT" for asset in portfolio.keys() if asset not in ["USDT", "BUSD"]
            ]
        except Exception:
            portfolio_pairs = []
        major_pairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT']
        trading_pairs = list(dict.fromkeys(portfolio_pairs + major_pairs))[:max_pairs_to_scan]
    elif scan_mode_selected == "All USDT Pairs":
        trading_pairs = [pair for pair in all_pairs if pair.endswith('USDT')][:max_pairs_to_scan]
    else:  # Custom Selection
        trading_pairs = st.multiselect(
            "Select Trading Pairs",
            all_pairs,
            default=['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
            key="multi_custom_pairs_multiselect"
        )[:max_pairs_to_scan]
    
    # -------------------------------------------------
    # Scan Controls
    # -------------------------------------------------
    scan_col1, scan_col2, scan_col3 = st.columns(3)
    with scan_col1:
        if st.button("🔍 Scan All Pairs", type="primary", key="multi_scan_all_button"):
            st.session_state['manual_scan_requested'] = True
    with scan_col2:
        if st.button("🔄 Refresh Signals", key="multi_refresh_signals_button"):
            st.session_state['manual_scan_requested'] = True
    with scan_col3:
        show_only_signals = st.checkbox(
            "Show Only Strong Signals",
            value=st.session_state['multi_show_only_signals'],
            key="multi_show_only_signals_checkbox"
        )
        # Update session state only when value changes
        if st.session_state['multi_show_only_signals'] != show_only_signals:
            st.session_state['multi_show_only_signals'] = show_only_signals
    
    # -------------------------------------------------
    # Scanning Process
    # -------------------------------------------------
    if st.session_state.get('manual_scan_requested', False):
        progress_bar = st.progress(0.0)
        status_text = st.empty()
        signals_data = []
        
        for i, symbol in enumerate(trading_pairs):
            try:
                progress = (i + 1) / len(trading_pairs)
                progress_bar.progress(progress)
                status_text.text(f"Analyzing {symbol}... ({i+1}/{len(trading_pairs)})")
                
                # Pull data
                rsi = components['market_analyzer'].get_latest_rsi(symbol)
                momentum = components['market_analyzer'].get_latest_momentum(symbol)
                volatility = components['market_analyzer'].get_volatility(symbol)
                price = components['market_analyzer'].get_price(symbol)
                
                # Heuristic signal logic
                quantum_decision = "HOLD"
                quantum_conf = 0.5
                if rsi < 30 and momentum > 3:
                    quantum_decision = "BUY"
                    quantum_conf = 0.75
                elif rsi > 70 and momentum < -3:
                    quantum_decision = "SELL"
                    quantum_conf = 0.75
                elif abs(momentum) > 5:
                    quantum_decision = "BUY" if momentum > 0 else "SELL"
                    quantum_conf = 0.65
                
                # ML simulation (more conservative)
                ml_decision = quantum_decision
                ml_conf = quantum_conf * 0.9
                
                # Technical analysis
                tech_decision = quantum_decision
                tech_conf = min(quantum_conf * 1.1, 1.0)
                
                # Final ensemble decision using current weights
                weights = {
                    "quantum": st.session_state['weight_quantum'],
                    "ml": st.session_state['weight_ml'],
                    "technical": st.session_state['weight_technical']
                }
                final_conf = (
                    quantum_conf * weights['quantum'] +
                    ml_conf * weights['ml'] +
                    tech_conf * weights['technical']
                ) / 100.0
                
                min_conf_threshold = st.session_state['multi_min_conf']
                final_decision = quantum_decision if final_conf >= min_conf_threshold else "HOLD"
                
                signal = {
                    "symbol": symbol,
                    "quantum": {"decision": quantum_decision, "confidence": quantum_conf},
                    "ml": {"decision": ml_decision, "confidence": ml_conf},
                    "technical": {"decision": tech_decision, "confidence": tech_conf},
                    "final": {"decision": final_decision, "confidence": final_conf},
                    "price": price,
                    "rsi": rsi,
                    "momentum": momentum,
                    "volatility": volatility
                }
                signals_data.append(signal)
                
                # Notify strong signals
                if final_decision in ("BUY", "SELL") and final_conf >= 0.8:
                    try:
                        notify_signal({
                            'symbol': symbol,
                            'signal': final_decision,
                            'confidence': final_conf,
                            'price': price,
                            'rsi': rsi,
                            'momentum': momentum,
                            'volatility': volatility
                        })
                    except Exception:
                        pass
            except Exception as e:
                st.error(f"Error analyzing {symbol}: {e}")
        
        progress_bar.empty()
        status_text.empty()
        
        st.session_state['latest_signals'] = signals_data
        st.session_state['manual_scan_requested'] = False
        st.session_state['last_scan_time'] = datetime.now()
    
    # -------------------------------------------------
    # Display Results
    # -------------------------------------------------
    signals_data = st.session_state.get('latest_signals', [])
    min_conf_display = st.session_state['multi_min_conf']
    show_only_signals_display = st.session_state['multi_show_only_signals']
    
    if signals_data:
        # Filter
        if show_only_signals_display:
            filtered_signals = [
                s for s in signals_data
                if s['final']['decision'] != 'HOLD' and s['final']['confidence'] >= min_conf_display
            ]
        else:
            filtered_signals = signals_data
        
        if filtered_signals:
            st.subheader(f"📊 Analysis Results ({len(filtered_signals)} pairs)")
            
            # DataFrame
            signals_df = []
            for s in filtered_signals:
                signals_df.append({
                    "Symbol": s["symbol"],
                    "Price": f"${s.get('price', 0):.4f}",
                    "Final Signal": s['final']['decision'],
                    "Confidence": f"{s['final']['confidence']:.3f}",
                    "Quantum": f"{s['quantum']['decision']} ({s['quantum']['confidence']:.2f})",
                    "ML": f"{s['ml']['decision']} ({s['ml']['confidence']:.2f})",
                    "Technical": f"{s['technical']['decision']} ({s['technical']['confidence']:.2f})",
                    "RSI": f"{s.get('rsi', 50):.1f}",
                    "Momentum": f"{s.get('momentum', 0):.2f}%",
                    "Volatility": f"{s.get('volatility', 0):.3f}"
                })
            df = pd.DataFrame(signals_df)
            
            def color_signals(val):
                if 'BUY' in val:
                    return 'background-color: #90EE90'
                if 'SELL' in val:
                    return 'background-color: #FFB6C1'
                return 'background-color: #F0F0F0'
            
            styled_df = df.style.applymap(color_signals, subset=['Final Signal'])
            st.dataframe(styled_df, use_container_width=True)
            
            # -------------------------------------------------
            # Quick Trading Interface
            # -------------------------------------------------
            st.subheader("⚡ Quick Trading Interface")
            
            import hashlib, time
            def create_unique_button_key(action, symbol, index):
                unique_string = f"{action}_{symbol}_{index}_{int(time.time()*1000)}"
                return f"{action}_{hashlib.md5(unique_string.encode()).hexdigest()[:8]}"
            
            strong_buy_signals = [s for s in filtered_signals if s['final']['decision'] == 'BUY']
            strong_sell_signals = [s for s in filtered_signals if s['final']['decision'] == 'SELL']
            
            if strong_buy_signals or strong_sell_signals:
                trade_col1, trade_col2 = st.columns(2)
                
                with trade_col1:
                    if strong_buy_signals:
                        st.write("**🟢 Strong BUY Signals:**")
                        for i, sig in enumerate(strong_buy_signals[:5]):
                            _sym = sig['symbol']
                            _conf = sig['final']['confidence']
                            _price = sig.get('price', 0)
                            if _price > 0:
                                sc1, sc2 = st.columns([3, 1])
                                with sc1:
                                    st.write(f"**{_sym}** - ${_price:.4f} (Conf: {_conf:.3f})")
                                with sc2:
                                    if st.button("🚀 Buy", key=create_unique_button_key("multi_buy", _sym, i)):
                                        st.session_state['selected_trade'] = {
                                            'symbol': _sym,
                                            'action': 'BUY',
                                            'price': _price,
                                            'confidence': _conf,
                                            'timestamp': datetime.now(),
                                            'source': 'multi_strategy'
                                        }
                                        st.success(f"Selected {_sym} for BUY")
                                        st.rerun()
                
                with trade_col2:
                    if strong_sell_signals:
                        st.write("**🔴 Strong SELL Signals:**")
                        for i, sig in enumerate(strong_sell_signals[:5]):
                            _sym = sig['symbol']
                            _conf = sig['final']['confidence']
                            _price = sig.get('price', 0)
                            if _price > 0:
                                sc1, sc2 = st.columns([3, 1])
                                with sc1:
                                    st.write(f"**{_sym}** - ${_price:.4f} (Conf: {_conf:.3f})")
                                with sc2:
                                    if st.button("📉 Sell", key=create_unique_button_key("multi_sell", _sym, i)):
                                        st.session_state['selected_trade'] = {
                                            'symbol': _sym,
                                            'action': 'SELL',
                                            'price': _price,
                                            'confidence': _conf,
                                            'timestamp': datetime.now(),
                                            'source': 'multi_strategy'
                                        }
                                        st.success(f"Selected {_sym} for SELL")
                                        st.rerun()
            
            # -------------------------------------------------
            # Execute Selected Trade
            # -------------------------------------------------
            if (
                'selected_trade' in st.session_state and
                st.session_state['selected_trade'].get('source') == 'multi_strategy'
            ):
                trade = st.session_state['selected_trade']
                st.divider()
                st.subheader(f"🎯 Execute Trade: {trade['action']} {trade['symbol']}")
                
                exec_col1, exec_col2, exec_col3 = st.columns(3)
                with exec_col1:
                    st.info(f"**Symbol:** {trade['symbol']}")
                    st.info(f"**Action:** {trade['action']}")
                    st.info(f"**Price:** ${trade['price']:.4f}")
                    st.info(f"**Confidence:** {trade['confidence']:.3f}")
                
                with exec_col2:
                    quantity = st.number_input(
                        "Quantity",
                        min_value=0.0001,
                        step=0.0001,
                        format="%.6f",
                        key="multi_strategy_quantity_input"
                    )
                    if quantity > 0:
                        trade_value = quantity * trade['price']
                        est_fee = trade_value * 0.001
                        st.info(f"Trade Value: ${trade_value:.2f}")
                        st.caption(f"Est. Fee: ${est_fee:.2f}")
                
                with exec_col3:
                    if st.button("🎯 Execute Trade", type="primary", key="multi_strategy_execute_button"):
                        if quantity > 0:
                            try:
                                result = components['trade_exec'].manual_trade(
                                    trade['symbol'], quantity,
                                    st.session_state["sl_mult"], st.session_state["tp_mult"]
                                )
                                st.success(f"✅ Trade Executed: {result}")
                                
                                # Log
                                st.session_state["logs"].append(
                                    f"[{datetime.now().strftime('%H:%M:%S')}] "
                                    f"Multi-Strategy Trade: {trade['action']} {quantity:.6f} "
                                    f"{trade['symbol']} @ ${trade['price']:.4f} "
                                    f"(Conf: {trade['confidence']:.3f})"
                                )
                                
                                # Notify
                                try:
                                    trade_data = {
                                        'symbol': trade['symbol'],
                                        'side': trade['action'],
                                        'quantity': quantity,
                                        'price': trade['price'],
                                        'value': quantity * trade['price'],
                                        'timestamp': datetime.now().isoformat(),
                                        'execution_type': 'multi_strategy',
                                        'confidence': trade['confidence']
                                    }
                                    notify_trade(trade_data)
                                except Exception:
                                    pass
                                
                                del st.session_state['selected_trade']
                                st.rerun()
                            
                            except Exception as e:
                                st.error(f"❌ Trade execution failed: {e}")
                                try:
                                    notify_error(
                                        "Multi-Strategy Trade Execution", str(e),
                                        {
                                            'symbol': trade['symbol'],
                                            'quantity': quantity,
                                            'action': trade['action']
                                        }
                                    )
                                except Exception:
                                    pass
                        else:
                            st.error("❌ Invalid quantity")
                    
                    if st.button("❌ Cancel Trade", key="multi_strategy_cancel_button"):
                        del st.session_state['selected_trade']
                        st.rerun()
            
            else:
                st.info("💡 Select a signal above to execute a trade")
            
            # -------------------------------------------------
            # Signal Statistics
            # -------------------------------------------------
            st.subheader("📈 Signal Statistics")
            total_scanned = len(signals_data)
            strong_signals = len(filtered_signals)
            buy_signals = len([s for s in filtered_signals if s['final']['decision'] == 'BUY'])
            sell_signals = len([s for s in filtered_signals if s['final']['decision'] == 'SELL'])
            
            stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
            with stats_col1:
                st.metric("Total Scanned", total_scanned)
            with stats_col2:
                st.metric("Strong Signals", strong_signals)
            with stats_col3:
                st.metric("BUY Signals", buy_signals)
            with stats_col4:
                st.metric("SELL Signals", sell_signals)
        
        else:
            st.warning("⚠️ No strong signals found with current confidence threshold")
            st.info("💡 Try lowering the minimum confidence or scanning more pairs")
        
        # Last scan info
        if st.session_state['last_scan_time']:
            st.caption(f"Last scan: {st.session_state['last_scan_time'].strftime('%H:%M:%S')}")
    
    else:
        # No signals yet (never scanned)
        st.info("🔍 Click 'Scan All Pairs' to analyze trading opportunities")
        st.subheader("📋 Pairs to be scanned:")
        if trading_pairs:
            pairs_cols = st.columns(4)
            for i, pair in enumerate(trading_pairs[:20]):
                pairs_cols[i % 4].write(f"• {pair}")
            if len(trading_pairs) > 20:
                st.caption(f"... and {len(trading_pairs) - 20} more pairs")
# ========================================
# COMPLETE SETTINGS TAB WITH NOTIFICATIONS
# ========================================
with tabs[4]:
    st.header("🛠 Trading Settings & Configuration")
    
    # Create main layout
    settings_col1, settings_col2 = st.columns(2)
    
    # ================================
    # LEFT COLUMN - Risk Management
    # ================================
    with settings_col1:
        st.subheader("⚠️ Risk Management")
        
        # Initialize session state defaults if not exists
        if "sl_mult" not in st.session_state:
            st.session_state["sl_mult"] = 2.0
        if "tp_mult" not in st.session_state:
            st.session_state["tp_mult"] = 3.0
        if "risk_pct" not in st.session_state:
            st.session_state["risk_pct"] = 2.0
        if "max_positions" not in st.session_state:
            st.session_state["max_positions"] = 5
        
        # Stop Loss Multiplier
        st.session_state["sl_mult"] = st.slider(
            "🛑 Stop Loss Multiplier (ATR)", 
            min_value=0.5, 
            max_value=5.0, 
            value=st.session_state["sl_mult"], 
            step=0.1,
            help="Multiplier for ATR-based stop loss calculation",
            key="settings_tab_sl_mult"
        )
        
        # Take Profit Multiplier
        st.session_state["tp_mult"] = st.slider(
            "🎯 Take Profit Multiplier (ATR)", 
            min_value=1.0, 
            max_value=10.0, 
            value=st.session_state["tp_mult"], 
            step=0.5,
            help="Multiplier for ATR-based take profit calculation",
            key="settings_tab_tp_mult"
        )
        
        # Risk per Trade
        st.session_state["risk_pct"] = st.slider(
            "💰 Risk per Trade (%)", 
            min_value=0.1, 
            max_value=5.0, 
            value=st.session_state["risk_pct"], 
            step=0.1,
            help="Percentage of account balance to risk per trade",
            key="settings_tab_risk_pct"
        )
        
        # Max Positions
        st.session_state["max_positions"] = st.slider(
            "📊 Maximum Positions", 
            min_value=1, 
            max_value=10, 
            value=st.session_state["max_positions"],
            help="Maximum number of simultaneous open positions",
            key="settings_tab_max_positions"
        )
        
        # Risk Level Indicator
        risk_level = "🔴 HIGH" if st.session_state["risk_pct"] > 3.0 else "🟡 MEDIUM" if st.session_state["risk_pct"] > 1.5 else "🟢 LOW"
        st.info(f"**Current Risk Level:** {risk_level}")
    
    # ================================
    # RIGHT COLUMN - Strategy Settings
    # ================================
    with settings_col2:
        st.subheader("⚙️ Strategy Settings")
        
        # Initialize strategy defaults
        if "min_confidence" not in st.session_state:
            st.session_state["min_confidence"] = 0.65
        if "scan_interval" not in st.session_state:
            st.session_state["scan_interval"] = 300
        if "auto_trade_enabled" not in st.session_state:
            st.session_state["auto_trade_enabled"] = False
        
        # Minimum Confidence
        st.session_state["min_confidence"] = st.slider(
            "🎯 Minimum Signal Confidence", 
            min_value=0.5, 
            max_value=1.0, 
            value=st.session_state["min_confidence"], 
            step=0.01,
            help="Minimum confidence threshold for trade signals",
            key="settings_tab_min_confidence"
        )
        
        # Scan Interval
        st.session_state["scan_interval"] = st.slider(
            "⏱️ Scan Interval (seconds)", 
            min_value=60, 
            max_value=600, 
            value=st.session_state["scan_interval"], 
            step=30,
            help="Time between market scans for new opportunities",
            key="settings_tab_scan_interval"
        )
        
        # Strategy Selection
        strategy_options = ["Breakout", "Momentum", "Mean Reversion", "Scalping", "Swing Trading"]
        selected_strategy = st.selectbox(
            "📈 Trading Strategy",
            strategy_options,
            index=0,
            help="Primary trading strategy to use",
            key="settings_tab_strategy"
        )
        
        # Auto-trading toggle
        st.session_state["auto_trade_enabled"] = st.checkbox(
            "🤖 Enable Auto-Trading", 
            value=st.session_state["auto_trade_enabled"],
            help="Allow bot to execute trades automatically",
            key="settings_tab_auto_trade"
        )
        
        if st.session_state["auto_trade_enabled"]:
            st.warning("⚠️ **Auto-trading ENABLED!** Monitor the bot closely.")
        else:
            st.info("ℹ️ Auto-trading disabled. Manual approval required.")
    
    # ================================
    # EMAIL NOTIFICATION SYSTEM
    # ================================
    st.markdown("---")
    st.subheader("📧 Email Notification System")
    
    # Get notification status
    notification_status = get_notification_status()
    
    notification_col1, notification_col2 = st.columns(2)
    
    with notification_col1:
        st.metric("Email System", "✅ Enabled" if notification_status['enabled'] else "❌ Disabled")
        st.metric("Configuration", "✅ Ready" if notification_status['configured'] else "⚠️ Incomplete")
        
        # Email preferences checkboxes
        if notification_status['enabled']:
            st.write("**Notification Types:**")
            preferences = notification_status['types']
            
            trade_alerts = st.checkbox(
                "🤖 Trade Alerts", 
                value=preferences['trades'],
                help="Get notified when trades are executed",
                key="settings_trade_alerts"
            )
            
            signal_alerts = st.checkbox(
                "🎯 Signal Alerts", 
                value=preferences['signals'],
                help="Get notified about strong trading signals",
                key="settings_signal_alerts"
            )
            
            system_alerts = st.checkbox(
                "🟢 System Alerts", 
                value=preferences['system'],
                help="Get notified about system events",
                key="settings_system_alerts"
            )
            error_alerts = st.checkbox(
                "❌ Error Alerts", 
                value=preferences['errors'],
                help="Get notified about errors and issues",
                key="settings_error_alerts"
            )
        else:
            st.warning("⚠️ Email notifications disabled. Set EMAIL_ENABLED=true in environment.")
    
    with notification_col2:
        st.metric("Emails Sent (Hour)", notification_status['emails_sent_hour'])
        st.metric("Queue Size", notification_status['queue_size'])
        
        if notification_status['enabled']:
            st.info(f"📧 **Recipients:** {', '.join(notification_status['to_emails'])}")
        
        # Test email button
        if st.button("📧 Send Test Email", key="settings_test_email"):
            with st.spinner("Sending test email..."):
                try:
                    success = send_test_notification()
                    if success:
                        st.success("✅ Test email sent successfully! Check your inbox.")
                    else:
                        st.error("❌ Failed to send test email. Check configuration.")
                except Exception as e:
                    st.error(f"❌ Email test failed: {e}")
                    notify_error("Email Test", str(e))
    
    # ================================
    # ADVANCED CONFIGURATION
    # ================================
    st.markdown("---")
    st.subheader("🔧 Advanced Configuration")
    
    advanced_col1, advanced_col2, advanced_col3 = st.columns(3)
    
    with advanced_col1:
        # Trading Mode
        trading_mode = st.selectbox(
            "🎮 Trading Mode",
            ["Demo", "Paper Trading", "Live Trading"],
            index=0,
            help="Select trading environment",
            key="settings_tab_trading_mode"
        )
        
        if trading_mode == "Live Trading":
            st.error("🚨 **LIVE TRADING MODE** - Real money at risk!")
        elif trading_mode == "Paper Trading":
            st.warning("📝 Paper trading mode - Virtual money")
        else:
            st.success("🎮 Demo mode - Safe testing environment")
    
    with advanced_col2:
        # Time Zone
        timezone = st.selectbox(
            "🌍 Time Zone",
            ["UTC", "EST", "PST", "GMT", "CET"],
            index=0,
            key="settings_tab_timezone"
        )
        
        # Notification frequency
        notify_frequency = st.selectbox(
            "🔔 Notification Frequency",
            ["Immediate", "Every 5 min", "Every 15 min", "Hourly"],
            index=0,
            help="How often to send notifications",
            key="settings_notification_frequency"
        )
    
    with advanced_col3:
        # Logging Level
        log_level = st.selectbox(
            "📝 Logging Level",
            ["INFO", "DEBUG", "WARNING", "ERROR"],
            index=0,
            help="Detail level for system logs",
            key="settings_tab_log_level"
        )
        
        # API Rate Limiting
        api_rate_limit = st.checkbox(
            "⏸️ Respect API Rate Limits",
            value=True,
            help="Enable automatic API rate limiting",
            key="settings_tab_rate_limit"
        )
    
    # ================================
    # NOTIFICATION PREFERENCES
    # ================================
    st.markdown("---")
    st.subheader("🔔 Detailed Notification Preferences")
    
    if notification_status['enabled']:
        pref_col1, pref_col2 = st.columns(2)
        
        with pref_col1:
            st.write("**Trading Notifications:**")
            notify_on_buy = st.checkbox("📈 Notify on BUY orders", value=True, key="settings_notify_buy")
            notify_on_sell = st.checkbox("📉 Notify on SELL orders", value=True, key="settings_notify_sell")
            notify_on_profit = st.checkbox("💰 Notify on profitable trades", value=True, key="settings_notify_profit")
            notify_on_loss = st.checkbox("📊 Notify on losing trades", value=True, key="settings_notify_loss")
        
        with pref_col2:
            st.write("**System Notifications:**")
            notify_on_startup = st.checkbox("🚀 Notify on bot startup", value=True, key="settings_notify_startup")
            notify_on_shutdown = st.checkbox("🛑 Notify on bot shutdown", value=True, key="settings_notify_shutdown")
            notify_on_errors = st.checkbox("⚠️ Notify on critical errors", value=True, key="settings_notify_errors")
            notify_on_signals = st.checkbox("🎯 Notify on strong signals", value=False, key="settings_notify_signals")
        
        # Minimum thresholds for notifications
        st.write("**Notification Thresholds:**")
        
        threshold_col1, threshold_col2 = st.columns(2)
        with threshold_col1:
            min_trade_value = st.number_input(
                "Min Trade Value for Notification ($)",
                min_value=0.0,
                value=10.0,
                step=5.0,
                key="settings_min_trade_notification"
            )
        
        with threshold_col2:
            min_signal_confidence = st.number_input(
                "Min Signal Confidence for Notification",
                min_value=0.5,
                max_value=1.0,
                value=0.8,
                step=0.05,
                key="settings_min_signal_notification"
            )
    
    # ================================
    # ACTION BUTTONS
    # ================================
    st.markdown("---")
    button_col1, button_col2, button_col3, button_col4 = st.columns(4)
    
    with button_col1:
        if st.button("💾 **Save All Settings**", type="primary", key="save_all_settings"):
            # Save all settings to session state
            settings_data = {
                "sl_mult": st.session_state["sl_mult"],
                "tp_mult": st.session_state["tp_mult"],
                "risk_pct": st.session_state["risk_pct"],
                "max_positions": st.session_state["max_positions"],
                "min_confidence": st.session_state["min_confidence"],
                "scan_interval": st.session_state["scan_interval"],
                "auto_trade_enabled": st.session_state["auto_trade_enabled"],
                "strategy": selected_strategy,
                "trading_mode": trading_mode,
                "timezone": timezone,
                "log_level": log_level,
                "api_rate_limit": api_rate_limit,
                "last_updated": datetime.now().isoformat()
            }
            
            # Save notification preferences if available
            if notification_status['enabled']:
                settings_data.update({
                    "notify_on_buy": st.session_state.get("settings_notify_buy", True),
                    "notify_on_sell": st.session_state.get("settings_notify_sell", True),
                    "notify_on_profit": st.session_state.get("settings_notify_profit", True),
                    "notify_on_loss": st.session_state.get("settings_notify_loss", True),
                    "notify_on_startup": st.session_state.get("settings_notify_startup", True),
                    "notify_on_shutdown": st.session_state.get("settings_notify_shutdown", True),
                    "notify_on_errors": st.session_state.get("settings_notify_errors", True),
                    "notify_on_signals": st.session_state.get("settings_notify_signals", False),
                    "min_trade_notification": st.session_state.get("settings_min_trade_notification", 10.0),
                    "min_signal_notification": st.session_state.get("settings_min_signal_notification", 0.8)
                })
            
            # Update session state
            st.session_state.update(settings_data)
            
            # Send system notification about settings update
            try:
                notify_system("settings_updated", "Trading bot settings have been updated")
            except:
                pass  # Continue if notification fails
            
            st.success("✅ **All settings saved successfully!**")
            time.sleep(1)
            st.rerun()
    
    with button_col2:
        if st.button("🔄 **Reset to Defaults**", key="reset_settings"):
            # Reset to default values
            st.session_state.update({
                "sl_mult": 2.0,
                "tp_mult": 3.0,
                "risk_pct": 2.0,
                "max_positions": 5,
                "min_confidence": 0.65,
                "scan_interval": 300,
                "auto_trade_enabled": False
            })
            st.info("🔄 Settings reset to defaults")
            time.sleep(1)
            st.rerun()
    
    with button_col3:
        if st.button("📤 **Export Config**", key="export_settings"):
            config_data = {
                "bot_settings": {
                    "sl_mult": st.session_state.get("sl_mult", 2.0),
                    "tp_mult": st.session_state.get("tp_mult", 3.0),
                    "risk_pct": st.session_state.get("risk_pct", 2.0),
                    "max_positions": st.session_state.get("max_positions", 5),
                    "min_confidence": st.session_state.get("min_confidence", 0.65),
                    "scan_interval": st.session_state.get("scan_interval", 300),
                    "auto_trade_enabled": st.session_state.get("auto_trade_enabled", False)
                },
                "notification_settings": {
                    "enabled": notification_status['enabled'],
                    "preferences": notification_status.get('types', {}),
                    "recipients": notification_status.get('to_emails', [])
                },
                "export_timestamp": datetime.now().isoformat(),
                "bot_version": "2.0"
            }
            
            import json
            config_json = json.dumps(config_data, indent=2)
            
            st.download_button(
                label="💾 Download Config",
                data=config_json,
                file_name=f"bot_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                key="download_config"
            )
    
    with button_col4:
        if st.button("🧪 **Test Configuration**", key="test_settings"):
            # Test current settings
            with st.spinner("Testing configuration..."):
                time.sleep(2)  # Simulate testing
                
                # Validation checks
                validation_results = []
                
                if st.session_state.get("risk_pct", 0) > 5.0:
                    validation_results.append("❌ Risk too high (>5%)")
                else:
                    validation_results.append("✅ Risk level acceptable")
                
                if st.session_state.get("sl_mult", 0) < 1.0:
                    validation_results.append("❌ Stop loss too tight")
                else:
                    validation_results.append("✅ Stop loss appropriate")
                
                if st.session_state.get("min_confidence", 0) < 0.5:
                    validation_results.append("❌ Confidence threshold too low")
                else:
                    validation_results.append("✅ Confidence threshold good")
                
                # Test notification system
                if notification_status['enabled']:
                    validation_results.append("✅ Email notifications configured")
                else:
                    validation_results.append("⚠️ Email notifications disabled")
                
                # Display results
                st.info("**Configuration Test Results:**")
                for result in validation_results:
                    st.write(result)
    
    # ================================
    # CURRENT SETTINGS SUMMARY
    # ================================
    st.markdown("---")
    st.subheader("📋 Current Settings Summary")
    
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        st.metric("Stop Loss", f"{st.session_state.get('sl_mult', 2.0):.1f}x ATR")
        st.metric("Take Profit", f"{st.session_state.get('tp_mult', 3.0):.1f}x ATR")
        st.metric("Risk per Trade", f"{st.session_state.get('risk_pct', 2.0):.1f}%")
    
    with summary_col2:
        st.metric("Max Positions", f"{st.session_state.get('max_positions', 5)}")
        st.metric("Min Confidence", f"{st.session_state.get('min_confidence', 0.65):.2f}")
        st.metric("Scan Interval", f"{st.session_state.get('scan_interval', 300)//60}min")
    
    with summary_col3:
        auto_trade_status = "✅ ENABLED" if st.session_state.get('auto_trade_enabled', False) else "❌ DISABLED"
        st.metric("Auto Trading", auto_trade_status)
        
        email_status = "✅ ACTIVE" if notification_status['enabled'] else "❌ INACTIVE"
        st.metric("Email Alerts", email_status)
        
        trading_mode_display = st.session_state.get('trading_mode', 'Demo')
        st.metric("Trading Mode", trading_mode_display)
    
    # Last updated info
    if "last_updated" in st.session_state:
        st.caption(f"⏰ Last updated: {st.session_state['last_updated']}")
    else:
        st.caption("⏰ Settings not yet saved")
    
    # ================================
    # NOTIFICATION STATUS OVERVIEW
    # ================================
    if notification_status['enabled']:
        st.markdown("---")
        st.subheader("📧 Email System Status")
        
        email_col1, email_col2, email_col3, email_col4 = st.columns(4)
        
        with email_col1:
            st.metric("System Status", "🟢 Active")
        
        with email_col2:
            st.metric("Config Status", "✅ Ready" if notification_status['configured'] else "⚠️ Incomplete")
        
        with email_col3:
            st.metric("Hourly Emails", notification_status['emails_sent_hour'])
        
        with email_col4:
            st.metric("Queue Size", notification_status['queue_size'])
        
        # Show current notification preferences in a compact format
        st.write("**Active Notification Types:**")
        active_notifications = []
        preferences = notification_status.get('types', {})
        
        if preferences.get('trades', False):
            active_notifications.append("🤖 Trades")
        if preferences.get('signals', False):
            active_notifications.append("🎯 Signals")
        if preferences.get('system', False):
            active_notifications.append("🟢 System")
        if preferences.get('errors', False):
            active_notifications.append("❌ Errors")
        
        if active_notifications:
            st.info(" | ".join(active_notifications))
        else:
            st.warning("No notification types currently active")
    
# ✅ CORRECTLY INDENTED EMAIL INTEGRATION CODE
# Add this inside your Settings tab (with tabs[4]:)

with tabs[4]:  # Settings tab
    st.header("⚙️ Settings")
    
    # Your existing settings code here...
    
    # ================================
    # EMAIL NOTIFICATION SYSTEM
    # ================================
    st.markdown("---")
    st.subheader("📧 Email Notification System")
    
    notification_status = get_notification_status()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Email System", "✅ Enabled" if notification_status['enabled'] else "❌ Disabled")
        st.metric("Configuration", "✅ Ready" if notification_status['configured'] else "⚠️ Incomplete")
    
    with col2:
        if st.button("📧 Send Test Email", use_container_width=True):
            if EMAIL_AVAILABLE:
                with st.spinner("Sending test email..."):
                    success = send_test_notification()
                    if success:
                        st.success("✅ Test email sent! Check your inbox.")
                    else:
                        st.error("❌ Failed to send. Check your Gmail App Password.")
            else:
                st.error("❌ Add notifications.py file first")
    
    if not notification_status['enabled']:
        st.warning("⚠️ Set EMAIL_ENABLED=true in Railway environment variables")
    
    # Your other settings code continues here...

# -------------------------
# System Health Tab
# -------------------------
with tabs[5]:
    st.header("🩺 System Health")
    
    health = get_system_health()
    
    health_col1, health_col2, health_col3 = st.columns(3)
    with health_col1:
        cpu_pct = float(health["CPU"].replace('%', ''))
        st.metric("CPU Usage", health["CPU"], delta="High" if cpu_pct > 80 else "Normal")
    with health_col2:
        mem_pct = float(health["Memory"].replace('%', ''))
        st.metric("Memory Usage", health["Memory"], delta="High" if mem_pct > 80 else "Normal")
    with health_col3:
        st.metric("Active Threads", health["Threads"])
    
    # API Connection Test
    st.subheader("🔗 API Connection Test")
    if client:
        try:
            server_time = client.get_server_time()
            st.success(f"✅ Binance API connected. Server time: {datetime.fromtimestamp(server_time['serverTime']/1000)}")
        except Exception as e:
            st.error(f"❌ API connection failed: {e}")
    else:
        st.error("❌ No API client available")
    
    # Module Status
    st.subheader("📦 Module Status")
    module_status = []
    for name, module in modules.items():
        status = "✅ Available" if module else "❌ Missing"
        module_status.append({"Module": name, "Status": status})
    
    module_df = pd.DataFrame(module_status)
    st.dataframe(module_df, use_container_width=True)

# -------------------------
# Logs Tab
# -------------------------
with tabs[6]:
    st.header("📜 Activity Logs")
    
    logs_col1, logs_col2, logs_col3 = st.columns([2, 1, 1])
    with logs_col1:
        log_filter = st.selectbox("Filter logs", ["All", "Manual", "Multi-Strategy", "ERROR", "SUCCESS", "WARNING"], key="log_filter")
    with logs_col2:
        if st.button("🗑️ Clear Logs", key="clear_logs"):
            st.session_state["logs"] = []
            st.success("Logs cleared")
    with logs_col3:
        if st.button("📥 Export Logs", key="export_logs"):
            logs = st.session_state.get("logs", [])
            if logs:
                log_text = "\n".join(logs)
                st.download_button(
                    label="💾 Download",
                    data=log_text,
                    file_name=f"trading_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    key="download_logs"
                )
    
    # Display logs
    logs = st.session_state.get("logs", [])
    if logs:
        # Show recent logs (last 100)
        recent_logs = logs[-100:]
        
        # Filter logs
        if log_filter != "All":
            recent_logs = [log for log in recent_logs if log_filter in log]
        
        # Count different types of logs
        total_logs = len(recent_logs)
        error_count = len([log for log in recent_logs if "ERROR" in log])
        success_count = len([log for log in recent_logs if "SUCCESS" in log])
        
        # Show log statistics
        log_stats_col1, log_stats_col2, log_stats_col3 = st.columns(3)
        with log_stats_col1:
            st.metric("Total Logs", total_logs)
        with log_stats_col2:
            st.metric("Errors", error_count, delta="High" if error_count > 5 else "Normal")
        with log_stats_col3:
            st.metric("Successes", success_count)
        
        st.divider()
        
        # Display logs in reverse order (newest first)
        for log in reversed(recent_logs):
            if "ERROR" in log or "FAIL" in log:
                st.error(log)
            elif "WARNING" in log:
                st.warning(log)
            elif "SUCCESS" in log:
                st.success(log)
            elif "Multi-Strategy" in log:
                st.info(log)
            elif "Manual" in log:
                st.info(log)
            else:
                st.text(log)
    else:
        st.info("📝 No logs available. Activity will appear here as the bot operates.")

# -------------------------
# Analytics Tab
# -------------------------
with tabs[7]:
    st.header("📈 Advanced Analytics")
    
    # Performance Overview
    st.subheader("📊 Portfolio Performance")
    
    try:
        # Create sample performance data
        dates = pd.date_range(start='2024-01-01', end=datetime.now(), freq='D')
        returns = np.random.normal(0.001, 0.02, len(dates))
        cumulative_returns = np.cumprod(1 + returns) - 1
        portfolio_values = 10000 * (1 + cumulative_returns)
        
        performance_df = pd.DataFrame({
            'Date': dates,
            'Portfolio_Value': portfolio_values
        })
        
        fig = px.line(performance_df, x='Date', y='Portfolio_Value', 
                     title="Portfolio Performance Over Time")
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance Metrics
        perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)
        with perf_col1:
            st.metric("Total Return", f"{cumulative_returns[-1]*100:.2f}%")
        with perf_col2:
            st.metric("Total Trades", len(st.session_state.get("logs", [])))
        with perf_col3:
            volatility = np.std(returns) * np.sqrt(252) * 100
            st.metric("Volatility", f"{volatility:.2f}%")
        with perf_col4:
            if volatility != 0:
                sharpe = (np.mean(returns) * 252) / (np.std(returns) * np.sqrt(252))
                st.metric("Sharpe Ratio", f"{sharpe:.2f}")
            else:
                st.metric("Sharpe Ratio", "N/A")
        
        # Trading Activity
        st.subheader("📈 Trading Activity Analysis")
        
        # Create sample trading data
        hours = list(range(24))
        trades_per_hour = np.random.poisson(2, 24)
        
        activity_df = pd.DataFrame({
            'Hour': hours,
            'Trades': trades_per_hour
        })
        
        fig_trades = px.bar(activity_df, x='Hour', y='Trades', 
                           title="Trading Activity by Hour")
        st.plotly_chart(fig_trades, use_container_width=True)
        
        # Recent Trades Analysis
        st.subheader("📊 Recent Trading Summary")
        
        logs = st.session_state.get("logs", [])
        trade_logs = [log for log in logs if "Trade" in log and ("BUY" in log or "SELL" in log)]
        
        if trade_logs:
            trade_analysis_col1, trade_analysis_col2 = st.columns(2)
            
            with trade_analysis_col1:
                st.write("**Recent Trade Activity:**")
                for log in trade_logs[-10:]:
                    if "SUCCESS" in log:
                        st.success(log)
                    elif "ERROR" in log or "FAIL" in log:
                        st.error(log)
                    else:
                        st.info(log)
            
            with trade_analysis_col2:
                total_trades = len(trade_logs)
                successful_trades = len([log for log in trade_logs if "SUCCESS" in log])
                failed_trades = len([log for log in trade_logs if "ERROR" in log or "FAIL" in log])
                
                st.metric("Total Trades", total_trades)
                st.metric("Successful", successful_trades)
                st.metric("Failed", failed_trades)
                
                if total_trades > 0:
                    success_rate = (successful_trades / total_trades) * 100
                    st.metric("Success Rate", f"{success_rate:.1f}%")
        else:
            st.info("📝 No trading activity recorded yet. Execute some trades to see analytics.")
            
    except Exception as e:
        st.error(f"Analytics error: {e}")
        st.info("📊 Analytics will show real data once more trading activity is recorded")

# -------------------------
# Status Bar
# -------------------------
st.divider()

status_col1, status_col2, status_col3, status_col4 = st.columns(4)

with status_col1:
    if client:
        st.success("🟢 API Connected")
    else:
        st.error("🔴 API Disconnected")

with status_col2:
    scanner = st.session_state.get("auto_scanner")
    if scanner and scanner.is_running():
        st.success("🟢 Scanner Active")
    else:
        st.warning("🟡 Scanner Inactive")

with status_col3:
    auto_trade = os.getenv("AUTO_TRADE_ENABLED", "false").lower() == "true"
    if auto_trade:
        st.success("🟢 Auto-Trade ON")
    else:
        st.info("🔵 Auto-Trade OFF")

with status_col4:
    mode = "🧪 TESTNET" if os.getenv("USE_TESTNET", "false").lower() == "true" else "🚀 LIVE"
    if "TESTNET" in mode:
        st.info(mode)
    else:
        st.warning(mode)

# -------------------------
# Enhanced Footer
# -------------------------
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px; margin-top: 20px;'>
        <div style='margin-bottom: 15px;'>
            <img src='https://static.wixstatic.com/media/80aa29_3bdfcbab4dd34671915e3b66b0b596e4~mv2.jpeg/v1/fill/w_146,h_104,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/LRC_1719585575250.jpeg' 
                 width='80' style='border-radius: 8px; opacity: 0.8;'/>
        </div>
        <h4 style='color: #333; margin: 10px 0;'>🧠 Hybrid Quantum Crypto Trading Bot v2.0</h4>
        <p style='color: #666; margin: 10px 0;'>
            ⚛️ Quantum Analytics | 🤖 AI Trading | 📊 Advanced Analytics
        </p>
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 15px; border-radius: 10px; margin: 15px 0; color: white;'>
            <h4 style='color: white; margin: 0;'>Rondanini Publishing Ltd.</h4>
            <p style='color: #f0f0f0; margin: 5px 0; font-size: 14px;'>
                Advanced Quantum-Enhanced Trading Solutions
            </p>
            <p style='color: #e0e0e0; margin: 5px 0; font-size: 12px;'>
                © 2025 All Rights Reserved
            </p>
        </div>
        <p style='color: #888; font-size: 12px; margin-top: 15px;'>
            ⚠️ <strong>Risk Disclaimer:</strong> Trading involves substantial risk of loss. 
            Past performance does not guarantee future results. Trade responsibly.
        </p>
    </div>
    """, 
    unsafe_allow_html=True
)

# -------------------------
# Background Tasks
# -------------------------
if os.getenv("AUTO_START_BOT", "false").lower() == "true":
    scanner = st.session_state.get("auto_scanner")
    if scanner and not scanner.is_running():
        scanner.start_scanning()
        st.session_state["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] Auto-scanner started")

print("✅ Hybrid Quantum Trading Bot loaded successfully!")