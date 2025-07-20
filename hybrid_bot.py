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
import threading
from datetime import datetime, timedelta
import traceback

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
    
    def manual_trade(self, symbol, qty, sl_mult, tp_mult, atr_value=None):
        price = FallbackMarketAnalyzer().get_price(symbol)
        trade_msg = f"[Manual] BUY {symbol} @ {price} Qty={qty}"
        self.log_callback(trade_msg)
        return f"✅ Trade executed: {symbol} quantity {qty}"
    
    def auto_execute(self, signal, total_balance, open_positions, sl_mult, tp_mult):
        return "✅ Auto-trade executed (demo)"

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
        return self.running# -------------------------
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
        use_testnet = os.getenv("USE_TESTNET", "true").lower() == "true"
        
        if use_testnet:
            client.API_URL = 'https://testnet.binance.vision/api'
        
        client.get_server_time()
        mode = "🧪 TESTNET" if use_testnet else "🚀 LIVE"
        return client, f"✅ Connected to Binance {mode}"
        
    except Exception as e:
        return None, f"❌ Connection failed: {str(e)}"

def initialize_components():
    """Initialize components safely"""
    components = {}
    
    # Binance client
    client, client_status = setup_binance_client()
    
    # Portfolio Manager
    if modules.get('PortfolioManager') and client:
        try:
            api_key = os.getenv("BINANCE_API_KEY") or os.getenv("BINANCE_TESTNET_API_KEY")
            api_secret = os.getenv("BINANCE_API_SECRET") or os.getenv("BINANCE_TESTNET_API_SECRET")
            use_testnet = os.getenv("USE_TESTNET", "true").lower() == "true"
            components['portfolio_mgr'] = modules['PortfolioManager'](api_key, api_secret, use_testnet)
            print("✅ Live Portfolio Manager initialized")
        except Exception as e:
            print(f"⚠️ Portfolio Manager failed, using fallback: {e}")
            components['portfolio_mgr'] = FallbackPortfolioManager()
    else:
        components['portfolio_mgr'] = FallbackPortfolioManager()
    
    # Market Analyzer
    if modules.get('MarketAnalyzer'):
        try:
            components['market_analyzer'] = modules['MarketAnalyzer'](client)
            print("✅ Live Market Analyzer initialized")
        except Exception as e:
            print(f"⚠️ Market Analyzer failed, using fallback: {e}")
            components['market_analyzer'] = FallbackMarketAnalyzer(client)
    else:
        components['market_analyzer'] = FallbackMarketAnalyzer(client)
    
    # Risk Manager
    if modules.get('RiskManager'):
        try:
            components['risk_mgr'] = modules['RiskManager'](max_risk_percent=0.02, max_positions=5)
            print("✅ Risk Manager initialized")
        except Exception as e:
            print(f"⚠️ Risk Manager failed: {e}")
            components['risk_mgr'] = None
    else:
        components['risk_mgr'] = None
    
   # -------------------------
# Trade Executor Section - CLEAN VERSION
# -------------------------

# Enhanced Fallback Trade Executor Class
class FallbackTradeExecutor:
    """Enhanced fallback executor with balance simulation"""
    
    def __init__(self, client=None, risk_mgr=None, log_callback=None):
        self.log = log_callback if log_callback else print
        self.active_orders = {}
        self.mock_balance = 1000.0
    
    def manual_trade(self, symbol, qty=None, sl_mult=1.5, tp_mult=3.0, trade_amount_usd=None):
        try:
            mock_prices = {
                'BTCUSDT': 117000.0,
                'ETHUSDT': 4000.0,
                'BNBUSDT': 600.0,
                'ADAUSDT': 0.45,
                'SOLUSDT': 200.0
            }
            
            price = mock_prices.get(symbol, 100.0)
            
            if trade_amount_usd:
                amount = min(trade_amount_usd, self.mock_balance * 0.1)
                qty = amount / price
            else:
                amount = min(50.0, self.mock_balance * 0.05)
                qty = amount / price
            
            self.log(f"📝 DEMO: Would buy {qty:.8f} {symbol} for ${amount:.2f}")
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

# Initialize Trade Executor - SAFE VERSION
print("🔧 Initializing Trade Executor...")

try:
    # Try balance-aware executor first
    from balance_aware_trade_executor import create_balance_aware_executor
    components['trade_exec'] = create_balance_aware_executor(
        client, 
        components.get('risk_mgr'),
        log_callback=lambda msg: st.session_state.setdefault("logs", []).append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    )
    print("✅ Balance-Aware Trade Executor initialized")
    
