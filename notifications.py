#!/usr/bin/env python3
"""
Email Notification System - notifications.py
============================================

Comprehensive email notification system for trading bot events.
Sends alerts for trades, signals, system status, and emergencies.
Fully compatible with Railway deployment and Gmail integration.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any, List, Optional
import threading
import queue
import time
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailNotificationSystem:
    """Advanced email notification system for trading bot"""
    
    def __init__(self):
        # Email configuration from Railway environment
        self.smtp_server = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
        self.username = os.getenv("EMAIL_USERNAME", "")
        self.password = os.getenv("EMAIL_PASSWORD", "")  # Use App Password for Gmail
        self.from_email = os.getenv("EMAIL_FROM", self.username)
        self.to_emails = [email.strip() for email in os.getenv("EMAIL_TO", "").split(",") if email.strip()]
        
        # Notification settings
        self.enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
        self.send_trades = os.getenv("EMAIL_TRADES", "true").lower() == "true"
        self.send_signals = os.getenv("EMAIL_SIGNALS", "true").lower() == "true"
        self.send_system = os.getenv("EMAIL_SYSTEM", "true").lower() == "true"
        self.send_errors = os.getenv("EMAIL_ERRORS", "true").lower() == "true"
        
        # Rate limiting (prevent spam)
        self.max_emails_per_hour = int(os.getenv("EMAIL_MAX_PER_HOUR", "20"))
        self.email_timestamps = []
        
        # Email queue for async sending
        self.email_queue = queue.Queue()
        self.worker_thread = None
        
        # Only start worker if properly configured
        if self.enabled and self.username and self.password and self.to_emails:
            self.start_worker()
        
        logger.info(f"Email notifications: {'ENABLED' if self.enabled else 'DISABLED'}")
        if self.enabled:
            logger.info(f"Configured to send to: {', '.join(self.to_emails)}")
    
    def start_worker(self):
        """Start background worker thread for sending emails"""
        if not self.worker_thread or not self.worker_thread.is_alive():
            self.worker_thread = threading.Thread(target=self._email_worker, daemon=True)
            self.worker_thread.start()
            logger.info("Email worker thread started")
    
    def _email_worker(self):
        """Background worker to process email queue"""
        while True:
            try:
                email_data = self.email_queue.get(timeout=60)
                if email_data is None:  # Shutdown signal
                    break
                
                self._send_email_sync(
                    email_data['subject'],
                    email_data['body'],
                    email_data['html']
                )
                
                self.email_queue.task_done()
                time.sleep(2)  # Rate limiting between emails
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Email worker error: {e}")
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        now = time.time()
        # Remove timestamps older than 1 hour
        self.email_timestamps = [ts for ts in self.email_timestamps if now - ts < 3600]
        
        return len(self.email_timestamps) < self.max_emails_per_hour
    
    def _send_email_sync(self, subject: str, body: str, html: bool = False):
        """Send email synchronously"""
        try:
            if not self.enabled or not self.username or not self.password or not self.to_emails:
                logger.debug("Email not configured properly, skipping")
                return False
            
            if not self._check_rate_limit():
                logger.warning("Email rate limit exceeded, skipping email")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            
            # Add body
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            # Record timestamp
            self.email_timestamps.append(time.time())
            logger.info(f"Email sent: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email '{subject}': {e}")
            return False
    
    def send_email_async(self, subject: str, body: str, html: bool = False):
        """Queue email for async sending"""
        if not self.enabled:
            return
        
        try:
            self.email_queue.put({
                'subject': subject,
                'body': body,
                'html': html
            }, timeout=5)
        except queue.Full:
            logger.warning("Email queue full, dropping email")
    
    def notify_trade_executed(self, trade_data: Dict[str, Any]):
        """Notify about executed trade"""
        if not self.send_trades:
            return
        
        symbol = trade_data.get('symbol', 'Unknown')
        side = trade_data.get('side', 'Unknown')
        quantity = trade_data.get('quantity', 0)
        price = trade_data.get('price', 0)
        value = trade_data.get('value', quantity * price if quantity and price else 0)
        
        subject = f"🤖 Bottie Trade: {side} {symbol}"
        
        body = f"""
🚀 BOTTIE TRADING ALERT - Trade Executed

📊 Trade Details:
• Symbol: {symbol}
• Side: {side}
• Quantity: {quantity}
• Price: ${price:,.4f}
• Value: ${value:,.2f}
• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

🎯 Strategy: Enhanced breakout detection
💰 Portfolio Impact: {'+' if side.upper() == 'BUY' else '-'}${value:,.2f}
🔗 Monitor: {os.getenv('RAILWAY_STATIC_URL', 'Your Dashboard URL')}

