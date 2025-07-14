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
    def get_stablecoin_swap_opportunities(self):
        """Scan for arbitrage or swap opportunities between USDT, BUSD, USDC"""
        if not self.client:
            return []
        stablecoins = ['USDT', 'BUSD', 'USDC']
        balances = self.get_portfolio_holdings()
        swaps = []
        # Get prices for all stablecoin pairs
        pairs = [('USDT', 'BUSD'), ('USDT', 'USDC'), ('BUSD', 'USDC')]
        for base, quote in pairs:
            symbol = f"{base}{quote}"
            reverse_symbol = f"{quote}{base}"
            try:
                price = None
                if symbol in [t['symbol'] for t in self.client.get_all_tickers()]:
                    price = float(self.client.get_symbol_ticker(symbol=symbol)['price'])
                elif reverse_symbol in [t['symbol'] for t in self.client.get_all_tickers()]:
                    price = 1 / float(self.client.get_symbol_ticker(symbol=reverse_symbol)['price'])
                if price and abs(price - 1) > 0.001:
                    # Arbitrage or swap opportunity
                    swaps.append({
                        'pair': f"{base}/{quote}",
                        'price': price,
                        'action': 'Swap',
                        'reason': f"Price deviation: {price:.4f}",
                        'base_balance': balances.get(base, {}).get('balance', 0),
                        'quote_balance': balances.get(quote, {}).get('balance', 0)
                    })
            except Exception as e:
                continue
        return swaps
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
        """Analyze trading opportunity for a specific coin using selected or auto strategy"""
        from enhanced_ml_strategy import get_strategy_signal
        symbol = coin_data['symbol']
        asset = symbol.replace('USDT', '').replace('BUSD', '').replace('USDC', '')
        try:
            if not self.client:
                # ...existing code for simulation...
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
            # Get market condition and user-selected strategy from session state
            market_condition = self.detect_market_condition(klines)
            import streamlit as st
            strategy_mode = st.session_state.get('strategy_mode', 'Automatic')
            user_selected_strategy = None
            if strategy_mode == 'Manual':
                user_selected_strategy = st.session_state.get('selected_strategy', None)
            # If Automatic, user_selected_strategy stays None (auto-select)
            # Get signal/confidence from strategy logic
            signal, confidence = get_strategy_signal(klines, market_condition, user_selected_strategy)
            closes = [float(k[4]) for k in klines]
            volumes = [float(k[5]) for k in klines]
            highs = [float(k[2]) for k in klines]
            lows = [float(k[3]) for k in klines]
            current_price = closes[-1]
            start_price = closes[0]
            change_2h = ((current_price - start_price) / start_price) * 100
            avg_volume_20 = sum(volumes[-20:]) / 20
            current_volume = volumes[-1]
            volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1
            rsi = self.calculate_rsi(closes)
            recent_high = max(highs[-10:])
            recent_low = min(lows[-10:])
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
                'data_source': 'Binance Live',
                'strategy_used': user_selected_strategy if user_selected_strategy else 'Automatic',
                'market_condition': market_condition
            }
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            return None

    def detect_market_condition(self, klines):
        """Detect market condition for auto strategy selection"""
        # Simple logic: use price change and volatility
        closes = [float(k[4]) for k in klines]
        if len(closes) < 60:
            return 'UNCERTAIN'
        returns = pd.Series(closes).pct_change().dropna()
        vol = returns.std() * (60 ** 0.5) * 100
        price_change = (closes[-1] - closes[0]) / closes[0] * 100
        if vol > 2:
            return 'HIGH_VOLATILITY'
        elif price_change > 5:
            return 'BULL_TRENDING'
        elif price_change < -5:
            return 'BEAR_TRENDING'
        elif abs(price_change) < 1:
            return 'CONSOLIDATING'
        else:
            return 'BALANCED'
    
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
        
        # Also scan for stablecoin swap opportunities
        stablecoin_swaps = self.get_stablecoin_swap_opportunities()
        # Add stablecoin swaps to opportunities (as special entries)
        for swap in stablecoin_swaps:
            opportunities.append({
                'asset': swap['pair'],
                'signal': swap['action'],
                'confidence': 1.0,
                'current_price': swap['price'],
                'change_2h': 0,
                'volume_ratio': 1,
                'rsi': 50,
                'support': 0,
                'resistance': 0,
                'usd_value': swap['base_balance'],
                'balance': swap['base_balance'],
                'data_source': 'Stablecoin Swap',
                'strategy_used': 'Stablecoin Arbitrage',
                'market_condition': 'STABLE'
            })
        return opportunities
    
    def execute_portfolio_rebalancing(self, opportunities):
        """Suggest portfolio rebalancing based on opportunities"""
        suggestions = []
        # Get max trade percent from session state or default to 10%
        max_trade_percent = float(st.session_state.get('max_trade_percent', 10)) / 100.0
        total_portfolio_value = sum(opp.get('usd_value', 0) for opp in opportunities)
        max_trade_amount = total_portfolio_value * max_trade_percent if total_portfolio_value > 0 else 0

        for opp in opportunities:
            if opp['signal'] != 'HOLD' and opp['confidence'] > 0.75:
                # Default logic
                if opp['signal'] == 'SELL':
                    amount = min(opp['usd_value'] * 0.1, max_trade_amount)
                else:
                    amount = min(100, max_trade_amount)
                suggestion = {
                    'action': opp['signal'],
                    'asset': opp['asset'],
                    'reason': f"{opp['change_2h']:+.1f}% move, {opp['confidence']:.1%} confidence",
                    'current_value': opp['usd_value'],
                    'suggested_amount': amount
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

    # Persist strategy selection and mode in session state
    if 'selected_strategy' not in st.session_state:
        st.session_state['selected_strategy'] = 'ML Enhanced'
    if 'strategy_mode' not in st.session_state:
        st.session_state['strategy_mode'] = 'Automatic'
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
            # Always read the latest strategy mode and selected strategy from session state
            strategy_mode = st.session_state.get('strategy_mode', 'Automatic')
            selected_strategy = st.session_state.get('selected_strategy', None)
            # Pass these to each coin analysis via session state (already used in analyze_coin_opportunity)
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

        # --- Password Protection ---
        if 'dashboard_password' not in st.session_state:
            st.session_state['dashboard_password'] = 'bottie'  # Default password
        if 'password_authenticated' not in st.session_state:
            st.session_state['password_authenticated'] = False

        if not st.session_state['password_authenticated']:
            st.subheader("🔒 Enter Dashboard Password")
            input_password = st.text_input("Password", type="password")
            if st.button("Login"):
                if input_password == st.session_state['dashboard_password']:
                    st.session_state['password_authenticated'] = True
                    st.success("Access granted!")
                    st.experimental_rerun()
                else:
                    st.error("Incorrect password.")
                    st.stop()
            if not st.session_state['password_authenticated']:
                st.stop()

        selected_tab = st.sidebar.radio(
            "Select Dashboard Tab",
            ["Portfolio Overview", "Market Indicators", "Performance", "Logs", "Settings", "Strategy", "Health"]
        )
        if selected_tab == "Market Indicators":
            st.subheader("📊 Market Indicators & Signals")
            st.caption("Live summary of all tracked coins, signals, and movements.")
            # Get latest scan results
            opportunities = st.session_state.get('last_opportunities', [])
            if not opportunities:
                st.info("No market data available yet. Start the bot to scan holdings.")
            else:
                # Build flashy table
                table_data = []
                for opp in opportunities:
                    color = "#d4f7dc" if opp['signal'] == 'BUY' else ("#f7d4d4" if opp['signal'] == 'SELL' else "#f7f7d4")
                    arrow = "⬆️" if opp['change_2h'] > 0 else ("⬇️" if opp['change_2h'] < 0 else "➡️")
                    table_data.append({
                        'Asset': opp['asset'],
                        'Signal': f"{opp['signal']} {arrow}",
                        'Confidence': f"{opp['confidence']:.1%}",
                        'Price': f"${opp['current_price']:.4f}",
                        'Change (2h)': f"{opp['change_2h']:+.2f}%",
                        'Volume Ratio': f"{opp['volume_ratio']:.2f}",
                        'RSI': f"{opp['rsi']:.1f}",
                        'Support': f"${opp.get('support', 0):.4f}",
                        'Resistance': f"${opp.get('resistance', 0):.4f}",
                        'Status': f"<span style='background-color:{color};padding:2px 8px;border-radius:6px'>{opp['signal']}</span>",
                        'Strategy': opp.get('strategy_used', 'Auto'),
                        'Source': opp.get('data_source', '')
                    })
                df = pd.DataFrame(table_data)
                # Show as HTML for color highlights
                st.markdown("### All Coin Signals")
                st.write(df.drop(columns=['Status']).style.applymap(
                    lambda v: 'background-color: #d4f7dc' if 'BUY' in str(v) else ('background-color: #f7d4d4' if 'SELL' in str(v) else ''), subset=['Signal']
                ))
                # Show trend chart for each asset
                st.markdown("---")
                st.markdown("#### Recent Movements")
                for opp in opportunities:
                    st.markdown(f"**{opp['asset']}** | Signal: {opp['signal']} | Change (2h): {opp['change_2h']:+.2f}% | RSI: {opp['rsi']:.1f}")
                    # Simulate mini chart (if you want real chart, fetch klines here)
                    st.progress(min(max((opp['rsi']-30)/40,0),1))
                    st.caption(f"Support: ${opp.get('support',0):.4f} | Resistance: ${opp.get('resistance',0):.4f}")

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
                if portfolio:
                    client = bot.client
                    volatilities = []
                    price_changes = []
                    for asset, data in list(portfolio.items())[:5]:
                        symbol = data['symbol']
                        klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=60)
                        closes = [float(k[4]) for k in klines]
                        returns = pd.Series(closes).pct_change().dropna()
                        vol = returns.std() * (60 ** 0.5) * 100
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
            st.caption("Tip: Monitor volatility and mode to adapt your trading decisions. High volatility may increase risk and opportunity.")
            render_portfolio_summary(portfolio, usd_to_gbp)
            render_pnl_chart()

        elif selected_tab == "Performance":
            # ...existing code...
            pass

        elif selected_tab == "Logs":
            # ...existing code...
            pass

        elif selected_tab == "Settings":
            st.subheader("Settings")
            st.write("Configure bot settings here.")
            st.write({
                "API_KEY": API_KEY,
                "USE_TESTNET": USE_TESTNET,
                "MIN_BALANCE_USD": MIN_BALANCE_USD
            })

            # Max trade percent setting
            max_trade_percent = st.number_input(
                "Max Trade Percentage of Portfolio (per deal)", min_value=1.0, max_value=100.0, value=float(st.session_state.get('max_trade_percent', 10)), step=0.5,
                help="Maximum percent of total portfolio value to use in a single trade."
            )
            st.session_state['max_trade_percent'] = max_trade_percent
            st.info(f"Current max trade per deal: {max_trade_percent:.1f}% of portfolio value.")

            # Password change form
            st.markdown("---")
            st.subheader("Change Dashboard Password")
            new_password = st.text_input("New Password", type="password")
            if st.button("Set New Password"):
                if new_password:
                    st.session_state['dashboard_password'] = new_password
                    st.success("Password updated for this session.")
                else:
                    st.warning("Password cannot be empty.")

        elif selected_tab == "Strategy":
            st.subheader("Strategy Selection")
            strategies = [
                "ML Enhanced", "Breakout", "Scalping", "Swing", "Conservative", "Balanced", "Aggressive"
            ]
            strategy_mode = st.radio(
                "Select Strategy Mode",
                ["Automatic", "Manual"],
                horizontal=True,
                key="strategy_mode_radio",
                index=["Automatic", "Manual"].index(st.session_state['strategy_mode'])
            )
            selected_strategy = st.selectbox(
                "Choose Strategy",
                strategies,
                key="selected_strategy_box",
                index=strategies.index(st.session_state['selected_strategy'])
            )
            # Always update session state with the latest selections
            st.session_state['strategy_mode'] = strategy_mode
            st.session_state['selected_strategy'] = selected_strategy
            st.write(f"Current Mode: {strategy_mode}")
            st.write(f"Selected Strategy: {selected_strategy}")
            if strategy_mode == "Manual":
                st.info("Manual mode: You control the strategy selection.")
            else:
                st.info("Automatic mode: Bot will select the best strategy based on analytics.")

            # Strategy characteristics box with full descriptions
            strategy_info = {
                "ML Enhanced": "Combines machine learning predictions with traditional technical analysis. Adapts to changing market conditions using features like price momentum, volatility, RSI, MACD, and support/resistance. Designed for dynamic, data-driven trading decisions.",
                "Breakout": "Trades when price breaks above resistance or below support. Looks for strong 5% moves, often after periods of consolidation. Suited for volatile markets and clear trend reversals.",
                "Scalping": "Executes frequent trades targeting small 2-3% price moves. Relies on high volume and liquidity. Positions are held for short periods, aiming for quick profits and minimal exposure.",
                "Swing": "Seeks 10-20% moves over longer timeframes. Trades on established trends and reversals. Holds positions for several hours to days, balancing risk and reward.",
                "Conservative": "Only trades on high-confidence signals and small price moves. Focuses on capital preservation and risk management. Avoids aggressive entries and prioritizes safety.",
                "Balanced": "Uses standard breakout logic with moderate confidence thresholds. Offers a mix of risk and reward, suitable for most market conditions.",
                "Aggressive": "Trades on lower confidence signals and larger price moves. Accepts higher risk for the potential of greater returns. Suited for traders seeking strong growth and willing to tolerate volatility."
            }
            st.markdown(f"**Strategy Characteristics:**\n> {strategy_info.get(selected_strategy, 'No info available.')}")

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
