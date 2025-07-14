import os
import time
import streamlit as st
from datetime import datetime
import pandas as pd
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# Check if we have Binance library
try:
    from binance.client import Client
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False

# Environment variables
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
USE_TESTNET = os.getenv("USE_TESTNET", "True").lower() == "true"
MIN_BALANCE_USD = float(os.getenv("MIN_BALANCE_USD", "10"))  # Minimum $10 to consider trading

class MultiCoinPortfolioBot:
    def __init__(self):
        self.client = None
        self.portfolio = {}
        self.opportunities = []
        self.trades = []
        self.all_symbols = []
        self.initialize_binance()
        
    def initialize_binance(self):
        """Initialize Binance connection"""
        if not BINANCE_AVAILABLE or not API_KEY or not API_SECRET:
            return False
            
        try:
            self.client = Client(API_KEY, API_SECRET)
            if USE_TESTNET:
                self.client.API_URL = "https://testnet.binance.vision/api"
            
            self.client.get_server_time()
            return True
        except Exception as e:
            st.error(f"❌ Binance connection failed: {e}")
            return False
    
    def get_portfolio_holdings(self):
        """Get all coins in portfolio with significant balances"""
        if not self.client:
            # Return demo portfolio
            return {
                'BTC': {'balance': 0.15234, 'usd_value': 9890.45, 'symbol': 'BTCUSDT'},
                'SOL': {'balance': 45.67, 'usd_value': 2876.32, 'symbol': 'SOLUSDT'},
                'XRP': {'balance': 1250.0, 'usd_value': 743.75, 'symbol': 'XRPUSDT'},
                'ETH': {'balance': 1.8945, 'usd_value': 4567.89, 'symbol': 'ETHUSDT'},
                'ADA': {'balance': 2890.5, 'usd_value': 1234.56, 'symbol': 'ADAUSDT'}
            }
        
        try:
            account = self.client.get_account()
            portfolio = {}
            
            # Get all tickers for price calculation
            all_tickers = {t['symbol']: float(t['price']) for t in self.client.get_all_tickers()}
            
            for balance in account['balances']:
                asset = balance['asset']
                free_balance = float(balance['free'])
                locked_balance = float(balance['locked'])
                total_balance = free_balance + locked_balance
                
                if total_balance > 0 and asset != 'USDT':  # Skip USDT, focus on crypto
                    # Try different trading pairs to get USD value
                    symbol_usdt = f"{asset}USDT"
                    symbol_busd = f"{asset}BUSD"
                    symbol_usdc = f"{asset}USDC"
                    
                    price_usd = 0
                    trading_symbol = None
                    
                    for symbol in [symbol_usdt, symbol_busd, symbol_usdc]:
                        if symbol in all_tickers:
                            price_usd = all_tickers[symbol]
                            trading_symbol = symbol
                            break
                    
                    if price_usd > 0:
                        usd_value = total_balance * price_usd
                        
                        # Only include if value is above minimum threshold
                        if usd_value >= MIN_BALANCE_USD:
                            portfolio[asset] = {
                                'balance': total_balance,
                                'free': free_balance,
                                'locked': locked_balance,
                                'price_usd': price_usd,
                                'usd_value': usd_value,
                                'symbol': trading_symbol
                            }
            
            return portfolio
            
        except Exception as e:
            st.error(f"❌ Error fetching portfolio: {e}")
            return {}
    
    def analyze_coin_opportunity(self, coin_data):
        """Analyze trading opportunity for a specific coin"""
        symbol = coin_data['symbol']
        asset = symbol.replace('USDT', '').replace('BUSD', '').replace('USDC', '')
        
        try:
            if not self.client:
                # Simulate analysis
                import random
                signals = ["BUY", "SELL", "HOLD", "HOLD", "HOLD"]
                signal = random.choice(signals)
                confidence = random.uniform(0.6, 0.95)
                change_2h = random.uniform(-8, 8)
                volume_ratio = random.uniform(0.8, 3.0)
                rsi = random.uniform(20, 80)
                
                return {
                    'asset': asset,
                    'symbol': symbol,
                    'signal': signal,
                    'confidence': confidence,
                    'current_price': coin_data['price_usd'],
                    'change_2h': change_2h,
                    'volume_ratio': volume_ratio,
                    'rsi': rsi,
                    'usd_value': coin_data['usd_value'],
                    'balance': coin_data['balance'],
                    'data_source': 'Simulated'
                }
            
            # Get real market data
            klines = self.client.get_klines(
                symbol=symbol,
                interval=Client.KLINE_INTERVAL_1MINUTE,
                limit=120
            )
            
            if len(klines) < 120:
                return None
            
            # Extract data for analysis
            closes = [float(k[4]) for k in klines]
            volumes = [float(k[5]) for k in klines]
            highs = [float(k[2]) for k in klines]
            lows = [float(k[3]) for k in klines]
            
            # Calculate indicators
            current_price = closes[-1]
            start_price = closes[0]
            change_2h = ((current_price - start_price) / start_price) * 100
            
            # Volume analysis
            avg_volume_20 = sum(volumes[-20:]) / 20
            current_volume = volumes[-1]
            volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1
            
            # RSI calculation
            rsi = self.calculate_rsi(closes)
            
            # Support/Resistance levels
            recent_high = max(highs[-10:])
            recent_low = min(lows[-10:])
            
            # Signal generation
            signal = "HOLD"
            confidence = 0.5
            
            # Enhanced signal logic for any coin
            if change_2h >= 5.0 and volume_ratio > 1.5 and rsi < 80:
                signal = "BUY"
                confidence = min(0.95, 0.7 + (volume_ratio - 1.5) * 0.1 + (change_2h - 5) * 0.02)
            elif change_2h <= -5.0 and volume_ratio > 1.5 and rsi > 20:
                signal = "SELL"
                confidence = min(0.95, 0.7 + (volume_ratio - 1.5) * 0.1 + abs(change_2h + 5) * 0.02)
            elif current_price >= recent_high * 0.98 and volume_ratio > 2.0:
                signal = "SELL"  # Near resistance with high volume
                confidence = 0.75
            elif current_price <= recent_low * 1.02 and volume_ratio > 2.0:
                signal = "BUY"   # Near support with high volume
                confidence = 0.75
            
            return {
                'asset': asset,
                'symbol': symbol,
                'signal': signal,
                'confidence': confidence,
                'current_price': current_price,
                'change_2h': change_2h,
                'volume_ratio': volume_ratio,
                'rsi': rsi,
                'support': recent_low,
                'resistance': recent_high,
                'usd_value': coin_data['usd_value'],
                'balance': coin_data['balance'],
                'data_source': 'Binance Live'
            }
            
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            return None
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d for d in deltas[-period:] if d > 0]
        losses = [-d for d in deltas[-period:] if d < 0]
        
        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def scan_all_holdings(self):
        """Scan all portfolio holdings for opportunities"""
        portfolio = self.get_portfolio_holdings()
        opportunities = []
        
        if not portfolio:
            return []
        
        # Use ThreadPoolExecutor for concurrent analysis
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit analysis tasks for all holdings
            future_to_coin = {
                executor.submit(self.analyze_coin_opportunity, coin_data): asset
                for asset, coin_data in portfolio.items()
            }
            
            # Collect results
            for future in as_completed(future_to_coin):
                asset = future_to_coin[future]
                try:
                    result = future.result()
                    if result:
                        opportunities.append(result)
                except Exception as e:
                    print(f"Error processing {asset}: {e}")
        
        # Sort by confidence and signal strength
        opportunities.sort(key=lambda x: (
            x['signal'] != 'HOLD',  # Active signals first
            x['confidence'],
            abs(x['change_2h'])     # Bigger moves
        ), reverse=True)
        
        return opportunities
    
    def execute_portfolio_rebalancing(self, opportunities):
        """Suggest portfolio rebalancing based on opportunities"""
        suggestions = []
        
        for opp in opportunities:
            if opp['signal'] != 'HOLD' and opp['confidence'] > 0.75:
                suggestion = {
                    'action': opp['signal'],
                    'asset': opp['asset'],
                    'reason': f"{opp['change_2h']:+.1f}% move, {opp['confidence']:.1%} confidence",
                    'current_value': opp['usd_value'],
                    'suggested_amount': opp['usd_value'] * 0.1 if opp['signal'] == 'SELL' else 100  # 10% of holdings or $100 buy
                }
                suggestions.append(suggestion)
        
        return suggestions

