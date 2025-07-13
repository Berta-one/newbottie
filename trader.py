# trader.py - Enhanced Position Management with Dynamic Sizing
import time
from datetime import datetime, timedelta
from strategy import get_strategy_confidence, calculate_volatility
import json
import os

def get_account_balance(client, asset='USDT'):
    """Get current account balance for specified asset"""
    try:
        account = client.get_account()
        for balance in account['balances']:
            if balance['asset'] == asset:
                return float(balance['free']) + float(balance['locked'])
        return 0.0
    except Exception as e:
        print(f"❌ Error getting account balance: {e}")
        return 1000.0  # Default fallback for testnet

def calculate_dynamic_position_size(account_balance, base_quantity, confidence, volatility, risk_percentage=0.015):
    """
    Calculate position size based on multiple factors
    """
    # Calculate maximum risk amount
    max_risk_amount = account_balance * risk_percentage
    
    # Confidence multiplier (0.5x to 1.5x base size)
    confidence_multiplier = 0.5 + (confidence * 1.0)
    
    # Volatility adjustment (reduce size in high volatility)
    volatility_adjustment = 1 / (1 + volatility * 10)
    
    # Account size adjustment (larger accounts can take bigger positions)
    if account_balance > 10000:
        size_multiplier = 1.2
    elif account_balance > 5000:
        size_multiplier = 1.1
    elif account_balance > 1000:
        size_multiplier = 1.0
    else:
        size_multiplier = 0.8
    
    # Calculate final position size
    adjusted_quantity = (base_quantity * 
                        confidence_multiplier * 
                        volatility_adjustment * 
                        size_multiplier)
    
    # Ensure position size limits
    min_quantity = base_quantity * 0.3
    max_quantity = base_quantity * 3.0
    
    final_quantity = max(min_quantity, min(max_quantity, adjusted_quantity))
    
    return final_quantity

def calculate_stop_take_levels(confidence, volatility):
    """
    Calculate stop loss and take profit levels based on market conditions
    """
    # Base levels
    base_stop_loss = 10.0
    base_take_profit = 10.0
    
    # Adjust based on confidence
    if confidence > 0.8:
        stop_loss_pct = base_stop_loss + 2.0    # Wider stops for high confidence
        take_profit_pct = base_take_profit + 5.0 # Higher targets
    elif confidence > 0.6:
        stop_loss_pct = base_stop_loss
        take_profit_pct = base_take_profit
    else:
        stop_loss_pct = base_stop_loss - 2.0    # Tighter stops for low confidence
        take_profit_pct = base_take_profit - 2.0 # Lower targets
    
    # Adjust based on volatility
    if volatility > 0.05:  # High volatility
        stop_loss_pct += 3.0
        take_profit_pct += 3.0
    elif volatility > 0.03:  # Medium volatility
        stop_loss_pct += 1.0
        take_profit_pct += 1.0
    
    return stop_loss_pct, take_profit_pct

def monitor_position_enhanced(entry_price, symbol, quantity, client, klines=None, max_hold_time=240):
    """
    Enhanced position monitoring with multiple exit strategies
    """
    print(f"📊 Enhanced monitoring started for {symbol}")
    
    entry_time = datetime.now()
    highest_price = entry_price
    lowest_price = entry_price
    
    # Get strategy parameters
    confidence = get_strategy_confidence(klines) if klines else 0.5
    volatility = calculate_volatility(klines, 20) if klines else 0.02
    
    # Calculate dynamic stop/take levels
    stop_loss_pct, take_profit_pct = calculate_stop_take_levels(confidence, volatility)
    
    print(f"📋 Position Details:")
    print(f"   Symbol: {symbol}")
    print(f"   Entry Price: ${entry_price:.4f}")
    print(f"   Quantity: {quantity}")
    print(f"   Confidence: {confidence:.2f}")
    print(f"   Stop Loss: {stop_loss_pct:.1f}%")
    print(f"   Take Profit: {take_profit_pct:.1f}%")
    
    while True:
        try:
            # Get current price
            ticker = client.get_symbol_ticker(symbol=symbol)
            current_price = float(ticker['price'])
            
            # Calculate P&L
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
            
            # Update price extremes
            if current_price > highest_price:
                highest_price = current_price
            if current_price < lowest_price:
                lowest_price = current_price
            
            # Calculate time held
            time_held = (datetime.now() - entry_time).total_seconds() / 60
            
            print(f"⏱️  {time_held:.0f}m | ${current_price:.4f} | P&L: {pnl_pct:+.2f}% | High: ${highest_price:.4f}")
            
            # EXIT CONDITIONS
            exit_reason = None
            
            # 1. Take Profit
            if pnl_pct >= take_profit_pct:
                exit_reason = f"✅ Take Profit: {pnl_pct:.2f}%"
            
            # 2. Stop Loss
            elif pnl_pct <= -stop_loss_pct:
                exit_reason = f"❌ Stop Loss: {pnl_pct:.2f}%"
            
            # 3. Trailing Stop (if profitable and high confidence)
            elif pnl_pct > 5.0 and confidence > 0.7:
                trailing_stop_pct = 3.0 if confidence > 0.8 else 4.0
                trailing_stop_price = highest_price * (1 - trailing_stop_pct / 100)
                
                if current_price <= trailing_stop_price:
                    exit_reason = f"📉 Trailing Stop: {pnl_pct:.2f}%"
            
            # 4. Time-based exit
            elif time_held >= max_hold_time:
                exit_reason = f"⏰ Time Limit: {pnl_pct:.2f}%"
            
            # 5. Emergency exit on extreme moves
            if abs(pnl_pct) > 20:
                exit_reason = f"🚨 Emergency Exit: {pnl_pct:.2f}%"
            
            # Execute exit if needed
            if exit_reason:
                result = execute_exit(client, symbol, quantity, current_price, entry_price, exit_reason)
                result['time_held_minutes'] = time_held
                result['highest_price'] = highest_price
                result['lowest_price'] = lowest_price
                result['confidence'] = confidence
                result['volatility'] = volatility
                return result
            
            # Wait before next check
            time.sleep(60)  # Check every minute
            
        except Exception as e:
            print(f"⛔ Error monitoring {symbol}: {e}")
            time.sleep(30)

