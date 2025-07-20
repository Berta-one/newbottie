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

# Fix Railway port issue - must be at the very top
if 'streamlit' in sys.argv[0] or 'RAILWAY_ENVIRONMENT' in os.environ:
    # Clear problematic Streamlit environment variables
    os.environ.pop('STREAMLIT_SERVER_PORT', None)
    os.environ.pop('STREAMLIT_SERVER_ADDRESS', None)
    
    # Set correct port from Railway
    if 'PORT' in os.environ:
        os.environ['STREAMLIT_SERVER_PORT'] = os.environ['PORT']
        os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psutil
import streamlit as st
import numpy as np

# Import modules with debug info
print("🔄 Starting module imports...")
modules = safe_import_modules()

# Debug: Print what was actually imported
print("📦 Available modules:")
for name, module in modules.items():
    status = "✅ Available" if module else "❌ Missing"
    print(f"  - {name}: {status}")
    
# ✅ Streamlit Config
st.set_page_config(page_title="Hybrid Quantum Trading Bot", layout="wide")

# -------------------------
# Conditional Imports with Error Handling
# -------------------------
def safe_import_modules():
    """Safely import modules with fallbacks"""
    modules = {}
    
    try:
        from portfolio_manager import PortfolioManager
        modules['PortfolioManager'] = PortfolioManager
        print("✅ PortfolioManager imported successfully")
    except ImportError as e:
        modules['PortfolioManager'] = None
        print(f"⚠️ PortfolioManager not available: {e}")
        st.warning("⚠️ PortfolioManager not available")
    
    try:
        from trade_executor import TradeExecutor
        modules['TradeExecutor'] = TradeExecutor
        print("✅ TradeExecutor imported successfully")
    except ImportError as e:
        modules['TradeExecutor'] = None
        print(f"⚠️ TradeExecutor not available: {e}")
        st.warning("⚠️ TradeExecutor not available")
    
    try:
        from risk_manager import RiskManager
        modules['RiskManager'] = RiskManager
        print("✅ RiskManager imported successfully")
    except ImportError as e:
        modules['RiskManager'] = None
        print(f"⚠️ RiskManager not available: {e}")
        st.warning("⚠️ RiskManager not available")
    
    try:
        from position_monitor import PositionMonitor
        modules['PositionMonitor'] = PositionMonitor
        print("✅ PositionMonitor imported successfully")
    except ImportError as e:
        modules['PositionMonitor'] = None
        print(f"⚠️ PositionMonitor not available: {e}")
        st.warning("⚠️ PositionMonitor not available")
    
    try:
        from market_analyzer import MarketAnalyzer
        modules['MarketAnalyzer'] = MarketAnalyzer
        print("✅ MarketAnalyzer imported successfully")
    except ImportError as e:
        modules['MarketAnalyzer'] = None
        print(f"❌ MarketAnalyzer not available: {e}")
        st.error("❌ MarketAnalyzer not available - Manual Trading disabled")
    
    try:
        from quantum_trading_integration import QuantumTrader
        modules['QuantumTrader'] = QuantumTrader
        print("✅ QuantumTrader imported successfully")
    except ImportError as e:
        modules['QuantumTrader'] = None
        print(f"⚠️ QuantumTrader not available: {e}")
        st.warning("⚠️ QuantumTrader not available - Using fallback")
    
    try:
        from quantum_engine import QuantumAnalyzer
        modules['QuantumAnalyzer'] = QuantumAnalyzer
        print("✅ QuantumAnalyzer imported successfully")
    except ImportError as e:
        modules['QuantumAnalyzer'] = None
        print(f"⚠️ QuantumAnalyzer not available: {e}")
        st.warning("⚠️ QuantumAnalyzer not available - Using fallback")
    
    try:
        from dashboard import TradingDashboard
        modules['TradingDashboard'] = TradingDashboard
        print("✅ TradingDashboard imported successfully")
    except ImportError as e:
        modules['TradingDashboard'] = None
        print(f"⚠️ TradingDashboard not available: {e}")
        st.warning("⚠️ TradingDashboard not available")
    
    try:
        from ensemble_signal_engine import EnsembleSignalEngine
        modules['EnsembleSignalEngine'] = EnsembleSignalEngine
        print("✅ EnsembleSignalEngine imported successfully")
    except ImportError as e:
        modules['EnsembleSignalEngine'] = None
        print(f"⚠️ EnsembleSignalEngine not available: {e}")
        st.warning("⚠️ EnsembleSignalEngine not available")
    
    try:
        from binance.client import Client
        modules['Client'] = Client
        print("✅ Binance Client imported successfully")
    except ImportError as e:
        modules['Client'] = None
        print(f"❌ Binance client not available: {e}")
        st.error("❌ Binance client not available")
    
    print(f"📦 Module import summary: {sum(1 for v in modules.values() if v is not None)}/{len(modules)} modules loaded")
    return modules

# -------------------------
# Environment & API Setup
# -------------------------
def setup_binance_client():
    """Setup Binance client with testnet/live mode"""
    api_key = os.getenv("BINANCE_API_KEY") or os.getenv("BINANCE_TESTNET_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET") or os.getenv("BINANCE_TESTNET_API_SECRET")
    use_testnet = os.getenv("USE_TESTNET", "true").lower() == "true"
    
    if not api_key or not api_secret:
        return None, "❌ API keys not configured"
    
    if modules['Client'] is None:
        return None, "❌ Binance client not available"
    
    try:
        # Choose correct API keys based on mode
        if use_testnet:
            api_key = os.getenv("BINANCE_TESTNET_API_KEY", api_key)
            api_secret = os.getenv("BINANCE_TESTNET_API_SECRET", api_secret)
        
        client = modules['Client'](api_key, api_secret)
        
        if use_testnet:
            client.API_URL = 'https://testnet.binance.vision/api'
        
        # Test connection
        client.get_server_time()
        
        mode = "🧪 TESTNET" if use_testnet else "🚀 LIVE"
        return client, f"✅ Connected to Binance {mode}"
        
    except Exception as e:
        return None, f"❌ Connection failed: {str(e)}"