except ImportError:
    print("⚠️ Balance-aware executor not found, trying standard executor...")
    # Try standard trade executor
    if modules.get('TradeExecutor'):
        try:
            components['trade_exec'] = modules['TradeExecutor'](
                client, 
                components.get('risk_mgr'),
                log_callback=lambda msg: st.session_state.setdefault("logs", []).append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
            )
            print("✅ Standard Trade Executor initialized")
        except Exception as e:
            print(f"⚠️ Standard executor failed: {e}")
            components['trade_exec'] = FallbackTradeExecutor(
                client, 
                components.get('risk_mgr'),
                log_callback=lambda msg: st.session_state.setdefault("logs", []).append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
            )
            print("✅ Using Fallback Trade Executor")
    else:
        print("⚠️ No TradeExecutor module found, using fallback...")
        components['trade_exec'] = FallbackTradeExecutor(
            client, 
            components.get('risk_mgr'),
            log_callback=lambda msg: st.session_state.setdefault("logs", []).append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        )
        print("✅ Using Fallback Trade Executor")
        
except Exception as e:
    print(f"⚠️ All executors failed: {e}")
    components['trade_exec'] = FallbackTradeExecutor(
        client, 
        components.get('risk_mgr'),
        log_callback=lambda msg: st.session_state.setdefault("logs", []).append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    )
    print("✅ Using Fallback Trade Executor (emergency)")

print(f"🎯 Trade Executor ready: {type(components['trade_exec']).__name__}")
    
    # Quantum Components
    if modules.get('QuantumTrader') and client:
        try:
            components['quantum_trader'] = modules['QuantumTrader'](client)
            print("✅ Quantum Trader initialized")
        except:
            components['quantum_trader'] = None
    else:
        components['quantum_trader'] = None
    
    if modules.get('QuantumAnalyzer'):
        try:
            components['quantum_analyzer'] = modules['QuantumAnalyzer']()
            print("✅ Quantum Analyzer initialized")
        except:
            components['quantum_analyzer'] = FallbackQuantumAnalyzer()
    else:
        components['quantum_analyzer'] = FallbackQuantumAnalyzer()
    
    # Other components
    components['position_monitor'] = None
    components['analytics_dashboard'] = None
    components['ensemble_engine'] = None
    
    return components, client, client_status

# Initialize everything
print("🔧 Initializing components...")
components, client, client_status = initialize_components()