def execute_exit(client, symbol, quantity, exit_price, entry_price, reason):
    """
    Execute position exit and return detailed results
    """
    try:
        print(f"🔄 Executing exit for {symbol}...")
        
        # Place market sell order
        order = client.order_market_sell(
            symbol=symbol,
            quantity=quantity
        )
        
        # Calculate final metrics
        actual_exit_price = float(order['fills'][0]['price']) if order['fills'] else exit_price
        actual_quantity = float(order['executedQty'])
        pnl_pct = ((actual_exit_price - entry_price) / entry_price) * 100
        
        # Calculate trade value
        trade_value = actual_exit_price * actual_quantity
        pnl_amount = (actual_exit_price - entry_price) * actual_quantity
        
        result = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'entry_price': entry_price,
            'exit_price': actual_exit_price,
            'quantity': actual_quantity,
            'pnl_percent': pnl_pct,
            'pnl_amount': pnl_amount,
            'trade_value': trade_value,
            'reason': reason,
            'order_id': order.get('orderId', 'Unknown'),
            'commission': sum([float(fill.get('commission', 0)) for fill in order.get('fills', [])]),
            'status': 'SUCCESS'
        }
        
        print(f"✅ Exit completed!")
        print(f"   Exit Price: ${actual_exit_price:.4f}")
        print(f"   P&L: {pnl_pct:+.2f}% (${pnl_amount:+.2f})")
        
        return result
        
    except Exception as e:
        print(f"❌ Error executing exit: {e}")
        return {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'entry_price': entry_price,
            'error': str(e),
            'reason': f"ERROR: {reason}",
            'status': 'FAILED'
        }

def execute_entry(client, symbol, quantity, signal_type="BUY"):
    """
    Execute position entry with detailed logging
    """
    try:
        print(f"💰 Executing {signal_type} for {symbol} (Qty: {quantity})")
        
        # Place market buy order
        order = client.order_market_buy(symbol=symbol, quantity=quantity)
        
        # Extract order details
        entry_price = float(order['fills'][0]['price']) if order['fills'] else 0
        actual_quantity = float(order['executedQty'])
        commission = sum([float(fill.get('commission', 0)) for fill in order.get('fills', [])])
        
        result = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'entry_price': entry_price,
            'quantity': actual_quantity,
            'signal_type': signal_type,
            'order_id': order.get('orderId'),
            'commission': commission,
            'status': 'SUCCESS'
        }
        
        print(f"✅ Entry executed!")
        print(f"   Entry Price: ${entry_price:.4f}")
        print(f"   Quantity: {actual_quantity}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error executing entry: {e}")
        return {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'error': str(e),
            'status': 'FAILED'
        }

def calculate_portfolio_metrics(trades_log):
    """
    Calculate comprehensive portfolio performance metrics
    """
    if not trades_log:
        return {}
    
    # Filter successful trades
    successful_trades = [trade for trade in trades_log if trade.get('pnl_percent') is not None]
    
    if not successful_trades:
        return {}
    
    # Basic metrics
    total_trades = len(successful_trades)
    winning_trades = [t for t in successful_trades if t['pnl_percent'] > 0]
    losing_trades = [t for t in successful_trades if t['pnl_percent'] < 0]
    
    win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
    
    # P&L metrics
    total_pnl = sum([t['pnl_percent'] for t in successful_trades])
    avg_win = sum([t['pnl_percent'] for t in winning_trades]) / len(winning_trades) if winning_trades else 0
    avg_loss = sum([t['pnl_percent'] for t in losing_trades]) / len(losing_trades) if losing_trades else 0
    
    # Risk metrics
    profit_factor = abs(avg_win * len(winning_trades) / (avg_loss * len(losing_trades))) if losing_trades else float('inf')
    
    return {
        'total_trades': total_trades,
        'win_rate': win_rate,
        'total_pnl_percent': total_pnl,
        'average_win': avg_win,
        'average_loss': avg_loss,
        'profit_factor': profit_factor,
        'best_trade': max([t['pnl_percent'] for t in successful_trades]),
        'worst_trade': min([t['pnl_percent'] for t in successful_trades]),
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades)
    }

# Backward compatibility
def monitor_position(entry_price, symbol, quantity, client):
    """Original function for backward compatibility"""
    return monitor_position_enhanced(entry_price, symbol, quantity, client)