# Initialize client
client, client_status = setup_binance_client()
# -------------------------
# Fallback Classes
# -------------------------
class FallbackManager:
    def __init__(self):
        self.dummy_portfolio = {
            'USDT': {'balance': 1000.0, 'price': 1.0, 'value': 1000.0, 'change': 0.0},
            'BTC': {'balance': 0.01, 'price': 45000.0, 'value': 450.0, 'change': 2.5},
            'ETH': {'balance': 0.1, 'price': 3000.0, 'value': 300.0, 'change': 1.8}
        }
    
    def get_portfolio(self):
        return self.dummy_portfolio
    
    def total_value(self):
        return sum(asset['value'] for asset in self.dummy_portfolio.values())

class FallbackMarketAnalyzer:
    def __init__(self, client=None):
        self.client = client
    
    def get_trading_pairs(self):
        return ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT']
    
    def get_price(self, symbol):
        prices = {'BTCUSDT': 45000, 'ETHUSDT': 3000, 'BNBUSDT': 400}
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
    def __init__(self, client, risk_mgr, log_callback=None):
        self.active_orders = {}
        self.log_callback = log_callback or print
    
    def manual_trade(self, symbol, qty, sl_mult, tp_mult, atr_value=None):
        self.log_callback(f"[DEMO] Trade executed: {symbol} qty={qty}")
        return f"✅ Demo trade: {symbol} quantity {qty}"
    
    def auto_execute(self, signal, total_balance, open_positions, sl_mult, tp_mult):
        return "Demo auto-trade executed"

# -------------------------
# Initialize Core Objects with Better Error Handling
# -------------------------
def initialize_components():
    """Initialize all trading components with proper error handling"""
    components = {}
    
    print("🔧 Initializing trading components...")
    
    # Portfolio Manager
    try:
        if modules.get('PortfolioManager') and client:
            # Get API keys from client or environment
            api_key = getattr(client, 'API_KEY', None) or os.getenv("BINANCE_API_KEY") or os.getenv("BINANCE_TESTNET_API_KEY")
            api_secret = getattr(client, 'API_SECRET', None) or os.getenv("BINANCE_API_SECRET") or os.getenv("BINANCE_TESTNET_API_SECRET")
            use_testnet = os.getenv("USE_TESTNET", "true").lower() == "true"
            
            components['portfolio_mgr'] = modules['PortfolioManager'](api_key, api_secret, use_testnet)
            print("✅ Portfolio Manager initialized successfully")
        else:
            components['portfolio_mgr'] = FallbackPortfolioManager()
            print("⚠️ Using Fallback Portfolio Manager")
    except Exception as e:
        print(f"❌ Portfolio Manager initialization failed: {e}")
        components['portfolio_mgr'] = FallbackPortfolioManager()
    
    # Risk Manager
    try:
        if modules.get('RiskManager'):
            components['risk_mgr'] = modules['RiskManager'](max_risk_percent=0.02, max_positions=5)
            print("✅ Risk Manager initialized successfully")
        else:
            components['risk_mgr'] = None
            print("⚠️ Risk Manager not available")
    except Exception as e:
        print(f"❌ Risk Manager initialization failed: {e}")
        components['risk_mgr'] = None
    
    # Position Monitor
    try:
        if modules.get('PositionMonitor'):
            components['position_monitor'] = modules['PositionMonitor']()
            print("✅ Position Monitor initialized successfully")
        else:
            components['position_monitor'] = None
            print("⚠️ Position Monitor not available")
    except Exception as e:
        print(f"❌ Position Monitor initialization failed: {e}")
        components['position_monitor'] = None
    
    # Market Analyzer
    try:
        if modules.get('MarketAnalyzer'):
            components['market_analyzer'] = modules['MarketAnalyzer'](client)
            print("✅ Market Analyzer initialized successfully")
        else:
            components['market_analyzer'] = FallbackMarketAnalyzer(client)
            print("⚠️ Using Fallback Market Analyzer")
    except Exception as e:
        print(f"❌ Market Analyzer initialization failed: {e}")
        components['market_analyzer'] = FallbackMarketAnalyzer(client)
    
    # Quantum Components
    try:
        if modules.get('QuantumTrader') and client:
            components['quantum_trader'] = modules['QuantumTrader'](client)
            print("✅ Quantum Trader initialized successfully")
        else:
            components['quantum_trader'] = None
            print("⚠️ Quantum Trader not available")
    except Exception as e:
        print(f"❌ Quantum Trader initialization failed: {e}")
        components['quantum_trader'] = None
    
    try:
        if modules.get('QuantumAnalyzer'):
            components['quantum_analyzer'] = modules['QuantumAnalyzer']()
            print("✅ Quantum Analyzer initialized successfully")
        else:
            components['quantum_analyzer'] = FallbackQuantumAnalyzer()
            print("⚠️ Using Fallback Quantum Analyzer")
    except Exception as e:
        print(f"❌ Quantum Analyzer initialization failed: {e}")
        components['quantum_analyzer'] = FallbackQuantumAnalyzer()
    
    # Dashboard
    try:
        if modules.get('TradingDashboard'):
            components['analytics_dashboard'] = modules['TradingDashboard']()
            print("✅ Analytics Dashboard initialized successfully")
        else:
            components['analytics_dashboard'] = None
            print("⚠️ Analytics Dashboard not available")
    except Exception as e:
        print(f"❌ Analytics Dashboard initialization failed: {e}")
        components['analytics_dashboard'] = None
    
    # Ensemble Engine
    try:
        if modules.get('EnsembleSignalEngine') and client:
            components['ensemble_engine'] = modules['EnsembleSignalEngine'](
                client, components.get('quantum_trader'), components.get('market_analyzer')
            )
            print("✅ Ensemble Engine initialized successfully")
        else:
            components['ensemble_engine'] = None
            print("⚠️ Ensemble Engine not available")
    except Exception as e:
        print(f"❌ Ensemble Engine initialization failed: {e}")
        components['ensemble_engine'] = None
    
    # Trade Executor
    try:
        if modules.get('TradeExecutor'):
            components['trade_exec'] = modules['TradeExecutor'](
                client, components.get('risk_mgr'), 
                log_callback=lambda msg: st.session_state.setdefault("logs", []).append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
            )
            print("✅ Trade Executor initialized successfully")
        else:
            components['trade_exec'] = FallbackTradeExecutor(
                client, components.get('risk_mgr'),
                log_callback=lambda msg: st.session_state.setdefault("logs", []).append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
            )
            print("⚠️ Using Fallback Trade Executor")
    except Exception as e:
        print(f"❌ Trade Executor initialization failed: {e}")
        components['trade_exec'] = FallbackTradeExecutor(
            client, components.get('risk_mgr'),
            log_callback=lambda msg: st.session_state.setdefault("logs", []).append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        )
    
    # Summary
    active_components = sum(1 for v in components.values() if v is not None)
    print(f"🎯 Component initialization complete: {active_components}/{len(components)} components active")
    
    return components

