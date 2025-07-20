import os
from datetime import datetime
from typing import Dict, Any
import logging

try:
    from binance.client import Client
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    Client = None  # type: ignore

class PortfolioManager:
    def __init__(self, api_key: str | None = None, api_secret: str | None = None, use_testnet: bool = None):
        # Auto-detect testnet mode from environment if not specified
        if use_testnet is None:
            use_testnet = os.getenv("USE_TESTNET", "true").lower() == "true"
        
        self._use_testnet = use_testnet
        self._live = BINANCE_AVAILABLE and api_key and api_secret
        self._client = None
        self._last_portfolio = {}
        self._last_update = None
        
        if self._live:
            try:
                self._client = Client(api_key, api_secret)
                if use_testnet:
                    self._client.API_URL = "https://testnet.binance.vision/api"
                
                # Test connection
                self._client.get_server_time()
                print(f"✅ Portfolio Manager connected to {'TESTNET' if use_testnet else 'LIVE'}")
            except Exception as e:
                print(f"❌ Portfolio Manager connection failed: {e}")
                self._live = False
                self._client = None

    def get_portfolio(self) -> Dict[str, Dict[str, Any]]:
        if self._live and self._client:
            try:
                portfolio = self._fetch_live_portfolio()
                self._last_portfolio = portfolio
                self._last_update = datetime.now()
                return portfolio
            except Exception as e:
                print(f"❌ Error fetching live portfolio: {e}")
                # Return cached portfolio if available
                if self._last_portfolio:
                    print("⚠️ Using cached portfolio data")
                    return self._last_portfolio
        
        print("⚠️ Using mock portfolio data")
        return self._mock_portfolio()

    def _fetch_live_portfolio(self) -> Dict[str, Dict[str, Any]]:
        """Fetch live portfolio from Binance API"""
        try:
            # Get account info
            account = self._client.get_account()
            
            # Get all current prices
            tickers = {}
            try:
                ticker_data = self._client.get_all_tickers()
                tickers = {t["symbol"]: float(t["price"]) for t in ticker_data}
            except Exception as e:
                print(f"⚠️ Could not fetch ticker prices: {e}")
                # Fallback prices
                tickers = {
                    "BTCUSDT": 117000.0,
                    "ETHUSDT": 4000.0,
                    "BNBUSDT": 600.0
                }
            
            portfolio: Dict[str, Dict[str, Any]] = {}
            
            # Process all balances
            for balance in account["balances"]:
                asset = balance["asset"]
                free = float(balance["free"] or 0)
                locked = float(balance["locked"] or 0)
                total = free + locked
                
                # Skip assets with zero balance (but keep small amounts that might be dust)
                if total < 0.00000001:
                    continue
                
                # Determine price for the asset
                price = 1.0  # Default for stablecoins
                
                if asset == "USDT" or asset == "BUSD" or asset == "USDC":
                    price = 1.0
                else:
                    # Try different quote currencies to find price
                    for quote in ["USDT", "BUSD", "USDC", "BTC", "ETH"]:
                        symbol = f"{asset}{quote}"
                        if symbol in tickers:
                            price = tickers[symbol]
                            
                            # Convert to USDT if priced in BTC/ETH
                            if quote == "BTC" and "BTCUSDT" in tickers:
                                price = price * tickers["BTCUSDT"]
                            elif quote == "ETH" and "ETHUSDT" in tickers:
                                price = price * tickers["ETHUSDT"]
                            
                            break
                
                # Calculate 24h change (simplified - you could enhance this)
                change = 0.0
                if asset != "USDT" and asset != "BUSD" and asset != "USDC":
                    try:
                        # Get 24hr ticker stats for price change
                        ticker_24hr = self._client.get_ticker(symbol=f"{asset}USDT")
                        change = float(ticker_24hr.get("priceChangePercent", 0.0))
                    except:
                        change = 0.0
                
                portfolio[asset] = {
                    "balance": total,
                    "free": free,
                    "locked": locked,
                    "price": price,
                    "value": total * price,
                    "change": change,
                    "last_updated": datetime.now().isoformat()
                }
            
            # Sort by value (highest first)
            portfolio = dict(sorted(portfolio.items(), key=lambda x: x[1]["value"], reverse=True))
            
            print(f"✅ Live portfolio fetched: {len(portfolio)} assets")
            return portfolio
            
        except Exception as e:
            print(f"❌ Error in _fetch_live_portfolio: {e}")
            raise

    def _mock_portfolio(self) -> Dict[str, Dict[str, Any]]:
        """Return mock portfolio data when live data is unavailable"""
        return {
            "USDT": {
                "balance": 1000.0, 
                "free": 1000.0,
                "locked": 0.0,
                "price": 1.0, 
                "value": 1000.0, 
                "change": 0.0,
                "last_updated": datetime.now().isoformat()
            },
            "BTC": {
                "balance": 0.01, 
                "free": 0.01,
                "locked": 0.0,
                "price": 117000.0, 
                "value": 1170.0, 
                "change": 2.5,
                "last_updated": datetime.now().isoformat()
            },
            "ETH": {
                "balance": 0.2, 
                "free": 0.2,
                "locked": 0.0,
                "price": 4000.0, 
                "value": 800.0, 
                "change": -1.2,
                "last_updated": datetime.now().isoformat()
            },
            "BNB": {
                "balance": 1.5, 
                "free": 1.5,
                "locked": 0.0,
                "price": 600.0, 
                "value": 900.0, 
                "change": 0.8,
                "last_updated": datetime.now().isoformat()
            },
        }

    def total_value(self) -> float:
        """Calculate total portfolio value in USDT"""
        try:
            portfolio = self.get_portfolio()
            return sum(v["value"] for v in portfolio.values())
        except Exception as e:
            print(f"❌ Error calculating total value: {e}")
            return 0.0

    def last_updated(self) -> str:
        """Return last update timestamp"""
        if self._last_update:
            return self._last_update.strftime("%Y-%m-%d %H:%M:%S")
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def refresh_portfolio(self) -> Dict[str, Dict[str, Any]]:
        """Force refresh portfolio data"""
        print("🔄 Refreshing portfolio data...")
        return self.get_portfolio()

    def get_asset_balance(self, asset: str) -> float:
        """Get balance for a specific asset"""
        try:
            portfolio = self.get_portfolio()
            return portfolio.get(asset, {}).get("balance", 0.0)
        except Exception:
            return 0.0

    def is_live(self) -> bool:
        """Check if using live data"""
        return self._live and self._client is not None

    def get_connection_status(self) -> str:
        """Get connection status string"""
        if self.is_live():
            mode = "🧪 TESTNET" if self._use_testnet else "🚀 LIVE"
            return f"✅ Connected to Binance {mode}"
        else:
            return "❌ Using mock data - API not connected"

    def get_trade_history(self, symbol: str = None, limit: int = 10) -> list:
        """Get recent trade history"""
        if not self.is_live():
            return []
        
        try:
            if symbol:
                trades = self._client.get_my_trades(symbol=symbol, limit=limit)
            else:
                # Get trades for all symbols (this might be slow)
                trades = []
                # For now, just get BTC trades as an example
                try:
                    btc_trades = self._client.get_my_trades(symbol="BTCUSDT", limit=5)
                    trades.extend(btc_trades)
                except:
                    pass
            
            # Format trades
            formatted_trades = []
            for trade in trades:
                formatted_trades.append({
                    "symbol": trade["symbol"],
                    "side": "BUY" if trade["isBuyer"] else "SELL",
                    "quantity": float(trade["qty"]),
                    "price": float(trade["price"]),
                    "value": float(trade["quoteQty"]),
                    "commission": float(trade["commission"]),
                    "time": datetime.fromtimestamp(trade["time"] / 1000).strftime("%H:%M:%S")
                })
            
            return formatted_trades
            
        except Exception as e:
            print(f"❌ Error fetching trade history: {e}")
            return []
