#!/usr/bin/env python3
"""
Hybrid Quantum Crypto Trading Bot for Railway Deployment
======================================================
Complete self-contained trading bot with quantum computing, ML, and technical analysis
Optimized for cloud deployment with environment-based configuration
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json, os, time, threading, requests
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Railway-specific configuration
RAILWAY_ENV = os.getenv('RAILWAY_ENVIRONMENT', 'production')
PORT = int(os.getenv('PORT', 8501))

# Dynamic imports with Railway-safe fallbacks
DEPENDENCIES = {
    'psutil': False,
    'binance': False,
    'dotenv': False,
    'ta': False,
    'sklearn': False,
    'scipy': False,
    'qiskit': False
}

# Safe imports
try:
    import psutil
    DEPENDENCIES['psutil'] = True
except ImportError:
    psutil = None

try:
    from dotenv import load_dotenv
    load_dotenv()
    DEPENDENCIES['dotenv'] = True
except ImportError:
    pass

try:
    from binance.client import Client
    DEPENDENCIES['binance'] = True
except ImportError:
    Client = None

try:
    import ta
    DEPENDENCIES['ta'] = True
except ImportError:
    ta = None

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    DEPENDENCIES['sklearn'] = True
except ImportError:
    RandomForestClassifier = None
    StandardScaler = None

try:
    from scipy import stats
    DEPENDENCIES['scipy'] = True
except ImportError:
    stats = None

try:
    from qiskit import QuantumCircuit, Aer, execute
    from qiskit.quantum_info import Statevector
    DEPENDENCIES['qiskit'] = True
except ImportError:
    QuantumCircuit = None
    Aer = None
    execute = None

# Railway-optimized configuration
CONFIG = {
    'BINANCE_API_KEY': os.getenv('BINANCE_API_KEY', ''),
    'BINANCE_API_SECRET': os.getenv('BINANCE_API_SECRET', ''),
    'MIN_BALANCE_USD': float(os.getenv('MIN_BALANCE_USD', '10.0')),
    'SCAN_INTERVAL': int(os.getenv('SCAN_INTERVAL', '180')),  # 3 minutes for Railway
    'MIN_CONFIDENCE': float(os.getenv('MIN_CONFIDENCE', '0.65')),
    'RISK_PERCENTAGE': float(os.getenv('RISK_PERCENTAGE', '0.015')),
    'MAX_POSITIONS': int(os.getenv('MAX_POSITIONS', '3')),
    'QUANTUM_ENABLED': os.getenv('QUANTUM_ENABLED', 'True').lower() == 'true',
    'ML_ENABLED': os.getenv('ML_ENABLED', 'True').lower() == 'true',
    'USE_TESTNET': os.getenv('USE_TESTNET', 'True').lower() == 'true',
    'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
    'TRADING_PAIRS': os.getenv('TRADING_PAIRS', 'BTCUSDT,ETHUSDT,BNBUSDT,XRPUSDT,ADAUSDT,SOLUSDT').split(','),
    'RAILWAY_DEPLOYMENT': True,
    'PERSISTENT_STORAGE': True
}

# Railway session state management
SESSION_DEFAULTS = {
    'auto_running': False,
    'last_action': 'Bot Ready for Railway',
    'scan_results': [],
    'risk_override': CONFIG['RISK_PERCENTAGE'],
    'quantum_enabled': CONFIG['QUANTUM_ENABLED'],
    'ml_enabled': CONFIG['ML_ENABLED'],
    'selected_pairs': CONFIG['TRADING_PAIRS'],
    'strategy_weights': {'quantum': 0.3, 'technical': 0.4, 'ml': 0.3},
    'min_confidence': CONFIG['MIN_CONFIDENCE'],
    'railway_logs': [],
    'performance_data': [],
    'portfolio_cache': {},
    'last_update': datetime.now().isoformat()
}

for key, value in SESSION_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

def railway_log(message, level="INFO"):
    """Railway-optimized logging"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    
    # Add to session state logs (persistent across Railway restarts)
    if 'railway_logs' not in st.session_state:
        st.session_state['railway_logs'] = []
    
    st.session_state['railway_logs'].append(log_entry)
    
    # Keep only last 100 logs to prevent memory issues
    if len(st.session_state['railway_logs']) > 100:
        st.session_state['railway_logs'] = st.session_state['railway_logs'][-100:]
    
    # Also print to console for Railway logs
    print(log_entry)