# Initialize components with error handling
print("🔧 Initializing components...")
try:
    components = initialize_components()
    print("✅ All components initialized successfully")
except Exception as e:
    st.error(f"🚨 Critical error during component initialization: {e}")
    st.code(traceback.format_exc())
    
    # Create minimal fallback components
    components = {
        'portfolio_mgr': FallbackPortfolioManager(),
        'market_analyzer': FallbackMarketAnalyzer(client),
        'quantum_analyzer': FallbackQuantumAnalyzer(),
        'trade_exec': FallbackTradeExecutor(client, None),
        'risk_mgr': None,
        'position_monitor': None,
        'quantum_trader': None,
        'analytics_dashboard': None,
        'ensemble_engine': None
    }
    print("🔄 Using minimal fallback components")
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
# Session State Initialization
# -------------------------
if "sl_mult" not in st.session_state:
    st.session_state["sl_mult"] = 1.5
if "tp_mult" not in st.session_state:
    st.session_state["tp_mult"] = 3.0
if "logs" not in st.session_state:
    st.session_state["logs"] = []
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
        if st.button("▶️ Start Scanner" if not auto_scanner.is_running() else "🛑 Stop Scanner"):
            if auto_scanner.is_running():
                auto_scanner.stop_scanning()
                st.success("Scanner stopped")
            else:
                auto_scanner.start_scanning()
                st.success("Scanner started")
            st.rerun()
    
    with col2:
        if st.button("🔄 Manual Scan"):
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
# Main UI Layout
# -------------------------
st.title("🧠 Hybrid Quantum Crypto Trading Bot")
st.caption("Advanced Crypto Trading with Technical, ML & Quantum Strategies")

# Connection Status
col1, col2 = st.columns([3, 1])
with col1:
    st.info(client_status)
with col2:
    if st.button("🔄 Refresh"):
        st.rerun()

# Main Tabs
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
        if st.button("🔄 Refresh Portfolio"):
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
                live_status = "🟢 Live" if components['portfolio_mgr'].is_live() else "🔴 Demo"
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
            if components['portfolio_mgr'].is_live():
                st.subheader("📈 Recent Trade History")
                trades = components['portfolio_mgr'].get_trade_history(limit=10)
                
                if trades:
                    trade_df = pd.DataFrame(trades)
                    st.dataframe(trade_df, use_container_width=True)
                else:
                    st.info("No recent trades found")
            
        else:
            st.warning("⚠️ No portfolio data available.")
            
    except Exception as e:
        st.error(f"Portfolio fetch error: {e}")
        st.code(traceback.format_exc())
        
        # Show debug info
        with st.expander("🔧 Debug Information"):
            st.write("Portfolio Manager Status:")
            st.write(f"- Live connection: {components['portfolio_mgr'].is_live()}")
            st.write(f"- Connection status: {components['portfolio_mgr'].get_connection_status()}")

