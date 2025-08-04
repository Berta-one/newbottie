# reporting/__init__.py (save as reporting/__init__.py)
from .email_reporter import EmailReporter
from .metrics_logger import MetricsLogger

__all__ = ['EmailReporter', 'MetricsLogger']

# reporting/email_reporter.py (save as reporting/email_reporter.py)
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

class EmailReporter:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email = os.getenv('BOT_EMAIL')
        self.password = os.getenv('BOT_EMAIL_PASSWORD')
        self.recipient = os.getenv('REPORT_RECIPIENT_EMAIL')
        self.logger = logging.getLogger(__name__)
    
    def send_email(self, subject, body):
        """Send email report"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = self.recipient
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            self.logger.info(f"Email sent successfully: {subject}")
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
    
    def generate_daily_report(self, metrics):
        """Generate HTML daily report"""
        html = f"""
        <html>
        <head><title>Trading Bot Daily Report</title></head>
        <body style="font-family: Arial, sans-serif;">
        
        <h2>🤖 Trading Bot Performance Report</h2>
        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px;">
        <h3>📊 Daily Summary</h3>
        <ul>
        <li><strong>Total Signals:</strong> {metrics.get('total_signals', 0)}</li>
        <li><strong>Executed Trades:</strong> {metrics.get('total_trades', 0)}</li>
        <li><strong>Win Rate:</strong> {metrics.get('win_rate', 0):.1%}</li>
        <li><strong>Daily P&L:</strong> <span style="color: {'green' if metrics.get('daily_pnl', 0) >= 0 else 'red'};">${metrics.get('daily_pnl', 0):.2f}</span></li>
        <li><strong>Portfolio Value:</strong> ${metrics.get('portfolio_value', 0):,.2f}</li>
        </ul>
        </div>
        
        <h3>📈 Recent Activity</h3>
        <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr style="background-color: #4CAF50; color: white;">
        <th style="padding: 8px;">Time</th>
        <th style="padding: 8px;">Signal</th>
        <th style="padding: 8px;">Price</th>
        <th style="padding: 8px;">Status</th>
        </tr>
        """
        
        for signal in metrics.get('recent_signals', [])[-10:]:  # Last 10 signals
            status_color = 'green' if signal.get('executed') else 'orange'
            status_text = 'Executed' if signal.get('executed') else 'Signal Only'
            
            html += f"""
            <tr>
            <td style="padding: 8px;">{signal.get('timestamp', '')[:19]}</td>
            <td style="padding: 8px; font-weight: bold;">{signal.get('signal', '')}</td>
            <td style="padding: 8px;">${signal.get('price', 0):.2f}</td>
            <td style="padding: 8px; color: {status_color};">{status_text}</td>
            </tr>
            """
        
        html += """
        </table>
        
        <hr>
        <p style="color: #666; font-size: 12px;">
        This is an automated report from your trading bot. 
        Check logs for detailed information.
        </p>
        
        </body>
        </html>
        """
        return html
    
    def send_error_alert(self, error_msg):
        """Send immediate error alert"""
        subject = "🚨 Trading Bot Error Alert"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
        <h2 style="color: red;">⚠️ Trading Bot Error</h2>
        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <div style="background-color: #ffebcc; padding: 15px; border-left: 5px solid #ff6b35;">
        <p><strong>Error Details:</strong></p>
        <pre style="background-color: #f5f5f5; padding: 10px; overflow-x: auto;">{error_msg}</pre>
        </div>
        <p>Please check the bot logs for more details: <code>logs/bot.log</code></p>
        </body>
        </html>
        """
        self.send_email(subject, body)

    def send_daily_report(self, report_html):
        """Send the daily report"""
        subject = f"📊 Trading Bot Daily Report - {datetime.now().strftime('%Y-%m-%d')}"
        self.send_email(subject, report_html)

# reporting/metrics_logger.py (save as reporting/metrics_logger.py)
import json
import csv
from datetime import datetime, date
from pathlib import Path
import pandas as pd
import logging

