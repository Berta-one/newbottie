#!/usr/bin/env python3
"""
WebSocket-based P&L Reporting System for Sntax Trading
Real-time trade tracking and P&L calculation since August 1st
"""

import asyncio
import websockets
import json
import sqlite3
from datetime import datetime, timezone
import time
import ccxt
import os
from typing import Dict, List, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradeDatabase:
    def __init__(self, db_path="trades_pnl.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for trade storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                amount REAL NOT NULL,
                price REAL NOT NULL,
                cost REAL NOT NULL,
                fee REAL DEFAULT 0,
                timestamp INTEGER NOT NULL,
                datetime TEXT NOT NULL,
                status TEXT DEFAULT 'open',
                entry_price REAL,
                exit_price REAL,
                pnl REAL DEFAULT 0,
                pnl_percentage REAL DEFAULT 0,
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        ''')
        
        # Create P&L summary table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pnl_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                symbol TEXT NOT NULL,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                total_pnl REAL DEFAULT 0,
                total_volume REAL DEFAULT 0,
                win_rate REAL DEFAULT 0,
                avg_win REAL DEFAULT 0,
                avg_loss REAL DEFAULT 0,
                largest_win REAL DEFAULT 0,
                largest_loss REAL DEFAULT 0,
                updated_at INTEGER DEFAULT (strftime('%s', 'now')),
                UNIQUE(date, symbol)
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)')
        
        conn.commit()
        conn.close()
        logger.info("✅ Trade database initialized")
    
    def store_trade(self, trade_data: dict):
        """Store a trade in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO trades 
                (trade_id, symbol, side, amount, price, cost, fee, timestamp, datetime, status, pnl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade_data.get('id', ''),
                trade_data.get('symbol', ''),
                trade_data.get('side', ''),
                trade_data.get('amount', 0),
                trade_data.get('price', 0),
                trade_data.get('cost', 0),
                trade_data.get('fee', {}).get('cost', 0) if trade_data.get('fee') else 0,
                trade_data.get('timestamp', int(time.time() * 1000)),
                trade_data.get('datetime', datetime.now().isoformat()),
                trade_data.get('status', 'closed'),
                trade_data.get('pnl', 0)
            ))
            conn.commit()
            logger.info(f"✅ Stored trade: {trade_data.get('symbol')} {trade_data.get('side')} {trade_data.get('amount')}")
        except Exception as e:
            logger.error(f"❌ Error storing trade: {e}")
        finally:
            conn.close()
    
    def get_trades_since_date(self, since_date: str = "2024-08-01") -> List[dict]:
        """Get all trades since specified date"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert date to timestamp
        since_timestamp = int(datetime.strptime(since_date, "%Y-%m-%d").timestamp() * 1000)
        
        cursor.execute('''
            SELECT * FROM trades 
            WHERE timestamp >= ? 
            ORDER BY timestamp DESC
        ''', (since_timestamp,))
        
        columns = [description[0] for description in cursor.description]
        trades = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return trades
    
    def calculate_pnl_summary(self, since_date: str = "2024-08-01") -> dict:
        """Calculate comprehensive P&L summary"""
        trades = self.get_trades_since_date(since_date)
        
        if not trades:
            return {
                "total_trades": 0,
                "total_pnl": 0,
                "win_rate": 0,
                "summary": {}
            }
        
        # Group by symbol for detailed analysis
        symbol_stats = {}
        total_pnl = 0
        total_trades = len(trades)
        winning_trades = 0
        
        for trade in trades:
            symbol = trade['symbol']
            pnl = trade['pnl'] or 0
            
            if symbol not in symbol_stats:
                symbol_stats[symbol] = {
                    "trades": 0,
                    "total_pnl": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "total_volume": 0,
                    "wins": [],
                    "losses": []
                }
            
            symbol_stats[symbol]["trades"] += 1
            symbol_stats[symbol]["total_pnl"] += pnl
            symbol_stats[symbol]["total_volume"] += trade['cost'] or 0
            
            if pnl > 0:
                symbol_stats[symbol]["winning_trades"] += 1
                symbol_stats[symbol]["wins"].append(pnl)
                winning_trades += 1
            elif pnl < 0:
                symbol_stats[symbol]["losing_trades"] += 1
                symbol_stats[symbol]["losses"].append(pnl)
            
            total_pnl += pnl
        
        # Calculate additional metrics
        for symbol in symbol_stats:
            stats = symbol_stats[symbol]
            stats["win_rate"] = (stats["winning_trades"] / stats["trades"] * 100) if stats["trades"] > 0 else 0
            stats["avg_win"] = sum(stats["wins"]) / len(stats["wins"]) if stats["wins"] else 0
            stats["avg_loss"] = sum(stats["losses"]) / len(stats["losses"]) if stats["losses"] else 0
            stats["largest_win"] = max(stats["wins"]) if stats["wins"] else 0
            stats["largest_loss"] = min(stats["losses"]) if stats["losses"] else 0
            
            # Remove raw win/loss arrays for JSON serialization
            del stats["wins"]
            del stats["losses"]
        
        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": total_trades - winning_trades,
            "total_pnl": total_pnl,
            "win_rate": (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            "avg_pnl_per_trade": total_pnl / total_trades if total_trades > 0 else 0,
            "symbol_breakdown": symbol_stats,
            "period": f"Since {since_date}",
            "last_updated": datetime.now().isoformat()
        }

class PnLWebSocketServer:
    def __init__(self):
        self.db = TradeDatabase()
        self.connected_clients = set()
        self.exchange_client = None
        self.running = False
        self.init_exchange()
    
    def init_exchange(self):
        """Initialize exchange client for real-time data"""
        try:
            # Try to initialize exchange client
            api_key = os.getenv('BINANCE_API_KEY')
            api_secret = os.getenv('BINANCE_API_SECRET')
            
            if api_key and api_secret:
                self.exchange_client = ccxt.binance({
                    'apiKey': api_key,
                    'secret': api_secret,
                    'sandbox': False,
                    'enableRateLimit': True,
                })
                logger.info("✅ Exchange client initialized")
            else:
                logger.warning("⚠️ No exchange credentials found - using demo mode")
        except Exception as e:
            logger.error(f"❌ Exchange initialization failed: {e}")
    
    async def register_client(self, websocket):
        """Register a new WebSocket client"""
        self.connected_clients.add(websocket)
        logger.info(f"✅ Client connected. Total clients: {len(self.connected_clients)}")
        
        # Send initial P&L data to new client
        await self.send_pnl_update(websocket)
    
    async def unregister_client(self, websocket):
        """Unregister a WebSocket client"""
        self.connected_clients.discard(websocket)
        logger.info(f"❌ Client disconnected. Total clients: {len(self.connected_clients)}")
    
    async def send_pnl_update(self, websocket=None):
        """Send P&L update to client(s)"""
        try:
            # Calculate current P&L summary
            pnl_summary = self.db.calculate_pnl_summary()
            
            # Get recent trades (last 50)
            recent_trades = self.db.get_trades_since_date()[:50]
            
            message = {
                "type": "pnl_update",
                "timestamp": int(time.time() * 1000),
                "data": {
                    "summary": pnl_summary,
                    "recent_trades": recent_trades
                }
            }
            
            if websocket:
                # Send to specific client
                await websocket.send(json.dumps(message))
            else:
                # Broadcast to all clients
                if self.connected_clients:
                    await asyncio.gather(
                        *[client.send(json.dumps(message)) for client in self.connected_clients],
                        return_exceptions=True
                    )
        except Exception as e:
            logger.error(f"❌ Error sending P&L update: {e}")
    
    async def simulate_trade(self, symbol="BTCUSDT", side="buy", amount=0.001):
        """Simulate a trade for testing purposes"""
        try:
            # Get current price (or simulate)
            current_price = 45000  # Default fallback
            
            if self.exchange_client:
                try:
                    ticker = self.exchange_client.fetch_ticker(symbol)
                    current_price = ticker['last']
                except:
                    pass
            
            # Create simulated trade
            trade_data = {
                "id": f"sim_{int(time.time() * 1000)}",
                "symbol": symbol,
                "side": side,
                "amount": amount,
                "price": current_price,
                "cost": amount * current_price,
                "fee": {"cost": amount * current_price * 0.001},  # 0.1% fee
                "timestamp": int(time.time() * 1000),
                "datetime": datetime.now().isoformat(),
                "status": "closed",
                "pnl": (amount * current_price * 0.02) * (1 if side == "buy" else -1)  # Simulate 2% P&L
            }
            
            # Store trade
            self.db.store_trade(trade_data)
            
            # Broadcast update
            await self.send_pnl_update()
            
            logger.info(f"✅ Simulated trade: {symbol} {side} {amount} @ ${current_price}")
            
        except Exception as e:
            logger.error(f"❌ Error simulating trade: {e}")
    
    async def handle_client_message(self, websocket, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "get_pnl_report":
                # Send P&L report
                await self.send_pnl_update(websocket)
                
            elif msg_type == "simulate_trade":
                # Simulate a trade for testing
                symbol = data.get("symbol", "BTCUSDT")
                side = data.get("side", "buy")
                amount = data.get("amount", 0.001)
                await self.simulate_trade(symbol, side, amount)
                
            elif msg_type == "get_trades":
                # Get trades for specific period
                since_date = data.get("since_date", "2024-08-01")
                trades = self.db.get_trades_since_date(since_date)
                
                response = {
                    "type": "trades_response",
                    "data": trades
                }
                await websocket.send(json.dumps(response))
                
        except Exception as e:
            logger.error(f"❌ Error handling client message: {e}")
    
    async def handle_client(self, websocket, path):
        """Handle WebSocket client connection"""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
    
    async def periodic_updates(self):
        """Send periodic P&L updates"""
        while self.running:
            try:
                await asyncio.sleep(10)  # Update every 10 seconds
                if self.connected_clients:
                    await self.send_pnl_update()
            except Exception as e:
                logger.error(f"❌ Error in periodic updates: {e}")
    
    async def start_server(self, host="localhost", port=8765):
        """Start the WebSocket server"""
        self.running = True
        
        logger.info(f"🚀 Starting P&L WebSocket server on {host}:{port}")
        
        # Start periodic updates task
        update_task = asyncio.create_task(self.periodic_updates())
        
        # Start WebSocket server
        server = await websockets.serve(self.handle_client, host, port)
        
        logger.info("✅ P&L WebSocket server started")
        logger.info("📊 Features available:")
        logger.info("  - Real-time P&L tracking")
        logger.info("  - Trade storage since August 1st")
        logger.info("  - WebSocket-based updates")
        logger.info("  - Comprehensive trade analytics")
        
        try:
            await server.wait_closed()
        finally:
            self.running = False
            update_task.cancel()

# Standalone server script
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Sntax P&L WebSocket Server")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8765, help="Server port")
    parser.add_argument("--simulate", action="store_true", help="Add sample trades for testing")
    
    args = parser.parse_args()
    
    # Create server instance
    server = PnLWebSocketServer()
    
    # Add sample trades if requested
    if args.simulate:
        print("📊 Adding sample trades for testing...")
        import random
        
        sample_trades = [
            {"symbol": "BTCUSDT", "side": "buy", "amount": 0.001, "price": 45000, "pnl": 450},
            {"symbol": "ETHUSDT", "side": "sell", "amount": 0.1, "price": 2800, "pnl": -28},
            {"symbol": "ADAUSDT", "side": "buy", "amount": 100, "price": 0.45, "pnl": 2.25},
            {"symbol": "BTCUSDT", "side": "sell", "amount": 0.0005, "price": 46000, "pnl": -11.5},
            {"symbol": "ETHUSDT", "side": "buy", "amount": 0.05, "price": 2750, "pnl": 13.75},
        ]
        
        for i, trade in enumerate(sample_trades):
            trade_data = {
                "id": f"sample_{i}",
                "symbol": trade["symbol"],
                "side": trade["side"],
                "amount": trade["amount"],
                "price": trade["price"],
                "cost": trade["amount"] * trade["price"],
                "fee": {"cost": trade["amount"] * trade["price"] * 0.001},
                "timestamp": int((time.time() - (i * 3600)) * 1000),  # Spread over hours
                "datetime": datetime.fromtimestamp(time.time() - (i * 3600)).isoformat(),
                "status": "closed",
                "pnl": trade["pnl"]
            }
            server.db.store_trade(trade_data)
        
        print("✅ Sample trades added")
    
    # Start server
    try:
        asyncio.run(server.start_server(args.host, args.port))
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")