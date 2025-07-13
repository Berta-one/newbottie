# logger.py - Comprehensive Logging System
import json
import csv
import os
from datetime import datetime
import pandas as pd

class TradingLogger:
    def __init__(self, log_dir='logs'):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Log files
        self.trade_log_file = os.path.join(log_dir, 'trades.csv')
        self.performance_file = os.path.join(log_dir, 'performance.json')
        self.scan_log_file = os.path.join(log_dir, 'scan_history.json')
        
        # Initialize CSV file if it doesn't exist
        self.setup_csv_logging()
    
    def setup_csv_logging(self):
        """Setup CSV logging with headers"""
        if not os.path.exists(self.trade_log_file):
            headers = [
                'timestamp', 'symbol', 'signal_type', 'entry_price', 'exit_price',
                'quantity', 'pnl_percent', 'pnl_amount', 'confidence', 'reason',
                'time_held_minutes', 'category', 'volatility', 'volume_ratio'
            ]
            
            with open(self.trade_log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
    
    def log_trade(self, trade_data):
        """Log a completed trade to CSV"""
        try:
            with open(self.trade_log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    trade_data.get('timestamp', datetime.now().isoformat()),
                    trade_data.get('symbol', ''),
                    trade_data.get('signal_type', ''),
                    trade_data.get('entry_price', 0),
                    trade_data.get('exit_price', 0),
                    trade_data.get('quantity', 0),
                    trade_data.get('pnl_percent', 0),
                    trade_data.get('pnl_amount', 0),
                    trade_data.get('confidence', 0),
                    trade_data.get('reason', ''),
                    trade_data.get('time_held_minutes', 0),
                    trade_data.get('category', ''),
                    trade_data.get('volatility', 0),
                    trade_data.get('volume_ratio', 0)
                ])
            print(f"📝 Trade logged to {self.trade_log_file}")
        except Exception as e:
            print(f"❌ Error logging trade: {e}")
    
    def calculate_performance_metrics(self):
        """Calculate comprehensive performance metrics from trade log"""
        try:
            if not os.path.exists(self.trade_log_file):
                return {}
            
            df = pd.read_csv(self.trade_log_file)
            
            if len(df) == 0:
                return {}
            
            # Basic metrics
            total_trades = len(df)
            winning_trades = len(df[df['pnl_percent'] > 0])
            losing_trades = len(df[df['pnl_percent'] < 0])
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            
            # P&L metrics
            total_pnl = df['pnl_percent'].sum()
            avg_win = df[df['pnl_percent'] > 0]['pnl_percent'].mean() if winning_trades > 0 else 0
            avg_loss = df[df['pnl_percent'] < 0]['pnl_percent'].mean() if losing_trades > 0 else 0
            
            # Risk metrics
            max_win = df['pnl_percent'].max()
            max_loss = df['pnl_percent'].min()
            volatility = df['pnl_percent'].std()
            
            # Profit factor
            total_wins = df[df['pnl_percent'] > 0]['pnl_percent'].sum()
            total_losses = abs(df[df['pnl_percent'] < 0]['pnl_percent'].sum())
            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
            
            # Sharpe ratio (simplified)
            sharpe_ratio = total_pnl / volatility if volatility > 0 else 0
            
            metrics = {
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
                'volatility': volatility,
                'last_updated': datetime.now().isoformat()
            }
            
            # Save metrics to file
            with open(self.performance_file, 'w') as f:
                json.dump(metrics, f, indent=2)
            
            return metrics
            
        except Exception as e:
            print(f"❌ Error calculating metrics: {e}")
            return {}
    
    def log_scan_result(self, scan_data):
        """Log scan results"""
        try:
            # Load existing scan history
            scan_history = []
            if os.path.exists(self.scan_log_file):
                with open(self.scan_log_file, 'r') as f:
                    scan_history = json.load(f)
            
            # Add new scan
            scan_history.append({
                'timestamp': datetime.now().isoformat(),
                'scan_mode': scan_data.get('scan_mode', ''),
                'pairs_scanned': scan_data.get('pairs_scanned', 0),
                'opportunities_found': scan_data.get('opportunities_found', 0),
                'signals_generated': scan_data.get('signals_generated', 0),
                'scan_duration_seconds': scan_data.get('scan_duration', 0)
            })
            
            # Keep only last 1000 scans
            scan_history = scan_history[-1000:]
            
            # Save updated history
            with open(self.scan_log_file, 'w') as f:
                json.dump(scan_history, f, indent=2)
                
        except Exception as e:
            print(f"❌ Error logging scan: {e}")
    
    def get_trade_summary(self, last_n_days=30):
        """Get trading summary for last N days"""
        try:
            if not os.path.exists(self.trade_log_file):
                return "No trade data available"
            
            df = pd.read_csv(self.trade_log_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Filter last N days
            cutoff_date = datetime.now() - pd.Timedelta(days=last_n_days)
            recent_df = df[df['timestamp'] >= cutoff_date]
            
            if len(recent_df) == 0:
                return f"No trades in the last {last_n_days} days"
            
            # Calculate summary
            summary = f"""
📊 TRADING SUMMARY (Last {last_n_days} days)
{'='*50}
Total Trades: {len(recent_df)}
Win Rate: {(len(recent_df[recent_df['pnl_percent'] > 0]) / len(recent_df) * 100):.1f}%
Total P&L: {recent_df['pnl_percent'].sum():.2f}%
Average P&L: {recent_df['pnl_percent'].mean():.2f}%
Best Trade: {recent_df['pnl_percent'].max():.2f}%
Worst Trade: {recent_df['pnl_percent'].min():.2f}%

📈 BY CATEGORY:
{recent_df.groupby('category')['pnl_percent'].agg(['count', 'mean', 'sum']).round(2)}

🎯 BY SIGNAL TYPE:
{recent_df.groupby('signal_type')['pnl_percent'].agg(['count', 'mean']).round(2)}
            """
            
            return summary
            
        except Exception as e:
            return f"Error generating summary: {e}"

# Global logger instance
trading_logger = TradingLogger()

# Convenience functions
def log_trade(trade_data):
    trading_logger.log_trade(trade_data)

def get_performance_metrics():
    return trading_logger.calculate_performance_metrics()

def log_scan(scan_data):
    trading_logger.log_scan_result(scan_data)

def get_trade_summary(days=30):
    return trading_logger.get_trade_summary(days)
