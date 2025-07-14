import time
import json
from datetime import datetime, timedelta
from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd

def get_account_balance(client, asset='USDT'):
    """Get account balance for specified asset"""
    try:
        account = client.get_account()
        for balance in account['balances']:
            if balance['asset'] == asset:
                return float(balance['free'])
        return 0.0
    except Exception as e:
        print(f"❌ Error getting account balance: {e}")
        return 0.0

def calculate_dynamic_position_size(account_balance, base_quantity, confidence, volatility, risk_percentage=0.015):
    """Calculate dynamic position size based on multiple factors"""
    try:
        # Base risk amount
        risk_amount = account_balance * risk_percentage
        
        # Confidence scaling (0.5x to 2.0x)
        confidence_multiplier = 0.5 + (confidence * 1.5)
        
        # Volatility adjustment (reduce size in high volatility)
        volatility_adjustment = max(0.3, 1.0 - (volatility * 2))
        
        # Account size adjustment
        if account_balance > 10000:
            account_multiplier = 1.5
        elif account_balance > 1000:
            account_multiplier = 1.2
        else:
            account_multiplier = 1.0
        
        # Calculate final multiplier
        final_multiplier = confidence_multiplier * volatility_adjustment * account_multiplier
        
        # Apply to base quantity
        adjusted_quantity = base_quantity * final_multiplier
        
        # Ensure we don't risk more than specified percentage
        max_quantity_by_risk = risk_amount / 50000  # Assuming ~$50k per base unit
        adjusted_quantity = min(adjusted_quantity, max_quantity_by_risk)
        
        # Minimum position size
        min_quantity = base_quantity * 0.3
        adjusted_quantity = max(adjusted_quantity, min_quantity)
        
        return round(adjusted_quantity, 6)
        
    except Exception as e:
        print(f"❌ Error calculating position size: {e}")
        return base_quantity

