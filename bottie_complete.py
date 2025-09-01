#!/usr/bin/env python3
"""
Complete Bottie Dashboard Solution - All components integrated
Memory optimized for 512MB Render limit with WebSocket tables
"""

import asyncio
import json
import logging
import os
import gc
import psutil
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from collections import deque
import threading
import sqlite3

# Memory configuration from environment
MAX_MEMORY_MB = int(os.getenv("MAX_MEMORY_MB", "400"))
MAX_STORED_RECORDS = int(os.getenv("MAX_STORED_RECORDS", "10000"))
MAX_LOG_ENTRIES = int(os.getenv("MAX_LOG_ENTRIES", "1000"))
CLEANUP_INTERVAL = int(os.getenv("CLEANUP_INTERVAL", "300"))
WEBSOCKET_BROADCAST_INTERVAL = int(os.getenv("WEBSOCKET_BROADCAST_INTERVAL", "15"))
UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", "60"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
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

class DataManager:
    """Memory-efficient data management"""
    
    def __init__(self):
        # Memory-efficient storage
        self.trades = deque(maxlen=1000)
        self.signals = deque(maxlen=1000)
        self.market_data = deque(maxlen=200)
        self.logs = deque(maxlen=MAX_LOG_ENTRIES)
        
        # Portfolio stats
        self.stats = {
            'total_trades': 0,
            'total_pnl': 0.0,
            'win_rate': 0.0,
            'equity': 10000.0,
            'memory_usage': 0.0
        }
        
        # Initialize database
        self.db_path = "/tmp/bottie.db"
        self._init_database()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()
    
    def _init_database(self):
        """Initialize SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT,
                    side TEXT,
                    amount REAL,
                    price REAL,
                    pnl REAL,
                    timestamp TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT,
                    signal TEXT,
                    confidence REAL,
                    price REAL,
                    timestamp TEXT
                )
            """)
            
            # Clean old data
            cutoff = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute("DELETE FROM trades WHERE timestamp < ?", (cutoff,))
            cursor.execute("DELETE FROM signals WHERE timestamp < ?", (cutoff,))
            cursor.execute("VACUUM")
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Database initialized")
        except Exception as e:
            logger.error(f"❌ Database error: {e}")
    
    def _cleanup_worker(self):
        """Background cleanup"""
        while True:
            try:
                time.sleep(CLEANUP_INTERVAL)
                
                # Check memory
                memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
                self.stats['memory_usage'] = memory_mb
                
                if memory_mb > MAX_MEMORY_MB * 0.8:
                    logger.warning(f"⚠️ High memory: {memory_mb:.1f}MB")
                    self._emergency_cleanup()
                
                # Regular cleanup
                gc.collect()
                
            except Exception as e:
                logger.error(f"❌ Cleanup error: {e}")
    
    def _emergency_cleanup(self):
        """Emergency cleanup"""
        try:
            # Reduce cache sizes
            while len(self.trades) > 100:
                self.trades.popleft()
            while len(self.signals) > 100:
                self.signals.popleft()
            while len(self.logs) > 100:
                self.logs.popleft()
            
            gc.collect()
            logger.info("🧹 Emergency cleanup completed")
        except Exception as e:
            logger.error(f"❌ Emergency cleanup error: {e}")
    
    def add_trade(self, trade_data):
        """Add trade record"""
        self.trades.append(trade_data)
        self.stats['total_trades'] += 1
        self.stats['total_pnl'] += trade_data.get('pnl', 0)
        
        # Update win rate
        profitable = sum(1 for t in self.trades if t.get('pnl', 0) > 0)
        self.stats['win_rate'] = (profitable / len(self.trades)) * 100 if self.trades else 0
        
        self.log(f"💰 Trade: {trade_data['side']} {trade_data['amount']:.4f} {trade_data['symbol']}")
    
    def add_signal(self, signal_data):
        """Add signal record"""
        self.signals.append(signal_data)
        self.log(f"🎯 Signal: {signal_data['signal']} {signal_data['symbol']} ({signal_data['confidence']:.1%})")
    
    def add_market_data(self, market_data):
        """Add market data"""
        self.market_data.append(market_data)
    
    def log(self, message):
        """Add log entry"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        logger.info(message)
    
    def get_table_data(self):
        """Get data for tables"""
        memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        self.stats['memory_usage'] = memory_mb
        
        return {
            'trades': list(self.trades)[-50:],
            'signals': list(self.signals)[-50:],
            'market_data': list(self.market_data)[-20:],
            'stats': dict(self.stats),
            'logs': list(self.logs)[-100:],
            'timestamp': datetime.now().isoformat(),
            'memory_status': {
                'current_mb': round(memory_mb, 1),
                'limit_mb': MAX_MEMORY_MB,
                'percent': round((memory_mb / MAX_MEMORY_MB) * 100, 1),
                'status': 'ok' if memory_mb < MAX_MEMORY_MB * 0.8 else 'warning'
            }
        }

class WebSocketManager:
    """Manage WebSocket connections"""
    
    def __init__(self, data_manager):
        self.connections = set()
        self.data_manager = data_manager
        self.max_connections = 10
    
    async def connect(self, websocket):
        """Add WebSocket connection"""
        if len(self.connections) >= self.max_connections:
            await websocket.close(code=1008, reason="Too many connections")
            return
            
        await websocket.accept()
        self.connections.add(websocket)
        logger.info(f"🔌 WebSocket connected: {len(self.connections)} total")
        
        # Send initial data
        await self.send_to_client(websocket, {
            'type': 'initial_data',
            'data': self.data_manager.get_table_data()
        })
    
    def disconnect(self, websocket):
        """Remove WebSocket connection"""
        self.connections.discard(websocket)
        logger.info(f"🔌 WebSocket disconnected: {len(self.connections)} remaining")
    
    async def send_to_client(self, websocket, message):
        """Send message to client"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"❌ Send error: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message):
        """Broadcast to all clients"""
        if not self.connections:
            return
            
        disconnected = set()
        message_str = json.dumps(message)
        
        for websocket in self.connections:
            try:
                await websocket.send_text(message_str)
            except:
                disconnected.add(websocket)
        
        for ws in disconnected:
            self.disconnect(ws)

