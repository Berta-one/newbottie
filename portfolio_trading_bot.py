import os
from dotenv import load_dotenv
load_dotenv()
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
        """Get all coins in portfolio with significant balances using Binance API only"""
        if not self.client:
            st.error("❌ Binance API client not initialized. Check your API keys and network connection.")
            return {}
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
    def render_portfolio_summary(portfolio, usd_to_gbp, show_table=True):
        if not portfolio:
            st.warning("No portfolio data available. Check your Binance API keys and account.")
            return
        total_usd = sum(coin['usd_value'] for coin in portfolio.values())
        total_gbp = total_usd * usd_to_gbp
        asset_count = len(portfolio)
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Value (USD)", f"${total_usd:,.2f}")
        col2.metric("Total Value (GBP)", f"£{total_gbp:,.2f}")
        col3.metric("Assets", asset_count)
        if show_table:
            st.markdown("### 🪙 Asset Breakdown")
            portfolio_data = []
            for asset, data in portfolio.items():
                gbp_value = data['usd_value'] * usd_to_gbp
                pct = (data['usd_value'] / total_usd) * 100 if total_usd else 0
                portfolio_data.append({
                    'Asset': asset,
                    'Free': f"{data.get('free', data['balance']):.4f}",
                    'Locked': f"{data.get('locked', 0):.4f}",
                    'USD Value': f"${data['usd_value']:.2f}",
                    'GBP Value': f"£{gbp_value:.2f}",
                    '% of Portfolio': f"{pct:.2f}%"
                })
            df = pd.DataFrame(portfolio_data)
            st.dataframe(df, use_container_width=True)
        st.markdown("### 📊 Portfolio Allocation")
        chart_data = pd.DataFrame({
            'Asset': [a for a in portfolio.keys()],
            'USD Value': [d['usd_value'] for d in portfolio.values()]
        })
        st.bar_chart(chart_data.set_index('Asset'))
        return total_usd, total_gbp, asset_count

    def render_pnl_chart():
        pnl_file = "logs/single_pair_performance.json"
        if os.path.exists(pnl_file):
            try:
                dfp = pd.read_json(pnl_file, lines=True)
                dfp['timestamp'] = pd.to_datetime(dfp['timestamp'])
                dfp = dfp.sort_values('timestamp')
                if not dfp.empty:
                    dfp['cumulative_pnl'] = dfp['pnl_percent'].cumsum()
                    st.markdown("### 📈 Portfolio PnL (Cumulative)")
                    import plotly.express as px
                    fig = px.line(dfp, x='timestamp', y='cumulative_pnl', title="Cumulative PnL (%)")
                    st.plotly_chart(fig, use_container_width=True)
                    st.metric("Total PnL", f"{dfp['pnl_percent'].sum():+.2f}%")
            except Exception as e:
                st.warning(f"Could not load PnL data: {e}")
        else:
            st.info("No PnL data available yet.")

    import threading
    from streamlit.runtime.scriptrunner import add_script_run_ctx

    # Shared state for bot running and thread
    if 'bot_running' not in st.session_state:
        st.session_state['bot_running'] = False
    if 'bot_thread' not in st.session_state:
        st.session_state['bot_thread'] = None
    if 'stop_bot' not in st.session_state:
        st.session_state['stop_bot'] = False

    def run_bot_continuous():
        st.session_state['bot_running'] = True
        bot = MultiCoinPortfolioBot()
        while not st.session_state.get('stop_bot', False):
            opportunities = bot.scan_all_holdings()
            st.session_state['last_opportunities'] = opportunities
            time.sleep(5)  # Scan every 5 seconds for near real-time updates
        st.session_state['bot_running'] = False

    st.sidebar.markdown("---")
    start_disabled = st.session_state.get('bot_running', False)
    stop_disabled = not st.session_state.get('bot_running', False)
    if st.sidebar.button("▶️ Start Bot", disabled=start_disabled):
        st.session_state['stop_bot'] = False
        bot_thread = threading.Thread(target=run_bot_continuous)
        add_script_run_ctx(bot_thread)
        bot_thread.start()
        st.session_state['bot_thread'] = bot_thread
        st.sidebar.success("Bot started!")
    if st.sidebar.button("⏹️ Stop Bot", disabled=stop_disabled):
        st.session_state['stop_bot'] = True
        st.sidebar.info("Stopping bot...")
    if st.session_state.get('bot_running', False):
        st.sidebar.info("Bot is running continuously...")
    elif 'last_opportunities' in st.session_state:
        st.sidebar.success("Bot stopped. Results available.")

    try:
        st.set_page_config(page_title="🎯 Multi-Coin Portfolio Bot", layout="wide")
        st.title("🎯 Multi-Coin Portfolio Trading Bot")
        st.caption("Scan ALL your cryptocurrency holdings for trading opportunities")

        selected_tab = st.sidebar.radio(
            "Select Dashboard Tab",
            ["Portfolio Overview", "Performance", "Logs", "Settings", "Strategy", "Health"]
        )

        if selected_tab == "Portfolio Overview":
            st.subheader("💼 Portfolio Overview")
            bot = MultiCoinPortfolioBot()
            portfolio = bot.get_portfolio_holdings()
            usd_to_gbp = bot.usd_to_gbp_rate

            # Show current mode and strategy
            mode = st.session_state.get('strategy_mode', 'Automatic')
            strategy = st.session_state.get('selected_strategy', 'ML Enhanced')
            st.markdown(f"**Mode:** `{mode}`  |  **Strategy:** `{strategy}`")

            # Market Volatility and Summary
            try:
                # Calculate volatility as stddev of 1h returns for top assets
                if portfolio:
                    client = bot.client
                    volatilities = []
                    price_changes = []
                    for asset, data in list(portfolio.items())[:5]:
                        symbol = data['symbol']
                        klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=60)
                        closes = [float(k[4]) for k in klines]
                        returns = pd.Series(closes).pct_change().dropna()
                        vol = returns.std() * (60 ** 0.5) * 100  # annualized approx
                        volatilities.append(vol)
                        price_changes.append((closes[-1] - closes[0]) / closes[0] * 100)
                    avg_vol = sum(volatilities) / len(volatilities)
                    avg_change = sum(price_changes) / len(price_changes)
                    st.info(f"**Market Volatility (1h, avg top assets):** {avg_vol:.2f}% | **Avg 1h Change:** {avg_change:+.2f}%")
                    if avg_vol > 2:
                        st.warning("High volatility: Consider risk management.")
                    elif avg_vol < 0.5:
                        st.info("Low volatility: Market is calm.")
                else:
                    st.info("No portfolio data to compute volatility.")
            except Exception as e:
                st.warning(f"Could not compute volatility: {e}")

            # Add any other important info for the trader
            st.caption("Tip: Monitor volatility and mode to adapt your trading decisions. High volatility may increase risk and opportunity.")

            render_portfolio_summary(portfolio, usd_to_gbp)
            render_pnl_chart()

        elif selected_tab == "Performance":
            st.subheader("Wallet Performance")
            bot = MultiCoinPortfolioBot()
            portfolio = bot.get_portfolio_holdings()
            usd_to_gbp = bot.usd_to_gbp_rate
            render_portfolio_summary(portfolio, usd_to_gbp, show_table=False)
            if portfolio:
                st.dataframe(pd.DataFrame(portfolio).T)

        elif selected_tab == "Logs":
            st.subheader("Bot Logs")
            log_file = "logs/console_output.log"
            if os.path.exists(log_file):
                with open(log_file, "r") as f:
                    logs = f.read()
                st.text_area("Console Output", logs, height=300)
            else:
                st.info("No log file found.")

        elif selected_tab == "Settings":
            st.subheader("Settings")
            st.write("Configure bot settings here.")
            st.write({
                "API_KEY": API_KEY,
                "USE_TESTNET": USE_TESTNET,
                "MIN_BALANCE_USD": MIN_BALANCE_USD
            })

        elif selected_tab == "Strategy":
            st.subheader("Strategy Selection")
            strategies = ["ML Enhanced", "Momentum", "Mean Reversion", "Manual"]
            strategy_mode = st.radio("Select Strategy Mode", ["Automatic", "Manual"], horizontal=True)
            selected_strategy = st.selectbox("Choose Strategy", strategies)
            st.write(f"Current Mode: {strategy_mode}")
            st.write(f"Selected Strategy: {selected_strategy}")
            if strategy_mode == "Manual":
                st.info("Manual mode: You control the strategy selection.")
            else:
                st.info("Automatic mode: Bot will select the best strategy based on analytics.")

        elif selected_tab == "Health":
            st.subheader("Bot Health & Status")
            st.write("Binance API Connected:" if BINANCE_AVAILABLE and API_KEY and API_SECRET else "Not Connected")
            st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Remove sleep and rerun for more responsive UI
    except Exception as e:
        print(f"Error in main loop: {e}")
        time.sleep(10)

if __name__ == "__main__":
    main()
