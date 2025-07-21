#!/usr/bin/env python3
"""
Flask Dashboard for Bottie
Features:
- Real-time logs using Flask-SocketIO + Redis
- Bot control (Start/Stop)
- Portfolio & Trade interface
Author: Rondanini Publishing Ltd
"""

import os
import subprocess
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, flash
from flask_socketio import SocketIO
from dotenv import load_dotenv
import psutil

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ✅ SocketIO for real-time updates (Redis as message queue)
socketio = SocketIO(app, cors_allowed_origins="*", message_queue='redis://')

BOT_SCRIPT = "bot_service.py"

# ✅ Check if bot is running
def is_bot_running():
    for proc in psutil.process_iter(['cmdline']):
        if BOT_SCRIPT in ' '.join(proc.info['cmdline']):
            return True
    return False

# ✅ Bot control routes
@app.route('/bot/start')
def start_bot():
    if not is_bot_running():
        subprocess.Popen(["python", BOT_SCRIPT])
        flash("✅ Bot started!", "success")
    else:
        flash("Bot is already running.", "info")
    return redirect(url_for('dashboard'))

@app.route('/bot/stop')
def stop_bot():
    if is_bot_running():
        os.system(f"pkill -f {BOT_SCRIPT}")
        flash("🛑 Bot stopped.", "warning")
    else:
        flash("Bot is not running.", "info")
    return redirect(url_for('dashboard'))

# ✅ WebSocket namespace
@socketio.on('connect', namespace='/logs')
def logs_connect():
    print("Client connected to logs namespace")

# ✅ Dashboard Template
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 Bottie Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; background: #111; color: #fff; margin: 0; padding: 0; }
        .navbar { background: #222; padding: 10px; display: flex; justify-content: space-between; }
        .navbar a { color: #fff; margin: 0 10px; text-decoration: none; }
        .container { padding: 20px; }
        .btn { padding: 10px 15px; border-radius: 5px; text-decoration: none; font-weight: bold; }
        .btn-start { background: #28a745; color: #fff; }
        .btn-stop { background: #dc3545; color: #fff; }
        #logs { background:#000; color:#0f0; height:300px; overflow:auto; padding:10px; font-family:monospace; }
    </style>
</head>
<body>
    <div class="navbar">
        <div><strong>🤖 Bottie Dashboard</strong></div>
        <div>
            <a href="/">Dashboard</a>
            <a href="/bot/start" class="btn btn-start">Start Bot</a>
            <a href="/bot/stop" class="btn btn-stop">Stop Bot</a>
        </div>
    </div>
    <div class="container">
        {% block content %}{% endblock %}
        <h3>📜 Live Logs</h3>
        <div id="logs"><p>Waiting for logs...</p></div>
    </div>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + '/logs');
        socket.on('log_update', function(data) {
            var logDiv = document.getElementById('logs');
            var newLog = document.createElement('div');
            newLog.textContent = data.log;
            logDiv.appendChild(newLog);
            logDiv.scrollTop = logDiv.scrollHeight;
        });
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    bot_status = "🟢 Running" if is_bot_running() else "🔴 Stopped"
    content = f"""
    {% extends "base" %}
    {% block content %}
    <h1>Bottie Dashboard</h1>
    <p><strong>Bot Status:</strong> {bot_status}</p>
    {% endblock %}
    """
    return render_template_string(BASE_TEMPLATE + content)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    print("🚀 Starting Flask-SocketIO server...")
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)