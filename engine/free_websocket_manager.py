"""
Free WebSocket Implementation for Binance
Replaces ccxt-pro with python-binance library (100% free)
Provides real-time price data, klines, and account updates without API rate limits
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from collections import defaultdict, deque
from datetime import datetime
import threading

# Free libraries - no ccxt-pro needed!
try:
    from binance import AsyncClient, BinanceSocketManager
    from binance.enums import KLINE_INTERVAL_1HOUR, KLINE_INTERVAL_1MINUTE
    BINANCE_AVAILABLE = True
except ImportError:
    # Fallback if python-binance not installed
    AsyncClient = None
    BinanceSocketManager = None
    BINANCE_AVAILABLE = False

log = logging.getLogger("FreeBinanceWebSocket")


class FreeBinanceWebSocketManager:
    """
    100% Free WebSocket manager using python-binance library
    No API rate limits, no ccxt-pro license required
    Real-time data for trading without API polling
    """
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.running = False
        self.connected = False
        
        # Real-time data storage (thread-safe)
        self._lock = threading.Lock()
        self.tickers: Dict[str, Dict[str, Any]] = {}
        self.klines: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.account_balance: Dict[str, float] = {}
        
        # Subscribed symbols
        self.ticker_symbols: set = set()
        self.kline_symbols: set = set()
        
        # WebSocket managers
        self.client: Optional[AsyncClient] = None
        self.bm: Optional[BinanceSocketManager] = None
        self.socket_tasks: List[asyncio.Task] = []
        
        # Connection status
        self.last_ticker_update = 0
        self.last_kline_update = 0
        self.last_balance_update = 0
        self.connection_errors = 0
        self.max_connection_errors = 5
        
        # Balance caching to reduce API calls
        self.cached_balance = {}
        self.balance_cache_ttl = 30  # Cache balance for 30 seconds
        self.last_balance_fetch = 0
        
        log.info("FreeBinanceWebSocketManager initialized")
    
    async def start(self, ticker_symbols: List[str] = None, kline_symbols: List[str] = None):
        """Start WebSocket connections with specified symbols"""
        if not BINANCE_AVAILABLE:
            log.error("python-binance not available. Install with: pip install python-binance")
            return False
            
        try:
            # Initialize Binance client (works without API keys for public data)
            if self.api_key and self.api_secret:
                self.client = await AsyncClient.create(api_key=self.api_key, api_secret=self.api_secret)
                log.info("Authenticated Binance client created")
            else:
                self.client = await AsyncClient.create()
                log.info("Public Binance client created (no authentication)")
            
            self.bm = BinanceSocketManager(self.client)
            
            # Start ticker streams
            if ticker_symbols:
                self.ticker_symbols.update(ticker_symbols)
                await self._start_ticker_stream()
            
            # Start kline streams  
            if kline_symbols:
                self.kline_symbols.update(kline_symbols)
                await self._start_kline_stream()
            
            # Start user data stream (if authenticated)
            if self.api_key and self.api_secret:
                await self._start_user_stream()
            
            self.running = True
            self.connected = True
            self.connection_errors = 0
            
            log.info(f"WebSocket started: {len(self.ticker_symbols)} tickers, {len(self.kline_symbols)} klines")
            return True
            
        except Exception as e:
            log.error(f"Failed to start WebSocket: {e}")
            self.connection_errors += 1
            return False
    
    async def _start_ticker_stream(self):
        """Start 24hr ticker WebSocket stream for all symbols"""
        try:
            symbols = [s.lower() for s in self.ticker_symbols]
            ts = self.bm.ticker_socket(symbols)
            
            async def handle_ticker_message(msg):
                try:
                    with self._lock:
                        symbol = msg['s']  # BTCUSDT format
                        # Convert to ccxt format: BTC/USDT
                        if symbol.endswith('USDT'):
                            formatted_symbol = f"{symbol[:-4]}/USDT"
                        elif symbol.endswith('BTC'):
                            formatted_symbol = f"{symbol[:-3]}/BTC"
                        elif symbol.endswith('ETH'):
                            formatted_symbol = f"{symbol[:-3]}/ETH"
                        else:
                            formatted_symbol = symbol
                        
                        self.tickers[formatted_symbol] = {
                            'symbol': formatted_symbol,
                            'last': float(msg['c']),      # Current price
                            'close': float(msg['c']),     # Close price
                            'bid': float(msg['b']),       # Best bid
                            'ask': float(msg['a']),       # Best ask
                            'high': float(msg['h']),      # 24hr high
                            'low': float(msg['l']),       # 24hr low
                            'volume': float(msg['v']),    # 24hr volume
                            'change': float(msg['P']),    # 24hr price change %
                            'timestamp': int(msg['E']),   # Event time
                        }
                        self.last_ticker_update = time.time()
                        
                except Exception as e:
                    log.error(f"Error processing ticker message: {e}")
            
            # Start the ticker WebSocket
            task = asyncio.create_task(self._run_socket(ts, handle_ticker_message))
            self.socket_tasks.append(task)
            
        except Exception as e:
            log.error(f"Failed to start ticker stream: {e}")
    
    async def _start_kline_stream(self):
        """Start kline (OHLCV) WebSocket stream"""
        try:
            for symbol in self.kline_symbols:
                symbol_lower = symbol.replace('/', '').lower()  # BTC/USDT -> btcusdt
                ks = self.bm.kline_socket(symbol_lower, KLINE_INTERVAL_1HOUR)
                
                async def handle_kline_message(msg, original_symbol=symbol):
                    try:
                        kline = msg['k']
                        if kline['x']:  # Only process completed klines
                            with self._lock:
                                ohlcv = [
                                    int(kline['t']),          # Open time
                                    float(kline['o']),        # Open
                                    float(kline['h']),        # High  
                                    float(kline['l']),        # Low
                                    float(kline['c']),        # Close
                                    float(kline['v'])         # Volume
                                ]
                                self.klines[original_symbol].append(ohlcv)
                                self.last_kline_update = time.time()
                                
                    except Exception as e:
                        log.error(f"Error processing kline message for {original_symbol}: {e}")
                
                # Start the kline WebSocket for this symbol
                task = asyncio.create_task(self._run_socket(ks, handle_kline_message))
                self.socket_tasks.append(task)
                
        except Exception as e:
            log.error(f"Failed to start kline stream: {e}")
    
    async def _start_user_stream(self):
        """Start user data stream for account updates (requires API keys)"""
        try:
            us = self.bm.user_socket()
            
            async def handle_user_message(msg):
                try:
                    with self._lock:
                        if msg.get('e') == 'balanceUpdate':
                            # Balance update
                            asset = msg['a']
                            balance = float(msg['d'])
                            self.account_balance[asset] = balance
                            
                        elif msg.get('e') == 'outboundAccountPosition':
                            # Account position update
                            for balance in msg.get('B', []):
                                asset = balance['a']
                                free = float(balance['f'])
                                locked = float(balance['l'])
                                self.account_balance[asset] = free + locked
                                
                            self.last_balance_update = time.time()
                                
                except Exception as e:
                    log.error(f"Error processing user message: {e}")
            
            # Start the user data WebSocket
            task = asyncio.create_task(self._run_socket(us, handle_user_message))
            self.socket_tasks.append(task)
            
        except Exception as e:
            log.error(f"Failed to start user stream: {e}")
    
    async def _run_socket(self, socket, handler):
        """Run a WebSocket with automatic reconnection"""
        while self.running:
            try:
                async with socket as stream:
                    async for msg in stream:
                        if not self.running:
                            break
                        await handler(msg)
                        
            except Exception as e:
                log.error(f"WebSocket error: {e}")
                self.connection_errors += 1
                
                if self.connection_errors >= self.max_connection_errors:
                    log.error("Too many connection errors, stopping WebSocket")
                    self.connected = False
                    break
                
                # Exponential backoff reconnection
                await asyncio.sleep(min(2 ** self.connection_errors, 60))
    
    async def stop(self):
        """Stop all WebSocket connections"""
        self.running = False
        self.connected = False
        
        # Cancel all socket tasks
        for task in self.socket_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.socket_tasks:
            await asyncio.gather(*self.socket_tasks, return_exceptions=True)
        
        # Close the client
        if self.client:
            await self.client.close_connection()
        
        log.info("WebSocket connections stopped")
    
    def is_connected(self) -> bool:
        """Check if WebSocket is connected and receiving data"""
        now = time.time()
        ticker_fresh = (now - self.last_ticker_update) < 60  # Data within last minute
        return self.connected and ticker_fresh
    
    def get_tickers(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Get real-time ticker data (replaces expensive API calls)"""
        with self._lock:
            if symbols is None:
                return self.tickers.copy()
            
            result = {}
            for symbol in symbols:
                if symbol in self.tickers:
                    result[symbol] = self.tickers[symbol]
            return result
    
    def get_klines(self, symbol: str, limit: int = 500) -> List[List[float]]:
        """Get real-time kline data (replaces expensive API calls)"""
        with self._lock:
            if symbol in self.klines:
                klines_deque = self.klines[symbol]
                # Return last 'limit' klines
                return list(klines_deque)[-limit:] if len(klines_deque) >= limit else list(klines_deque)
            return []
    
    def get_balance(self) -> Dict[str, float]:
        """Get real-time balance data (requires authentication)"""
        with self._lock:
            return self.account_balance.copy()
    
    def get_total_balance_usdt(self, exchange_client=None) -> float:
        """Calculate total balance in USDT using real-time prices"""
        with self._lock:
            total_usdt = self.account_balance.get('USDT', 0.0)
            
            # Add crypto values converted to USDT using WebSocket prices
            for asset, amount in self.account_balance.items():
                if asset != 'USDT' and amount > 0:
                    # Try to find price from WebSocket tickers
                    symbol_key = f"{asset}/USDT"
                    if symbol_key in self.tickers:
                        price = self.tickers[symbol_key].get('last', 0)
                        total_usdt += amount * price
                    elif exchange_client:
                        # Fallback to REST API only if WebSocket data not available
                        try:
                            ticker = exchange_client.fetch_ticker(symbol_key)
                            price = ticker.get('last') or ticker.get('close') or 0
                            total_usdt += amount * price
                        except:
                            pass
            
            return total_usdt
    
    def get_formatted_balance(self, exchange_client=None) -> Dict[str, Any]:
        """Get balance in the format expected by the API with intelligent caching"""
        now = time.time()
        
        with self._lock:
            # If WebSocket balance is available and recent, use it
            if self.account_balance and (now - self.last_balance_update) < 60:
                balance_copy = self.account_balance.copy()
                total_usdt = self.get_total_balance_usdt(exchange_client)
                balance_copy['total_usdt'] = total_usdt
                return balance_copy
            
            # If we have cached balance and it's still valid, use it
            if self.cached_balance and (now - self.last_balance_fetch) < self.balance_cache_ttl:
                return self.cached_balance.copy()
            
            # Otherwise, we need to fetch from API (this will be handled by calling code)
            return None
    
    def cache_balance_data(self, balance_data: Dict[str, Any]) -> None:
        """Cache balance data to reduce API calls"""
        with self._lock:
            self.cached_balance = balance_data.copy()
            self.last_balance_fetch = time.time()
    
    def add_symbols(self, ticker_symbols: List[str] = None, kline_symbols: List[str] = None):
        """Add new symbols to existing streams (requires restart)"""
        restart_needed = False
        
        if ticker_symbols:
            new_tickers = set(ticker_symbols) - self.ticker_symbols
            if new_tickers:
                self.ticker_symbols.update(new_tickers)
                restart_needed = True
        
        if kline_symbols:
            new_klines = set(kline_symbols) - self.kline_symbols  
            if new_klines:
                self.kline_symbols.update(new_klines)
                restart_needed = True
        
        return restart_needed
    
    def get_status(self) -> Dict[str, Any]:
        """Get WebSocket connection status"""
        now = time.time()
        return {
            "connected": self.connected,
            "running": self.running,
            "ticker_symbols": len(self.ticker_symbols),
            "kline_symbols": len(self.kline_symbols),
            "ticker_count": len(self.tickers),
            "kline_count": sum(len(deque) for deque in self.klines.values()),
            "last_ticker_update": self.last_ticker_update,
            "last_kline_update": self.last_kline_update,
            "ticker_age_seconds": now - self.last_ticker_update if self.last_ticker_update else None,
            "kline_age_seconds": now - self.last_kline_update if self.last_kline_update else None,
            "connection_errors": self.connection_errors,
            "authenticated": bool(self.api_key and self.api_secret),
            "balance_assets": len(self.account_balance)
        }