# -------------------------
# Session State Initialization
# -------------------------
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
    
    mode = "🧪 TESTNET" if os.getenv("USE_TESTNET", "true").lower() == "true" else "🚀 LIVE"
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
                mode = "🧪 TESTNET" if os.getenv("USE_TESTNET", "true").lower() == "true" else "🚀 LIVE"
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
                    "24h Change": f"{data['change']:.2f}%"
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
        
        # Trade execution
        if st.button("🚀 Execute Trade", type="primary", key="manual_execute"):
            if qty > 0:
                try:
                    total_balance = components['portfolio_mgr'].total_value()
                    open_positions = 0  # Fallback
                    
                    if components['risk_mgr']:
                        validation = components['risk_mgr'].validate_trade(symbol, qty, current_price, total_balance, open_positions)
                        if validation["status"]:
                            result = components['trade_exec'].manual_trade(
                                symbol, qty, st.session_state["sl_mult"], st.session_state["tp_mult"]
                            )
                            st.success(f"✅ {result}")
                        else:
                            st.error(f"❌ Trade blocked: {validation['reason']}")
                    else:
                        result = components['trade_exec'].manual_trade(
                            symbol, qty, st.session_state["sl_mult"], st.session_state["tp_mult"]
                        )
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
# Multi-Strategy Tab
# -------------------------
with tabs[3]:
    st.header("⚛ Multi-Strategy Market Scanner")
    st.caption("Quantum + ML + Technical Analysis for ALL Trading Pairs")
    
    # Configuration Section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Strategy weights with auto-balancing
        st.write("**Strategy Weights (Auto-balanced to 100%)**")
        
        # Initialize weights in session state if not exists
        if 'weight_quantum' not in st.session_state:
            st.session_state['weight_quantum'] = 30
        if 'weight_ml' not in st.session_state:
            st.session_state['weight_ml'] = 30
        if 'weight_technical' not in st.session_state:
            st.session_state['weight_technical'] = 40
        
        # Create three columns for sliders
        subcol1, subcol2, subcol3 = st.columns(3)
        
        with subcol1:
            quantum_weight = st.slider("Quantum Weight", 0, 100, st.session_state['weight_quantum'], key="multi_quantum_weight")
        with subcol2:
            ml_weight = st.slider("ML Weight", 0, 100, st.session_state['weight_ml'], key="multi_ml_weight")
        with subcol3:
            technical_weight = st.slider("Technical Weight", 0, 100, st.session_state['weight_technical'], key="multi_technical_weight")
        
        # Auto-balance weights
        total = quantum_weight + ml_weight + technical_weight
        if total != 100:
            quantum_weight = int((quantum_weight / total) * 100)
            ml_weight = int((ml_weight / total) * 100)
            technical_weight = 100 - quantum_weight - ml_weight
        
        # Update session state
        st.session_state['weight_quantum'] = quantum_weight
        st.session_state['weight_ml'] = ml_weight
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
        
        # Quick preset buttons
        preset_col1, preset_col2, preset_col3, preset_col4 = st.columns(4)
        
        with preset_col1:
            if st.button("⚛️ Quantum Focus", key="preset_quantum"):
                st.session_state['weight_quantum'] = 60
                st.session_state['weight_ml'] = 20
                st.session_state['weight_technical'] = 20
                st.rerun()
        
        with preset_col2:
            if st.button("🤖 ML Focus", key="preset_ml"):
                st.session_state['weight_quantum'] = 20
                st.session_state['weight_ml'] = 60
                st.session_state['weight_technical'] = 20
                st.rerun()
        
        with preset_col3:
            if st.button("📊 Technical Focus", key="preset_technical"):
                st.session_state['weight_quantum'] = 20
                st.session_state['weight_ml'] = 20
                st.session_state['weight_technical'] = 60
                st.rerun()
        
        with preset_col4:
            if st.button("⚖️ Balanced", key="preset_balanced"):
                st.session_state['weight_quantum'] = 33
                st.session_state['weight_ml'] = 33
                st.session_state['weight_technical'] = 34
                st.rerun()
    
    with col2:
        # Configuration parameters
        min_conf = st.slider("Min Confidence", 0.5, 1.0, 0.65, 0.01, key="multi_min_conf")
        max_pairs = st.slider("Max Pairs to Scan", 5, 50, 20, 5, key="multi_max_pairs")
        
        # Scan mode selection
        scan_mode = st.selectbox("Scan Mode", [
            "Top Volume Pairs",
            "Portfolio + Major Pairs", 
            "All USDT Pairs",
            "Custom Selection"
        ], key="multi_scan_mode")
    
    # Pair Selection Logic
    all_pairs = components['market_analyzer'].get_trading_pairs()
    
    if scan_mode == "Top Volume Pairs":
        trading_pairs = all_pairs[:max_pairs]
    elif scan_mode == "Portfolio + Major Pairs":
        try:
            portfolio = components['portfolio_mgr'].get_portfolio()
            portfolio_pairs = [f"{asset}USDT" for asset in portfolio.keys() if asset not in ["USDT", "BUSD"]]
        except:
            portfolio_pairs = []
        major_pairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT']
        trading_pairs = list(set(portfolio_pairs + major_pairs))[:max_pairs]
    elif scan_mode == "All USDT Pairs":
        trading_pairs = [pair for pair in all_pairs if pair.endswith('USDT')][:max_pairs]
    else:  # Custom Selection
        trading_pairs = st.multiselect(
            "Select Trading Pairs", 
            all_pairs, 
            default=['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
            key="multi_custom_pairs"
        )
    
    # Scan Controls
    scan_col1, scan_col2, scan_col3 = st.columns(3)
    
    with scan_col1:
        if st.button("🔍 Scan All Pairs", type="primary", key="multi_scan_button"):
            st.session_state['manual_scan_requested'] = True
    
    with scan_col2:
        if st.button("🔄 Refresh Signals", key="multi_refresh_button"):
            st.session_state['refresh_signals'] = True
    
    with scan_col3:
        show_only_signals = st.checkbox("Show Only Strong Signals", value=True, key="multi_show_only_signals")
    
    # Scanning process
    if st.session_state.get('manual_scan_requested', False):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        signals_data = []
        
        for i, symbol in enumerate(trading_pairs):
            try:
                progress = (i + 1) / len(trading_pairs)
                progress_bar.progress(progress)
                status_text.text(f"Analyzing {symbol}... ({i+1}/{len(trading_pairs)})")
                
                # Generate signals using current components
                rsi = components['market_analyzer'].get_latest_rsi(symbol)
                momentum = components['market_analyzer'].get_latest_momentum(symbol)
                volatility = components['market_analyzer'].get_volatility(symbol)
                price = components['market_analyzer'].get_price(symbol)
                
                # Enhanced signal logic
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
                
                # Final ensemble decision
                weights = {
                    "quantum": quantum_weight,
                    "ml": ml_weight,
                    "technical": technical_weight
                }
                
                final_conf = (quantum_conf * weights['quantum'] + 
                            ml_conf * weights['ml'] + 
                            tech_conf * weights['technical']) / 100
                
                final_decision = quantum_decision if final_conf > min_conf else "HOLD"
                
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
                
            except Exception as e:
                st.error(f"Error analyzing {symbol}: {e}")
                continue
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        # Store results in session state
        st.session_state['latest_signals'] = signals_data
        st.session_state['manual_scan_requested'] = False
        st.session_state['last_scan_time'] = datetime.now()
    
    # Display Results
    signals_data = st.session_state.get('latest_signals', [])
    
    if signals_data:
        # Filter signals if requested
        if show_only_signals:
            filtered_signals = [
                s for s in signals_data 
                if s['final']['decision'] != 'HOLD' and s['final']['confidence'] > min_conf
            ]
        else:
            filtered_signals = signals_data
        
        if filtered_signals:
            st.subheader(f"📊 Analysis Results ({len(filtered_signals)} pairs)")
            
            # Create signals dataframe
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
            
            # Color coding for signals
            def color_signals(val):
                if 'BUY' in val:
                    return 'background-color: #90EE90'  # Light green
                elif 'SELL' in val:
                    return 'background-color: #FFB6C1'  # Light red
                else:
                    return 'background-color: #F0F0F0'  # Light gray
            
            # Apply styling
            styled_df = df.style.applymap(color_signals, subset=['Final Signal'])
            st.dataframe(styled_df, use_container_width=True)
            
            # Trading Interface
            st.subheader("⚡ Quick Trading Interface")
            
            # Select signal for trading
            strong_buy_signals = [s for s in filtered_signals if s['final']['decision'] == 'BUY']
            strong_sell_signals = [s for s in filtered_signals if s['final']['decision'] == 'SELL']
            
            if strong_buy_signals or strong_sell_signals:
                trade_col1, trade_col2 = st.columns(2)
                
                with trade_col1:
                    if strong_buy_signals:
                        st.write("**🟢 Strong BUY Signals:**")
                        for i, signal in enumerate(strong_buy_signals[:5]):  # Top 5
                            symbol = signal['symbol']
                            conf = signal['final']['confidence']
                            price = signal.get('price', 0)
                            
                            if price > 0:
                                signal_col1, signal_col2 = st.columns([3, 1])
                                
                                with signal_col1:
                                    st.write(f"**{symbol}** - ${price:.4f} (Conf: {conf:.3f})")
                                
                                with signal_col2:
                                    if st.button(f"🚀 Buy", key=f"multi_buy_{symbol}_{i}"):
                                        st.session_state['selected_trade'] = {
                                            'symbol': symbol,
                                            'action': 'BUY',
                                            'price': price,
                                            'confidence': conf,
                                            'timestamp': datetime.now(),
                                            'source': 'multi_strategy'
                                        }
                                        st.success(f"Selected {symbol} for BUY")
                                        st.rerun()
                
                with trade_col2:
                    if strong_sell_signals:
                        st.write("**🔴 Strong SELL Signals:**")
                        for i, signal in enumerate(strong_sell_signals[:5]):  # Top 5
                            symbol = signal['symbol']
                            conf = signal['final']['confidence']
                            price = signal.get('price', 0)
                            
                            if price > 0:
                                signal_col1, signal_col2 = st.columns([3, 1])
                                
                                with signal_col1:
                                    st.write(f"**{symbol}** - ${price:.4f} (Conf: {conf:.3f})")
                                
                                with signal_col2:
                                    if st.button(f"📉 Sell", key=f"multi_sell_{symbol}_{i}"):
                                        st.session_state['selected_trade'] = {
                                            'symbol': symbol,
                                            'action': 'SELL',
                                            'price': price,
                                            'confidence': conf,
                                            'timestamp': datetime.now(),
                                            'source': 'multi_strategy'
                                        }
                                        st.success(f"Selected {symbol} for SELL")
                                        st.rerun()
            
            # Execute Selected Trade
            if 'selected_trade' in st.session_state and st.session_state['selected_trade'].get('source') == 'multi_strategy':
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
                    quantity = st.number_input("Quantity", min_value=0.0001, step=0.0001, format="%.6f", key="multi_strategy_quantity")
                    
                    if quantity > 0:
                        trade_value = quantity * trade['price']
                        est_fee = trade_value * 0.001
                        st.info(f"Trade Value: ${trade_value:.2f}")
                        st.caption(f"Est. Fee: ${est_fee:.4f}")
                    else:
                        st.warning("⚠️ Enter quantity")
                
                with exec_col3:
                    use_sl_tp = st.checkbox("Use Stop Loss / Take Profit", value=True, key="multi_strategy_sl_tp")
                    
                    if use_sl_tp:
                        sl_pct = st.number_input("Stop Loss %", min_value=1.0, value=5.0, max_value=20.0, key="multi_strategy_sl")
                        tp_pct = st.number_input("Take Profit %", min_value=1.0, value=10.0, max_value=50.0, key="multi_strategy_tp")
                    
                    # Execute button
                    if st.button("🚀 EXECUTE TRADE", type="primary", key="multi_strategy_execute"):
                        if quantity > 0:
                            try:
                                result = components['trade_exec'].manual_trade(
                                    trade['symbol'], quantity, 
                                    st.session_state["sl_mult"], st.session_state["tp_mult"]
                                )
                                st.success(f"✅ Trade Executed: {result}")
                                
                                success_msg = f"Multi-Strategy Trade: {trade['action']} {quantity:.6f} {trade['symbol']} @ ${trade['price']:.4f} (Conf: {trade['confidence']:.3f})"
                                st.session_state["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] {success_msg}")
                                
                                # Clear selected trade
                                del st.session_state['selected_trade']
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"❌ Trade execution failed: {e}")
                        else:
                            st.error("❌ Invalid quantity")
                
                # Cancel trade button
                if st.button("❌ Cancel Trade", key="multi_strategy_cancel"):
                    del st.session_state['selected_trade']
                    st.rerun()
            
            else:
                st.info("💡 Select a signal above to execute a trade")
            
            # Signal Statistics
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
        if 'last_scan_time' in st.session_state:
            st.caption(f"Last scan: {st.session_state['last_scan_time'].strftime('%H:%M:%S')}")
    
    else:
        st.info("🔍 Click 'Scan All Pairs' to analyze trading opportunities")
        
        # Show pairs to be scanned
        st.subheader("📋 Pairs to be scanned:")
        if trading_pairs:
            pairs_cols = st.columns(4)
            for i, pair in enumerate(trading_pairs[:20]):
                pairs_cols[i % 4].write(f"• {pair}")
            
            if len(trading_pairs) > 20:
                st.caption(f"... and {len(trading_pairs) - 20} more pairs")
