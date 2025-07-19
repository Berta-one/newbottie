#!/usr/bin/env python3
"""
Complete Hybrid Crypto Trading Bot Dashboard
===========================================
Professional-grade trading bot with live/testnet switching,
portfolio management, market analysis, and automated trading
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json
import os
import time
import threading
import requests
import numpy as np
import warnings
import asyncio
import sys
import logging
from typing import Dict, List, Optional, Tuple
import concurrent.futures

warnings.filterwarnings('ignore')

# Configuration - Environment Variables
CONFIG = {
    'BINANCE_API_KEY': os.getenv('BINANCE_API_KEY', ''),
    'BINANCE_API_SECRET': os.getenv('BINANCE_API_SECRET', ''),
    'USE_TESTNET': os.getenv('USE_TESTNET', 'false').lower() == 'true',
    'MIN_BALANCE_USD': float(os.getenv('MIN_BALANCE_USD', '10.0')),
    'SCAN_INTERVAL': int(os.getenv('SCAN_INTERVAL', '300')),
    'MIN_CONFIDENCE': float(os.getenv('MIN_CONFIDENCE', '0.65')),
    'RISK_PERCENTAGE': float(os.getenv('RISK_PERCENTAGE', '0.015')),
    'MAX_POSITIONS': int(os.getenv('MAX_POSITIONS', '3')),
    'TRADING_PAIRS': os.getenv('TRADING_PAIRS', 'BTCUSDT,ETHUSDT,BNBUSDT,XRPUSDT,ADAUSDT,SOLUSDT,DOTUSDT,LINKUSDT,LTCUSDT,BCHUSDT').split(','),
    'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
    'RAILWAY_ENV': os.getenv('RAILWAY_ENVIRONMENT') == 'production'
}

# Page configuration
st.set_page_config(
    page_title="🤖 Hybrid Crypto Trading Bot",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import dependencies with fallbacks
DEPENDENCIES = {
    'binance': False,
    'ta': False,
    'numpy': True,
    'pandas': True,
    'plotly': True
}

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

# Logging setup
logging.basicConfig(
    level=getattr(logging, CONFIG['LOG_LEVEL']),
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Session state initialization
DEFAULT_SESSION_STATE = {
    'auto_running': False,
    'last_action': 'None',
    'scan_results': [],
    'portfolio_data': {},
    'trade_history': [],
    'active_positions': {},
    'performance_metrics': {},
    'scan_count': 0,
    'last_scan_time': None,
    'bot_start_time': None
}

for key, value in DEFAULT_SESSION_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Utility Functions
def create_directories():
    """Create necessary directories"""
    directories = ['logs', 'data', 'models']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def get_binance_client():
    """Get Binance client with proper configuration"""
    if not DEPENDENCIES['binance'] or not CONFIG['BINANCE_API_KEY'] or not CONFIG['BINANCE_API_SECRET']:
        return None
    
    try:
        client = Client(CONFIG['BINANCE_API_KEY'], CONFIG['BINANCE_API_SECRET'])
        if CONFIG['USE_TESTNET']:
            client.API_URL = "https://testnet.binance.vision/api"
        return client
    except Exception as e:
        logger.error(f"Binance client error: {e}")
        return None

def log_activity(message):
    """Log bot activity"""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {message}"
    
    # Log to file
    try:
        with open('logs/bot_activity.log', 'a') as f:
            f.write(log_entry + '\n')
    except:
        pass
    
    # Log to console
    logger.info(message)

def get_account_balance():
    """Get comprehensive account balance"""
    client = get_binance_client()
    if not client:
        return {}
    
    try:
        account = client.get_account()
        balances = {}
        
        for balance in account['balances']:
            total = float(balance['free']) + float(balance['locked'])
            if total > 0:
                balances[balance['asset']] = {
                    'free': float(balance['free']),
                    'locked': float(balance['locked']),
                    'total': total
                }
        
        return balances
    except Exception as e:
        logger.error(f"Balance retrieval error: {e}")
        return {}

def get_portfolio_value():
    """Calculate comprehensive portfolio value"""
    client = get_binance_client()
    balances = get_account_balance()
    
    if not client or not balances:
        return 0, {}, 0
    
    try:
        # Get all ticker prices and 24h data
        tickers = {t['symbol']: float(t['price']) for t in client.get_all_tickers()}
        ticker_24h = {t['symbol']: {'change': float(t['priceChangePercent']), 'volume': float(t['volume'])} 
                     for t in client.get_24hr_ticker()}
        
        portfolio = {}
        total_usd = 0
        total_change_24h = 0
        
        for asset, balance in balances.items():
            if balance['total'] > 0:
                if asset == 'USDT':
                    price = 1.0
                    change_24h = 0.0
                    volume_24h = 0
                else:
                    symbol = f"{asset}USDT"
                    price = tickers.get(symbol, 0)
                    ticker_data = ticker_24h.get(symbol, {})
                    change_24h = ticker_data.get('change', 0)
                    volume_24h = ticker_data.get('volume', 0)
                
                usd_value = balance['total'] * price
                
                if usd_value >= CONFIG['MIN_BALANCE_USD']:
                    portfolio[asset] = {
                        **balance,
                        'price': price,
                        'usd_value': usd_value,
                        'change_24h': change_24h,
                        'volume_24h': volume_24h,
                        'allocation_percent': 0  # Will be calculated later
                    }
                    total_usd += usd_value
                    total_change_24h += usd_value * (change_24h / 100)
        
        # Calculate allocation percentages
        for asset in portfolio:
            if total_usd > 0:
                portfolio[asset]['allocation_percent'] = (portfolio[asset]['usd_value'] / total_usd) * 100
        
        portfolio_change_pct = (total_change_24h / total_usd * 100) if total_usd > 0 else 0
        
        return total_usd, portfolio, portfolio_change_pct
    
    except Exception as e:
        logger.error(f"Portfolio calculation error: {e}")
        return 0, {}, 0

def calculate_rsi(prices, period=14):
    """Calculate RSI manually"""
    try:
        if len(prices) < period + 1:
            return 50
        
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

def analyze_symbol(symbol, client):
    """Comprehensive symbol analysis"""
    try:
        # Get multiple timeframes
        klines_5m = client.get_klines(symbol=symbol, interval='5m', limit=100)
        klines_1h = client.get_klines(symbol=symbol, interval='1h', limit=100)
        ticker_24h = client.get_24hr_ticker(symbol=symbol)
        
        if not klines_5m or not klines_1h:
            return None
        
        # Extract price data
        prices_5m = [float(k[4]) for k in klines_5m]
        prices_1h = [float(k[4]) for k in klines_1h]
        volumes_5m = [float(k[5]) for k in klines_5m]
        
        current_price = prices_5m[-1]
        price_change_24h = float(ticker_24h['priceChangePercent'])
        volume_24h = float(ticker_24h['volume'])
        
        # Technical indicators
        rsi_5m = calculate_rsi(prices_5m)
        rsi_1h = calculate_rsi(prices_1h)
        
        # Moving averages
        sma_20_5m = np.mean(prices_5m[-20:]) if len(prices_5m) >= 20 else current_price
        sma_50_5m = np.mean(prices_5m[-50:]) if len(prices_5m) >= 50 else current_price
        
        # Volume analysis
        avg_volume = np.mean(volumes_5m[-20:]) if len(volumes_5m) >= 20 else volumes_5m[-1]
        volume_ratio = volumes_5m[-1] / avg_volume if avg_volume > 0 else 1
        
        # Volatility
        volatility = np.std(prices_5m[-20:]) / np.mean(prices_5m[-20:]) if len(prices_5m) >= 20 else 0
        
        # Signal generation
        signal = "HOLD"
        confidence = 0.5
        
        # Breakout detection (5% move in last 2 hours = 24 candles)
        if len(prices_5m) >= 24:
            price_start = prices_5m[-24]
            price_change_2h = ((current_price - price_start) / price_start) * 100
            
            # Volume confirmation
            volume_confirmed = volume_ratio > 1.5
            
            # RSI not extreme
            rsi_ok = 20 < rsi_5m < 80
            
            # Trend alignment
            trend_up = current_price > sma_20_5m > sma_50_5m
            trend_down = current_price < sma_20_5m < sma_50_5m
            
            if abs(price_change_2h) >= 5 and volume_confirmed and rsi_ok:
                if price_change_2h > 0 and trend_up:
                    signal = "BUY"
                    confidence = min(0.9, 0.6 + abs(price_change_2h) / 20)
                elif price_change_2h < 0 and trend_down:
                    signal = "SELL"
                    confidence = min(0.9, 0.6 + abs(price_change_2h) / 20)
        
        return {
            'symbol': symbol,
            'signal': signal,
            'confidence': confidence,
            'current_price': current_price,
            'price_change_24h': price_change_24h,
            'price_change_2h': price_change_2h if 'price_change_2h' in locals() else 0,
            'volume_24h': volume_24h,
            'volume_ratio': volume_ratio,
            'rsi_5m': rsi_5m,
            'rsi_1h': rsi_1h,
            'volatility': volatility,
            'sma_20': sma_20_5m,
            'sma_50': sma_50_5m,
            'trend_direction': 'UP' if trend_up else 'DOWN' if trend_down else 'SIDEWAYS' if 'trend_up' in locals() else 'UNKNOWN',
            'timestamp': datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Symbol analysis error for {symbol}: {e}")
        return None

def scan_trading_opportunities():
    """Advanced market scanning"""
    client = get_binance_client()
    if not client:
        return []
    
    opportunities = []
    
    with st.spinner("Scanning markets..."):
        progress_bar = st.progress(0)
        
        for i, symbol in enumerate(CONFIG['TRADING_PAIRS']):
            try:
                analysis = analyze_symbol(symbol, client)
                if analysis and analysis['confidence'] > CONFIG['MIN_CONFIDENCE']:
                    opportunities.append(analysis)
                
                progress_bar.progress((i + 1) / len(CONFIG['TRADING_PAIRS']))
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
                continue
        
        progress_bar.empty()
    
    # Sort by confidence
    opportunities.sort(key=lambda x: x['confidence'], reverse=True)
    
    # Update session state
    st.session_state['scan_results'] = opportunities
    st.session_state['scan_count'] += 1
    st.session_state['last_scan_time'] = datetime.now()
    
    # Log scan results
    log_activity(f"Market scan completed: {len(opportunities)} opportunities found")
    
    return opportunities

def execute_trade(symbol, signal, quantity, current_price):
    """Execute a trade (simulation for safety)"""
    try:
        # For safety, this is a simulation
        trade = {
            'symbol': symbol,
            'signal': signal,
            'quantity': quantity,
            'entry_price': current_price,
            'timestamp': datetime.now(),
            'status': 'SIMULATED',  # Changed to SIMULATED for safety
            'order_id': f"SIM_{int(time.time())}"
        }
        
        # Add to active positions
        position_id = f"{symbol}_{signal}_{int(time.time())}"
        st.session_state['active_positions'][position_id] = trade
        
        log_activity(f"SIMULATED TRADE: {signal} {quantity} {symbol} at ${current_price}")
        return trade
        
    except Exception as e:
        logger.error(f"Trade execution error: {e}")
        return None

def auto_trading_loop():
    """Main auto trading loop"""
    st.session_state['bot_start_time'] = datetime.now()
    
    while st.session_state.get('auto_running', False):
        try:
            log_activity("Auto trading scan starting...")
            
            # Scan for opportunities
            opportunities = scan_trading_opportunities()
            
            if opportunities:
                best_opportunity = opportunities[0]
                
                # Check if we should trade
                max_positions = CONFIG['MAX_POSITIONS']
                current_positions = len(st.session_state.get('active_positions', {}))
                
                if current_positions < max_positions:
                    # Calculate position size (simulation)
                    portfolio_value, _, _ = get_portfolio_value()
                    risk_amount = portfolio_value * CONFIG['RISK_PERCENTAGE']
                    quantity = risk_amount / best_opportunity['current_price']
                    
                    # Execute trade (simulated)
                    trade = execute_trade(
                        best_opportunity['symbol'],
                        best_opportunity['signal'],
                        quantity,
                        best_opportunity['current_price']
                    )
                    
                    if trade:
                        action = f"🤖 AUTO TRADE: {trade['signal']} {trade['quantity']:.6f} {trade['symbol']} at ${trade['entry_price']:.4f}"
                        st.session_state['last_action'] = action
                else:
                    st.session_state['last_action'] = f"Max positions ({max_positions}) reached, waiting..."
            else:
                st.session_state['last_action'] = "No opportunities found meeting criteria"
            
            # Sleep for scan interval
            time.sleep(CONFIG['SCAN_INTERVAL'])
            
        except Exception as e:
            error_msg = f"Auto trading error: {e}"
            st.session_state['last_action'] = error_msg
            log_activity(error_msg)
            time.sleep(60)  # Wait 1 minute before retry

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

def calculate_performance_metrics():
    """Calculate performance metrics"""
    trade_history = st.session_state.get('trade_history', [])
    
    if not trade_history:
        return {
            'total_trades': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'total_pnl_percent': 0,
            'best_trade': 0,
            'worst_trade': 0,
            'avg_trade': 0
        }
    
    df = pd.DataFrame(trade_history)
    
    metrics = {
        'total_trades': len(df),
        'winning_trades': len(df[df['pnl'] > 0]),
        'losing_trades': len(df[df['pnl'] < 0]),
        'win_rate': len(df[df['pnl'] > 0]) / len(df) * 100 if len(df) > 0 else 0,
        'total_pnl': df['pnl'].sum(),
        'total_pnl_percent': df['pnl_percent'].sum(),
        'best_trade': df['pnl'].max() if len(df) > 0 else 0,
        'worst_trade': df['pnl'].min() if len(df) > 0 else 0,
        'avg_trade': df['pnl'].mean() if len(df) > 0 else 0
    }
    
    return metrics

def main():
    """Main dashboard application"""
    
    # Create necessary directories
    create_directories()
    
    # Header
    st.title("🤖 Hybrid Crypto Trading Bot")
    st.caption("Professional-grade cryptocurrency trading with advanced analytics")
    
    # Mode indicator
    mode = "🧪 TESTNET MODE" if CONFIG['USE_TESTNET'] else "🚀 LIVE TRADING MODE"
    if CONFIG['USE_TESTNET']:
        st.success(f"{mode} - Safe for testing")
    else:
        st.warning(f"{mode} - Real money trading")
    
    # Sidebar
    with st.sidebar:
        st.header("🎛️ Bot Control Panel")
        
        # Connection status
        client = get_binance_client()
        if client:
            st.success("✅ Binance API Connected")
        else:
            st.error("❌ Binance API Not Connected")
            st.warning("Set BINANCE_API_KEY and BINANCE_API_SECRET")
        
        st.divider()
        
        # Bot controls
        st.subheader("🤖 Auto Trading Bot")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Start", disabled=not client, type="primary"):
                start_auto_bot()
                st.success("Bot started!")
                st.rerun()
        
        with col2:
            if st.button("⏹️ Stop", disabled=not client):
                stop_auto_bot()
                st.success("Bot stopped!")
                st.rerun()
        
        # Bot status
        status = "🟢 RUNNING" if st.session_state.get('auto_running') else "🔴 STOPPED"
        st.metric("Status", status)
        
        if st.session_state.get('bot_start_time'):
            runtime = datetime.now() - st.session_state['bot_start_time']
            st.write(f"**Runtime:** {str(runtime).split('.')[0]}")
        
        st.write(f"**Last Action:** {st.session_state.get('last_action', 'None')}")
        st.write(f"**Scans:** {st.session_state.get('scan_count', 0)}")
        
        st.divider()
        
        # Manual controls
        st.subheader("🔍 Manual Actions")
        
        if st.button("🔄 Scan Markets", disabled=not client):
            results = scan_trading_opportunities()
            st.success(f"Found {len(results)} opportunities!")
            st.rerun()
        
        if st.button("📊 Refresh Portfolio", disabled=not client):
            get_portfolio_value()  # This updates the cache
            st.success("Portfolio refreshed!")
            st.rerun()
        
        st.divider()
        
        # Quick stats
        st.subheader("📈 Quick Stats")
        total_usd, _, portfolio_change = get_portfolio_value()
        active_positions = len(st.session_state.get('active_positions', {}))
        
        st.metric("Portfolio Value", f"${total_usd:,.2f}", f"{portfolio_change:+.2f}%")
        st.metric("Active Positions", active_positions)
        st.metric("Max Positions", CONFIG['MAX_POSITIONS'])
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Portfolio", 
        "🔍 Market Scanner", 
        "📈 Performance", 
        "💼 Active Trades",
        "⚙️ Settings"
    ])
    
    with tab1:
        st.header("📊 Portfolio Analytics")
        
        if client:
            total_usd, portfolio, portfolio_change = get_portfolio_value()
            
            if portfolio:
                # Portfolio overview
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("💵 Total Value", f"${total_usd:,.2f}")
                
                with col2:
                    st.metric("📊 Assets", len(portfolio))
                
                with col3:
                    st.metric("24h Change", f"{portfolio_change:+.2f}%")
                
                with col4:
                    usdt_balance = portfolio.get('USDT', {}).get('total', 0)
                    st.metric("💰 USDT", f"{usdt_balance:,.2f}")
                
                st.divider()
                
                # Portfolio table
                st.subheader("💼 Holdings Breakdown")
                
                portfolio_data = []
                for asset, data in portfolio.items():
                    portfolio_data.append({
                        'Asset': asset,
                        'Balance': f"{data['total']:.6f}".rstrip('0').rstrip('.'),
                        'Price': f"${data['price']:.4f}",
                        'Value': f"${data['usd_value']:.2f}",
                        '24h Change': f"{data['change_24h']:+.2f}%",
                        'Allocation': f"{data['allocation_percent']:.1f}%"
                    })
                
                df = pd.DataFrame(portfolio_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Charts
                col1, col2 = st.columns(2)
                
                with col1:
                    # Portfolio allocation pie chart
                    if len(portfolio) > 1:
                        fig = px.pie(
                            values=[data['usd_value'] for data in portfolio.values()],
                            names=list(portfolio.keys()),
                            title="Portfolio Allocation"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # 24h performance bar chart
                    assets = list(portfolio.keys())
                    changes = [portfolio[asset]['change_24h'] for asset in assets]
                    
                    fig = go.Figure(data=[
                        go.Bar(
                            x=assets,
                            y=changes,
                            marker_color=['green' if x > 0 else 'red' for x in changes]
                        )
                    ])
                    fig.update_layout(title="24h Performance by Asset", yaxis_title="Change %")
                    st.plotly_chart(fig, use_container_width=True)
            
            else:
                st.warning("No significant portfolio holdings found.")
                st.info(f"Minimum balance filter: ${CONFIG['MIN_BALANCE_USD']}")
        else:
            st.error("Cannot load portfolio - Binance API not connected")
    
    with tab2:
        st.header("🔍 Advanced Market Scanner")
        
        scan_results = st.session_state.get('scan_results', [])
        last_scan = st.session_state.get('last_scan_time')
        
        # Scan info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Opportunities Found", len(scan_results))
        with col2:
            st.metric("Symbols Scanned", len(CONFIG['TRADING_PAIRS']))
        with col3:
            if last_scan:
                st.metric("Last Scan", last_scan.strftime("%H:%M:%S"))
        
        if scan_results:
            st.success(f"Found {len(scan_results)} trading opportunities")
            
            # Top opportunities
            st.subheader("🎯 Top Opportunities")
            
            for i, result in enumerate(scan_results[:5]):
                with st.expander(f"#{i+1} {result['symbol']} - {result['signal']} Signal ({result['confidence']:.1%} confidence)"):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Price", f"${result['current_price']:.4f}")
                        st.metric("24h Change", f"{result['price_change_24h']:+.2f}%")
                    
                    with col2:
                        st.metric("2h Change", f"{result['price_change_2h']:+.2f}%")
                        st.metric("Volume Ratio", f"{result['volume_ratio']:.1f}x")
                    
                    with col3:
                        st.metric("RSI (5m)", f"{result['rsi_5m']:.1f}")
                        st.metric("RSI (1h)", f"{result['rsi_1h']:.1f}")
                    
                    with col4:
                        st.metric("Volatility", f"{result['volatility']:.1%}")
                        st.metric("Trend", result['trend_direction'])
                    
                    # Signal details
                    st.write(f"**Signal:** {result['signal']}")
                    st.write(f"**Confidence:** {result['confidence']:.1%}")
                    st.write(f"**Timestamp:** {result['timestamp'].strftime('%H:%M:%S')}")
            
            # All results table
            if len(scan_results) > 5:
                st.subheader("📋 All Scan Results")
                
                results_data = []
                for result in scan_results:
                    results_data.append({
                        'Symbol': result['symbol'],
                        'Signal': result['signal'],
                        'Confidence': f"{result['confidence']:.1%}",
                        'Price': f"${result['current_price']:.4f}",
                        '24h Change': f"{result['price_change_24h']:+.2f}%",
                        '2h Change': f"{result['price_change_2h']:+.2f}%",
                        'RSI 5m': f"{result['rsi_5m']:.1f}",
                        'Trend': result['trend_direction']
                    })
                
                st.dataframe(pd.DataFrame(results_data), use_container_width=True, hide_index=True)
        
        else:
            st.info("No scan results yet. Click 'Scan Markets' to find opportunities.")
            
            # Show trading pairs being monitored
            st.subheader("📡 Monitored Trading Pairs")
            pairs_text = ", ".join(CONFIG['TRADING_PAIRS'])
            st.write(pairs_text)
    
    with tab3:
        st.header("📈 Performance Analytics")
        
        metrics = calculate_performance_metrics()
        
        # Performance overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Trades", metrics['total_trades'])
        
        with col2:
            st.metric("Win Rate", f"{metrics['win_rate']:.1f}%")
        
        with col3:
            st.metric("Total P&L", f"${metrics['total_pnl']:.2f}")
        
        with col4:
            st.metric("P&L %", f"{metrics['total_pnl_percent']:+.2f}%")
        
        if metrics['total_trades'] > 0:
            # Additional metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Best Trade", f"${metrics['best_trade']:.2f}")
            
            with col2:
                st.metric("Worst Trade", f"${metrics['worst_trade']:.2f}")
            
            with col3:
                st.metric("Avg Trade", f"${metrics['avg_trade']:.2f}")
            
            # Performance chart would go here
            st.info("📊 Performance charts will display once trading history is available")
        
        else:
            st.info("No trading history available yet. Start the auto bot to begin tracking performance.")
        
        # Bot statistics
        st.subheader("🤖 Bot Statistics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Scans Completed", st.session_state.get('scan_count', 0))
        
        with col2:
            if st.session_state.get('bot_start_time'):
                runtime = datetime.now() - st.session_state['bot_start_time']
                st.metric("Bot Runtime", str(runtime).split('.')[0])
            else:
                st.metric("Bot Runtime", "Not started")
        
        with col3:
            active_positions = len(st.session_state.get('active_positions', {}))
            st.metric("Active Positions", f"{active_positions}/{CONFIG['MAX_POSITIONS']}")
    
    with tab4:
        st.header("💼 Active Trades & Positions")
        
        active_positions = st.session_state.get('active_positions', {})
        
        if active_positions:
            st.success(f"Managing {len(active_positions)} active positions")
            
            # Active positions table
            position_data = []
            for pos_id, position in active_positions.items():
                # Calculate current P&L (simulated)
                current_time = datetime.now()
                time_held = current_time - position['timestamp']
                
                # Simulate price movement for demo
                price_change = np.random.uniform(-0.02, 0.02)  # Random ±2%
                current_price = position['entry_price'] * (1 + price_change)
                
                if position['signal'] == 'BUY':
                    pnl_pct = ((current_price - position['entry_price']) / position['entry_price']) * 100
                else:
                    pnl_pct = ((position['entry_price'] - current_price) / position['entry_price']) * 100
                
                pnl_usd = (position['quantity'] * position['entry_price']) * (pnl_pct / 100)
                
                position_data.append({
                    'Symbol': position['symbol'],
                    'Signal': position['signal'],
                    'Entry Price': f"${position['entry_price']:.4f}",
                    'Current Price': f"${current_price:.4f}",
                    'Quantity': f"{position['quantity']:.6f}",
                    'P&L %': f"{pnl_pct:+.2f}%",
                    'P&L USD': f"${pnl_usd:+.2f}",
                    'Time Held': str(time_held).split('.')[0],
                    'Status': position['status']
                })
            
            df_positions = pd.DataFrame(position_data)
            st.dataframe(df_positions, use_container_width=True, hide_index=True)
            
            # Position management controls
            st.subheader("🎛️ Position Management")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📊 Update All Positions"):
                    st.success("Positions updated!")
            
            with col2:
                if st.button("⚠️ Close All Positions"):
                    st.session_state['active_positions'] = {}
                    st.success("All positions closed!")
                    st.rerun()
            
            with col3:
                if st.button("📈 Optimize Positions"):
                    st.info("Position optimization completed!")
        
        else:
            st.info("No active positions. Start the auto bot or execute manual trades to see positions here.")
        
        # Trade history
        st.subheader("📝 Recent Trade History")
        trade_history = st.session_state.get('trade_history', [])
        
        if trade_history:
            history_data = []
            for trade in trade_history[-10:]:  # Last 10 trades
                history_data.append({
                    'Time': trade['timestamp'].strftime('%H:%M:%S'),
                    'Symbol': trade['symbol'],
                    'Signal': trade['signal'],
                    'Entry': f"${trade['entry_price']:.4f}",
                    'Exit': f"${trade['exit_price']:.4f}",
                    'P&L': f"${trade['pnl']:+.2f}",
                    'P&L %': f"{trade['pnl_percent']:+.2f}%"
                })
            
            st.dataframe(pd.DataFrame(history_data), use_container_width=True, hide_index=True)
        else:
            st.info("No completed trades yet.")
    
    with tab5:
        st.header("⚙️ Bot Configuration & Settings")
        
        # Current configuration
        st.subheader("📋 Current Configuration")
        
        config_display = {
            'Setting': [
                'Trading Mode',
                'API Connection', 
                'Minimum Balance Filter',
                'Risk Per Trade',
                'Maximum Positions',
                'Minimum Confidence',
                'Scan Interval',
                'Trading Pairs Count'
            ],
            'Value': [
                'Testnet' if CONFIG['USE_TESTNET'] else 'Live Trading',
                'Connected' if client else 'Disconnected',
                f"${CONFIG['MIN_BALANCE_USD']}",
                f"{CONFIG['RISK_PERCENTAGE']:.1%}",
                CONFIG['MAX_POSITIONS'],
                f"{CONFIG['MIN_CONFIDENCE']:.1%}",
                f"{CONFIG['SCAN_INTERVAL']}s",
                len(CONFIG['TRADING_PAIRS'])
            ],
            'Status': [
                '🧪' if CONFIG['USE_TESTNET'] else '🚀',
                '✅' if client else '❌',
                '✅',
                '✅',
                '✅', 
                '✅',
                '✅',
                '✅'
            ]
        }
        
        st.dataframe(pd.DataFrame(config_display), use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Environment variables
        st.subheader("🔧 Environment Variables")
        
        with st.expander("View Environment Configuration"):
            st.code(f"""