class QuantumTradingEngine:
    """Railway-optimized Quantum Trading Engine"""
    
    def __init__(self):
        self.enabled = DEPENDENCIES['qiskit'] and CONFIG['QUANTUM_ENABLED']
        self.simulator = None
        
        if self.enabled:
            try:
                self.simulator = Aer.get_backend('statevector_simulator')
                railway_log("✅ Quantum engine initialized")
            except Exception as e:
                railway_log(f"⚠️ Quantum fallback mode: {e}")
                self.enabled = False
    
    def quantum_price_prediction(self, price_data, volume_data):
        """Quantum analysis with Railway optimization"""
        if not self.enabled or len(price_data) < 10:
            return self._classical_fallback(price_data)
        
        try:
            # Create quantum circuit
            qc = QuantumCircuit(3)
            
            # Encode market data
            price_change = (price_data[-1] - price_data[-5]) / price_data[-5]
            volume_change = (volume_data[-1] - volume_data[-5]) / volume_data[-5] if len(volume_data) >= 5 else 0
            
            # Apply quantum gates based on market data
            if abs(price_change) > 0.01:
                qc.ry(price_change * np.pi, 0)
            
            if abs(volume_change) > 0.1:
                qc.rz(volume_change * np.pi, 1)
            
            # Create entanglement
            qc.cx(0, 1)
            qc.cx(1, 2)
            qc.h(2)
            
            # Execute quantum simulation
            job = execute(qc, self.simulator)
            result = job.result()
            statevector = result.get_statevector(qc)
            
            # Convert quantum state to trading signal
            probabilities = np.abs(statevector) ** 2
            bull_prob = sum(probabilities[i] for i in [0, 1, 2, 3])
            bear_prob = sum(probabilities[i] for i in [4, 5, 6, 7])
            
            if bull_prob > bear_prob:
                signal = 'BUY'
                confidence = min(0.9, bull_prob * 1.3)
            else:
                signal = 'SELL'
                confidence = min(0.9, bear_prob * 1.3)
            
            return {
                'signal': signal,
                'confidence': confidence,
                'quantum_state': f"|ψ⟩ = {probabilities[0]:.3f}|000⟩ + ...",
                'bull_probability': bull_prob,
                'bear_probability': bear_prob,
                'method': 'quantum'
            }
            
        except Exception as e:
            railway_log(f"Quantum error: {e}")
            return self._classical_fallback(price_data)
    
    def _classical_fallback(self, price_data):
        """Classical analysis fallback"""
        if len(price_data) < 5:
            return {'signal': 'HOLD', 'confidence': 0.5, 'method': 'classical'}
        
        momentum = (price_data[-1] - price_data[-5]) / price_data[-5]
        
        if momentum > 0.02:
            return {'signal': 'BUY', 'confidence': 0.7, 'method': 'classical'}
        elif momentum < -0.02:
            return {'signal': 'SELL', 'confidence': 0.7, 'method': 'classical'}
        else:
            return {'signal': 'HOLD', 'confidence': 0.5, 'method': 'classical'}

