#!/usr/bin/env python3
"""
Pure Flask Crypto Trading Bot Dashboard
Railway-compatible without Streamlit issues
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, redirect, url_for
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Try to import Binance
try:
    from binance.client import Client
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False

# Configuration
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')
USE_TESTNET = os.getenv('USE_TESTNET', 'true').lower() == 'true'

# In-memory storage (you could use a database in production)
trades = []
logs = []

def log_message(message):
    """Add log message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    logs.append(log_entry)
    if len(logs) > 100:
        logs.pop(0)

def get_binance_client():
    """Get Binance client"""
    if not BINANCE_AVAILABLE or not API_KEY or not API_SECRET:
        return None
    
    try:
        client = Client(API_KEY, API_SECRET)
        if USE_TESTNET:
            client.API_URL = 'https://testnet.binance.vision/api'
        return client
    except:
        return None

# HTML Templates
MAIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🤖 Crypto Trading Bot</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; min-height: 100vh;
        }
        .navbar { 
            background: rgba(0,0,0,0.3); padding: 1rem; display: flex; 
            justify-content: space-between; align-items: center;
        }
        .nav-links { display: flex; gap: 1rem; }
        .nav-links a { 
            color: white; text-decoration: none; padding: 0.5rem 1rem; 
            border-radius: 5px; transition: background 0.3s;
        }
        .nav-links a:hover { background: rgba(255,255,255,0.2); }
        .nav-links a.active { background: rgba(255,255,255,0.3); }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }
        .card { 
            background: rgba(255,255,255,0.1); border-radius: 15px; 
            padding: 1.5rem; backdrop-filter: blur(10px);
        }
        .metric { text-align: center; }
        .metric h3 { font-size: 2rem; margin-bottom: 0.5rem; }
        .metric p { opacity: 0.8; }
        .btn { 
            background: #ff6b6b; color: white; border: none; 
            padding: 0.75rem 1.5rem; border-radius: 25px; 
            cursor: pointer; font-size: 1rem; transition: all 0.3s;
        }
        .btn:hover { background: #ff5252; transform: translateY(-2px); }
        .btn-secondary { background: #4ecdc4; }
        .btn-secondary:hover { background: #45b7b8; }
        .form-group { margin-bottom: 1rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; }
        .form-group input, .form-group select { 
            width: 100%; padding: 0.75rem; border: none; 
            border-radius: 8px; font-size: 1rem;
        }
        .status { 
            display: inline-block; padding: 0.25rem 0.75rem; 
            border-radius: 15px; font-size: 0.875rem;
        }
        .status.connected { background: #2ecc71; }
        .status.disconnected { background: #e74c3c; }
        .log-container { 
            background: rgba(0,0,0,0.3); padding: 1rem; 
            border-radius: 8px; max-height: 300px; overflow-y: auto;
        }
        .log-entry { font-family: monospace; font-size: 0.875rem; margin-bottom: 0.25rem; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 0.75rem; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }
        th { background: rgba(255,255,255,0.1); }
    </style>
</head>
<body>
    <nav class="navbar">
        <h1>🤖 Crypto Trading Bot</h1>
        <div class="nav-links">
            <a href="/" class="{{ 'active' if page == 'dashboard' else '' }}">🏠 Dashboard</a>
            <a href="/portfolio" class="{{ 'active' if page == 'portfolio' else '' }}">📊 Portfolio</a>
            <a href="/trade" class="{{ 'active' if page == 'trade' else '' }}">✋ Trade</a>
            <a href="/logs" class="{{ 'active' if page == 'logs' else '' }}">📜 Logs</a>
        </div>
    </nav>
    
    <div class="container">
        {% block content %}{% endblock %}
    </div>
    
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
"""

DASHBOARD_CONTENT = """
{% extends "base" %}
{% block content %}
<div style="text-align: center; margin-bottom: 2rem;">
    <h2>Trading Dashboard</h2>
    <span class="status {{ 'connected' if connected else 'disconnected' }}">
        {{ '✅ Connected' if connected else '❌ Disconnected' }}
    </span>
    <span class="status" style="background: #f39c12; margin-left: 1rem;">
        🧪 {{ 'Testnet' if testnet else 'Live' }} Mode
    </span>
</div>

<div class="grid">
    <div class="card metric">
        <h3>${{ balance }}</h3>
        <p>Portfolio Value</p>
    </div>
    <div class="card metric">
        <h3>{{ trades_count }}</h3>
        <p>Total Trades</p>
    </div>
    <div class="card metric">
        <h3>{{ assets_count }}</h3>
        <p>Assets Held</p>
    </div>
    <div class="card metric">
        <h3>{{ 'ON' if auto_trading else 'OFF' }}</h3>
        <p>Auto Trading</p>
    </div>
</div>

<div class="grid" style="margin-top: 2rem;">
    <div class="card">
        <h3>⚡ Quick Actions</h3>
        <div style="display: flex; gap: 1rem; margin-top: 1rem;">
            <button class="btn" onclick="location.href='/trade'">📈 Manual Trade</button>
            <button class="btn btn-secondary" onclick="location.href='/portfolio'">📊 View Portfolio</button>
        </div>
    </div>
    
    <div class="card">
        <h3>📊 System Status</h3>
        <p>🔗 API: {{ 'Connected' if connected else 'Disconnected' }}</p>
        <p>⏰ Last Update: {{ timestamp }}</p>
        <p>🖥️ Server: Railway</p>
    </div>
</div>
{% endblock %}
"""

@app.route('/')
def dashboard():
    """Main dashboard"""
    client = get_binance_client()
    connected = client is not None
    
    # Get basic info
    balance = "0.00"
    assets_count = 0
    
    if connected:
        try:
            account = client.get_account()
            balances = [b for b in account['balances'] if float(b['free']) > 0 or float(b['locked']) > 0]
            assets_count = len(balances)
            
            # Calculate total USDT value (simplified)
            usdt_balance = next((float(b['free']) for b in balances if b['asset'] == 'USDT'), 0)
            balance = f"{usdt_balance:.2f}"
            
        except Exception as e:
            log_message(f"Error fetching account: {e}")
    
    data = {
        'page': 'dashboard',
        'connected': connected,
        'testnet': USE_TESTNET,
        'balance': balance,
        'trades_count': len(trades),
        'assets_count': assets_count,
        'auto_trading': False,  # Placeholder
        'timestamp': datetime.now().strftime("%H:%M:%S")
    }
    
    return render_template_string(MAIN_TEMPLATE.replace('{% block content %}{% endblock %}', DASHBOARD_CONTENT), **data)

@app.route('/portfolio')
def portfolio():
    """Portfolio page"""
    client = get_binance_client()
    
    portfolio_html = """
    <h2>📊 Portfolio Overview</h2>
    """
    
    if client:
        try:
            account = client.get_account()
            balances = [b for b in account['balances'] if float(b['free']) > 0 or float(b['locked']) > 0]
            
            portfolio_html += f"""
            <div class="card">
                <h3>💰 Holdings ({len(balances)} assets)</h3>
                <table>
                    <tr><th>Asset</th><th>Free</th><th>Locked</th><th>Total</th></tr>
            """
            
            for balance in balances:
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                portfolio_html += f"""
                <tr>
                    <td>{balance['asset']}</td>
                    <td>{free:.6f}</td>
                    <td>{locked:.6f}</td>
                    <td>{total:.6f}</td>
                </tr>
                """
            
            portfolio_html += "</table></div>"
            
        except Exception as e:
            portfolio_html += f"<div class='card'><p>❌ Error: {e}</p></div>"
    else:
        portfolio_html += "<div class='card'><p>❌ No API connection</p></div>"
    
    return render_template_string(MAIN_TEMPLATE.replace('{% block content %}{% endblock %}', portfolio_html), page='portfolio')

@app.route('/trade', methods=['GET', 'POST'])
def trade():
    """Trading page"""
    if request.method == 'POST':
        # Handle trade execution
        symbol = request.form.get('symbol')
        side = request.form.get('side')
        amount = float(request.form.get('amount', 0))
        
        client = get_binance_client()
        if client and amount > 0:
            try:
                # Simplified trade execution
                log_message(f"Trade simulation: {side} {symbol} ${amount}")
                trades.append({
                    'timestamp': datetime.now().isoformat(),
                    'symbol': symbol,
                    'side': side,
                    'amount': amount,
                    'status': 'SIMULATED'
                })
                return redirect(url_for('trade'))
            except Exception as e:
                log_message(f"Trade error: {e}")
    
    trade_html = """
    <h2>✋ Manual Trading</h2>
    <div class="grid">
        <div class="card">
            <h3>📈 Execute Trade</h3>
            <form method="POST">
                <div class="form-group">
                    <label>Trading Pair</label>
                    <select name="symbol">
                        <option>BTCUSDT</option>
                        <option>ETHUSDT</option>
                        <option>BNBUSDT</option>
                        <option>ADAUSDT</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Order Type</label>
                    <select name="side">
                        <option value="BUY">BUY</option>
                        <option value="SELL">SELL</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Amount (USDT)</label>
                    <input type="number" name="amount" min="10" step="0.01" value="50">
                </div>
                <button type="submit" class="btn">🚀 Execute Trade</button>
            </form>
        </div>
        
        <div class="card">
            <h3>📋 Recent Trades</h3>
            <div style="max-height: 300px; overflow-y: auto;">
    """
    
    for trade in trades[-10:]:
        trade_html += f"""
        <div style="padding: 0.5rem; border-bottom: 1px solid rgba(255,255,255,0.1);">
            <strong>{trade['symbol']}</strong> - {trade['side']} ${trade['amount']}<br>
            <small>{trade['timestamp'][:19]} - {trade['status']}</small>
        </div>
        """
    
    trade_html += """
            </div>
        </div>
    </div>
    """
    
    return render_template_string(MAIN_TEMPLATE.replace('{% block content %}{% endblock %}', trade_html), page='trade')

@app.route('/logs')
def logs_page():
    """Logs page"""
    logs_html = f"""
    <h2>📜 Activity Logs</h2>
    <div class="card">
        <h3>Recent Activity ({len(logs)} entries)</h3>
        <div class="log-container">
    """
    
    for log in logs[-50:]:
        logs_html += f'<div class="log-entry">{log}</div>'
    
    logs_html += """
        </div>
    </div>
    """
    
    return render_template_string(MAIN_TEMPLATE.replace('{% block content %}{% endblock %}', logs_html), page='logs')

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    client = get_binance_client()
    return jsonify({
        'connected': client is not None,
        'testnet': USE_TESTNET,
        'trades': len(trades),
        'logs': len(logs),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health():
    """Health check"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8501))
    log_message("🚀 Flask Trading Bot started")
    app.run(host='0.0.0.0', port=port, debug=False)