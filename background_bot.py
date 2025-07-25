 -*- coding: utf-8 -*-
# background_bot.py - True 24/7 Trading Bot Service
import time
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
USE_TESTNET = os.getenv("USE_TESTNET", "True").lower() == "true"
MIN_BALANCE_USD = float(os.getenv("MIN_BALANCE_USD", "10.0"))
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "30"))  # 30 seconds

try:
    from binance.client import Client

    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    print("âŒ python-binance not available. Install with: pip install python-binance")


class BackgroundTradingBot:
    def __init__(self):
        self.running = False
        self.scan_count = 0
        self.client = None
        self.initialize_client()
        self.create_log_directories()

    def create_log_directories(self):
        """Create log directories"""
        os.makedirs("logs", exist_ok=True)

    def initialize_client(self):
        """Initialize Binance client"""
        if not BINANCE_AVAILABLE or not API_KEY or not API_SECRET:
            print("âŒ Binance client initialization failed")
            return False

        try:
            self.client = Client(API_KEY, API_SECRET)
            if USE_TESTNET:
                self.client.API_URL = "https://testnet.binance.vision/api"
            print("âœ… Binance client initialized")
            return True
        except Exception as e:
            print(f"âŒ Error connecting to Binance: {e}")
            return False

    def get_portfolio(self):
        """Get portfolio from Binance"""
        if not self.client:
            return {}

        try:
            account = self.client.get_account()
            all_prices = self.client.get_all_tickers()
            price_dict = {
                ticker["symbol"]: float(ticker["price"]) for ticker in all_prices
            }

            portfolio = {}

            for balance in account["balances"]:
                asset = balance["asset"]
                free_balance = float(balance["free"])
                locked_balance = float(balance["locked"])
                total_balance = free_balance + locked_balance

                if total_balance > 0:
                    if asset == "USDT":
                        portfolio[asset] = {
                            "balance": total_balance,
                            "price_usd": 1.0,
                            "usd_value": total_balance,
                            "symbol": "USDT",
                        }
                    else:
                        trading_symbol = f"{asset}USDT"
                        if trading_symbol in price_dict:
                            price_usd = price_dict[trading_symbol]
                            usd_value = total_balance * price_usd

                            if usd_value >= MIN_BALANCE_USD:
                                portfolio[asset] = {
                                    "balance": total_balance,
                                    "price_usd": price_usd,
                                    "usd_value": usd_value,
                                    "symbol": trading_symbol,
                                }

            return portfolio

        except Exception as e:
            print(f"âŒ Error fetching portfolio: {e}")
            return {}

    def analyze_opportunity(self, symbol):
        """Analyze trading opportunity for symbol"""
        if not self.client:
            return None

        try:
            # Get 2 hours of 1-minute data
            klines = self.client.get_klines(symbol=symbol, interval="1m", limit=120)

            if len(klines) < 120:
                return None

            # Calculate price change over 2 hours
            open_price = float(klines[0][1])
            close_price = float(klines[-1][4])
            change_pct = ((close_price - open_price) / open_price) * 100

            # Calculate volume ratio
            volumes = [float(kline[5]) for kline in klines[-20:]]
            avg_volume = sum(volumes) / len(volumes)
            current_volume = float(klines[-1][5])
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

            # Generate signal
            signal = "HOLD"
            confidence = 0.5

            if abs(change_pct) >= 5.0 and volume_ratio >= 1.5:
                if change_pct >= 5.0:
                    signal = "BUY_LONG"
                    confidence = min(0.95, 0.6 + (change_pct - 5) * 0.05)
                elif change_pct <= -5.0:
                    signal = "BUY_SHORT"
                    confidence = min(0.95, 0.6 + (abs(change_pct) - 5) * 0.05)

            return {
                "symbol": symbol,
                "signal": signal,
                "confidence": confidence,
                "change_pct": change_pct,
                "volume_ratio": volume_ratio,
                "current_price": close_price,
            }

        except Exception as e:
            print(f"âŒ Error analyzing {symbol}: {e}")
            return None

    def scan_portfolio(self):
        """Scan portfolio for opportunities"""
        portfolio = self.get_portfolio()
        opportunities = []

        if not portfolio:
            return opportunities

        for asset, data in portfolio.items():
            if asset == "USDT":
                continue

            opportunity = self.analyze_opportunity(data["symbol"])

            if opportunity and opportunity["signal"] != "HOLD":
                opportunity.update(
                    {
                        "asset": asset,
                        "balance": data["balance"],
                        "usd_value": data["usd_value"],
                    }
                )
                opportunities.append(opportunity)

        return opportunities

    def log_scan_result(self, opportunities):
        """Log scan results to file"""
        scan_result = {
            "timestamp": datetime.now().isoformat(),
            "scan_count": self.scan_count,
            "opportunities_found": len(opportunities),
            "opportunities": opportunities,
        }

        try:
            with open("logs/background_bot_scans.log", "a") as f:
                f.write(f"{json.dumps(scan_result)}\n")
        except Exception as e:
            print(f"âŒ Error logging scan result: {e}")

    def log_bot_event(self, event, data=None):
        """Log bot events"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "data": data,
        }

        try:
            with open("logs/background_bot_events.log", "a") as f:
                f.write(f"{json.dumps(log_entry)}\n")
        except:
            pass

    def run_continuous(self):
        """Run continuous scanning loop"""
        self.running = True
        print("ðŸš€ Background Trading Bot Started")
        print(f"ðŸ“Š Scan Interval: {SCAN_INTERVAL} seconds")
        print(f"ðŸ”— Mode: {'Testnet' if USE_TESTNET else 'Live Trading'}")
        print("=" * 50)

        self.log_bot_event(
            "bot_started", {"scan_interval": SCAN_INTERVAL, "testnet": USE_TESTNET}
        )

        try:
            while self.running:
                self.scan_count += 1
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                print(f"\nðŸ”„ [{current_time}] Scan #{self.scan_count}")

                # Perform scan
                opportunities = self.scan_portfolio()

                # Log results
                self.log_scan_result(opportunities)

                # Display results
                if opportunities:
                    print(f"ðŸŽ¯ Found {len(opportunities)} trading opportunities:")
                    for opp in opportunities:
                        print(
                            f"   {opp['asset']}: {opp['signal']} "
                            f"({opp['confidence']:.1%} confidence, "
                            f"{opp['change_pct']:+.2f}% change)"
                        )
                else:
                    print("ðŸ˜´ No trading opportunities found")

                # Wait for next scan
                print(f"â±ï¸  Waiting {SCAN_INTERVAL} seconds until next scan...")
                time.sleep(SCAN_INTERVAL)

        except KeyboardInterrupt:
            print(f"\nðŸ›‘ Bot stopped by user after {self.scan_count} scans")
        except Exception as e:
            print(f"\nâŒ Unexpected error: {e}")
        finally:
            self.running = False
            self.log_bot_event("bot_stopped", {"final_scan_count": self.scan_count})
            print("ðŸ”´ Background Trading Bot Stopped")


def main():
    """Main entry point"""
    print("ðŸŽ¯ Background Crypto Trading Bot")
    print("=" * 40)

    # Validate configuration
    if not API_KEY or not API_SECRET:
        print("âŒ Error: BINANCE_API_KEY and BINANCE_API_SECRET must be set")
        return

    if not BINANCE_AVAILABLE:
        print("âŒ Error: python-binance library not available")
        return

    # Create and run bot
    bot = BackgroundTradingBot()

    if bot.client:
        bot.run_continuous()
    else:
        print("âŒ Failed to initialize Binance client")


if __name__ == "__main__":
    main()

