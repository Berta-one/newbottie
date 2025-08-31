#!/usr/bin/env python3
"""
Ultra-minimal dashboard - guaranteed under 512MB
Single file, minimal dependencies, maximum efficiency
"""

import asyncio
import json
import os
import gc
import time
from datetime import datetime
from typing import List, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from collections import deque
import random

# Ultra-minimal configuration  
MAX_TRADES = 100      # Very small cache
MAX_SIGNALS = 100     # Very small cache
MAX_LOGS = 50         # Minimal logs
UPDATE_INTERVAL = 30  # Less frequent updates

# Simple data storage
trades = deque(maxlen=MAX_TRADES)
signals = deque(maxlen=MAX_SIGNALS) 
logs = deque(maxlen=MAX_LOGS)
connections = set()

# Stats
stats = {'trades': 0, 'pnl': 0.0, 'equity': 10000.0}

def log(msg: str):
    """Add log entry"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    logs.append(f"[{timestamp}] {msg}")
    print(f"[{timestamp}] {msg}")

# Minimal FastAPI app
app = FastAPI(title="Minimal Bottie", docs_url=None, redoc_url=None)

@app.get("/")
async def dashboard():
    """Serve ultra-minimal dashboard"""
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>Bottie Minimal Dashboard</title>
    <style>
        body { font-family: monospace; background: #000; color: #0f0; margin: 0; padding: 10px; }
        .header { border-bottom: 1px solid #0f0; padding: 10px 0; margin-bottom: 20px; }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; }
        .stat { border: 1px solid #333; padding: 10px; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        th, td { border: 1px solid #333; padding: 5px; font-size: 12px; }
        th { background: #333; }
        .buy { color: #0f0; }
        .sell { color: #f44; }
        .profit { color: #0f0; }
        .loss { color: #f44; }
        .logs { height: 150px; overflow-y: auto; background: #111; padding: 5px; border: 1px solid #333; font-size: 11px; }
        #status { color: #ff0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Bottie Minimal Dashboard</h1>
        <div>Status: <span id="status">Connecting...</span> | Memory Optimized | Real-time Tables</div>
    </div>

    <div class="stats">
        <div class="stat">Trades: <span id="trade-count">0</span></div>
        <div class="stat">P&L: $<span id="pnl">0.00</span></div>
        <div class="stat">Equity: $<span id="equity">10000</span></div>
        <div class="stat">Memory: <span id="memory">--MB</span></div>
    </div>

    <h3>📊 Recent Trades</h3>
    <table>
        <tr><th>Time</th><th>Symbol</th><th>Side</th><th>Amount</th><th>Price</th><th>P&L</th></tr>
        <tbody id="trades-table"><tr><td colspan="6">Loading...</td></tr></tbody>
    </table>

    <h3>🎯 Trading Signals</h3>
    <table>
        <tr><th>Time</th><th>Symbol</th><th>Signal</th><th>Confidence</th><th>Price</th></tr>
        <tbody id="signals-table"><tr><td colspan="5">Loading...</td></tr></tbody>
    </table>

    <h3>📝 System Logs</h3>
    <div id="logs" class="logs">Loading...</div>

    <script>
        let ws;
        
        function connect() {
            const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`;
            ws = new WebSocket(wsUrl);
            
            ws.onopen = () => {
                document.getElementById('status').textContent = 'Connected';
                ws.send('{"type":"get_data"}');
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateTables(data);
            };
            
            ws.onclose = () => {
                document.getElementById('status').textContent = 'Disconnected';
                setTimeout(connect, 3000);
            };
        }
        
        function updateTables(data) {
            // Update stats
            document.getElementById('trade-count').textContent = data.stats?.trades || 0;
            document.getElementById('pnl').textContent = (data.stats?.pnl || 0).toFixed(2);
            document.getElementById('equity').textContent = (data.stats?.equity || 0).toFixed(2);
            document.getElementById('memory').textContent = (data.memory || 0).toFixed(1) + 'MB';
            
            // Update trades table
            if (data.trades) {
                const tradesHtml = data.trades.map(t => `
                    <tr>
                        <td>${new Date(t.timestamp).toLocaleTimeString()}</td>
                        <td>${t.symbol}</td>
                        <td class="${t.side}">${t.side.toUpperCase()}</td>
                        <td>${t.amount.toFixed(4)}</td>
                        <td>$${t.price.toFixed(2)}</td>
                        <td class="${t.pnl >= 0 ? 'profit' : 'loss'}">$${t.pnl.toFixed(2)}</td>
                    </tr>
                `).join('');
                document.getElementById('trades-table').innerHTML = tradesHtml;
            }
            
            // Update signals table
            if (data.signals) {
                const signalsHtml = data.signals.map(s => `
                    <tr>
                        <td>${new Date(s.timestamp).toLocaleTimeString()}</td>
                        <td>${s.symbol}</td>
                        <td class="${s.signal.toLowerCase()}">${s.signal}</td>
                        <td>${(s.confidence * 100).toFixed(1)}%</td>
                        <td>$${s.price.toFixed(2)}</td>
                    </tr>
                `).join('');
                document.getElementById('signals-table').innerHTML = signalsHtml;
            }
            
            // Update logs
            if (data.logs) {
                document.getElementById('logs').innerHTML = data.logs.join('<br>');
                document.getElementById('logs').scrollTop = document.getElementById('logs').scrollHeight;
            }
        }
        
        // Auto-refresh
        setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send('{"type":"get_data"}');
            }
        }, 10000);
        
        connect();
    </script>
</body>
</html>""")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Minimal WebSocket handler"""
    await websocket.accept()
    connections.add(websocket)
    log(f"WebSocket connected: {len(connections)} total")
    
    try:
        while True:
            await websocket.receive_text()  # Wait for client request
            
            # Get memory usage
            try:
                import psutil
                memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
            except:
                memory_mb = 0
            
            # Send data
            await websocket.send_text(json.dumps({
                'trades': list(trades)[-20:],
                'signals': list(signals)[-20:], 
                'logs': list(logs)[-30:],
                'stats': stats,
                'memory': memory_mb
            }))
            
    except WebSocketDisconnect:
        connections.discard(websocket)
        log(f"WebSocket disconnected: {len(connections)} remaining")

@app.get("/health")
def health():
    """Simple health check"""
    try:
        import psutil
        memory = psutil.Process().memory_info().rss / 1024 / 1024
        status = "healthy" if memory < 400 else "warning"
    except:
        memory = 0
        status = "unknown"
    
    return {
        "status": status,
        "memory_mb": round(memory, 1),
        "trades": len(trades),
        "signals": len(signals),
        "connections": len(connections)
    }

# Background data generation
async def generate_data():
    """Generate minimal demo data"""
    symbols = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'SOL/USDT']
    prices = {'BTC/USDT': 45000, 'ETH/USDT': 2800, 'ADA/USDT': 0.45, 'SOL/USDT': 95}
    
    trade_id = 1
    
    while True:
        try:
            # Memory cleanup
            try:
                import psutil
                memory = psutil.Process().memory_info().rss / 1024 / 1024
                if memory > 300:  # Conservative threshold
                    gc.collect()
                    log(f"Memory cleanup: {memory:.1f}MB")
            except:
                gc.collect()
            
            # Generate trade (20% chance)
            if random.random() < 0.2:
                symbol = random.choice(symbols)
                side = random.choice(['buy', 'sell'])
                amount = random.uniform(0.01, 0.5)
                price = prices[symbol] * random.uniform(0.98, 1.02)
                pnl = random.uniform(-20, 50)
                
                trade = {
                    'id': trade_id,
                    'symbol': symbol,
                    'side': side,
                    'amount': amount,
                    'price': price,
                    'pnl': pnl,
                    'timestamp': datetime.now().isoformat()
                }
                
                trades.append(trade)
                stats['trades'] += 1
                stats['pnl'] += pnl
                
                log(f"Trade: {side} {amount:.4f} {symbol} @ ${price:.2f}")
                trade_id += 1
            
            # Generate signal (30% chance)
            if random.random() < 0.3:
                symbol = random.choice(symbols)
                signal_type = random.choice(['BUY', 'SELL', 'HOLD'])
                confidence = random.uniform(0.6, 0.9)
                price = prices[symbol] * random.uniform(0.99, 1.01)
                
                signal = {
                    'symbol': symbol,
                    'signal': signal_type,
                    'confidence': confidence,
                    'price': price,
                    'timestamp': datetime.now().isoformat()
                }
                
                signals.append(signal)
                log(f"Signal: {signal_type} {symbol} ({confidence:.1%})")
            
            # Broadcast to WebSocket clients
            if connections:
                try:
                    import psutil
                    memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
                except:
                    memory_mb = 0
                
                message = json.dumps({
                    'trades': list(trades)[-20:],
                    'signals': list(signals)[-20:],
                    'logs': list(logs)[-30:],
                    'stats': stats,
                    'memory': memory_mb
                })
                
                disconnected = set()
                for ws in connections.copy():
                    try:
                        await ws.send_text(message)
                    except:
                        disconnected.add(ws)
                
                for ws in disconnected:
                    connections.discard(ws)
            
            await asyncio.sleep(UPDATE_INTERVAL)
            
        except Exception as e:
            log(f"Error: {e}")
            await asyncio.sleep(30)

@app.on_event("startup")
async def startup():
    """Start background tasks"""
    log("🚀 Minimal dashboard started")
    asyncio.create_task(generate_data())

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    log(f"Starting minimal dashboard on port {port}")
    
    # Force garbage collection before starting
    gc.collect()
    
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=port,
        log_level="warning",  # Minimal logging
        access_log=False,     # No access logs
        workers=1,            # Single worker
        loop="asyncio"
    )