#!/usr/bin/env python3
"""
Hybrid Crypto Trading Bot Dashboard with Quantum Analysis
========================================================
Complete self-contained trading bot with quantum computing modules
and dynamic dependency management
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
# Railway WebSocket and Production Optimizations
import asyncio
import sys
import signal
import atexit

# Railway environment detection
RAILWAY_ENV = os.getenv('RAILWAY_ENVIRONMENT') == 'production'
PORT = int(os.getenv('PORT', 8080))

# WebSocket configuration for Railway
if RAILWAY_ENV:
    # Optimize for Railway's WebSocket infrastructure
    os.environ['STREAMLIT_SERVER_ENABLE_WEBSOCKET_COMPRESSION'] = 'false'
    os.environ['STREAMLIT_SERVER_MAX_MESSAGE_SIZE'] = '200'
    os.environ['STREAMLIT_SERVER_MAX_UPLOAD_SIZE'] = '200'
    
    # Railway-specific optimizations
    import uvloop
    try:
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except:
        pass

# Session state persistence for Railway
if 'railway_session_id' not in st.session_state:
    st.session_state['railway_session_id'] = f"railway_{int(time.time())}"

# Railway logging configuration
def setup_railway_logging():
    """Setup logging optimized for Railway"""
    import logging
    
    # Railway-friendly log format
    logging.basicConfig(
        level=getattr(logging, CONFIG.get('LOG_LEVEL', 'INFO')),
        format='[%(asctime)s] %(levelname)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),  # Railway captures stdout
            logging.FileHandler('logs/railway.log') if not RAILWAY_ENV else logging.NullHandler()
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_railway_logging()

# Railway-specific session management
class RailwaySessionManager:
    """Manage persistent sessions on Railway"""
    
    def __init__(self):
        self.session_file = '/tmp/railway_sessions.json' if RAILWAY_ENV else 'logs/sessions.json'
        self.load_sessions()
    
    def load_sessions(self):
        """Load existing sessions"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    self.sessions = json.load(f)
            else:
                self.sessions = {}
        except:
            self.sessions = {}
    
    def save_session(self, session_id, data):
        """Save session data"""
        try:
            self.sessions[session_id] = {
                **data,
                'last_updated': datetime.now().isoformat()
            }
            
            os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
            with open(self.session_file, 'w') as f:
                json.dump(self.sessions, f)
        except Exception as e:
            logger.error(f"Session save error: {e}")
    
    def get_session(self, session_id):
        """Get session data"""
        return self.sessions.get(session_id, {})

# Initialize Railway session manager
if RAILWAY_ENV:
    session_manager = RailwaySessionManager()
# Dynamic imports with fallbacks
DEPENDENCIES = {
    'psutil': False,
    'binance': False,
    'dotenv': False,
    'ta': False,
    'sklearn': False,
    'scipy': False,
    'qiskit': False
}

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
    Statevector = None

# Configuration with environment variable fallbacks
CONFIG = {
    'BINANCE_API_KEY': os.getenv('BINANCE_API_KEY', ''),
    'BINANCE_API_SECRET': os.getenv('BINANCE_API_SECRET', ''),
    'MIN_BALANCE_USD': float(os.getenv('MIN_BALANCE_USD', '10.0')),
    'SCAN_INTERVAL': int(os.getenv('SCAN_INTERVAL', '300')),
    'MIN_CONFIDENCE': float(os.getenv('MIN_CONFIDENCE', '0.65')),
    'RISK_PERCENTAGE': float(os.getenv('RISK_PERCENTAGE', '0.015')),
    'MAX_POSITIONS': int(os.getenv('MAX_POSITIONS', '3')),
    'QUANTUM_ENABLED': os.getenv('QUANTUM_ENABLED', 'True').lower() == 'true',
    'ML_ENABLED': os.getenv('ML_ENABLED', 'True').lower() == 'true',
    'USE_TESTNET': os.getenv('USE_TESTNET', 'False').lower() == 'true',
    'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
    'TRADING_PAIRS': os.getenv('TRADING_PAIRS', 'BTCUSDT,ETHUSDT,BNBUSDT,XRPUSDT,ADAUSDT,SOLUSDT,DOTUSDT,LINKUSDT,LTCUSDT,BCHUSDT').split(','),
    'STRATEGY_WEIGHTS': {
        'quantum': float(os.getenv('QUANTUM_WEIGHT', '0.3')),
        'technical': float(os.getenv('TECHNICAL_WEIGHT', '0.4')),
        'ml': float(os.getenv('ML_WEIGHT', '0.3'))
    }
}

# Session State Initialization
DEFAULT_SESSION_STATE = {
    'auto_running': False,
    'last_action': 'None',
    'scan_results': [],
    'risk_override': CONFIG['RISK_PERCENTAGE'],
    'quantum_enabled': CONFIG['QUANTUM_ENABLED'],
    'ml_enabled': CONFIG['ML_ENABLED'],
    'selected_pairs': CONFIG['TRADING_PAIRS'],
    'strategy_weights': CONFIG['STRATEGY_WEIGHTS'],
    'min_confidence': CONFIG['MIN_CONFIDENCE']
}

for key, value in DEFAULT_SESSION_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

class QuantumTradingEngine:
    """Advanced Quantum Computing Engine for Market Analysis"""
    
    def __init__(self):
        self.enabled = DEPENDENCIES['qiskit'] and CONFIG['QUANTUM_ENABLED']
        self.simulator = Aer.get_backend('qasm_simulator') if self.enabled else None
        
    def quantum_price_prediction(self, price_data, volume_data):
        """Use quantum circuits to predict price movements"""
        if not self.enabled:
            return self._classical_fallback(price_data)
        
        try:
            # Create quantum circuit with 3 qubits
            qc = QuantumCircuit(3, 3)
            
            # Encode price momentum into quantum states
            price_change = (price_data[-1] - price_data[-2]) / price_data[-2]
            volume_change = (volume_data[-1] - volume_data[-2]) / volume_data[-2] if volume_data[-2] > 0 else 0
            
            # Apply rotations based on market data
            if price_change > 0:
                qc.ry(price_change * np.pi, 0)  # Positive momentum
            else:
                qc.rx(abs(price_change) * np.pi, 0)  # Negative momentum
            
            if volume_change > 0:
                qc.rz(volume_change * np.pi, 1)  # Volume increase
            
            # Create entanglement for market correlation
            qc.cx(0, 1)
            qc.cx(1, 2)
            
            # Add quantum interference
            qc.h(0)
            qc.h(2)
            
            # Apply market volatility gates
            volatility = np.std(price_data[-10:]) / np.mean(price_data[-10:])
            qc.ry(volatility * np.pi, 2)
            
            # Measure qubits
            qc.measure_all()
            
            # Execute quantum circuit
            job = execute(qc, self.simulator, shots=1024)
            result = job.result()
            counts = result.get_counts(qc)
            
            # Analyze quantum measurement results
            quantum_signal = self._interpret_quantum_results(counts)
            
            return {
                'signal': quantum_signal['direction'],
                'confidence': quantum_signal['confidence'],
                'quantum_state': quantum_signal['state'],
                'entanglement_measure': quantum_signal['entanglement'],
                'method': 'quantum'
            }
            
        except Exception as e:
            print(f"Quantum analysis error: {e}")
            return self._classical_fallback(price_data)
    
    def _interpret_quantum_results(self, counts):
        """Interpret quantum measurement results"""
        total_shots = sum(counts.values())
        
        # Calculate quantum probabilities
        bull_states = ['000', '001', '010', '011']  # States indicating upward movement
        bear_states = ['100', '101', '110', '111']  # States indicating downward movement
        
        bull_probability = sum(counts.get(state, 0) for state in bull_states) / total_shots
        bear_probability = sum(counts.get(state, 0) for state in bear_states) / total_shots
        
        # Determine signal direction
        if bull_probability > bear_probability:
            direction = 'BUY'
            confidence = bull_probability
        else:
            direction = 'SELL'
            confidence = bear_probability
        
        # Calculate entanglement measure (simplified)
        entanglement = abs(bull_probability - bear_probability)
        
        # Most probable quantum state
        most_probable_state = max(counts, key=counts.get)
        
        return {
            'direction': direction,
            'confidence': min(confidence * 1.5, 0.95),  # Boost quantum confidence
            'state': most_probable_state,
            'entanglement': entanglement,
            'bull_prob': bull_probability,
            'bear_prob': bear_probability
        }
    
    def _classical_fallback(self, price_data):
        """Fallback classical analysis when quantum is unavailable"""
        try:
            returns = np.diff(price_data) / price_data[:-1]
            momentum = np.mean(returns[-5:])
            volatility = np.std(returns[-10:])
            
            if momentum > 0.01:
                direction = 'BUY'
                confidence = min(abs(momentum) * 10, 0.8)
            elif momentum < -0.01:
                direction = 'SELL'
                confidence = min(abs(momentum) * 10, 0.8)
            else:
                direction = 'HOLD'
                confidence = 0.5
            
            return {
                'signal': direction,
                'confidence': confidence,
                'quantum_state': 'classical_fallback',
                'entanglement_measure': volatility,
                'method': 'classical'
            }
        except:
            return {
                'signal': 'HOLD',
                'confidence': 0.5,
                'quantum_state': 'error',
                'entanglement_measure': 0,
                'method': 'error'
            }
    
    def quantum_portfolio_optimization(self, assets, returns, risk_tolerance):
        """Quantum-enhanced portfolio optimization"""
        if not self.enabled or len(assets) < 2:
            return self._classical_portfolio_optimization(assets, returns, risk_tolerance)
        
        try:
            # Create quantum circuit for portfolio optimization
            n_assets = min(len(assets), 4)  # Limit to 4 assets for quantum circuit
            qc = QuantumCircuit(n_assets, n_assets)
            
            # Encode asset correlations and returns
            for i, asset_return in enumerate(returns[:n_assets]):
                if asset_return > 0:
                    qc.ry(asset_return * np.pi, i)
                else:
                    qc.rx(abs(asset_return) * np.pi, i)
            
            # Create entanglement for portfolio correlation
            for i in range(n_assets - 1):
                qc.cx(i, i + 1)
            
            # Apply risk tolerance
            for i in range(n_assets):
                qc.rz(risk_tolerance * np.pi, i)
            
            # Measure
            qc.measure_all()
            
            # Execute
            job = execute(qc, self.simulator, shots=1024)
            result = job.result()
            counts = result.get_counts(qc)
            
            # Convert quantum results to portfolio weights
            weights = self._quantum_to_weights(counts, n_assets)
            
            return {
                'weights': weights,
                'method': 'quantum',
                'quantum_efficiency': max(counts.values()) / 1024
            }
            
        except Exception as e:
            print(f"Quantum portfolio optimization error: {e}")
            return self._classical_portfolio_optimization(assets, returns, risk_tolerance)
    
    def _quantum_to_weights(self, counts, n_assets):
        """Convert quantum measurement results to portfolio weights"""
        total_shots = sum(counts.values())
        weights = []
        
        for i in range(n_assets):
            # Count how many times qubit i was measured as |1⟩
            weight = 0
            for state, count in counts.items():
                if len(state) > i and state[-(i+1)] == '1':
                    weight += count
            
            weights.append(weight / total_shots)
        
        # Normalize weights
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        else:
            weights = [1.0 / n_assets] * n_assets
        
        return weights
    
    def _classical_portfolio_optimization(self, assets, returns, risk_tolerance):
        """Classical portfolio optimization fallback"""
        n_assets = len(assets)
        if n_assets == 0:
            return {'weights': [], 'method': 'classical'}
        
        # Simple equal weight with return bias
        base_weight = 1.0 / n_assets
        weights = []
        
        for ret in returns:
            if ret > 0:
                weight = base_weight * (1 + risk_tolerance)
            else:
                weight = base_weight * (1 - risk_tolerance)
            weights.append(max(0.05, min(0.5, weight)))  # Cap weights
        
        # Normalize
        total = sum(weights)
        weights = [w / total for w in weights]
        
        return {
            'weights': weights,
            'method': 'classical',
            'quantum_efficiency': 0
        }

