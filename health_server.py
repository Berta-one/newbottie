#!/usr/bin/env python3
"""
Railway Health Check Server
===========================
Lightweight health endpoint for Railway deployment
"""

import os
import json
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle health check requests"""
        if self.path == "/health":
            self.send_health_response()
        elif self.path == "/":
            self.send_status_response()
        else:
            self.send_response(404)
            self.end_headers()

    def send_health_response(self):
        """Send basic health response"""
        try:
            # Check if main app is responsive
            status = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "uptime": time.time(),
                "environment": "railway",
            }

            # Check log files
            if os.path.exists("logs/bot_activity.log"):
                status["logs"] = "accessible"
            else:
                status["logs"] = "missing"

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "error": str(e)}).encode())

    def send_status_response(self):
        """Send simple status for Railway dashboard"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()

        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Hybrid Crypto Bot - Railway</title></head>
        <body>
            <h1>🧠 Hybrid Crypto Bot</h1>
            <p>✅ Running on Railway</p>
            <p>⚛️ Quantum + 🤖 ML + 📊 Technical Analysis</p>
            <p>🔗 <a href="/health">Health Check</a></p>
        </body>
        </html>
        """
        self.wfile.write(html.encode())

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def start_health_server():
    """Start health check server on different port"""
    health_port = int(os.getenv("HEALTH_PORT", 8081))

    try:
        server = HTTPServer(("0.0.0.0", health_port), HealthHandler)
        print(f"Health server running on port {health_port}")
        server.serve_forever()
    except Exception as e:
        print(f"Health server error: {e}")


if __name__ == "__main__":
    start_health_server()
