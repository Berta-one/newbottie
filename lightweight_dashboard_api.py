#!/usr/bin/env python3
"""
Lightweight WebSocket Dashboard API - Memory Optimized for Render 512MB limit
Combines all functionality into efficient table-based real-time updates
"""

import asyncio
import json
import sqlite3
import logging
import os
import gc
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from collections import deque
import threading
from dataclasses import dataclass, asdict

# ML-scale configuration with smart memory management
MAX_STORED_RECORDS = 10000    # Sufficient for ML analysis (10k records)
MAX_LOG_ENTRIES = 1000        # More logs for detailed tracking
CLEANUP_INTERVAL = 600        # Cleanup every 10 minutes (less frequent)
GC_INTERVAL = 120            # Garbage collection every 2 minutes
MAX_MEMORY_MB = int(os.getenv("MAX_MEMORY_MB", "400"))

# ML-specific configuration
ML_TRAINING_WINDOW = 5000     # Use 5000 records for ML training
ML_ANALYSIS_BATCH_SIZE = 100  # Process ML in batches to save memory
DATABASE_RETENTION_DAYS = 30  # Keep 30 days of data for ML analysis
MEMORY_PRESSURE_THRESHOLD = 0.75  # Start cleanup at 75% memory usage

# Configure minimal logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TradeRecord:
    """Memory-efficient trade record"""
    symbol: str
    side: str
    amount: float
    price: float
    timestamp: str
    pnl: float = 0.0
    status: str = "executed"
    
@dataclass
class SignalRecord:
    """Memory-efficient signal record"""
    symbol: str
    signal: str
    confidence: float
    price: float
    timestamp: str
    reason: str = ""

@dataclass
class MarketData:
    """Memory-efficient market data"""
    symbol: str
    price: float
    change_24h: float
    volume: float
    timestamp: str