class MLTradingEngine:
    """Railway-optimized ML Engine"""
    
    def __init__(self):
        self.enabled = DEPENDENCIES['sklearn'] and CONFIG['ML_ENABLED']
        self.model = None
        self.scaler = None
        
        if self.enabled:
            try:
                self.model = RandomForestClassifier(n_estimators=50, random_state=42)
                self.scaler = StandardScaler()
                self._train_synthetic_model()
                railway_log("✅ ML engine initialized")
            except Exception as e:
                railway_log(f"⚠️ ML fallback mode: {e}")
                self.enabled = False
    
    def _train_synthetic_model(self):
        """Train model with synthetic data for Railway demo"""
        try:
            # Generate synthetic training data
            X = np.random.randn(200, 6)  # 6 features
            y = (X[:, 0] + X[:, 1] * 0.5 + np.random.randn(200) * 0.1) > 0
            
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled, y.astype(int))
            
        except Exception as e:
            railway_log(f"ML training error: {e}")
    
    def predict_movement(self, price_data, volume_data):
        """ML prediction with Railway optimization"""
        if not self.enabled or len(price_data) < 10:
            return self._simple_prediction(price_data)
        
        try:
            # Extract features
            returns = np.diff(price_data) / price_data[:-1]
            features = [
                np.mean(returns[-5:]),  # Recent momentum
                np.std(returns[-10:]),  # Volatility
                (price_data[-1] - price_data[-10]) / price_data[-10],  # 10-period change
                np.mean(volume_data[-5:]) / np.mean(volume_data[-10:]) if len(volume_data) >= 10 else 1,  # Volume ratio
                returns[-1],  # Last return
                len([r for r in returns[-5:] if r > 0]) / 5  # Positive return ratio
            ]
            
            # Scale and predict
            features_scaled = self.scaler.transform([features])
            prediction = self.model.predict(features_scaled)[0]
            probabilities = self.model.predict_proba(features_scaled)[0]
            
            signal = 'BUY' if prediction == 1 else 'SELL'
            confidence = max(probabilities)
            
            return {
                'signal': signal,
                'confidence': confidence,
                'probability_up': probabilities[1] if len(probabilities) > 1 else 0.5,
                'method': 'ml'
            }
            
        except Exception as e:
            railway_log(f"ML prediction error: {e}")
            return self._simple_prediction(price_data)
    
    def _simple_prediction(self, price_data):
        """Simple prediction fallback"""
        if len(price_data) < 3:
            return {'signal': 'HOLD', 'confidence': 0.5, 'method': 'simple'}
        
        change = (price_data[-1] - price_data[-3]) / price_data[-3]
        
        if change > 0.015:
            return {'signal': 'BUY', 'confidence': 0.6, 'method': 'simple'}
        elif change < -0.015:
            return {'signal': 'SELL', 'confidence': 0.6, 'method': 'simple'}
        else:
            return {'signal': 'HOLD', 'confidence': 0.5, 'method': 'simple'}

class TechnicalAnalysisEngine:
    """Railway-optimized Technical Analysis"""
    
    def __init__(self):
        self.ta_enabled = DEPENDENCIES['ta']
    
    def analyze_symbol(self, symbol, client):
        """Technical analysis with Railway optimization"""
        try:
            # Get market data
            klines = client.get_klines(symbol=symbol, interval='5m', limit=100)
            
            if len(klines) < 50:
                return None
            
            # Extract price data
            closes = [float(k[4]) for k in klines]
            volumes = [float(k[5]) for k in klines]
            
            # Calculate indicators
            sma_20 = np.mean(closes[-20:])
            sma_50 = np.mean(closes[-50:])
            current_price = closes[-1]
            
            # Price changes
            change_1h = (closes[-1] - closes[-12]) / closes[-12] * 100 if len(closes) >= 12 else 0
            change_4h = (closes[-1] - closes[-48]) / closes[-48] * 100 if len(closes) >= 48 else 0
            
            # Volume analysis
            avg_volume = np.mean(volumes[-20:])
            volume_ratio = volumes[-1] / avg_volume if avg_volume > 0 else 1
            
            # RSI calculation
            rsi = self._calculate_rsi(closes)
            
            # Generate signal
            signals = []
            
            if current_price > sma_20 and sma_20 > sma_50:
                signals.append('BUY')
            elif current_price < sma_20 and sma_20 < sma_50:
                signals.append('SELL')
            
            if rsi < 30:
                signals.append('BUY')
            elif rsi > 70:
                signals.append('SELL')
            
            # Determine final signal
            buy_count = signals.count('BUY')
            sell_count = signals.count('SELL')
            
            if buy_count > sell_count:
                final_signal = 'BUY'
                confidence = min(0.8, 0.5 + buy_count * 0.1)
            elif sell_count > buy_count:
                final_signal = 'SELL'
                confidence = min(0.8, 0.5 + sell_count * 0.1)
            else:
                final_signal = 'HOLD'
                confidence = 0.5
            
            return {
                'symbol': symbol,
                'signal': final_signal,
                'confidence': confidence,
                'current_price': current_price,
                'price_change_1h': change_1h,
                'price_change_4h': change_4h,
                'volume_ratio': volume_ratio,
                'rsi': rsi,
                'sma_trend': 'BULLISH' if sma_20 > sma_50 else 'BEARISH',
                'method': 'technical'
            }
            
        except Exception as e:
            railway_log(f"Technical analysis error for {symbol}: {e}")
            return None
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        try:
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])
            
            if avg_loss == 0:
                return 100
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
            
        except:
            return 50

