#!/usr/bin/env python3
"""
Real-Time Trade Execution Monitor
This script will capture and log exactly what happens during trade execution
"""

import os
import sys
import time
import json
from datetime import datetime
from dotenv import load_dotenv

class TradeExecutionMonitor:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_API_SECRET')
        self.use_testnet = os.getenv('USE_TESTNET', 'False').lower() == 'true'
        self.client = None
        self.log_file = f'logs/trade_execution_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
    
    def log_event(self, event_type, message, data=None):
        """Log events with timestamp"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'event_type': event_type,
            'message': message,
            'data': data
        }
        
        # Print to console
        print(f"[{timestamp}] {event_type}: {message}")
        if data:
            print(f"  Data: {json.dumps(data, indent=2)}")
        
        # Save to log file
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"Failed to write log: {e}")
    
    def initialize_client(self):
        """Initialize Binance client with detailed logging"""
        self.log_event("INIT", "Initializing Binance client...")
        
        try:
            from binance.client import Client
            from binance.exceptions import BinanceAPIException
            
            self.BinanceAPIException = BinanceAPIException
            
            if not self.api_key or not self.api_secret:
                self.log_event("ERROR", "Missing API credentials")
                return False
            
            self.client = Client(self.api_key, self.api_secret)
            
            if self.use_testnet:
                self.client.API_URL = 'https://testnet.binance.vision/api'
                self.log_event("INFO", "Using Binance Testnet")
            else:
                self.log_event("WARNING", "Using LIVE Binance - REAL MONEY!")
            
            # Test connection
            account = self.client.get_account()
            
            self.log_event("SUCCESS", "Client initialized successfully", {
                'account_type': account.get('accountType'),
                'can_trade': account.get('canTrade'),
                'can_withdraw': account.get('canWithdraw')
            })
            
            return True
            
        except ImportError:
            self.log_event("ERROR", "Binance library not installed - run: pip install python-binance")
            return False
        except Exception as e:
            self.log_event("ERROR", f"Client initialization failed: {e}")
            return False
    
    def check_account_status(self):
        """Check account balance and trading permissions"""
        self.log_event("CHECK", "Checking account status...")
        
        try:
            account = self.client.get_account()
            
            if not account.get('canTrade'):
                self.log_event("ERROR", "Trading permissions disabled on account")
                return False
            
            # Get balances
            balances = {b['asset']: float(b['free']) for b in account['balances'] if float(b['free']) > 0}
            
            usdt_balance = balances.get('USDT', 0)
            btc_balance = balances.get('BTC', 0)
            
            self.log_event("SUCCESS", "Account status check completed", {
                'usdt_balance': usdt_balance,
                'btc_balance': btc_balance,
                'total_assets': len(balances),
                'assets_with_balance': list(balances.keys())[:10]  # First 10
            })
            
            if usdt_balance < 10:
                self.log_event("WARNING", f"Low USDT balance: ${usdt_balance}")
                if usdt_balance == 0:
                    self.log_event("ERROR", "No USDT available for trading")
                    return False
            
            return True
            
        except Exception as e:
            self.log_event("ERROR", f"Account status check failed: {e}")
            return False
    
    def get_symbol_info(self, symbol='BTCUSDT'):
        """Get detailed symbol trading information"""
        self.log_event("CHECK", f"Getting symbol info for {symbol}...")
        
        try:
            exchange_info = self.client.get_exchange_info()
            symbol_info = next((s for s in exchange_info['symbols'] if s['symbol'] == symbol), None)
            
            if not symbol_info:
                self.log_event("ERROR", f"Symbol {symbol} not found")
                return None
            
            # Extract key trading rules
            trading_rules = {}
            for filter_info in symbol_info['filters']:
                if filter_info['filterType'] == 'LOT_SIZE':
                    trading_rules['min_qty'] = float(filter_info['minQty'])
                    trading_rules['max_qty'] = float(filter_info['maxQty'])
                    trading_rules['step_size'] = float(filter_info['stepSize'])
                elif filter_info['filterType'] == 'MIN_NOTIONAL':
                    trading_rules['min_notional'] = float(filter_info['minNotional'])
                elif filter_info['filterType'] == 'PRICE_FILTER':
                    trading_rules['min_price'] = float(filter_info['minPrice'])
                    trading_rules['max_price'] = float(filter_info['maxPrice'])
                    trading_rules['tick_size'] = float(filter_info['tickSize'])
            
            self.log_event("SUCCESS", f"Symbol {symbol} info retrieved", {
                'symbol': symbol,
                'status': symbol_info['status'],
                'trading_rules': trading_rules
            })
            
            return trading_rules
            
        except Exception as e:
            self.log_event("ERROR", f"Failed to get symbol info: {e}")
            return None
    
    def attempt_trade_execution(self, symbol='BTCUSDT', trade_amount_usd=10.0):
        """Attempt to execute a trade with detailed logging"""
        self.log_event("TRADE_START", f"Attempting trade execution for {symbol}")
        
        try:
            # Step 1: Get current price
            self.log_event("STEP", "Getting current market price...")
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            current_price = float(ticker['price'])
            
            self.log_event("INFO", f"Current {symbol} price: ${current_price:,.2f}")
            
            # Step 2: Calculate quantity
            self.log_event("STEP", "Calculating trade quantity...")
            quantity = trade_amount_usd / current_price
            
            # Get symbol info for rounding
            trading_rules = self.get_symbol_info(symbol)
            if not trading_rules:
                return False
            
            # Round quantity to proper step size
            step_size = trading_rules['step_size']
            quantity = round(quantity / step_size) * step_size
            quantity = round(quantity, 8)  # Max 8 decimal places
            
            # Validate quantity
            if quantity < trading_rules['min_qty']:
                self.log_event("ERROR", f"Quantity {quantity} below minimum {trading_rules['min_qty']}")
                return False
            
            if quantity > trading_rules['max_qty']:
                self.log_event("ERROR", f"Quantity {quantity} above maximum {trading_rules['max_qty']}")
                return False
            
            # Check notional value
            notional_value = quantity * current_price
            if notional_value < trading_rules['min_notional']:
                self.log_event("ERROR", f"Notional value ${notional_value:.2f} below minimum ${trading_rules['min_notional']}")
                return False
            
            self.log_event("SUCCESS", "Trade parameters validated", {
                'symbol': symbol,
                'side': 'BUY',
                'type': 'MARKET',
                'quantity': quantity,
                'estimated_cost': notional_value,
                'current_price': current_price
            })
            
            # Step 3: Test order first (safe)
            self.log_event("STEP", "Executing test order (no real trade)...")
            
            test_result = self.client.create_test_order(
                symbol=symbol,
                side='BUY',
                type='MARKET',
                quantity=quantity
            )
            
            self.log_event("SUCCESS", "Test order successful - trade parameters are valid")
            
            # Step 4: Ask for real trade confirmation
            print("\n" + "=" * 60)
            print("🎯 READY TO EXECUTE REAL TRADE")
            print("=" * 60)
            print(f"Symbol: {symbol}")
            print(f"Side: BUY")
            print(f"Quantity: {quantity:.8f}")
            print(f"Estimated Cost: ${notional_value:.2f}")
            print(f"Current Price: ${current_price:,.2f}")
            print("\n⚠️ WARNING: This will be a REAL trade with REAL money!")
            
            confirm = input("\nType 'EXECUTE' to place real order: ")
            
            if confirm.upper() != 'EXECUTE':
                self.log_event("INFO", "Real trade cancelled by user")
                return True  # Diagnostic was successful
            
            # Step 5: Execute real order
            self.log_event("TRADE_EXECUTE", "Executing REAL market order...")
            
            order = self.client.order_market_buy(
                symbol=symbol,
                quantity=quantity
            )
            
            self.log_event("SUCCESS", "REAL TRADE EXECUTED SUCCESSFULLY!", {
                'order_id': order['orderId'],
                'symbol': order['symbol'],
                'side': order['side'],
                'status': order['status'],
                'executed_qty': order.get('executedQty', 'N/A'),
                'cummulative_quote_qty': order.get('cummulativeQuoteQty', 'N/A')
            })
            
            return True
            
        except self.BinanceAPIException as e:
            self.log_event("TRADE_ERROR", f"Binance API error during trade execution", {
                'error_code': e.code,
                'error_message': e.message,
                'symbol': symbol,
                'attempted_quantity': quantity if 'quantity' in locals() else 'N/A',
                'attempted_notional': notional_value if 'notional_value' in locals() else 'N/A'
            })
            
            # Provide specific error guidance
            if e.code == -1013:
                print(f"\n🔧 SOLUTION FOR -1013:")
                print(f"   Order violates trading rules")
                print(f"   Min quantity: {trading_rules.get('min_qty', 'Unknown')}")
                print(f"   Min notional: ${trading_rules.get('min_notional', 'Unknown')}")
            elif e.code == -2010:
                print(f"\n🔧 SOLUTION FOR -2010:")
                print(f"   Insufficient account balance")
                print(f"   Check USDT balance vs required ${notional_value:.2f}")
            elif e.code == -2015:
                print(f"\n🔧 SOLUTION FOR -2015:")
                print(f"   API permissions issue - enable 'Spot & Margin Trading'")
            
            return False
            
        except Exception as e:
            self.log_event("TRADE_ERROR", f"Unexpected error during trade execution: {e}")
            return False
    
    def run_full_diagnostic(self):
        """Run complete trade execution diagnostic"""
        print(f"🚀 STARTING COMPREHENSIVE TRADE EXECUTION DIAGNOSTIC")
        print(f"📝 Logging to: {self.log_file}")
        print("=" * 80)
        
        # Step 1: Initialize
        if not self.initialize_client():
            return False
        
        # Step 2: Check account
        if not self.check_account_status():
            return False
        
        # Step 3: Get symbol info
        trading_rules = self.get_symbol_info()
        if not trading_rules:
            return False
        
        # Step 4: Attempt trade
        return self.attempt_trade_execution()

def main():
    print("🔍 LIVE TRADE EXECUTION DIAGNOSTIC")
    print("This will show EXACTLY why your trades fail")
    print("=" * 60)
    
    monitor = TradeExecutionMonitor()
    
    success = monitor.run_full_diagnostic()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 DIAGNOSTIC COMPLETE!")
        print("✅ Your setup CAN execute trades")
        print(f"📝 Full log saved to: {monitor.log_file}")
        print("\nIf your bot still fails, the issue is in the bot code logic,")
        print("not in the API connection or permissions.")
    else:
        print("🛑 DIAGNOSTIC FAILED!")
        print("❌ Fix the errors above before attempting live trades")
        print(f"📝 Error details saved to: {monitor.log_file}")

if __name__ == "__main__":
    main()