class MLScaleDataManager:
    """ML-scale data management with intelligent memory optimization"""
    
    def __init__(self):
        # Smart tiered storage system
        self.recent_trades = deque(maxlen=1000)      # Recent trades in memory for dashboard
        self.recent_signals = deque(maxlen=1000)     # Recent signals in memory for dashboard  
        self.recent_market_data = deque(maxlen=200)  # Recent market data in memory
        self.logs = deque(maxlen=MAX_LOG_ENTRIES)
        
        # ML analysis cache (loaded on demand)
        self.ml_analysis_cache = {}
        self.ml_last_update = 0
        
        # Portfolio and stats
        self.portfolio = {}
        self.stats = {
            'total_trades': 0,
            'total_pnl': 0.0,
            'win_rate': 0.0,
            'equity': 10000.0,
            'memory_usage': 0.0,
            'database_size_mb': 0.0,
            'ml_model_accuracy': 0.0
        }
        
        # Memory management
        self.memory_pressure = False
        self.last_cleanup = 0
        
        # Start background threads
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()
        
        self.ml_thread = threading.Thread(target=self._ml_analysis_worker, daemon=True)
        self.ml_thread.start()
        
        # Initialize database with ML-optimized schema
        self._init_ml_database()
        
    def _init_ml_database(self):
        """Initialize ML-optimized database with larger capacity"""
        try:
            self.db_path = "/tmp/bottie_ml.db"
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Enable WAL mode for better performance with large datasets
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=10000")
            cursor.execute("PRAGMA temp_store=memory")
            
            # ML-optimized trades table with additional features for analysis
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    amount REAL NOT NULL,
                    price REAL NOT NULL,
                    pnl REAL DEFAULT 0,
                    timestamp TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    volume_24h REAL,
                    price_change_1h REAL,
                    rsi_14 REAL,
                    ema_20 REAL,
                    ml_prediction REAL,
                    confidence_score REAL
                )
            """)
            
            # ML-optimized signals table with feature data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    price REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ema_signal REAL,
                    rsi_signal REAL,
                    volume_signal REAL,
                    ml_score REAL,
                    quantum_score REAL,
                    sentiment_score REAL,
                    final_score REAL
                )
            """)
            
            # Market data with ML features
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    change_24h REAL,
                    volume REAL,
                    timestamp TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    high_24h REAL,
                    low_24h REAL,
                    volatility REAL,
                    trend_strength REAL
                )
            """)
            
            # ML analysis results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ml_analysis (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    prediction_1h REAL,
                    prediction_4h REAL,
                    prediction_24h REAL,
                    confidence_1h REAL,
                    confidence_4h REAL,
                    confidence_24h REAL,
                    model_accuracy REAL,
                    feature_importance TEXT,
                    timestamp TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Performance optimization indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol_time ON trades(symbol, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_symbol_time ON signals(symbol, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_symbol_time ON market_data(symbol, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ml_symbol_time ON ml_analysis(symbol, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_created ON trades(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_created ON signals(created_at)")
            
            # Only clean very old data (keep 30 days for ML)
            cutoff = (datetime.now() - timedelta(days=DATABASE_RETENTION_DAYS)).isoformat()
            cursor.execute("DELETE FROM trades WHERE timestamp < ?", (cutoff,))
            cursor.execute("DELETE FROM signals WHERE timestamp < ?", (cutoff,))
            cursor.execute("DELETE FROM market_data WHERE timestamp < ?", (cutoff,))
            cursor.execute("DELETE FROM ml_analysis WHERE timestamp < ?", (cutoff,))
            
            # Analyze and optimize
            cursor.execute("ANALYZE")
            
            conn.commit()
            conn.close()
            
            # Get database size
            db_size_mb = os.path.getsize(self.db_path) / 1024 / 1024 if os.path.exists(self.db_path) else 0
            self.stats['database_size_mb'] = db_size_mb
            
            logger.info(f"✅ ML-scale database initialized (Size: {db_size_mb:.1f}MB)")
        except Exception as e:
            logger.error(f"❌ Database init error: {e}")
    
    def _cleanup_worker(self):
        """Intelligent cleanup based on memory pressure and ML needs"""
        while True:
            try:
                time.sleep(CLEANUP_INTERVAL)
                
                # Update memory usage
                memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
                self.stats['memory_usage'] = memory_mb
                memory_pressure_ratio = memory_mb / MAX_MEMORY_MB
                
                # Adaptive cleanup based on memory pressure
                if memory_pressure_ratio > 0.9:  # 90% - Critical
                    logger.critical(f"🚨 CRITICAL MEMORY: {memory_mb:.1f}MB")
                    self._emergency_cleanup()
                    self.memory_pressure = True
                elif memory_pressure_ratio > MEMORY_PRESSURE_THRESHOLD:  # 75% - Warning
                    logger.warning(f"⚠️ Memory pressure: {memory_mb:.1f}MB")
                    self._smart_cleanup()
                    self.memory_pressure = True
                else:
                    self.memory_pressure = False
                    # Light maintenance cleanup
                    self._maintenance_cleanup()
                
                # Update database size
                if os.path.exists(self.db_path):
                    db_size_mb = os.path.getsize(self.db_path) / 1024 / 1024
                    self.stats['database_size_mb'] = db_size_mb
                
                # Force garbage collection
                collected = gc.collect()
                logger.info(f"🧹 Cleanup: {memory_mb:.1f}MB memory ({memory_pressure_ratio:.1%}), DB: {self.stats['database_size_mb']:.1f}MB, GC: {collected}")
                    
            except Exception as e:
                logger.error(f"❌ Cleanup error: {e}")
    
    def _ml_analysis_worker(self):
        """Background ML analysis on stored data"""
        while True:
            try:
                time.sleep(300)  # Run ML analysis every 5 minutes
                
                # Only run ML analysis if not under memory pressure
                if not self.memory_pressure:
                    self._run_ml_analysis()
                else:
                    logger.info("⏸️ Skipping ML analysis due to memory pressure")
                    
            except Exception as e:
                logger.error(f"❌ ML analysis worker error: {e}")
    
    def _run_ml_analysis(self):
        """Run ML analysis on historical data"""
        try:
            # Get training data from database (last 5000 records)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get recent trades for analysis
            cursor.execute("""
                SELECT symbol, side, amount, price, pnl, timestamp, 
                       volume_24h, price_change_1h, rsi_14, ema_20
                FROM trades 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (ML_TRAINING_WINDOW,))
            
            trades_data = cursor.fetchall()
            
            if len(trades_data) < 100:  # Need minimum data for ML
                logger.info("📊 Insufficient data for ML analysis")
                conn.close()
                return
            
            # Simple ML analysis (without heavy libraries to save memory)
            symbol_performance = {}
            total_trades = len(trades_data)
            profitable_trades = 0
            
            for trade in trades_data:
                symbol = trade[0]
                pnl = trade[4] or 0
                
                if symbol not in symbol_performance:
                    symbol_performance[symbol] = {'trades': 0, 'total_pnl': 0, 'wins': 0}
                
                symbol_performance[symbol]['trades'] += 1
                symbol_performance[symbol]['total_pnl'] += pnl
                if pnl > 0:
                    symbol_performance[symbol]['wins'] += 1
                    profitable_trades += 1
            
            # Calculate overall metrics
            overall_win_rate = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0
            self.stats['win_rate'] = overall_win_rate
            self.stats['ml_model_accuracy'] = min(95, max(50, overall_win_rate))  # Convert to accuracy
            
            # Generate ML predictions for each symbol
            for symbol, perf in symbol_performance.items():
                win_rate = (perf['wins'] / perf['trades']) * 100 if perf['trades'] > 0 else 50
                avg_pnl = perf['total_pnl'] / perf['trades'] if perf['trades'] > 0 else 0
                
                # Simple prediction model based on historical performance
                prediction_1h = 1.0 + (avg_pnl / 1000)  # Convert PnL to price multiplier
                prediction_4h = 1.0 + (avg_pnl / 800)
                prediction_24h = 1.0 + (avg_pnl / 500)
                
                confidence = min(0.95, max(0.5, win_rate / 100))
                
                # Store ML analysis
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ml_analysis 
                    (symbol, prediction_1h, prediction_4h, prediction_24h, 
                     confidence_1h, confidence_4h, confidence_24h, model_accuracy, 
                     feature_importance, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (symbol, prediction_1h, prediction_4h, prediction_24h,
                      confidence, confidence * 0.9, confidence * 0.8, win_rate,
                      json.dumps({'historical_performance': avg_pnl, 'trade_count': perf['trades']}),
                      datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            # Update cache with latest analysis
            self.ml_analysis_cache = {
                'last_update': time.time(),
                'model_accuracy': overall_win_rate,
                'total_trades_analyzed': total_trades,
                'symbols_analyzed': len(symbol_performance)
            }
            
            logger.info(f"🤖 ML analysis completed: {total_trades} trades, {len(symbol_performance)} symbols, {overall_win_rate:.1f}% accuracy")
            
        except Exception as e:
            logger.error(f"❌ ML analysis error: {e}")
    
    def _smart_cleanup(self):
        """Smart cleanup that preserves ML training data"""
        try:
            # Only clean in-memory caches, preserve database for ML
            while len(self.recent_trades) > 500:  # Keep 500 most recent in memory
                self.recent_trades.popleft()
            
            while len(self.recent_signals) > 500:  # Keep 500 most recent in memory
                self.recent_signals.popleft()
            
            while len(self.logs) > 200:  # Reduce logs during pressure
                self.logs.popleft()
            
            # Clear ML cache if under severe pressure
            if self.stats['memory_usage'] > MAX_MEMORY_MB * 0.85:
                self.ml_analysis_cache.clear()
            
            gc.collect()
            logger.info("🧠 Smart cleanup: Preserved ML data, cleaned memory caches")
            
        except Exception as e:
            logger.error(f"❌ Smart cleanup error: {e}")
    
    def _maintenance_cleanup(self):
        """Light maintenance cleanup during normal operation"""
        try:
            # Only clean very old database entries (keep 30 days)
            if time.time() - self.last_cleanup > 3600:  # Once per hour
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Clean only very old data
                cutoff = (datetime.now() - timedelta(days=DATABASE_RETENTION_DAYS)).isoformat()
                
                cursor.execute("DELETE FROM trades WHERE timestamp < ?", (cutoff,))
                cursor.execute("DELETE FROM signals WHERE timestamp < ?", (cutoff,))
                cursor.execute("DELETE FROM market_data WHERE timestamp < ?", (cutoff,))
                
                # Optimize database occasionally
                if time.time() - self.last_cleanup > 86400:  # Once per day
                    cursor.execute("VACUUM")
                    cursor.execute("ANALYZE")
                
                conn.commit()
                conn.close()
                
                self.last_cleanup = time.time()
                logger.info("🔧 Maintenance cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Maintenance cleanup error: {e}")
    
    def _emergency_cleanup(self):
        """Emergency memory cleanup"""
        try:
            # Reduce deque sizes
            while len(self.trades) > 100:
                self.trades.popleft()
            while len(self.signals) > 100:
                self.signals.popleft()
            while len(self.logs) > 50:
                self.logs.popleft()
            
            # Clear portfolio cache
            self.portfolio.clear()
            
            # Force garbage collection
            gc.collect()
            
            logger.warning("🚨 Emergency cleanup completed")
        except Exception as e:
            logger.error(f"❌ Emergency cleanup error: {e}")
    
    def _cleanup_database(self):
        """Remove old database entries to save space"""
        try:
            cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Keep only recent data
            cursor.execute("DELETE FROM trades WHERE timestamp < ?", (cutoff,))
            cursor.execute("DELETE FROM signals WHERE timestamp < ?", (cutoff,))
            cursor.execute("VACUUM")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Database cleanup error: {e}")
    
    def add_trade(self, trade: TradeRecord):
        """Add trade record efficiently"""
        try:
            self.trades.append(trade)
            self.stats['total_trades'] += 1
            self.stats['total_pnl'] += trade.pnl
            
            # Update win rate
            profitable_trades = sum(1 for t in self.trades if t.pnl > 0)
            self.stats['win_rate'] = (profitable_trades / len(self.trades)) * 100 if self.trades else 0
            
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO trades (symbol, side, amount, price, pnl, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (trade.symbol, trade.side, trade.amount, trade.price, trade.pnl, trade.timestamp)
            )
            conn.commit()
            conn.close()
            
            self.log(f"💰 Trade: {trade.side} {trade.amount} {trade.symbol} @ ${trade.price} (P&L: ${trade.pnl})")
        except Exception as e:
            logger.error(f"❌ Add trade error: {e}")
    
    def add_signal(self, signal: SignalRecord):
        """Add signal record efficiently"""
        try:
            self.signals.append(signal)
            
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO signals (symbol, signal, confidence, price, timestamp) VALUES (?, ?, ?, ?, ?)",
                (signal.symbol, signal.signal, signal.confidence, signal.price, signal.timestamp)
            )
            conn.commit()
            conn.close()
            
            self.log(f"🎯 Signal: {signal.signal} {signal.symbol} ({signal.confidence:.1%}) - {signal.reason}")
        except Exception as e:
            logger.error(f"❌ Add signal error: {e}")
    
    def add_market_data(self, data: MarketData):
        """Add market data efficiently"""
        self.market_data.append(data)
        
        # Update portfolio if this symbol is held
        if data.symbol in self.portfolio:
            self.portfolio[data.symbol]['current_price'] = data.price
    
    def log(self, message: str):
        """Add log entry with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        logger.info(message)
    
    def get_ml_training_data(self, symbol: str = None, limit: int = ML_TRAINING_WINDOW) -> Dict[str, Any]:
        """Get ML training data efficiently from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build query based on parameters
            if symbol:
                query = """
                    SELECT symbol, side, amount, price, pnl, timestamp, 
                           volume_24h, price_change_1h, rsi_14, ema_20, ml_prediction, confidence_score
                    FROM trades 
                    WHERE symbol = ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                """
                cursor.execute(query, (symbol, limit))
            else:
                query = """
                    SELECT symbol, side, amount, price, pnl, timestamp, 
                           volume_24h, price_change_1h, rsi_14, ema_20, ml_prediction, confidence_score
                    FROM trades 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """
                cursor.execute(query, (limit,))
            
            trades = cursor.fetchall()
            
            # Get corresponding signals data
            if symbol:
                cursor.execute("""
                    SELECT symbol, signal, confidence, price, timestamp,
                           ema_signal, rsi_signal, volume_signal, ml_score, quantum_score, sentiment_score
                    FROM signals 
                    WHERE symbol = ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (symbol, limit))
            else:
                cursor.execute("""
                    SELECT symbol, signal, confidence, price, timestamp,
                           ema_signal, rsi_signal, volume_signal, ml_score, quantum_score, sentiment_score
                    FROM signals 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
            
            signals = cursor.fetchall()
            
            conn.close()
            
            return {
                'trades': trades,
                'signals': signals,
                'total_trades': len(trades),
                'total_signals': len(signals),
                'data_quality': 'sufficient' if len(trades) >= 100 else 'insufficient'
            }
            
        except Exception as e:
            logger.error(f"❌ ML training data error: {e}")
            return {'trades': [], 'signals': [], 'total_trades': 0, 'total_signals': 0, 'data_quality': 'error'}
    
    def get_table_data(self) -> Dict[str, Any]:
        """Get all data formatted for table display with ML insights"""
        # Get memory usage
        memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        self.stats['memory_usage'] = memory_mb
        
        # Get recent data from memory (for dashboard display)
        recent_trades = [asdict(trade) for trade in list(self.recent_trades)[-100:]]
        recent_signals = [asdict(signal) for signal in list(self.recent_signals)[-100:]]
        recent_market = [asdict(data) for data in list(self.recent_market_data)[-50:]]
        
        # Get ML analysis summary
        ml_summary = self.get_ml_summary()
        
        return {
            'trades': recent_trades,
            'signals': recent_signals,
            'market_data': recent_market,
            'portfolio': dict(self.portfolio),
            'stats': dict(self.stats),
            'logs': list(self.logs)[-200:],  # More logs for detailed tracking
            'ml_analysis': ml_summary,
            'timestamp': datetime.now().isoformat(),
            'memory_status': {
                'current_mb': round(memory_mb, 1),
                'limit_mb': MAX_MEMORY_MB,
                'percent': round((memory_mb / MAX_MEMORY_MB) * 100, 1),
                'status': 'ok' if memory_mb < MAX_MEMORY_MB * 0.8 else 'warning',
                'database_mb': round(self.stats.get('database_size_mb', 0), 1)
            },
            'data_scale': {
                'total_available_trades': self.get_total_trades_count(),
                'total_available_signals': self.get_total_signals_count(),
                'ml_training_window': ML_TRAINING_WINDOW,
                'retention_days': DATABASE_RETENTION_DAYS
            }
        }
    
    def get_ml_summary(self) -> Dict[str, Any]:
        """Get ML analysis summary"""
        if self.ml_analysis_cache:
            return {
                'status': 'active',
                'last_update': datetime.fromtimestamp(self.ml_analysis_cache['last_update']).strftime('%H:%M:%S'),
                'model_accuracy': round(self.ml_analysis_cache['model_accuracy'], 1),
                'trades_analyzed': self.ml_analysis_cache['total_trades_analyzed'],
                'symbols_analyzed': self.ml_analysis_cache['symbols_analyzed'],
                'next_analysis': 'In 5 minutes'
            }
        else:
            return {
                'status': 'initializing',
                'message': 'ML analysis starting soon...'
            }
    
    def get_total_trades_count(self) -> int:
        """Get total number of trades in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM trades")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except:
            return 0
    
    def get_total_signals_count(self) -> int:
        """Get total number of signals in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM signals")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except:
            return 0

class WebSocketManager:
    """Manage WebSocket connections efficiently"""
    
    def __init__(self, data_manager: MLScaleDataManager):
        self.connections: List[WebSocket] = []
        self.data_manager = data_manager
        self.max_connections = int(os.getenv("MAX_WEBSOCKET_CONNECTIONS", "10"))
        
    async def connect(self, websocket: WebSocket):
        """Add new WebSocket connection"""
        # Limit connections to prevent memory issues
        if len(self.connections) >= self.max_connections:
            await websocket.close(code=1008, reason="Too many connections")
            return
            
        await websocket.accept()
        self.connections.append(websocket)
        logger.info(f"🔌 WebSocket connected. Total: {len(self.connections)}")
        
        # Send initial data
        await self.send_to_client(websocket, {
            'type': 'initial_data',
            'data': self.data_manager.get_table_data()
        })
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.connections:
            self.connections.remove(websocket)
        logger.info(f"🔌 WebSocket disconnected. Total: {len(self.connections)}")
    
    async def send_to_client(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to specific client"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"❌ Send error: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.connections:
            return
            
        disconnected = []
        message_str = json.dumps(message)
        
        for websocket in self.connections:
            try:
                await websocket.send_text(message_str)
            except:
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for ws in disconnected:
            self.disconnect(ws)

# Initialize components
data_manager = MLScaleDataManager()
ws_manager = WebSocketManager(data_manager)

# FastAPI app with minimal memory footprint
app = FastAPI(
    title="Bottie Lightweight Dashboard", 
    version="1.0.0",
    docs_url=None,  # Disable docs to save memory
    redoc_url=None  # Disable redoc to save memory
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time table updates"""
    await ws_manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            message = await websocket.receive_text()
            data = json.loads(message)
            
            if data.get('type') == 'request_update':
                # Send current data
                await ws_manager.send_to_client(websocket, {
                    'type': 'data_update',
                    'data': data_manager.get_table_data()
                })
                
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        ws_manager.disconnect(websocket)

@app.get("/")
async def get_dashboard():
    """Serve the optimized dashboard HTML"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>Bottie Lightweight Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Courier New', monospace; 
            background: #0a0a0a; 
            color: #00ff00; 
            overflow-x: auto; 
            font-size: 13px;
        }
        .header { 
            background: #000; 
            padding: 10px; 
            border-bottom: 2px solid #00ff00; 
            position: sticky; 
            top: 0; 
            z-index: 100; 
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .status { display: inline-block; margin-right: 20px; }
        .container { padding: 15px; max-width: 1600px; margin: 0 auto; }
        .section { margin-bottom: 25px; }
        .section-title { 
            color: #ffff00; 
            font-size: 16px; 
            margin-bottom: 8px; 
            border-bottom: 1px solid #333; 
            padding-bottom: 3px; 
        }
        table { 
            width: 100%; 
            border-collapse: collapse; 
            margin-bottom: 15px; 
            font-size: 11px; 
            background: #111;
        }
        th, td { 
            border: 1px solid #333; 
            padding: 6px; 
            text-align: left; 
            white-space: nowrap; 
        }
        th { background: #222; color: #ffff00; font-weight: bold; }
        tr:nth-child(even) { background: #1a1a1a; }
        tr:hover { background: #2a2a2a; }
        .buy { color: #00ff88; font-weight: bold; }
        .sell { color: #ff6b6b; font-weight: bold; }
        .profit { color: #00ff88; }
        .loss { color: #ff6b6b; }
        .neutral { color: #ffaa00; }
        .logs { 
            height: 180px; 
            overflow-y: auto; 
            background: #000; 
            padding: 8px; 
            border: 1px solid #333; 
            font-size: 10px;
            font-family: monospace;
        }
        .stats { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); 
            gap: 8px; 
            margin-bottom: 15px; 
        }
        .stat-card { 
            background: #1a1a1a; 
            padding: 12px; 
            border: 1px solid #333; 
            border-radius: 4px;
        }
        .stat-value { font-size: 20px; color: #00ff00; font-weight: bold; }
        .stat-label { color: #ccc; font-size: 11px; margin-top: 2px; }
        .connected { color: #00ff00; }
        .disconnected { color: #ff6b6b; }
        .loading { color: #ffff00; }
        .memory-ok { color: #00ff00; }
        .memory-warning { color: #ffaa00; }
        .memory-critical { color: #ff6b6b; }
        .scroll-container { max-height: 400px; overflow-y: auto; }
        .timestamp { font-size: 10px; color: #888; }
        .performance-profit { background: rgba(0, 255, 136, 0.1); }
        .performance-loss { background: rgba(255, 107, 107, 0.1); }
    </style>
</head>
<body>
    <div class="header">
        <div>
            📊 <span id="status" class="loading">Connecting...</span> |
            💾 <span id="memory-status" class="memory-ok">Memory: --MB</span> |
            🕐 <span id="timestamp">--:--:--</span>
        </div>
        <div>
            🚀 Bottie Lightweight | Real-time Tables | Memory Optimized
        </div>
    </div>

    <div class="container">
        <!-- Stats Cards -->
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value" id="total-trades">0</div>
                <div class="stat-label">Total Trades</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="total-pnl">$0.00</div>
                <div class="stat-label">Total P&L</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="win-rate">0%</div>
                <div class="stat-label">Win Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="equity">$0.00</div>
                <div class="stat-label">Portfolio Equity</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="memory-usage">0MB</div>
                <div class="stat-label">Memory Usage</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="connections">0</div>
                <div class="stat-label">WebSocket Connections</div>
            </div>
        </div>

        <!-- Recent Trades -->
        <div class="section">
            <div class="section-title">💰 Recent Trades (Live Updates)</div>
            <div class="scroll-container">
                <table id="trades-table">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Symbol</th>
                            <th>Side</th>
                            <th>Amount</th>
                            <th>Price</th>
                            <th>P&L</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody id="trades-body">
                        <tr><td colspan="7">🔄 Loading trades...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Recent Signals -->
        <div class="section">
            <div class="section-title">🎯 Trading Signals (Live Updates)</div>
            <div class="scroll-container">
                <table id="signals-table">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Symbol</th>
                            <th>Signal</th>
                            <th>Confidence</th>
                            <th>Price</th>
                            <th>Reason</th>
                        </tr>
                    </thead>
                    <tbody id="signals-body">
                        <tr><td colspan="6">🔄 Loading signals...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Market Data -->
        <div class="section">
            <div class="section-title">📈 Live Market Data</div>
            <div class="scroll-container">
                <table id="market-table">
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th>Price</th>
                            <th>24h Change</th>
                            <th>Volume</th>
                            <th>Updated</th>
                        </tr>
                    </thead>
                    <tbody id="market-body">
                        <tr><td colspan="5">🔄 Loading market data...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- System Logs -->
        <div class="section">
            <div class="section-title">📝 System Activity Logs (Live Feed)</div>
            <div id="logs" class="logs">🔄 Loading logs...</div>
        </div>
    </div>

    <script>
        let ws = null;
        let reconnectInterval = null;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 5;

        function connect() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            document.getElementById('status').textContent = 'Connecting...';
            document.getElementById('status').className = 'loading';
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {
                document.getElementById('status').textContent = 'Connected';
                document.getElementById('status').className = 'connected';
                clearInterval(reconnectInterval);
                reconnectAttempts = 0;
                
                // Request initial data
                ws.send(JSON.stringify({type: 'request_update'}));
                
                console.log('✅ WebSocket connected');
            };
            
            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);
                updateDashboard(message.data);
            };
            
            ws.onclose = function() {
                document.getElementById('status').textContent = 'Disconnected';
                document.getElementById('status').className = 'disconnected';
                
                // Auto-reconnect with exponential backoff
                if (reconnectAttempts < maxReconnectAttempts) {
                    const delay = Math.min(30000, 1000 * Math.pow(2, reconnectAttempts));
                    reconnectAttempts++;
                    
                    setTimeout(() => {
                        console.log(`🔄 Reconnect attempt ${reconnectAttempts}/${maxReconnectAttempts}`);
                        connect();
                    }, delay);
                }
            };
            
            ws.onerror = function(error) {
                console.error('❌ WebSocket error:', error);
            };
        }

        function updateDashboard(data) {
            if (!data) return;
            
            // Update timestamp
            const timestamp = new Date().toLocaleTimeString();
            document.getElementById('timestamp').textContent = timestamp;
            
            // Update memory status
            if (data.memory_status) {
                const memEl = document.getElementById('memory-status');
                const memText = `${data.memory_status.current_mb}MB (${data.memory_status.percent}%)`;
                memEl.textContent = `Memory: ${memText}`;
                memEl.className = `memory-${data.memory_status.status}`;
            }
            
            // Update stats cards
            if (data.stats) {
                document.getElementById('total-trades').textContent = data.stats.total_trades || 0;
                document.getElementById('total-pnl').textContent = `$${(data.stats.total_pnl || 0).toFixed(2)}`;
                document.getElementById('win-rate').textContent = `${(data.stats.win_rate || 0).toFixed(1)}%`;
                document.getElementById('equity').textContent = `$${(data.stats.equity || 0).toFixed(2)}`;
                document.getElementById('memory-usage').textContent = `${(data.stats.memory_usage || 0).toFixed(1)}MB`;
            }
            
            // Update connections count
            document.getElementById('connections').textContent = ws ? '1' : '0';
            
            // Update trades table
            if (data.trades && data.trades.length > 0) {
                const tradesBody = document.getElementById('trades-body');
                tradesBody.innerHTML = data.trades.slice(-30).reverse().map(trade => {
                    const time = new Date(trade.timestamp).toLocaleTimeString();
                    const pnlClass = trade.pnl >= 0 ? 'profit' : 'loss';
                    const performanceClass = trade.pnl >= 0 ? 'performance-profit' : 'performance-loss';
                    
                    return `
                        <tr class="${performanceClass}">
                            <td class="timestamp">${time}</td>
                            <td><strong>${trade.symbol}</strong></td>
                            <td class="${trade.side.toLowerCase()}">${trade.side.toUpperCase()}</td>
                            <td>${parseFloat(trade.amount).toFixed(6)}</td>
                            <td>$${parseFloat(trade.price).toFixed(4)}</td>
                            <td class="${pnlClass}"><strong>$${parseFloat(trade.pnl).toFixed(2)}</strong></td>
                            <td>${trade.status}</td>
                        </tr>
                    `;
                }).join('');
            }
            
            // Update signals table
            if (data.signals && data.signals.length > 0) {
                const signalsBody = document.getElementById('signals-body');
                signalsBody.innerHTML = data.signals.slice(-30).reverse().map(signal => {
                    const time = new Date(signal.timestamp).toLocaleTimeString();
                    const signalClass = signal.signal.toLowerCase();
                    const confidence = (signal.confidence * 100).toFixed(1);
                    
                    return `
                        <tr>
                            <td class="timestamp">${time}</td>
                            <td><strong>${signal.symbol}</strong></td>
                            <td class="${signalClass}"><strong>${signal.signal.toUpperCase()}</strong></td>
                            <td>${confidence}%</td>
                            <td>$${parseFloat(signal.price).toFixed(4)}</td>
                            <td>${signal.reason || 'Technical analysis'}</td>
                        </tr>
                    `;
                }).join('');
            }
            
            // Update market data table
            if (data.market_data && data.market_data.length > 0) {
                const marketBody = document.getElementById('market-body');
                marketBody.innerHTML = data.market_data.map(market => {
                    const time = new Date(market.timestamp).toLocaleTimeString();
                    const changeClass = market.change_24h >= 0 ? 'profit' : 'loss';
                    const change = market.change_24h >= 0 ? '+' : '';
                    
                    return `
                        <tr>
                            <td><strong>${market.symbol}</strong></td>
                            <td>$${parseFloat(market.price).toFixed(4)}</td>
                            <td class="${changeClass}"><strong>${change}${parseFloat(market.change_24h).toFixed(2)}%</strong></td>
                            <td>${parseInt(market.volume).toLocaleString()}</td>
                            <td class="timestamp">${time}</td>
                        </tr>
                    `;
                }).join('');
            }
            
            // Update logs
            if (data.logs && data.logs.length > 0) {
                const logsDiv = document.getElementById('logs');
                logsDiv.innerHTML = data.logs.slice(-50).join('<br>');
                logsDiv.scrollTop = logsDiv.scrollHeight;
            }
        }

        // Auto-refresh data every 10 seconds
        setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({type: 'request_update'}));
            }
        }, 10000);

        // Connect on page load
        connect();
        
        // Page visibility API to pause updates when tab not active
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                console.log('📱 Tab hidden, reducing update frequency');
            } else {
                console.log('📱 Tab visible, resuming normal updates');
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({type: 'request_update'}));
                }
            }
        });
    </script>
</body>
</html>
    """)

@app.get("/health")
async def health_check():
    """Comprehensive health check with ML data scale info"""
    try:
        memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        return {
            "status": "healthy" if memory < MAX_MEMORY_MB else "memory_warning",
            "memory_mb": round(memory, 1),
            "memory_limit_mb": MAX_MEMORY_MB,
            "memory_percent": round((memory / MAX_MEMORY_MB) * 100, 1),
            "timestamp": datetime.now().isoformat(),
            "websocket_connections": len(ws_manager.connections),
            "data_scale": {
                "memory_trades": len(data_manager.recent_trades),
                "memory_signals": len(data_manager.recent_signals),
                "database_trades": data_manager.get_total_trades_count(),
                "database_signals": data_manager.get_total_signals_count(),
                "ml_training_window": ML_TRAINING_WINDOW,
                "retention_days": DATABASE_RETENTION_DAYS
            },
            "ml_status": data_manager.get_ml_summary(),
            "database_size_mb": round(data_manager.stats.get('database_size_mb', 0), 1)
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/ml/training-data")
async def get_ml_training_data(symbol: str = None, limit: int = 1000):
    """Get ML training data for analysis (up to 5000 records)"""
    try:
        # Limit to prevent memory issues
        safe_limit = min(limit, ML_TRAINING_WINDOW)
        training_data = data_manager.get_ml_training_data(symbol, safe_limit)
        
        return {
            "status": "success",
            "data": training_data,
            "requested_limit": limit,
            "actual_limit": safe_limit,
            "memory_safe": True,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/ml/analysis")
async def get_ml_analysis():
    """Get current ML analysis results"""
    try:
        conn = sqlite3.connect(data_manager.db_path)
        cursor = conn.cursor()
        
        # Get latest ML analysis for each symbol
        cursor.execute("""
            SELECT symbol, prediction_1h, prediction_4h, prediction_24h,
                   confidence_1h, confidence_4h, confidence_24h, model_accuracy,
                   feature_importance, timestamp
            FROM ml_analysis 
            WHERE timestamp > datetime('now', '-1 hour')
            ORDER BY created_at DESC
        """)
        
        analysis_data = []
        for row in cursor.fetchall():
            analysis_data.append({
                'symbol': row[0],
                'prediction_1h': row[1],
                'prediction_4h': row[2], 
                'prediction_24h': row[3],
                'confidence_1h': row[4],
                'confidence_4h': row[5],
                'confidence_24h': row[6],
                'model_accuracy': row[7],
                'feature_importance': json.loads(row[8]) if row[8] else {},
                'timestamp': row[9]
            })
        
        conn.close()
        
        return {
            "status": "success",
            "analysis": analysis_data,
            "total_symbols": len(analysis_data),
            "ml_summary": data_manager.get_ml_summary(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/data/stats")
async def get_data_statistics():
    """Get comprehensive data statistics for ML analysis"""
    try:
        conn = sqlite3.connect(data_manager.db_path)
        cursor = conn.cursor()
        
        # Get trade statistics by symbol
        cursor.execute("""
            SELECT symbol, 
                   COUNT(*) as trade_count,
                   AVG(pnl) as avg_pnl,
                   SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                   MIN(timestamp) as first_trade,
                   MAX(timestamp) as last_trade
            FROM trades 
            GROUP BY symbol
            ORDER BY trade_count DESC
        """)
        
        trade_stats = []
        for row in cursor.fetchall():
            win_rate = (row[3] / row[1]) * 100 if row[1] > 0 else 0
            trade_stats.append({
                'symbol': row[0],
                'trade_count': row[1],
                'avg_pnl': round(row[2] or 0, 2),
                'winning_trades': row[3],
                'win_rate': round(win_rate, 1),
                'first_trade': row[4],
                'last_trade': row[5],
                'data_quality': 'excellent' if row[1] > 100 else 'good' if row[1] > 50 else 'limited'
            })
        
        # Get signal statistics
        cursor.execute("""
            SELECT symbol,
                   COUNT(*) as signal_count,
                   AVG(confidence) as avg_confidence,
                   COUNT(CASE WHEN signal = 'BUY' THEN 1 END) as buy_signals,
                   COUNT(CASE WHEN signal = 'SELL' THEN 1 END) as sell_signals,
                   COUNT(CASE WHEN signal = 'HOLD' THEN 1 END) as hold_signals
            FROM signals
            GROUP BY symbol
            ORDER BY signal_count DESC
        """)
        
        signal_stats = []
        for row in cursor.fetchall():
            signal_stats.append({
                'symbol': row[0],
                'signal_count': row[1],
                'avg_confidence': round(row[2] or 0, 3),
                'buy_signals': row[3],
                'sell_signals': row[4],
                'hold_signals': row[5],
                'signal_distribution': {
                    'buy_pct': round((row[3] / row[1]) * 100, 1) if row[1] > 0 else 0,
                    'sell_pct': round((row[4] / row[1]) * 100, 1) if row[1] > 0 else 0,
                    'hold_pct': round((row[5] / row[1]) * 100, 1) if row[1] > 0 else 0
                }
            })
        
        conn.close()
        
        return {
            "status": "success",
            "trade_statistics": trade_stats,
            "signal_statistics": signal_stats,
            "overall_stats": {
                "total_trades": data_manager.get_total_trades_count(),
                "total_signals": data_manager.get_total_signals_count(),
                "ml_training_window": ML_TRAINING_WINDOW,
                "database_retention_days": DATABASE_RETENTION_DAYS,
                "database_size_mb": data_manager.stats.get('database_size_mb', 0)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Data simulation for demo/testing
async def simulate_trading_data():
    """Simulate realistic trading data for demo"""
    import random
    
    symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT', 'DOT/USDT']
    base_prices = {
        'BTC/USDT': 45000, 'ETH/USDT': 2800, 'BNB/USDT': 320,
        'ADA/USDT': 0.45, 'SOL/USDT': 95, 'DOT/USDT': 7.8
    }
    
    while True:
        try:
            # Simulate trade (30% chance)
            if random.random() < 0.3:
                symbol = random.choice(symbols)
                side = random.choice(['buy', 'sell'])
                amount = random.uniform(0.01, 1.0)
                price = base_prices[symbol] * random.uniform(0.95, 1.05)
                pnl = random.uniform(-50, 100)
                
                trade = TradeRecord(
                    symbol=symbol,
                    side=side,
                    amount=amount,
                    price=price,
                    timestamp=datetime.now().isoformat(),
                    pnl=pnl
                )
                data_manager.recent_trades.append(trade)
                
                # Add enhanced trade data to database for ML
                try:
                    conn = sqlite3.connect(data_manager.db_path)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO trades 
                        (symbol, side, amount, price, pnl, timestamp, volume_24h, price_change_1h, rsi_14, ema_20, ml_prediction, confidence_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (symbol, side, amount, price, pnl, trade.timestamp,
                          random.uniform(10000, 100000),  # volume_24h
                          random.uniform(-5, 5),          # price_change_1h
                          random.uniform(20, 80),         # rsi_14
                          price * random.uniform(0.98, 1.02),  # ema_20
                          random.uniform(0.3, 0.9),       # ml_prediction
                          random.uniform(0.5, 0.95)))     # confidence_score
                    conn.commit()
                    conn.close()
                except Exception as e:
                    logger.error(f"❌ Enhanced trade data error: {e}")
            
            # Simulate signal (50% chance)
            if random.random() < 0.5:
                symbol = random.choice(symbols)
                signal = random.choice(['BUY', 'SELL', 'HOLD'])
                confidence = random.uniform(0.5, 0.95)
                price = base_prices[symbol] * random.uniform(0.98, 1.02)
                
                signal_record = SignalRecord(
                    symbol=symbol,
                    signal=signal,
                    confidence=confidence,
                    price=price,
                    timestamp=datetime.now().isoformat(),
                    reason=random.choice(['EMA crossover', 'RSI oversold', 'Volume spike', 'Support bounce'])
                )
                data_manager.recent_signals.append(signal_record)
            
            # Simulate market data updates
            for symbol in symbols:
                price = base_prices[symbol] * random.uniform(0.98, 1.02)
                change_24h = random.uniform(-8, 8)
                volume = random.uniform(10000, 100000)
                
                market = MarketData(
                    symbol=symbol,
                    price=price,
                    change_24h=change_24h,
                    volume=volume,
                    timestamp=datetime.now().isoformat()
                )
                data_manager.recent_market_data.append(market)
            
            # Broadcast update to WebSocket clients
            if ws_manager.connections:
                await ws_manager.broadcast({
                    'type': 'data_update',
                    'data': data_manager.get_table_data()
                })
            
            await asyncio.sleep(15)  # Update every 15 seconds
            
        except Exception as e:
            logger.error(f"❌ Simulation error: {e}")
            await asyncio.sleep(15)

@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    logger.info("🚀 Lightweight dashboard starting...")
    
    # Log system info
    memory_info = psutil.virtual_memory()
    logger.info(f"📊 System RAM: {memory_info.total / 1024**3:.1f}GB available")
    logger.info(f"💾 Memory limit: {MAX_MEMORY_MB}MB")
    logger.info(f"🎛️ Demo mode: {os.getenv('DEMO_MODE', '1')}")
    
    # Start data simulation for demo/testing
    if os.getenv("DEMO_MODE", "1") == "1":
        asyncio.create_task(simulate_trading_data())
        logger.info("🎭 Demo mode: Simulating trading data")
    
    # Start memory monitoring
    asyncio.create_task(memory_monitoring_loop())
    
    data_manager.log("🚀 Lightweight dashboard started")
    logger.info("✅ Bottie Lightweight Dashboard ready!")

async def memory_monitoring_loop():
    """Monitor memory usage continuously"""
    while True:
        try:
            memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            if memory > MAX_MEMORY_MB * 0.9:
                logger.critical(f"🚨 CRITICAL: Memory at {memory:.1f}MB")
                # Emergency cleanup
                gc.collect()
                data_manager._emergency_cleanup()
            elif memory > MAX_MEMORY_MB * 0.8:
                logger.warning(f"⚠️ HIGH MEMORY: {memory:.1f}MB")
            
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"❌ Memory monitoring error: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    
    # Configure uvicorn for memory efficiency
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info",
        access_log=False,  # Disable access logs to save memory
        workers=1,         # Single worker
        loop="asyncio"
    )