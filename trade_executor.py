#!/usr/bin/env python3
"""
FIXED TradeExecutor - Resolves -2015 API Errors
===============================================
This version properly handles USE_TESTNET environment variable
and fixes the API URL configuration issues
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    Client = None
    BinanceAPIException = Exception

class TradeExecutor:
    """
    Fixed Trade Executor that properly handles API endpoints
    """
    
    def __init__(self, client=None, risk_manager=None, log_callback=None):
        self.client = client
        self.risk_manager = risk_manager
        self.active_orders = {}
        self.log = log_callback if log_callback else print
        
        # CRITICAL FIX: Ensure client uses correct API URL
        if self.client:
            self._configure_client_endpoint()
    
    def _configure_client_endpoint(self):
        """
        CRITICAL FIX: Configure the correct API endpoint based on USE_TESTNET
        This fixes the -2015 errors
        """
        try:
            use_testnet = os.getenv('USE_TESTNET', 'false').lower() == 'true'
            
            if use_testnet:
                self.client.API_URL = 'https://testnet.binance.vision/api'
                self.log("🧪 TradeExecutor: Using TESTNET endpoint")
            else:
                # Ensure we're using live endpoint (default)
                self.client.API_URL = 'https://api.binance.com/api'
                self.log("🚀 TradeExecutor: Using LIVE endpoint")
                
            # Test the connection immediately
            self.client.get_server_time()
            self.log("✅ TradeExecutor: API connection verified")
            
        except Exception as e:
            self.log(f"❌ TradeExecutor: API configuration failed - {e}")
    
    def manual_trade(self, symbol: str, qty: float, sl_mult: float = 1.5, tp_mult: float = 3.0, atr_value: Optional[float] = None, trade_amount_usd: Optional[float] = None) -> str:
        """
        Execute manual trade with proper error handling
        """
        if not self.client:
            return "❌ No API client available"
        
        try:
            # Reconfigure endpoint before each trade (safety measure)
            self._configure_client_endpoint()
            
            # Get current price
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            price = float(ticker["price"])

            # Allow optional USD-based trade sizing
            if trade_amount_usd is not None:
                qty = trade_amount_usd / price
            
            self.log(f"🎯 Executing trade: {symbol} @ ${price:,.4f}, Qty: {qty}")
            
            # Execute market buy order
            order = self.client.order_market_buy(
                symbol=symbol, 
                quantity=qty
            )
            
            self.log(f"✅ BUY order executed: {symbol} @ {price} Qty={qty}")
            
            # Set up stop-loss and take-profit if ATR provided
            if atr_value:
                stop_price = round(price - atr_value * sl_mult, 2)
                tp_price = round(price + atr_value * tp_mult, 2)
                
                try:
                    oco = self.client.create_oco_order(
                        symbol=symbol,
                        side="SELL",
                        quantity=qty,
                        price=str(tp_price),
                        stopPrice=str(stop_price),
                        stopLimitPrice=str(stop_price * 0.999),
                        stopLimitTimeInForce="GTC"
                    )
                    self.active_orders[symbol] = oco
                    self.log(f"✅ OCO order set: SL=${stop_price}, TP=${tp_price}")
                except Exception as oco_error:
                    self.log(f"⚠️ OCO order failed: {oco_error}")
            
            return f"✅ Trade executed successfully: BUY {qty} {symbol} @ ${price:,.4f}"
            
        except BinanceAPIException as api_error:
            error_msg = f"❌ Binance API Error: {api_error}"
            self.log(error_msg)
            
            # Specific error handling
            if api_error.code == -2015:
                additional_info = "🔧 Fix: Check API permissions and IP whitelist"
                self.log(additional_info)
                return f"{error_msg} - {additional_info}"
            elif api_error.code == -2014:
                additional_info = "🔧 Fix: Check API key format"
                self.log(additional_info)
                return f"{error_msg} - {additional_info}"
            else:
                return error_msg
                
        except Exception as e:
            error_msg = f"❌ Trade execution failed: {e}"
            self.log(error_msg)
            return error_msg
    
    def auto_execute(self, signal: Dict[str, Any], total_balance: float, open_positions: int, sl_mult: float = 1.5, tp_mult: float = 3.0) -> str:
        """
        Auto-execute trade based on signal
        """
        if not signal or signal.get("decision") != "BUY":
            return "⏭️ Skipped: Non-BUY signal"
        
        symbol = signal["symbol"]
        
        try:
            # Get current price
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            price = float(ticker["price"])
            
            # Calculate position size (1% of balance)
            position_value = total_balance * 0.01
            qty = round(position_value / price, 6)
            
            # Risk validation
            if self.risk_manager:
                validation = self.risk_manager.validate_trade(symbol, qty, price, total_balance, open_positions)
                if not validation.get("status", False):
                    return f"❌ Risk check failed: {validation.get('reason', 'Unknown')}"
            
            # Execute trade
            atr_value = signal.get("atr", price * 0.02)  # Default 2% ATR
            return self.manual_trade(symbol, qty, sl_mult, tp_mult, atr_value)
            
        except Exception as e:
            return f"❌ Auto-execution failed: {e}"
    
    def get_active_orders(self) -> Dict[str, Any]:
        """Get all active orders"""
        return self.active_orders.copy()
    
    def cancel_order(self, symbol: str) -> str:
        """Cancel active order for symbol"""
        if symbol not in self.active_orders:
            return f"❌ No active order for {symbol}"
        
        try:
            order_id = self.active_orders[symbol].get('orderListId')
            if order_id:
                self.client.cancel_order_list(symbol=symbol, orderListId=order_id)
                del self.active_orders[symbol]
                return f"✅ Cancelled order for {symbol}"
            else:
                return f"❌ Invalid order ID for {symbol}"
        except Exception as e:
            return f"❌ Cancel failed: {e}"
    
    def get_connection_status(self) -> str:
        """Get connection status"""
        if not self.client:
            return "❌ No client configured"
        
        try:
            use_testnet = os.getenv('USE_TESTNET', 'false').lower() == 'true'
            mode = "🧪 TESTNET" if use_testnet else "🚀 LIVE"
            
            # Test connection
            server_time = self.client.get_server_time()
            return f"✅ Connected to Binance {mode}"
            
        except Exception as e:
            return f"❌ Connection failed: {e}"


# Fallback class for when Binance is not available
class FallbackTradeExecutor:
    """Fallback trade executor for demo purposes"""
    
    def __init__(self, client=None, risk_manager=None, log_callback=None):
        self.log = log_callback if log_callback else print
        self.active_orders = {}
    
    def manual_trade(self, symbol: str, qty: float, sl_mult: float = 1.5, tp_mult: float = 3.0, atr_value: Optional[float] = None, trade_amount_usd: Optional[float] = None) -> str:
        if trade_amount_usd is not None:
            qty = trade_amount_usd  # In demo mode qty represents USD value
        self.log(f"📝 DEMO: Would execute BUY {qty} {symbol}")
        return f"📝 Demo trade: BUY {qty} {symbol} (API not available)"
    
    def auto_execute(self, signal: Dict[str, Any], total_balance: float, open_positions: int, sl_mult: float = 1.5, tp_mult: float = 3.0) -> str:
        symbol = signal.get("symbol", "UNKNOWN")
        return f"📝 Demo auto-trade: {symbol} (API not available)"
    
    def get_active_orders(self) -> Dict[str, Any]:
        return {}
    
    def cancel_order(self, symbol: str) -> str:
        return f"📝 Demo: Would cancel order for {symbol}"
    
    def get_connection_status(self) -> str:
        return "📝 Demo mode - Binance API not available"


# Factory function to create appropriate executor
def create_trade_executor(client=None, risk_manager=None, log_callback=None):
    """Create appropriate trade executor based on available dependencies"""
    if BINANCE_AVAILABLE and client:
        return TradeExecutor(client, risk_manager, log_callback)
    else:
        return FallbackTradeExecutor(client, risk_manager, log_callback)