def execute_entry(client, symbol, quantity, signal_type):
    """Execute entry trade (buy order)"""
    try:
        print(f"📈 Executing {signal_type} entry for {symbol}")
        print(f"   Quantity: {quantity}")
        
        if signal_type in ['BUY_LONG', 'BUY_SHORT']:
            order = client.order_market_buy(
                symbol=symbol,
                quantity=quantity
            )
            
            if order['status'] == 'FILLED':
                fills = order.get('fills', [])
                if fills:
                    avg_price = sum(float(fill['price']) * float(fill['qty']) for fill in fills) / sum(float(fill['qty']) for fill in fills)
                else:
                    avg_price = float(order.get('price', 0))
                
                return {
                    'status': 'SUCCESS',
                    'entry_price': avg_price,
                    'quantity': float(order['executedQty']),
                    'timestamp': datetime.now(),
                    'order_id': order['orderId'],
                    'order_details': order
                }
            else:
                return {
                    'status': 'FAILED',
                    'error': f"Order not filled: {order['status']}",
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

def execute_exit(client, symbol, quantity, exit_price, entry_price, reason):
    """Execute exit trade (sell order)"""
    try:
        print(f"📉 Executing exit for {symbol}")
        print(f"   Quantity: {quantity}")
        print(f"   Reason: {reason}")
        
        order = client.order_market_sell(
            symbol=symbol,
            quantity=quantity
        )
        
        if order['status'] == 'FILLED':
            fills = order.get('fills', [])
            if fills:
                avg_price = sum(float(fill['price']) * float(fill['qty']) for fill in fills) / sum(float(fill['qty']) for fill in fills)
            else:
                avg_price = float(order.get('price', exit_price))
            
            return {
                'status': 'SUCCESS',
                'exit_price': avg_price,
                'quantity': float(order['executedQty']),
                'timestamp': datetime.now(),
                'order_id': order['orderId'],
                'pnl_percent': ((avg_price - entry_price) / entry_price) * 100,
                'order_details': order
            }
        else:
            return {
                'status': 'FAILED',
                'error': f"Order not filled: {order['status']}",
                'order_details': order
            }
            
    except Exception as e:
        return {
            'status': 'FAILED',
            'error': f"Exit error: {str(e)}"
        }

def monitor_position_enhanced(client, symbol, entry_price):
    """Enhanced position monitoring with multiple exit strategies"""
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        current_price = float(ticker['price'])
        
        pnl_percent = ((current_price - entry_price) / entry_price) * 100
        
        if pnl_percent >= 10.0:
            return True, f"Take Profit: {pnl_percent:+.2f}%"
        elif pnl_percent <= -10.0:
            return True, f"Stop Loss: {pnl_percent:+.2f}%"
        
        return False, "Hold"
        
    except Exception as e:
        print(f"❌ Error monitoring position: {e}")
        return False, "Error"

def calculate_portfolio_metrics(trades_log):
    """Calculate comprehensive portfolio performance metrics"""
    if not trades_log:
        return {
            'total_trades': 0,
            'win_rate': 0.0,
            'total_pnl_percent': 0.0,
            'profit_factor': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0
        }
    
    try:
        df = pd.DataFrame(trades_log)
        
        total_trades = len(df)
        winning_trades = len(df[df['pnl_percent'] > 0])
        losing_trades = len(df[df['pnl_percent'] < 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        total_pnl = df['pnl_percent'].sum()
        total_wins = df[df['pnl_percent'] > 0]['pnl_percent'].sum()
        total_losses = abs(df[df['pnl_percent'] < 0]['pnl_percent'].sum())
        
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        returns_std = df['pnl_percent'].std()
        sharpe_ratio = total_pnl / returns_std if returns_std > 0 else 0
        
        cumulative_pnl = df['pnl_percent'].cumsum()
        running_max = cumulative_pnl.expanding().max()
        drawdown = running_max - cumulative_pnl
        max_drawdown = drawdown.max()
        
        avg_win = df[df['pnl_percent'] > 0]['pnl_percent'].mean() if winning_trades > 0 else 0
        avg_loss = df[df['pnl_percent'] < 0]['pnl_percent'].mean() if losing_trades > 0 else 0
        max_win = df['pnl_percent'].max()
        max_loss = df['pnl_percent'].min()
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl_percent': total_pnl,
            'average_win': avg_win,
            'average_loss': avg_loss,
            'max_win': max_win,
            'max_loss': max_loss,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'volatility': returns_std
        }
        
    except Exception as e:
        print(f"❌ Error calculating portfolio metrics: {e}")
        return {
            'total_trades': len(trades_log),
            'win_rate': 0.0,
            'total_pnl_percent': 0.0,
            'error': str(e)
        }

# Legacy compatibility functions
def monitor_position(entry_price, symbol, quantity, client):
    """Legacy function for backward compatibility"""
    should_exit, reason = monitor_position_enhanced(client, symbol, entry_price)
    return reason if should_exit else None
import time
import json
from datetime import datetime, timedelta
from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd

def get_account_balance(client, asset='USDT'):
    """Get account balance for specified asset"""
    try:
        account = client.get_account()
        for balance in account['balances']:
            if balance['asset'] == asset:
                return float(balance['free'])
        return 0.0
    except Exception as e:
        print(f"❌ Error getting account balance: {e}")
        return 0.0

def calculate_dynamic_position_size(account_balance, base_quantity, confidence, volatility, risk_percentage=0.015):
    """
    Calculate dynamic position size based on multiple factors
    
    Args:
        account_balance: Available USDT balance
        base_quantity: Base position size for the symbol
        confidence: Strategy confidence (0.0 to 1.0)
        volatility: Market volatility (0.0 to 1.0)
        risk_percentage: Risk per trade as percentage of account
    
    Returns:
        Adjusted position size
    """
    try:
        # Base risk amount
        risk_amount = account_balance * risk_percentage
        
        # Confidence scaling (0.5x to 2.0x)
        confidence_multiplier = 0.5 + (confidence * 1.5)
        
        # Volatility adjustment (reduce size in high volatility)
        volatility_adjustment = max(0.3, 1.0 - (volatility * 2))
        
        # Account size adjustment
        if account_balance > 10000:
            account_multiplier = 1.5
        elif account_balance > 1000:
            account_multiplier = 1.2
        else:
            account_multiplier = 1.0
        
        # Calculate final multiplier
        final_multiplier = confidence_multiplier * volatility_adjustment * account_multiplier
        
        # Apply to base quantity
        adjusted_quantity = base_quantity * final_multiplier
        
        # Ensure we don't risk more than specified percentage
        max_quantity_by_risk = risk_amount / 50000  # Assuming ~$50k per base unit
        adjusted_quantity = min(adjusted_quantity, max_quantity_by_risk)
        
        # Minimum position size
        min_quantity = base_quantity * 0.3
        adjusted_quantity = max(adjusted_quantity, min_quantity)
        
        return round(adjusted_quantity, 6)
        
    except Exception as e:
        print(f"❌ Error calculating position size: {e}")
        return base_quantity

def execute_entry(client, symbol, quantity, signal_type):
    """
    Execute entry trade (buy order)
    
    Args:
        client: Binance client
        symbol: Trading symbol (e.g., 'BTCUSDT')
        quantity: Position size
        signal_type: 'BUY_LONG' or 'BUY_SHORT'
    
    Returns:
        Dict with execution results
    """
    try:
        print(f"📈 Executing {signal_type} entry for {symbol}")
        print(f"   Quantity: {quantity}")
        
        # For crypto spot trading, we only do BUY orders
        # BUY_SHORT would require futures trading which is more complex
        if signal_type in ['BUY_LONG', 'BUY_SHORT']:
            order = client.order_market_buy(
                symbol=symbol,
                quantity=quantity
            )
            
            # Extract execution details
            if order['status'] == 'FILLED':
                fills = order.get('fills', [])
                if fills:
                    avg_price = sum(float(fill['price']) * float(fill['qty']) for fill in fills) / sum(float(fill['qty']) for fill in fills)
                else:
                    avg_price = float(order.get('price', 0))
                
                return {
                    'status': 'SUCCESS',
                    'entry_price': avg_price,
                    'quantity': float(order['executedQty']),
                    'timestamp': datetime.now(),
                    'order_id': order['orderId'],
                    'order_details': order
                }
            else:
                return {
                    'status': 'FAILED',
                    'error': f"Order not filled: {order['status']}",
                    'order_details': order
                }
        else:
            return {
                'status': 'FAILED',
                'error': f"Invalid signal type: {signal_type}"
            }
            
    except BinanceAPIException as e:
        return {
            'status': 'FAILED',
            'error': f"Binance API error: {e.message}",
            'code': e.code
        }
    except Exception as e:
        return {
            'status': 'FAILED',
            'error': f"Execution error: {str(e)}"
        }

def execute_exit(client, symbol, quantity, exit_price, entry_price, reason):
    """
    Execute exit trade (sell order)
    
    Args:
        client: Binance client
        symbol: Trading symbol
        quantity: Position size to sell
        exit_price: Current market price
        entry_price: Original entry price
        reason: Exit reason
    
    Returns:
        Dict with execution results
    """
    try:
        print(f"📉 Executing exit for {symbol}")
        print(f"   Quantity: {quantity}")
        print(f"   Reason: {reason}")
        
        # Execute market sell order
        order = client.order_market_sell(
            symbol=symbol,
            quantity=quantity
        )
        
        # Extract execution details
        if order['status'] == 'FILLED':
            fills = order.get('fills', [])
            if fills:
                avg_price = sum(float(fill['price']) * float(fill['qty']) for fill in fills) / sum(float(fill['qty']) for fill in fills)
            else:
                avg_price = float(order.get('price', exit_price))
            
            return {
                'status': 'SUCCESS',
                'exit_price': avg_price,
                'quantity': float(order['executedQty']),
                'timestamp': datetime.now(),
                'order_id': order['orderId'],
                'pnl_percent': ((avg_price - entry_price) / entry_price) * 100,
                'order_details': order
            }
        else:
            return {
                'status': 'FAILED',
                'error': f"Order not filled: {order['status']}",
                'order_details': order
            }
            
    except BinanceAPIException as e:
        return {
            'status': 'FAILED',
            'error': f"Binance API error: {e.message}",
            'code': e.code
        }
    except Exception as e:
        return {
            'status': 'FAILED',
            'error': f"Exit error: {str(e)}"
        }

def monitor_position_enhanced(client, symbol, entry_price):
    """
    Enhanced position monitoring with multiple exit strategies
    
    Args:
        client: Binance client
        symbol: Trading symbol
        entry_price: Entry price for P&L calculation
    
    Returns:
        Tuple: (should_exit: bool, reason: str)
    """
    try:
        # Get current market price
        ticker = client.get_symbol_ticker(symbol=symbol)
        current_price = float(ticker['price'])
        
        # Calculate P&L percentage
        pnl_percent = ((current_price - entry_price) / entry_price) * 100
        
        # Simple exit conditions (you can enhance these)
        if pnl_percent >= 10.0:
            return True, f"Take Profit: {pnl_percent:+.2f}%"
        elif pnl_percent <= -10.0:
            return True, f"Stop Loss: {pnl_percent:+.2f}%"
        
        return False, "Hold"
        
    except Exception as e:
        print(f"❌ Error monitoring position: {e}")
        return False, "Error"

def calculate_portfolio_metrics(trades_log):
    """
    Calculate comprehensive portfolio performance metrics
    
    Args:
        trades_log: List of trade records
    
    Returns:
        Dict with performance metrics
    """
    if not trades_log:
        return {
            'total_trades': 0,
            'win_rate': 0.0,
            'total_pnl_percent': 0.0,
            'profit_factor': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0
        }
    
    try:
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(trades_log)
        
        # Basic metrics
        total_trades = len(df)
        winning_trades = len(df[df['pnl_percent'] > 0])
        losing_trades = len(df[df['pnl_percent'] < 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # P&L metrics
        total_pnl = df['pnl_percent'].sum()
        total_wins = df[df['pnl_percent'] > 0]['pnl_percent'].sum()
        total_losses = abs(df[df['pnl_percent'] < 0]['pnl_percent'].sum())
        
        # Profit factor
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Volatility and Sharpe ratio
        returns_std = df['pnl_percent'].std()
        sharpe_ratio = total_pnl / returns_std if returns_std > 0 else 0
        
        # Maximum drawdown
        cumulative_pnl = df['pnl_percent'].cumsum()
        running_max = cumulative_pnl.expanding().max()
        drawdown = running_max - cumulative_pnl
        max_drawdown = drawdown.max()
        
        # Additional metrics
        avg_win = df[df['pnl_percent'] > 0]['pnl_percent'].mean() if winning_trades > 0 else 0
        avg_loss = df[df['pnl_percent'] < 0]['pnl_percent'].mean() if losing_trades > 0 else 0
        max_win = df['pnl_percent'].max()
        max_loss = df['pnl_percent'].min()
        
        # Consecutive wins/losses
        df['win'] = df['pnl_percent'] > 0
        df['streak'] = df['win'].groupby((df['win'] != df['win'].shift()).cumsum()).cumcount() + 1
        max_winning_streak = df[df['win']]['streak'].max() if winning_trades > 0 else 0
        max_losing_streak = df[~df['win']]['streak'].max() if losing_trades > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl_percent': total_pnl,
            'average_win': avg_win,
            'average_loss': avg_loss,
            'max_win': max_win,
            'max_loss': max_loss,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'volatility': returns_std,
            'max_winning_streak': max_winning_streak,
            'max_losing_streak': max_losing_streak,
            'total_wins_amount': total_wins,
            'total_losses_amount': total_losses
        }
        
    except Exception as e:
        print(f"❌ Error calculating portfolio metrics: {e}")
        return {
            'total_trades': len(trades_log),
            'win_rate': 0.0,
            'total_pnl_percent': 0.0,
            'error': str(e)
        }

def validate_trade_parameters(symbol, quantity, price=None):
    """
    Validate trade parameters before execution
    
    Args:
        symbol: Trading symbol
        quantity: Position size
        price: Price (optional)
    
    Returns:
        Tuple: (is_valid: bool, error_message: str)
    """
    try:
        # Basic validation
        if not symbol or not isinstance(symbol, str):
            return False, "Invalid symbol"
        
        if quantity <= 0:
            return False, "Quantity must be positive"
        
        if price is not None and price <= 0:
            return False, "Price must be positive"
        
        # Symbol format validation
        if not symbol.endswith('USDT'):
            return False, "Only USDT pairs supported"
        
        # Quantity limits (basic check)
        if quantity > 1000:  # Adjust based on your needs
            return False, "Quantity too large"
        
        if quantity < 0.000001:  # Minimum quantity
            return False, "Quantity too small"
        
        return True, "Valid"
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def get_symbol_info(client, symbol):
    """
    Get trading symbol information and limits
    
    Args:
        client: Binance client
        symbol: Trading symbol
    
    Returns:
        Dict with symbol information
    """
    try:
        exchange_info = client.get_exchange_info()
        
        for symbol_info in exchange_info['symbols']:
            if symbol_info['symbol'] == symbol:
                # Extract key information
                filters = {f['filterType']: f for f in symbol_info['filters']}
                
                return {
                    'symbol': symbol,
                    'status': symbol_info['status'],
                    'baseAsset': symbol_info['baseAsset'],
                    'quoteAsset': symbol_info['quoteAsset'],
                    'minQty': float(filters.get('LOT_SIZE', {}).get('minQty', 0)),
                    'maxQty': float(filters.get('LOT_SIZE', {}).get('maxQty', 0)),
                    'stepSize': float(filters.get('LOT_SIZE', {}).get('stepSize', 0)),
                    'minPrice': float(filters.get('PRICE_FILTER', {}).get('minPrice', 0)),
                    'maxPrice': float(filters.get('PRICE_FILTER', {}).get('maxPrice', 0)),
                    'tickSize': float(filters.get('PRICE_FILTER', {}).get('tickSize', 0)),
                    'minNotional': float(filters.get('MIN_NOTIONAL', {}).get('minNotional', 0))
                }
        
        return None
        
    except Exception as e:
        print(f"❌ Error getting symbol info: {e}")
        return None

def format_quantity(quantity, step_size):
    """
    Format quantity according to symbol step size
    
    Args:
        quantity: Raw quantity
        step_size: Symbol step size from exchange info
    
    Returns:
        Properly formatted quantity
    """
    try:
        if step_size == 0:
            return quantity
        
        # Calculate precision based on step size
        precision = len(str(step_size).split('.')[-1]) if '.' in str(step_size) else 0
        
        # Round to appropriate precision
        formatted_qty = round(quantity / step_size) * step_size
        
        return round(formatted_qty, precision)
        
    except Exception as e:
        print(f"❌ Error formatting quantity: {e}")
        return quantity

# Legacy compatibility functions
def monitor_position(entry_price, symbol, quantity, client):
    """Legacy function for backward compatibility"""
    should_exit, reason = monitor_position_enhanced(client, symbol, entry_price)
    return reason if should_exit else None

def calculate_position_size(account_balance, risk_percent=0.015):
    """Simple position size calculation for backward compatibility"""
    return account_balance * risk_percent / 50000  # Assuming ~$50k BTC price

# Trade logging helper
def log_trade_execution(trade_type, symbol, quantity, price, result):
    """Log trade execution for debugging"""
    timestamp = datetime.now().isoformat()
    log_entry = {
        'timestamp': timestamp,
        'trade_type': trade_type,
        'symbol': symbol,
        'quantity': quantity,
        'price': price,
        'result': result
    }
    
    try:
        with open('logs/trade_executions.json', 'a') as f:
            json.dump(log_entry, f)
            f.write('\n')
    except Exception as e:
        print(f"❌ Error logging trade execution: {e}")

# Emergency functions
def emergency_close_all_positions(client, symbols_list):
    """Emergency function to close all positions"""
    print("🚨 EMERGENCY: Closing all positions!")
    
    results = []
    for symbol in symbols_list:
        try:
            # Get current balance of base asset
            base_asset = symbol.replace('USDT', '')
            balance = get_account_balance(client, base_asset)
            
            if balance > 0:
                result = execute_exit(client, symbol, balance, 0, 0, "Emergency Close")
                results.append((symbol, result))
                print(f"   {symbol}: {result['status']}")
        except Exception as e:
            print(f"   {symbol}: Error - {e}")
            results.append((symbol, {'status': 'ERROR', 'error': str(e)}))
    
    return results

def get_portfolio_summary(client, symbols_list):
    """Get current portfolio summary"""
    try:
        portfolio = {}
        total_value_usdt = 0
        
        # Get USDT balance
        usdt_balance = get_account_balance(client, 'USDT')
        portfolio['USDT'] = {
            'balance': usdt_balance,
            'value_usdt': usdt_balance,
            'percentage': 0  # Will calculate after total
        }
        total_value_usdt += usdt_balance
        
        # Get crypto balances
        for symbol in symbols_list:
            base_asset = symbol.replace('USDT', '')
            balance = get_account_balance(client, base_asset)
            
            if balance > 0:
                # Get current price
                ticker = client.get_symbol_ticker(symbol=symbol)
                price = float(ticker['price'])
                value_usdt = balance * price
                
                portfolio[base_asset] = {
                    'balance': balance,
                    'price': price,
                    'value_usdt': value_usdt,
                    'percentage': 0  # Will calculate after total
                }
                total_value_usdt += value_usdt
        
        # Calculate percentages
        for asset in portfolio:
            portfolio[asset]['percentage'] = (portfolio[asset]['value_usdt'] / total_value_usdt) * 100 if total_value_usdt > 0 else 0
        
        return {
            'total_value_usdt': total_value_usdt,
            'portfolio': portfolio,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error getting portfolio summary: {e}")
        return None