#!/usr/bin/env python3
"""
Pure Flask Crypto Trading Bot - No Streamlit Dependencies
"""
import subprocess
import psutil
import os

BOT_SCRIPT = "bot_service.py"

# ✅ Check if the bot is running
def is_bot_running():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if BOT_SCRIPT in " ".join(proc.info['cmdline']):
            return True
    return False

# ✅ Auto-start the bot if not running
if not is_bot_running():
    subprocess.Popen(["python", BOT_SCRIPT])

import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, flash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Try to import Binance
try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False

# Configuration
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')
USE_TESTNET = os.getenv('USE_TESTNET', 'true').lower() == 'true'

# In-memory storage
trades_history = []
activity_logs = []
bot_status = {
    'auto_trading': False,
    'last_scan': None,
    'total_trades': 0,
    'total_pnl': 0.0
}

def log_activity(message):
    """Log activity with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    activity_logs.append(log_entry)
    if len(activity_logs) > 200:
        activity_logs.pop(0)
    print(log_entry)  # Also print to console

def get_binance_client():
    """Initialize Binance client"""
    if not BINANCE_AVAILABLE:
        return None, "Binance library not available"
    
    if not API_KEY or not API_SECRET:
        return None, "API credentials not configured"
    
    try:
        client = Client(API_KEY, API_SECRET)
        if USE_TESTNET:
            client.API_URL = 'https://testnet.binance.vision/api'
        
        # Test connection
        client.get_server_time()
        return client, "Connected"
    except Exception as e:
        return None, str(e)

def get_portfolio_data():
    """Get portfolio information"""
    client, status = get_binance_client()
    
    if not client:
        return {}, 0.0, status
    
    try:
        account = client.get_account()
        portfolio = {}
        total_value = 0.0
        
        for balance in account['balances']:
            free = float(balance['free'])
            locked = float(balance['locked'])
            total = free + locked
            
            if total > 0:
                asset = balance['asset']
                usd_value = total
                
                # Convert to USD (simplified - just use USDT rate)
                if asset != 'USDT':
                    try:
                        ticker = client.get_symbol_ticker(symbol=f"{asset}USDT")
                        usd_value = total * float(ticker['price'])
                    except:
                        usd_value = 0
                
                portfolio[asset] = {
                    'free': free,
                    'locked': locked,
                    'total': total,
                    'usd_value': usd_value
                }
                total_value += usd_value
        
        return portfolio, total_value, "Success"
    
    except Exception as e:
        return {}, 0.0, str(e)

# HTML Template
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 Crypto Trading Bot</title>
    <style>
        :root {
            --primary: #667eea;
            --secondary: #764ba2;
            --accent: #ff6b6b;
            --success: #2ecc71;
            --warning: #f39c12;
            --danger: #e74c3c;
            --dark: rgba(0,0,0,0.8);
            --light: rgba(255,255,255,0.1);
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            min-height: 100vh;
            line-height: 1.6;
        }
        
        .navbar {
            background: var(--dark);
            padding: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }
        
        .logo { font-size: 1.5rem; font-weight: bold; }
        
        .nav-links {
            display: flex;
            gap: 1rem;
            list-style: none;
        }
        
        .nav-links a {
            color: white;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        
        .nav-links a:hover, .nav-links a.active {
            background: var(--light);
            transform: translateY(-2px);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .card {
            background: var(--light);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 1.5rem;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.3s ease;
        }
        
        .card:hover { transform: translateY(-5px); }
        
        .card h3 {
            margin-bottom: 1rem;
            color: #fff;
            font-size: 1.2rem;
        }
        
        .metric {
            text-align: center;
            padding: 1rem;
        }
        
        .metric .value {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
            display: block;
        }
        
        .metric .label {
            opacity: 0.8;
            font-size: 0.9rem;
        }
        
        .btn {
            background: var(--accent);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1rem;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s ease;
            text-align: center;
        }
        
        .btn:hover {
            background: #ff5252;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(255,107,107,0.4);
        }
        
        .btn-success { background: var(--success); }
        .btn-success:hover { background: #27ae60; }
        
        .btn-warning { background: var(--warning); }
        .btn-warning:hover { background: #e67e22; }
        
        .form-group {
            margin-bottom: 1rem;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }
        
        .form-group input,
        .form-group select {
            width: 100%;
            padding: 0.75rem;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            background: rgba(255,255,255,0.9);
            color: #333;
        }
        
        .status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .status-connected { background: var(--success); }
        .status-disconnected { background: var(--danger); }
        .status-testnet { background: var(--warning); }
        
        .table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }
        
        .table th,
        .table td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .table th {
            background: var(--light);
            font-weight: 600;
        }
        
        .logs-container {
            background: var(--dark);
            padding: 1rem;
            border-radius: 8px;
            max-height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.875rem;
        }
        
        .log-entry {
            margin-bottom: 0.25rem;
            padding: 0.25rem;
            border-radius: 4px;
        }
        
        .log-entry:hover {
            background: rgba(255,255,255,0.05);
        }
        
        .flash-messages {
            margin-bottom: 1rem;
        }
        
        .flash-message {
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
        }
        
        .flash-success { background: var(--success); }
        .flash-error { background: var(--danger); }
        .flash-warning { background: var(--warning); }
        
        @media (max-width: 768px) {
            .navbar {
                flex-direction: column;
                gap: 1rem;
            }
            
            .nav-links {
                flex-wrap: wrap;
                justify-content: center;
            }
            
            .container {
                padding: 1rem;
            }
            
            .grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="logo">🤖 Crypto Trading Bot</div>
        <ul class="nav-links">
            <li><a href="/" class="{{ 'active' if request.endpoint == 'dashboard' else '' }}">🏠 Dashboard</a></li>
            <li><a href="/portfolio" class="{{ 'active' if request.endpoint == 'portfolio' else '' }}">📊 Portfolio</a></li>
            <li><a href="/trade" class="{{ 'active' if request.endpoint == 'trade' else '' }}">💰 Trade</a></li>
            <li><a href="/logs" class="{{ 'active' if request.endpoint == 'logs_page' else '' }}">📜 Logs</a></li>
        </ul>
    </nav>
    
    <div class="container">
        <div class="flash-messages">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="flash-message flash-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
        </div>
        
        {% block content %}{% endblock %}
    </div>
    
    <script>
        // Auto-refresh every 60 seconds for dashboard
        if (window.location.pathname === '/') {
            setTimeout(() => {
                window.location.reload();
            }, 60000);
        }
        
        // Add some interactivity
        document.addEventListener('DOMContentLoaded', function() {
            // Add loading state to buttons
            const buttons = document.querySelectorAll('.btn');
            buttons.forEach(btn => {
                btn.addEventListener('click', function() {
                    if (this.type === 'submit') {
                        this.innerHTML = '⏳ Processing...';
                        this.disabled = true;
                    }
                });
            });
        });
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Main dashboard"""
    log_activity("Dashboard accessed")
    
    # Get connection status
    client, connection_status = get_binance_client()
    connected = client is not None
    
    # Get portfolio data
    portfolio, total_value, portfolio_status = get_portfolio_data()
    
    # Calculate metrics
    assets_count = len(portfolio)
    recent_trades = len([t for t in trades_history if 
                        datetime.fromisoformat(t.get('timestamp', '2000-01-01')) > 
                        datetime.now() - timedelta(hours=24)])
    
    dashboard_html = f"""
    {{% extends "base" %}}
    {{% block content %}}
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="font-size: 2.5rem; margin-bottom: 1rem;">Trading Dashboard</h1>
        <div>
            <span class="status-badge status-{'connected' if connected else 'disconnected'}">
                {'🟢 Connected' if connected else '🔴 Disconnected'}
            </span>
            <span class="status-badge status-testnet" style="margin-left: 1rem;">
                {'🧪 Testnet Mode' if USE_TESTNET else '⚠️ Live Trading'}
            </span>
        </div>
    </div>
    
    <div class="grid">
        <div class="card metric">
            <span class="value">${total_value:,.2f}</span>
            <span class="label">Portfolio Value</span>
        </div>
        <div class="card metric">
            <span class="value">{assets_count}</span>
            <span class="label">Assets Held</span>
        </div>
        <div class="card metric">
            <span class="value">{len(trades_history)}</span>
            <span class="label">Total Trades</span>
        </div>
        <div class="card metric">
            <span class="value">{recent_trades}</span>
            <span class="label">24h Trades</span>
        </div>
    </div>
    
    <div class="grid">
        <div class="card">
            <h3>⚡ Quick Actions</h3>
            <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                <a href="/trade" class="btn">💰 Manual Trade</a>
                <a href="/portfolio" class="btn btn-success">📊 View Portfolio</a>
                <a href="/api/refresh" class="btn btn-warning">🔄 Refresh Data</a>
            </div>
        </div>
        
        <div class="card">
            <h3>📊 System Status</h3>
            <p><strong>API Connection:</strong> {connection_status}</p>
            <p><strong>Portfolio Status:</strong> {portfolio_status}</p>
            <p><strong>Trading Mode:</strong> {'Testnet' if USE_TESTNET else 'Live'}</p>
            <p><strong>Last Update:</strong> {datetime.now().strftime('%H:%M:%S')}</p>
            <p><strong>Server:</strong> Railway Cloud</p>
        </div>
    </div>
    
    <div class="card">
        <h3>📈 Recent Activity</h3>
        <div class="logs-container">
    """
    
    for log in activity_logs[-20:]:
        dashboard_html += f'<div class="log-entry">{log}</div>'
    
    dashboard_html += """
        </div>
    </div>
    {% endblock %}
    """
    
    return render_template_string(BASE_TEMPLATE + dashboard_html)

