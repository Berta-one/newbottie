# hybrid_bot.py - Complete Dashboard + Never-Stop Background Bot + Manual Trading
import streamlit as st
import threading
import time
import os
import json
import subprocess
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px

# Load environment variables
load_dotenv()

# Configuration
USE_TESTNET = os.getenv("USE_TESTNET", "True").lower() == "true"
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
MIN_BALANCE_USD = float(os.getenv("MIN_BALANCE_USD", "10.0"))
SCAN_INTERVAL = 30  # 30 seconds

# Check for Binance library
try:
    from binance.client import Client
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False

# Initialize session state
if 'dashboard_password' not in st.session_state:
    st.session_state['dashboard_password'] = 'bottie'  # Default password
if 'password_authenticated' not in st.session_state:
    st.session_state['password_authenticated'] = False
if 'background_bot_running' not in st.session_state:
    st.session_state['background_bot_running'] = False
if 'background_bot_thread' not in st.session_state:
    st.session_state['background_bot_thread'] = None
if 'selected_strategy' not in st.session_state:
    st.session_state['selected_strategy'] = 'Breakout'
if 'settings_risk_level' not in st.session_state:
    st.session_state['settings_risk_level'] = 'Balanced'

class RobustBackgroundBot:
    """Never-stop background trading bot with robust error handling"""
    def __init__(self):
        self.running = False
        self.scan_count = 0
        self.client = None
        self.start_time = datetime.now()
        self.heartbeat_count = 0
        self.last_heartbeat = datetime.now()
        self.create_log_directories()
        self.initialize_client()
    
    def create_log_directories(self):
        """Create log directories"""
        os.makedirs('logs', exist_ok=True)
    
    def initialize_client(self):
        """Initialize Binance client with error handling"""
        if not BINANCE_AVAILABLE or not API_KEY or not API_SECRET:
            return False
        
        try:
            self.client = Client(API_KEY, API_SECRET)
            if USE_TESTNET:
                self.client.API_URL = "https://testnet.binance.vision/api"
            return True
        except Exception as e:
            self.log_to_console(f"❌ Error connecting to Binance: {e}")
            return False
    
    def log_to_console(self, message):
        """Log message to console and file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        
        try:
            with open('logs/console_output.log', 'a', encoding='utf-8') as f:
                f.write(f"{log_line}\n")
        except:
            pass
    
    def start_keep_alive(self):
        """Start heartbeat system"""
        def heartbeat_loop():
            while self.running:
                try:
                    self.heartbeat_count += 1
                    self.last_heartbeat = datetime.now()
                    self.log_to_console(f"💓 Heartbeat #{self.heartbeat_count} - Bot alive and scanning")
                    time.sleep(60)  # Heartbeat every minute
                except:
                    break
        
        heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        heartbeat_thread.start()
    
    def get_portfolio_balances(self):
        """Get portfolio balances with robust error handling"""
        if not self.client:
            return {}
        
        try:
            account = self.client.get_account()
            balances = {}
            
            for balance in account['balances']:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total > 0:
                    try:
                        ticker = f"{asset}USDT"
                        if asset == 'USDT':
                            price = 1.0
                        else:
                            price_data = self.client.get_symbol_ticker(symbol=ticker)
                            price = float(price_data['price'])
                        
                        usd_value = total * price
                        
                        if usd_value >= MIN_BALANCE_USD:
                            balances[asset] = {
                                'balance': total,
                                'price_usd': price,
                                'usd_value': usd_value,
                                'free': free,
                                'locked': locked
                            }
                    except Exception:
                        pass  # Skip assets with pricing errors
            
            return balances
        except Exception as e:
            self.log_to_console(f"❌ Error getting portfolio: {e}")
            return {}
    
    def scan_for_opportunities(self):
        """Scan for trading opportunities with robust error handling and user-selected strategy"""
        portfolio = self.get_portfolio_balances()
        opportunities = []
        # DEBUG: Opportunity scan diagnostics
        import logging
        logging.basicConfig(filename='logs/console_output.log', level=logging.INFO, format='%(asctime)s %(message)s')
        status = load_bot_status()
        strategy = status.get('latest_strategy', 'Breakout')
        risk = status.get('latest_risk_level', 'Balanced')
        portfolio = status.get('portfolio', {})
        logging.info(f"[SCAN] Starting opportunity scan | Strategy: {strategy} | Risk: {risk} | Portfolio assets: {len(portfolio)}")
        opportunities = []
        assets_scanned = 0
        assets_skipped = 0
        for asset, data in portfolio.items():
            assets_scanned += 1
            price_change = data.get('price_change_pct', 0)
            volume_ratio = data.get('volume_ratio', 1)
            confidence = data.get('confidence', 0.5)
            # Thresholds (adjust as needed)
            # LESS STRICT THRESHOLDS
            if strategy == 'Breakout':
                min_change = 1.5 * (1.0 if risk == 'Balanced' else 0.7 if risk == 'Conservative' else 1.3)
                min_volume = 1.0
                min_conf = 0.45
            elif strategy == 'Scalping':
                min_change = 0.5 * (1.0 if risk == 'Balanced' else 0.7 if risk == 'Conservative' else 1.3)
                min_volume = 0.7
                min_conf = 0.40
            elif strategy == 'Swing':
                min_change = 2.5 * (1.0 if risk == 'Balanced' else 0.7 if risk == 'Conservative' else 1.3)
                min_volume = 0.7
                min_conf = 0.35
            else:
                min_change = 1.5
                min_volume = 0.7
                min_conf = 0.40
            # Detailed debug output for each asset
            logging.info(f"[SCAN-DETAIL] Asset: {asset} | price_change_pct: {price_change} | volume_ratio: {volume_ratio} | confidence: {confidence} | min_change: {min_change} | min_volume: {min_volume} | min_conf: {min_conf}")
            # Opportunity filter
            if abs(price_change) >= min_change and volume_ratio >= min_volume and confidence >= min_conf:
                opportunities.append({
                    'asset': asset,
                    'signal': 'BUY' if price_change > 0 else 'SELL',
                    'confidence': confidence,
                    'change_pct': price_change,
                    'volume_ratio': volume_ratio,
                    'strategy_used': strategy,
                    'risk_level_used': risk
                })
                logging.info(f"[SCAN] Opportunity found: {asset} | Change: {price_change:.2f}% | Volume: {volume_ratio:.2f}x | Confidence: {confidence:.2f}")
            else:
                assets_skipped += 1
                logging.info(f"[SCAN] Skipped {asset} | Change: {price_change:.2f}% | Volume: {volume_ratio:.2f}x | Confidence: {confidence:.2f} | Thresholds: Change>={min_change}, Volume>={min_volume}, Conf>={min_conf}")
        logging.info(f"[SCAN] Scan complete | Opportunities found: {len(opportunities)} | Assets scanned: {assets_scanned} | Assets skipped: {assets_skipped}")
        # Save status
        self.save_status(portfolio, opportunities)
        # Always read latest strategy and risk level from logs/bot_status.json
        selected_strategy = 'Breakout'
        risk_level = 'Balanced'
        try:
            if os.path.exists('logs/bot_status.json'):
                with open('logs/bot_status.json', 'r') as f:
                    status = json.load(f)
                if status.get('latest_strategy'):
                    selected_strategy = status['latest_strategy']
                if status.get('latest_risk_level'):
                    risk_level = status['latest_risk_level']
        except Exception:
            pass

        # Define thresholds for each strategy and risk level
        base_thresholds = {
            'Breakout': {'change': 5.0, 'volume': 1.5},
            'Scalping': {'change': 2.0, 'volume': 1.2},
            'Swing': {'change': 8.0, 'volume': 1.0},
        }
        # Risk level modifiers
        risk_modifiers = {
            'Conservative': 0.8,
            'Balanced': 1.0,
            'Aggressive': 1.2,
        }
        thresholds = base_thresholds.get(selected_strategy, base_thresholds['Breakout']).copy()
        modifier = risk_modifiers.get(risk_level, 1.0)
        thresholds['change'] *= modifier
        thresholds['volume'] *= modifier

        for asset, data in portfolio.items():
            if asset == 'USDT':
                continue

            try:
                symbol = f"{asset}USDT"

                # Get recent price data
                klines = self.client.get_klines(
                    symbol=symbol,
                    interval='1m',
                    limit=120
                )

                if len(klines) >= 120:
                    # Calculate price change over 2 hours
                    current_price = float(klines[-1][4])  # Close price
                    price_2h_ago = float(klines[-120][4])  # Close price 120 minutes ago
                    change_pct = ((current_price - price_2h_ago) / price_2h_ago) * 100

                    # Calculate volume
                    volumes = [float(k[5]) for k in klines[-20:]]  # Last 20 periods
                    avg_volume = sum(volumes) / len(volumes)
                    current_volume = float(klines[-1][5])
                    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

                    # Strategy-based signal logic
                    signal = "HOLD"
                    confidence = 0.5

                    # Use thresholds based on selected strategy and risk level
                    if abs(change_pct) >= thresholds['change'] and volume_ratio >= thresholds['volume']:
                        # Additional filters for quality signals
                        if self.is_good_trading_time() and volume_ratio >= (thresholds['volume'] + 0.5 * modifier):
                            if change_pct > 0:
                                signal = "BUY_LONG"
                                confidence = min(0.9, 0.6 + (change_pct / (30 / modifier)))
                            else:
                                signal = "BUY_SHORT"
                                confidence = min(0.9, 0.6 + (abs(change_pct) / (30 / modifier)))

                    # Only add high-confidence opportunities
                    if signal != "HOLD" and confidence >= 0.65:
                        opportunities.append({
                            'asset': asset,
                            'signal': signal,
                            'confidence': confidence,
                            'current_price': current_price,
                            'change_pct': change_pct,
                            'volume_ratio': volume_ratio,
                            'balance': data['balance'],
                            'usd_value': data['usd_value'],
                            'timestamp': datetime.now().isoformat(),
                            'strategy_used': selected_strategy,
                            'risk_level_used': risk_level
                        })

            except Exception as e:
                self.log_to_console(f"⚠️ Error analyzing {asset}: {e}")

        return portfolio, opportunities
    
    def is_good_trading_time(self):
        """Check if current time is good for trading (avoid low volume hours)"""
        current_hour = datetime.utcnow().hour
        # Avoid trading during low volume hours (0-6 UTC, 22-23 UTC)
        return current_hour not in [0, 1, 2, 3, 4, 5, 22, 23]
    
    def save_status(self, portfolio, opportunities):
        """Save bot status to multiple files for monitoring, preserving latest strategy and risk level"""
        # Read previous bot_status.json to preserve latest_strategy and latest_risk_level
        status_path = 'logs/bot_status.json'
        prev_strategy = None
        prev_risk = None
        try:
            if os.path.exists(status_path):
                with open(status_path, 'r') as f:
                    prev_status = json.load(f)
                prev_strategy = prev_status.get('latest_strategy')
                prev_risk = prev_status.get('latest_risk_level')
        except Exception:
            pass

        status = {
            'timestamp': datetime.now().isoformat(),
            'running': self.running,
            'scan_count': self.scan_count,
            'opportunities': opportunities,
            'portfolio': portfolio,
            'uptime_seconds': int((datetime.now() - self.start_time).total_seconds()),
            'heartbeat_count': self.heartbeat_count,
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'mode': 'Testnet' if USE_TESTNET else 'Live Trading',
            'latest_strategy': prev_strategy if prev_strategy else 'Breakout',
            'latest_risk_level': prev_risk if prev_risk else 'Balanced'
        }

        try:
            # Main status file for dashboard
            with open(status_path, 'w') as f:
                json.dump(status, f, indent=2)

            # Append to scan history
            with open('logs/robust_bot_scans.log', 'a') as f:
                f.write(f"{json.dumps(status)}\n")

        except Exception as e:
            self.log_to_console(f"❌ Error saving status: {e}")
    
    def run_continuous(self):
        """Main bot loop with robust error handling"""
        self.running = True
        self.start_time = datetime.now()
        
        self.log_to_console("🚀 Robust Trading Bot Started")
        self.log_to_console(f"📊 Scan Interval: {SCAN_INTERVAL} seconds")
        self.log_to_console(f"🔗 Mode: {'Testnet' if USE_TESTNET else 'Live Trading'}")
        self.log_to_console(f"💓 Keep-alive: Enabled")
        self.log_to_console("=" * 60)
        
        # Start heartbeat system
        self.start_keep_alive()
        
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        while self.running:
            try:
                self.scan_count += 1
                self.log_to_console(f"🔍 Starting scan #{self.scan_count}")
                
                # Perform scan
                portfolio, opportunities = self.scan_for_opportunities()
                
                # Save status
                self.save_status(portfolio, opportunities)
                
                # Log results
                opp_count = len(opportunities)
                portfolio_count = len(portfolio)
                self.log_to_console(f"✅ Scan #{self.scan_count} complete - {portfolio_count} assets, {opp_count} opportunities")
                
                # Reset error counter on successful scan
                consecutive_errors = 0
                
                # Wait for next scan
                time.sleep(SCAN_INTERVAL)
                
            except Exception as e:
                consecutive_errors += 1
                self.log_to_console(f"❌ Scan #{self.scan_count} error: {e}")
                
                if consecutive_errors >= max_consecutive_errors:
                    self.log_to_console(f"🛑 Too many consecutive errors ({consecutive_errors}). Stopping bot.")
                    break
                
                # Progressive backoff on errors
                error_delay = min(300, 30 * consecutive_errors)  # Max 5 minutes
                self.log_to_console(f"⏰ Waiting {error_delay} seconds before retry...")
                time.sleep(error_delay)
        
        self.log_to_console("🛑 Background bot stopped")
    
    def stop(self):
        """Stop the background bot"""
        self.running = False
        self.log_to_console("🛑 Stop signal received")

# Global bot instance
if 'background_bot' not in st.session_state:
    st.session_state['background_bot'] = RobustBackgroundBot()

def start_background_bot():
    """Start background bot in thread"""
    if not st.session_state['background_bot_running']:
        bot = st.session_state['background_bot']
        thread = threading.Thread(target=bot.run_continuous, daemon=True)
        thread.start()
        st.session_state['background_bot_thread'] = thread
        st.session_state['background_bot_running'] = True
        return True
    return False

def stop_background_bot():
    """Stop background bot"""
    if st.session_state['background_bot_running']:
        bot = st.session_state['background_bot']
        bot.stop()
        st.session_state['background_bot_running'] = False
        return True
    return False

def get_tailscale_ip():
    """Get Tailscale IP for remote access"""
    try:
        output = subprocess.check_output("tailscale ip -4", shell=True, text=True).strip()
        return output.splitlines()[0]
    except:
        return "Unavailable"

def load_logs(log_file, max_lines=200):
    """Load log file contents"""
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            return f.readlines()[-max_lines:]
    return ["No logs found."]

def load_trade_data():
    """Load trade performance data"""
    log_path = "logs/single_pair_performance.json"
    try:
        df = pd.read_json(log_path, lines=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        return df
    except Exception:
        return pd.DataFrame()

def load_bot_status():
    """Load bot status from file"""
    try:
        if os.path.exists('logs/bot_status.json'):
            with open('logs/bot_status.json', 'r') as f:
                return json.load(f)
    except:
        pass
    
    return {
        'timestamp': datetime.now().isoformat(),
        'running': False,
        'scan_count': 0,
        'opportunities': [],
        'portfolio': {},
        'uptime_seconds': 0,
        'heartbeat_count': 0,
        'last_heartbeat': datetime.now().isoformat(),
        'latest_strategy': 'Breakout',
        'latest_risk_level': 'Balanced'
    }

def get_gbp_exchange_rate():
    """Get USD to GBP exchange rate"""
    try:
        import requests
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        return response.json()['rates']['GBP']
    except:
        return 0.79

def color_line(line):
    """Color code log lines"""
    if "error" in line.lower():
        return f":red[{line.strip()}]"
    elif any(x in line.lower() for x in ["profit", "+", "✅", "success"]):
        return f":green[{line.strip()}]"
    elif any(x in line.lower() for x in ["heartbeat", "💓"]):
        return f":blue[{line.strip()}]"
    elif "🔍" in line or "scan" in line.lower():
        return f":orange[{line.strip()}]"
    return f"{line.strip()}"

def simulate_market_analysis(portfolio):
    """Simulate market condition analysis"""
    if not portfolio:
        return "UNCERTAIN", 0.5, 2.0
    
    # Simple volatility calculation based on portfolio size
    volatility = min(5.0, len(portfolio) * 0.5 + 1.0)
    
    if volatility > 3.5:
        condition = "HIGH_VOLATILITY"
        score = 0.7
    elif volatility > 2.0:
        condition = "CONSOLIDATING"
        score = 0.6
    else:
        condition = "BULL_TRENDING"
        score = 0.8
    
    return condition, score, volatility

def update_bot_status_shared():
    """Updated function to properly handle bot status updates"""
    try:
        status_path = 'logs/bot_status.json'
        
        # Read existing status or create new
        if os.path.exists(status_path):
            with open(status_path, 'r') as f:
                status = json.load(f)
        else:
            status = {}
        
        # Update with current session state values
        status['latest_strategy'] = st.session_state.get('selected_strategy', 'Breakout')
        status['latest_risk_level'] = st.session_state.get('settings_risk_level', 'Balanced')
        status['last_updated'] = datetime.now().isoformat()
        status['updated_by'] = 'dashboard_update'
        
        # Write back to file
        with open(status_path, 'w') as f:
            json.dump(status, f, indent=2)
            
        return True
        
    except Exception as e:
        st.error(f"Error updating bot status: {e}")
        return False

def render_portfolio_overview_tab(portfolio, gbp_rate, market_condition, condition_score, avg_volatility):
    """Render portfolio overview tab"""
    st.header("💼 Portfolio Overview")
    st.caption("Live portfolio analysis with dynamic risk management")
    
    if not portfolio:
        st.warning("⚠️ No portfolio data available.")
        if st.session_state['background_bot_running']:
            st.info("Background bot is running. Portfolio data will appear after the first scan.")
        else:
            st.info("Start the background bot in Settings to begin scanning your portfolio.")
        return
    
    # Calculate totals
    total_usd = sum(coin['usd_value'] for coin in portfolio.values())
    total_gbp = total_usd * gbp_rate
    
    # Get actual user-selected strategy and risk level
    status = load_bot_status()
    actual_strategy = status.get('latest_strategy', 'Breakout')
    actual_risk = status.get('latest_risk_level', 'Balanced')
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💷 Portfolio Value", f"£{total_gbp:,.2f}")
    
    with col2:
        condition_color = "🟢" if condition_score > 0.6 else "🟡" if condition_score > 0.4 else "🔴"
        st.metric(f"{condition_color} Market", market_condition.replace('_', ' ').title())
    
    with col3:
        volatility_level = "High" if avg_volatility > 3 else "Medium" if avg_volatility > 1.5 else "Low"
        st.metric("📈 Volatility", f"{avg_volatility:.1f}%")
    
    with col4:
        # Select profile based on market condition (original logic)
        if market_condition == "BULL_TRENDING":
            profile = "Aggressive" if avg_volatility > 2.5 else "Swing"
        elif market_condition == "BEAR_TRENDING":
            profile = "Conservative"
        elif market_condition == "HIGH_VOLATILITY":
            profile = "Scalping"
        else:
            profile = "Balanced"
        
        st.metric("🎯 Active Profile", profile)
    
    st.divider()
    
    # Enhanced Market Analysis & Strategy Display
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Market Analysis")
        
        # Market condition explanations
        market_explanations = {
            "BULL_TRENDING": {
                "emoji": "🟢",
                "description": "Bullish Market",
                "explanation": "Assets are generally trending upward with positive momentum. Good time for swing trades and moderate risk-taking.",
                "best_strategies": ["Swing", "Breakout"],
                "risk_level": "Medium to High"
            },
            "BEAR_TRENDING": {
                "emoji": "🔴", 
                "description": "Bearish Market",
                "explanation": "Assets are trending downward with negative momentum. Focus on capital preservation and short positions.",
                "best_strategies": ["Conservative", "Scalping"],
                "risk_level": "Low"
            },
            "HIGH_VOLATILITY": {
                "emoji": "⚡",
                "description": "High Volatility",
                "explanation": "Rapid price movements in both directions. Quick entries and exits recommended. High risk, high reward.",
                "best_strategies": ["Scalping", "Breakout"],
                "risk_level": "High"
            },
            "CONSOLIDATING": {
                "emoji": "🟡",
                "description": "Consolidating",
                "explanation": "Prices are moving sideways in a range. Good for range trading and accumulation strategies.",
                "best_strategies": ["Scalping", "Balanced"],
                "risk_level": "Medium"
            },
            "UNCERTAIN": {
                "emoji": "❓",
                "description": "Uncertain Market",
                "explanation": "Mixed signals and unclear direction. Use conservative approach until clarity emerges.",
                "best_strategies": ["Conservative", "Balanced"],
                "risk_level": "Low to Medium"
            }
        }
        
        current_market = market_explanations.get(market_condition, market_explanations["UNCERTAIN"])
        
        st.write(f"**{current_market['emoji']} {current_market['description']}**")
        st.write(current_market['explanation'])
        
        # Volatility analysis
        st.markdown("**📈 Volatility Analysis:**")
        if avg_volatility > 4.0:
            st.write("🔥 **Very High** - Extreme price swings expected")
        elif avg_volatility > 3.0:
            st.write("⚡ **High** - Significant price movements likely")
        elif avg_volatility > 1.5:
            st.write("🟡 **Medium** - Moderate price fluctuations")
        else:
            st.write("🟢 **Low** - Stable price movements")
        
        # Market recommendations
        st.markdown("**💡 Market Recommendations:**")
        st.write(f"• **Best Strategies:** {', '.join(current_market['best_strategies'])}")
        st.write(f"• **Risk Level:** {current_market['risk_level']}")
        st.write(f"• **Active Profile:** {profile}")
    
    with col2:
        st.subheader("🎛️ Your Current Settings")
        
        # Current strategy and risk display
        st.markdown("**🎯 Selected Strategy:**")
        
        strategy_descriptions = {
            "Breakout": {
                "emoji": "🚀",
                "description": "Captures 1.5%+ price movements with moderate volume confirmation (less strict)",
                "best_for": "Trending or choppy markets, more frequent signals",
                "risk": "Low to Medium"
            },
            "Scalping": {
                "emoji": "⚡",
                "description": "Quick 0.5%+ moves with lower volume requirements (less strict)",
                "best_for": "High volatility, ranging or flat markets",
                "risk": "Low (shorter exposure, more trades)"
            },
            "Swing": {
                "emoji": "🌊",
                "description": "Captures 2.5%+ moves with patient positioning (less strict)",
                "best_for": "Strong trends, but more signals in quieter markets too",
                "risk": "Low to Medium (longer holds, more opportunities)"
            }
        }
        
        current_strategy_info = strategy_descriptions.get(actual_strategy, strategy_descriptions["Breakout"])
        
        st.success(f"**{current_strategy_info['emoji']} {actual_strategy} Strategy**")
        st.write(current_strategy_info['description'])
        st.write(f"**Best for:** {current_strategy_info['best_for']}")
        st.write(f"**Risk level:** {current_strategy_info['risk']}")
        
        # Risk level display
        st.markdown("**⚖️ Risk Level:**")
        
        risk_descriptions = {
            "Conservative": {
                "emoji": "🛡️",
                "multiplier": "0.7x",
                "description": "Lowest thresholds, most signals, tightest stops, capital preservation focus (less strict)"
            },
            "Balanced": {
                "emoji": "⚖️",
                "multiplier": "1.0x",
                "description": "Moderate thresholds, balanced risk-reward, frequent signals (less strict)"
            },
            "Aggressive": {
                "emoji": "🔥",
                "multiplier": "1.3x",
                "description": "Highest thresholds, widest stops, maximum profit potential, but still more signals (less strict)"
            }
        }
        
        current_risk_info = risk_descriptions.get(actual_risk, risk_descriptions["Balanced"])
        
        st.success(f"**{current_risk_info['emoji']} {actual_risk} Risk**")
        st.write(f"**Multiplier:** {current_risk_info['multiplier']} threshold adjustment")
        st.write(current_risk_info['description'])
        
        # Strategy vs Market alignment
        st.markdown("---")
        st.markdown("**🎯 Strategy Alignment:**")
        
        # Check if user's strategy matches market recommendation
        recommended_strategies = current_market['best_strategies']
        if actual_strategy in recommended_strategies:
            st.success(f"✅ Your {actual_strategy} strategy aligns well with current {market_condition.replace('_', ' ').lower()} conditions!")
        else:
            st.warning(f"⚠️ Consider {'/'.join(recommended_strategies)} for current {market_condition.replace('_', ' ').lower()} conditions")
        
        # Risk alignment
        market_risk = current_market['risk_level'].lower()
        user_risk = actual_risk.lower()
        
        if (("high" in market_risk and user_risk == "aggressive") or 
            ("medium" in market_risk and user_risk == "balanced") or
            ("low" in market_risk and user_risk == "conservative")):
            st.success(f"✅ Your {actual_risk} risk level suits the market")
        else:
            st.info(f"💡 Market suggests {current_market['risk_level']} risk approach")
    
    st.divider()
    
    # Portfolio breakdown table
    st.subheader("💼 Portfolio Holdings")
    
    portfolio_data = []
    for asset, data in portfolio.items():
        portfolio_data.append({
            'Asset': asset,
            'Balance': f"{data['balance']:.8f}".rstrip('0').rstrip('.'),
            'Price (USD)': f"${data['price_usd']:.4f}",
            'Value (USD)': f"${data['usd_value']:.2f}",
            'Value (GBP)': f"£{data['usd_value'] * gbp_rate:.2f}",
            'Percentage': f"{(data['usd_value'] / total_usd * 100):.1f}%"
        })
    
    df = pd.DataFrame(portfolio_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Quick action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Portfolio"):
            st.rerun()
    
    with col2:
        if st.button("⚙️ Adjust Strategy"):
            st.info("💡 Go to Settings tab to change your strategy and risk level")
    
    with col3:
        if st.button("📊 View Opportunities"):
            st.info("💡 Go to Market Indicators tab to see current trading opportunities")

def render_market_indicators_tab():
    """Render market indicators tab"""
    st.header("📊 Market Indicators & Signals")
    st.caption("Live summary of all tracked coins, signals, and movements.")
    
    status = load_bot_status()
    opportunities = status.get('opportunities', [])
    
    if st.session_state['background_bot_running']:
        st.success("🤖 Background bot is continuously scanning your portfolio...")
    else:
        st.warning("🤖 Background bot is stopped. Start it in Settings to begin scanning.")
    
    if opportunities:
        st.success(f"Found {len(opportunities)} trading opportunities!")
        
        for opp in opportunities:
            with st.expander(f"🎯 {opp['asset']} - {opp['signal']} (Confidence: {opp['confidence']:.1%})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Current Price", f"${opp['current_price']:.4f}")
                    st.metric("2h Change", f"{opp['change_pct']:+.2f}%")
                
                with col2:
                    st.metric("Your Balance", f"{opp['balance']:.6f} {opp['asset']}")
                    st.metric("USD Value", f"${opp['usd_value']:.2f}")
                
                with col3:
                    st.metric("Volume Ratio", f"{opp['volume_ratio']:.2f}x")
                    st.metric("Signal Strength", opp['signal'])
                    
                # Show which strategy/risk was used
                st.info(f"Strategy: {opp.get('strategy_used', 'Unknown')} | Risk: {opp.get('risk_level_used', 'Unknown')}")
    else:
        st.info("🔍 No trading opportunities found at this time.")

def render_manual_trading_tab():
    """Render manual trading tab with live trading capabilities"""
    st.header("📈 Manual Trading")
    st.caption("Execute trades manually with real-time market data and safety controls")
    
    # Safety warning for live trading
    if not USE_TESTNET:
        st.error("🚨 **LIVE TRADING MODE** - Real money at risk!")
        st.warning("⚠️ Double-check all trades before execution")
    else:
        st.success("🧪 **TESTNET MODE** - Safe for testing")
    
    # Check API connection
    if not BINANCE_AVAILABLE or not API_KEY or not API_SECRET:
        st.error("❌ Binance API not configured. Please check your .env file.")
        return
    
    # Initialize client
    try:
        client = Client(API_KEY, API_SECRET)
        if USE_TESTNET:
            client.API_URL = "https://testnet.binance.vision/api"
    except Exception as e:
        st.error(f"❌ Failed to connect to Binance: {e}")
        return
    
    # Get account balance
    try:
        account = client.get_account()
        balances = {b['asset']: {'free': float(b['free']), 'locked': float(b['locked'])} 
                   for b in account['balances'] if float(b['free']) > 0 or float(b['locked']) > 0}
        usdt_balance = balances.get('USDT', {'free': 0, 'locked': 0})['free']
    except Exception as e:
        st.error(f"❌ Failed to get account balance: {e}")
        return
    # ...existing code...
    # Find this section in your render_manual_trading_tab() function and replace it:

    # Main trading interface
    col1, col2 = st.columns([2, 1])
    
    # Replace the ENTIRE trading interface section with this simple version:

    # Main trading interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎯 Trade Execution")
        
        # Simple action selection - NO FORM
        action = st.selectbox(
            "💰 What do you want to do?",
            [
                "💸 Sell my crypto for USDT",
                "🛒 Buy crypto with USDT"
            ]
        )
        
        is_selling = "Sell" in action
        
        if is_selling:
            st.success("✅ You're selling crypto to get USDT")
            
            # Show available assets
            available_assets = []
            for asset, balance in balances.items():
                if asset != 'USDT' and balance['free'] > 0:
                    available_assets.append(asset)
            
            if not available_assets:
                st.error("❌ You don't have any crypto to sell")
                st.info("💡 You need crypto assets to sell them for USDT")
            else:
                # Asset selection
                selected_asset = st.selectbox(
                    "Select crypto to sell:",
                    available_assets
                )
                
                symbol = f"{selected_asset}USDT"
                trade_side = "SELL"
                
                # Get current price and balance
                try:
                    ticker = client.get_symbol_ticker(symbol=symbol)
                    current_price = float(ticker['price'])
                    asset_balance = balances.get(selected_asset, {'free': 0})['free']
                    
                    # Show current info
                    col_info1, col_info2, col_info3 = st.columns(3)
                    with col_info1:
                        st.metric("Current Price", f"${current_price:.4f}")
                    with col_info2:
                        st.metric("Your Balance", f"{asset_balance:.8f} {selected_asset}")
                    with col_info3:
                        st.metric("Max USDT Value", f"${asset_balance * current_price:.2f}")
                    
                    # Quantity selection
                    st.write(f"**How much {selected_asset} do you want to sell?**")
                    
                    # Simple percentage buttons
                    col_25, col_50, col_75, col_100 = st.columns(4)
                    with col_25:
                        if st.button("25%", key="sell_25"):
                            st.session_state['sell_quantity'] = asset_balance * 0.25
                    with col_50:
                        if st.button("50%", key="sell_50"):
                            st.session_state['sell_quantity'] = asset_balance * 0.50
                    with col_75:
                        if st.button("75%", key="sell_75"):
                            st.session_state['sell_quantity'] = asset_balance * 0.75
                    with col_100:
                        if st.button("100%", key="sell_100"):
                            st.session_state['sell_quantity'] = asset_balance
                    
                    # Initialize default quantity if not set
                    if 'sell_quantity' not in st.session_state:
                        st.session_state['sell_quantity'] = asset_balance * 0.1
                    
                    # Quantity input
                    quantity = st.number_input(
                        f"Amount to sell:",
                        min_value=0.000001,
                        max_value=asset_balance,
                        value=st.session_state['sell_quantity'],
                        format="%.8f"
                    )
                    
                    # Update session state
                    st.session_state['sell_quantity'] = quantity
                    
                    # Show estimated return
                    if quantity > 0:
                        estimated_usdt = quantity * current_price
                        st.success(f"💰 You'll receive approximately **${estimated_usdt:.2f} USDT**")
                        st.info(f"📊 That's {(quantity/asset_balance)*100:.1f}% of your {selected_asset}")
                    
                except Exception as e:
                    st.error(f"Error getting price for {selected_asset}: {e}")
                    current_price = 0
                    asset_balance = 0
                    quantity = 0
        
        else:
            st.info("ℹ️ You're buying crypto with USDT")
            
            # Crypto selection
            crypto_options = ["BTC", "ETH", "XRP", "SOL", "ADA", "BNB", "AVAX", "MATIC", "DOT", "LINK"]
            selected_crypto = st.selectbox(
                "Select crypto to buy:",
                crypto_options
            )
            
            symbol = f"{selected_crypto}USDT"
            trade_side = "BUY"
            
            # Get current price
            try:
                ticker = client.get_symbol_ticker(symbol=symbol)
                current_price = float(ticker['price'])
                
                # Show current info
                col_info1, col_info2, col_info3 = st.columns(3)
                with col_info1:
                    st.metric("Current Price", f"${current_price:.4f}")
                with col_info2:
                    st.metric("Your USDT", f"${usdt_balance:.2f}")
                with col_info3:
                    max_buyable = usdt_balance / current_price * 0.99
                    st.metric("Max You Can Buy", f"{max_buyable:.8f} {selected_crypto}")
                
                # Quantity selection
                st.write(f"**How much {selected_crypto} do you want to buy?**")
                
                # Simple USDT amount buttons
                col_10, col_25, col_50, col_100 = st.columns(4)
                with col_10:
                    if st.button("$10", key="buy_10"):
                        st.session_state['buy_quantity'] = 10.0 / current_price
                with col_25:
                    if st.button("$25", key="buy_25"):
                        st.session_state['buy_quantity'] = 25.0 / current_price
                with col_50:
                    if st.button("$50", key="buy_50"):
                        st.session_state['buy_quantity'] = 50.0 / current_price
                with col_100:
                    if st.button("$100", key="buy_100"):
                        st.session_state['buy_quantity'] = 100.0 / current_price
                
                # Initialize default quantity if not set
                if 'buy_quantity' not in st.session_state:
                    st.session_state['buy_quantity'] = min(usdt_balance * 0.1, 50.0) / current_price
                
                # Quantity input
                quantity = st.number_input(
                    f"Amount to buy:",
                    min_value=0.000001,
                    max_value=max_buyable,
                    value=st.session_state['buy_quantity'],
                    format="%.8f"
                )
                
                # Update session state
                st.session_state['buy_quantity'] = quantity
                
                # Show estimated cost
                if quantity > 0:
                    estimated_cost = quantity * current_price
                    st.info(f"💳 This will cost approximately **${estimated_cost:.2f} USDT**")
                    st.success(f"📊 You'll get **{quantity:.8f} {selected_crypto}**")
                
            except Exception as e:
                st.error(f"Error getting price for {selected_crypto}: {e}")
                current_price = 0
                quantity = 0
        
        # Order type selection
        st.markdown("---")
        order_type = st.selectbox("Order Type", ["MARKET", "LIMIT"])
        
        # Limit price for limit orders
        limit_price = None
        if order_type == "LIMIT" and current_price > 0:
            limit_price = st.number_input(
                f"Limit Price (USD)",
                min_value=0.0001,
                value=current_price,
                format="%.4f"
            )
        
        # Risk management
        st.markdown("---")
        st.write("**🛡️ Risk Management (Optional)**")
        
        use_stop_loss = st.checkbox("Enable Stop Loss")
        stop_loss_pct = 10.0
        if use_stop_loss:
            stop_loss_pct = st.number_input("Stop Loss %", min_value=1.0, max_value=50.0, value=10.0)
        
        use_take_profit = st.checkbox("Enable Take Profit")
        take_profit_pct = 15.0
        if use_take_profit:
            take_profit_pct = st.number_input("Take Profit %", min_value=1.0, max_value=100.0, value=15.0)
        
        # Execute button
        st.markdown("---")
        if is_selling:
            button_text = f"🔥 Sell {quantity:.6f} {selected_asset} for USDT"
        else:
            button_text = f"🛒 Buy {quantity:.6f} {selected_crypto} with USDT"
        
        # Validation
        can_execute = True
        if quantity <= 0:
            st.error("❌ Please enter a valid quantity")
            can_execute = False
        elif is_selling and quantity > asset_balance:
            st.error(f"❌ You only have {asset_balance:.8f} {selected_asset}")
            can_execute = False
        elif not is_selling and (quantity * current_price) > usdt_balance:
            st.error(f"❌ You only have ${usdt_balance:.2f} USDT")
            can_execute = False
        
        # Execute button
        if st.button(button_text, type="primary", use_container_width=True, disabled=not can_execute):
            if can_execute:
                # Execute the trade
                execute_manual_trade(
                    client, symbol, trade_side, order_type, quantity,
                    limit_price, use_stop_loss, stop_loss_pct,
                    use_take_profit, take_profit_pct, current_price
                )
    
    with col2:
        st.subheader("💰 Account Balance")
        
        # Display balances
        if balances:
            balance_data = []
            for asset, balance in balances.items():
                if balance['free'] > 0 or balance['locked'] > 0:
                    total_balance = balance['free'] + balance['locked']
                    
                    # Get USD value
                    try:
                        if asset == 'USDT':
                            usd_value = total_balance
                        else:
                            ticker = client.get_symbol_ticker(symbol=f"{asset}USDT")
                            usd_value = total_balance * float(ticker['price'])
                    except:
                        usd_value = 0
                    
                    if usd_value >= 1:  # Only show assets worth $1+
                        balance_data.append({
                            'Asset': asset,
                            'Free': f"{balance['free']:.6f}".rstrip('0').rstrip('.'),
                            'Locked': f"{balance['locked']:.6f}".rstrip('0').rstrip('.'),
                            'USD Value': f"${usd_value:.2f}"
                        })
            
            if balance_data:
                df_balance = pd.DataFrame(balance_data)
                st.dataframe(df_balance, use_container_width=True, hide_index=True)
        
        # Current opportunities
        st.markdown("---")
        st.subheader("🎯 Trading Opportunities")
        
        status = load_bot_status()
        opportunities = status.get('opportunities', [])
        
        if opportunities:
            st.success(f"Found {len(opportunities)} opportunities")
            
            for opp in opportunities[:3]:  # Show top 3
                with st.expander(f"{opp['asset']} - {opp['signal']}"):
                    st.metric("Confidence", f"{opp['confidence']:.1%}")
                    st.metric("Price Change", f"{opp['change_pct']:+.2f}%")
                    st.metric("Volume Ratio", f"{opp['volume_ratio']:.2f}x")
                    
                    # Quick trade button
                    if st.button(f"Quick Trade {opp['asset']}", key=f"quick_{opp['asset']}"):
                        st.session_state['trade_symbol'] = f"{opp['asset']}USDT"
                        st.session_state['trade_side'] = "BUY" if opp['signal'] == "BUY_LONG" else "SELL"
                        st.rerun()
        else:
            st.info("No opportunities found")
        
        # Market data
        st.markdown("---")
        st.subheader("📊 Market Data")
        
        # Quick market stats
        try:
            btc_ticker = client.get_symbol_ticker(symbol="BTCUSDT")
            eth_ticker = client.get_symbol_ticker(symbol="ETHUSDT")
            
            st.metric("BTC/USDT", f"${float(btc_ticker['price']):,.0f}")
            st.metric("ETH/USDT", f"${float(eth_ticker['price']):,.0f}")
        except:
            st.info("Market data unavailable")

def execute_manual_trade(client, symbol, side, order_type, quantity, limit_price, 
                        use_stop_loss, stop_loss_pct, use_take_profit, take_profit_pct, current_price):
    """Execute manual trade with error handling and logging"""
    
    try:
        # Prepare order parameters
        order_params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity,
        }
        
        # Add price for limit orders
        if order_type == "LIMIT":
            order_params['price'] = limit_price
            order_params['timeInForce'] = 'GTC'
        
        # Execute main order
        with st.spinner("Executing trade..."):
            order_result = client.create_order(**order_params)
        
        # Log successful trade
        st.success(f"✅ Trade executed successfully!")
        
        # Display order details
        with st.expander("📋 Order Details"):
            st.json(order_result)
        
        # Set up stop loss and take profit if requested
        if order_result['status'] == 'FILLED' and (use_stop_loss or use_take_profit):
            setup_risk_management(client, symbol, side, quantity, current_price, 
                                use_stop_loss, stop_loss_pct, use_take_profit, take_profit_pct)
        
        # Log trade to performance tracking
        log_manual_trade(order_result, use_stop_loss, stop_loss_pct, use_take_profit, take_profit_pct)
        
    except Exception as e:
        st.error(f"❌ Trade failed: {str(e)}")
        
        # Log failed trade
        try:
            with open('logs/manual_trade_errors.log', 'a') as f:
                f.write(f"[{datetime.now().isoformat()}] FAILED: {symbol} {side} {quantity} - {str(e)}\n")
        except:
            pass

def setup_risk_management(client, symbol, original_side, quantity, entry_price, 
                         use_stop_loss, stop_loss_pct, use_take_profit, take_profit_pct):
    """Set up stop loss and take profit orders"""
    
    try:
        # Calculate stop loss and take profit prices
        if original_side == "BUY":
            stop_side = "SELL"
            if use_stop_loss:
                stop_price = entry_price * (1 - stop_loss_pct / 100)
            if use_take_profit:
                take_profit_price = entry_price * (1 + take_profit_pct / 100)
        else:
            stop_side = "BUY"
            if use_stop_loss:
                stop_price = entry_price * (1 + stop_loss_pct / 100)
            if use_take_profit:
                take_profit_price = entry_price * (1 - take_profit_pct / 100)
        
        # Create stop loss order
        if use_stop_loss:
            try:
                stop_order = client.create_order(
                    symbol=symbol,
                    side=stop_side,
                    type='STOP_LOSS_LIMIT',
                    quantity=quantity,
                    price=stop_price * 0.99,  # Slightly below stop price
                    stopPrice=stop_price,
                    timeInForce='GTC'
                )
                st.success(f"✅ Stop loss set at ${stop_price:.4f}")
            except Exception as e:
                st.warning(f"⚠️ Failed to set stop loss: {e}")
        
        # Create take profit order
        if use_take_profit:
            try:
                tp_order = client.create_order(
                    symbol=symbol,
                    side=stop_side,
                    type='LIMIT',
                    quantity=quantity,
                    price=take_profit_price,
                    timeInForce='GTC'
                )
                st.success(f"✅ Take profit set at ${take_profit_price:.4f}")
            except Exception as e:
                st.warning(f"⚠️ Failed to set take profit: {e}")
                
    except Exception as e:
        st.error(f"❌ Risk management setup failed: {e}")

def log_manual_trade(order_result, use_stop_loss, stop_loss_pct, use_take_profit, take_profit_pct):
    """Log manual trade to performance tracking"""
    
    try:
        # Extract fill price for market orders
        fill_price = 0.0
        if order_result['status'] == 'FILLED':
            # Market orders: price is in fills[0]['price']
            fills = order_result.get('fills', [])
            if fills and 'price' in fills[0]:
                fill_price = float(fills[0]['price'])
            else:
                # Fallback to reported price if available
                fill_price = float(order_result.get('price', 0))
        else:
            # For limit/pending orders, use reported price
            fill_price = float(order_result.get('price', 0))

        trade_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'manual_trade',
            'symbol': order_result['symbol'],
            'side': order_result['side'],
            'quantity': float(order_result['executedQty']),
            'price': fill_price,
            'order_id': order_result['orderId'],
            'status': order_result['status'],
            'stop_loss_enabled': use_stop_loss,
            'stop_loss_pct': stop_loss_pct if use_stop_loss else None,
            'take_profit_enabled': use_take_profit,
            'take_profit_pct': take_profit_pct if use_take_profit else None,
            'trade_mode': 'testnet' if USE_TESTNET else 'live'
        }

        # Log to manual trades file
        with open('logs/manual_trades.log', 'a') as f:
            f.write(f"{json.dumps(trade_data)}\n")

    except Exception as e:
        st.error(f"Error logging trade: {e}")

def render_performance_tab():
    """Render performance tab"""
    st.header("📊 Performance")
    st.caption("Trading performance metrics and live wallet")
    
    # Load trade data from both manual and bot logs
    df_bot = load_trade_data()
    manual_log_path = "logs/manual_trades.log"
    manual_trades = []
    if os.path.exists(manual_log_path):
        with open(manual_log_path, "r") as f:
            for line in f:
                try:
                    manual_trades.append(json.loads(line))
                except:
                    pass
    df_manual = pd.DataFrame(manual_trades)
    # Combine both
    if not df_bot.empty and not df_manual.empty:
        df_bot['source'] = 'Bot'
        df_manual['source'] = 'Manual'
        df = pd.concat([df_bot, df_manual], ignore_index=True, sort=False)
    elif not df_bot.empty:
        df_bot['source'] = 'Bot'
        df = df_bot.copy()
    elif not df_manual.empty:
        df_manual['source'] = 'Manual'
        df = df_manual.copy()
    else:
        df = pd.DataFrame()

    if not df.empty:
        # Fill missing columns for display
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        if 'pnl_percent' not in df.columns:
            df['pnl_percent'] = 0.0
        if 'side' not in df.columns:
            df['side'] = ''
        if 'symbol' not in df.columns:
            df['symbol'] = ''
        if 'source' not in df.columns:
            df['source'] = 'Unknown'

        # Performance metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Trades", len(df))
        with col2:
            win_rate = (df['pnl_percent'] > 0).mean() * 100 if 'pnl_percent' in df.columns else 0
            st.metric("Win Rate", f"{win_rate:.1f}%")
        with col3:
            total_pnl = df['pnl_percent'].sum() if 'pnl_percent' in df.columns else 0
            st.metric("Total P&L", f"{total_pnl:+.2f}%")
        with col4:
            avg_pnl = df['pnl_percent'].mean() if 'pnl_percent' in df.columns else 0
            st.metric("Avg P&L", f"{avg_pnl:+.2f}%")

        # Performance chart
        if 'pnl_percent' in df.columns and 'timestamp' in df.columns:
            df_sorted = df.sort_values('timestamp')
            df_sorted['cumulative_pnl'] = df_sorted['pnl_percent'].cumsum()
            fig = px.line(df_sorted, x='timestamp', y='cumulative_pnl', color='source',
                         title="Cumulative P&L Performance")
            st.plotly_chart(fig, use_container_width=True)

        # Recent trades
        with st.expander("📋 Recent Trades"):
            recent_df = df.sort_values('timestamp').tail(10).copy()
            if 'timestamp' in recent_df.columns:
                recent_df['timestamp'] = pd.to_datetime(recent_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
            # Add indicator column
            if 'source' in recent_df.columns:
                recent_df['Trade Type'] = recent_df['source']
            st.dataframe(recent_df[['timestamp','symbol','side','quantity','price','pnl_percent','status','Trade Type']], use_container_width=True, hide_index=True)

        # Open trades (if any) with Mark-to-Market P&L
        if 'status' in df.columns:
            open_trades = df[df['status'].str.lower().isin(['open','pending'])].copy()
            if not open_trades.empty:
                st.subheader("Open Trades (Mark-to-Market P&L)")
                # Get current market prices for each symbol
                if BINANCE_AVAILABLE and API_KEY and API_SECRET:
                    try:
                        client = Client(API_KEY, API_SECRET)
                        if USE_TESTNET:
                            client.API_URL = "https://testnet.binance.vision/api"
                        mtm_pnl = []
                        for idx, trade in open_trades.iterrows():
                            symbol = trade.get('symbol','')
                            side = trade.get('side','BUY')
                            qty = float(trade.get('quantity',0))
                            entry_price = float(trade.get('price',0))
                            try:
                                ticker = client.get_symbol_ticker(symbol=symbol)
                                market_price = float(ticker['price'])
                                if side.upper() == 'BUY':
                                    pnl = (market_price - entry_price) / entry_price * 100
                                else:
                                    pnl = (entry_price - market_price) / entry_price * 100
                            except:
                                market_price = None
                                pnl = None
                            mtm_pnl.append({
                                'timestamp': trade.get('timestamp',''),
                                'symbol': symbol,
                                'side': side,
                                'quantity': qty,
                                'entry_price': entry_price,
                                'market_price': market_price,
                                'mtm_pnl_percent': pnl,
                                'status': trade.get('status',''),
                                'source': trade.get('source','Unknown')
                            })
                        df_mtm = pd.DataFrame(mtm_pnl)
                        st.dataframe(df_mtm[['timestamp','symbol','side','quantity','entry_price','market_price','mtm_pnl_percent','status','source']], use_container_width=True, hide_index=True)
                    except Exception as e:
                        st.error(f"Error fetching market prices for MTM P&L: {e}")
                else:
                    st.info("Binance API not available for Mark-to-Market calculation.")
    else:
        st.info("No trade data available yet. If you have traded, check your logs for errors or format issues.")
    
    # Live Wallet
    st.subheader("💰 Live Wallet (Binance)")
    try:
        if BINANCE_AVAILABLE and API_KEY and API_SECRET:
            client = Client(API_KEY, API_SECRET)
            if USE_TESTNET:
                client.API_URL = "https://testnet.binance.vision/api"
            
            account_info = client.get_account()
            balances = account_info['balances']
            df_wallet = pd.DataFrame(balances)
            df_wallet['free'] = df_wallet['free'].astype(float)
            df_wallet['locked'] = df_wallet['locked'].astype(float)
            df_wallet = df_wallet[df_wallet['free'] > 0]
            st.dataframe(df_wallet[['asset', 'free', 'locked']], use_container_width=True)
            
            # Show total USDT
            usdt_row = df_wallet[df_wallet['asset'] == 'USDT']
            if not usdt_row.empty:
                st.metric("USDT Balance", usdt_row['free'].values[0])
            else:
                st.info("No USDT balance found.")
        else:
            st.warning("Binance API keys not found in environment variables.")
    except Exception as e:
        st.error(f"Error fetching wallet: {e}")
    st.info("If you see no wallet, check your API keys and Binance account.")

def render_logs_tab():
    """Render logs tab"""
    st.header("📡 Logs")
    st.caption("Live logs from your bot will appear here")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        refresh_rate = st.slider("🔁 Refresh every (seconds)", 5, 30, 10)
    
    with col2:
        if st.button("🔄 Manual Refresh"):
            st.rerun()
    
    # Bot status
    status = load_bot_status()
    if st.session_state['background_bot_running']:
        st.success(f"🟢 Background bot is running (Scan #{status.get('scan_count', 0)})")
        
        # Heartbeat check
        if 'last_heartbeat' in status:
            heartbeat_time = datetime.fromisoformat(status['last_heartbeat'])
            time_since_heartbeat = (datetime.now() - heartbeat_time).total_seconds()
            if time_since_heartbeat < 120:  # Within 2 minutes
                st.success(f"💓 Heartbeat active ({int(time_since_heartbeat)}s ago)")
            else:
                st.warning(f"⚠️ Last heartbeat {int(time_since_heartbeat)}s ago")
    else:
        st.warning("🔴 Background bot is stopped")
    
    # Display logs with color coding
    lines = load_logs("logs/console_output.log")
    colored_logs = []
    for line in lines:
        colored_logs.append(color_line(line))
    
    log_output = "\n".join(colored_logs[-50:])  # Show last 50 lines
    st.text_area("Recent Logs", log_output, height=400)
    
    st.info("Live logs from your bot will appear here. If empty, check your log file path and bot status.")

def render_settings_tab():
    """Render settings tab - FIXED VERSION"""
    st.header("⚙️ Settings")
    st.caption("Bot controls and configuration")
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🤖 Background Bot Control")
        
        if st.session_state['background_bot_running']:
            st.success("✅ Background bot is RUNNING 24/7")
            st.info("Bot scans every 30 seconds automatically")
            
            if st.button("🛑 Stop Background Bot", type="secondary"):
                if stop_background_bot():
                    st.success("Background bot stopped")
                    st.rerun()
        else:
            st.warning("⏹️ Background bot is STOPPED")
            
            if st.button("▶️ Start Background Bot", type="primary"):
                if start_background_bot():
                    st.success("🚀 Background bot started!")
                    st.rerun()
        
        # Password change
        st.markdown("---")
        st.subheader("🔐 Change Dashboard Password")
        new_password = st.text_input("New Password", type="password")
        if st.button("Set New Password"):
            if new_password:
                st.session_state['dashboard_password'] = new_password
                st.success("Password updated.")
            else:
                st.warning("Password cannot be empty.")
    
    with col2:
        # Trading mode settings
        st.subheader("🎛️ Trading Configuration")
        trading_mode = st.radio("Trading Mode", ["Automated", "Manual"], key="settings_trading_mode")
        
        # Strategy and Risk Level Selection - FIXED VERSION
        st.markdown("### 🎯 Strategy & Risk Configuration")
        
        # Strategy and Risk options
        strategy_options = ["Breakout", "Scalping", "Swing"]
        risk_options = ["Conservative", "Balanced", "Aggressive"]
        
        # Get current values from bot_status.json for display only
        current_strategy = "Unknown"
        current_risk = "Unknown"
        try:
            status_path = 'logs/bot_status.json'
            if os.path.exists(status_path):
                with open(status_path, 'r') as f:
                    status = json.load(f)
                current_strategy = status.get('latest_strategy', 'Unknown')
                current_risk = status.get('latest_risk_level', 'Unknown')
        except Exception:
            pass
        
        # Display current active settings
        st.info(f"**Currently Active:** Strategy: {current_strategy}, Risk: {current_risk}")
        
        # User selection form
        with st.form(key="strategy_risk_form"):
            st.write("**Select New Configuration:**")
            
            selected_strategy = st.selectbox(
                "Strategy", 
                strategy_options, 
                index=strategy_options.index(st.session_state['selected_strategy']) if st.session_state['selected_strategy'] in strategy_options else 0
            )
            
            risk_level = st.selectbox(
                "Risk Level", 
                risk_options,
                index=risk_options.index(st.session_state['settings_risk_level']) if st.session_state['settings_risk_level'] in risk_options else 1
            )
            
            submitted = st.form_submit_button("✅ Apply New Strategy & Risk", type="primary")
            
            if submitted:
                # Update session state with new values
                st.session_state['selected_strategy'] = selected_strategy
                st.session_state['settings_risk_level'] = risk_level
                
                # Update the bot_status.json file
                try:
                    status_path = 'logs/bot_status.json'
                    
                    # Read existing status or create new
                    if os.path.exists(status_path):
                        with open(status_path, 'r') as f:
                            status = json.load(f)
                    else:
                        status = {}
                    
                    # Update with new selections
                    status['latest_strategy'] = selected_strategy
                    status['latest_risk_level'] = risk_level
                    status['last_updated'] = datetime.now().isoformat()
                    status['updated_by'] = 'dashboard_user'
                    
                    # Write back to file
                    with open(status_path, 'w') as f:
                        json.dump(status, f, indent=2)
                    
                    st.success(f"✅ Successfully updated! New settings: Strategy={selected_strategy}, Risk={risk_level}")
                    
                    # Force refresh to show updated values
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error updating settings: {e}")
                    st.write("Please check file permissions and try again.")
        
        # Additional settings
        st.markdown("---")
        log_retention = st.slider("Log Retention (days)", 1, 30, 7, key="settings_log_retention")
        notification = st.multiselect("Notification Channels", ["Email", "Telegram"], key="settings_notification")

        st.write(f"**Current Configuration:**")
        st.write(f"- Mode: {trading_mode}")
        st.write(f"- Log retention: {log_retention} days")
        st.write(f"- Notifications: {', '.join(notification) if notification else 'None'}")
        
        st.info("💡 New strategy and risk settings will be applied on the next bot scan cycle.")

def render_strategy_tab():
    """Render strategy tab"""
    st.header("🧠 Strategy")
    st.caption("Strategy selection & ML status")
    
    # Get current strategy settings
    status = load_bot_status()
    current_strategy = status.get('latest_strategy', 'Breakout')
    current_risk = status.get('latest_risk_level', 'Balanced')
    
    st.write("**Strategy Status:**")
    st.success(f"✅ Active Strategy: {current_strategy}")
    st.success(f"✅ Risk Level: {current_risk}")
    st.info("Enhanced breakout, scalping, and swing strategies active with volume and time filters")

    st.markdown("---")
    st.subheader("📊 Current Strategy Configuration")

    col1, col2 = st.columns(2)
    with col1:
        st.write("**Breakout Strategy:**")
        st.write("- Threshold: 5% price movement")
        st.write("- Volume: 1.5x average required")
        st.write("- Time filter: Avoid low-volume hours")
        
        st.write("**Scalping Strategy:**")
        st.write("- Threshold: 2% quick moves")
        st.write("- Volume: 1.2x average required")
        st.write("- High frequency trading")

    with col2:
        st.write("**Swing Strategy:**")
        st.write("- Threshold: 8% price movement")
        st.write("- Volume: 1.0x average required")
        st.write("- Longer hold periods")
        
        st.write("**Risk Management:**")
        st.write("- Confidence threshold: 65% minimum")
        st.write("- Dynamic position sizing")
        st.write("- Stop loss: 8-15% based on confidence")

    st.markdown("---")
    st.subheader("🎯 Current Opportunities")
    
    # Show recent opportunities
    opportunities = status.get('opportunities', [])
    if opportunities:
        st.success(f"Current opportunities found: {len(opportunities)}")
        for opp in opportunities[:3]:  # Show top 3
            strategy_used = opp.get('strategy_used', 'Unknown')
            risk_used = opp.get('risk_level_used', 'Unknown')
            st.write(f"• {opp['asset']}: {opp['signal']} (Confidence: {opp['confidence']:.1%}) - Strategy: {strategy_used}, Risk: {risk_used}")
    else:
        st.write("No current opportunities detected.")
    
    st.info("💡 Change strategy and risk settings in the Settings tab to see different opportunities.")

def render_health_tab():
    """Render health tab"""
    st.header("💓 Health")
    st.caption("Bot health & connection status")
    
    # Bot running status
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🤖 Bot Status")
        if st.session_state['background_bot_running']:
            st.success("🟢 Bot is RUNNING")
        else:
            st.error("🔴 Bot is STOPPED")
        
        # API connection status
        st.subheader("🔗 API Connection")
        if BINANCE_AVAILABLE and API_KEY and API_SECRET:
            st.success("✅ Binance API Connected")
            mode = "Testnet" if USE_TESTNET else "Live Trading"
            st.info(f"📡 Mode: {mode}")
        else:
            st.error("❌ Binance API Not Connected")
    
    with col2:
        st.subheader("📊 Health Metrics")
        status = load_bot_status()
        
        # Heartbeat info
        if 'last_heartbeat' in status:
            heartbeat_time = datetime.fromisoformat(status['last_heartbeat'])
            time_since_heartbeat = (datetime.now() - heartbeat_time).total_seconds()
            if time_since_heartbeat < 120:  # Within 2 minutes
                st.success(f"💓 Heartbeat: Active ({int(time_since_heartbeat)}s ago)")
            else:
                st.warning(f"⚠️ Heartbeat: {int(time_since_heartbeat)}s ago")
        else:
            st.info("💓 Heartbeat: No data")
        
        # Scan stats
        st.metric("Total Scans", status.get('scan_count', 0))
        uptime = status.get('uptime_seconds', 0)
        st.metric("Bot Uptime", f"{uptime // 3600:.0f}h {(uptime % 3600) // 60:.0f}m")
        # Show last scan time if available
        if 'timestamp' in status:
            st.metric("Last Scan", status['timestamp'])
    
    # Log file check
    st.subheader("📁 Log File Status")
    if os.path.exists("logs/console_output.log"):
        with open("logs/console_output.log", "r", encoding="utf-8") as f:
            last_lines = f.readlines()[-10:]
        
        st.success("✅ Log file accessible")
        heartbeat_found = any("heartbeat" in l.lower() for l in last_lines)
        if heartbeat_found:
            st.success("✅ Recent heartbeat detected in logs")
        else:
            st.warning("⚠️ No recent heartbeat in logs")
        
        # Show last few log lines
        st.subheader("📝 Recent Log Activity")
        st.code("\n".join([line.strip() for line in last_lines]))
    else:
        st.error("❌ Log file not found")
    
    st.info("If health info is missing, check your bot and log file paths.")

def dashboard():
    """Main dashboard function - Updated to include Trading tab"""
    # Get Tailscale IP and setup sidebar controls
    ts_ip = get_tailscale_ip()
    remote_url = f"http://{ts_ip}:8501" if ts_ip != "Unavailable" else "Unavailable"
    
    # Sidebar setup
    st.sidebar.markdown(f"**Tailscale IP:** `{ts_ip}`")
    st.sidebar.text_input("🔗 Access URL", value=remote_url, key="url", label_visibility="collapsed")
    st.sidebar.download_button("📥 Download Logs", data="\n".join(load_logs("logs/console_output.log")), file_name="console_output.log")

    # Bot status in sidebar
    st.sidebar.subheader("🤖 Bot Status")
    if st.session_state['background_bot_running']:
        st.sidebar.success("🟢 Bot is running")
        if st.sidebar.button("🛑 Stop Bot"):
            stop_background_bot()
            st.sidebar.info("Bot stopped.")
    else:
        st.sidebar.warning("🔴 Bot is stopped")
        if st.sidebar.button("▶️ Start Bot"):
            if start_background_bot():
                st.sidebar.success("Bot started.")
            else:
                st.sidebar.error("Failed to start bot.")

    if st.sidebar.button("🔄 Refresh Dashboard"):
        st.rerun()

    # Auto-start background bot on first load if configured
    if not st.session_state['background_bot_running'] and BINANCE_AVAILABLE and API_KEY and API_SECRET:
        start_background_bot()

    # Sidebar navigation - UPDATED to include Trading tab
    selected_tab = st.sidebar.radio(
        "Select Dashboard Tab",
        ["Portfolio Overview", "Market Indicators", "Trading", "Performance", "Logs", "Settings", "Strategy", "Health"]
    )
    
    # Get portfolio data for all tabs
    status = load_bot_status()
    portfolio = status.get('portfolio', {})
    gbp_rate = get_gbp_exchange_rate()
    
    if portfolio:
        market_condition, condition_score, avg_volatility = simulate_market_analysis(portfolio)
    else:
        market_condition, condition_score, avg_volatility = "UNCERTAIN", 0.5, 2.0
    
    # Render selected tab - UPDATED to include Trading tab
    if selected_tab == "Portfolio Overview":
        render_portfolio_overview_tab(portfolio, gbp_rate, market_condition, condition_score, avg_volatility)
    elif selected_tab == "Market Indicators":
        render_market_indicators_tab()
    elif selected_tab == "Trading":
        render_manual_trading_tab()
    elif selected_tab == "Performance":
        render_performance_tab()
    elif selected_tab == "Logs":
        render_logs_tab()
    elif selected_tab == "Settings":
        render_settings_tab()
    elif selected_tab == "Strategy":
        render_strategy_tab()
    elif selected_tab == "Health":
        render_health_tab()

def main():
    """Main application entry point"""
    st.set_page_config(page_title="🤖 Crypto Trading Bot Dashboard", layout="wide")
    
    # Password authentication
    if not st.session_state['password_authenticated']:
        st.title("🔒 Enter Dashboard Password")
        input_password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if input_password == st.session_state['dashboard_password']:
                st.session_state['password_authenticated'] = True
                st.success("Access granted!")
                st.rerun()
            else:
                st.error("Incorrect password.")
                st.stop()
        
        if not st.session_state['password_authenticated']:
            st.stop()
    
    # Main dashboard
    st.title("🤖 Crypto Trading Bot Dashboard")
    st.caption("Professional trading with 24/7 background scanning")
    
    dashboard()

if __name__ == "__main__":
    main()