# -------------------------
# Manual Trading Tab
# -------------------------
with tabs[1]:
    st.header("✋ Manual Trading")
    
    if components['market_analyzer']:
        col1, col2 = st.columns(2)
        
        with col1:
            pairs = components['market_analyzer'].get_trading_pairs()
            symbol = st.selectbox("Select Trading Pair", pairs)
            
            # Get current price
            current_price = components['market_analyzer'].get_price(symbol)
            st.info(f"Current Price: ${current_price:,.2f}")
        
        with col2:
            qty = st.number_input("Quantity", min_value=0.0001, step=0.0001, format="%.6f")
            
            # Calculate trade value
            trade_value = qty * current_price
            st.info(f"Trade Value: ${trade_value:.2f}")
        
        # Trade execution
        if st.button("🚀 Execute Trade", type="primary"):
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
    
    if auto_trade_enabled:
        st.success("✅ Auto-trading is ENABLED in environment")
    else:
        st.warning("⚠️ Auto-trading is DISABLED in environment")
    
    # Scanner interface
    display_scanner_results()
    
    # Active orders display
    st.subheader("📋 Active Orders")
    if hasattr(components['trade_exec'], 'active_orders'):
        if components['trade_exec'].active_orders:
            st.json(components['trade_exec'].active_orders)
        else:
            st.info("No active orders")
    else:
        st.info("Order tracking not available")
        # -------------------------
