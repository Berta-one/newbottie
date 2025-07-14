import os
import time
import streamlit as st
from datetime import datetime
import pandas as pd
import json
from binance.client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET") 
USE_TESTNET = os.getenv("USE_TESTNET", "True").lower() == "true"
ENABLE_PAPER_TRADING = os.getenv("ENABLE_PAPER_TRADING", "True").lower() == "true"
TRADE_SYMBOL = os.getenv("TRADE_SYMBOL", "BTCUSDT")

# Initialize Binance client
@st.cache_resource
def get_binance_client():
    try:
        if not API_KEY or not API_SECRET:
            return None
            
        client = Client(API_KEY, API_SECRET)
        
        if USE_TESTNET:
            client.API_URL = "https://testnet.binance.vision/api"
        
        # Test connection
        client.get_server_time()
        return client
    except Exception as e:
        st.error(f"❌ Binance connection failed: {e}")
        return None

# Real strategy functions
def calculate_rsi(prices, period=14):
    """Calculate RSI"""
    if len(prices) < period + 1:
        return 50
    
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d for d in deltas if d > 0]
    losses = [-d for d in deltas if d < 0]
    
    avg_gain = sum(gains[-period:]) / period if gains else 0
    avg_loss = sum(losses[-period:]) / period if losses else 0
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def analyze_real_market(klines):
    """Analyze real market data with enhanced strategy"""
    if len(klines) < 120:
        return "HOLD", 0.5, {}
    
    # Extract prices and volumes
    closes = [float(k[4]) for k in klines]
    volumes = [float(k[5]) for k in klines]
    
    # Calculate indicators
    current_price = closes[-1]
    start_price = closes[0]
    change_2h = ((current_price - start_price) / start_price) * 100
    
    # Volume analysis
    avg_volume = sum(volumes[-20:]) / 20
    current_volume = volumes[-1]
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
    
    # RSI
    rsi = calculate_rsi(closes)
    
    # Moving averages
    sma_20 = sum(closes[-20:]) / 20
    sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else sma_20
    
    # Enhanced breakout detection
    base_threshold = 5.0
    
    # Adjust threshold based on volume
    if volume_ratio > 2.0:
        threshold = base_threshold * 0.8  # Lower threshold for high volume
    else:
        threshold = base_threshold
    
    # Generate signals
    signal = "HOLD"
    confidence = 0.5
    
    if change_2h >= threshold:
        if rsi < 80 and current_price > sma_20:  # Not overbought + above MA
            signal = "BUY_LONG"
            confidence = min(0.9, 0.6 + (volume_ratio - 1) * 0.1)
    elif change_2h <= -threshold:
        if rsi > 20 and current_price < sma_20:  # Not oversold + below MA
            signal = "BUY_SHORT"
            confidence = min(0.9, 0.6 + (volume_ratio - 1) * 0.1)
    
    # Market context
    context = {
        'current_price': current_price,
        'change_2h': change_2h,
        'volume_ratio': volume_ratio,
        'rsi': rsi,
        'sma_20': sma_20,
        'sma_50': sma_50,
        'threshold_used': threshold
    }
    
    return signal, confidence, context

def get_account_balance(client, asset='USDT'):
    """Get account balance"""
    try:
        account = client.get_account()
        for balance in account['balances']:
            if balance['asset'] == asset:
                return float(balance['free'])
        return 0.0
    except:
        return 10000.0 if USE_TESTNET else 0.0