class MetricsLogger:
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.trades_file = self.log_dir / "trades.csv"
        self.signals_file = self.log_dir / "signals.csv"
        self.metrics_file = self.log_dir / "daily_metrics.jsonl"
        self.logger = logging.getLogger(__name__)
        
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
        try:
            with open(self.signals_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    signal_result.get('signal', 'UNKNOWN'),
                    signal_result.get('price', 0),
                    signal_result.get('confidence', ''),
                    signal_result.get('signal', '') in ['BUY', 'SELL']
                ])
            self.logger.debug(f"Logged signal: {signal_result.get('signal')}")
        except Exception as e:
            self.logger.error(f"Failed to log signal: {e}")
    
    def log_trade_execution(self, trade_result):
        """Log executed trade to CSV"""
        try:
            with open(self.trades_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    trade_result.get('signal', 'UNKNOWN'),
                    trade_result.get('price', 0),
                    trade_result.get('quantity', 0),
                    trade_result.get('pnl', 0),
                    trade_result.get('portfolio_value', 0)
                ])
            self.logger.info(f"Logged trade execution: {trade_result.get('signal')} at ${trade_result.get('price')}")
        except Exception as e:
            self.logger.error(f"Failed to log trade: {e}")
    
    def get_daily_metrics(self):
        """Calculate daily performance metrics"""
        try:
            today = date.today()
            
            # Load data with error handling
            trades_df = self._safe_load_csv(self.trades_file)
            signals_df = self._safe_load_csv(self.signals_file)
            
            if trades_df.empty and signals_df.empty:
                return self._empty_metrics()
            
            # Filter for today
            if not signals_df.empty:
                signals_df['date'] = pd.to_datetime(signals_df['timestamp']).dt.date
                today_signals = signals_df[signals_df['date'] == today]
            else:
                today_signals = pd.DataFrame()
            
            if not trades_df.empty:
                trades_df['date'] = pd.to_datetime(trades_df['timestamp']).dt.date
                today_trades = trades_df[trades_df['date'] == today]
            else:
                today_trades = pd.DataFrame()
            
            # Calculate metrics
            total_signals = len(today_signals)
            total_trades = len(today_trades)
            profitable_trades = len(today_trades[today_trades['pnl'] > 0]) if total_trades > 0 else 0
            win_rate = profitable_trades / total_trades if total_trades > 0 else 0
            daily_pnl = today_trades['pnl'].sum() if total_trades > 0 else 0
            portfolio_value = today_trades['portfolio_value'].iloc[-1] if total_trades > 0 else 10000  # Default
            
            # Recent signals (convert to dict for JSON serialization)
            recent_signals = []
            if not today_signals.empty:
                recent_signals = today_signals.tail(20).to_dict('records')
                # Clean up the records for JSON serialization
                for signal in recent_signals:
                    if pd.isna(signal.get('confidence')):
                        signal['confidence'] = None
            
            metrics = {
                'date': today.isoformat(),
                'total_signals': total_signals,
                'total_trades': total_trades,
                'profitable_trades': profitable_trades,
                'win_rate': win_rate,
                'daily_pnl': float(daily_pnl),
                'portfolio_value': float(portfolio_value),
                'recent_signals': recent_signals
            }
            
            # Save daily metrics to JSONL file
            self._save_daily_metrics(metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating daily metrics: {e}")
            return {'error': str(e)}
    
    def _safe_load_csv(self, filepath):
        """Safely load CSV file"""
        try:
            if filepath.exists():
                return pd.read_csv(filepath)
            else:
                return pd.DataFrame()
        except Exception as e:
            self.logger.warning(f"Could not load {filepath}: {e}")
            return pd.DataFrame()
    
    def _empty_metrics(self):
        """Return empty metrics structure"""
        return {
            'date': date.today().isoformat(),
            'total_signals': 0,
            'total_trades': 0,
            'profitable_trades': 0,
            'win_rate': 0.0,
            'daily_pnl': 0.0,
            'portfolio_value': 10000.0,  # Starting capital
            'recent_signals': []
        }
    
    def _save_daily_metrics(self, metrics):
        """Save daily metrics to JSONL file"""
        try:
            with open(self.metrics_file, 'a') as f:
                f.write(json.dumps(metrics) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to save daily metrics: {e}")

# requirements_headless.txt (save as requirements_headless.txt in root)
ccxt>=4.0.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
xgboost>=1.7.0
tensorflow>=2.13.0
requests>=2.31.0
python-dotenv>=1.0.0

# Optional quantum dependencies (uncomment if using quantum features)
# qiskit>=0.45.0
# qiskit-machine-learning>=0.7.0
# qiskit-optimization>=0.6.0

# Updated .env file (save as .env in root)
# Trading Configuration
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_here
MODE=paper  # or 'live' for real trading

# Email Reporting Configuration
BOT_EMAIL=your.bot.email@gmail.com
BOT_EMAIL_PASSWORD=your_app_specific_password
REPORT_RECIPIENT_EMAIL=your.email@gmail.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Model Configuration
LSTM_MODEL_PATH=models/lstm_model.h5
XGB_MODEL_PATH=models/xgboost_model.json

# Trading Parameters
INITIAL_CAPITAL=10000
RISK_PER_TRADE=0.02
MAX_POSITIONS=3
