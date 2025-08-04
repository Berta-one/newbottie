# headless_bot.py - Main execution loop
import time
import logging
from datetime import datetime
from engine.trading_core import TradingCore
from reporting.email_reporter import EmailReporter
from reporting.metrics_logger import MetricsLogger

logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[
                       logging.FileHandler('bot.log'),
                       logging.StreamHandler()
                   ])

class HeadlessTradingBot:
    def __init__(self):
        self.trading_core = TradingCore()
        self.email_reporter = EmailReporter()
        self.metrics_logger = MetricsLogger()
        self.logger = logging.getLogger(__name__)
        
    def run_trading_cycle(self):
        """Execute one trading cycle"""
        try:
            # Get market data
            market_data = self.trading_core.get_market_data()
            
            # Generate signals
            signal_result = self.trading_core.process_market_data(market_data)
            
            # Log metrics
            self.metrics_logger.log_trade_signal(signal_result)
            
            # Execute trades if needed
            if signal_result['signal'] in ['BUY', 'SELL']:
                trade_result = self.trading_core.execute_trade(signal_result)
                self.metrics_logger.log_trade_execution(trade_result)
                
            return signal_result
            
        except Exception as e:
            self.logger.error(f"Trading cycle failed: {e}")
            self.email_reporter.send_error_alert(str(e))
            return None
    
    def daily_report(self):
        """Generate and send daily performance report"""
        try:
            metrics = self.metrics_logger.get_daily_metrics()
            report = self.email_reporter.generate_daily_report(metrics)
            self.email_reporter.send_daily_report(report)
            self.logger.info("Daily report sent successfully")
        except Exception as e:
            self.logger.error(f"Daily report failed: {e}")
    
    def run(self):
        """Main execution loop"""
        self.logger.info("Starting headless trading bot...")
        last_daily_report = datetime.now().date()
        
        while True:
            try:
                # Run trading cycle
                self.run_trading_cycle()
                
                # Send daily report if needed
                current_date = datetime.now().date()
                if current_date > last_daily_report:
                    self.daily_report()
                    last_daily_report = current_date
                
                # Wait for next cycle (e.g., 5 minutes)
                time.sleep(300)
                
            except KeyboardInterrupt:
                self.logger.info("Bot stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    bot = HeadlessTradingBot()
    bot.run()

# reporting/email_reporter.py
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

class EmailReporter:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email = os.getenv('BOT_EMAIL')
        self.password = os.getenv('BOT_EMAIL_PASSWORD')
        self.recipient = os.getenv('REPORT_RECIPIENT_EMAIL')
    
    def send_email(self, subject, body):
        """Send email report"""
        msg = MIMEMultipart()
        msg['From'] = self.email
        msg['To'] = self.recipient
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.email, self.password)
            server.send_message(msg)
    
    def generate_daily_report(self, metrics):
        """Generate HTML daily report"""
        html = f"""
        <html>
        <head><title>Trading Bot Daily Report</title></head>
        <body>
        <h2>Trading Bot Performance - {datetime.now().strftime('%Y-%m-%d')}</h2>
        
        <h3>Summary</h3>
        <ul>
        <li>Total Trades: {metrics.get('total_trades', 0)}</li>
        <li>Profitable Trades: {metrics.get('profitable_trades', 0)}</li>
        <li>Win Rate: {metrics.get('win_rate', 0):.1%}</li>
        <li>Daily P&L: ${metrics.get('daily_pnl', 0):.2f}</li>
        <li>Total Portfolio Value: ${metrics.get('portfolio_value', 0):.2f}</li>
        </ul>
        
        <h3>Recent Signals</h3>
        <table border="1">
        <tr><th>Time</th><th>Signal</th><th>Price</th><th>Confidence</th></tr>
        """
        
        for signal in metrics.get('recent_signals', []):
            html += f"""
            <tr>
            <td>{signal['timestamp']}</td>
            <td>{signal['signal']}</td>
            <td>${signal['price']:.2f}</td>
            <td>{signal.get('confidence', 'N/A')}</td>
            </tr>
            """
        
        html += """
        </table>
        </body>
        </html>
        """
        return html
    
    def send_error_alert(self, error_msg):
        """Send immediate error alert"""
        subject = "🚨 Trading Bot Error Alert"
        body = f"""
        <html>
        <body>
        <h2>Trading Bot Error</h2>
        <p><strong>Time:</strong> {datetime.now()}</p>
        <p><strong>Error:</strong> {error_msg}</p>
        <p>Please check the bot logs for more details.</p>
        </body>
        </html>
        """
        self.send_email(subject, body)

# reporting/metrics_logger.py
import json
import csv
from datetime import datetime, date
from pathlib import Path

class MetricsLogger:
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.trades_file = self.log_dir / "trades.csv"
        self.signals_file = self.log_dir / "signals.csv"
        
        # Initialize CSV files if they don't exist
        self._init_csv_files()
    
    def _init_csv_files(self):
        """Initialize CSV files with headers"""
        if not self.trades_file.exists():
            with open(self.trades_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'signal', 'price', 'quantity', 'pnl', 'portfolio_value'])
        
        if not self.signals_file.exists():
            with open(self.signals_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'signal', 'price', 'confidence', 'executed'])
    
    def log_trade_signal(self, signal_result):
        """Log trading signal to CSV"""
        with open(self.signals_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                signal_result['signal'],
                signal_result['price'],
                signal_result.get('confidence', ''),
                signal_result['signal'] in ['BUY', 'SELL']
            ])
    
    def log_trade_execution(self, trade_result):
        """Log executed trade to CSV"""
        with open(self.trades_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                trade_result['signal'],
                trade_result['price'],
                trade_result['quantity'],
                trade_result.get('pnl', 0),
                trade_result.get('portfolio_value', 0)
            ])
    
    def get_daily_metrics(self):
        """Calculate daily performance metrics"""
        import pandas as pd
        
        today = date.today()
        
        # Load today's data
        try:
            trades_df = pd.read_csv(self.trades_file)
            signals_df = pd.read_csv(self.signals_file)
            
            # Filter for today
            trades_df['date'] = pd.to_datetime(trades_df['timestamp']).dt.date
            signals_df['date'] = pd.to_datetime(signals_df['timestamp']).dt.date
            
            today_trades = trades_df[trades_df['date'] == today]
            today_signals = signals_df[signals_df['date'] == today]
            
            # Calculate metrics
            total_trades = len(today_trades)
            profitable_trades = len(today_trades[today_trades['pnl'] > 0])
            win_rate = profitable_trades / total_trades if total_trades > 0 else 0
            daily_pnl = today_trades['pnl'].sum() if total_trades > 0 else 0
            portfolio_value = today_trades['portfolio_value'].iloc[-1] if total_trades > 0 else 0
            
            # Recent signals
            recent_signals = today_signals.tail(10).to_dict('records')
            
            return {
                'total_trades': total_trades,
                'profitable_trades': profitable_trades,
                'win_rate': win_rate,
                'daily_pnl': daily_pnl,
                'portfolio_value': portfolio_value,
                'recent_signals': recent_signals
            }
            
        except Exception as e:
            return {'error': str(e)}

# Simplified Dockerfile for headless deployment
FROM python:3.11-slim

WORKDIR /app

# Install only essential dependencies
COPY requirements_headless.txt .
RUN pip install --no-cache-dir -r requirements_headless.txt

COPY . .

# Run the headless bot
CMD ["python", "headless_bot.py"]
