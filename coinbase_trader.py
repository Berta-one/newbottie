# coinbase_trader.py - Coinbase Pro API Integration
import time
import json
import hmac
import hashlib
import base64
import requests
from datetime import datetime
import pandas as pd

class CoinbaseProClient:
    def __init__(self, api_key, api_secret, passphrase, sandbox=True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        
        if sandbox:
            self.base_url = 'https://api-public.sandbox.pro.coinbase.com'
        else:
            self.base_url = 'https://api.pro.coinbase.com'
    
    def _create_signature(self, timestamp, method, request_path, body=''):
        """Create authentication signature"""
        message = timestamp + method + request_path + body
        hmac_key = base64.b64decode(self.api_secret)
        signature = hmac.new(hmac_key, message.encode(), hashlib.sha256)
        return base64.b64encode(signature.digest()).decode()
    
    def _request(self, method, endpoint, params=None, data=None):
        """Make authenticated request to Coinbase Pro API"""
        url = self.base_url + endpoint
        timestamp = str(time.time())
        
        if data:
            body = json.dumps(data)
        else:
            body = ''
        
        signature = self._create_signature(timestamp, method, endpoint, body)
        
        headers = {
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-SIGN': signature,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Coinbase API Error: {e}")
            return None
    
    def get_accounts(self):
        """Get account balances"""
        return self._request('GET', '/accounts')
    
    def get_account_balance(self, currency='USD'):
        """Get balance for specific currency"""
        accounts = self.get_accounts()
        if accounts:
            for account in accounts:
                if account['currency'] == currency:
                    return float(account['balance'])
        return 0.0
    
    def get_products(self):
        """Get available trading pairs"""
        return self._request('GET', '/products')
    
    def get_product_ticker(self, product_id):
        """Get current price for product"""
        endpoint = f'/products/{product_id}/ticker'
        return self._request('GET', endpoint)
    
    def get_product_candles(self, product_id, start=None, end=None, granularity=60):
        """Get historical candle data"""
        endpoint = f'/products/{product_id}/candles'
        params = {'granularity': granularity}
        
        if start:
            params['start'] = start
        if end:
            params['end'] = end
            
        return self._request('GET', endpoint, params=params)
    
    def place_order(self, product_id, side, order_type='market', size=None, funds=None, price=None):
        """Place trading order"""
        endpoint = '/orders'
        
        order_data = {
            'product_id': product_id,
            'side': side,  # 'buy' or 'sell'
            'type': order_type
        }
        
        if order_type == 'market':
            if size:
                order_data['size'] = str(size)
            elif funds:
                order_data['funds'] = str(funds)
        elif order_type == 'limit':
            order_data['size'] = str(size)
            order_data['price'] = str(price)
        
        return self._request('POST', endpoint, data=order_data)
    
    def get_orders(self, status='all'):
        """Get order history"""
        params = {'status': status}
        return self._request('GET', '/orders', params=params)
    
    def cancel_order(self, order_id):
        """Cancel specific order"""
        endpoint = f'/orders/{order_id}'
        return self._request('DELETE', endpoint)

# Enhanced trading functions for Coinbase
def get_account_balance_coinbase(client, asset='USD'):
    """Get account balance for specified asset"""
    try:
        return client.get_account_balance(asset)
    except Exception as e:
        print(f"❌ Error getting account balance: {e}")
        return 0.0

def calculate_dynamic_position_size_coinbase(account_balance, base_quantity, confidence, volatility, risk_percentage=0.015):
    """Calculate dynamic position size for Coinbase trading"""
    try:
        # Base risk amount in USD
        risk_amount = account_balance * risk_percentage
        
        # Confidence scaling (0.5x to 2.0x)
        confidence_multiplier = 0.5 + (confidence * 1.5)
        
        # Volatility adjustment
        volatility_adjustment = max(0.3, 1.0 - (volatility * 2))
        
        # Calculate final multiplier
        final_multiplier = confidence_multiplier * volatility_adjustment
        
        # Convert to USD amount for purchase
        position_size_usd = risk_amount * final_multiplier
        
        # Minimum position size ($10)
        min_position = 10.0
        position_size_usd = max(position_size_usd, min_position)
        
        return round(position_size_usd, 2)
        
    except Exception as e:
        print(f"❌ Error calculating position size: {e}")
        return 50.0  # Default $50 position

def execute_entry_coinbase(client, product_id, funds_usd, signal_type):
    """Execute entry trade on Coinbase"""
    try:
        print(f"📈 Executing {signal_type} entry for {product_id}")
        print(f"   Funds: ${funds_usd}")
        
        # Coinbase spot trading - buy with USD funds
        if signal_type in ['BUY_LONG', 'BUY_SHORT']:
            order = client.place_order(
                product_id=product_id,
                side='buy',
                order_type='market',
                funds=funds_usd
            )
            
            if order and order.get('id'):
                # Wait a moment for order to fill
                time.sleep(2)
                
                # Get order details
                order_details = client._request('GET', f'/orders/{order["id"]}')
                
                if order_details and order_details.get('status') == 'done':
                    filled_size = float(order_details.get('filled_size', 0))
                    executed_value = float(order_details.get('executed_value', 0))
                    avg_price = executed_value / filled_size if filled_size > 0 else 0
                    
                    return {
                        'status': 'SUCCESS',
                        'entry_price': avg_price,
                        'quantity': filled_size,
                        'timestamp': datetime.now(),
                        'order_id': order['id'],
                        'order_details': order_details
                    }
                else:
                    return {
                        'status': 'FAILED',
                        'error': f"Order not filled: {order_details.get('status', 'unknown')}",
                        'order_details': order_details
                    }
            else:
                return {
                    'status': 'FAILED',
                    'error': 'Failed to place order',
                    'order_details': order
                }
        else:
            return {
                'status': 'FAILED',
                'error': f"Invalid signal type: {signal_type}"
            }
            
    except Exception as e:
        return {
            'status': 'FAILED',
            'error': f"Execution error: {str(e)}"
        }

def execute_exit_coinbase(client, product_id, quantity, exit_price, entry_price, reason):
    """Execute exit trade on Coinbase"""
    try:
        print(f"📉 Executing exit for {product_id}")
        print(f"   Quantity: {quantity}")
        print(f"   Reason: {reason}")
        
        # Execute market sell order
        order = client.place_order(
            product_id=product_id,
            side='sell',
            order_type='market',
            size=quantity
        )
        
        if order and order.get('id'):
            # Wait for order to fill
            time.sleep(2)
            
            # Get order details
            order_details = client._request('GET', f'/orders/{order["id"]}')
            
            if order_details and order_details.get('status') == 'done':
                filled_size = float(order_details.get('filled_size', 0))
                executed_value = float(order_details.get('executed_value', 0))
                avg_price = executed_value / filled_size if filled_size > 0 else exit_price
                
                return {
                    'status': 'SUCCESS',
                    'exit_price': avg_price,
                    'quantity': filled_size,
                    'timestamp': datetime.now(),
                    'order_id': order['id'],
                    'pnl_percent': ((avg_price - entry_price) / entry_price) * 100,
                    'order_details': order_details
                }
            else:
                return {
                    'status': 'FAILED',
                    'error': f"Order not filled: {order_details.get('status', 'unknown')}",
                    'order_details': order_details
                }
        else:
            return {
                'status': 'FAILED',
                'error': 'Failed to place sell order',
                'order_details': order
            }
            
    except Exception as e:
        return {
            'status': 'FAILED',
            'error': f"Exit error: {str(e)}"
        }

def get_coinbase_candles(client, product_id, periods=120):
    """Get candlestick data for Coinbase"""
    try:
        # Get 2 hours of 1-minute candles
        end_time = datetime.now()
        start_time = end_time - pd.Timedelta(hours=2)
        
        candles = client.get_product_candles(
            product_id=product_id,
            start=start_time.isoformat(),
            end=end_time.isoformat(),
            granularity=60  # 1 minute
        )
        
        if candles:
            # Convert Coinbase format to Binance-like format
            # Coinbase: [timestamp, low, high, open, close, volume]
            # Binance: [timestamp, open, high, low, close, volume, ...]
            converted_candles = []
            for candle in reversed(candles):  # Coinbase returns newest first
                converted_candles.append([
                    int(candle[0] * 1000),  # timestamp to milliseconds
                    str(candle[3]),  # open
                    str(candle[2]),  # high
                    str(candle[1]),  # low
                    str(candle[4]),  # close
                    str(candle[5]),  # volume
                    0, 0, 0, 0, 0, 0  # padding for Binance compatibility
                ])
            
            return converted_candles[-periods:]  # Return last N periods
        
        return None
        
    except Exception as e:
        print(f"❌ Error getting Coinbase candles: {e}")
        return None

def monitor_position_enhanced_coinbase(client, product_id, entry_price):
    """Enhanced position monitoring for Coinbase"""
    try:
        ticker = client.get_product_ticker(product_id)
        if ticker:
            current_price = float(ticker['price'])
            
            pnl_percent = ((current_price - entry_price) / entry_price) * 100
            
            if pnl_percent >= 10.0:
                return True, f"Take Profit: {pnl_percent:+.2f}%"
            elif pnl_percent <= -10.0:
                return True, f"Stop Loss: {pnl_percent:+.2f}%"
            
            return False, "Hold"
        
        return False, "Error getting price"
        
    except Exception as e:
        print(f"❌ Error monitoring position: {e}")
        return False, "Error"

# Symbol conversion utilities
def binance_to_coinbase_symbol(binance_symbol):
    """Convert Binance symbol to Coinbase product ID"""
    # BTCUSDT -> BTC-USD
    if binance_symbol.endswith('USDT'):
        base = binance_symbol[:-4]
        return f"{base}-USD"
    return binance_symbol

def coinbase_to_binance_symbol(coinbase_product):
    """Convert Coinbase product ID to Binance symbol"""
    # BTC-USD -> BTCUSDT
    if '-USD' in coinbase_product:
        base = coinbase_product.replace('-USD', '')
        return f"{base}USDT"
    return coinbase_product