# Enhanced Multi-Strategy Tab (Replace the existing Multi-Strategy section)
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
        if 'last_changed_weight' not in st.session_state:
            st.session_state['last_changed_weight'] = None
        
        # Create three columns for sliders
        subcol1, subcol2, subcol3 = st.columns(3)
        
        with subcol1:
            new_quantum = st.slider(
                "Quantum Weight", 
                0, 100, 
                st.session_state['weight_quantum'],
                key="quantum_slider"
            )
        
        with subcol2:
            new_ml = st.slider(
                "ML Weight", 
                0, 100, 
                st.session_state['weight_ml'],
                key="ml_slider"
            )
        
        with subcol3:
            new_technical = st.slider(
                "Technical Weight", 
                0, 100, 
                st.session_state['weight_technical'],
                key="technical_slider"
            )
        
        # Auto-balance logic
        def auto_balance_weights(changed_weight, new_value):
            """Auto-balance weights to sum to 100%"""
            old_quantum = st.session_state['weight_quantum']
            old_ml = st.session_state['weight_ml'] 
            old_technical = st.session_state['weight_technical']
            
            if changed_weight == 'quantum':
                # Quantum changed
                remaining = 100 - new_value
                if remaining >= 0:
                    # Distribute remaining between ML and Technical proportionally
                    old_total = old_ml + old_technical
                    if old_total > 0:
                        ratio_ml = old_ml / old_total
                        ratio_technical = old_technical / old_total
                        new_ml_calc = int(remaining * ratio_ml)
                        new_technical_calc = remaining - new_ml_calc
                    else:
                        new_ml_calc = remaining // 2
                        new_technical_calc = remaining - new_ml_calc
                    
                    return new_value, new_ml_calc, new_technical_calc
                else:
                    return old_quantum, old_ml, old_technical
                    
            elif changed_weight == 'ml':
                # ML changed
                remaining = 100 - new_value
                if remaining >= 0:
                    old_total = old_quantum + old_technical
                    if old_total > 0:
                        ratio_quantum = old_quantum / old_total
                        ratio_technical = old_technical / old_total
                        new_quantum_calc = int(remaining * ratio_quantum)
                        new_technical_calc = remaining - new_quantum_calc
                    else:
                        new_quantum_calc = remaining // 2
                        new_technical_calc = remaining - new_quantum_calc
                    
                    return new_quantum_calc, new_value, new_technical_calc
                else:
                    return old_quantum, old_ml, old_technical
                    
            elif changed_weight == 'technical':
                # Technical changed
                remaining = 100 - new_value
                if remaining >= 0:
                    old_total = old_quantum + old_ml
                    if old_total > 0:
                        ratio_quantum = old_quantum / old_total
                        ratio_ml = old_ml / old_total
                        new_quantum_calc = int(remaining * ratio_quantum)
                        new_ml_calc = remaining - new_quantum_calc
                    else:
                        new_quantum_calc = remaining // 2
                        new_ml_calc = remaining - new_quantum_calc
                    
                    return new_quantum_calc, new_ml_calc, new_value
                else:
                    return old_quantum, old_ml, old_technical
            
            return old_quantum, old_ml, old_technical
        
        # Check which weight changed and auto-balance
        weights_changed = False
        
        if new_quantum != st.session_state['weight_quantum']:
            # Quantum changed
            balanced_quantum, balanced_ml, balanced_technical = auto_balance_weights('quantum', new_quantum)
            weights_changed = True
            st.session_state['last_changed_weight'] = 'quantum'
            
        elif new_ml != st.session_state['weight_ml']:
            # ML changed
            balanced_quantum, balanced_ml, balanced_technical = auto_balance_weights('ml', new_ml)
            weights_changed = True
            st.session_state['last_changed_weight'] = 'ml'
            
        elif new_technical != st.session_state['weight_technical']:
            # Technical changed
            balanced_quantum, balanced_ml, balanced_technical = auto_balance_weights('technical', new_technical)
            weights_changed = True
            st.session_state['last_changed_weight'] = 'technical'
            
        else:
            # No change, use current values
            balanced_quantum = st.session_state['weight_quantum']
            balanced_ml = st.session_state['weight_ml']
            balanced_technical = st.session_state['weight_technical']
        
        # Update session state
        st.session_state['weight_quantum'] = balanced_quantum
        st.session_state['weight_ml'] = balanced_ml
        st.session_state['weight_technical'] = balanced_technical
        
        # If weights were auto-balanced, refresh to update sliders
        if weights_changed:
            st.rerun()
        
        # Display current weights with visual indicator
        total_weight = balanced_quantum + balanced_ml + balanced_technical
        
        # Visual weight display
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            st.metric("Quantum", f"{balanced_quantum}%")
        with col2:
            st.metric("ML", f"{balanced_ml}%")
        with col3:
            st.metric("Technical", f"{balanced_technical}%")
        with col4:
            # Total should always be 100%, but show it anyway
            if total_weight == 100:
                st.metric("Total", f"{total_weight}%", delta="✅")
            else:
                st.metric("Total", f"{total_weight}%", delta="⚠️")
        
        # Progress bar visualization
        st.write("**Weight Distribution:**")
        progress_col1, progress_col2, progress_col3 = st.columns(3)
        
        with progress_col1:
            st.write(f"Quantum: {balanced_quantum}%")
            st.progress(balanced_quantum / 100)
        
        with progress_col2:
            st.write(f"ML: {balanced_ml}%")
            st.progress(balanced_ml / 100)
        
        with progress_col3:
            st.write(f"Technical: {balanced_technical}%")
            st.progress(balanced_technical / 100)
        
        # Quick preset buttons
        st.write("**Quick Presets:**")
        preset_col1, preset_col2, preset_col3, preset_col4 = st.columns(4)
        
        with preset_col1:
            if st.button("⚛️ Quantum Focus", help="Quantum: 60%, ML: 20%, Technical: 20%"):
                st.session_state['weight_quantum'] = 60
                st.session_state['weight_ml'] = 20
                st.session_state['weight_technical'] = 20
                st.rerun()
        
        with preset_col2:
            if st.button("🤖 ML Focus", help="Quantum: 20%, ML: 60%, Technical: 20%"):
                st.session_state['weight_quantum'] = 20
                st.session_state['weight_ml'] = 60
                st.session_state['weight_technical'] = 20
                st.rerun()
        
        with preset_col3:
            if st.button("📊 Technical Focus", help="Quantum: 20%, ML: 20%, Technical: 60%"):
                st.session_state['weight_quantum'] = 20
                st.session_state['weight_ml'] = 20
                st.session_state['weight_technical'] = 60
                st.rerun()
        
        with preset_col4:
            if st.button("⚖️ Balanced", help="Quantum: 33%, ML: 33%, Technical: 34%"):
                st.session_state['weight_quantum'] = 33
                st.session_state['weight_ml'] = 33
                st.session_state['weight_technical'] = 34
                st.rerun()
        
        # Final weights dictionary for use in analysis
        weights = {
            "quantum": balanced_quantum, 
            "ml": balanced_ml, 
            "technical": balanced_technical
        }
        
        # Display which weight was last changed (for user feedback)
        if st.session_state.get('last_changed_weight'):
            last_changed = st.session_state['last_changed_weight'].title()
            st.caption(f"💡 Last changed: {last_changed} weight - others auto-adjusted")
    
    with col2:
        # Fixed: Added the missing configuration parameters
        min_conf = st.slider("Min Confidence", 0.5, 1.0, 0.65, 0.01)
        max_pairs = st.slider("Max Pairs to Scan", 5, 50, 20, 5)
        
        # Scan mode selection
        scan_mode = st.selectbox("Scan Mode", [
            "Top Volume Pairs",
            "Portfolio + Major Pairs", 
            "All USDT Pairs",
            "Custom Selection"
        ])
        # Pair Selection Logic
    if scan_mode == "Top Volume Pairs":
        # Get high volume pairs
        all_pairs = components['market_analyzer'].get_trading_pairs()
        trading_pairs = all_pairs[:max_pairs]  # Top N by volume
        
    elif scan_mode == "Portfolio + Major Pairs":
        # Existing positions + major pairs
        try:
            portfolio = components['portfolio_mgr'].get_portfolio()
            portfolio_pairs = [f"{asset}USDT" for asset in portfolio.keys() if asset not in ["USDT", "BUSD"]]
        except:
            portfolio_pairs = []
        
        major_pairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT', 'LINKUSDT']
        trading_pairs = list(set(portfolio_pairs + major_pairs))[:max_pairs]
        
    elif scan_mode == "All USDT Pairs":
        # All available USDT pairs
        all_pairs = components['market_analyzer'].get_trading_pairs()
        trading_pairs = [pair for pair in all_pairs if pair.endswith('USDT')][:max_pairs]
        
    else:  # Custom Selection
        # Let user select custom pairs
        all_pairs = components['market_analyzer'].get_trading_pairs()
        trading_pairs = st.multiselect(
            "Select Trading Pairs", 
            all_pairs, 
            default=['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        )
    
    # Scan Controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Scan All Pairs", type="primary"):
            st.session_state['manual_scan_requested'] = True
    
    with col2:
        if st.button("🔄 Refresh Signals"):
            st.session_state['refresh_signals'] = True
    
    with col3:
        show_only_signals = st.checkbox("Show Only Strong Signals", value=True)
    
    # Progress bar for scanning
    if st.session_state.get('manual_scan_requested', False):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        signals_data = []
        
        for i, symbol in enumerate(trading_pairs):
            try:
                # Update progress
                progress = (i + 1) / len(trading_pairs)
                progress_bar.progress(progress)
                status_text.text(f"Analyzing {symbol}... ({i+1}/{len(trading_pairs)})")
                
                if components['ensemble_engine']:
                    signal = components['ensemble_engine'].get_signals(symbol, weights, min_conf)
                else:
                    # Enhanced fallback signal generation
                    rsi = components['market_analyzer'].get_latest_rsi(symbol)
                    momentum = components['market_analyzer'].get_latest_momentum(symbol)
                    volatility = components['market_analyzer'].get_volatility(symbol)
                    price = components['market_analyzer'].get_price(symbol)
                    
                    # Advanced signal logic
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
                    tech_conf = quantum_conf * 1.1
                    
                    # Final ensemble decision
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
            
            # Create comprehensive signals dataframe
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
                col1, col2 = st.columns(2)
                
                with col1:
                    if strong_buy_signals:
                        st.write("**🟢 Strong BUY Signals:**")
                        for signal in strong_buy_signals[:5]:  # Top 5
                            symbol = signal['symbol']
                            conf = signal['final']['confidence']
                            price = signal.get('price', 0)
                            
                            # Validate price before displaying
                            if price <= 0:
                                # Try to get fresh price
                                try:
                                    fresh_price = components['market_analyzer'].get_price(symbol)
                                    price = fresh_price if fresh_price > 0 else 0
                                except:
                                    price = 0
                            
                            if price > 0:  # Only show if we have valid price
                                signal_col1, signal_col2 = st.columns([3, 1])
                                
                                with signal_col1:
                                    st.write(f"**{symbol}** - ${price:.4f} (Conf: {conf:.3f})")
                                
                                with signal_col2:
                                    if st.button(f"🚀 Buy", key=f"buy_{symbol}"):
                                        # Store selected trade with validated price
                                        st.session_state['selected_trade'] = {
                                            'symbol': symbol,
                                            'action': 'BUY',
                                            'price': price,
                                            'confidence': conf,
                                            'timestamp': datetime.now()
                                        }
                                        st.success(f"Selected {symbol} for BUY")
                                        st.rerun()
                            else:
                                st.warning(f"⚠️ {symbol} - Price data unavailable")
                
                with col2:
                    if strong_sell_signals:
                        st.write("**🔴 Strong SELL Signals:**")
                        for signal in strong_sell_signals[:5]:  # Top 5
                            symbol = signal['symbol']
                            conf = signal['final']['confidence']
                            price = signal.get('price', 0)
                            
                            # Validate price before displaying
                            if price <= 0:
                                # Try to get fresh price
                                try:
                                    fresh_price = components['market_analyzer'].get_price(symbol)
                                    price = fresh_price if fresh_price > 0 else 0
                                except:
                                    price = 0
                            
                            if price > 0:  # Only show if we have valid price
                                signal_col1, signal_col2 = st.columns([3, 1])
                                
                                with signal_col1:
                                    st.write(f"**{symbol}** - ${price:.4f} (Conf: {conf:.3f})")
                                
                                with signal_col2:
                                    if st.button(f"📉 Sell", key=f"sell_{symbol}"):
                                        # Store selected trade with validated price
                                        st.session_state['selected_trade'] = {
                                            'symbol': symbol,
                                            'action': 'SELL',
                                            'price': price,
                                            'confidence': conf,
                                            'timestamp': datetime.now()
                                        }
                                        st.success(f"Selected {symbol} for SELL")
                                        st.rerun()
                            else:
                                st.warning(f"⚠️ {symbol} - Price data unavailable")
            
            # Execute Selected Trade
            if 'selected_trade' in st.session_state:
                trade = st.session_state['selected_trade']
                
                st.divider()
                st.subheader(f"🎯 Execute Trade: {trade['action']} {trade['symbol']}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.info(f"**Symbol:** {trade['symbol']}")
                    st.info(f"**Action:** {trade['action']}")
                    st.info(f"**Price:** ${trade['price']:.4f}")
                    st.info(f"**Confidence:** {trade['confidence']:.3f}")
                
                with col2:
                    # Fixed: Added the missing quantity input
                    quantity = st.number_input("Quantity", min_value=0.0001, step=0.0001, format="%.6f", key="multi_strategy_qty")
                    
                    # Calculate trade value
                    if quantity > 0:
                        trade_value = quantity * trade['price']
                        st.info(f"Trade Value: ${trade_value:.2f}")
                    else:
                        st.warning("⚠️ Enter quantity")
                
                with col3:
                    # Risk management
                    use_sl_tp = st.checkbox("Use Stop Loss / Take Profit", value=True)
                    
                    if use_sl_tp:
                        sl_pct = st.number_input("Stop Loss %", min_value=1.0, value=5.0, max_value=20.0)
                        tp_pct = st.number_input("Take Profit %", min_value=1.0, value=10.0, max_value=50.0)
                    
                    # Execute button
                    if st.button("🚀 EXECUTE TRADE", type="primary"):
                        try:
                            # Validate trade
                            if quantity > 0:
                                total_balance = components['portfolio_mgr'].total_value()
                                open_positions = 0  # Fallback
                                
                                if components['risk_mgr']:
                                    validation = components['risk_mgr'].validate_trade(
                                        trade['symbol'], quantity, trade['price'], total_balance, open_positions
                                    )
                                    if validation["status"]:
                                        result = components['trade_exec'].manual_trade(
                                            trade['symbol'], quantity, 
                                            st.session_state["sl_mult"], st.session_state["tp_mult"]
                                        )
                                        st.success(f"✅ Trade Executed: {result}")
                                        
                                        # Log the trade
                                        log_msg = f"Multi-Strategy Trade: {trade['action']} {quantity:.6f} {trade['symbol']} @ ${trade['price']:.4f} (Conf: {trade['confidence']:.3f})"
                                        st.session_state["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] {log_msg}")
                                        
                                        # Clear selected trade
                                        del st.session_state['selected_trade']
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Trade blocked: {validation['reason']}")
                                else:
                                    # Execute without risk validation (fallback)
                                    result = components['trade_exec'].manual_trade(
                                        trade['symbol'], quantity, 
                                        st.session_state["sl_mult"], st.session_state["tp_mult"]
                                    )
                                    st.success(f"✅ Trade Executed: {result}")
                            else:
                                st.error("❌ Invalid quantity")
                                
                        except Exception as e:
                            st.error(f"❌ Trade execution failed: {e}")
                
                # Cancel trade
                if st.button("❌ Cancel Trade"):
                    del st.session_state['selected_trade']
                    st.rerun()
            
            # Signal Statistics
            st.subheader("📈 Signal Statistics")
            
            total_scanned = len(signals_data)
            strong_signals = len(filtered_signals)
            buy_signals = len([s for s in filtered_signals if s['final']['decision'] == 'BUY'])
            sell_signals = len([s for s in filtered_signals if s['final']['decision'] == 'SELL'])
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Scanned", total_scanned)
            with col2:
                st.metric("Strong Signals", strong_signals)
            with col3:
                st.metric("BUY Signals", buy_signals)
            with col4:
                st.metric("SELL Signals", sell_signals)
        
        else:
            st.warning("⚠️ No strong signals found with current confidence threshold")
            st.info("💡 Try lowering the minimum confidence or scanning more pairs")
        
        # Last scan info
        if 'last_scan_time' in st.session_state:
            st.caption(f"Last scan: {st.session_state['last_scan_time'].strftime('%H:%M:%S')}")
    
    else:
        # Initial state - no scan performed yet
        st.info("🔍 Click 'Scan All Pairs' to analyze trading opportunities across multiple cryptocurrencies")
        
        # Show sample pairs that will be scanned
        st.subheader("📋 Pairs to be scanned:")
        if trading_pairs:
            # Display in columns
            pairs_per_col = 5
            cols = st.columns(min(len(trading_pairs) // pairs_per_col + 1, 4))
            
            for i, pair in enumerate(trading_pairs[:20]):  # Show first 20
                col_idx = i % len(cols)
                cols[col_idx].write(f"• {pair}")
            
            if len(trading_pairs) > 20:
                st.caption(f"... and {len(trading_pairs) - 20} more pairs")
        else:
            st.warning("⚠️ No trading pairs selected")
            # -------------------------
# Settings Tab
# -------------------------
with tabs[4]:
    st.header("🛠 Trading Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Risk Management")
        st.session_state["sl_mult"] = st.slider(
            "Stop Loss Multiplier (ATR)", 0.5, 5.0, st.session_state["sl_mult"], 0.1
        )
        st.session_state["tp_mult"] = st.slider(
            "Take Profit Multiplier (ATR)", 1.0, 10.0, st.session_state["tp_mult"], 0.5
        )
        
        risk_pct = st.slider("Risk per Trade (%)", 0.1, 5.0, 2.0, 0.1)
        max_positions = st.slider("Max Positions", 1, 10, 5)
    
    with col2:
        st.subheader("Strategy Settings")
        min_confidence = st.slider("Min Signal Confidence", 0.5, 1.0, 0.65, 0.01)
        scan_interval = st.slider("Scan Interval (seconds)", 60, 600, 300, 30)
        
        # Auto-trading toggle
        auto_trade = st.checkbox("Enable Auto-Trading", value=False)
        if auto_trade:
            st.warning("⚠️ Auto-trading enabled. Monitor closely!")
    
    if st.button("💾 Save Settings"):
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
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("CPU Usage", health["CPU"])
    with col2:
        st.metric("Memory Usage", health["Memory"])
    with col3:
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
    
    df = pd.DataFrame(module_status)
    st.dataframe(df, use_container_width=True)

# -------------------------
# Logs Tab
# -------------------------
with tabs[6]:
    st.header("📜 Activity Logs")
    
    if st.button("🗑️ Clear Logs"):
        st.session_state["logs"] = []
        st.success("Logs cleared")
    
    # Display logs
    logs = st.session_state.get("logs", [])
    if logs:
        # Show recent logs (last 50)
        recent_logs = logs[-50:]
        
        # Log level filtering
        log_filter = st.selectbox("Filter logs", ["All", "INFO", "ERROR", "WARNING"])
        
        filtered_logs = recent_logs
        if log_filter != "All":
            filtered_logs = [log for log in recent_logs if log_filter in log]
        
        # Display logs in reverse order (newest first)
        for log in reversed(filtered_logs):
            if "ERROR" in log:
                st.error(log)
            elif "WARNING" in log:
                st.warning(log)
            else:
                st.text(log)
    else:
        st.info("📝 No logs available. Activity will appear here as the bot operates.")

# -------------------------
# Analytics Tab
# -------------------------
with tabs[7]:
    st.header("📈 Advanced Analytics")
    
    if components['analytics_dashboard']:
        try:
            components['analytics_dashboard'].render_analytics_dashboard()
        except Exception as e:
            st.error(f"Analytics dashboard error: {e}")
            
            # Fallback analytics
            st.subheader("📊 Basic Analytics")
            
            # Mock performance data
            dates = pd.date_range(start='2024-01-01', end=datetime.now(), freq='D')
            cumulative_pnl = np.cumsum(np.random.randn(len(dates)) * 50)
            
            performance_df = pd.DataFrame({
                'Date': dates,
                'Cumulative_PnL': cumulative_pnl
            })
            
            fig = px.line(performance_df, x='Date', y='Cumulative_PnL', 
                         title="Portfolio Performance (Demo Data)")
            st.plotly_chart(fig, use_container_width=True)
            
            # Basic metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Trades", "0")
            with col2:
                st.metric("Win Rate", "0%")
            with col3:
                st.metric("Total P&L", "$0.00")
            with col4:
                st.metric("Best Trade", "$0.00")
    else:
        st.warning("⚠️ Analytics dashboard not available")
        
        # Simple performance overview
        st.subheader("📊 Portfolio Overview")
        try:
            portfolio = components['portfolio_mgr'].get_portfolio()
            total_value = sum(v["value"] for v in portfolio.values())
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Portfolio Value", f"${total_value:,.2f}")
            with col2:
                change = sum(v["change"] for v in portfolio.values()) / len(portfolio)
                st.metric("Avg Change", f"{change:.2f}%")
                
        except Exception as e:
            st.error(f"Portfolio overview error: {e}")
            # -------------------------
# Auto-refresh and Status Bar
# -------------------------
# Status bar at bottom
st.divider()

col1, col2, col3, col4 = st.columns(4)

with col1:
    if client:
        st.success("🟢 API Connected")
    else:
        st.error("🔴 API Disconnected")

with col2:
    scanner = st.session_state.get("auto_scanner")
    if scanner and scanner.is_running():
        st.success("🟢 Scanner Active")
    else:
        st.warning("🟡 Scanner Inactive")

with col3:
    auto_trade = os.getenv("AUTO_TRADE_ENABLED", "false").lower() == "true"
    if auto_trade:
        st.success("🟢 Auto-Trade ON")
    else:
        st.info("🔵 Auto-Trade OFF")

with col4:
    mode = "🧪 TESTNET" if os.getenv("USE_TESTNET", "true").lower() == "true" else "🚀 LIVE"
    if "TESTNET" in mode:
        st.info(mode)
    else:
        st.warning(mode)

# Auto-refresh option
if st.checkbox("🔄 Auto-refresh (30s)", value=False):
    time.sleep(30)
    st.rerun()

# -------------------------
# Footer
# -------------------------
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
    🧠 Hybrid Quantum Crypto Trading Bot v2.0 | 
    ⚛️ Quantum Analytics | 🤖 AI Trading | 📊 Advanced Analytics<br>
    <small>⚠️ Trading involves risk. Past performance does not guarantee future results.</small>
    </div>
    """, 
    unsafe_allow_html=True
)

# -------------------------
# Background Tasks (if enabled)
# -------------------------
if os.getenv("AUTO_START_BOT", "false").lower() == "true":
    # Auto-start scanner if configured
    scanner = st.session_state.get("auto_scanner")
    if scanner and not scanner.is_running():
        scanner.start_scanning()
        st.session_state["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] Auto-scanner started on bot initialization")

# -------------------------
# Error Handling and Recovery
# -------------------------
def handle_critical_error(error):
    """Handle critical errors gracefully"""
    st.error(f"🚨 Critical Error: {error}")
    st.info("🔧 Try refreshing the page or check your configuration")
    
    # Log critical error
    st.session_state["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] CRITICAL ERROR: {error}")
    
    # Show recovery options
    if st.button("🔄 Restart Components"):
        # Clear session state and reinitialize
        for key in list(st.session_state.keys()):
            if key not in ["logs"]:  # Keep logs
                del st.session_state[key]
        st.rerun()

# -------------------------
# Development/Debug Info (if enabled)
# -------------------------
if os.getenv("DEBUG_MODE", "false").lower() == "true":
    with st.expander("🔧 Debug Information"):
        st.subheader("Environment Variables")
        debug_env = {
            "USE_TESTNET": os.getenv("USE_TESTNET"),
            "AUTO_TRADE_ENABLED": os.getenv("AUTO_TRADE_ENABLED"),
            "DASHBOARD_PASSWORD": "***" if os.getenv("DASHBOARD_PASSWORD") else "Not Set",
            "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT"),
            "PORT": os.getenv("PORT")
        }
        st.json(debug_env)
        
        st.subheader("Session State")
        debug_session = {k: v for k, v in st.session_state.items() if not callable(v)}
        st.json(debug_session, expanded=False)
        
        st.subheader("Component Status")
        component_status = {name: str(type(comp)) for name, comp in components.items()}
        st.json(component_status)

# -------------------------
# Performance Monitoring
# -------------------------
if "performance_metrics" not in st.session_state:
    st.session_state["performance_metrics"] = {
        "page_loads": 0,
        "errors": 0,
        "last_load": datetime.now()
    }

# Update performance metrics
st.session_state["performance_metrics"]["page_loads"] += 1
st.session_state["performance_metrics"]["last_load"] = datetime.now()

# -------------------------
# Main Execution Guard
# -------------------------
if __name__ == "__main__":
    # This section runs when the script is executed directly
    try:
        st.info("🚀 Hybrid Quantum Trading Bot is running successfully!")
        
        # Initialize logging
        if not st.session_state.get("logs"):
            st.session_state["logs"] = [
                f"[{datetime.now().strftime('%H:%M:%S')}] Bot initialized successfully",
                f"[{datetime.now().strftime('%H:%M:%S')}] {client_status}",
                f"[{datetime.now().strftime('%H:%M:%S')}] Dashboard loaded"
            ]
        
    except Exception as e:
        handle_critical_error(e)

# -------------------------
# Script Termination Handler
# -------------------------
def cleanup_on_exit():
    """Cleanup function called on script termination"""
    try:
        # Stop scanner if running
        scanner = st.session_state.get("auto_scanner")
        if scanner and scanner.is_running():
            scanner.stop_scanning()
        
        # Log shutdown
        st.session_state["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] Bot shutdown")
        
    except Exception as e:
        print(f"Cleanup error: {e}")

# Register cleanup function
import atexit
atexit.register(cleanup_on_exit)