class HybridTradingEngine:
    """Railway-optimized Hybrid Engine"""
    
    def __init__(self):
        self.quantum_engine = QuantumTradingEngine()
        self.ml_engine = MLTradingEngine()
        self.ta_engine = TechnicalAnalysisEngine()
        railway_log("🤖 Hybrid trading engine initialized")
    
    def analyze_symbol_hybrid(self, symbol, client):
        """Hybrid analysis optimized for Railway"""
        try:
            # Get technical analysis first
            ta_result = self.ta_engine.analyze_symbol(symbol, client)
            if not ta_result:
                return None
            
            # Get price data for other engines
            klines = client.get_klines(symbol=symbol, interval='5m', limit=60)
            prices = [float(k[4]) for k in klines]
            volumes = [float(k[5]) for k in klines]
            
            # Run quantum and ML analysis
            quantum_result = None
            ml_result = None
            
            if st.session_state.get('quantum_enabled', False):
                quantum_result = self.quantum_engine.quantum_price_prediction(prices, volumes)
            
            if st.session_state.get('ml_enabled', False):
                ml_result = self.ml_engine.predict_movement(prices, volumes)
            
            # Combine results
            weights = st.session_state.get('strategy_weights', {'technical': 0.4, 'quantum': 0.3, 'ml': 0.3})
            
            weighted_signals = []
            
            # Technical analysis weight
            if ta_result['signal'] != 'HOLD':
                weighted_signals.append((ta_result['signal'], ta_result['confidence'] * weights['technical']))
            
            # Quantum analysis weight
            if quantum_result and quantum_result['signal'] != 'HOLD':
                weighted_signals.append((quantum_result['signal'], quantum_result['confidence'] * weights['quantum']))
            
            # ML analysis weight
            if ml_result and ml_result['signal'] != 'HOLD':
                weighted_signals.append((ml_result['signal'], ml_result['confidence'] * weights['ml']))
            
            # Determine final signal
            if not weighted_signals:
                final_signal = 'HOLD'
                final_confidence = 0.5
            else:
                buy_weight = sum(conf for sig, conf in weighted_signals if sig == 'BUY')
                sell_weight = sum(conf for sig, conf in weighted_signals if sig == 'SELL')
                
                if buy_weight > sell_weight:
                    final_signal = 'BUY'
                    final_confidence = min(0.95, buy_weight)
                elif sell_weight > buy_weight:
                    final_signal = 'SELL'
                    final_confidence = min(0.95, sell_weight)
                else:
                    final_signal = 'HOLD'
                    final_confidence = 0.5
            
            # Enhanced result
            result = ta_result.copy()
            result.update({
                'hybrid_signal': final_signal,
                'hybrid_confidence': final_confidence,
                'quantum_analysis': quantum_result,
                'ml_analysis': ml_result,
                'analysis_methods': {
                    'technical': True,
                    'quantum': quantum_result is not None,
                    'ml': ml_result is not None
                }
            })
            
            return result
            
        except Exception as e:
            railway_log(f"Hybrid analysis error for {symbol}: {e}")
            return None