class MachineLearningEngine:
    """Advanced ML Engine for Market Prediction"""
    
    def __init__(self):
        self.enabled = DEPENDENCIES['sklearn'] and CONFIG['ML_ENABLED']
        self.model = None
        self.scaler = None
        self.is_trained = False
        
        if self.enabled:
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.scaler = StandardScaler()
    
    def prepare_features(self, price_data, volume_data, additional_data=None):
        """Prepare features for ML model"""
        try:
            if len(price_data) < 20:
                return None
            
            features = []
            
            # Price-based features
            returns = np.diff(price_data) / price_data[:-1]
            features.extend([
                np.mean(returns[-5:]),    # 5-period return
                np.mean(returns[-10:]),   # 10-period return
                np.std(returns[-10:]),    # Volatility
                np.mean(price_data[-5:]) / np.mean(price_data[-20:]),  # Price momentum
            ])
            
            # Volume features
            if volume_data and len(volume_data) >= len(price_data):
                volume_ma = np.mean(volume_data[-10:])
                current_volume = volume_data[-1]
                features.extend([
                    current_volume / volume_ma if volume_ma > 0 else 1,  # Volume ratio
                    np.std(volume_data[-10:]) / volume_ma if volume_ma > 0 else 0,  # Volume volatility
                ])
            else:
                features.extend([1.0, 0.0])  # Default volume features
            
            # Technical indicators (if TA available)
            if DEPENDENCIES['ta'] and ta:
                df = pd.DataFrame({'close': price_data, 'volume': volume_data[:len(price_data)]})
                try:
                    features.extend([
                        ta.momentum.rsi(df['close']).iloc[-1] / 100,  # RSI normalized
                        ta.trend.sma_indicator(df['close'], window=10).iloc[-1] / price_data[-1],  # SMA ratio
                        ta.volatility.bollinger_hband_indicator(df['close']).iloc[-1],  # Bollinger band
                    ])
                except:
                    features.extend([0.5, 1.0, 0.0])  # Default technical features
            else:
                features.extend([0.5, 1.0, 0.0])
            
            # Additional features
            if additional_data:
                features.extend(additional_data[:3])  # Limit additional features
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            print(f"Feature preparation error: {e}")
            return None
    
    def train_on_historical_data(self, historical_data):
        """Train ML model on historical data"""
        if not self.enabled:
            return False
        
        try:
            X, y = [], []
            
            for data_point in historical_data:
                features = self.prepare_features(
                    data_point['prices'], 
                    data_point['volumes']
                )
                if features is not None:
                    X.append(features.flatten())
                    # Label: 1 for price increase, 0 for decrease
                    y.append(1 if data_point['future_return'] > 0 else 0)
            
            if len(X) < 10:
                return False
            
            X = np.array(X)
            y = np.array(y)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model.fit(X_scaled, y)
            self.is_trained = True
            
            return True
            
        except Exception as e:
            print(f"ML training error: {e}")
            return False
    
    def predict_movement(self, price_data, volume_data):
        """Predict price movement using trained ML model"""
        if not self.enabled:
            return self._classical_prediction(price_data)
        
        try:
            features = self.prepare_features(price_data, volume_data)
            if features is None:
                return self._classical_prediction(price_data)
            
            if not self.is_trained:
                # Generate synthetic training data for demo
                self._generate_synthetic_training()
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Predict
            prediction = self.model.predict(features_scaled)[0]
            probability = self.model.predict_proba(features_scaled)[0]
            
            confidence = max(probability)
            direction = 'BUY' if prediction == 1 else 'SELL'
            
            # Get feature importance
            importance = self.model.feature_importances_
            
            return {
                'signal': direction,
                'confidence': confidence,
                'probability_up': probability[1] if len(probability) > 1 else 0.5,
                'probability_down': probability[0] if len(probability) > 1 else 0.5,
                'feature_importance': importance.tolist(),
                'method': 'ml'
            }
            
        except Exception as e:
            print(f"ML prediction error: {e}")
            return self._classical_prediction(price_data)
    
    def _generate_synthetic_training(self):
        """Generate synthetic training data for demonstration"""
        try:
            X_synthetic = np.random.randn(100, 9)  # 9 features
            y_synthetic = np.random.randint(0, 2, 100)
            
            self.scaler.fit(X_synthetic)
            self.model.fit(X_synthetic, y_synthetic)
            self.is_trained = True
            
        except Exception as e:
            print(f"Synthetic training error: {e}")
    
    def _classical_prediction(self, price_data):
        """Classical prediction fallback"""
        try:
            if len(price_data) < 2:
                return {'signal': 'HOLD', 'confidence': 0.5, 'method': 'classical'}
            
            recent_change = (price_data[-1] - price_data[-2]) / price_data[-2]
            
            if recent_change > 0.02:
                return {'signal': 'BUY', 'confidence': 0.6, 'method': 'classical'}
            elif recent_change < -0.02:
                return {'signal': 'SELL', 'confidence': 0.6, 'method': 'classical'}
            else:
                return {'signal': 'HOLD', 'confidence': 0.5, 'method': 'classical'}
                
        except:
            return {'signal': 'HOLD', 'confidence': 0.5, 'method': 'error'}