def main():
    st.set_page_config(page_title="🎯 Multi-Coin Portfolio Bot", layout="wide")
    
    st.title("🎯 Multi-Coin Portfolio Trading Bot")
    st.caption("Scan ALL your cryptocurrency holdings for trading opportunities")
    
    # Initialize bot
    if 'portfolio_bot' not in st.session_state:
        st.session_state.portfolio_bot = MultiCoinPortfolioBot()
    
    bot = st.session_state.portfolio_bot
    
    # Status bar
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if bot.client:
            st.metric("🟢 Connection", "Live", "Binance API")
        else:
            st.metric("🟡 Connection", "Demo", "Simulation Mode")
    
    with col2:
        st.metric("☁️ Platform", "Railway", "24/7 Cloud")
    
    with col3:
        st.metric("🎯 Strategy", "Multi-Coin", "Portfolio Scan")
    
    with col4:
        st.metric("⏰ Time", datetime.now().strftime("%H:%M:%S"), "Live")
    
    # Portfolio overview
    st.subheader("💼 Your Cryptocurrency Portfolio")
    
    portfolio = bot.get_portfolio_holdings()
    
    if portfolio:
        # Portfolio summary
        total_value = sum(coin['usd_value'] for coin in portfolio.values())
        coin_count = len(portfolio)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Total Value", f"${total_value:,.2f}", "USD")
        with col2:
            st.metric("🪙 Assets", coin_count, "Cryptocurrencies")
        with col3:
            largest_holding = max(portfolio.values(), key=lambda x: x['usd_value'])
            st.metric("🥇 Largest", f"{largest_holding.get('balance', 0):.4f}", 
                     f"{max(portfolio.keys(), key=lambda k: portfolio[k]['usd_value'])}")
        
        # Portfolio breakdown
        portfolio_df = pd.DataFrame([
            {
                'Asset': asset,
                'Balance': f"{data['balance']:.6f}",
                'USD Value': f"${data['usd_value']:.2f}",
                'Price': f"${data.get('price_usd', 0):.4f}",
                'Percentage': f"{(data['usd_value']/total_value)*100:.1f}%"
            }
            for asset, data in portfolio.items()
        ])
        
        st.dataframe(portfolio_df, use_container_width=True)
    
    # Opportunity scanner
    st.subheader("🔍 Live Opportunity Scanner")
    
    if st.button("🚀 Scan All Holdings for Opportunities") or 'last_scan' not in st.session_state:
        with st.spinner("Analyzing all cryptocurrency holdings..."):
            opportunities = bot.scan_all_holdings()
            st.session_state.opportunities = opportunities
            st.session_state.last_scan = datetime.now()
    
    # Display opportunities
    if 'opportunities' in st.session_state and st.session_state.opportunities:
        opportunities = st.session_state.opportunities
        
        st.subheader("🎯 Trading Opportunities Found")
        
        # Filter active opportunities
        active_opps = [opp for opp in opportunities if opp['signal'] != 'HOLD']
        
        if active_opps:
            st.success(f"Found {len(active_opps)} active trading opportunities!")
            
            # Display opportunities
            for i, opp in enumerate(active_opps[:10]):  # Top 10
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        signal_color = "🟢" if opp['signal'] == 'BUY' else "🔴"
                        st.metric(f"{signal_color} {opp['asset']}", 
                                 f"${opp['current_price']:.4f}",
                                 f"{opp['change_2h']:+.1f}%")
                    
                    with col2:
                        st.metric("Signal", opp['signal'], 
                                 f"Confidence: {opp['confidence']:.1%}")
                    
                    with col3:
                        st.metric("Volume", f"{opp['volume_ratio']:.1f}x", "vs Average")
                    
                    with col4:
                        st.metric("RSI", f"{opp['rsi']:.0f}", 
                                 "Overbought" if opp['rsi'] > 70 else "Oversold" if opp['rsi'] < 30 else "Neutral")
                    
                    with col5:
                        st.metric("Portfolio", f"${opp['usd_value']:.0f}", 
                                 f"{opp['balance']:.4f} {opp['asset']}")
                
                st.divider()
        
        else:
            st.info("🕐 No active signals found. All holdings are in HOLD status.")
        
        # Portfolio rebalancing suggestions
        suggestions = bot.execute_portfolio_rebalancing(opportunities)
        
        if suggestions:
            st.subheader("⚖️ Portfolio Rebalancing Suggestions")
            
            for suggestion in suggestions:
                action_color = "🟢" if suggestion['action'] == 'BUY' else "🔴"
                st.write(f"{action_color} **{suggestion['action']} {suggestion['asset']}**: {suggestion['reason']}")
                st.write(f"   Current holding: ${suggestion['current_value']:.2f}")
                st.write(f"   Suggested amount: ${suggestion['suggested_amount']:.2f}")
    
    # Configuration and settings
    with st.expander("⚙️ Bot Configuration"):
        st.json({
            "Portfolio Scanning": "All holdings > $10 USD value",
            "Supported Pairs": "USDT, BUSD, USDC trading pairs",
            "Signal Threshold": "±5% price movement in 2 hours",
            "Volume Confirmation": "1.5x average volume required",
            "RSI Filters": "Avoid extreme overbought/oversold",
            "Support/Resistance": "10-period high/low analysis",
            "Concurrent Analysis": "Up to 5 coins simultaneously",
            "Minimum Balance": f"${MIN_BALANCE_USD} USD equivalent",
            "Rebalancing": "10% of holdings for SELL, $100 for BUY"
        })
    
    # Setup guide
    if not bot.client:
        st.subheader("🔧 Setup for Live Portfolio Scanning")
        
        with st.expander("Enable Multi-Coin Analysis"):
            st.info("""
            **Add these to Railway Environment Variables:**
            """)
            
            st.code("""
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_secret
USE_TESTNET=True
MIN_BALANCE_USD=10
            """)
            
            st.warning("""
            **Portfolio Requirements:**
            - Bot scans ALL coins in your wallet
            - Minimum $10 USD value to be included
            - Supports USDT, BUSD, USDC trading pairs
            - Works with any cryptocurrency (BTC, ETH, SOL, XRP, ADA, etc.)
            """)
    
    # Auto-refresh every 30 seconds for portfolio scanning
    time.sleep(1)
    st.rerun()

if __name__ == "__main__":
    main()
