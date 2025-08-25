#!/usr/bin/env python3
"""
P&L Integration Module for Sntax Trading System
Connects existing trading API to WebSocket P&L server
"""

import asyncio
import websockets
import json
import time
import requests
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PnLIntegration:
    def __init__(self, api_base="http://localhost:8000", ws_url="ws://localhost:8765"):
        self.api_base = api_base
        self.ws_url = ws_url
        self.ws = None
        self.running = False
        
    async def connect_websocket(self):
        """Connect to P&L WebSocket server"""
        try:
            self.ws = await websockets.connect(self.ws_url)
            logger.info("✅ Connected to P&L WebSocket server")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to P&L WebSocket: {e}")
            return False
    
    async def send_trade_to_pnl(self, trade_data):
        """Send trade data to P&L server via WebSocket"""
        if not self.ws:
            await self.connect_websocket()
        
        if self.ws:
            try:
                message = {
                    "type": "new_trade",
                    "data": trade_data
                }
                await self.ws.send(json.dumps(message))
                logger.info(f"✅ Sent trade to P&L server: {trade_data.get('symbol')} {trade_data.get('side')}")
            except Exception as e:
                logger.error(f"❌ Failed to send trade to P&L server: {e}")
    
    def fetch_recent_trades_from_api(self):
        """Fetch recent trades from the main API"""
        try:
            response = requests.get(f"{self.api_base}/trades/recent", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('trades', [])
            else:
                logger.warning(f"⚠️ API returned status {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"❌ Error fetching trades from API: {e}")
            return []
    
    def calculate_trade_pnl(self, trade, current_prices):
        """Calculate P&L for a trade"""
        try:
            symbol = trade.get('symbol', '')
            side = trade.get('side', '').lower()
            amount = float(trade.get('amount', 0))
            entry_price = float(trade.get('price', 0))
            
            current_price = current_prices.get(symbol, entry_price)
            
            if side == 'buy':
                pnl = amount * (current_price - entry_price)
            else:  # sell
                pnl = amount * (entry_price - current_price)
            
            return pnl
        except Exception as e:
            logger.error(f"❌ Error calculating P&L: {e}")
            return 0
    
    def fetch_current_prices(self):
        """Fetch current prices from the API"""
        try:
            response = requests.get(f"{self.api_base}/crypto/prices", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('prices', {})
            else:
                return {}
        except Exception as e:
            logger.error(f"❌ Error fetching current prices: {e}")
            return {}
    
    async def sync_trades_to_pnl(self):
        """Sync recent trades to P&L system"""
        logger.info("🔄 Syncing trades to P&L system...")
        
        # Fetch recent trades
        trades = self.fetch_recent_trades_from_api()
        current_prices = self.fetch_current_prices()
        
        for trade in trades:
            # Calculate P&L
            pnl = self.calculate_trade_pnl(trade, current_prices)
            
            # Prepare trade data for P&L system
            pnl_trade_data = {
                "id": trade.get('id', f"sync_{int(time.time() * 1000)}"),
                "symbol": trade.get('symbol', ''),
                "side": trade.get('side', ''),
                "amount": trade.get('amount', 0),
                "price": trade.get('price', 0),
                "cost": trade.get('cost', trade.get('amount', 0) * trade.get('price', 0)),
                "fee": trade.get('fee', {}),
                "timestamp": trade.get('timestamp', int(time.time() * 1000)),
                "datetime": trade.get('datetime', datetime.now().isoformat()),
                "status": trade.get('status', 'closed'),
                "pnl": pnl
            }
            
            # Send to P&L system
            await self.send_trade_to_pnl(pnl_trade_data)
        
        logger.info(f"✅ Synced {len(trades)} trades to P&L system")
    
    async def monitor_api_for_new_trades(self):
        """Monitor the API for new trades and sync them"""
        last_check = time.time()
        
        while self.running:
            try:
                # Check for new trades since last check
                trades = self.fetch_recent_trades_from_api()
                current_prices = self.fetch_current_prices()
                
                new_trades = [
                    trade for trade in trades 
                    if trade.get('timestamp', 0) > last_check * 1000
                ]
                
                if new_trades:
                    logger.info(f"🆕 Found {len(new_trades)} new trades")
                    
                    for trade in new_trades:
                        pnl = self.calculate_trade_pnl(trade, current_prices)
                        
                        pnl_trade_data = {
                            "id": trade.get('id', f"new_{int(time.time() * 1000)}"),
                            "symbol": trade.get('symbol', ''),
                            "side": trade.get('side', ''),
                            "amount": trade.get('amount', 0),
                            "price": trade.get('price', 0),
                            "cost": trade.get('cost', trade.get('amount', 0) * trade.get('price', 0)),
                            "fee": trade.get('fee', {}),
                            "timestamp": trade.get('timestamp', int(time.time() * 1000)),
                            "datetime": trade.get('datetime', datetime.now().isoformat()),
                            "status": trade.get('status', 'closed'),
                            "pnl": pnl
                        }
                        
                        await self.send_trade_to_pnl(pnl_trade_data)
                
                last_check = time.time()
                
                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"❌ Error in trade monitoring: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def start_integration(self):
        """Start the P&L integration service"""
        self.running = True
        logger.info("🚀 Starting P&L integration service...")
        
        # Connect to WebSocket
        connected = await self.connect_websocket()
        if not connected:
            logger.error("❌ Could not connect to P&L WebSocket server")
            return
        
        # Initial sync
        await self.sync_trades_to_pnl()
        
        # Start monitoring for new trades
        await self.monitor_api_for_new_trades()
    
    def stop_integration(self):
        """Stop the integration service"""
        self.running = False
        if self.ws:
            asyncio.create_task(self.ws.close())

async def main():
    """Main function to run the integration"""
    logging.basicConfig(level=logging.INFO)
    
    print("🔗 Sntax P&L Integration Service")
    print("=" * 40)
    print("This service connects your trading API to the P&L WebSocket server")
    print("Features:")
    print("  - Real-time trade synchronization")
    print("  - Automatic P&L calculation")
    print("  - WebSocket-based updates")
    print("\n🎯 Starting integration...")
    
    integration = PnLIntegration()
    
    try:
        await integration.start_integration()
    except KeyboardInterrupt:
        print("\n🛑 Integration stopped by user")
        integration.stop_integration()
    except Exception as e:
        print(f"❌ Integration error: {e}")

if __name__ == "__main__":
    asyncio.run(main())