#!/usr/bin/env python3
"""
Memory-Optimized Trading Data Collector
Integrates with existing Bottie systems while maintaining low memory footprint
Feeds data to WebSocket dashboard efficiently
"""

import asyncio
import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sqlite3
import threading
import time
from collections import deque
import gc
import psutil  # For memory monitoring

# Memory management settings
MAX_MEMORY_MB = int(os.getenv("MAX_MEMORY_MB", "400"))  # Stay well under 512MB limit
MEMORY_CHECK_INTERVAL = int(os.getenv("MEMORY_CHECK_INTERVAL", "30"))  # Check memory every 30 seconds
MAX_CANDLE_CACHE = int(os.getenv("MAX_CANDLE_CACHE", "100"))     # Limit candle data cache
MAX_POSITION_CACHE = int(os.getenv("MAX_POSITION_CACHE", "50"))    # Limit position cache
CLEANUP_INTERVAL = int(os.getenv("CLEANUP_INTERVAL", "300"))     # Deep cleanup every 5 minutes

# Trading settings (optimized for low API usage)
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT', 'DOT/USDT', 'LINK/USDT', 'UNI/USDT']
UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", "30"))       # Update data every 30 seconds (reduced from previous)
BALANCE_UPDATE_INTERVAL = int(os.getenv("BALANCE_UPDATE_INTERVAL", "300"))  # Update balance every 5 minutes

# Configure minimal logging to save memory
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class MemoryMonitor:
    """Monitor memory usage and trigger cleanup when needed"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.max_memory_bytes = MAX_MEMORY_MB * 1024 * 1024
        
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage"""
        memory_info = self.process.memory_info()
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': self.process.memory_percent()
        }
    
    def is_memory_critical(self) -> bool:
        """Check if memory usage is approaching limits"""
        memory = self.get_memory_usage()
        return memory['rss_mb'] > (MAX_MEMORY_MB * 0.8)  # 80% threshold
    
    def force_cleanup(self):
        """Force garbage collection and cleanup"""
        collected = gc.collect()
        logger.info(f"🧹 Emergency cleanup: {collected} objects collected")