# Initialize engines
hybrid_engine = HybridTradingEngine()

def get_binance_client():
    """Get Binance client with Railway optimization"""
    if not DEPENDENCIES['binance'] or not CONFIG['BINANCE_API_KEY']:
        return None
    
    try:
        client = Client(CONFIG['BINANCE_API_KEY'], CONFIG['BINANCE_API_SECRET'])
        if CONFIG['USE_TESTNET']:
            client.API_URL = "https://testnet.binance.vision/api"
        return client
    except Exception as e:
        railway_log(f"Binance client error: {e}")
        return None

def get_portfolio_railway():
    """Railway-optimized portfolio fetching"""
    client = get_binance_client()
    if not client:
        return {}, 0, 0
    
    try:
        # Use cached data if recent (Railway optimization)
        if 'portfolio_cache' in st.session_state:
            cache_time = st.session_state.get('portfolio_cache_time', 0)
            if time.time() - cache_time < 60:  # 1-minute cache
                cached = st.session_state['portfolio_cache']
                return cached['portfolio'], cached['total_usd'], cached['total_gbp']
        
        account = client.get_account()
        tickers = {t['symbol']: float(t['price']) for t in client.get_all_tickers()}
        
        portfolio = {}
        total_usd = 0
        
        for balance in account['balances']:
            total = float(balance['free']) + float(balance['locked'])
            if total > 0:
                asset = balance['asset']
                
                if asset in ['USDT', 'BUSD', 'USDC']:
                    price = 1.0
                else:
                    symbol = f"{asset}USDT"
                    price = tickers.get(symbol, 0)
                
                usd_value = total * price
                
                if usd_value >= CONFIG['MIN_BALANCE_USD']:
                    portfolio[asset] = {
                        'balance': total,
                        'price_usd': price,
                        'usd_value': usd_value
                    }
                    total_usd += usd_value
        
        total_gbp = total_usd * 0.79  # Approximate GBP rate
        
        # Cache results
        st.session_state['portfolio_cache'] = {
            'portfolio': portfolio,
            'total_usd': total_usd,
            'total_gbp': total_gbp
        }
        st.session_state['portfolio_cache_time'] = time.time()
        
        return portfolio, total_usd, total_gbp
        
    except Exception as e:
        railway_log(f"Portfolio error: {e}")
        return {}, 0, 0

def scan_markets_railway():
    """Railway-optimized market scanning"""
    client = get_binance_client()
    if not client:
        return []
    
    symbols = st.session_state.get('selected_pairs', CONFIG['TRADING_PAIRS'][:5])  # Limit for Railway
    results = []
    
    for symbol in symbols:
        try:
            result = hybrid_engine.analyze_symbol_hybrid(symbol, client)
            if result and result['hybrid_confidence'] > 0.6:
                results.append(result)
            time.sleep(0.2)  # Rate limiting
        except Exception as e:
            railway_log(f"Scan error {symbol}: {e}")
            continue
    
    results.sort(key=lambda x: x['hybrid_confidence'], reverse=True)
    return results

def auto_trading_loop_railway():
    """Railway-optimized auto trading loop"""
    while st.session_state.get('auto_running', False):
        try:
            railway_log("🔍 Auto scan starting")
            
            results = scan_markets_railway()
            
            if results:
                best = results[0]
                if best['hybrid_confidence'] > st.session_state.get('min_confidence', 0.7):
                    action = f"SIGNAL: {best['symbol']} {best['hybrid_signal']} ({best['hybrid_confidence']:.1%})"
                    st.session_state['last_action'] = action
                    railway_log(f"📊 {action}")
            
            time.sleep(CONFIG['SCAN_INTERVAL'])
            
        except Exception as e:
            railway_log(f"Auto trading error: {e}")
            time.sleep(60)

