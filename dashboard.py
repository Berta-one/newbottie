# dashboard.py - Advanced Multi-Pair Trading Dashboard
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
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(page_title="🚀 Advanced Multi-Pair Trading Bot", layout="wide")

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

if "scan_mode" not in st.session_state:
    st.session_state.scan_mode = "SELECTED"

if "selected_profile" not in st.session_state:
    st.session_state.selected_profile = "AUTO"

# Advanced Trading Configuration
SCAN_MODES = {
    "ALL": "Scan all USDT pairs with minimum volume",
    "SELECTED": "Curated list of quality crypto pairs",
    "CUSTOM": "User-defined symbol list"
}

# Multi-Pair Categories (from knowledge base)
SELECTED_PAIRS = {
    "MAJOR": [
        {"symbol": "BTCUSDT", "category": "Major", "risk_multiplier": 1.0},
        {"symbol": "ETHUSDT", "category": "Major", "risk_multiplier": 1.0},
        {"symbol": "BNBUSDT", "category": "Major", "risk_multiplier": 1.0}
    ],
    "LARGE_CAP": [
        {"symbol": "ADAUSDT", "category": "Large Cap", "risk_multiplier": 0.8},
        {"symbol": "SOLUSDT", "category": "Large Cap", "risk_multiplier": 0.8},
        {"symbol": "XRPUSDT", "category": "Large Cap", "risk_multiplier": 0.8},
        {"symbol": "DOTUSDT", "category": "Large Cap", "risk_multiplier": 0.8},
        {"symbol": "AVAXUSDT", "category": "Large Cap", "risk_multiplier": 0.8}
    ],
    "MID_CAP": [
        {"symbol": "LINKUSDT", "category": "Mid Cap", "risk_multiplier": 0.7},
        {"symbol": "UNIUSDT", "category": "Mid Cap", "risk_multiplier": 0.7},
        {"symbol": "LTCUSDT", "category": "Mid Cap", "risk_multiplier": 0.7}
    ],
    "DEFI": [
        {"symbol": "AAVEUSDT", "category": "DeFi", "risk_multiplier": 0.6},
        {"symbol": "COMPUSDT", "category": "DeFi", "risk_multiplier": 0.6}
    ],
    "GAMING": [
        {"symbol": "SANDUSDT", "category": "Gaming", "risk_multiplier": 0.5},
        {"symbol": "MANAUSDT", "category": "Gaming", "risk_multiplier": 0.5}
    ]
}