Happy Trading! 🚀
Bottie Bot System
        """
        
        self.send_email_async(subject, body)
    
    def notify_trade_closed(self, trade_data: Dict[str, Any]):
        """Notify about closed position"""
        if not self.send_trades:
            return
        
        symbol = trade_data.get('symbol', 'Unknown')
        pnl = trade_data.get('pnl', 0)
        pnl_percent = trade_data.get('pnl_percent', 0)
        reason = trade_data.get('reason', 'Unknown')
        
        emoji = "📈" if pnl > 0 else "📉"
        subject = f"{emoji} Position Closed: {symbol} ({pnl_percent:+.2f}%)"
        
        body = f"""
{emoji} BOTTIE TRADING ALERT - Position Closed

📊 Position Summary:
• Symbol: {symbol}
• P&L: ${pnl:,.2f} ({pnl_percent:+.2f}%)
• Exit Reason: {reason}
• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

{'🎉 Profitable trade! Great job Bottie!' if pnl > 0 else '📊 Loss contained by risk management'}

🔗 View Analytics: {os.getenv('RAILWAY_STATIC_URL', 'Your Dashboard URL')}

Keep Trading! 🚀
Bottie Bot System
        """
        
        self.send_email_async(subject, body)
    
    def notify_strong_signal(self, signal_data: Dict[str, Any]):
        """Notify about strong trading signals"""
        if not self.send_signals:
            return
        
        symbol = signal_data.get('symbol', 'Unknown')
        confidence = signal_data.get('confidence', 0)
        signal = signal_data.get('signal', 'Unknown')
        price = signal_data.get('price', 0)
        
        # Only send for very strong signals (80%+ confidence)
        if confidence < 0.8:
            return
        
        subject = f"🎯 Strong Signal: {signal} {symbol} ({confidence:.1%})"
        
        body = f"""
🎯 BOTTIE SIGNAL ALERT - High Confidence Detection

📊 Signal Analysis:
• Symbol: {symbol}
• Signal: {signal}
• Confidence: {confidence:.1%}
• Current Price: ${price:,.4f}
• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

🔍 Technical Analysis:
• Breakout Strength: {signal_data.get('breakout_strength', 'N/A')}
• Volume Ratio: {signal_data.get('volume_ratio', 'N/A')}
• RSI Level: {signal_data.get('rsi', 'N/A')}

{'🤖 Auto-executing if enabled...' if os.getenv('AUTO_TRADE_ENABLED', 'false') == 'true' else '✋ Manual review recommended'}

🔗 Dashboard: {os.getenv('RAILWAY_STATIC_URL', 'Your Dashboard URL')}

Stay Alert! 🚀
Bottie Bot System
        """
        
        self.send_email_async(subject, body)
    
    def notify_system_status(self, status: str, details: str = ""):
        """Notify about system status changes"""
        if not self.send_system:
            return
        
        emoji_map = {
            "started": "🟢",
            "stopped": "🔴", 
            "error": "❌",
            "warning": "⚠️",
            "maintenance": "🔧",
            "scanning": "🔍",
            "trading": "📈"
        }
        
        emoji = emoji_map.get(status.lower(), "ℹ️")
        subject = f"{emoji} Bottie System: {status.title()}"
        
        body = f"""
{emoji} BOTTIE SYSTEM ALERT

🖥️ System Status: {status.title()}
🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

📝 Details:
{details}

🔗 Dashboard: {os.getenv('RAILWAY_STATIC_URL', 'Your Dashboard URL')}
📊 Railway Logs: Check your Railway dashboard for technical details