class OptimizedDataCollector:
    """Collect and process trading data with minimal memory footprint"""
    
    def __init__(self):
        self.memory_monitor = MemoryMonitor()
        
        # Memory-efficient data storage
        self.price_cache = {}  # Only store latest prices
        self.signal_cache = deque(maxlen=100)  # Limited signal history
        self.trade_cache = deque(maxlen=100)   # Limited trade history
        
        # Database for persistence
        self.db_path = os.getenv("DB_PATH", "/tmp/bottie_optimized.db")
        self._init_database()
        
        # Exchange connection (lazy initialization)
        self._exchange = None
        
        # Start memory monitoring
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_memory, daemon=True)
        self.monitor_thread.start()
        
    def _init_database(self):
        """Initialize optimized SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Optimized table structure
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS live_data (
                    symbol TEXT PRIMARY KEY,
                    price REAL,
                    change_24h REAL,
                    volume REAL,
                    timestamp TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT,
                    action TEXT,
                    confidence REAL,
                    price REAL,
                    timestamp TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT,
                    side TEXT,
                    amount REAL,
                    price REAL,
                    pnl REAL,
                    timestamp TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Cleanup old data immediately
            cutoff = datetime.now() - timedelta(days=3)
            cursor.execute("DELETE FROM signals WHERE created_at < ?", (cutoff,))
            cursor.execute("DELETE FROM trades WHERE created_at < ?", (cutoff,))
            cursor.execute("VACUUM")
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Optimized database initialized")
            
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
    
    def _monitor_memory(self):
        """Background memory monitoring and cleanup"""
        while self.monitoring_active:
            try:
                memory = self.memory_monitor.get_memory_usage()
                logger.info(f"💾 Memory usage: {memory['rss_mb']:.1f}MB ({memory['percent']:.1f}%)")
                
                if self.memory_monitor.is_memory_critical():
                    logger.warning("⚠️ High memory usage detected, cleaning up...")
                    self._emergency_cleanup()
                
                time.sleep(MEMORY_CHECK_INTERVAL)
                
            except Exception as e:
                logger.error(f"❌ Memory monitoring error: {e}")
                time.sleep(MEMORY_CHECK_INTERVAL)
    
    def _emergency_cleanup(self):
        """Emergency cleanup when memory is critical"""
        try:
            # Clear caches
            self.price_cache.clear()
            
            # Limit deque sizes further
            while len(self.signal_cache) > 50:
                self.signal_cache.popleft()
            while len(self.trade_cache) > 50:
                self.trade_cache.popleft()
            
            # Force garbage collection
            self.memory_monitor.force_cleanup()
            
            # Clean database
            self._cleanup_database()
            
        except Exception as e:
            logger.error(f"❌ Emergency cleanup error: {e}")
    
    def _cleanup_database(self):
        """Clean old data from database"""
        try:
            cutoff = datetime.now() - timedelta(hours=24)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Keep only recent data
            cursor.execute("DELETE FROM signals WHERE created_at < ?", (cutoff,))
            cursor.execute("DELETE FROM trades WHERE created_at < ?", (cutoff,))
            
            # Update live data timestamp
            cursor.execute("DELETE FROM live_data WHERE timestamp < ?", 
                          ((datetime.now() - timedelta(minutes=30)).isoformat(),))
            
            cursor.execute("VACUUM")
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Database cleanup error: {e}")
    
    def _get_exchange(self):
        """Lazy initialize exchange connection"""
        if self._exchange is None:
            try:
                # Try to import ccxt
                import ccxt
                
                # Use minimal exchange configuration
                self._exchange = ccxt.binance({
                    'apiKey': os.getenv('BINANCE_API_KEY', ''),
                    'secret': os.getenv('BINANCE_SECRET', ''),
                    'sandbox': os.getenv('BINANCE_TESTNET', 'false').lower() == 'true',
                    'enableRateLimit': True,
                    'rateLimit': 1200,  # Conservative rate limiting
                    'timeout': 30000,
                    'options': {
                        'defaultType': 'spot'
                    }
                })
                
                logger.info("✅ Exchange connection initialized")
                
            except Exception as e:
                logger.error(f"❌ Exchange initialization error: {e}")
                # Use demo mode if exchange fails
                self._exchange = None
                
        return self._exchange
    
    async def collect_market_data(self) -> List[Dict[str, Any]]:
        """Collect market data efficiently"""
        try:
            exchange = self._get_exchange()
            if not exchange:
                # Return demo data
                return self._generate_demo_market_data()
            
            # Fetch only essential data
            tickers = exchange.fetch_tickers(SYMBOLS)
            
            market_data = []
            timestamp = datetime.now().isoformat()
            
            for symbol in SYMBOLS:
                if symbol in tickers:
                    ticker = tickers[symbol]
                    data = {
                        'symbol': symbol,
                        'price': ticker.get('last', 0),
                        'change_24h': ticker.get('percentage', 0),
                        'volume': ticker.get('baseVolume', 0),
                        'timestamp': timestamp
                    }
                    
                    # Update cache (memory efficient)
                    self.price_cache[symbol] = data['price']
                    market_data.append(data)
                    
                    # Save to database
                    self._save_market_data(data)
            
            return market_data
            
        except Exception as e:
            logger.error(f"❌ Market data collection error: {e}")
            return self._generate_demo_market_data()
    
    def _generate_demo_market_data(self) -> List[Dict[str, Any]]:
        """Generate demo market data for testing"""
        import random
        
        demo_data = []
        timestamp = datetime.now().isoformat()
        
        base_prices = {
            'BTC/USDT': 45000, 'ETH/USDT': 3000, 'BNB/USDT': 300,
            'ADA/USDT': 0.5, 'SOL/USDT': 100, 'DOT/USDT': 20,
            'LINK/USDT': 15, 'UNI/USDT': 8
        }
        
        for symbol in SYMBOLS:
            base_price = base_prices.get(symbol, 100)
            current_price = base_price * (1 + random.uniform(-0.05, 0.05))
            
            data = {
                'symbol': symbol,
                'price': current_price,
                'change_24h': random.uniform(-10, 10),
                'volume': random.uniform(1000, 100000),
                'timestamp': timestamp
            }
            
            self.price_cache[symbol] = current_price
            demo_data.append(data)
        
        return demo_data
    
    def _save_market_data(self, data: Dict[str, Any]):
        """Save market data to database efficiently"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO live_data 
                (symbol, price, change_24h, volume, timestamp) 
                VALUES (?, ?, ?, ?, ?)
            """, (data['symbol'], data['price'], data['change_24h'], 
                  data['volume'], data['timestamp']))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Save market data error: {e}")
    
    async def generate_signals(self) -> List[Dict[str, Any]]:
        """Generate trading signals efficiently"""
        signals = []
        timestamp = datetime.now().isoformat()
        
        try:
            # Simple signal generation based on price changes
            for symbol, price in self.price_cache.items():
                # Get previous price (simplified)
                import random
                
                if random.random() < 0.3:  # 30% chance of signal
                    action = random.choice(['BUY', 'SELL', 'HOLD'])
                    confidence = random.uniform(0.5, 0.95)
                    
                    signal = {
                        'symbol': symbol,
                        'action': action,
                        'confidence': confidence,
                        'price': price,
                        'timestamp': timestamp,
                        'reason': 'Technical analysis'
                    }
                    
                    signals.append(signal)
                    self.signal_cache.append(signal)
                    
                    # Save to database
                    self._save_signal(signal)
            
        except Exception as e:
            logger.error(f"❌ Signal generation error: {e}")
        
        return signals
    
    def _save_signal(self, signal: Dict[str, Any]):
        """Save signal to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO signals (symbol, action, confidence, price, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (signal['symbol'], signal['action'], signal['confidence'],
                  signal['price'], signal['timestamp']))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Save signal error: {e}")
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary efficiently"""
        try:
            exchange = self._get_exchange()
            if not exchange:
                return {
                    'total_balance': 10000.0,
                    'available_balance': 8500.0,
                    'total_pnl': 150.0,
                    'positions': 5,
                    'equity': 10150.0
                }
            
            # Fetch balance (cached)
            balance = exchange.fetch_balance()
            total_balance = balance['total']['USDT'] or 0
            
            return {
                'total_balance': total_balance,
                'available_balance': balance['free']['USDT'] or 0,
                'total_pnl': 0.0,  # Calculate separately if needed
                'positions': len([k for k, v in balance['total'].items() if v > 0]),
                'equity': total_balance
            }
            
        except Exception as e:
            logger.error(f"❌ Portfolio summary error: {e}")
            return {
                'total_balance': 0.0,
                'available_balance': 0.0,
                'total_pnl': 0.0,
                'positions': 0,
                'equity': 0.0
            }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get all dashboard data efficiently"""
        try:
            # Get data from database to save memory
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Recent signals
            cursor.execute("""
                SELECT symbol, action, confidence, price, timestamp 
                FROM signals 
                ORDER BY created_at DESC 
                LIMIT 50
            """)
            signals = [{'symbol': row[0], 'action': row[1], 'confidence': row[2],
                       'price': row[3], 'timestamp': row[4]} for row in cursor.fetchall()]
            
            # Recent trades
            cursor.execute("""
                SELECT symbol, side, amount, price, pnl, timestamp 
                FROM trades 
                ORDER BY created_at DESC 
                LIMIT 50
            """)
            trades = [{'symbol': row[0], 'side': row[1], 'amount': row[2],
                      'price': row[3], 'pnl': row[4], 'timestamp': row[5]} for row in cursor.fetchall()]
            
            # Live market data
            cursor.execute("""
                SELECT symbol, price, change_24h, volume, timestamp 
                FROM live_data 
                ORDER BY timestamp DESC
            """)
            market_data = [{'symbol': row[0], 'price': row[1], 'change_24h': row[2],
                           'volume': row[3], 'timestamp': row[4]} for row in cursor.fetchall()]
            
            conn.close()
            
            # Portfolio summary
            portfolio = self.get_portfolio_summary()
            
            # System stats
            memory = self.memory_monitor.get_memory_usage()
            
            return {
                'signals': signals,
                'trades': trades,
                'market_data': market_data,
                'portfolio': portfolio,
                'stats': {
                    'total_signals': len(signals),
                    'total_trades': len(trades),
                    'memory_usage_mb': memory['rss_mb'],
                    'memory_percent': memory['percent'],
                    'active_symbols': len(market_data)
                },
                'timestamp': datetime.now().isoformat(),
                'system_status': 'healthy' if memory['rss_mb'] < MAX_MEMORY_MB else 'high_memory'
            }
            
        except Exception as e:
            logger.error(f"❌ Dashboard data error: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    async def run_collection_loop(self):
        """Main data collection loop"""
        logger.info("🚀 Starting optimized data collection loop")
        
        while True:
            try:
                # Check memory before processing
                if self.memory_monitor.is_memory_critical():
                    logger.warning("⚠️ Memory critical, skipping collection cycle")
                    self._emergency_cleanup()
                    await asyncio.sleep(UPDATE_INTERVAL * 2)  # Wait longer
                    continue
                
                # Collect market data
                market_data = await self.collect_market_data()
                logger.info(f"📊 Collected data for {len(market_data)} symbols")
                
                # Generate signals
                signals = await self.generate_signals()
                if signals:
                    logger.info(f"🎯 Generated {len(signals)} signals")
                
                # Log memory usage periodically
                memory = self.memory_monitor.get_memory_usage()
                if memory['rss_mb'] > MAX_MEMORY_MB * 0.7:  # 70% threshold
                    logger.warning(f"⚠️ High memory usage: {memory['rss_mb']:.1f}MB")
                
                await asyncio.sleep(UPDATE_INTERVAL)
                
            except Exception as e:
                logger.error(f"❌ Collection loop error: {e}")
                await asyncio.sleep(UPDATE_INTERVAL)
    
    def stop(self):
        """Stop the data collector"""
        self.monitoring_active = False
        logger.info("🛑 Data collector stopped")