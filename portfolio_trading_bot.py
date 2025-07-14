import os
import time
import streamlit as st
from datetime import datetime
import pandas as pd
import json
import requests
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
MIN_BALANCE_USD = float(os.getenv("MIN_BALANCE_USD", "10"))

class MultiCoinPortfolioBot:
    def __init__(self):
        self.client = None
        self.portfolio = {}
        self.opportunities = []
        self.trades = []
        self.usd_to_gbp_rate = 0.79  # Default fallback rate
        self.initialize_binance()
        self.update_gbp_rate()
        
    def update_gbp_rate(self):
        """Get live USD to GBP exchange rate"""
        try:
            # Try multiple free forex APIs
            apis = [
                "https://api.exchangerate-api.com/v4/latest/USD",
                "https://api.fxratesapi.com/latest?base=USD",
                "https://open.er-api.com/v6/latest/USD"
            ]
            
            for api_url in apis:
                try:
                    response = requests.get(api_url, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if 'rates' in data and 'GBP' in data['rates']:
                            self.usd_to_gbp_rate = data['rates']['GBP']
                            return True
                except:
                    continue
            
            # Fallback: Try Binance GBPUSDT if available
            if self.client:
                try:
                    ticker = self.client.get_symbol_ticker(symbol='GBPUSDT')
                    gbp_usd_rate = float(ticker['price'])
                    self.usd_to_gbp_rate = 1 / gbp_usd_rate  # Convert to USD/GBP
                    return True
                except:
                    pass
                    
        except Exception as e:
            print(f"Exchange rate API error: {e}")
        
        return False
    
    def get_portfolio_value_gbp(self, usd_value):
        """Convert USD value to GBP"""
        gbp_value = usd_value * self.usd_to_gbp_rate
        return gbp_value
        
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
            # Return demo portfolio with more realistic values
            return {
                'BTC': {'balance': 0.15234, 'usd_value': 9890.45, 'symbol': 'BTCUSDT', 'price_usd': 64950.0},
                'SOL': {'balance': 45.67, 'usd_value': 2876.32, 'symbol': 'SOLUSDT', 'price_usd': 62.98},
                'XRP': {'balance': 1250.0, 'usd_value': 743.75, 'symbol': 'XRPUSDT', 'price_usd': 0.595},
                'ETH': {'balance': 1.8945, 'usd_value': 4567.89, 'symbol': 'ETHUSDT', 'price_usd': 2410.50},
                'ADA': {'balance': 2890.5, 'usd_value': 1234.56, 'symbol': 'ADAUSDT', 'price_usd': 0.427}
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
                
                if total_balance > 0 and asset != 'USDT':
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
                signal = "SELL"
                confidence = 0.75
            elif current_price <= recent_low * 1.02 and volume_ratio > 2.0:
                signal = "BUY"
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
            future_to_coin = {
                executor.submit(self.analyze_coin_opportunity, coin_data): asset
                for asset, coin_data in portfolio.items()
            }
            
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
            x['signal'] != 'HOLD',
            x['confidence'],
            abs(x['change_2h'])
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
                    'suggested_amount': opp['usd_value'] * 0.1 if opp['signal'] == 'SELL' else 100
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
    
    # Update exchange rate periodically (every 5 minutes)
    if 'last_fx_update' not in st.session_state or \
       (datetime.now() - st.session_state.last_fx_update).total_seconds() > 300:
        bot.update_gbp_rate()
        st.session_state.last_fx_update = datetime.now()
    
    # Status bar
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if bot.client:
            st.metric("🟢 Connection", "Live", "Binance API")
        else:
            st.metric("🟡 Connection", "Demo", "Simulation Mode")
    
    with col2:
        st.metric("💷 USD/GBP", f"{bot.usd_to_gbp_rate:.4f}", "Live Rate")
    
    with col3:
        st.metric("🎯 Strategy", "Multi-Coin", "Portfolio Scan")
    
    with col4:
        st.metric("⏰ Time", datetime.now().strftime("%H:%M:%S"), "Live")
    
    # Portfolio overview with GBP conversion
    st.subheader("💼 Your Cryptocurrency Portfolio")
    
    portfolio = bot.get_portfolio_holdings()
    
    if portfolio:
        # Calculate total values
        total_usd = sum(coin['usd_value'] for coin in portfolio.values())
        total_gbp = bot.get_portfolio_value_gbp(total_usd)
        coin_count = len(portfolio)
        
        # Portfolio summary with prominent GBP display
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💷 Total Value (GBP)", f"£{total_gbp:,.2f}", 
                     f"${total_usd:,.2f} USD")
        
        with col2:
            st.metric("💰 USD Value", f"${total_usd:,.2f}", "USD")
        
        with col3:
            st.metric("🪙 Assets", coin_count, "Cryptocurrencies")
        
        with col4:
            if portfolio:
                largest_holding = max(portfolio.values(), key=lambda x: x['usd_value'])
                largest_asset = max(portfolio.keys(), key=lambda k: portfolio[k]['usd_value'])
                st.metric("🥇 Largest", f"{largest_holding.get('balance', 0):.4f}", f"{largest_asset}")
        
        # Enhanced portfolio breakdown with GBP values
        portfolio_data = []
        for asset, data in portfolio.items():
            gbp_value = bot.get_portfolio_value_gbp(data['usd_value'])
            portfolio_data.append({
                'Asset': asset,
                'Balance': f"{data['balance']:.6f}",
                'Price (USD)': f"${data.get('price_usd', 0):.4f}",
                'USD Value': f"${data['usd_value']:.2f}",
                'GBP Value': f"£{gbp_value:.2f}",
                'Portfolio %': f"{(data['usd_value']/total_usd)*100:.1f}%"
            })
        
        portfolio_df = pd.DataFrame(portfolio_data)
        st.dataframe(portfolio_df, use_container_width=True)
        
        # Portfolio allocation chart
        if len(portfolio) > 1:
            chart_data = pd.DataFrame([
                {'Asset': asset, 'Value': data['usd_value']}
                for asset, data in portfolio.items()
            ])
            st.subheader("📊 Portfolio Allocation")
            st.bar_chart(chart_data.set_index('Asset'))
    
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
            
            # Display opportunities with GBP values
            for i, opp in enumerate(active_opps[:10]):
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        signal_color = "🟢" if opp['signal'] == 'BUY' else "🔴"
                        gbp_value = bot.get_portfolio_value_gbp(opp['usd_value'])
                        st.metric(f"{signal_color} {opp['asset']}", 
                                 f"${opp['current_price']:.4f}",
                                 f"{opp['change_2h']:+.1f}%")
                    
                    with col2:
                        st.metric("Signal", opp['signal'], 
                                 f"Confidence: {opp['confidence']:.1%}")
                    
                    with col3:
                        st.metric("Volume", f"{opp['volume_ratio']:.1f}x", "vs Average")
                    
                    with col4:
                        rsi_status = "Overbought" if opp['rsi'] > 70 else "Oversold" if opp['rsi'] < 30 else "Neutral"
                        st.metric("RSI", f"{opp['rsi']:.0f}", rsi_status)
                    
                    with col5:
                        st.metric("Holdings", f"£{gbp_value:.0f}", 
                                 f"{opp['balance']:.4f} {opp['asset']}")
                
                st.divider()
        
        else:
            st.info("🕐 No active signals found. All holdings are in HOLD status.")
        
        # Portfolio rebalancing suggestions with GBP amounts
        suggestions = bot.execute_portfolio_rebalancing(opportunities)
        
        if suggestions:
            st.subheader("⚖️ Portfolio Rebalancing Suggestions")
            
            for suggestion in suggestions:
                action_color = "🟢" if suggestion['action'] == 'BUY' else "🔴"
                gbp_current = bot.get_portfolio_value_gbp(suggestion['current_value'])
                gbp_suggested = bot.get_portfolio_value_gbp(suggestion['suggested_amount'])
                
                st.write(f"{action_color} **{suggestion['action']} {suggestion['asset']}**: {suggestion['reason']}")
                st.write(f"   Current holding: £{gbp_current:.2f} (${suggestion['current_value']:.2f})")
                st.write(f"   Suggested amount: £{gbp_suggested:.2f} (${suggestion['suggested_amount']:.2f})")
    
    # Exchange rate info
    with st.expander("💷 Currency Information"):
        st.info(f"""
        **Current Exchange Rate:** 1 USD = {bot.usd_to_gbp_rate:.4f} GBP
        
        **Rate Source:** Live forex API (updates every 5 minutes)
        
        **Portfolio Display:**
        - All values shown in both GBP and USD
        - GBP is primary display currency
        - Exchange rates updated automatically
        """)
    
    # Configuration and settings
    with st.expander("⚙️ Bot Configuration"):
        st.json({
            "Portfolio Scanning": "All holdings > $10 USD value",
            "Currency Display": "GBP primary, USD secondary",
            "Exchange Rate": f"1 USD = {bot.usd_to_gbp_rate:.4f} GBP",
            "Supported Pairs": "USDT, BUSD, USDC trading pairs",
            "Signal Threshold": "±5% price movement in 2 hours",
            "Volume Confirmation": "1.5x average volume required",
            "RSI Filters": "Avoid extreme overbought/oversold",
            "Support/Resistance": "10-period high/low analysis",
            "Concurrent Analysis": "Up to 5 coins simultaneously",
            "Minimum Balance": f"${MIN_BALANCE_USD} USD equivalent",
            "Rate Updates": "Every 5 minutes"
        })
    
    # Auto-refresh every 30 seconds
    time.sleep(1)
    st.rerun()

if __name__ == "__main__":
    main()
