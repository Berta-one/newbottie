import requests
import json
import pandas as pd
from datetime import datetime

class TradingAnalyzer:
    def __init__(self, base_url='https://bottie-1.onrender.com'):
        self.base_url = base_url
        # Suppress SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def fetch_data(self, endpoint):
        """Fetch data from a given endpoint"""
        try:
            response = requests.get(f'{self.base_url}{endpoint}', verify=False)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching {endpoint}: {e}")
            return None

    def analyze_signals(self):
        """Comprehensive analysis of trading signals"""
        signals = self.fetch_data('/signals')
        if not signals:
            print("No signals found.")
            return None

        # Convert to DataFrame for easy analysis
        df_signals = pd.DataFrame(signals)
        
        print("\n🚦 Signal Analysis Report")
        print("=" * 30)
        
        # Overall Signal Distribution
        print("\n1. Signal Distribution:")
        signal_counts = df_signals['signal'].value_counts()
        print(signal_counts)
        
        # Confidence Analysis
        print("\n2. Confidence Analysis:")
        print(f"Average Confidence: {df_signals['confidence'].mean():.2f}")
        print(f"Confidence Range: {df_signals['confidence'].min()} - {df_signals['confidence'].max()}")
        
        # Price Change Analysis
        print("\n3. 24h Price Change Analysis:")
        change_stats = df_signals['change_24h'].describe()
        print(change_stats)
        
        # Detailed Breakdown
        print("\n4. Detailed Signal Breakdown:")
        detailed_breakdown = df_signals.groupby('signal').agg({
            'symbol': 'count',
            'confidence': 'mean',
            'change_24h': ['mean', 'min', 'max']
        })
        print(detailed_breakdown)
        
        return df_signals

    def analyze_trade_execution(self):
        """Comprehensive analysis of trade execution"""
        trades = self.fetch_data('/trades')
        if not trades:
            print("No trades found.")
            return None

        # Handle different possible response formats
        trades_list = trades.get('trades', trades) if isinstance(trades, dict) else trades

        # Convert to DataFrame
        df_trades = pd.DataFrame(trades_list)
        
        print("\n💹 Trade Execution Analysis Report")
        print("=" * 40)
        
        # Basic Trade Statistics
        print("\n1. Trade Overview:")
        print(f"Total Trades: {len(df_trades)}")
        
        # Trade Side Analysis
        print("\n2. Trade Side Distribution:")
        side_counts = df_trades['side'].value_counts()
        print(side_counts)
        
        # Profit and Loss Analysis
        print("\n3. Profit and Loss Analysis:")
        pnl_stats = df_trades['pnl'].describe()
        print(pnl_stats)
        
        # Profitable Trades
        profitable_trades = df_trades[df_trades['pnl'] > 0]
        print("\n4. Profitable Trades:")
        print(f"Total Profitable Trades: {len(profitable_trades)}")
        print(f"Profitable Trade Percentage: {len(profitable_trades) / len(df_trades) * 100:.2f}%")
        
        # Asset-wise Performance
        print("\n5. Performance by Asset:")
        asset_performance = df_trades.groupby('symbol').agg({
            'pnl': ['count', 'sum', 'mean'],
            'quantity': 'sum',
            'price': 'mean'
        })
        print(asset_performance)
        
        # Time-based Analysis
        df_trades['trade_time'] = pd.to_datetime(df_trades['timestamp'], unit='s')
        print("\n6. Time-based Analysis:")
        time_analysis = df_trades.groupby(pd.Grouper(key='trade_time', freq='H')).size()
        print("Trades per Hour:")
        print(time_analysis)
        
        return df_trades

    def compare_signals_and_trades(self):
        """Compare recent signals with executed trades"""
        signals = self.fetch_data('/signals')
        trades = self.fetch_data('/trades')
        
        if not signals or not trades:
            print("Insufficient data for comparison.")
            return
        
        # Convert trades to DataFrame
        trades_list = trades.get('trades', trades) if isinstance(trades, dict) else trades
        df_trades = pd.DataFrame(trades_list)
        df_signals = pd.DataFrame(signals)
        
        print("\n🔍 Signal vs Trade Comparison")
        print("=" * 30)
        
        # Match signals with recent trades
        df_trades['trade_time'] = pd.to_datetime(df_trades['timestamp'], unit='s')
        
        # Check how many signals resulted in trades
        matched_trades = []
        for _, signal in df_signals.iterrows():
            symbol_trades = df_trades[df_trades['symbol'] == signal['symbol']]
            
            # Look for trades matching signal direction
            matching_trades = symbol_trades[
                ((signal['signal'] == 'BUY') & (symbol_trades['side'] == 'BUY')) |
                ((signal['signal'] == 'SELL') & (symbol_trades['side'] == 'SELL'))
            ]
            
            if not matching_trades.empty:
                matched_trades.append({
                    'symbol': signal['symbol'],
                    'signal': signal['signal'],
                    'signal_confidence': signal['confidence'],
                    'matching_trades': len(matching_trades)
                })
        
        print("Signals Resulting in Trades:")
        for match in matched_trades:
            print(f"{match['symbol']}: {match['signal']} (Confidence: {match['signal_confidence']}) - {match['matching_trades']} matching trades")

def main():
    analyzer = TradingAnalyzer()
    
    print("\n🤖 Bottie Trading System Diagnostic")
    print("=" * 35)
    
    print("\n1. Analyzing Trading Signals...")
    analyzer.analyze_signals()
    
    print("\n2. Analyzing Trade Execution...")
    analyzer.analyze_trade_execution()
    
    print("\n3. Comparing Signals and Trades...")
    analyzer.compare_signals_and_trades()

if __name__ == "__main__":
    main()