#!/usr/bin/env python3
"""
Dynamic Portfolio Scanner & Real-time WebSocket Monitor
Automatically scans your live exchange positions and monitors ALL relevant pairs
"""

import asyncio
import websockets
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ccxt
import logging
from pathlib import Path
import os
from collections import defaultdict, deque
import sqlite3
from typing import Dict, List, Set, Optional, Tuple
import signal
import sys
import time
from dataclasses import dataclass, asdict
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('live_portfolio_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Position:
    """Represents a trading position"""
    symbol: str
    amount: float
    avg_price: float
    current_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_percent: float = 0.0
    last_updated: str = ""

@dataclass
class TradingPair:
    """Represents a trading pair"""
    symbol: str
    base: str
    quote: str
    price: float = 0.0
    volume_24h: float = 0.0
    price_change_24h: float = 0.0
    is_portfolio_pair: bool = False
    last_updated: str = ""

class LivePortfolioScanner:
    """Scans live positions from multiple exchanges"""
    
    def __init__(self, config_file="exchange_config.json"):
        self.config_file = config_file
        self.exchanges = {}
        self.positions = {}
        self.load_exchange_config()
        self.setup_exchanges()
    
    def load_exchange_config(self):
        """Load exchange API configurations"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                # Create default config
                self.config = {
                    "binance": {
                        "api_key": os.getenv("BINANCE_API_KEY", ""),
                        "secret": os.getenv("BINANCE_SECRET", ""),
                        "sandbox": os.getenv("BINANCE_SANDBOX", "true").lower() == "true",
                        "enabled": True
                    },
                    "coinbase": {
                        "api_key": os.getenv("COINBASE_API_KEY", ""),
                        "secret": os.getenv("COINBASE_SECRET", ""),
                        "sandbox": os.getenv("COINBASE_SANDBOX", "true").lower() == "true",
                        "enabled": False
                    },
                    "kraken": {
                        "api_key": os.getenv("KRAKEN_API_KEY", ""),
                        "secret": os.getenv("KRAKEN_SECRET", ""),
                        "enabled": False
                    },
                    "kucoin": {
                        "api_key": os.getenv("KUCOIN_API_KEY", ""),
                        "secret": os.getenv("KUCOIN_SECRET", ""),
                        "passphrase": os.getenv("KUCOIN_PASSPHRASE", ""),
                        "sandbox": True,
                        "enabled": False
                    }
                }
                self.save_config()
                logger.info(f"Created default config file: {self.config_file}")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.config = {}
    
    def save_config(self):
        """Save exchange configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def setup_exchanges(self):
        """Initialize exchange connections"""
        for exchange_name, config in self.config.items():
            if not config.get("enabled", False):
                continue
            
            if not config.get("api_key") or not config.get("secret"):
                logger.warning(f"Missing API credentials for {exchange_name}")
                continue
            
            try:
                if exchange_name == "binance":
                    exchange = ccxt.binance({
                        'apiKey': config['api_key'],
                        'secret': config['secret'],
                        'sandbox': config.get('sandbox', True),
                        'enableRateLimit': True,
                        'options': {'defaultType': 'spot'}
                    })
                elif exchange_name == "coinbase":
                    exchange = ccxt.coinbasepro({
                        'apiKey': config['api_key'],
                        'secret': config['secret'],
                        'sandbox': config.get('sandbox', True),
                        'enableRateLimit': True
                    })
                elif exchange_name == "kraken":
                    exchange = ccxt.kraken({
                        'apiKey': config['api_key'],
                        'secret': config['secret'],
                        'enableRateLimit': True
                    })
                elif exchange_name == "kucoin":
                    exchange = ccxt.kucoin({
                        'apiKey': config['api_key'],
                        'secret': config['secret'],
                        'passphrase': config['passphrase'],
                        'sandbox': config.get('sandbox', True),
                        'enableRateLimit': True
                    })
                else:
                    continue
                
                # Test connection
                exchange.load_markets()
                self.exchanges[exchange_name] = exchange
                logger.info(f"✅ Connected to {exchange_name}")
                
            except Exception as e:
                logger.error(f"❌ Failed to connect to {exchange_name}: {e}")
    
    async def scan_all_positions(self) -> Dict[str, Position]:
        """Scan positions from all connected exchanges"""
        all_positions = {}
        
        for exchange_name, exchange in self.exchanges.items():
            try:
                logger.info(f"Scanning positions on {exchange_name}...")
                positions = await self.scan_exchange_positions(exchange, exchange_name)
                
                # Merge positions (same currency from different exchanges)
                for currency, position in positions.items():
                    if currency in all_positions:
                        # Combine positions
                        existing = all_positions[currency]
                        total_value = (existing.amount * existing.avg_price) + (position.amount * position.avg_price)
                        total_amount = existing.amount + position.amount
                        avg_price = total_value / total_amount if total_amount > 0 else 0
                        
                        all_positions[currency] = Position(
                            symbol=currency,
                            amount=total_amount,
                            avg_price=avg_price,
                            last_updated=datetime.now().isoformat()
                        )
                    else:
                        all_positions[currency] = position
                
                logger.info(f"Found {len(positions)} positions on {exchange_name}")
                
            except Exception as e:
                logger.error(f"Error scanning {exchange_name}: {e}")
        
        # Filter out dust positions (very small amounts)
        filtered_positions = {}
        for currency, position in all_positions.items():
            if position.amount * position.avg_price > 10:  # $10 minimum
                filtered_positions[currency] = position
            else:
                logger.debug(f"Filtering out dust position: {currency} (${position.amount * position.avg_price:.2f})")
        
        self.positions = filtered_positions
        logger.info(f"Total portfolio: {len(filtered_positions)} positions worth tracking")
        
        return filtered_positions
    
    async def scan_exchange_positions(self, exchange, exchange_name: str) -> Dict[str, Position]:
        """Scan positions from a specific exchange"""
        positions = {}
        
        try:
            # Get account balance
            balance = exchange.fetch_balance()
            
            for currency, amounts in balance.items():
                if currency in ['info', 'free', 'used', 'total']:
                    continue
                
                total_amount = amounts.get('total', 0)
                if total_amount <= 0:
                    continue
                
                # Try to get average price (this varies by exchange)
                avg_price = await self.estimate_avg_price(exchange, currency, exchange_name)
                
                position = Position(
                    symbol=currency,
                    amount=total_amount,
                    avg_price=avg_price,
                    last_updated=datetime.now().isoformat()
                )
                
                positions[currency] = position
                logger.debug(f"{exchange_name} - {currency}: {total_amount} @ ${avg_price:.4f}")
        
        except Exception as e:
            logger.error(f"Error fetching balance from {exchange_name}: {e}")
        
        return positions
    
    async def estimate_avg_price(self, exchange, currency: str, exchange_name: str) -> float:
        """Estimate average price for a currency"""
        try:
            # Try to get current price against USDT, BUSD, or USD
            quote_currencies = ['USDT', 'BUSD', 'USD', 'USDC']
            
            for quote in quote_currencies:
                symbol = f"{currency}/{quote}"
                try:
                    ticker = exchange.fetch_ticker(symbol)
                    return float(ticker['last'])
                except:
                    continue
            
            # If no direct pair found, try reverse
            for quote in quote_currencies:
                symbol = f"{quote}/{currency}"
                try:
                    ticker = exchange.fetch_ticker(symbol)
                    return 1.0 / float(ticker['last'])
                except:
                    continue
            
            # Default fallback
            return 1.0 if currency in ['USDT', 'BUSD', 'USD', 'USDC'] else 0.0
            
        except Exception as e:
            logger.debug(f"Could not estimate price for {currency}: {e}")
            return 1.0 if currency in ['USDT', 'BUSD', 'USD', 'USDC'] else 0.0
    
    def get_portfolio_currencies(self) -> Set[str]:
        """Get all currencies in portfolio"""
        return set(self.positions.keys())
    
    def save_positions_snapshot(self):
        """Save current positions to file"""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'positions': {k: asdict(v) for k, v in self.positions.items()}
        }
        
        with open(f"portfolio_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(snapshot, f, indent=2)

class DynamicWebSocketMonitor:
    """Dynamic WebSocket monitor that adapts to portfolio changes"""
    
    def __init__(self, portfolio_scanner: LivePortfolioScanner):
        self.portfolio_scanner = portfolio_scanner
        self.data_buffer = defaultdict(lambda: deque(maxlen=1000))
        self.db_manager = DatabaseManager()
        self.active_pairs = set()
        self.websocket_tasks = []
        self.running = False
        
        # Performance tracking
        self.stats = {
            'messages_received': 0,
            'pairs_monitored': 0,
            'last_portfolio_scan': 0,
            'portfolio_scan_interval': 300  # 5 minutes
        }
    
    async def get_relevant_trading_pairs(self) -> Set[str]:
        """Get all trading pairs relevant to current portfolio"""
        portfolio_currencies = self.portfolio_scanner.get_portfolio_currencies()
        if not portfolio_currencies:
            logger.warning("No portfolio currencies found")
            return set()
        
        relevant_pairs = set()
        
        # Get all possible pairs between portfolio currencies
        for exchange_name, exchange in self.portfolio_scanner.exchanges.items():
            try:
                markets = exchange.load_markets()
                
                for symbol, market in markets.items():
                    if not market.get('active', True):
                        continue
                    
                    base = market['base']
                    quote = market['quote']
                    
                    # Include if either base or quote is in portfolio
                    if base in portfolio_currencies or quote in portfolio_currencies:
                        # Convert to Binance format for WebSocket
                        binance_symbol = f"{base}{quote}"
                        relevant_pairs.add(binance_symbol)
                
                break  # Use first exchange for market discovery
                
            except Exception as e:
                logger.error(f"Error getting markets from {exchange_name}: {e}")
        
        logger.info(f"Found {len(relevant_pairs)} relevant trading pairs for currencies: {portfolio_currencies}")
        return relevant_pairs
    
    async def update_monitoring_pairs(self):
        """Update the pairs being monitored based on current portfolio"""
        new_pairs = await self.get_relevant_trading_pairs()
        
        if new_pairs != self.active_pairs:
            logger.info(f"Portfolio changed. Updating monitoring from {len(self.active_pairs)} to {len(new_pairs)} pairs")
            
            # Stop existing WebSocket connections
            await self.stop_websockets()
            
            # Update active pairs
            self.active_pairs = new_pairs
            self.stats['pairs_monitored'] = len(new_pairs)
            
            # Start new WebSocket connections
            if new_pairs:
                await self.start_websockets()
    
    async def start_websockets(self):
        """Start WebSocket connections for active pairs"""
        if not self.active_pairs:
            logger.warning("No active pairs to monitor")
            return
        
        # Split pairs into chunks for multiple connections
        pair_chunks = [list(self.active_pairs)[i:i+200] for i in range(0, len(self.active_pairs), 200)]
        
        for chunk_idx, pairs in enumerate(pair_chunks):
            task = asyncio.create_task(self.websocket_connection(pairs, chunk_idx))
            self.websocket_tasks.append(task)
            logger.info(f"Started WebSocket connection {chunk_idx + 1} for {len(pairs)} pairs")
    
    async def stop_websockets(self):
        """Stop all WebSocket connections"""
        for task in self.websocket_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.websocket_tasks:
            await asyncio.gather(*self.websocket_tasks, return_exceptions=True)
        
        self.websocket_tasks = []
        logger.info("Stopped all WebSocket connections")
    
    async def websocket_connection(self, pairs: List[str], connection_id: int):
        """Handle WebSocket connection for a group of pairs"""
        streams = [f"{pair.lower()}@ticker" for pair in pairs]
        url = f"wss://stream.binance.com:9443/ws/{'/'.join(streams)}"
        
        while self.running:
            try:
                logger.info(f"Connecting WebSocket {connection_id} to {len(pairs)} pairs...")
                
                async with websockets.connect(url) as websocket:
                    logger.info(f"WebSocket {connection_id} connected")
                    
                    async for message in websocket:
                        if not self.running:
                            break
                        
                        try:
                            data = json.loads(message)
                            await self.handle_price_update(data)
                            self.stats['messages_received'] += 1
                            
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON: {message[:100]}")
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
            
            except websockets.exceptions.ConnectionClosed:
                if self.running:
                    logger.warning(f"WebSocket {connection_id} disconnected, reconnecting in 5s...")
                    await asyncio.sleep(5)
            except Exception as e:
                if self.running:
                    logger.error(f"WebSocket {connection_id} error: {e}, reconnecting in 10s...")
                    await asyncio.sleep(10)
    
    async def handle_price_update(self, data: dict):
        """Handle incoming price update"""
        try:
            symbol = data.get('s')  # Symbol
            if not symbol:
                return
            
            price_data = {
                'timestamp': time.time(),
                'symbol': symbol,
                'price': float(data.get('c', 0)),
                'volume': float(data.get('v', 0)),
                'high': float(data.get('h', 0)),
                'low': float(data.get('l', 0)),
                'change_24h': float(data.get('P', 0)),
                'count': int(data.get('n', 0))
            }
            
            # Add to buffer
            self.data_buffer[symbol].append(price_data)
            
            # Update portfolio positions with current prices
            await self.update_portfolio_values(symbol, price_data['price'])
            
            # Periodic database save (every 10th message per symbol)
            if self.stats['messages_received'] % 10 == 0:
                self.db_manager.save_price_tick(symbol, price_data)
        
        except Exception as e:
            logger.error(f"Error handling price update: {e}")
    
    async def update_portfolio_values(self, symbol: str, price: float):
        """Update portfolio position values with current market price"""
        try:
            # Extract base and quote from symbol
            for currency in self.portfolio_scanner.positions.keys():
                if symbol.startswith(currency) or symbol.endswith(currency):
                    position = self.portfolio_scanner.positions[currency]
                    
                    # Determine if this is the right price for this currency
                    if symbol.startswith(currency) and symbol.endswith('USDT'):
                        # Direct USD price
                        position.current_price = price
                    elif symbol.endswith(currency) and symbol.startswith('USDT'):
                        # Inverse USD price
                        position.current_price = 1.0 / price if price > 0 else 0
                    
                    # Calculate unrealized P&L
                    if position.current_price > 0:
                        position.market_value = position.amount * position.current_price
                        position.unrealized_pnl = position.market_value - (position.amount * position.avg_price)
                        position.unrealized_pnl_percent = (position.unrealized_pnl / (position.amount * position.avg_price)) * 100 if position.avg_price > 0 else 0
                        position.last_updated = datetime.now().isoformat()
        
        except Exception as e:
            logger.debug(f"Error updating portfolio values: {e}")
    
    async def periodic_portfolio_rescan(self):
        """Periodically rescan portfolio for changes"""
        while self.running:
            try:
                current_time = time.time()
                
                if current_time - self.stats['last_portfolio_scan'] > self.stats['portfolio_scan_interval']:
                    logger.info("Rescanning portfolio for changes...")
                    
                    # Rescan positions
                    await self.portfolio_scanner.scan_all_positions()
                    
                    # Update monitoring pairs
                    await self.update_monitoring_pairs()
                    
                    # Save snapshot
                    self.portfolio_scanner.save_positions_snapshot()
                    
                    self.stats['last_portfolio_scan'] = current_time
                    
                    # Print portfolio summary
                    await self.print_portfolio_summary()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in periodic portfolio rescan: {e}")
                await asyncio.sleep(60)
    
    async def print_portfolio_summary(self):
        """Print current portfolio summary"""
        try:
            total_value = 0
            total_pnl = 0
            
            logger.info("=" * 80)
            logger.info("📊 LIVE PORTFOLIO SUMMARY")
            logger.info("=" * 80)
            
            for currency, position in self.portfolio_scanner.positions.items():
                if position.current_price > 0:
                    total_value += position.market_value
                    total_pnl += position.unrealized_pnl
                    
                    pnl_color = "🟢" if position.unrealized_pnl >= 0 else "🔴"
                    
                    logger.info(
                        f"{currency:>8s}: {position.amount:>12.4f} @ ${position.current_price:>10.4f} "
                        f"= ${position.market_value:>12.2f} {pnl_color} "
                        f"{position.unrealized_pnl_percent:>+7.2f}% (${position.unrealized_pnl:>+10.2f})"
                    )
            
            logger.info("-" * 80)
            logger.info(f"💰 Total Portfolio Value: ${total_value:,.2f}")
            logger.info(f"📈 Total Unrealized P&L: ${total_pnl:+,.2f} ({(total_pnl/total_value)*100:+.2f}%)")
            logger.info(f"📡 Monitoring {self.stats['pairs_monitored']} trading pairs")
            logger.info(f"🔄 Messages received: {self.stats['messages_received']:,}")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Error printing portfolio summary: {e}")
    
    async def start_monitoring(self):
        """Start the complete monitoring system"""
        self.running = True
        logger.info("🚀 Starting Dynamic Portfolio Monitor...")
        
        # Initial portfolio scan
        await self.portfolio_scanner.scan_all_positions()
        
        # Set up monitoring pairs
        await self.update_monitoring_pairs()
        
        # Start periodic tasks
        rescan_task = asyncio.create_task(self.periodic_portfolio_rescan())
        status_task = asyncio.create_task(self.periodic_status_report())
        
        try:
            # Run until interrupted
            await asyncio.gather(rescan_task, status_task)
        except KeyboardInterrupt:
            logger.info("📴 Stopping monitor...")
            self.running = False
            await self.stop_websockets()
            rescan_task.cancel()
            status_task.cancel()
    
    async def periodic_status_report(self):
        """Periodic status reporting"""
        while self.running:
            await asyncio.sleep(300)  # Every 5 minutes
            if self.running:
                await self.print_portfolio_summary()

class DatabaseManager:
    """Enhanced database manager for dynamic data"""
    
    def __init__(self, db_path="live_portfolio_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with enhanced schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_ticks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                symbol TEXT,
                price REAL,
                volume REAL,
                high REAL,
                low REAL,
                change_24h REAL,
                count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                currency TEXT,
                amount REAL,
                avg_price REAL,
                current_price REAL,
                market_value REAL,
                unrealized_pnl REAL,
                unrealized_pnl_percent REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_symbol_time ON price_ticks(symbol, timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_portfolio_currency_time ON portfolio_snapshots(currency, timestamp)')
        
        conn.commit()
        conn.close()
    
    def save_price_tick(self, symbol: str, data: dict):
        """Save price tick to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO price_ticks (timestamp, symbol, price, volume, high, low, change_24h, count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['timestamp'], symbol, data['price'], data['volume'],
                data['high'], data['low'], data['change_24h'], data['count']
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving price tick: {e}")
    
    def save_portfolio_snapshot(self, positions: Dict[str, Position]):
        """Save portfolio snapshot to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = time.time()
            
            for currency, position in positions.items():
                cursor.execute('''
                    INSERT INTO portfolio_snapshots 
                    (timestamp, currency, amount, avg_price, current_price, market_value, unrealized_pnl, unrealized_pnl_percent)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp, currency, position.amount, position.avg_price,
                    position.current_price, position.market_value,
                    position.unrealized_pnl, position.unrealized_pnl_percent
                ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving portfolio snapshot: {e}")

async def main():
    """Main function to run the dynamic monitor"""
    
    # Create configuration helper
    print("🔧 Setting up Dynamic Portfolio Monitor...")
    print("This tool will scan your live exchange positions and monitor ALL relevant trading pairs.")
    print()
    
    # Initialize components
    scanner = LivePortfolioScanner()
    monitor = DynamicWebSocketMonitor(scanner)
    
    # Handle graceful shutdown
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal")
        monitor.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start monitoring
        await monitor.start_monitoring()
    except Exception as e:
        logger.error(f"Monitor error: {e}")
    finally:
        logger.info("Monitor stopped")

if __name__ == "__main__":
    asyncio.run(main())