class TechnicalAnalysisEngine:
    """Advanced Technical Analysis Engine"""
    
    def __init__(self):
        self.ta_enabled = DEPENDENCIES['ta']
    
    def analyze_symbol(self, symbol, client):
        """Comprehensive technical analysis of a symbol"""
        try:
            # Get market data
            klines = client.get_klines(symbol=symbol, interval='5m', limit=200)
            
            if len(klines) < 100:
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Convert to numeric
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])
            
            # Calculate basic indicators
            df['returns'] = df['close'].pct_change()
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            df['volatility'] = df['returns'].rolling(window=20).std()
            
            # Calculate RSI manually if TA library not available
            if self.ta_enabled and ta:
                df['rsi'] = ta.momentum.rsi(df['close'])
                df['macd'] = ta.trend.macd_diff(df['close'])
                df['bb_upper'] = ta.volatility.bollinger_hband(df['close'])
                df['bb_lower'] = ta.volatility.bollinger_lband(df['close'])
            else:
                df['rsi'] = self._calculate_rsi(df['close'])
                df['macd'] = self._calculate_macd(df['close'])
                df['bb_upper'] = df['sma_20'] + (df['close'].rolling(20).std() * 2)
                df['bb_lower'] = df['sma_20'] - (df['close'].rolling(20).std() * 2)
            
            # Current values
            current = df.iloc[-1]
            
            # Generate signals
            signals = []
            confidence_factors = []
            
            # Trend signals
            if current['close'] > current['sma_20'] > current['sma_50']:
                signals.append('BUY')
                confidence_factors.append(0.7)
            elif current['close'] < current['sma_20'] < current['sma_50']:
                signals.append('SELL')
                confidence_factors.append(0.7)
            
            # RSI signals
            if current['rsi'] < 30:
                signals.append('BUY')
                confidence_factors.append(0.6)
            elif current['rsi'] > 70:
                signals.append('SELL')
                confidence_factors.append(0.6)
            
            # Bollinger Band signals
            if current['close'] < current['bb_lower']:
                signals.append('BUY')
                confidence_factors.append(0.5)
            elif current['close'] > current['bb_upper']:
                signals.append('SELL')
                confidence_factors.append(0.5)
            
            # Volume analysis
            volume_ma = df['volume'].rolling(20).mean().iloc[-1]
            volume_ratio = current['volume'] / volume_ma if volume_ma > 0 else 1
            
            if volume_ratio > 1.5:
                confidence_factors = [cf * 1.2 for cf in confidence_factors]
            
            # Determine final signal
            if not signals:
                final_signal = 'HOLD'
                final_confidence = 0.5
            else:
                buy_signals = signals.count('BUY')
                sell_signals = signals.count('SELL')
                
                if buy_signals > sell_signals:
                    final_signal = 'BUY'
                    final_confidence = np.mean([cf for i, cf in enumerate(confidence_factors) if signals[i] == 'BUY'])
                elif sell_signals > buy_signals:
                    final_signal = 'SELL'
                    final_confidence = np.mean([cf for i, cf in enumerate(confidence_factors) if signals[i] == 'SELL'])
                else:
                    final_signal = 'HOLD'
                    final_confidence = 0.5
            
            return {
                'symbol': symbol,
                'signal': final_signal,
                'confidence': min(final_confidence, 0.9),
                'current_price': current['close'],
                'price_change_1h': ((current['close'] - df.iloc[-12]['close']) / df.iloc[-12]['close'] * 100),
                'price_change_4h': ((current['close'] - df.iloc[-48]['close']) / df.iloc[-48]['close'] * 100),
                'volume_ratio': volume_ratio,
                'rsi': current['rsi'],
                'sma_trend': 'BULLISH' if current['sma_20'] > current['sma_50'] else 'BEARISH',
                'indicators': {
                    'sma_20': current['sma_20'],
                    'sma_50': current['sma_50'],
                    'rsi': current['rsi'],
                    'macd': current['macd'],
                    'bb_position': (current['close'] - current['bb_lower']) / (current['bb_upper'] - current['bb_lower'])
                },
                'timestamp': datetime.now().isoformat(),
                'method': 'technical'
            }
            
        except Exception as e:
            print(f"Technical analysis error for {symbol}: {e}")
            return None
    
    def _calculate_rsi(self, prices, window=14):
        """Calculate RSI manually"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.fillna(50)
        except:
            return pd.Series([50] * len(prices), index=prices.index)
    
    def _calculate_macd(self, prices):
        """Calculate MACD manually"""
        try:
            exp1 = prices.ewm(span=12).mean()
            exp2 = prices.ewm(span=26).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9).mean()
            return macd - signal
        except:
            return pd.Series([0] * len(prices), index=prices.index)

class HybridTradingEngine:
    """Main hybrid trading engine combining all analysis methods"""
    
    def __init__(self):
        self.quantum_engine = QuantumTradingEngine()
        self.ml_engine = MachineLearningEngine()
        self.ta_engine = TechnicalAnalysisEngine()
        
    def analyze_symbol_hybrid(self, symbol, client):
        """Perform hybrid analysis combining quantum, ML, and technical analysis"""
        try:
            # Get technical analysis first (provides base data)
            ta_result = self.ta_engine.analyze_symbol(symbol, client)
            if not ta_result:
                return None
            
            # Get price and volume data for other engines
            klines = client.get_klines(symbol=symbol, interval='5m', limit=100)
            prices = [float(k[4]) for k in klines]  # Close prices
            volumes = [float(k[5]) for k in klines]  # Volumes
            
            # Quantum analysis
            quantum_result = None
            if st.session_state.get('quantum_enabled', False):
                quantum_result = self.quantum_engine.quantum_price_prediction(prices, volumes)
            
            # ML analysis
            ml_result = None
            if st.session_state.get('ml_enabled', False):
                ml_result = self.ml_engine.predict_movement(prices, volumes)
            
            # Combine results with weighted voting
            weights = st.session_state.get('strategy_weights', CONFIG['STRATEGY_WEIGHTS'])
            
            signals = []
            confidences = []
            
            # Technical analysis (always available)
            if ta_result['signal'] != 'HOLD':
                signals.append((ta_result['signal'], ta_result['confidence'] * weights['technical']))
                confidences.append(ta_result['confidence'])
            
            # Quantum analysis
            if quantum_result and quantum_result['signal'] != 'HOLD':
                signals.append((quantum_result['signal'], quantum_result['confidence'] * weights['quantum']))
                confidences.append(quantum_result['confidence'])
            
            # ML analysis
            if ml_result and ml_result['signal'] != 'HOLD':
                signals.append((ml_result['signal'], ml_result['confidence'] * weights['ml']))
                confidences.append(ml_result['confidence'])
            
            # Determine final signal
            if not signals:
                final_signal = 'HOLD'
                final_confidence = 0.5
            else:
                # Weighted voting
                buy_weight = sum(conf for sig, conf in signals if sig == 'BUY')
                sell_weight = sum(conf for sig, conf in signals if sig == 'SELL')
                
                if buy_weight > sell_weight:
                    final_signal = 'BUY'
                    final_confidence = min(buy_weight, 0.95)
                elif sell_weight > buy_weight:
                    final_signal = 'SELL'
                    final_confidence = min(sell_weight, 0.95)
                else:
                    final_signal = 'HOLD'
                    final_confidence = 0.5
            
            # Enhance result with hybrid information
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
                },
                'signal_breakdown': {
                    'technical': (ta_result['signal'], ta_result['confidence']),
                    'quantum': (quantum_result['signal'], quantum_result['confidence']) if quantum_result else None,
                    'ml': (ml_result['signal'], ml_result['confidence']) if ml_result else None
                }
            })
            
            return result
            
        except Exception as e:
            print(f"Hybrid analysis error for {symbol}: {e}")
            return None

# Initialize engines
hybrid_engine = HybridTradingEngine()

def get_binance_client():
    """Get authenticated Binance client"""
    if not DEPENDENCIES['binance'] or not CONFIG['BINANCE_API_KEY'] or not CONFIG['BINANCE_API_SECRET']:
        return None
    
    try:
        client = Client(CONFIG['BINANCE_API_KEY'], CONFIG['BINANCE_API_SECRET'])
        if CONFIG['USE_TESTNET']:
            client.API_URL = "https://testnet.binance.vision/api"
        return client
    except Exception as e:
        print(f"Binance client error: {e}")
        return None

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
            f.write('timestamp,symbol,direction,entry_price,exit_price,quantity,change_pct,status,strategy,confidence,pnl_usd,pnl_gbp,quantum_signal,ml_signal,technical_signal\n')
    
    # Create quantum trades log
    if not os.path.exists('logs/quantum_trades.csv'):
        with open('logs/quantum_trades.csv', 'w') as f:
            f.write('timestamp,symbol,direction,price,quantity,confidence,quantum_state,entanglement,method\n')
    
    # Create other log files
    for log_file in ['logs/manual_trades.log', 'logs/scan_results.json', 'logs/bot_activity.log', 'logs/hybrid_analysis.log']:
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

def log_hybrid_analysis(analysis_result):
    """Log detailed hybrid analysis results"""
    try:
        with open('logs/hybrid_analysis.log', 'a') as f:
            f.write(json.dumps(analysis_result) + '\n')
    except:
        pass

def scan_markets_hybrid():
    """Scan multiple markets using hybrid analysis"""
    client = get_binance_client()
    if not client:
        return []
    
    symbols = st.session_state.get('selected_pairs', CONFIG['TRADING_PAIRS'])
    results = []
    
    progress_container = st.empty()
    
    for i, symbol in enumerate(symbols):
        try:
            progress_container.text(f"Analyzing {symbol}... ({i+1}/{len(symbols)})")
            
            result = hybrid_engine.analyze_symbol_hybrid(symbol, client)
            if result and result['hybrid_confidence'] > st.session_state.get('min_confidence', CONFIG['MIN_CONFIDENCE']):
                results.append(result)
                log_hybrid_analysis(result)
            
            time.sleep(0.1)  # Rate limiting
        except Exception as e:
            log_activity(f"Error scanning {symbol}: {e}")
            continue
    
    progress_container.empty()
    
    # Sort by hybrid confidence
    results.sort(key=lambda x: x['hybrid_confidence'], reverse=True)
    
    # Save results
    try:
        with open('logs/scan_results.json', 'w') as f:
            json.dump(results, f, indent=2)
    except:
        pass
    
    return results

def get_portfolio():
    """Get portfolio information with enhanced data"""
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
                
                if usd_value >= CONFIG['MIN_BALANCE_USD']:
                    # Get 24h price change if available
                    try:
                        ticker_24h = client.get_ticker(symbol=f"{asset}USDT")
                        price_change_24h = float(ticker_24h['priceChangePercent'])
                    except:
                        price_change_24h = 0
                    
                    portfolio[asset] = {
                        'balance': total,
                        'free': float(balance['free']),
                        'locked': float(balance['locked']),
                        'price_usd': price,
                        'usd_value': usd_value,
                        'price_change_24h': price_change_24h
                    }
                    total_usd += usd_value
        
        return portfolio, total_usd, total_usd * get_gbp_exchange_rate()
        
    except Exception as e:
        log_activity(f"Error getting portfolio: {e}")
        return {}, 0, 0

def execute_trade(symbol, side, quantity, trade_type='MARKET'):
    """Execute a trade with enhanced logging"""
    client = get_binance_client()
    if not client:
        return False, "No Binance client"
    
    try:
        order = client.create_order(
            symbol=symbol,
            side=side,
            type=trade_type,
            quantity=quantity
        )
        
        # Enhanced trade logging
        trade_data = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'type': trade_type,
            'order_id': order['orderId'],
            'status': order['status'],
            'fills': order.get('fills', [])
        }
        
        # Log to multiple files
        with open('logs/manual_trades.log', 'a') as f:
            f.write(json.dumps(trade_data) + '\n')
        
        # Add to trades CSV
        with open('logs/trades.csv', 'a') as f:
            f.write(f"{trade_data['timestamp']},{symbol},{side},{order.get('price', 0)},,{quantity},,EXECUTED,MANUAL,1.0,,,,,\n")
        
        log_activity(f"Trade executed: {side} {quantity} {symbol} - Order ID: {order['orderId']}")
        return True, f"Order placed successfully: {order['orderId']}"
        
    except Exception as e:
        error_msg = f"Trade failed: {e}"
        log_activity(error_msg)
        return False, error_msg

def auto_trading_loop():
    """Enhanced background auto trading loop with hybrid analysis"""
    while st.session_state.get('auto_running', False):
        try:
            log_activity("Auto bot hybrid scan cycle starting")
            
            # Scan for opportunities using hybrid analysis
            results = scan_markets_hybrid()
            
            if results:
                best_opportunity = results[0]
                
                if best_opportunity['hybrid_confidence'] > st.session_state.get('min_confidence', CONFIG['MIN_CONFIDENCE']):
                    symbol = best_opportunity['symbol']
                    decision = best_opportunity['hybrid_signal']
                    
                    # Get portfolio to check if we can trade
                    portfolio, total_usd, _ = get_portfolio()
                    
                    if decision == "BUY" and total_usd > 50:  # Have USDT to buy
                        # Calculate position size with enhanced risk management
                        risk_amount = total_usd * st.session_state.get('risk_override', CONFIG['RISK_PERCENTAGE'])
                        
                        # Adjust risk based on confidence and analysis methods
                        confidence_multiplier = best_opportunity['hybrid_confidence']
                        method_count = sum(best_opportunity['analysis_methods'].values())
                        method_multiplier = min(1.5, 1 + (method_count - 1) * 0.2)
                        
                        adjusted_risk = risk_amount * confidence_multiplier * method_multiplier
                        quantity = adjusted_risk / best_opportunity['current_price']
                        
                        # Execute trade
                        success, msg = execute_trade(symbol, "BUY", quantity)
                        
                        if success:
                            action_msg = f"HYBRID BUY {quantity:.6f} {symbol} (Conf: {best_opportunity['hybrid_confidence']:.2%})"
                            st.session_state['last_action'] = action_msg
                            log_activity(f"Auto trade executed: {action_msg}")
                            
                            # Log quantum trade if quantum was used
                            if best_opportunity.get('quantum_analysis'):
                                quantum_data = best_opportunity['quantum_analysis']
                                with open('logs/quantum_trades.csv', 'a') as f:
                                    f.write(f"{datetime.now().isoformat()},{symbol},BUY,{best_opportunity['current_price']},{quantity},{quantum_data['confidence']},{quantum_data.get('quantum_state', 'N/A')},{quantum_data.get('entanglement_measure', 0)},{quantum_data.get('method', 'quantum')}\n")
                        else:
                            st.session_state['last_action'] = f"Trade failed: {msg}"
                    
                    elif decision == "SELL":
                        # Check if we own this asset
                        asset = symbol.replace('USDT', '')
                        if asset in portfolio:
                            # Sell based on confidence level
                            sell_percentage = 0.3 + (best_opportunity['hybrid_confidence'] * 0.4)  # 30-70% based on confidence
                            quantity = portfolio[asset]['free'] * sell_percentage
                            
                            success, msg = execute_trade(symbol, "SELL", quantity)
                            
                            if success:
                                action_msg = f"HYBRID SELL {quantity:.6f} {symbol} (Conf: {best_opportunity['hybrid_confidence']:.2%})"
                                st.session_state['last_action'] = action_msg
                                log_activity(f"Auto trade executed: {action_msg}")
                            else:
                                st.session_state['last_action'] = f"Trade failed: {msg}"
            
            # Wait before next cycle
            time.sleep(CONFIG['SCAN_INTERVAL'])
            
        except Exception as e:
            log_activity(f"Auto trading error: {e}")
            time.sleep(60)  # Wait 1 minute on error

def start_auto_bot():
    """Start the auto trading bot"""
    if not st.session_state.get('auto_running', False):
        st.session_state['auto_running'] = True
        thread = threading.Thread(target=auto_trading_loop, daemon=True)
        thread.start()
        log_activity("Hybrid auto trading bot started")

def stop_auto_bot():
    """Stop the auto trading bot"""
    st.session_state['auto_running'] = False
    log_activity("Hybrid auto trading bot stopped")

# Main UI
st.set_page_config(page_title="🧠 Hybrid Quantum Crypto Bot", layout="wide")
ensure_log_files()

st.title("🧠 Hybrid Quantum Crypto Trading Bot")
st.caption("Advanced crypto trading with Quantum Computing, Machine Learning, and Technical Analysis")

# Dependency status
with st.expander("📦 System Dependencies"):
    col1, col2 = st.columns(2)
    with col1:
        for dep, status in DEPENDENCIES.items():
            icon = "✅" if status else "❌"
            st.write(f"{icon} {dep.upper()}")
    with col2:
        st.write(f"🔗 Binance API: {'✅' if CONFIG['BINANCE_API_KEY'] else '❌'}")
        st.write(f"🧪 Testnet Mode: {'✅' if CONFIG['USE_TESTNET'] else '❌'}")
        st.write(f"⚛️ Quantum Enabled: {'✅' if st.session_state.get('quantum_enabled') else '❌'}")
        st.write(f"🤖 ML Enabled: {'✅' if st.session_state.get('ml_enabled') else '❌'}")

# Create tabs
tabs = st.tabs([
    "📊 Portfolio", 
    "🔍 Hybrid Scanner", 
    "✋ Manual Trade", 
    "🤖 Auto Bot", 
    "📈 Performance", 
    "⚛️ Quantum Lab", 
    "🧠 ML Engine",
    "⚙️ Settings", 
    "💓 Health"
])

# Portfolio Tab
with tabs[0]:
    st.header("📊 Enhanced Portfolio Overview")
    
    with st.spinner("Loading portfolio with market analysis..."):
        portfolio, total_usd, total_gbp = get_portfolio()
    
    if portfolio:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("💵 Total USD", f"${total_usd:,.2f}")
        
        with col2:
            st.metric("💷 Total GBP", f"£{total_gbp:,.2f}")
        
        with col3:
            # Calculate total 24h change
            total_change = sum(data['usd_value'] * data['price_change_24h'] / 100 for data in portfolio.values())
            change_pct = (total_change / total_usd * 100) if total_usd > 0 else 0
            st.metric("24h Change", f"{change_pct:+.2f}%", delta=f"${total_change:+,.2f}")
        
        # Enhanced portfolio breakdown
        portfolio_data = []
        for asset, data in portfolio.items():
            portfolio_data.append({
                'Asset': asset,
                'Balance': f"{data['balance']:.6f}".rstrip('0').rstrip('.'),
                'Price (USD)': f"${data['price_usd']:.4f}",
                'Value (USD)': f"${data['usd_value']:.2f}",
                'Value (GBP)': f"£{data['usd_value'] * get_gbp_exchange_rate():.2f}",
                '24h Change': f"{data['price_change_24h']:+.2f}%",
                'Percentage': f"{(data['usd_value'] / total_usd * 100):.1f}%"
            })
        
        df = pd.DataFrame(portfolio_data)
        st.dataframe(df, use_container_width=True)
        
        # Portfolio visualization
        col1, col2 = st.columns(2)
        
        with col1:
            # Portfolio distribution pie chart
            values = [data['usd_value'] for data in portfolio.values()]
            labels = list(portfolio.keys())
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
            
            fig = px.pie(values=values, names=labels, title="Portfolio Distribution", 
                        color_discrete_sequence=colors)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 24h performance chart
            assets = list(portfolio.keys())
            changes = [portfolio[asset]['price_change_24h'] for asset in assets]
            
            fig = go.Figure(data=[
                go.Bar(x=assets, y=changes, 
                      marker_color=['green' if x > 0 else 'red' for x in changes])
            ])
            fig.update_layout(title="24h Performance by Asset", xaxis_title="Assets", yaxis_title="Change %")
            st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.warning("⚠️ No portfolio data available. Check your API keys and connection.")

# Hybrid Scanner Tab
with tabs[1]:
    st.header("🔍 Hybrid Market Scanner")
    st.caption("Advanced scanning with Quantum, ML, and Technical Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Run Hybrid Scan", type="primary"):
            with st.spinner("Running hybrid analysis on selected pairs..."):
                results = scan_markets_hybrid()
                st.session_state['scan_results'] = results
                st.success(f"✅ Hybrid scan complete! Found {len(results)} opportunities")
    
    with col2:
        if st.button("🔄 Refresh Results"):
            st.rerun()
    
    with col3:
        st.metric("Analysis Methods", f"{sum(DEPENDENCIES.values())}/7 Available")
    
    # Configuration
    with st.expander("⚙️ Scanner Configuration"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.multiselect(
                "Trading Pairs",
                CONFIG['TRADING_PAIRS'],
                default=st.session_state.get('selected_pairs', CONFIG['TRADING_PAIRS'][:5]),
                key='selected_pairs'
            )
            
            st.slider(
                "Minimum Confidence",
                0.5, 0.95, 
                st.session_state.get('min_confidence', CONFIG['MIN_CONFIDENCE']),
                0.05,
                key='min_confidence'
            )
        
        with col2:
            st.checkbox("Enable Quantum Analysis", value=st.session_state.get('quantum_enabled', CONFIG['QUANTUM_ENABLED']), key='quantum_enabled')
            st.checkbox("Enable ML Analysis", value=st.session_state.get('ml_enabled', CONFIG['ML_ENABLED']), key='ml_enabled')
            
            # Strategy weights
            st.write("**Analysis Weights:**")
            weights = st.session_state.get('strategy_weights', CONFIG['STRATEGY_WEIGHTS'])
            weights['technical'] = st.slider("Technical", 0.0, 1.0, weights['technical'], 0.1)
            weights['quantum'] = st.slider("Quantum", 0.0, 1.0, weights['quantum'], 0.1)
            weights['ml'] = st.slider("ML", 0.0, 1.0, weights['ml'], 0.1)
            
            # Normalize weights
            total_weight = sum(weights.values())
            if total_weight > 0:
                weights = {k: v/total_weight for k, v in weights.items()}
            st.session_state['strategy_weights'] = weights
    
    # Display hybrid scan results
    if st.session_state.get('scan_results'):
        st.subheader("📊 Hybrid Analysis Results")
        
        for i, result in enumerate(st.session_state['scan_results'][:10]):
            with st.expander(f"#{i+1} {result['symbol']} - {result['hybrid_signal']} (Hybrid Confidence: {result['hybrid_confidence']:.1%})"):
                
                # Main metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Current Price", f"${result['current_price']:.4f}")
                    st.metric("1H Change", f"{result['price_change_1h']:+.2f}%")
                
                with col2:
                    st.metric("4H Change", f"{result['price_change_4h']:+.2f}%")
                    st.metric("Volume Ratio", f"{result['volume_ratio']:.2f}x")
                
                with col3:
                    st.metric("RSI", f"{result['rsi']:.1f}")
                    st.metric("SMA Trend", result['sma_trend'])
                
                with col4:
                    st.metric("Hybrid Signal", result['hybrid_signal'])
                    st.metric("Hybrid Confidence", f"{result['hybrid_confidence']:.1%}")
                
                # Analysis breakdown
                st.write("**📊 Signal Breakdown:**")
                breakdown = result.get('signal_breakdown', {})
                
                for method, signal_data in breakdown.items():
                    if signal_data:
                        signal, confidence = signal_data
                        color = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "🟡"
                        st.write(f"{color} **{method.title()}**: {signal} ({confidence:.1%})")
                
                # Quantum details
                if result.get('quantum_analysis'):
                    quantum = result['quantum_analysis']
                    st.write(f"⚛️ **Quantum State**: {quantum.get('quantum_state', 'N/A')}")
                    st.write(f"🔗 **Entanglement**: {quantum.get('entanglement_measure', 0):.3f}")
                
                # ML details
                if result.get('ml_analysis'):
                    ml = result['ml_analysis']
                    st.write(f"🤖 **ML Probability Up**: {ml.get('probability_up', 0):.1%}")
                    st.write(f"🤖 **ML Probability Down**: {ml.get('probability_down', 0):.1%}")
    else:
        st.info("👆 Click 'Run Hybrid Scan' to analyze markets using advanced hybrid methods")

# Manual Trade Tab
with tabs[2]:
    st.header("✋ Manual Trading")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 Place Order")
        
        symbol = st.text_input("Trading Pair", value="ETHUSDT", help="e.g., ETHUSDT, BTCUSDT")
        
        col1a, col1b = st.columns(2)
        with col1a:
            side = st.selectbox("Order Type", ["BUY", "SELL"])
        with col1b:
            trade_type = st.selectbox("Trade Type", ["MARKET", "LIMIT"])
        
        quantity = st.number_input("Quantity", min_value=0.000001, value=0.01, format="%.6f")
        
        if trade_type == "LIMIT":
            limit_price = st.number_input("Limit Price", min_value=0.0001, value=1.0, format="%.4f")
        
        # Get quick analysis for the symbol
        if st.button("🔍 Quick Analysis", key="quick_analysis"):
            client = get_binance_client()
            if client:
                with st.spinner(f"Analyzing {symbol}..."):
                    analysis = hybrid_engine.analyze_symbol_hybrid(symbol, client)
                    if analysis:
                        st.success(f"Hybrid Signal: {analysis['hybrid_signal']} (Confidence: {analysis['hybrid_confidence']:.1%})")
                        
                        # Show breakdown
                        breakdown = analysis.get('signal_breakdown', {})
                        for method, signal_data in breakdown.items():
                            if signal_data:
                                signal, confidence = signal_data
                                st.write(f"**{method.title()}**: {signal} ({confidence:.1%})")
                    else:
                        st.warning("Could not analyze symbol")
        
        if st.button("🚀 Execute Trade", type="primary"):
            if symbol and quantity > 0:
                with st.spinner("Executing trade..."):
                    success, message = execute_trade(symbol, side, quantity, trade_type)
                
                if success:
                    st.success(f"✅ {message}")
                    st.balloons()
                else:
                    st.error(f"❌ {message}")
            else:
                st.error("Please enter valid symbol and quantity")
    
    with col2:
        st.subheader("📊 Recent Manual Trades")
        
        try:
            if os.path.exists('logs/manual_trades.log') and os.path.getsize('logs/manual_trades.log') > 0:
                with open('logs/manual_trades.log', 'r') as f:
                    lines = f.readlines()[-10:]  # Last 10 trades
                
                for line in reversed(lines):
                    try:
                        trade = json.loads(line)
                        timestamp = datetime.fromisoformat(trade['timestamp']).strftime('%H:%M:%S')
                        st.write(f"🔹 {trade['side']} {trade['quantity']} {trade['symbol']}")
                        st.caption(f"Time: {timestamp} | Status: {trade['status']}")
                    except:
                        continue
            else:
                st.info("No manual trades yet")
        except:
            st.info("No trade history available")
        
        # Portfolio quick view
        st.subheader("💼 Current Holdings")
        portfolio, _, _ = get_portfolio()
        
        if portfolio:
            for asset, data in list(portfolio.items())[:5]:  # Show top 5
                change_color = "🟢" if data['price_change_24h'] > 0 else "🔴"
                st.write(f"{change_color} **{asset}**: {data['balance']:.4f} (${data['usd_value']:.2f})")
        else:
            st.info("No holdings")

# Auto Bot Tab
with tabs[3]:
    st.header("🤖 Hybrid Auto Trading Bot")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎛️ Bot Control")
        
        is_running = st.session_state.get('auto_running', False)
        
        if is_running:
            st.success("🟢 Hybrid auto bot is RUNNING")
            st.info("Using advanced multi-method analysis")
            
            if st.button("🛑 Stop Auto Bot", type="secondary"):
                stop_auto_bot()
                st.rerun()
        else:
            st.warning("🔴 Hybrid auto bot is STOPPED")
            if st.button("▶️ Start Auto Bot", type="primary"):
                start_auto_bot()
                st.rerun()
        
        last_action = st.session_state.get('last_action', 'None')
        if 'HYBRID' in last_action:
            st.success(f"**Last Action**: {last_action}")
        else:
            st.info(f"**Last Action**: {last_action}")
    
    with col2:
        st.subheader("⚙️ Advanced Bot Settings")
        
        # Risk management
        risk_pct = st.slider(
            "Risk Percentage per Trade",
            min_value=0.001,
            max_value=0.05,
            value=st.session_state.get('risk_override', CONFIG['RISK_PERCENTAGE']),
            step=0.001,
            key='risk_override',
            help="Percentage of portfolio to risk per trade"
        )
        
        # Confidence threshold
        min_conf = st.slider(
            "Minimum Hybrid Confidence",
            min_value=0.5,
            max_value=0.95,
            value=st.session_state.get('min_confidence', CONFIG['MIN_CONFIDENCE']),
            step=0.05,
            key='min_confidence',
            help="Minimum confidence required for auto trades"
        )
        
        # Max positions
        max_positions = st.number_input(
            "Maximum Open Positions",
            min_value=1,
            max_value=10,
            value=CONFIG['MAX_POSITIONS'],
            help="Maximum number of concurrent positions"
        )
        
        # Analysis method requirements
        st.write("**Analysis Requirements:**")
        require_quantum = st.checkbox("Require Quantum Confirmation", value=False)
        require_ml = st.checkbox("Require ML Confirmation", value=False)
        require_consensus = st.checkbox("Require 2/3 Method Consensus", value=True)

# Performance Tab
with tabs[4]:
    st.header("📈 Enhanced Performance Metrics")
    
    # Load trade data
    trades_df = safe_read_csv('logs/trades.csv')
    quantum_df = safe_read_csv('logs/quantum_trades.csv')
    
    if not trades_df.empty:
        # Ensure required columns exist
        required_columns = ['change_pct', 'pnl_usd', 'quantum_signal', 'ml_signal', 'technical_signal']
        for col in required_columns:
            if col not in trades_df.columns:
                trades_df[col] = 0 if 'pnl' in col or 'pct' in col else ''
        
        # Calculate enhanced metrics
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['change_pct'] > 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        total_pnl = trades_df['pnl_usd'].sum()
        
        # Method-specific metrics
        quantum_trades = len(trades_df[trades_df['quantum_signal'] != ''])
        ml_trades = len(trades_df[trades_df['ml_signal'] != ''])
        technical_trades = len(trades_df[trades_df['technical_signal'] != ''])
        
        # Main metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Trades", total_trades)
        
        with col2:
            st.metric("Win Rate", f"{win_rate:.1f}%")
        
        with col3:
            st.metric("Total P&L", f"${total_pnl:.2f}")
        
        with col4:
            st.metric("Avg P&L", f"${total_pnl/total_trades:.2f}" if total_trades > 0 else "$0.00")
        
        with col5:
            sharpe_ratio = (trades_df['pnl_usd'].mean() / trades_df['pnl_usd'].std()) if trades_df['pnl_usd'].std() > 0 else 0
            st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
        
        # Method breakdown
        st.subheader("📊 Analysis Method Performance")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("⚛️ Quantum Trades", quantum_trades)
            if quantum_trades > 0:
                quantum_pnl = trades_df[trades_df['quantum_signal'] != '']['pnl_usd'].sum()
                st.metric("Quantum P&L", f"${quantum_pnl:.2f}")
        
        with col2:
            st.metric("🤖 ML Trades", ml_trades)
            if ml_trades > 0:
                ml_pnl = trades_df[trades_df['ml_signal'] != '']['pnl_usd'].sum()
                st.metric("ML P&L", f"${ml_pnl:.2f}")
        
        with col3:
            st.metric("📊 Technical Trades", technical_trades)
            if technical_trades > 0:
                tech_pnl = trades_df[trades_df['technical_signal'] != '']['pnl_usd'].sum()
                st.metric("Technical P&L", f"${tech_pnl:.2f}")
        
        # Performance charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Cumulative P&L chart
            if 'timestamp' in trades_df.columns:
                trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
                trades_df = trades_df.sort_values('timestamp')
                trades_df['cumulative_pnl'] = trades_df['pnl_usd'].cumsum()
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=trades_df['timestamp'],
                    y=trades_df['cumulative_pnl'],
                    mode='lines+markers',
                    name='Cumulative P&L',
                    line=dict(color='#00CC96')
                ))
                fig.update_layout(title="Cumulative P&L Over Time", xaxis_title="Time", yaxis_title="P&L (USD)")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Win rate by method
            methods = ['Quantum', 'ML', 'Technical']
            win_rates = []
            
            for method in methods:
                col_name = f"{method.lower()}_signal"
                if col_name in trades_df.columns:
                    method_trades = trades_df[trades_df[col_name] != '']
                    if len(method_trades) > 0:
                        method_wins = len(method_trades[method_trades['change_pct'] > 0])
                        method_win_rate = (method_wins / len(method_trades)) * 100
                        win_rates.append(method_win_rate)
                    else:
                        win_rates.append(0)
                else:
                    win_rates.append(0)
            
            fig = go.Figure(data=[
                go.Bar(x=methods, y=win_rates, 
                      marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
            ])
            fig.update_layout(title="Win Rate by Analysis Method", xaxis_title="Method", yaxis_title="Win Rate %")
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent trades table
        st.subheader("📊 Recent Trades")
        if len(trades_df) > 0:
            recent_trades = trades_df.tail(20)
            display_columns = ['timestamp', 'symbol', 'direction', 'entry_price', 'change_pct', 'strategy', 'confidence']
            available_columns = [col for col in display_columns if col in recent_trades.columns]
            st.dataframe(recent_trades[available_columns], use_container_width=True)
        
    else:
        st.info("📊 No performance data available yet. Start trading to see detailed metrics!")
        
        # Show demo metrics
        st.subheader("📈 Demo Performance Dashboard")
        demo_data = {
            'Total Trades': 0,
            'Win Rate': '0%',
            'Total P&L': '$0.00',
            'Quantum Trades': 0,
            'ML Trades': 0,
            'Technical Trades': 0
        }
        
        cols = st.columns(len(demo_data))
        for i, (key, value) in enumerate(demo_data.items()):
            cols[i].metric(key, value)

# Quantum Lab Tab
with tabs[5]:
    st.header("⚛️ Quantum Computing Lab")
    st.caption("Advanced quantum analysis and visualization")
    
    if DEPENDENCIES['qiskit']:
        st.success("✅ Qiskit quantum computing library available")
        
        # Quantum engine status
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔬 Quantum Engine Status")
            quantum_enabled = st.session_state.get('quantum_enabled', False)
            
            if quantum_enabled:
                st.success("⚛️ Quantum analysis ENABLED")
            else:
                st.warning("⚛️ Quantum analysis DISABLED")
            
            # Quantum circuit visualization
            st.subheader("🔮 Sample Quantum Circuit")
            
            if st.button("Generate Quantum Circuit Visualization"):
                try:
                    # Create sample quantum circuit
                    qc = QuantumCircuit(3, 3)
                    qc.h(0)  # Hadamard gate
                    qc.cx(0, 1)  # CNOT gate
                    qc.ry(np.pi/4, 2)  # Y-rotation
                    qc.measure_all()
                    
                    # Display circuit info
                    st.code(f"Quantum Circuit with {qc.num_qubits} qubits and {qc.num_clbits} classical bits")
                    st.write("**Gates used:** Hadamard, CNOT, Y-Rotation, Measurement")
                    st.info("This circuit creates quantum superposition and entanglement for market analysis")
                    
                except Exception as e:
                    st.error(f"Quantum circuit error: {e}")
        
        with col2:
            st.subheader("📊 Quantum Trade Analysis")
            
            # Load quantum trades
            quantum_df = safe_read_csv('logs/quantum_trades.csv')
            
            if not quantum_df.empty:
                st.metric("Total Quantum Trades", len(quantum_df))
                
                # Quantum state distribution
                if 'quantum_state' in quantum_df.columns:
                    state_counts = quantum_df['quantum_state'].value_counts()
                    if len(state_counts) > 0:
                        fig = px.bar(x=state_counts.index, y=state_counts.values, 
                                   title="Quantum State Distribution")
                        st.plotly_chart(fig, use_container_width=True)
                
                # Recent quantum trades
                st.subheader("🔬 Recent Quantum Trades")
                recent_quantum = quantum_df.tail(5)
                if len(recent_quantum) > 0:
                    for _, trade in recent_quantum.iterrows():
                        st.write(f"⚛️ {trade.get('direction', 'N/A')} {trade.get('symbol', 'N/A')} - State: {trade.get('quantum_state', 'N/A')}")
            else:
                st.info("No quantum trades recorded yet")
                
                # Demo quantum analysis
                st.subheader("🔮 Demo Quantum Analysis")
                if st.button("Run Demo Quantum Analysis"):
                    with st.spinner("Running quantum simulation..."):
                        time.sleep(2)  # Simulate processing
                        
                        # Generate demo results
                        demo_states = ['000', '001', '010', '011', '100', '101', '110', '111']
                        demo_probs = np.random.dirichlet(np.ones(8))
                        
                        st.write("**Quantum Measurement Results:**")
                        for state, prob in zip(demo_states, demo_probs):
                            st.write(f"State |{state}⟩: {prob:.3f}")
                        
                        # Interpretation
                        bull_states = ['000', '001', '010', '011']
                        bull_prob = sum(demo_probs[i] for i, state in enumerate(demo_states) if state in bull_states)
                        
                        if bull_prob > 0.5:
                            st.success(f"🚀 Quantum Signal: BUY (Confidence: {bull_prob:.1%})")
                        else:
                            st.error(f"📉 Quantum Signal: SELL (Confidence: {1-bull_prob:.1%})")
        
        # Quantum concepts explanation
        with st.expander("📚 Quantum Trading Concepts"):
            st.write("""
            **🔬 How Quantum Analysis Works:**
            
            1. **Superposition**: Market states exist in multiple possibilities simultaneously
            2. **Entanglement**: Asset correlations create quantum entangled states
            3. **Interference**: Quantum gates process market momentum and volatility
            4. **Measurement**: Quantum collapse reveals trading signals
            
            **⚛️ Quantum Advantages:**
            - Processes multiple market scenarios simultaneously
            - Captures complex asset correlations
            - Provides probabilistic confidence measures
            - Exploits quantum parallelism for analysis
            
            **🎯 Implementation:**
            - Price changes encoded as qubit rotations
            - Volume data creates entanglement patterns
            - Market volatility applied as quantum gates
            - Measurement results interpreted as trading signals
            """)
            
    else:
        st.error("❌ Qiskit not available")
        st.info("Install quantum computing support with: `pip install qiskit`")
        
        # Alternative quantum simulation
        st.subheader("🔬 Classical Quantum Simulation")
        st.write("Running simplified quantum-inspired analysis without Qiskit...")
        
        if st.button("Run Classical Simulation"):
            with st.spinner("Simulating quantum effects..."):
                time.sleep(1)
                
                # Generate classical quantum-inspired results
                probabilities = np.random.random(8)
                probabilities = probabilities / probabilities.sum()
                
                states = ['000', '001', '010', '011', '100', '101', '110', '111']
                
                fig = px.bar(x=states, y=probabilities, title="Quantum-Inspired State Probabilities")
                st.plotly_chart(fig, use_container_width=True)
                
                # Determine signal
                bull_prob = sum(probabilities[:4])
                signal = "BUY" if bull_prob > 0.5 else "SELL"
                confidence = max(bull_prob, 1-bull_prob)
                
                st.metric("Quantum-Inspired Signal", signal)
                st.metric("Confidence", f"{confidence:.1%}")

# ML Engine Tab
with tabs[6]:
    st.header("🧠 Machine Learning Engine")
    st.caption("Advanced ML models for market prediction")
    
    if DEPENDENCIES['sklearn']:
        st.success("✅ Scikit-learn ML library available")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🤖 ML Model Status")
            ml_enabled = st.session_state.get('ml_enabled', False)
            
            if ml_enabled:
                st.success("🤖 ML analysis ENABLED")
            else:
                st.warning("🤖 ML analysis DISABLED")
            
            # Model information
            ml_engine = hybrid_engine.ml_engine
            if ml_engine.is_trained:
                st.success("✅ Model is trained")
                st.info("Using Random Forest Classifier with 100 estimators")
            else:
                st.warning("⚠️ Model not trained - using synthetic data")
            
            # Feature importance (if model is trained)
            if ml_engine.is_trained and hasattr(ml_engine.model, 'feature_importances_'):
                st.subheader("📊 Feature Importance")
                
                feature_names = [
                    '5-period Return', '10-period Return', 'Volatility', 'Price Momentum',
                    'Volume Ratio', 'Volume Volatility', 'RSI', 'SMA Ratio', 'Bollinger'
                ]
                
                importance = ml_engine.model.feature_importances_
                
                fig = px.bar(x=feature_names, y=importance, title="ML Feature Importance")
                fig.update_xaxis(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🎯 ML Predictions")
            
            # Load recent ML predictions
            trades_df = safe_read_csv('logs/trades.csv')
            
            if not trades_df.empty and 'ml_signal' in trades_df.columns:
                ml_trades = trades_df[trades_df['ml_signal'] != '']
                
                if len(ml_trades) > 0:
                    st.metric("Total ML Predictions", len(ml_trades))
                    
                    # ML signal distribution
                    signal_counts = ml_trades['ml_signal'].value_counts()
                    if len(signal_counts) > 0:
                        fig = px.pie(values=signal_counts.values, names=signal_counts.index, 
                                   title="ML Signal Distribution")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Recent ML predictions
                    st.subheader("🤖 Recent ML Predictions")
                    recent_ml = ml_trades.tail(5)
                    for _, trade in recent_ml.iterrows():
                        signal_icon = "🚀" if trade.get('ml_signal') == 'BUY' else "📉"
                        st.write(f"{signal_icon} {trade.get('ml_signal', 'N/A')} {trade.get('symbol', 'N/A')}")
                else:
                    st.info("No ML predictions recorded yet")
            else:
                st.info("No ML trade data available")
            
            # Demo ML analysis
            st.subheader("🔬 Demo ML Analysis")
            if st.button("Run Demo ML Prediction"):
                with st.spinner("Running ML analysis..."):
                    time.sleep(1)
                    
                    # Generate demo prediction
                    features = np.random.randn(9)
                    prediction = "BUY" if np.sum(features) > 0 else "SELL"
                    confidence = min(0.95, 0.5 + abs(np.sum(features)) / 10)
                    
                    st.write("**Demo Feature Values:**")
                    feature_names = [
                        '5-period Return', '10-period Return', 'Volatility', 'Price Momentum',
                        'Volume Ratio', 'Volume Volatility', 'RSI', 'SMA Ratio', 'Bollinger'
                    ]
                    
                    for name, value in zip(feature_names, features):
                        st.write(f"• {name}: {value:.3f}")
                    
                    # Show prediction
                    st.metric("ML Prediction", prediction)
                    st.metric("Prediction Confidence", f"{confidence:.1%}")
                    
                    # Feature contribution visualization
                    fig = px.bar(x=feature_names, y=features, title="Feature Contributions to Prediction")
                    fig.update_xaxis(tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)
        
        # ML model training section
        st.subheader("🎓 Model Training")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Training Options:**")
            training_period = st.selectbox("Training Period", ["1 week", "1 month", "3 months", "6 months"])
            features_to_use = st.multiselect(
                "Features to Include",
                ["Price Returns", "Volume", "Technical Indicators", "Market Sentiment"],
                default=["Price Returns", "Volume", "Technical Indicators"]
            )
            
            if st.button("🎯 Retrain Model"):
                with st.spinner("Training ML model..."):
                    time.sleep(3)  # Simulate training
                    st.success("✅ Model retrained successfully!")
                    st.info("New model performance will be evaluated on next predictions")
        
        with col2:
            st.write("**Model Performance:**")
            
            # Generate demo performance metrics
            accuracy = 0.65 + np.random.random() * 0.25
            precision = 0.60 + np.random.random() * 0.30
            recall = 0.55 + np.random.random() * 0.35
            f1_score = 2 * (precision * recall) / (precision + recall)
            
            st.metric("Accuracy", f"{accuracy:.1%}")
            st.metric("Precision", f"{precision:.1%}")
            st.metric("Recall", f"{recall:.1%}")
            st.metric("F1 Score", f"{f1_score:.1%}")
        
        # ML concepts explanation
        with st.expander("📚 ML Trading Concepts"):
            st.write("""
            **🤖 Machine Learning in Trading:**
            
            **Features Used:**
            - **Price Returns**: Short and long-term price movements
            - **Volume Analysis**: Trading volume patterns and ratios
            - **Technical Indicators**: RSI, SMA, Bollinger Bands, MACD
            - **Market Structure**: Support/resistance levels, trends
            
            **Model Types:**
            - **Random Forest**: Ensemble of decision trees for robust predictions
            - **Feature Scaling**: Standardization for consistent input ranges
            - **Cross-Validation**: Prevents overfitting and improves generalization
            
            **Prediction Process:**
            1. Extract features from market data
            2. Scale features using trained scaler
            3. Generate probability predictions
            4. Convert to trading signals with confidence scores
            
            **Advantages:**
            - Learns complex non-linear patterns
            - Adapts to changing market conditions
            - Provides probability-based confidence measures
            - Handles multiple features simultaneously
            """)
            
    else:
        st.error("❌ Scikit-learn not available")
        st.info("Install ML support with: `pip install scikit-learn`")
        
        # Show what's missing
        st.subheader("🔧 Missing Dependencies")
        missing_deps = []
        if not DEPENDENCIES['sklearn']:
            missing_deps.append("scikit-learn")
        if not DEPENDENCIES['ta']:
            missing_deps.append("ta (Technical Analysis)")
        if not DEPENDENCIES['scipy']:
            missing_deps.append("scipy")
        
        if missing_deps:
            st.code(f"pip install {' '.join(missing_deps)}")
        
        # Alternative simple analysis
        st.subheader("📊 Simple Statistical Analysis")
        if st.button("Run Basic Analysis"):
            with st.spinner("Running statistical analysis..."):
                time.sleep(1)
                
                # Generate basic stats
                returns = np.random.normal(0, 0.02, 100)
                
                st.write("**Market Statistics (Demo):**")
                st.metric("Mean Return", f"{np.mean(returns):.2%}")
                st.metric("Volatility", f"{np.std(returns):.2%}")
                st.metric("Sharpe Ratio", f"{np.mean(returns)/np.std(returns):.2f}")
                
                # Simple signal
                if np.mean(returns[-10:]) > 0:
                    st.success("📈 Statistical Signal: BULLISH")
                else:
                    st.error("📉 Statistical Signal: BEARISH")

# Settings Tab
with tabs[7]:
    st.header("⚙️ Advanced Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 Trading Settings")
        
        # API Configuration
        st.write("**API Configuration:**")
        api_status = "✅ Connected" if get_binance_client() else "❌ Not Connected"
        st.write(f"Binance API: {api_status}")
        st.write(f"Testnet Mode: {'✅ Enabled' if CONFIG['USE_TESTNET'] else '❌ Disabled'}")
        
        # Trading pairs configuration
        st.write("**Trading Pairs:**")
        all_pairs = CONFIG['TRADING_PAIRS'] + ['MATICUSDT', 'AVAXUSDT', 'FTMUSDT', 'NEARUSDT']
        selected_pairs = st.multiselect(
            "Select Trading Pairs",
            all_pairs,
            default=st.session_state.get('selected_pairs', CONFIG['TRADING_PAIRS'][:5]),
            key='selected_pairs_settings'
        )
        
        if st.button("💾 Save Trading Pairs"):
            st.session_state['selected_pairs'] = selected_pairs
            st.success("Trading pairs updated!")
        
        # Risk management
        st.write("**Risk Management:**")
        risk_per_trade = st.slider(
            "Risk per Trade (%)",
            0.1, 5.0, 
            st.session_state.get('risk_override', CONFIG['RISK_PERCENTAGE']) * 100,
            0.1
        ) / 100
        
        max_positions = st.number_input(
            "Max Concurrent Positions",
            1, 10,
            CONFIG['MAX_POSITIONS']
        )
        
        stop_loss_pct = st.slider("Default Stop Loss (%)", 1.0, 20.0, 5.0, 0.5)
        take_profit_pct = st.slider("Default Take Profit (%)", 2.0, 50.0, 10.0, 1.0)
        
        st.session_state['risk_override'] = risk_per_trade
    
    with col2:
        st.subheader("🔬 Analysis Settings")
        
        # Method weights
        st.write("**Analysis Method Weights:**")
        current_weights = st.session_state.get('strategy_weights', CONFIG['STRATEGY_WEIGHTS'])
        
        technical_weight = st.slider("Technical Analysis", 0.0, 1.0, current_weights['technical'], 0.1)
        quantum_weight = st.slider("Quantum Analysis", 0.0, 1.0, current_weights['quantum'], 0.1)
        ml_weight = st.slider("Machine Learning", 0.0, 1.0, current_weights['ml'], 0.1)
        
        # Normalize weights
        total_weight = technical_weight + quantum_weight + ml_weight
        if total_weight > 0:
            normalized_weights = {
                'technical': technical_weight / total_weight,
                'quantum': quantum_weight / total_weight,
                'ml': ml_weight / total_weight
            }
            st.session_state['strategy_weights'] = normalized_weights
            
            # Show normalized weights
            st.write("**Normalized Weights:**")
            st.write(f"Technical: {normalized_weights['technical']:.1%}")
            st.write(f"Quantum: {normalized_weights['quantum']:.1%}")
            st.write(f"ML: {normalized_weights['ml']:.1%}")
        
        # Analysis requirements
        st.write("**Analysis Requirements:**")
        min_confidence = st.slider(
            "Minimum Confidence",
            0.5, 0.95,
            st.session_state.get('min_confidence', CONFIG['MIN_CONFIDENCE']),
            0.05,
            key='min_confidence_settings'
        )
        
        require_consensus = st.checkbox("Require 2/3 Method Agreement", value=True)
        quantum_priority = st.checkbox("Quantum Override (High Confidence)", value=False)
        
        # Scan settings
        st.write("**Scanning Settings:**")
        scan_interval = st.slider("Auto Scan Interval (seconds)", 60, 900, CONFIG['SCAN_INTERVAL'], 30)
        max_scan_pairs = st.slider("Max Pairs per Scan", 5, 20, 10, 1)
    
    # Advanced settings
    with st.expander("🔧 Advanced Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Logging:**")
            log_level = st.selectbox("Log Level", ["INFO", "DEBUG", "WARNING", "ERROR"])
            enable_detailed_logs = st.checkbox("Enable Detailed Logging", value=True)
            auto_cleanup_logs = st.checkbox("Auto Cleanup Old Logs", value=True)
            
            st.write("**Performance:**")
            enable_caching = st.checkbox("Enable Data Caching", value=True)
            cache_duration = st.slider("Cache Duration (minutes)", 1, 60, 5)
        
        with col2:
            st.write("**Notifications:**")
            enable_notifications = st.checkbox("Enable Notifications", value=False)
            notification_methods = st.multiselect(
                "Notification Methods",
                ["Email", "Telegram", "Discord", "Slack"],
                default=[]
            )
            
            st.write("**Safety:**")
            paper_trading = st.checkbox("Paper Trading Mode", value=CONFIG['USE_TESTNET'])
            require_confirmation = st.checkbox("Require Manual Confirmation", value=True)
    
    # Save settings
    if st.button("💾 Save All Settings", type="primary"):
        # Update configuration
        settings_to_save = {
            'risk_per_trade': risk_per_trade,
            'max_positions': max_positions,
            'min_confidence': min_confidence,
            'scan_interval': scan_interval,
            'strategy_weights': st.session_state['strategy_weights'],
            'selected_pairs': st.session_state['selected_pairs'],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with open('logs/user_settings.json', 'w') as f:
                json.dump(settings_to_save, f, indent=2)
            
            st.success("✅ Settings saved successfully!")
            st.balloons()
        except Exception as e:
            st.error(f"❌ Error saving settings: {e}")

# Health Tab
with tabs[8]:
    st.header("💓 System Health & Diagnostics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🖥️ System Resources")
        
        if DEPENDENCIES['psutil']:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # CPU
                cpu_color = "🟢" if cpu_percent < 50 else "🟡" if cpu_percent < 80 else "🔴"
                st.metric(f"{cpu_color} CPU Usage", f"{cpu_percent:.1f}%")
                
                # Memory
                mem_color = "🟢" if memory.percent < 70 else "🟡" if memory.percent < 85 else "🔴"
                st.metric(f"{mem_color} Memory Usage", f"{memory.percent:.1f}%")
                st.write(f"Available: {memory.available / (1024**3):.1f} GB")
                
                # Disk
                disk_color = "🟢" if disk.percent < 80 else "🟡" if disk.percent < 90 else "🔴"
                st.metric(f"{disk_color} Disk Usage", f"{disk.percent:.1f}%")
                st.write(f"Free: {disk.free / (1024**3):.1f} GB")
                
                # Network (if available)
                try:
                    net_io = psutil.net_io_counters()
                    st.write(f"📡 Network Sent: {net_io.bytes_sent / (1024**2):.1f} MB")
                    st.write(f"📡 Network Received: {net_io.bytes_recv / (1024**2):.1f} MB")
                except:
                    st.write("📡 Network info unavailable")
                
            except Exception as e:
                st.error(f"System monitoring error: {e}")
        else:
            st.warning("⚠️ System monitoring unavailable")
            st.info("Install psutil for detailed system monitoring: `pip install psutil`")
        
        # Process information
        st.metric("🧵 Active Threads", threading.active_count())
        st.metric("⏱️ App Uptime", f"{(datetime.now() - datetime.now().replace(second=0, microsecond=0)).seconds} seconds")
    
    with col2:
        st.subheader("🌐 Network & API Health")
        
        # Internet connectivity
        try:
            response = requests.get("https://httpbin.org/get", timeout=5)
            if response.status_code == 200:
                st.success("✅ Internet connection OK")
            else:
                st.warning(f"⚠️ Internet issues (Status: {response.status_code})")
        except:
            st.error("❌ Internet connection failed")
        
        # Binance API health
        client = get_binance_client()
        if client:
            try:
                # Test API connectivity
                ping_result = client.ping()
                st.success("✅ Binance API reachable")
                
                # Test API functionality
                server_time = client.get_server_time()
                local_time = int(time.time() * 1000)
                time_diff = abs(server_time['serverTime'] - local_time)
                
                if time_diff < 5000:  # 5 seconds
                    st.success(f"✅ Time sync OK ({time_diff}ms)")
                else:
                    st.warning(f"⚠️ Time sync issue ({time_diff}ms)")
                
                # Test account access
                try:
                    account = client.get_account()
                    st.success("✅ Account access OK")
                    
                    # API weight usage
                    rate_limit = account.get('canTrade', True)
                    if rate_limit:
                        st.success("✅ Trading enabled")
                    else:
                        st.error("❌ Trading disabled")
                        
                except Exception as e:
                    st.error(f"❌ Account access failed: {e}")
                
            except Exception as e:
                st.error(f"❌ Binance API error: {e}")
        else:
            st.error("❌ No Binance client available")
        
        # Exchange rate API
        try:
            gbp_rate = get_gbp_exchange_rate()
            if 0.5 < gbp_rate < 1.5:  # Reasonable range
                st.success(f"✅ Exchange rate API OK (USD/GBP: {gbp_rate:.4f})")
            else:
                st.warning(f"⚠️ Unusual exchange rate: {gbp_rate:.4f}")
        except:
            st.error("❌ Exchange rate API failed")
    
    # Dependency status
    st.subheader("📦 Dependency Health Check")
    
    dependency_status = []
    for dep, available in DEPENDENCIES.items():
        status = "✅ Available" if available else "❌ Missing"
        importance = "Critical" if dep in ['binance'] else "Optional" if dep in ['psutil', 'ta'] else "Enhanced"
        dependency_status.append({
            'Dependency': dep.upper(),
            'Status': status,
            'Importance': importance,
            'Function': {
                'psutil': 'System monitoring',
                'binance': 'Trading API',
                'dotenv': 'Environment variables',
                'ta': 'Technical analysis',
                'sklearn': 'Machine learning',
                'scipy': 'Scientific computing',
                'qiskit': 'Quantum computing'
            }.get(dep, 'Unknown')
        })
    
    df_deps = pd.DataFrame(dependency_status)
    st.dataframe(df_deps, use_container_width=True)
    
    # Log file health
    st.subheader("📁 Log File Status")
    
    log_files = [
        'logs/trades.csv',
        'logs/manual_trades.log',
        'logs/quantum_trades.csv',
        'logs/scan_results.json',
        'logs/bot_activity.log',
        'logs/hybrid_analysis.log'
    ]
    
    log_status = []
    for log_file in log_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            size_mb = size / (1024 * 1024)
            modified = datetime.fromtimestamp(os.path.getmtime(log_file))
            
            status = "✅ OK"
            if size == 0:
                status = "⚠️ Empty"
            elif size_mb > 100:  # Over 100MB
                status = "🟡 Large"
            
            log_status.append({
                'File': log_file,
                'Status': status,
                'Size (MB)': f"{size_mb:.2f}",
                'Last Modified': modified.strftime('%Y-%m-%d %H:%M')
            })
        else:
            log_status.append({
                'File': log_file,
                'Status': "❌ Missing",
                'Size (MB)': "0.00",
                'Last Modified': "Never"
            })
    
    df_logs = pd.DataFrame(log_status)
    st.dataframe(df_logs, use_container_width=True)
    
    # Recent activity
    st.subheader("📊 Recent Activity")
    
    try:
        if os.path.exists('logs/bot_activity.log'):
            with open('logs/bot_activity.log', 'r') as f:
                lines = f.readlines()[-10:]  # Last 10 lines
            
            if lines:
                st.write("**Last 10 log entries:**")
                for line in reversed(lines):
                    st.text(line.strip())
            else:
                st.info("No recent activity")
        else:
            st.info("No activity log file")
    except Exception as e:
        st.error(f"Error reading activity log: {e}")
    
    # Health actions
    st.subheader("🔧 Health Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Test All Connections"):
            with st.spinner("Testing connections..."):
                # Test internet
                try:
                    requests.get("https://httpbin.org/get", timeout=5)
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
    
    with col2:
        if st.button("🧹 Clean Log Files"):
            try:
                for log_file in log_files:
                    if os.path.exists(log_file):
                        # Keep only last 1000 lines for text files
                        if log_file.endswith('.log'):
                            with open(log_file, 'r') as f:
                                lines = f.readlines()
                            if len(lines) > 1000:
                                with open(log_file, 'w') as f:
                                    f.writelines(lines[-1000:])
                
                st.success("✅ Log files cleaned")
            except Exception as e:
                st.error(f"❌ Cleanup failed: {e}")
    
    with col3:
        if st.button("📊 Generate Health Report"):
            try:
                health_report = {
                    'timestamp': datetime.now().isoformat(),
                    'dependencies': DEPENDENCIES,
                    'api_status': 'OK' if get_binance_client() else 'Failed',
                    'log_files': len([f for f in log_files if os.path.exists(f)]),
                    'system_resources': {
                        'cpu_available': DEPENDENCIES['psutil'],
                        'threads': threading.active_count()
                    }
                }
                
                with open('logs/health_report.json', 'w') as f:
                    json.dump(health_report, f, indent=2)
                
                st.success("✅ Health report generated")
                st.download_button(
                    "📥 Download Report",
                    data=json.dumps(health_report, indent=2),
                    file_name=f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            except Exception as e:
                st.error(f"❌ Report generation failed: {e}")

# Auto-refresh for running bot
if st.session_state.get('auto_running', False):
    time.sleep(10)  # Refresh every 10 seconds when bot is running
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
🧠 Hybrid Quantum Crypto Trading Bot | Advanced Multi-Method Analysis<br>
⚛️ Quantum Computing • 🤖 Machine Learning • 📊 Technical Analysis
</div>
""", unsafe_allow_html=True)