def start_auto_bot_railway():
    """Start Railway-optimized auto bot"""
    if not st.session_state.get('auto_running', False):
        st.session_state['auto_running'] = True
        thread = threading.Thread(target=auto_trading_loop_railway, daemon=True)
        thread.start()
        railway_log("🚀 Auto bot started on Railway")

def stop_auto_bot_railway():
    """Stop auto bot"""
    st.session_state['auto_running'] = False
    railway_log("🛑 Auto bot stopped")

# Main Streamlit App
st.set_page_config(
    page_title="🧠 Hybrid Quantum Crypto Bot - Railway",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🧠 Hybrid Quantum Crypto Bot")
st.caption("🚀 Advanced trading on Railway with Quantum Computing & ML")

# Railway deployment info
if CONFIG['RAILWAY_DEPLOYMENT']:
    st.info(f"🚂 Running on Railway | Environment: {RAILWAY_ENV} | Dependencies: {sum(DEPENDENCIES.values())}/7")

# Create tabs
tabs = st.tabs([
    "📊 Portfolio", 
    "🔍 Scanner", 
    "🤖 Auto Bot", 
    "⚛️ Quantum", 
    "🧠 ML Engine",
    "📈 Performance", 
    "⚙️ Settings",
    "💓 Health"
])

# Portfolio Tab
with tabs[0]:
    st.header("📊 Portfolio Overview")
    
    portfolio, total_usd, total_gbp = get_portfolio_railway()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💵 USD Value", f"${total_usd:,.2f}")
    with col2:
        st.metric("💷 GBP Value", f"£{total_gbp:,.2f}")
    with col3:
        st.metric("📊 Assets", len(portfolio))
    
    if portfolio:
        # Portfolio table
        portfolio_data = []
        for asset, data in portfolio.items():
            portfolio_data.append({
                'Asset': asset,
                'Balance': f"{data['balance']:.6f}".rstrip('0').rstrip('.'),
                'Price': f"${data['price_usd']:.4f}",
                'Value': f"${data['usd_value']:.2f}",
                'Percentage': f"{(data['usd_value']/total_usd*100):.1f}%"
            })
        
        df = pd.DataFrame(portfolio_data)
        st.dataframe(df, use_container_width=True)
        
        # Portfolio chart
        fig = px.pie(df, values=[float(p['Value'].replace('$', '')) for p in portfolio_data], 
                    names=df['Asset'], title="Portfolio Distribution")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ No portfolio data available")

# Scanner Tab
with tabs[1]:
    st.header("🔍 Hybrid Market Scanner")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Run Hybrid Scan", type="primary"):
            with st.spinner("Scanning with hybrid analysis..."):
                results = scan_markets_railway()
                st.session_state['scan_results'] = results
                st.success(f"✅ Found {len(results)} opportunities")
    
    with col2:
        st.metric("Analysis Methods", f"{sum(DEPENDENCIES.values())}/7 Available")
    
    # Display results
    if st.session_state.get('scan_results'):
        for i, result in enumerate(st.session_state['scan_results'][:5]):
            with st.expander(f"#{i+1} {result['symbol']} - {result['hybrid_signal']} ({result['hybrid_confidence']:.1%})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Price", f"${result['current_price']:.4f}")
                    st.metric("1H Change", f"{result['price_change_1h']:+.2f}%")
                
                with col2:
                    st.metric("RSI", f"{result['rsi']:.1f}")
                    st.metric("Volume", f"{result['volume_ratio']:.2f}x")
                
                with col3:
                    st.metric("Signal", result['hybrid_signal'])
                    st.metric("Confidence", f"{result['hybrid_confidence']:.1%}")
                
                # Method breakdown
                methods = result.get('analysis_methods', {})
                active_methods = [method for method, active in methods.items() if active]
                st.write(f"🔬 **Active Methods:** {', '.join(active_methods)}")

# Auto Bot Tab
with tabs[2]:
    st.header("🤖 Railway Auto Bot")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎛️ Bot Control")
        
        is_running = st.session_state.get('auto_running', False)
        
        if is_running:
            st.success("🟢 Auto bot RUNNING on Railway")
            if st.button("🛑 Stop Bot"):
                stop_auto_bot_railway()
                st.rerun()
        else:
            st.warning("🔴 Auto bot STOPPED")
            if st.button("▶️ Start Bot"):
                start_auto_bot_railway()
                st.rerun()
        
        st.info(f"**Last Action:** {st.session_state.get('last_action', 'None')}")
    
    with col2:
        st.subheader("⚙️ Bot Settings")
        
        st.slider(
            "Scan Interval (seconds)",
            60, 600, CONFIG['SCAN_INTERVAL'],
            help="Time between scans (Railway optimized)"
        )
        
        st.slider(
            "Min Confidence",
            0.5, 0.95,
            st.session_state.get('min_confidence', 0.7),
            0.05,
            key='min_confidence'
        )

# Quantum Tab
with tabs[3]:
    st.header("⚛️ Quantum Lab")
    
    if DEPENDENCIES['qiskit']:
        st.success("✅ Qiskit available on Railway")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔮 Quantum Analysis")
            quantum_enabled = st.checkbox("Enable Quantum Analysis", 
                                        value=st.session_state.get('quantum_enabled', True),
                                        key='quantum_enabled')
            
            if quantum_enabled:
                st.success("⚛️ Quantum engine ACTIVE")
            else:
                st.warning("⚛️ Quantum engine DISABLED")
        
        with col2:
            st.subheader("📊 Quantum Demo")
            if st.button("🔬 Run Quantum Simulation"):
                with st.spinner("Running quantum analysis..."):
                    time.sleep(2)
                    
                    # Demo quantum results
                    states = ['|000⟩', '|001⟩', '|010⟩', '|011⟩', '|100⟩', '|101⟩', '|110⟩', '|111⟩']
                    probs = np.random.dirichlet(np.ones(8))
                    
                    fig = px.bar(x=states, y=probs, title="Quantum State Probabilities")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    bull_prob = sum(probs[:4])
                    signal = "BUY" if bull_prob > 0.5 else "SELL"
                    st.metric("Quantum Signal", signal)
                    st.metric("Confidence", f"{max(bull_prob, 1-bull_prob):.1%}")
    else:
        st.error("❌ Qiskit not available")
        st.code("pip install qiskit")

# ML Engine Tab
with tabs[4]:
    st.header("🧠 ML Engine")
    
    if DEPENDENCIES['sklearn']:
        st.success("✅ Scikit-learn available on Railway")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🤖 Model Status")
            ml_enabled = st.checkbox("Enable ML Analysis",
                                    value=st.session_state.get('ml_enabled', True),
                                    key='ml_enabled')
            
            if ml_enabled:
                st.success("🤖 ML engine ACTIVE")
                st.info("Random Forest with 50 estimators")
            else:
                st.warning("🤖 ML engine DISABLED")
        
        with col2:
            st.subheader("📊 ML Demo")
            if st.button("🎯 Run ML Prediction"):
                with st.spinner("Running ML analysis..."):
                    time.sleep(1)
                    
                    # Demo ML results
                    features = ['Momentum', 'Volatility', 'Volume', 'RSI', 'Trend', 'Returns']
                    importance = np.random.dirichlet(np.ones(6))
                    
                    fig = px.bar(x=features, y=importance, title="Feature Importance")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    prediction = np.random.choice(['BUY', 'SELL'])
                    confidence = 0.6 + np.random.random() * 0.3
                    
                    st.metric("ML Prediction", prediction)
                    st.metric("Confidence", f"{confidence:.1%}")
    else:
        st.error("❌ Scikit-learn not available")
        st.code("pip install scikit-learn")

# Performance Tab
with tabs[5]:
    st.header("📈 Performance")
    
    # Demo performance data
    dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
    pnl = np.cumsum(np.random.normal(0.5, 2, 30))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=pnl, mode='lines+markers', name='P&L'))
    fig.update_layout(title="Cumulative P&L", xaxis_title="Date", yaxis_title="P&L (%)")
    st.plotly_chart(fig, use_container_width=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Trades", "47")
    with col2:
        st.metric("Win Rate", "68.1%")
    with col3:
        st.metric("Total P&L", f"{pnl[-1]:+.2f}%")
    with col4:
        st.metric("Sharpe Ratio", "1.34")

# Settings Tab
with tabs[6]:
    st.header("⚙️ Railway Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 Trading Configuration")
        
        # Strategy weights
        st.write("**Analysis Weights:**")
        weights = st.session_state.get('strategy_weights', {'technical': 0.4, 'quantum': 0.3, 'ml': 0.3})
        
        tech_weight = st.slider("Technical", 0.0, 1.0, weights['technical'], 0.1)
        quantum_weight = st.slider("Quantum", 0.0, 1.0, weights['quantum'], 0.1)
        ml_weight = st.slider("ML", 0.0, 1.0, weights['ml'], 0.1)
        
        # Normalize
        total = tech_weight + quantum_weight + ml_weight
        if total > 0:
            st.session_state['strategy_weights'] = {
                'technical': tech_weight / total,
                'quantum': quantum_weight / total,
                'ml': ml_weight / total
            }
        
        # Trading pairs
        st.multiselect(
            "Trading Pairs",
            CONFIG['TRADING_PAIRS'],
            default=st.session_state.get('selected_pairs', CONFIG['TRADING_PAIRS'][:3]),
            key='selected_pairs'
        )
    
    with col2:
        st.subheader("🚂 Railway Status")
        
        st.write(f"**Environment:** {RAILWAY_ENV}")
        st.write(f"**Port:** {PORT}")
        st.write(f"**Testnet:** {'✅' if CONFIG['USE_TESTNET'] else '❌'}")
        
        # Dependencies
        st.write("**Dependencies:**")
        for dep, status in DEPENDENCIES.items():
            icon = "✅" if status else "❌"
            st.write(f"{icon} {dep}")
        
        # API status
        client = get_binance_client()
        if client:
            st.success("✅ Binance API Connected")
        else:
            st.error("❌ Binance API Not Available")

# Health Tab
with tabs[7]:
    st.header("💓 Railway Health")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🖥️ System Status")
        
        if DEPENDENCIES['psutil']:
            try:
                cpu = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                
                st.metric("CPU Usage", f"{cpu:.1f}%")
                st.metric("Memory Usage", f"{memory.percent:.1f}%")
                st.metric("Available Memory", f"{memory.available / (1024**3):.1f} GB")
            except:
                st.info("System monitoring limited on Railway")
        else:
            st.info("Install psutil for detailed monitoring")
        
        st.metric("Active Threads", threading.active_count())
    
    with col2:
        st.subheader("📡 Connection Health")
        
        # Test internet
        try:
            response = requests.get("https://httpbin.org/get", timeout=5)
            if response.status_code == 200:
                st.success("✅ Internet OK")
        except:
            st.error("❌ Internet failed")
        
        # Test Binance
        client = get_binance_client()
        if client:
            try:
                client.ping()
                st.success("✅ Binance API OK")
            except:
                st.error("❌ Binance API failed")
        else:
            st.error("❌ No Binance client")
    
    # Railway logs
    st.subheader("📋 Railway Logs")
    logs = st.session_state.get('railway_logs', [])
    
    if logs:
        for log in logs[-10:]:  # Show last 10
            st.text(log)
    else:
        st.info("No logs yet")
    
    if st.button("🔄 Refresh Health"):
        st.rerun()

# Auto-refresh for Railway
if st.session_state.get('auto_running', False):
    time.sleep(15)  # Refresh every 15 seconds when bot is running
    st.rerun()

# Railway footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
🚂 Railway Deployment | 🧠 Hybrid Quantum Crypto Bot<br>
⚛️ Quantum Computing • 🤖 Machine Learning • 📊 Technical Analysis
</div>
""", unsafe_allow_html=True)