System Monitoring 🤖
Bottie Bot System
        """
        
        self.send_email_async(subject, body)
    
    def notify_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Notify about system errors"""
        if not self.send_errors:
            return
        
        subject = f"❌ Bottie Error: {error_type}"
        
        body = f"""
❌ BOTTIE ERROR ALERT

🚨 Error Type: {error_type}
🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

📝 Error Details:
{error_message}

🔍 Context:
{json.dumps(context, indent=2) if context else 'No additional context available'}

🔧 Recommended Actions:
1. Check Railway application logs for detailed traces
2. Verify Binance API connection and credentials
3. Monitor system resources and performance
4. Restart application if necessary

🔗 Dashboard: {os.getenv('RAILWAY_STATIC_URL', 'Your Dashboard URL')}
📱 Railway Console: Check your Railway project dashboard

System Recovery 🤖
Bottie Bot System
        """
        
        self.send_email_async(subject, body)
    
    def notify_portfolio_milestone(self, milestone_data: Dict[str, Any]):
        """Notify about portfolio milestones"""
        milestone_type = milestone_data.get('type', 'unknown')
        value = milestone_data.get('value', 0)
        
        subject = f"🎉 Portfolio Milestone: {milestone_type}"
        
        body = f"""
🎉 BOTTIE MILESTONE ALERT

🏆 Achievement: {milestone_type}
💰 Current Value: ${value:,.2f}
🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

📊 Statistics:
• Total Trades: {milestone_data.get('total_trades', 'N/A')}
• Win Rate: {milestone_data.get('win_rate', 'N/A')}%
• Best Trade: {milestone_data.get('best_trade', 'N/A')}%

🚀 Keep up the great work!

🔗 View Details: {os.getenv('RAILWAY_STATIC_URL', 'Your Dashboard URL')}

Celebrating Success! 🎊
Bottie Bot System
        """
        
        self.send_email_async(subject, body)
    
    def send_test_email(self) -> bool:
        """Send test email to verify configuration"""
        subject = "🧪 Bottie Email Test - System Ready"
        
        body = f"""
🧪 BOTTIE EMAIL TEST

✅ Email notification system is operational!

📧 Configuration:
• SMTP Server: {self.smtp_server}:{self.smtp_port}
• From: {self.from_email}
• To: {', '.join(self.to_emails)}
• Rate Limit: {self.max_emails_per_hour} emails/hour

🔧 Enabled Notifications:
• Trade Execution: {'✅' if self.send_trades else '❌'}
• Strong Signals: {'✅' if self.send_signals else '❌'}
• System Status: {'✅' if self.send_system else '❌'}
• Error Alerts: {'✅' if self.send_errors else '❌'}

🚀 Bottie will now send you important trading updates!

🔗 Dashboard: {os.getenv('RAILWAY_STATIC_URL', 'Your Dashboard URL')}

System Ready ✅
Bottie Bot System

---
Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
        """
        
        return self._send_email_sync(subject, body)
    
    def get_status(self) -> Dict[str, Any]:
        """Get notification system status"""
        return {
            'enabled': self.enabled,
            'configured': bool(self.username and self.password and self.to_emails),
            'worker_running': self.worker_thread and self.worker_thread.is_alive() if self.worker_thread else False,
            'queue_size': self.email_queue.qsize(),
            'emails_sent_hour': len(self.email_timestamps),
            'rate_limit': self.max_emails_per_hour,
            'to_emails': self.to_emails,
            'types': {
                'trades': self.send_trades,
                'signals': self.send_signals,
                'system': self.send_system,
                'errors': self.send_errors
            }
        }

# Global notification instance
_notification_system = None

def get_notification_system():
    """Get global notification system instance"""
    global _notification_system
    if _notification_system is None:
        _notification_system = EmailNotificationSystem()
    return _notification_system

# Convenience functions for easy integration
def notify_trade(trade_data: Dict[str, Any]):
    """Quick function to notify about trade execution"""
    get_notification_system().notify_trade_executed(trade_data)

def notify_trade_close(trade_data: Dict[str, Any]):
    """Quick function to notify about trade closure"""
    get_notification_system().notify_trade_closed(trade_data)

def notify_signal(signal_data: Dict[str, Any]):
    """Quick function to notify about strong signals"""
    get_notification_system().notify_strong_signal(signal_data)

def notify_error(error_type: str, error_message: str, context: Dict[str, Any] = None):
    """Quick function to notify about errors"""
    get_notification_system().notify_error(error_type, error_message, context)

def notify_system(status: str, details: str = ""):
    """Quick function to notify about system status"""
    get_notification_system().notify_system_status(status, details)

def notify_milestone(milestone_data: Dict[str, Any]):
    """Quick function to notify about milestones"""
    get_notification_system().notify_portfolio_milestone(milestone_data)

def send_test_notification() -> bool:
    """Send test notification to verify setup"""
    return get_notification_system().send_test_email()

def get_notification_status() -> Dict[str, Any]:
    """Get notification system status"""
    return get_notification_system().get_status()

if __name__ == "__main__":
    # Test the notification system
    print("Testing Bottie Email Notification System...")
    print("=" * 50)
    
    notifier = EmailNotificationSystem()
    status = notifier.get_status()
    
    print(f"System Status:")
    print(f"  Enabled: {status['enabled']}")
    print(f"  Configured: {status['configured']}")
    print(f"  Worker Running: {status['worker_running']}")
    print(f"  To Emails: {', '.join(status['to_emails']) if status['to_emails'] else 'None'}")
    
    if status['enabled'] and status['configured']:
        print("\nSending test email...")
        success = notifier.send_test_email()
        print(f"Test Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    else:
        print("\n⚠️ Email notifications not fully configured.")
        print("Set EMAIL_ENABLED=true and configure EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_TO")