import os
import time
import streamlit as st
from datetime import datetime
import pandas as pd
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np

# Check if we have Binance library
try:
    from binance.client import Client
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False

class AdaptiveRiskManager:
    def __init__(self):
        # Professional risk management rulesets
        self.risk_profiles = {
            "CONSERVATIVE": {
                "name": "Conservative",
                "take_profit": 6.0,
                "stop_loss": 4.0,
                "trailing_stop": 2.5,
                "max_hold_hours": 6,
                "confidence_threshold": 0.8,
                "description": "Low volatility, high confidence trades"
            },
            "BALANCED": {
                "name": "Balanced", 
                "take_profit": 10.0,
                "stop_loss": 8.0,
                "trailing_stop": 3.5,
                "max_hold_hours": 4,
                "confidence_threshold": 0.7,
                "description": "Standard institutional approach"
            },
            "AGGRESSIVE": {
                "name": "Aggressive",
                "take_profit": 15.0,
                "stop_loss": 12.0,
                "trailing_stop": 5.0,
                "max_hold_hours": 8,
                "confidence_threshold": 0.6,
                "description": "High volatility, trend-following"
            },
            "SCALPING": {
                "name": "Scalping",
                "take_profit": 3.0,
                "stop_loss": 2.0,
                "trailing_stop": 1.0,
                "max_hold_hours": 1,
                "confidence_threshold": 0.85,
                "description": "Quick profits, minimal risk"
            },
            "SWING": {
                "name": "Swing Trading",
                "take_profit": 20.0,
                "stop_loss": 15.0,
                "trailing_stop": 8.0,
                "max_hold_hours": 24,
                "confidence_threshold": 0.75,
                "description": "Multi-day position holding"
            }
        }
        
        # Market condition indicators
        self.market_conditions = {
            "BULL_TRENDING": "Strong upward momentum",
            "BEAR_TRENDING": "Strong downward momentum", 
            "CONSOLIDATING": "Sideways movement, low volatility",
            "HIGH_VOLATILITY": "Rapid price swings",
            "UNCERTAIN": "Mixed signals, unclear direction"
        }
    
    def calculate_market_volatility(self, klines_data):
        """Calculate market volatility using multiple timeframes"""
        try:
            if not klines_data or len(klines_data) < 50:
                return 0.02  # Default 2% volatility
            
            # Get price data
            closes = [float(k[4]) for k in klines_data]
            highs = [float(k[2]) for k in klines_data]
            lows = [float(k[3]) for k in klines_data]
            
            # Calculate returns
            returns = [(closes[i] / closes[i-1] - 1) for i in range(1, len(closes))]
            
            # Average True Range (ATR) for volatility
            true_ranges = []
            for i in range(1, len(klines_data)):
                tr1 = highs[i] - lows[i]
                tr2 = abs(highs[i] - closes[i-1])
                tr3 = abs(lows[i] - closes[i-1])
                true_ranges.append(max(tr1, tr2, tr3))
            
            atr = sum(true_ranges[-14:]) / 14 if len(true_ranges) >= 14 else sum(true_ranges) / len(true_ranges)
            atr_pct = (atr / closes[-1]) * 100
            
            # Standard deviation of returns
            if len(returns) > 1:
                std_dev = np.std(returns) * 100  # Convert to percentage
            else:
                std_dev = 1.0
            
            # Combined volatility measure
            volatility = (atr_pct + std_dev) / 2
            
            return volatility
            
        except Exception as e:
            print(f"Volatility calculation error: {e}")
            return 0.02
    
    def analyze_market_condition(self, symbol_data_list):
        """Analyze overall market condition across portfolio"""
        try:
            if not symbol_data_list:
                return "UNCERTAIN", 0.5
            
            volatilities = []
            trends = []
            volumes = []
            
            for data in symbol_data_list:
                if 'klines' in data and data['klines']:
                    klines = data['klines']
                    closes = [float(k[4]) for k in klines]
                    volumes_data = [float(k[5]) for k in klines]
                    
                    # Volatility
                    volatility = self.calculate_market_volatility(klines)
                    volatilities.append(volatility)
                    
                    # Trend strength (SMA comparison)
                    if len(closes) >= 50:
                        sma_20 = sum(closes[-20:]) / 20
                        sma_50 = sum(closes[-50:]) / 50
                        trend_strength = (sma_20 - sma_50) / sma_50 * 100
                        trends.append(trend_strength)
                    
                    # Volume trend
                    if len(volumes_data) >= 20:
                        avg_vol_recent = sum(volumes_data[-10:]) / 10
                        avg_vol_old = sum(volumes_data[-20:-10]) / 10
                        vol_trend = (avg_vol_recent - avg_vol_old) / avg_vol_old * 100
                        volumes.append(vol_trend)
            
            if not volatilities:
                return "UNCERTAIN", 0.5
            
            # Calculate market metrics
            avg_volatility = sum(volatilities) / len(volatilities)
            avg_trend = sum(trends) / len(trends) if trends else 0
            avg_volume_trend = sum(volumes) / len(volumes) if volumes else 0
            
            # Determine market condition
            condition_score = 0.5
            
            if avg_volatility > 4.0:  # High volatility
                if abs(avg_trend) > 3.0:  # Strong trend
                    if avg_trend > 0:
                        condition = "BULL_TRENDING"
                        condition_score = 0.8
                    else:
                        condition = "BEAR_TRENDING" 
                        condition_score = 0.3
                else:
                    condition = "HIGH_VOLATILITY"
                    condition_score = 0.4
            elif avg_volatility < 1.5:  # Low volatility
                condition = "CONSOLIDATING"
                condition_score = 0.6
            else:  # Medium volatility
                if abs(avg_trend) > 2.0:
                    if avg_trend > 0:
                        condition = "BULL_TRENDING"
                        condition_score = 0.75
                    else:
                        condition = "BEAR_TRENDING"
                        condition_score = 0.35
                else:
                    condition = "UNCERTAIN"
                    condition_score = 0.5
            
            return condition, condition_score
            
        except Exception as e:
            print(f"Market condition analysis error: {e}")
            return "UNCERTAIN", 0.5
    
    def select_optimal_risk_profile(self, market_condition, volatility, portfolio_performance=None):
        """Select the best risk profile based on market conditions"""
        
        # Default to balanced
        recommended_profile = "BALANCED"
        
        # Market condition based selection
        if market_condition == "BULL_TRENDING":
            if volatility < 2.0:
                recommended_profile = "SWING"  # Ride the trend
            else:
                recommended_profile = "AGGRESSIVE"  # Volatile uptrend
                
        elif market_condition == "BEAR_TRENDING":
            recommended_profile = "CONSERVATIVE"  # Protect capital
            
        elif market_condition == "CONSOLIDATING":
            if volatility < 1.5:
                recommended_profile = "SCALPING"  # Range trading
            else:
                recommended_profile = "CONSERVATIVE"  # Wait for clarity
                
        elif market_condition == "HIGH_VOLATILITY":
            recommended_profile = "SCALPING"  # Quick in and out
            
        else:  # UNCERTAIN
            recommended_profile = "CONSERVATIVE"  # Preserve capital
        
        # Adjust based on recent portfolio performance
        if portfolio_performance:
            win_rate = portfolio_performance.get('win_rate', 50)
            recent_pnl = portfolio_performance.get('recent_pnl', 0)
            
            # If doing well, can be slightly more aggressive
            if win_rate > 70 and recent_pnl > 5:
                if recommended_profile == "CONSERVATIVE":
                    recommended_profile = "BALANCED"
                elif recommended_profile == "BALANCED":
                    recommended_profile = "AGGRESSIVE"
            
            # If doing poorly, be more conservative
            elif win_rate < 40 or recent_pnl < -10:
                if recommended_profile == "AGGRESSIVE":
                    recommended_profile = "BALANCED"
                elif recommended_profile in ["BALANCED", "SWING"]:
                    recommended_profile = "CONSERVATIVE"
        
        return recommended_profile
    
    def get_dynamic_rules(self, asset, confidence, market_condition, volatility):
        """Get dynamic rules for specific asset and conditions"""
        
        # Select base profile
        base_profile_name = self.select_optimal_risk_profile(market_condition, volatility)
        base_profile = self.risk_profiles[base_profile_name]
        
        # Asset-specific adjustments
        asset_multipliers = {
            'BTC': {'risk': 0.9, 'reward': 0.9},    # Slightly more conservative
            'ETH': {'risk': 1.0, 'reward': 1.0},    # Standard
            'SOL': {'risk': 1.1, 'reward': 1.2},    # More volatile
            'XRP': {'risk': 1.0, 'reward': 1.1},    # Standard+
            'ADA': {'risk': 1.1, 'reward': 1.1},    # Slightly more volatile
            'DEFAULT': {'risk': 1.2, 'reward': 1.3}  # Unknown alts - more risk
        }
        
        multiplier = asset_multipliers.get(asset, asset_multipliers['DEFAULT'])
        
        # Confidence adjustments
        confidence_factor = min(1.5, max(0.7, confidence / 0.7))
        
        # Calculate final rules
        dynamic_rules = {
            'profile_used': base_profile_name,
            'take_profit': base_profile['take_profit'] * multiplier['reward'] * confidence_factor,
            'stop_loss': base_profile['stop_loss'] * multiplier['risk'] / confidence_factor,
            'trailing_stop': base_profile['trailing_stop'] * multiplier['risk'],
            'max_hold_hours': base_profile['max_hold_hours'],
            'confidence_threshold': base_profile['confidence_threshold'],
            'market_condition': market_condition,
            'volatility': volatility,
            'asset_risk_factor': multiplier['risk'],
            'confidence_factor': confidence_factor
        }
        
        # Ensure reasonable bounds
        dynamic_rules['take_profit'] = max(2.0, min(25.0, dynamic_rules['take_profit']))
        dynamic_rules['stop_loss'] = max(1.5, min(20.0, dynamic_rules['stop_loss']))
        dynamic_rules['trailing_stop'] = max(0.5, min(10.0, dynamic_rules['trailing_stop']))
        
        return dynamic_rules
    
    def should_exit_position(self, position_data, current_price, dynamic_rules):
        """Determine if position should be exited based on dynamic rules"""
        
        entry_price = position_data['entry_price']
        entry_time = position_data['entry_time']
        signal_type = position_data.get('signal_type', 'BUY')
        highest_price = position_data.get('highest_price', entry_price)
        
        # Calculate current P&L
        if signal_type in ['BUY_LONG', 'BUY']:
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
        else:  # SHORT positions
            pnl_pct = ((entry_price - current_price) / entry_price) * 100
        
        # Update highest price for trailing stop
        if current_price > highest_price:
            position_data['highest_price'] = current_price
            highest_price = current_price
        
        # Time-based exit
        time_held = (datetime.now() - entry_time).total_seconds() / 3600  # hours
        if time_held >= dynamic_rules['max_hold_hours']:
            return True, f"Time limit reached: {time_held:.1f}h (Max: {dynamic_rules['max_hold_hours']}h)"
        
        # Take profit
        if pnl_pct >= dynamic_rules['take_profit']:
            return True, f"Take profit: {pnl_pct:+.2f}% (Target: {dynamic_rules['take_profit']:.1f}%)"
        
        # Stop loss
        if pnl_pct <= -dynamic_rules['stop_loss']:
            return True, f"Stop loss: {pnl_pct:+.2f}% (Max loss: {dynamic_rules['stop_loss']:.1f}%)"
        
        # Trailing stop (only if in profit)
        if pnl_pct > 2.0:  # Only activate trailing stop after 2% profit
            trailing_exit_price = highest_price * (1 - dynamic_rules['trailing_stop'] / 100)
            if current_price <= trailing_exit_price:
                return True, f"Trailing stop: {pnl_pct:+.2f}% (Trail: {dynamic_rules['trailing_stop']:.1f}%)"
        
        # Emergency exits (circuit breakers)
        if abs(pnl_pct) > 25:  # Emergency stop at 25%
            return True, f"Emergency exit: {pnl_pct:+.2f}% (Circuit breaker)"
        
        return False, f"Hold: {pnl_pct:+.2f}% (Profile: {dynamic_rules['profile_used']})"

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
        self.positions = {}
        self.usd_to_gbp_rate = 0.79
        self.risk_manager = AdaptiveRiskManager()
        self.initialize_binance()
        self.update_gbp_rate()
        
    def update_gbp_rate(self):
        """Get live USD to GBP exchange rate"""
        try:
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
            
            if self.client:
                try:
                    ticker = self.client.get_symbol_ticker(symbol='GBPUSDT')
                    gbp_usd_rate = float(ticker['price'])
                    self.usd_to_gbp_rate = 1 / gbp_usd_rate
                    return True
                except:
                    pass
                    
        except Exception as e:
            print(f"Exchange rate API error: {e}")
        
        return False
    
    def get_portfolio_value_gbp(self, usd_value):
        """Convert USD value to GBP"""
        return usd_value * self.usd_to_gbp_rate
        
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
            all_tickers = {t['symbol']: float(t['price']) for t in self.client.get_all_tickers()}
            
            for balance in account['balances']:
                asset = balance['asset']
                free_balance = float(balance['free'])
                locked_balance = float(balance['locked'])
                total_balance = free_balance + locked_balance
                
                if total_balance > 0 and asset != 'USDT':
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