# Initialize components
data_manager = DataManager()
ws_manager = WebSocketManager(data_manager)

# FastAPI app
app = FastAPI(title="Bottie Complete Dashboard", version="1.0.0")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data"""
    await ws_manager.connect(websocket)
    
    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            
            if data.get('type') == 'request_update':
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
async def dashboard():
    """Serve the complete dashboard"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>Bottie Complete Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Courier New', monospace; 
            background: #0a0a0a; 
            color: #00ff00; 
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
            🚀 Bottie Complete Dashboard | Memory Optimized | Real-time Tables
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
        </div>

        <!-- Recent Trades -->
        <div class="section">
            <div class="section-title">💰 Recent Trades (Live Updates)</div>
            <div class="scroll-container">
                <table>
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
                <table>
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
                <table>
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
            
            // Update trades table
            if (data.trades && data.trades.length > 0) {
                const tradesBody = document.getElementById('trades-body');
                tradesBody.innerHTML = data.trades.slice(-30).reverse().map(trade => {
                    const time = new Date(trade.timestamp).toLocaleTimeString();
                    const pnlClass = trade.pnl >= 0 ? 'profit' : 'loss';
                    
                    return `
                        <tr>
                            <td class="timestamp">${time}</td>
                            <td><strong>${trade.symbol}</strong></td>
                            <td class="${trade.side.toLowerCase()}">${trade.side.toUpperCase()}</td>
                            <td>${parseFloat(trade.amount).toFixed(6)}</td>
                            <td>$${parseFloat(trade.price).toFixed(4)}</td>
                            <td class="${pnlClass}"><strong>$${parseFloat(trade.pnl).toFixed(2)}</strong></td>
                            <td>${trade.status || 'executed'}</td>
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
    """Comprehensive health check"""
    try:
        memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        return {
            "status": "healthy" if memory < MAX_MEMORY_MB else "memory_warning",
            "memory_mb": round(memory, 1),
            "memory_limit_mb": MAX_MEMORY_MB,
            "memory_percent": round((memory / MAX_MEMORY_MB) * 100, 1),
            "timestamp": datetime.now().isoformat(),
            "websocket_connections": len(ws_manager.connections),
            "total_trades": len(data_manager.trades),
            "total_signals": len(data_manager.signals)
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/memory")
async def memory_status():
    """Detailed memory status"""
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss_mb": round(memory_info.rss / 1024**2, 1),
            "vms_mb": round(memory_info.vms / 1024**2, 1),
            "percent": round(process.memory_percent(), 1),
            "limit_mb": MAX_MEMORY_MB,
            "available_mb": round(MAX_MEMORY_MB - (memory_info.rss / 1024**2), 1),
            "threads": process.num_threads(),
            "gc_counts": gc.get_count()
        }
        
    except Exception as e:
        return {"error": str(e)}

# Data simulation and collection
async def simulate_trading_data():
    """Generate realistic trading data"""
    symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT', 'DOT/USDT']
    base_prices = {
        'BTC/USDT': 45000, 'ETH/USDT': 2800, 'BNB/USDT': 320,
        'ADA/USDT': 0.45, 'SOL/USDT': 95, 'DOT/USDT': 7.8
    }
    
    trade_id = 1
    
    while True:
        try:
            # Memory management
            memory = psutil.Process().memory_info().rss / 1024 / 1024
            if memory > MAX_MEMORY_MB * 0.8:
                gc.collect()
                data_manager.log(f"🧹 Memory cleanup at {memory:.1f}MB")
            
            # Generate trade (30% chance)
            if random.random() < 0.3:
                symbol = random.choice(symbols)
                side = random.choice(['buy', 'sell'])
                amount = random.uniform(0.01, 1.0)
                price = base_prices[symbol] * random.uniform(0.95, 1.05)
                pnl = random.uniform(-50, 100)
                
                trade = {
                    'id': f'trade_{trade_id}',
                    'symbol': symbol,
                    'side': side,
                    'amount': amount,
                    'price': price,
                    'pnl': pnl,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'executed'
                }
                
                data_manager.add_trade(trade)
                trade_id += 1
            
            # Generate signal (50% chance)
            if random.random() < 0.5:
                symbol = random.choice(symbols)
                signal = random.choice(['BUY', 'SELL', 'HOLD'])
                confidence = random.uniform(0.5, 0.95)
                price = base_prices[symbol] * random.uniform(0.98, 1.02)
                
                signal_data = {
                    'symbol': symbol,
                    'signal': signal,
                    'confidence': confidence,
                    'price': price,
                    'timestamp': datetime.now().isoformat(),
                    'reason': random.choice(['EMA crossover', 'RSI signal', 'Volume spike', 'Support level'])
                }
                
                data_manager.add_signal(signal_data)
            
            # Generate market data
            for symbol in symbols:
                price = base_prices[symbol] * random.uniform(0.98, 1.02)
                change_24h = random.uniform(-8, 8)
                volume = random.uniform(10000, 100000)
                
                market = {
                    'symbol': symbol,
                    'price': price,
                    'change_24h': change_24h,
                    'volume': volume,
                    'timestamp': datetime.now().isoformat()
                }
                
                data_manager.add_market_data(market)
            
            # Broadcast update to WebSocket clients
            if ws_manager.connections:
                await ws_manager.broadcast({
                    'type': 'data_update',
                    'data': data_manager.get_table_data()
                })
            
            await asyncio.sleep(UPDATE_INTERVAL)
            
        except Exception as e:
            logger.error(f"❌ Simulation error: {e}")
            await asyncio.sleep(UPDATE_INTERVAL)

# Memory monitoring task
async def memory_monitoring():
    """Monitor memory usage continuously"""
    while True:
        try:
            memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            if memory > MAX_MEMORY_MB * 0.9:
                logger.critical(f"🚨 CRITICAL: Memory at {memory:.1f}MB")
                gc.collect()
                data_manager._emergency_cleanup()
            elif memory > MAX_MEMORY_MB * 0.8:
                logger.warning(f"⚠️ HIGH MEMORY: {memory:.1f}MB")
            elif memory > MAX_MEMORY_MB * 0.7:
                logger.info(f"💾 Memory usage: {memory:.1f}MB")
            
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"❌ Memory monitoring error: {e}")
            await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    """Start all background tasks"""
    logger.info("🚀 Bottie Complete Dashboard starting...")
    
    # Log system info
    memory_info = psutil.virtual_memory()
    logger.info(f"📊 System RAM: {memory_info.total / 1024**3:.1f}GB")
    logger.info(f"💾 Memory limit: {MAX_MEMORY_MB}MB")
    logger.info(f"🎛️ Demo mode: {os.getenv('DEMO_MODE', '1')}")
    
    # Start background tasks
    asyncio.create_task(simulate_trading_data())
    asyncio.create_task(memory_monitoring())
    
    data_manager.log("🚀 Complete dashboard started")
    logger.info("✅ All systems operational!")

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    
    logger.info("🚀 Bottie Complete Dashboard - Starting Up")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info",
        access_log=False,
        workers=1
    )