# Advanced Risk Profiles (from knowledge base)
ADVANCED_RISK_PROFILES = {
    "AUTO": {
        "name": "Auto-Adaptive",
        "description": "AI-powered profile selection based on market conditions",
        "features": ["Market condition detection", "Volatility adaptation", "Performance feedback"]
    },
    "CONSERVATIVE": {
        "name": "Conservative",
        "take_profit": 6.0, "stop_loss": 4.0, "trailing_stop": 2.5,
        "max_hold_hours": 6, "confidence_threshold": 0.8,
        "description": "Low volatility, high confidence trades"
    },
    "BALANCED": {
        "name": "Balanced",
        "take_profit": 10.0, "stop_loss": 8.0, "trailing_stop": 3.5,
        "max_hold_hours": 4, "confidence_threshold": 0.7,
        "description": "Standard institutional approach"
    },
    "AGGRESSIVE": {
        "name": "Aggressive",
        "take_profit": 15.0, "stop_loss": 12.0, "trailing_stop": 5.0,
        "max_hold_hours": 8, "confidence_threshold": 0.6,
        "description": "High volatility, trend-following"
    },
    "SCALPING": {
        "name": "Scalping",
        "take_profit": 3.0, "stop_loss": 2.0, "trailing_stop": 1.0,
        "max_hold_hours": 1, "confidence_threshold": 0.85,
        "description": "Quick profits, minimal risk"
    },
    "SWING": {
        "name": "Swing Trading",
        "take_profit": 20.0, "stop_loss": 15.0, "trailing_stop": 8.0,
        "max_hold_hours": 24, "confidence_threshold": 0.75,
        "description": "Multi-day position holding"
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
        
        client.get_server_time()
        return client
    except Exception as e:
        st.error(f"❌ Binance connection failed: {e}")
        return None

@st.cache_data(ttl=60)
def get_gbp_exchange_rate():
    """Get live USD to GBP exchange rate"""
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        if response.status_code == 200:
            return response.json()['rates']['GBP']
    except:
        pass
    return 0.79

@st.cache_data(ttl=300)
def get_all_usdt_pairs():
    """Get all USDT trading pairs with volume filtering"""
    client = get_binance_client()
    if not client:
        return []
    
    try:
        ticker_24h = client.get_ticker()
        usdt_pairs = []
        excluded_keywords = ['UP', 'DOWN', 'BEAR', 'BULL']
        
        for ticker in ticker_24h:
            symbol = ticker['symbol']
            volume = float(ticker['quoteVolume'])
            price_change = float(ticker['priceChangePercent'])
            
            if (symbol.endswith('USDT') and 
                volume >= 2000000 and  # Minimum $2M volume
                not any(keyword in symbol for keyword in excluded_keywords)):
                
                usdt_pairs.append({
                    'symbol': symbol,
                    'volume_24h': volume,
                    'price_change_24h': price_change,
                    'category': 'Market',
                    'risk_multiplier': 1.0
                })
        
        # Sort by volume
        usdt_pairs.sort(key=lambda x: x['volume_24h'], reverse=True)
        return usdt_pairs[:50]  # Top 50 by volume
        
    except Exception as e:
        st.error(f"❌ Error fetching USDT pairs: {e}")
        return []

def simulate_multi_pair_analysis():
    """Simulate advanced multi-pair analysis"""
    # Get all selected pairs
    all_pairs = []
    for category, pairs in SELECTED_PAIRS.items():
        all_pairs.extend(pairs)
    
    opportunities = []
    
    for pair in all_pairs:
        # Simulate market analysis
        signal = np.random.choice(["BUY_LONG", "BUY_SHORT", "HOLD"], p=[0.15, 0.15, 0.7])
        confidence = np.random.uniform(0.5, 0.95)
        current_price = np.random.uniform(0.1, 70000)
        change_2h = np.random.uniform(-8, 8)
        volume_ratio = np.random.uniform(0.8, 4.0)
        rsi = np.random.uniform(20, 80)
        
        # Calculate scan score
        scan_score = confidence * 0.6
        if volume_ratio > 2.0:
            scan_score += 0.2
        if 30 < rsi < 70:
            scan_score += 0.1
        
        opportunities.append({
            'symbol': pair['symbol'],
            'category': pair['category'],
            'signal': signal,
            'confidence': confidence,
            'current_price': current_price,
            'change_2h': change_2h,
            'volume_ratio': volume_ratio,
            'rsi': rsi,
            'scan_score': min(1.0, scan_score),
            'risk_multiplier': pair['risk_multiplier']
        })
    
    # Sort by scan score
    opportunities.sort(key=lambda x: x['scan_score'], reverse=True)
    return opportunities

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
                trading_symbols = []
                
                if asset in ['USDT', 'BUSD', 'USDC']:
                    usd_value = total_balance
                    price_usd = 1.0
                    trading_symbols = [f"{asset}USDT"]
                else:
                    # Check multiple trading pairs
                    for quote in ['USDT', 'BUSD', 'USDC', 'BTC', 'ETH']:
                        symbol = f"{asset}{quote}"
                        if symbol in price_map:
                            trading_symbols.append(symbol)
                            if quote in ['USDT', 'BUSD', 'USDC']:
                                price_usd = price_map[symbol]
                                usd_value = total_balance * price_usd
                
                if usd_value >= 1.0:
                    # Get 24h price change
                    change_24h = 0.0
                    try:
                        if trading_symbols:
                            ticker_24h = client.get_24hr_ticker(symbol=trading_symbols[0])
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
                        'trading_pairs': trading_symbols
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
    """Demo portfolio with multiple trading pairs"""
    gbp_rate = get_gbp_exchange_rate()
    
    portfolio = {
        'BTC': {
            'balance': 0.15234, 'price_usd': 64950.0, 'usd_value': 9890.45,
            'change_24h': 2.34, 'free': 0.15234, 'locked': 0.0,
            'trading_pairs': ['BTCUSDT', 'BTCBUSD', 'BTCETH']
        },
        'ETH': {
            'balance': 1.8945, 'price_usd': 2410.50, 'usd_value': 4567.89,
            'change_24h': -1.23, 'free': 1.8945, 'locked': 0.0,
            'trading_pairs': ['ETHUSDT', 'ETHBUSD', 'ETHBTC']
        },
        'SOL': {
            'balance': 45.67, 'price_usd': 62.98, 'usd_value': 2876.32,
            'change_24h': 5.67, 'free': 45.67, 'locked': 0.0,
            'trading_pairs': ['SOLUSDT', 'SOLBUSD']
        },
        'ADA': {
            'balance': 2890.5, 'price_usd': 0.427, 'usd_value': 1234.56,
            'change_24h': -2.1, 'free': 2890.5, 'locked': 0.0,
            'trading_pairs': ['ADAUSDT', 'ADABUSD', 'ADABTC']
        },
        'USDT': {
            'balance': 1234.56, 'price_usd': 1.0, 'usd_value': 1234.56,
            'change_24h': 0.0, 'free': 1234.56, 'locked': 0.0,
            'trading_pairs': ['USDT']
        }
    }
    
    total_usd = sum(p['usd_value'] for p in portfolio.values())
    
    for asset in portfolio:
        portfolio[asset]['gbp_value'] = portfolio[asset]['usd_value'] * gbp_rate
        portfolio[asset]['percentage'] = (portfolio[asset]['usd_value'] / total_usd) * 100
    
    return portfolio, total_usd, total_usd * gbp_rate

def load_multi_pair_data():
    """Load multi-pair trading data"""
    try:
        # Load from multiple log files
        single_pair_trades = []
        multi_pair_trades = []
        
        # Single pair trades
        if os.path.exists("logs/single_pair_performance.json"):
            with open("logs/single_pair_performance.json", "r") as f:
                for line in f:
                    if line.strip():
                        trade = json.loads(line)
                        if trade.get('mode') != 'SIMULATION':
                            single_pair_trades.append(trade)
        
        # Multi-pair trades
        if os.path.exists("logs/multi_pair_trades.json"):
            with open("logs/multi_pair_trades.json", "r") as f:
                multi_pair_trades = json.load(f)
        
        all_trades = single_pair_trades + multi_pair_trades
        return pd.DataFrame(all_trades)
        
    except Exception as e:
        return pd.DataFrame()

def load_scan_results():
    """Load latest scan results"""
    try:
        scan_files = [
            "logs/scan_results.json",
            "logs/selected_scan_results.json",
            "logs/custom_scan_results.json"
        ]
        
        latest_results = None
        latest_time = 0
        
        for file_path in scan_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        scan_time = datetime.fromisoformat(data.get('scan_timestamp', '2000-01-01'))
                        if scan_time.timestamp() > latest_time:
                            latest_time = scan_time.timestamp()
                            latest_results = data
                except:
                    continue
        
        return latest_results
    except:
        return None

def render_multi_pair_scanner_tab():
    """Render the advanced multi-pair scanner tab"""
    st.header("🔍 Advanced Multi-Pair Scanner")
    
    # Scanner configuration
    col1, col2, col3 = st.columns(3)
    
    with col1:
        scan_mode = st.selectbox(
            "📊 Scan Mode:",
            options=list(SCAN_MODES.keys()),
            format_func=lambda x: f"{x}: {SCAN_MODES[x]}",
            index=list(SCAN_MODES.keys()).index(st.session_state.scan_mode)
        )
        st.session_state.scan_mode = scan_mode
    
    with col2:
        min_confidence = st.slider("🎯 Min Confidence:", 0.5, 0.95, 0.65, 0.05)
    
    with col3:
        max_positions = st.slider("📈 Max Positions:", 1, 10, 3)
    
    # Display scan mode details
    if scan_mode == "ALL":
        st.info("🌍 **ALL Mode**: Scanning all USDT pairs with minimum $2M 24h volume")
        pairs_to_scan = get_all_usdt_pairs()
        st.write(f"📊 Found {len(pairs_to_scan)} qualifying USDT pairs")
        
    elif scan_mode == "SELECTED":
        st.success("✅ **SELECTED Mode**: Curated quality crypto pairs across categories")
        
        # Show categories
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🥇 Major Pairs:**")
            for pair in SELECTED_PAIRS["MAJOR"]:
                st.write(f"• {pair['symbol']} (Risk: {pair['risk_multiplier']}x)")
        
        with col2:
            st.markdown("**📈 Large Cap:**")
            for pair in SELECTED_PAIRS["LARGE_CAP"]:
                st.write(f"• {pair['symbol']} (Risk: {pair['risk_multiplier']}x)")
        
        with col3:
            st.markdown("**🎯 Specialized:**")
            for category in ["MID_CAP", "DEFI", "GAMING"]:
                st.write(f"**{category.replace('_', ' ').title()}:**")
                for pair in SELECTED_PAIRS[category]:
                    st.write(f"• {pair['symbol']}")
        
    else:  # CUSTOM
        st.warning("🎯 **CUSTOM Mode**: User-defined symbol list")
        custom_symbols = st.text_area(
            "Enter symbols (comma-separated):",
            value="BTCUSDT,ETHUSDT,ADAUSDT,SOLUSDT",
            height=100
        )
    
    # Scan button
    if st.button("🚀 Start Multi-Pair Scan", type="primary", use_container_width=True):
        with st.spinner("🔄 Scanning multiple pairs for opportunities..."):
            # Simulate scan results
            opportunities = simulate_multi_pair_analysis()
            
            # Filter by confidence
            filtered_opps = [opp for opp in opportunities if opp['confidence'] >= min_confidence]
            
            st.success(f"✅ Scan completed! Found {len(filtered_opps)} opportunities above {min_confidence:.0%} confidence")
            
            # Display top opportunities
            if filtered_opps:
                st.subheader("🎯 Top Trading Opportunities")
                
                # Create opportunities table
                opp_data = []
                for opp in filtered_opps[:10]:
                    opp_data.append({
                        'Symbol': opp['symbol'],
                        'Category': opp['category'],
                        'Signal': opp['signal'],
                        'Confidence': f"{opp['confidence']:.2f}",
                        'Score': f"{opp['scan_score']:.2f}",
                        'Price': f"${opp['current_price']:.4f}",
                        '2h Change': f"{opp['change_2h']:+.1f}%",
                        'Volume': f"{opp['volume_ratio']:.1f}x",
                        'RSI': f"{opp['rsi']:.0f}"
                    })
                
                df_opps = pd.DataFrame(opp_data)
                st.dataframe(df_opps, use_container_width=True, hide_index=True)
                
                # Opportunity distribution chart
                col1, col2 = st.columns(2)
                
                with col1:
                    # Signal distribution
                    signal_counts = pd.Series([opp['signal'] for opp in filtered_opps]).value_counts()
                    fig_signals = px.pie(values=signal_counts.values, names=signal_counts.index,
                                       title="Signal Distribution")
                    st.plotly_chart(fig_signals, use_container_width=True)
                
                with col2:
                    # Category distribution
                    category_counts = pd.Series([opp['category'] for opp in filtered_opps]).value_counts()
                    fig_categories = px.bar(x=category_counts.index, y=category_counts.values,
                                          title="Opportunities by Category")
                    st.plotly_chart(fig_categories, use_container_width=True)

def render_portfolio_tab():
    """Render enhanced portfolio tab with multi-pair support"""
    st.header("💼 Multi-Pair Portfolio Overview")
    
    # Get portfolio data
    use_testnet = os.getenv("USE_TESTNET", "True").lower() == "true"
    
    if use_testnet:
        st.info("🧪 **TESTNET MODE** - Using demo portfolio data with multi-pair support")
        portfolio, total_usd, total_gbp = get_demo_portfolio()
    else:
        st.success("💰 **LIVE MODE** - Real Binance portfolio with all trading pairs")
        portfolio, total_usd, total_gbp = get_real_portfolio()
    
    # Enhanced portfolio summary
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("💷 Total (GBP)", f"£{total_gbp:,.2f}")
    
    with col2:
        st.metric("💰 Total (USD)", f"${total_usd:,.2f}")
    
    with col3:
        st.metric("🪙 Assets", len(portfolio))
    
    with col4:
        # Count total trading pairs
        total_pairs = sum(len(data.get('trading_pairs', [])) for data in portfolio.values())
        st.metric("🔗 Trading Pairs", total_pairs)
    
    with col5:
        # Portfolio 24h change
        total_24h_change = 0
        for asset, data in portfolio.items():
            weight = data['percentage'] / 100
            total_24h_change += data['change_24h'] * weight
        
        change_color = "🟢" if total_24h_change > 0 else "🔴" if total_24h_change < 0 else "⚪"
        st.metric(f"{change_color} 24h Change", f"{total_24h_change:+.2f}%")
    
    # Enhanced holdings table with trading pairs
    st.subheader("📊 Multi-Pair Holdings Analysis")
    
    if portfolio:
        portfolio_data = []
        for asset, data in portfolio.items():
            trading_pairs_str = ", ".join(data.get('trading_pairs', [])[:3])
            if len(data.get('trading_pairs', [])) > 3:
                trading_pairs_str += f" +{len(data['trading_pairs']) - 3} more"
            
            portfolio_data.append({
                'Asset': asset,
                'Balance': f"{data['balance']:.6f}".rstrip('0').rstrip('.'),
                'USD Value': f"${data['usd_value']:.2f}",
                'GBP Value': f"£{data['gbp_value']:.2f}",
                '24h Change': f"{data['change_24h']:+.2f}%",
                'Portfolio %': f"{data['percentage']:.1f}%",
                'Trading Pairs': trading_pairs_str,
                'Free': f"{data['free']:.6f}".rstrip('0').rstrip('.'),
                'Locked': f"{data['locked']:.6f}".rstrip('0').rstrip('.') if data['locked'] > 0 else "0"
            })
        
        df = pd.DataFrame(portfolio_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Portfolio visualization
        col1, col2 = st.columns(2)
        
        with col1:
            # Allocation pie chart
            assets = list(portfolio.keys())
            values = [portfolio[asset]['usd_value'] for asset in assets]
            
            fig = px.pie(values=values, names=assets, title="Portfolio Allocation")
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 24h performance bar chart
            changes = [portfolio[asset]['change_24h'] for asset in assets]
            colors = ['green' if x > 0 else 'red' if x < 0 else 'gray' for x in changes]
            
            fig = px.bar(x=assets, y=changes, title="24h Performance by Asset",
                        color=changes, color_continuous_scale='RdYlGn')
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

def render_enhanced_performance_tab():
    """Render enhanced performance tab with multi-pair analysis"""
    st.header("📈 Advanced Multi-Pair Performance")
    
    df = load_multi_pair_data()
    
    if not df.empty:
        # Enhanced performance metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
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
            if 'symbol' in df.columns:
                unique_pairs = df['symbol'].nunique()
                st.metric("🔗 Pairs Traded", unique_pairs)
            else:
                st.metric("🔗 Pairs Traded", "N/A")
        
        with col5:
            if 'confidence' in df.columns:
                avg_confidence = df['confidence'].mean()
                st.metric("🎯 Avg Confidence", f"{avg_confidence:.2f}")
            else:
                st.metric("🎯 Avg Confidence", "N/A")
        
        # Multi-pair performance analysis
        if 'symbol' in df.columns and len(df) > 1:
            st.subheader("📊 Performance by Trading Pair")
            
            pair_performance = df.groupby('symbol').agg({
                'pnl_percent': ['count', 'sum', 'mean'],
                'confidence': 'mean' if 'confidence' in df.columns else lambda x: 0
            }).round(2)
            
            pair_performance.columns = ['Trades', 'Total P&L %', 'Avg P&L %', 'Avg Confidence']
            pair_performance = pair_performance.sort_values('Total P&L %', ascending=False)
            
            st.dataframe(pair_performance, use_container_width=True)
            
            # Performance visualization
            col1, col2 = st.columns(2)
            
            with col1:
                # Cumulative P&L over time
                if 'timestamp' in df.columns:
                    df_sorted = df.copy()
                    df_sorted['timestamp'] = pd.to_datetime(df_sorted['timestamp'])
                    df_sorted = df_sorted.sort_values('timestamp')
                    df_sorted['cumulative_pnl'] = df_sorted['pnl_percent'].cumsum()
                    
                    fig = px.line(df_sorted, x='timestamp', y='cumulative_pnl',
                                 title="Cumulative P&L Over Time", color='symbol' if 'symbol' in df.columns else None)
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # P&L distribution by symbol
                if len(pair_performance) > 1:
                    fig = px.bar(pair_performance, y=pair_performance.index, x='Total P&L %',
                               title="Total P&L by Trading Pair", orientation='h')
                    st.plotly_chart(fig, use_container_width=True)
        
        # Strategy performance analysis
        if 'confidence' in df.columns:
            st.subheader("🧠 Strategy Intelligence Analysis")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Confidence vs P&L correlation
                if len(df) > 5:
                    fig = px.scatter(df, x='confidence', y='pnl_percent',
                                   title="Confidence vs P&L Correlation",
                                   trendline="ols")
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Confidence distribution
                fig = px.histogram(df, x='confidence', bins=20,
                                 title="Trade Confidence Distribution")
                st.plotly_chart(fig, use_container_width=True)
            
            with col3:
                # P&L distribution
                fig = px.histogram(df, x='pnl_percent', bins=20,
                                 title="P&L Distribution")
                st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("📊 No multi-pair trading data available yet")
        st.markdown("""
        **Advanced Multi-Pair Features Ready:**
        - Multi-pair simultaneous trading
        - Cross-pair correlation analysis  
        - Dynamic risk adjustment per pair
        - Portfolio-wide risk management
        - ML-enhanced signal generation
        
        Start the multi-pair scanner to begin generating data!
        """)

def render_advanced_logs_tab():
    """Render advanced logs tab with multi-pair monitoring"""
    st.header("📡 Advanced Multi-Pair Monitoring")
    
    # Multi-bot status monitoring
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Single-pair bot status
        single_status = load_bot_status()
        status = single_status.get("status", "unknown")
        if status.lower() == "running":
            st.success("🟢 Single-Pair Bot: RUNNING")
        else:
            st.error("🔴 Single-Pair Bot: STOPPED")
    
    with col2:
        # Multi-pair scanner status
        scanner_status = "unknown"
        if os.path.exists("logs/scanner_status.json"):
            try:
                with open("logs/scanner_status.json", "r") as f:
                    scanner_data = json.load(f)
                    scanner_status = scanner_data.get("status", "unknown")
            except:
                pass
        
        if scanner_status.lower() == "running":
            st.success("🟢 Multi-Pair Scanner: RUNNING")
        else:
            st.warning("🟡 Multi-Pair Scanner: IDLE")
    
    with col3:
        # ML Strategy status
        ml_status = "unknown"
        if os.path.exists("logs/ml_strategy_status.json"):
            try:
                with open("logs/ml_strategy_status.json", "r") as f:
                    ml_data = json.load(f)
                    ml_status = ml_data.get("status", "unknown")
            except:
                pass
        
        if ml_status.lower() == "active":
            st.success("🟢 ML Strategy: ACTIVE")
        else:
            st.info("🔵 ML Strategy: TRADITIONAL")
    
    # Latest scan results
    scan_results = load_scan_results()
    if scan_results:
        st.subheader("🔍 Latest Scan Results")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🕐 Scan Time", 
                     scan_results.get('scan_timestamp', '').split('T')[1][:8] if 'scan_timestamp' in scan_results else 'Unknown')
        
        with col2:
            st.metric("📊 Pairs Scanned", scan_results.get('total_opportunities', 0))
        
        with col3:
            st.metric("🎯 Opportunities", scan_results.get('trading_opportunities', 0))
        
        with col4:
            scan_duration = scan_results.get('scan_duration', 0)
            st.metric("⚡ Scan Duration", f"{scan_duration:.1f}s" if scan_duration else "N/A")
    
    # Real-time log streaming with filtering
    st.subheader("📄 Real-Time Log Stream")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        log_filter = st.selectbox("🔍 Filter Logs:", 
                                 ["All", "Errors", "Warnings", "Signals", "Trading", "ML"])
    
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    with col3:
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=True)
    
    # Load and filter logs
    logs = []
    log_files = [
        "logs/console_output.log",
        "logs/scanner_output.log", 
        "logs/ml_strategy.log"
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    file_logs = f.readlines()[-20:]  # Last 20 lines per file
                    for line in file_logs:
                        logs.append(f"[{os.path.basename(log_file)}] {line.strip()}")
            except:
                continue
    
    # Apply filters
    filtered_logs = []
    for line in logs:
        if log_filter == "All":
            filtered_logs.append(line)
        elif log_filter == "Errors" and "ERROR" in line.upper():
            filtered_logs.append(f"🔴 {line}")
        elif log_filter == "Warnings" and "WARNING" in line.upper():
            filtered_logs.append(f"🟡 {line}")
        elif log_filter == "Signals" and any(x in line for x in ["BUY", "SELL", "SIGNAL"]):
            filtered_logs.append(f"🟢 {line}")
        elif log_filter == "Trading" and any(x in line for x in ["TRADE", "POSITION", "PROFIT"]):
            filtered_logs.append(f"💰 {line}")
        elif log_filter == "ML" and any(x in line for x in ["ML", "CONFIDENCE", "ENHANCED"]):
            filtered_logs.append(f"🧠 {line}")
    
    if filtered_logs:
        log_text = "\n".join(filtered_logs[-30:])  # Show last 30 filtered lines
        st.text_area("Filtered Logs", log_text, height=400)
    else:
        st.info(f"No logs found matching filter: {log_filter}")

def render_advanced_settings_tab():
    """Render advanced settings with multi-pair controls"""
    st.header("⚙️ Advanced Multi-Pair Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎛️ Multi-Bot Controls")
        
        # Single-pair bot control
        run_flag_exists = os.path.exists("run_bot.flag")
        
        if run_flag_exists:
            st.success("🟢 Single-Pair Bot: RUNNING")
            if st.button("🛑 Stop Single-Pair Bot", use_container_width=True):
                try:
                    os.remove("run_bot.flag")
                    st.success("✅ Single-pair bot stopped")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to stop: {e}")
        else:
            st.warning("🔴 Single-Pair Bot: STOPPED")
            if st.button("▶️ Start Single-Pair Bot", use_container_width=True):
                try:
                    with open("run_bot.flag", "w") as f:
                        f.write("run\n")
                    st.success("✅ Single-pair bot started")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to start: {e}")
        
        st.divider()
        
        # Multi-pair scanner control
        scanner_flag_exists = os.path.exists("scanner_bot.flag")
        
        if scanner_flag_exists:
            st.success("🟢 Multi-Pair Scanner: RUNNING")
            if st.button("🛑 Stop Multi-Pair Scanner", use_container_width=True):
                try:
                    os.remove("scanner_bot.flag")
                    st.success("✅ Multi-pair scanner stopped")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to stop: {e}")
        else:
            st.warning("🔴 Multi-Pair Scanner: STOPPED")
            if st.button("▶️ Start Multi-Pair Scanner", use_container_width=True):
                try:
                    with open("scanner_bot.flag", "w") as f:
                        f.write("run\n")
                    st.success("✅ Multi-pair scanner started")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to start: {e}")
        
        st.divider()
        
        # Advanced Risk Profile Selection
        st.subheader("🛡️ Advanced Risk Management")
        
        current_profile = st.session_state.selected_profile
        
        profile_options = list(ADVANCED_RISK_PROFILES.keys())
        selected_index = profile_options.index(current_profile) if current_profile in profile_options else 0
        
        new_profile = st.selectbox(
            "Select Advanced Trading Profile:",
            options=profile_options,
            format_func=lambda x: ADVANCED_RISK_PROFILES[x]['name'],
            index=selected_index,
            key="advanced_profile_selector"
        )
        
        if new_profile != current_profile:
            st.session_state.selected_profile = new_profile
            # Save profile selection
            try:
                with open("logs/selected_profile.json", "w") as f:
                    json.dump({
                        "profile": new_profile, 
                        "timestamp": datetime.now().isoformat(),
                        "features": ADVANCED_RISK_PROFILES[new_profile].get('features', [])
                    }, f)
                st.success(f"✅ Profile: {ADVANCED_RISK_PROFILES[new_profile]['name']}")
            except Exception as e:
                st.error(f"❌ Failed to save: {e}")
        
        # Display profile details
        profile_info = ADVANCED_RISK_PROFILES[new_profile]
        st.info(f"**{profile_info['name']}**: {profile_info['description']}")
        
        if new_profile != "AUTO" and 'take_profit' in profile_info:
            st.write(f"**Take Profit:** {profile_info['take_profit']}%")
            st.write(f"**Stop Loss:** {profile_info['stop_loss']}%")
            st.write(f"**Max Hold:** {profile_info['max_hold_hours']} hours")
        
        if 'features' in profile_info:
            st.write("**Features:**")
            for feature in profile_info['features']:
                st.write(f"• {feature}")
    
    with col2:
        st.subheader("📊 Advanced Configuration")
        
        # Multi-pair configuration
        config = {
            "Trading Mode": "🧪 TESTNET" if os.getenv("USE_TESTNET", "True").lower() == "true" else "💰 LIVE",
            "Scan Mode": st.session_state.scan_mode,
            "Min Confidence": os.getenv("MIN_CONFIDENCE", "0.65"),
            "Max Positions": os.getenv("MAX_POSITIONS", "3"),
            "Risk per Trade": f"{float(os.getenv('RISK_PERCENTAGE', '0.015'))*100:.1f}%",
            "Scan Interval": f"{os.getenv('SCAN_INTERVAL', '300')} seconds",
            "ML Enhancement": "Enabled" if os.getenv("USE_ML_ENHANCEMENT", "True").lower() == "true" else "Disabled"
        }
        
        for key, value in config.items():
            st.write(f"**{key}:** {value}")
        
        st.divider()
        
        # System status
        st.subheader("📁 Advanced System Status")
        
        files_status = {
            "🏃 Single Bot": "✅" if os.path.exists("run_bot.flag") else "❌",
            "🔍 Scanner Bot": "✅" if os.path.exists("scanner_bot.flag") else "❌",
            "📊 Bot Status": "✅" if os.path.exists("logs/bot_status.json") else "❌",
            "🔍 Scan Results": "✅" if any(os.path.exists(f"logs/{f}") for f in ["scan_results.json", "selected_scan_results.json"]) else "❌",
            "🧠 ML Model": "✅" if os.path.exists("models/trading_model.pkl") else "❌",
            "💹 Multi-Pair Data": "✅" if os.path.exists("logs/multi_pair_trades.json") else "❌",
            "⚙️ Environment": "✅" if os.path.exists(".env") else "❌"
        }
        
        for item, status in files_status.items():
            st.write(f"{item}: {status}")
        
        st.divider()
        
        # Advanced data export
        st.subheader("📥 Advanced Data Export")
        
        # Export all logs
        if st.button("📄 Export All Logs", use_container_width=True):
            all_logs = []
            log_files = ["logs/console_output.log", "logs/scanner_output.log", "logs/ml_strategy.log"]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    with open(log_file, "r", encoding="utf-8") as f:
                        all_logs.extend([f"=== {log_file} ==="] + f.readlines() + ["\n"])
            
            if all_logs:
                log_data = "".join(all_logs)
                st.download_button(
                    "📥 Download Complete Logs",
                    data=log_data,
                    file_name=f"complete_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
        
        # Export scan results
        scan_results = load_scan_results()
        if scan_results:
            if st.button("🔍 Export Scan Results", use_container_width=True):
                scan_data = json.dumps(scan_results, indent=2)
                st.download_button(
                    "📥 Download Scan Results",
                    data=scan_data,
                    file_name=f"scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        # Export performance data
        df = load_multi_pair_data()
        if not df.empty:
            if st.button("📊 Export Performance Data", use_container_width=True):
                csv_data = df.to_csv(index=False)
                st.download_button(
                    "📥 Download Performance Data",
                    data=csv_data,
                    file_name=f"performance_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

def main():
    """Main advanced dashboard function"""
    
    # PIN Protection
    if not st.session_state.authenticated:
        st.title("🔐 Advanced Trading Dashboard Access")
        st.caption("Enter your PIN to access the institutional-grade trading platform")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            user_pin = st.text_input("Enter PIN:", type="password", placeholder="Enter 4-digit PIN")
            
            if st.button("🔓 Access Advanced Dashboard", use_container_width=True):
                if user_pin == PIN_REQUIRED:
                    st.session_state.authenticated = True
                    st.success("✅ Access granted to advanced features!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Incorrect PIN. Please try again.")
        
        st.info("💡 Default PIN is **1234** (configurable in .env file)")
        
        # Feature preview
        st.markdown("### 🚀 Advanced Features Available")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **🔍 Multi-Pair Scanner**
            - Scan 100+ crypto pairs
            - ML-enhanced signals
            - Real-time opportunities
            """)
        
        with col2:
            st.markdown("""
            **🧠 Advanced Analytics**
            - Cross-pair correlation
            - Dynamic risk management
            - Performance attribution
            """)
        
        with col3:
            st.markdown("""
            **⚡ Professional Tools**
            - Institutional-grade risk profiles
            - Multi-bot orchestration
            - Advanced monitoring
            """)
        
        return
    
    # Main Advanced Dashboard
    st.title("🚀 Advanced Multi-Pair Trading Platform")
    st.caption("Institutional-grade cryptocurrency trading with ML-enhanced multi-pair analysis")
    
    # System status header
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        bot_status = load_bot_status().get("status", "unknown")
        status_color = "🟢" if bot_status == "running" else "🔴"
        st.metric(f"{status_color} Single-Pair", bot_status.upper())
    
    with col2:
        scanner_status = "idle"
        if os.path.exists("scanner_bot.flag"):
            scanner_status = "running"
        scanner_color = "🟢" if scanner_status == "running" else "🟡"
        st.metric(f"{scanner_color} Multi-Pair", scanner_status.upper())
    
    with col3:
        ml_status = "traditional"
        if os.getenv("USE_ML_ENHANCEMENT", "True").lower() == "true":
            ml_status = "enhanced"
        ml_color = "🧠" if ml_status == "enhanced" else "📊"
        st.metric(f"{ml_color} Strategy", ml_status.upper())
    
    with col4:
        current_profile = st.session_state.selected_profile
        profile_name = ADVANCED_RISK_PROFILES[current_profile]['name']
        st.metric("🛡️ Risk Profile", profile_name)
    
    with col5:
        gbp_rate = get_gbp_exchange_rate()
        st.metric("💱 USD/GBP", f"{gbp_rate:.4f}")
    
    # Advanced tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Multi-Pair Scanner",
        "💼 Portfolio & Pairs",
        "📈 Advanced Performance",
        "📡 System Monitoring",
        "⚙️ Advanced Settings"
    ])
    
    with tab1:
        render_multi_pair_scanner_tab()
    
    with tab2:
        render_portfolio_tab()
    
    with tab3:
        render_enhanced_performance_tab()
    
    with tab4:
        render_advanced_logs_tab()
    
    with tab5:
        render_advanced_settings_tab()
    
    # Advanced footer
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.caption("🔄 Auto-refresh: Every 30 seconds")
    
    with col2:
        st.caption(f"⏰ Last Updated: {datetime.now().strftime('%H:%M:%S')}")
    
    with col3:
        scan_results = load_scan_results()
        last_scan = "Never"
        if scan_results and 'scan_timestamp' in scan_results:
            last_scan = scan_results['scan_timestamp'].split('T')[1][:8]
        st.caption(f"🔍 Last Scan: {last_scan}")
    
    with col4:
        use_testnet = os.getenv("USE_TESTNET", "True").lower() == "true"
        mode = "🧪 TESTNET" if use_testnet else "💰 LIVE"
        st.caption(f"Mode: {mode}")
    
    # Auto-refresh
    time.sleep(2)
    st.rerun()

if __name__ == "__main__":
    main()