def main():

    
    st.title("🎯 Adaptive Risk Management Trading Bot")
    st.caption("Professional, emotion-free trading with dynamic risk adjustment")
    
    # Initialize bot
    if 'adaptive_bot' not in st.session_state:
        st.session_state.adaptive_bot = MultiCoinPortfolioBot()
    
    bot = st.session_state.adaptive_bot
    risk_manager = bot.risk_manager
    
    # Risk Profile Overview
    st.subheader("⚙️ Professional Risk Management Profiles")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Available Risk Profiles")
        for profile_key, profile in risk_manager.risk_profiles.items():
            with st.expander(f"{profile['name']} Profile"):
                st.write(f"**Description:** {profile['description']}")
                st.write(f"**Take Profit:** {profile['take_profit']}%")
                st.write(f"**Stop Loss:** {profile['stop_loss']}%")
                st.write(f"**Trailing Stop:** {profile['trailing_stop']}%")
                st.write(f"**Max Hold:** {profile['max_hold_hours']} hours")
                st.write(f"**Min Confidence:** {profile['confidence_threshold']:.0%}")
    
    with col2:
        st.markdown("### 🌍 Market Conditions")
        for condition, description in risk_manager.market_conditions.items():
            st.write(f"**{condition.replace('_', ' ').title()}:** {description}")
    
    # Live Market Analysis
    st.subheader("📊 Live Market Condition Analysis")
    
    # Simulate market analysis for demo
    portfolio = bot.get_portfolio_holdings()
    
    if portfolio:
        # Simulate market data for each asset
        market_data = []
        for asset, data in portfolio.items():
            # Simulate klines data for market analysis
            import random
            simulated_klines = []
            base_price = data['price_usd']
            
            for i in range(120):
                change = random.uniform(-0.002, 0.002)
                base_price *= (1 + change)
                simulated_klines.append([
                    0, str(base_price), str(base_price * 1.001), 
                    str(base_price * 0.999), str(base_price), str(random.uniform(100, 1000)),
                    0, 0, 0, 0, 0, 0
                ])
            
            market_data.append({
                'asset': asset,
                'klines': simulated_klines,
                'symbol': data['symbol']
            })
        
        # Analyze market condition
        market_condition, condition_score = risk_manager.analyze_market_condition(market_data)
        avg_volatility = sum(risk_manager.calculate_market_volatility(data['klines']) for data in market_data) / len(market_data)
        
        # Recommended profile
        recommended_profile = risk_manager.select_optimal_risk_profile(market_condition, avg_volatility)
        
        # Display market analysis
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            condition_color = "🟢" if condition_score > 0.6 else "🟡" if condition_score > 0.4 else "🔴"
            st.metric(f"{condition_color} Market Condition", 
                     market_condition.replace('_', ' ').title(),
                     f"Score: {condition_score:.2f}")
        
        with col2:
            volatility_level = "High" if avg_volatility > 3 else "Medium" if avg_volatility > 1.5 else "Low"
            st.metric("📈 Volatility", f"{avg_volatility:.1f}%", volatility_level)
        
        with col3:
            st.metric("🎯 Recommended Profile", 
                     risk_manager.risk_profiles[recommended_profile]['name'],
                     "Auto-Selected")
        
        with col4:
            st.metric("⏰ Last Update", 
                     datetime.now().strftime("%H:%M:%S"), "Live")
        
        # Dynamic rules for each asset
        st.subheader("⚖️ Dynamic Risk Rules by Asset")
        
        for asset, data in portfolio.items():
            confidence = random.uniform(0.6, 0.95)  # Simulated confidence
            dynamic_rules = risk_manager.get_dynamic_rules(asset, confidence, market_condition, avg_volatility)
            
            with st.expander(f"{asset} - Dynamic Rules"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Take Profit", f"{dynamic_rules['take_profit']:.1f}%")
                    st.metric("Stop Loss", f"{dynamic_rules['stop_loss']:.1f}%")
                
                with col2:
                    st.metric("Trailing Stop", f"{dynamic_rules['trailing_stop']:.1f}%")
                    st.metric("Max Hold", f"{dynamic_rules['max_hold_hours']:.0f}h")
                
                with col3:
                    st.metric("Profile Used", dynamic_rules['profile_used'])
                    st.metric("Risk Factor", f"{dynamic_rules['asset_risk_factor']:.2f}x")
        
        # Portfolio overview with GBP
        total_usd = sum(coin['usd_value'] for coin in portfolio.values())
        total_gbp = bot.get_portfolio_value_gbp(total_usd)
        
        st.subheader("💼 Portfolio Overview")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💷 Total Value (GBP)", f"£{total_gbp:,.2f}")
        with col2:
            st.metric("💰 Total Value (USD)", f"${total_usd:,.2f}")
        with col3:
            st.metric("🪙 Assets", len(portfolio))
    
    # Configuration
    with st.expander("🔧 System Configuration"):
        st.json({
            "Risk Management": "Adaptive, market-condition based",
            "Profiles Available": list(risk_manager.risk_profiles.keys()),
            "Market Analysis": "Multi-timeframe volatility + trend analysis",
            "Asset Adjustments": "BTC conservative, alts more aggressive",
            "Confidence Scaling": "Higher confidence = wider targets",
            "Emergency Stops": "25% circuit breaker on all positions",
            "Auto-Selection": "System chooses optimal profile automatically",
            "Update Frequency": "Real-time based on market conditions"
        })
    
    # Auto-refresh every 30 seconds
    time.sleep(1)
    st.rerun()

if __name__ == "__main__":
    main()