# -------------------------
# Settings Tab
# -------------------------
with tabs[4]:
    st.header("🛠 Trading Settings")
    
    settings_col1, settings_col2 = st.columns(2)
    
    with settings_col1:
        st.subheader("Risk Management")
        st.session_state["sl_mult"] = st.slider(
            "Stop Loss Multiplier (ATR)", 0.5, 5.0, st.session_state["sl_mult"], 0.1, key="settings_sl_mult"
        )
        st.session_state["tp_mult"] = st.slider(
            "Take Profit Multiplier (ATR)", 1.0, 10.0, st.session_state["tp_mult"], 0.5, key="settings_tp_mult"
        )
        
        risk_pct = st.slider("Risk per Trade (%)", 0.1, 5.0, 2.0, 0.1, key="settings_risk_pct")
        max_positions = st.slider("Max Positions", 1, 10, 5, key="settings_max_positions")
    
    with settings_col2:
        st.subheader("Strategy Settings")
        min_confidence = st.slider("Min Signal Confidence", 0.5, 1.0, 0.65, 0.01, key="settings_min_confidence")
        scan_interval = st.slider("Scan Interval (seconds)", 60, 600, 300, 30, key="settings_scan_interval")
        
        # Auto-trading toggle
        auto_trade = st.checkbox("Enable Auto-Trading", value=False, key="settings_auto_trade")
        if auto_trade:
            st.warning("⚠️ Auto-trading enabled. Monitor closely!")
    
    if st.button("💾 Save Settings", key="save_settings"):
        st.session_state.update({
            "risk_pct": risk_pct,
            "max_positions": max_positions,
            "min_confidence": min_confidence,
            "scan_interval": scan_interval
        })
        st.success("✅ Settings saved!")

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
    mode = "🧪 TESTNET" if os.getenv("USE_TESTNET", "true").lower() == "true" else "🚀 LIVE"
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

                