# Global instance
_free_ws_manager: Optional[FreeBinanceWebSocketManager] = None


def get_free_websocket_manager() -> FreeBinanceWebSocketManager:
    """Get global WebSocket manager instance"""
    global _free_ws_manager
    if _free_ws_manager is None:
        _free_ws_manager = FreeBinanceWebSocketManager()
    return _free_ws_manager


async def initialize_free_websocket_data(symbols: List[str], kline_symbols: List[str] = None, 
                                       api_key: str = None, api_secret: str = None):
    """Initialize free WebSocket data streams"""
    manager = get_free_websocket_manager()
    
    # Set API credentials if provided
    if api_key and api_secret:
        manager.api_key = api_key
        manager.api_secret = api_secret
    
    # Start WebSocket streams
    success = await manager.start(
        ticker_symbols=symbols,
        kline_symbols=kline_symbols or symbols[:10]  # Limit klines to prevent overload
    )
    
    if success:
        log.info(f"Free WebSocket initialized: {len(symbols)} symbols")
    else:
        log.error("Failed to initialize free WebSocket")
    
    return success


# Compatibility functions for existing code
def get_websocket_manager():
    """Compatibility function - returns free WebSocket manager"""
    return get_free_websocket_manager()


async def initialize_websocket_data(*args, **kwargs):
    """Compatibility function - initializes free WebSocket"""
    return await initialize_free_websocket_data(*args, **kwargs)
