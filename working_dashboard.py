#!/usr/bin/env python3
"""
Working Dashboard - Guaranteed to work on Render with WebSocket tables
Combines all functionality in a single file to avoid import issues
"""

import asyncio
import json
import logging
import os
import gc
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from collections import deque
import threading
import random

# Memory configuration
MAX_MEMORY_MB = int(os.getenv("MAX_MEMORY_MB", "400"))
MAX_STORED_RECORDS = int(os.getenv("MAX_STORED_RECORDS", "10000"))
MAX_LOG_ENTRIES = int(os.getenv("MAX_LOG_ENTRIES", "1000"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Global data storage
trades_data = deque(maxlen=1000)  # Recent trades for dashboard
signals_data = deque(maxlen=1000)  # Recent signals for dashboard
market_data = deque(maxlen=100)   # Recent market data
system_logs = deque(maxlen=MAX_LOG_ENTRIES)
portfolio_stats = {
    'total_trades': 0,
    'total_pnl': 0.0,
    'win_rate': 0.0,
    'equity': 10000.0,
    'memory_usage': 0.0
}

# WebSocket connections
websocket_connections = set()

def log_message(message: str):
    """Add log message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    system_logs.append(log_entry)
    logger.info(message)

def get_memory_usage():
    """Get current memory usage"""
    try:
        memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        portfolio_stats['memory_usage'] = memory_mb
        return memory_mb
    except:
        return 0.0

def cleanup_memory():
    """Clean up memory when needed"""
    try:
        memory_mb = get_memory_usage()
        
        if memory_mb > MAX_MEMORY_MB * 0.8:  # 80% threshold
            logger.warning(f"⚠️ High memory usage: {memory_mb:.1f}MB, cleaning up...")
            
            # Reduce data sizes
            while len(trades_data) > 500:
                trades_data.popleft()
            while len(signals_data) > 500:
                signals_data.popleft()
            while len(system_logs) > 200:
                system_logs.popleft()
            
            # Force garbage collection
            collected = gc.collect()
            logger.info(f"🧹 Cleanup: {collected} objects collected")
            
    except Exception as e:
        logger.error(f"❌ Cleanup error: {e}")

# FastAPI app
app = FastAPI(title="Bottie Working Dashboard", version="1.0.0")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data"""
    await websocket.accept()
    websocket_connections.add(websocket)
    log_message(f"🔌 WebSocket connected. Total: {len(websocket_connections)}")
    
    try:
        # Send initial data
        await websocket.send_text(json.dumps({
            'type': 'initial_data',
            'data': get_dashboard_data()
        }))
        
        while True:
            # Listen for requests
            message = await websocket.receive_text()
            data = json.loads(message)
            
            if data.get('type') == 'request_update':
                await websocket.send_text(json.dumps({
                    'type': 'data_update',
                    'data': get_dashboard_data()
                }))
                
    except WebSocketDisconnect:
        websocket_connections.discard(websocket)
        log_message(f"🔌 WebSocket disconnected. Total: {len(websocket_connections)}")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        websocket_connections.discard(websocket)

def get_dashboard_data():
    """Get all dashboard data"""
    memory_mb = get_memory_usage()
    
    return {
        'trades': list(trades_data)[-50:],  # Last 50 trades
        'signals': list(signals_data)[-50:],  # Last 50 signals
        'market_data': list(market_data)[-20:],  # Last 20 market updates
        'stats': dict(portfolio_stats),
        'logs': list(system_logs)[-100:],  # Last 100 logs
        'timestamp': datetime.now().isoformat(),
        'memory_status': {
            'current_mb': round(memory_mb, 1),
            'limit_mb': MAX_MEMORY_MB,
            'percent': round((memory_mb / MAX_MEMORY_MB) * 100, 1),
            'status': 'ok' if memory_mb < MAX_MEMORY_MB * 0.8 else 'warning'
        }
    }

@app.get("/")
async def get_dashboard():
    """Serve the working dashboard"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>Bottie Working Dashboard</title>
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
        }
        .stat-value { font-size: 20px; color: #00ff00; font-weight: bold; }
        .stat-label { color: #ccc; font-size: 11px; }
        .connected { color: #00ff00; }
        .disconnected { color: #ff6b6b; }
        .scroll-container { max-height: 400px; overflow-y: auto; }
    </style>
</head>
<body>
    <div class="header">
        <div>
            📊 <span id="status" class="disconnected">Connecting...</span> |
            💾 <span id="memory-status">Memory: --MB</span> |
            🕐 <span id="timestamp">--:--:--</span>
        </div>
        <div>🚀 Bottie Working Dashboard | Real-time Tables</div>
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
            <div class="section-title">📝 System Activity Logs</div>
            <div id="logs" class="logs">🔄 Loading logs...</div>
        </div>
    </div>

    <script>
        let ws = null;

        function connect() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {
                document.getElementById('status').textContent = 'Connected';
                document.getElementById('status').className = 'connected';
                ws.send(JSON.stringify({type: 'request_update'}));
            };
            
            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);
                updateDashboard(message.data);
            };
            
            ws.onclose = function() {
                document.getElementById('status').textContent = 'Disconnected';
                document.getElementById('status').className = 'disconnected';
                setTimeout(connect, 5000);  // Reconnect
            };
        }

        function updateDashboard(data) {
            if (!data) return;
            
            // Update timestamp
            document.getElementById('timestamp').textContent = new Date().toLocaleTimeString();
            
            // Update memory status
            if (data.memory_status) {
                document.getElementById('memory-status').textContent = 
                    `Memory: ${data.memory_status.current_mb}MB (${data.memory_status.percent}%)`;
            }
            
            // Update stats
            if (data.stats) {
                document.getElementById('total-trades').textContent = data.stats.total_trades || 0;
                document.getElementById('total-pnl').textContent = `$${(data.stats.total_pnl || 0).toFixed(2)}`;
                document.getElementById('win-rate').textContent = `${(data.stats.win_rate || 0).toFixed(1)}%`;
                document.getElementById('equity').textContent = `$${(data.stats.equity || 0).toFixed(2)}`;
            }
            
            // Update trades table
            if (data.trades && data.trades.length > 0) {
                const tradesBody = document.getElementById('trades-body');
                tradesBody.innerHTML = data.trades.slice(-20).reverse().map(trade => {
                    const time = new Date(trade.timestamp).toLocaleTimeString();
                    const pnlClass = trade.pnl >= 0 ? 'profit' : 'loss';
                    
                    return `
                        <tr>
                            <td>${time}</td>
                            <td><strong>${trade.symbol}</strong></td>
                            <td class="${trade.side}">${trade.side.toUpperCase()}</td>
                            <td>${parseFloat(trade.amount).toFixed(6)}</td>
                            <td>$${parseFloat(trade.price).toFixed(4)}</td>
                            <td class="${pnlClass}">$${parseFloat(trade.pnl).toFixed(2)}</td>
                            <td>${trade.status}</td>
                        </tr>
                    `;
                }).join('');
            }
            
            // Update signals table
            if (data.signals && data.signals.length > 0) {
                const signalsBody = document.getElementById('signals-body');
                signalsBody.innerHTML = data.signals.slice(-20).reverse().map(signal => {
                    const time = new Date(signal.timestamp).toLocaleTimeString();
                    
                    return `
                        <tr>
                            <td>${time}</td>
                            <td><strong>${signal.symbol}</strong></td>
                            <td class="${signal.signal.toLowerCase()}">${signal.signal.toUpperCase()}</td>
                            <td>${(signal.confidence * 100).toFixed(1)}%</td>
                            <td>$${parseFloat(signal.price).toFixed(4)}</td>
                            <td>${signal.reason || 'Analysis'}</td>
                        </tr>
                    `;
                }).join('');
            }
            
            // Update market data
            if (data.market_data && data.market_data.length > 0) {
                const marketBody = document.getElementById('market-body');
                marketBody.innerHTML = data.market_data.map(market => {
                    const time = new Date(market.timestamp).toLocaleTimeString();
                    const changeClass = market.change_24h >= 0 ? 'profit' : 'loss';
                    
                    return `
                        <tr>
                            <td><strong>${market.symbol}</strong></td>
                            <td>$${parseFloat(market.price).toFixed(4)}</td>
                            <td class="${changeClass}">${parseFloat(market.change_24h).toFixed(2)}%</td>
                            <td>${parseInt(market.volume).toLocaleString()}</td>
                            <td>${time}</td>
                        </tr>
                    `;
                }).join('');
            }
            
            // Update logs
            if (data.logs) {
                document.getElementById('logs').innerHTML = data.logs.slice(-50).join('<br>');
            }
        }

        // Auto-refresh every 10 seconds
        setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({type: 'request_update'}));
            }
        }, 10000);

        // Connect on load
        connect();
    </script>
</body>
</html>
    """)

@app.get("/health")
async def health_check():
    """Simple health check"""
    memory = get_memory_usage()
    
    return {
        "status": "healthy" if memory < MAX_MEMORY_MB else "memory_warning",
        "memory_mb": round(memory, 1),
        "memory_limit_mb": MAX_MEMORY_MB,
        "timestamp": datetime.now().isoformat(),
        "websocket_connections": len(websocket_connections),
        "total_trades": len(trades_data),
        "total_signals": len(signals_data)
    }

# Background data simulation
async def simulate_data():
    """Generate demo trading data"""
    symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT', 'DOT/USDT']
    base_prices = {
        'BTC/USDT': 45000, 'ETH/USDT': 2800, 'BNB/USDT': 320,
        'ADA/USDT': 0.45, 'SOL/USDT': 95, 'DOT/USDT': 7.8
    }
    
    trade_id = 1
    
    while True:
        try:
            # Memory cleanup check
            cleanup_memory()
            
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
                
                trades_data.append(trade)
                portfolio_stats['total_trades'] += 1
                portfolio_stats['total_pnl'] += pnl
                
                # Update win rate
                profitable_trades = sum(1 for t in trades_data if t['pnl'] > 0)
                portfolio_stats['win_rate'] = (profitable_trades / len(trades_data)) * 100 if trades_data else 0
                
                log_message(f"💰 Trade: {side} {amount:.4f} {symbol} @ ${price:.2f} (P&L: ${pnl:.2f})")
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
                
                signals_data.append(signal_data)
                log_message(f"🎯 Signal: {signal} {symbol} ({confidence:.1%}) - {signal_data['reason']}")
            
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
                
                market_data.append(market)
            
            # Broadcast to WebSocket clients
            if websocket_connections:
                message = json.dumps({
                    'type': 'data_update',
                    'data': get_dashboard_data()
                })
                
                disconnected = set()
                for ws in websocket_connections.copy():
                    try:
                        await ws.send_text(message)
                    except:
                        disconnected.add(ws)
                
                for ws in disconnected:
                    websocket_connections.discard(ws)
            
            await asyncio.sleep(15)  # Update every 15 seconds
            
        except Exception as e:
            logger.error(f"❌ Simulation error: {e}")
            await asyncio.sleep(15)

@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    log_message("🚀 Bottie Working Dashboard started")
    
    # Start data simulation
    asyncio.create_task(simulate_data())
    
    # Start memory monitoring
    asyncio.create_task(memory_monitoring())
    
    logger.info("✅ Working dashboard ready!")

async def memory_monitoring():
    """Monitor memory usage"""
    while True:
        try:
            memory = get_memory_usage()
            
            if memory > MAX_MEMORY_MB * 0.9:
                logger.critical(f"🚨 CRITICAL: Memory at {memory:.1f}MB")
                cleanup_memory()
            elif memory > MAX_MEMORY_MB * 0.8:
                logger.warning(f"⚠️ HIGH MEMORY: {memory:.1f}MB")
            
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"❌ Memory monitoring error: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    log_message(f"🚀 Starting on port {port}")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info",
        access_log=False,
        workers=1
    )