# Main dashboard
def main():
    st.set_page_config(page_title="🚀 Live Crypto Trading Bot", layout="wide")
    
    st.title("🚀 Live Crypto Trading Bot - Binance Integration")
    st.caption("Real-time market data and trading analysis")
    
    # Initialize session state
    if 'trades' not in st.session_state:
        st.session_state.trades = []
    if 'positions' not in st.session_state:
        st.session_state.positions = {}
    
    # Get Binance client
    client = get_binance_client()
    
    # Connection status
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if client:
            st.metric("🟢 Binance", "Connected", "Live Data")
        else:
            st.metric("🔴 Binance", "Disconnected", "Need API Keys")
    
    with col2:
        mode = "TESTNET" if USE_TESTNET else "LIVE"
        st.metric("🌐 Mode", mode, "Paper Trading" if ENABLE_PAPER_TRADING else "Real Trading")
    
    with col3:
        if client:
            balance = get_account_balance(client)
            st.metric("💰 Balance", f"${balance:,.2f}", "USDT")
        else:
            st.metric("💰 Balance", "No Data", "API Required")
    
    with col4:
        st.metric("⏰ Time", datetime.now().strftime("%H:%M:%S"), "Live")
    
    # API Key configuration
    if not client:
        st.error("🔐 Binance API Configuration Required")
        
        with st.expander("🔧 Configure API Keys"):
            st.warning("⚠️ Add these environment variables in Railway:")
            
            st.code("""
# Go to Railway → Your Project → Variables tab
# Add these variables:

BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_secret_here
USE_TESTNET=True
ENABLE_PAPER_TRADING=True
TRADE_SYMBOL=BTCUSDT
            """)
            
            st.info("""
            **Get Testnet API Keys:**
            1. Go to: https://testnet.binance.vision/
            2. Create account
            3. Generate API Key + Secret
            4. Add to Railway environment variables
            5. Redeploy the app
            """)
        
        return
    
    # Real-time market analysis
    st.subheader("📈 Live Market Analysis")
    
    try:
        # Get real market data
        klines = client.get_klines(
            symbol=TRADE_SYMBOL,
            interval=Client.KLINE_INTERVAL_1MINUTE,
            limit=120
        )
        
        ticker = client.get_symbol_ticker(symbol=TRADE_SYMBOL)
        current_price = float(ticker['price'])
        
        # Analyze market
        signal, confidence, context = analyze_real_market(klines)
        
        # Display market data
        col1, col2, col3 = st.columns(3)
        
        with col1:
            change_24h = float(client.get_ticker(symbol=TRADE_SYMBOL)['priceChangePercent'])
            st.metric(f"💰 {TRADE_SYMBOL}", f"${current_price:,.2f}", f"{change_24h:+.2f}%")
        
        with col2:
            signal_color = "🟢" if signal == "BUY_LONG" else "🔴" if signal == "BUY_SHORT" else "🟡"
            st.metric(f"{signal_color} Signal", signal, f"Confidence: {confidence:.1%}")
        
        with col3:
            st.metric("📊 2h Change", f"{context['change_2h']:+.2f}%", 
                     f"Threshold: ±{context['threshold_used']:.1f}%")
        
        # Technical indicators
        st.subheader("🔍 Technical Analysis")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📈 RSI", f"{context['rsi']:.1f}", 
                     "Overbought" if context['rsi'] > 70 else "Oversold" if context['rsi'] < 30 else "Neutral")
        
        with col2:
            st.metric("📊 Volume", f"{context['volume_ratio']:.1f}x", "vs 20-period avg")
        
        with col3:
            st.metric("📉 SMA 20", f"${context['sma_20']:,.2f}", 
                     "Above" if current_price > context['sma_20'] else "Below")
        
        with col4:
            st.metric("📈 SMA 50", f"${context['sma_50']:,.2f}",
                     "Above" if current_price > context['sma_50'] else "Below")
        
        # Trading simulation
        st.subheader("🎯 Trading Activity")
        
        if ENABLE_PAPER_TRADING:
            st.info("📝 Paper Trading Mode - All trades are simulated")
        else:
            st.warning("⚠️ LIVE TRADING MODE - Real money at risk!")
        
        # Auto-execute trades
        if signal != "HOLD" and confidence > 0.7:
            position_key = f"{signal}_{int(time.time() // 300)}"  # 5-minute windows
            
            if position_key not in st.session_state.positions:
                # Execute new trade
                trade = {
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "action": signal,
                    "price": current_price,
                    "confidence": confidence,
                    "volume_ratio": context['volume_ratio'],
                    "rsi": context['rsi']
                }
                
                st.session_state.trades.append(trade)
                st.session_state.positions[position_key] = {
                    "entry_price": current_price,
                    "entry_time": datetime.now(),
                    "signal": signal,
                    "confidence": confidence
                }
                
                st.success(f"🎯 {signal} Signal Executed at ${current_price:,.2f} (Confidence: {confidence:.1%})")
        
        # Monitor positions
        for pos_key, position in list(st.session_state.positions.items()):
            entry_price = position["entry_price"]
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
            time_held = (datetime.now() - position["entry_time"]).total_seconds() / 60
            
            # Auto-close conditions
            take_profit = 10.0 if position["confidence"] > 0.8 else 8.0
            stop_loss = 10.0 if position["confidence"] > 0.8 else 8.0
            
            if pnl_pct >= take_profit or pnl_pct <= -stop_loss or time_held >= 240:
                # Close position
                reason = "Take Profit" if pnl_pct >= take_profit else "Stop Loss" if pnl_pct <= -stop_loss else "Time Limit"
                
                exit_trade = {
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "action": f"CLOSE_{position['signal']}",
                    "price": current_price,
                    "pnl": pnl_pct,
                    "reason": reason,
                    "time_held": time_held
                }
                
                st.session_state.trades.append(exit_trade)
                del st.session_state.positions[pos_key]
                
                if pnl_pct > 0:
                    st.success(f"💰 Position Closed: {pnl_pct:+.2f}% PROFIT ({reason})")
                else:
                    st.error(f"📉 Position Closed: {pnl_pct:+.2f}% LOSS ({reason})")
        
        # Display open positions
        if st.session_state.positions:
            st.subheader("📊 Open Positions")
            
            for pos_key, position in st.session_state.positions.items():
                entry_price = position["entry_price"]
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
                time_held = (datetime.now() - position["entry_time"]).total_seconds() / 60
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.text(f"Signal: {position['signal']}")
                with col2:
                    st.text(f"Entry: ${entry_price:,.2f}")
                with col3:
                    color = "green" if pnl_pct > 0 else "red"
                    st.markdown(f"P&L: <span style='color:{color}'>{pnl_pct:+.2f}%</span>", 
                               unsafe_allow_html=True)
                with col4:
                    st.text(f"Time: {time_held:.0f}m")
        
        # Trading history and performance
        if st.session_state.trades:
            st.subheader("📋 Trading History")
            
            # Performance metrics
            closed_trades = [t for t in st.session_state.trades if 'pnl' in t]
            
            if closed_trades:
                total_trades = len(closed_trades)
                winning_trades = len([t for t in closed_trades if t['pnl'] > 0])
                total_pnl = sum(t['pnl'] for t in closed_trades)
                win_rate = (winning_trades / total_trades) * 100
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("🎯 Trades", total_trades)
                with col2:
                    st.metric("📈 Win Rate", f"{win_rate:.1f}%")
                with col3:
                    color = "green" if total_pnl > 0 else "red"
                    st.markdown(f"💰 Total P&L: <span style='color:{color}'>{total_pnl:+.2f}%</span>", 
                               unsafe_allow_html=True)
                with col4:
                    avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
                    st.metric("📊 Avg Trade", f"{avg_pnl:+.2f}%")
            
            # Recent trades table
            recent_trades = st.session_state.trades[-15:]  # Last 15 trades
            if recent_trades:
                df = pd.DataFrame(recent_trades)
                st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error fetching market data: {e}")
        st.info("🔄 Retrying in next refresh...")
    
    # Configuration
    with st.expander("⚙️ Current Configuration"):
        config = {
            "Exchange": "Binance",
            "Mode": "Testnet" if USE_TESTNET else "Live",
            "Trading": "Paper" if ENABLE_PAPER_TRADING else "Real",
            "Symbol": TRADE_SYMBOL,
            "Strategy": "Enhanced 5% Breakout",
            "Take Profit": "8-10% (confidence based)",
            "Stop Loss": "8-10% (confidence based)",
            "Max Hold Time": "4 hours",
            "Volume Filter": "Required for signals",
            "RSI Filter": "Avoid overbought/oversold",
            "Auto Refresh": "Every 5 seconds"
        }
        st.json(config)
    
    # Auto-refresh
    time.sleep(1)
    st.rerun()

if __name__ == "__main__":
    main()