@app.route('/portfolio')
def portfolio():
    """Portfolio page"""
    log_activity("Portfolio page accessed")
    
    portfolio, total_value, status = get_portfolio_data()
    
    portfolio_html = f"""
    {{% extends "base" %}}
    {{% block content %}}
    <h1>📊 Portfolio Overview</h1>
    
    <div class="grid">
        <div class="card metric">
            <span class="value">${total_value:,.2f}</span>
            <span class="label">Total Portfolio Value</span>
        </div>
        <div class="card metric">
            <span class="value">{len(portfolio)}</span>
            <span class="label">Assets Held</span>
        </div>
    </div>
    
    <div class="card">
        <h3>💰 Asset Holdings</h3>
        <p><strong>Status:</strong> {status}</p>
    """
    
    if portfolio:
        portfolio_html += """
        <table class="table">
            <thead>
                <tr>
                    <th>Asset</th>
                    <th>Free</th>
                    <th>Locked</th>
                    <th>Total</th>
                    <th>USD Value</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for asset, data in portfolio.items():
            portfolio_html += f"""
                <tr>
                    <td><strong>{asset}</strong></td>
                    <td>{data['free']:.6f}</td>
                    <td>{data['locked']:.6f}</td>
                    <td>{data['total']:.6f}</td>
                    <td>${data['usd_value']:.2f}</td>
                </tr>
            """
        
        portfolio_html += "</tbody></table>"
    else:
        portfolio_html += "<p>No assets found or unable to fetch portfolio data.</p>"
    
    portfolio_html += """
    </div>
    {% endblock %}
    """
    
    return render_template_string(BASE_TEMPLATE + portfolio_html)

@app.route('/trade', methods=['GET', 'POST'])
def trade():
    """Trading interface"""
    if request.method == 'POST':
        symbol = request.form.get('symbol')
        side = request.form.get('side')
        amount = float(request.form.get('amount', 0))
        
        if amount < 10:
            flash('Minimum trade amount is $10', 'error')
        else:
            # Simulate trade execution
            trade_record = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'status': 'SIMULATED',
                'price': 0  # Would get real price in actual implementation
            }
            
            trades_history.append(trade_record)
            log_activity(f"Trade executed: {side} {symbol} ${amount}")
            flash(f'Trade simulated: {side} {symbol} ${amount}', 'success')
            
            return redirect(url_for('trade'))
    
    trade_html = """
    {% extends "base" %}
    {% block content %}
    <h1>💰 Manual Trading</h1>
    
    <div class="grid">
        <div class="card">
            <h3>📈 Execute Trade</h3>
            <form method="POST">
                <div class="form-group">
                    <label for="symbol">Trading Pair</label>
                    <select name="symbol" id="symbol" required>
                        <option value="BTCUSDT">BTC/USDT</option>
                        <option value="ETHUSDT">ETH/USDT</option>
                        <option value="BNBUSDT">BNB/USDT</option>
                        <option value="ADAUSDT">ADA/USDT</option>
                        <option value="SOLUSDT">SOL/USDT</option>
                        <option value="XRPUSDT">XRP/USDT</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="side">Order Type</label>
                    <select name="side" id="side" required>
                        <option value="BUY">🟢 BUY (Long)</option>
                        <option value="SELL">🔴 SELL (Short)</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="amount">Amount (USDT)</label>
                    <input type="number" name="amount" id="amount" min="10" step="0.01" value="50" required>
                </div>
                
                <button type="submit" class="btn" style="width: 100%;">🚀 Execute Trade</button>
            </form>
        </div>
        
        <div class="card">
            <h3>📋 Recent Trades</h3>
            <div style="max-height: 400px; overflow-y: auto;">
    """
    
    for trade in trades_history[-10:]:
        timestamp = trade['timestamp'][:19].replace('T', ' ')
        trade_html += f"""
            <div style="padding: 0.75rem; border-bottom: 1px solid rgba(255,255,255,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong>{trade['symbol']}</strong>
                    <span class="status-badge status-{'connected' if trade['status'] == 'FILLED' else 'testnet'}">{trade['status']}</span>
                </div>
                <div>{trade['side']} ${trade['amount']}</div>
                <small style="opacity: 0.7;">{timestamp}</small>
            </div>
        """
    
    if not trades_history:
        trade_html += "<p style='text-align: center; opacity: 0.7;'>No trades executed yet</p>"
    
    trade_html += """
            </div>
        </div>
    </div>
    {% endblock %}
    """
    
    return render_template_string(BASE_TEMPLATE + trade_html)

@app.route('/logs')
def logs_page():
    """Activity logs page"""
    logs_html = f"""
    {{% extends "base" %}}
    {{% block content %}}
    <h1>📜 Activity Logs</h1>
    
    <div class="card">
        <h3>Recent Activity ({len(activity_logs)} total entries)</h3>
        <div class="logs-container">
    """
    
    for log in reversed(activity_logs[-100:]):
        logs_html += f'<div class="log-entry">{log}</div>'
    
    if not activity_logs:
        logs_html += "<p style='text-align: center; opacity: 0.7;'>No activity logs yet</p>"
    
    logs_html += """
        </div>
    </div>
    {% endblock %}
    """
    
    return render_template_string(BASE_TEMPLATE + logs_html)

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    client, status = get_binance_client()
    portfolio, total_value, portfolio_status = get_portfolio_data()
    
    return jsonify({
        'connected': client is not None,
        'connection_status': status,
        'testnet_mode': USE_TESTNET,
        'portfolio_value': total_value,
        'assets_count': len(portfolio),
        'total_trades': len(trades_history),
        'logs_count': len(activity_logs),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/refresh')
def refresh_data():
    """Refresh data endpoint"""
    log_activity("Data refresh requested")
    flash('Data refreshed successfully', 'success')
    return redirect(url_for('dashboard'))

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8501))
    log_activity(f"🚀 Pure Flask Trading Bot starting on port {port}")
    log_activity(f"Mode: {'Testnet' if USE_TESTNET else 'Live Trading'}")
    
    app.run(host='0.0.0.0', port=port, debug=False)