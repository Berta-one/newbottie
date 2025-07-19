#!/usr/bin/env python3
"""
Flask wrapper for Streamlit bot
Fixes Railway deployment issues
"""

import os
import subprocess
import threading
import time
from flask import Flask, render_template_string, redirect

app = Flask(__name__)

# HTML template for the landing page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🤖 Crypto Trading Bot</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
        }
        .container { 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 40px 20px;
        }
        .btn { 
            display: inline-block; 
            padding: 15px 30px; 
            margin: 10px; 
            background: #ff6b6b; 
            color: white; 
            text-decoration: none; 
            border-radius: 25px; 
            font-size: 18px;
            transition: all 0.3s ease;
        }
        .btn:hover { 
            background: #ff5252; 
            transform: translateY(-2px);
        }
        .status { 
            background: rgba(255,255,255,0.1); 
            padding: 20px; 
            border-radius: 15px; 
            margin: 20px 0;
        }
        h1 { font-size: 3em; margin-bottom: 20px; }
        .features { text-align: left; margin: 20px auto; max-width: 600px; }
        .feature { margin: 10px 0; padding: 10px; background: rgba(255,255,255,0.1); border-radius: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Crypto Trading Bot</h1>
        <p style="font-size: 1.2em;">Advanced Multi-Pair Cryptocurrency Trading System</p>
        
        <div class="status">
            <h3>🚀 System Status</h3>
            <p>✅ Railway Deployment: <strong>ACTIVE</strong></p>
            <p>🔗 API Connection: <strong>READY</strong></p>
            <p>🧪 Mode: <strong>{{ mode }}</strong></p>
        </div>
        
        <div class="features">
            <h3>📊 Features</h3>
            <div class="feature">✋ <strong>Manual Trading</strong> - Execute trades on any crypto pair</div>
            <div class="feature">🤖 <strong>Auto-Trading</strong> - Automated multi-pair scanning</div>
            <div class="feature">📈 <strong>Portfolio Tracking</strong> - Real-time balance monitoring</div>
            <div class="feature">📊 <strong>Analytics Dashboard</strong> - Performance metrics and charts</div>
            <div class="feature">🛡️ <strong>Risk Management</strong> - Advanced position sizing</div>
        </div>
        
        <a href="/dashboard" class="btn">🎯 Launch Trading Dashboard</a>
        <a href="/api/status" class="btn">📊 API Status</a>
        
        <div style="margin-top: 40px; font-size: 0.9em; opacity: 0.8;">
            <p>⚠️ This bot is for educational purposes. Trade responsibly.</p>
            <p>🔒 Your API keys are secure and never logged.</p>
        </div>
    </div>
</body>
</html>
"""

STREAMLIT_PROCESS = None

def start_streamlit():
    """Start Streamlit in background"""
    global STREAMLIT_PROCESS
    
    # Remove problematic environment variable
    if 'STREAMLIT_SERVER_PORT' in os.environ:
        del os.environ['STREAMLIT_SERVER_PORT']
    
    try:
        STREAMLIT_PROCESS = subprocess.Popen([
            'streamlit', 'run', 'hybrid_bot.py',
            '--server.port=8502',  # Different port than Flask
            '--server.address=0.0.0.0',
            '--server.headless=true'
        ])
        print("✅ Streamlit started on port 8502")
    except Exception as e:
        print(f"❌ Failed to start Streamlit: {e}")

@app.route('/')
def home():
    """Landing page"""
    mode = "TESTNET" if os.getenv('USE_TESTNET', 'true').lower() == 'true' else "LIVE"
    return render_template_string(HTML_TEMPLATE, mode=mode)

@app.route('/dashboard')
def dashboard():
    """Redirect to Streamlit dashboard"""
    # Start Streamlit if not running
    if STREAMLIT_PROCESS is None:
        start_streamlit()
        time.sleep(3)  # Wait for Streamlit to start
    
    # Redirect to Streamlit (assuming same domain, different port)
    return redirect(f"http://{os.getenv('RAILWAY_PUBLIC_DOMAIN', 'localhost')}:8502")

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    status = {
        'api_configured': bool(api_key and api_secret),
        'testnet_mode': os.getenv('USE_TESTNET', 'true').lower() == 'true',
        'streamlit_running': STREAMLIT_PROCESS is not None,
        'timestamp': time.time()
    }
    
    return status

@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'healthy', 'timestamp': time.time()}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8501))
    
    # Start Streamlit in background
    threading.Thread(target=start_streamlit, daemon=True).start()
    
    print(f"🚀 Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)