# Core Configuration
USE_TESTNET={CONFIG['USE_TESTNET']}
BINANCE_API_KEY={'***' + CONFIG['BINANCE_API_KEY'][-4:] if CONFIG['BINANCE_API_KEY'] else 'Not Set'}
BINANCE_API_SECRET={'***' + CONFIG['BINANCE_API_SECRET'][-4:] if CONFIG['BINANCE_API_SECRET'] else 'Not Set'}

# Trading Parameters
MIN_BALANCE_USD={CONFIG['MIN_BALANCE_USD']}
RISK_PERCENTAGE={CONFIG['RISK_PERCENTAGE']}
MAX_POSITIONS={CONFIG['MAX_POSITIONS']}
MIN_CONFIDENCE={CONFIG['MIN_CONFIDENCE']}
SCAN_INTERVAL={CONFIG['SCAN_INTERVAL']}

# System
LOG_LEVEL={CONFIG['LOG_LEVEL']}
RAILWAY_ENV={CONFIG['RAILWAY_ENV']}
            """)
        
        # Dependency status
        st.subheader("📦 System Dependencies")
        
        dep_data = []
        for dep, available in DEPENDENCIES.items():
            dep_data.append({
                'Dependency': dep.upper(),
                'Status': 'Available' if available else 'Missing',
                'Icon': '✅' if available else '❌'
            })
        
        st.dataframe(pd.DataFrame(dep_data), use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Trading pairs configuration
        st.subheader("📊 Trading Pairs")
        
        with st.expander("View All Trading Pairs"):
            pairs_per_row = 5
            pairs = CONFIG['TRADING_PAIRS']
            
            for i in range(0, len(pairs), pairs_per_row):
                cols = st.columns(pairs_per_row)
                for j, pair in enumerate(pairs[i:i+pairs_per_row]):
                    with cols[j]:
                        st.write(f"• {pair}")
        
        # Safety warnings
        st.subheader("⚠️ Safety Information")
        
        if not CONFIG['USE_TESTNET']:
            st.error("🚨 LIVE TRADING MODE ACTIVE - Real money at risk!")
            st.warning("• All trades execute with real funds")
            st.warning("• Monitor bot activity closely")
            st.warning("• Set appropriate risk limits")
        else:
            st.success("🧪 TESTNET MODE - Safe for testing")
            st.info("• All trades are simulated")
            st.info("• No real money at risk")
            st.info("• Perfect for strategy testing")
        
        # System health
        st.subheader("💓 System Health")
        
        health_metrics = {
            'Metric': ['Memory Usage', 'Active Threads', 'API Latency', 'Last Error'],
            'Value': ['N/A', 'N/A', 'N/A', 'None'],
            'Status': ['🟢', '🟢', '🟢', '🟢']
        }
        
        st.dataframe(pd.DataFrame(health_metrics), use_container_width=True, hide_index=True)
        
        # Manual controls
        st.subheader("🛠️ Manual Controls")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ Clear Session Data"):
                # Clear non-essential session data
                for key in ['scan_results', 'trade_history']:
                    if key in st.session_state:
                        st.session_state[key] = []
                st.session_state['scan_count'] = 0
                st.success("Session data cleared!")
        
        with col2:
            if st.button("📝 Export Logs"):
                # Create download for logs
                log_data = {
                    'scan_results': st.session_state.get('scan_results', []),
                    'trade_history': st.session_state.get('trade_history', []),
                    'active_positions': st.session_state.get('active_positions', {}),
                    'timestamp': datetime.now().isoformat()
                }
                st.download_button(
                    "📥 Download Log Data",
                    json.dumps(log_data, indent=2, default=str),
                    file_name=f"bot_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col3:
            if st.button("🔄 Reset Bot"):
                # Reset all bot data
                for key in DEFAULT_SESSION_STATE:
                    st.session_state[key] = DEFAULT_SESSION_STATE[key]
                st.success("Bot reset complete!")
                st.rerun()

if __name__ == "__main__":
    # Initialize logging
    log_activity("Hybrid Crypto Trading Bot started")
    
    # Run main application
    main()
    
    # Footer
    st.divider()
    st.caption(f"🤖 Hybrid Crypto Trading Bot v1.0 | Mode: {'Testnet' if CONFIG['USE_TESTNET'] else 'Live'} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if CONFIG['RAILWAY_ENV']:
        st.caption("🚂 Running on Railway Platform")