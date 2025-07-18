# railway_deployment_main.py - Main Railway entry point
"""
Railway Deployment Main Entry Point
==================================

This file serves as the main entry point for Railway deployment while
preserving all your existing bot logic in hybrid_bot.py, main.py, etc.

It combines:
- Your existing hybrid_bot.py (Streamlit dashboard)
- Always-on background functionality
- Health endpoints for Railway
- Keep-alive systems

Usage: Railway will start this file, which then runs your existing system.
"""

import os
import sys
import time
import threading
import subprocess
import signal
import json
import requests
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Add current directory to path so we can import your existing modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

class RailwayHealthHandler(BaseHTTPRequestHandler):
    """HTTP handler for Railway health checks and keep-alive"""
    
    def do_GET(self):
        try:
            if self.path in ['/health', '/ping', '/status']:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                # Get bot status
                status = self.get_bot_status()
                self.wfile.write(json.dumps(status).encode())
                
            elif self.path == '/':
                # Redirect to main app
                self.send_response(302)
                self.send_header('Location', f'http://localhost:{os.getenv("PORT", 8501)}')
                self.end_headers()
                
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Not Found')
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f'Server Error: {str(e)}'.encode())
    
    def get_bot_status(self):
        """Get current bot status"""
        try:
            # Try to read bot status from your existing logs
            if os.path.exists('logs/bot_status.json'):
                with open('logs/bot_status.json', 'r') as f:
                    status = json.load(f)
            else:
                status = {}
            
            # Add Railway-specific status
            status.update({
                'railway_status': 'alive',
                'timestamp': datetime.now().isoformat(),
                'uptime_seconds': (datetime.now() - start_time).total_seconds() if 'start_time' in globals() else 0,
                'version': '2.0.0',
                'platform': 'Railway',
                'main_process': 'hybrid_bot.py',
                'health_endpoint': 'active'
            })
            
            return status
            
        except Exception as e:
            return {
                'railway_status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'platform': 'Railway'
            }
    
    def log_message(self, format, *args):
        # Suppress HTTP access logs
        pass

class RailwayKeepAliveSystem:
    """Keep-alive system for Railway deployment"""
    
    def __init__(self):
        self.running = False
        self.heartbeat_count = 0
        self.start_time = datetime.now()
        
    def start_keepalive(self):
        """Start all keep-alive mechanisms"""
        if not self.running:
            self.running = True
            
            # Start heartbeat thread
            heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
            heartbeat_thread.start()
            
            # Start activity thread
            activity_thread = threading.Thread(target=self.activity_loop, daemon=True)
            activity_thread.start()
            
            print("💓 Railway keep-alive system started")
    
    def heartbeat_loop(self):
        """Continuous heartbeat logging"""
        while self.running:
            try:
                self.heartbeat_count += 1
                uptime = (datetime.now() - self.start_time).total_seconds()
                
                print(f"💓 Railway Heartbeat #{self.heartbeat_count} - Uptime: {uptime:.0f}s")
                
                # Save heartbeat to your existing logs structure
                os.makedirs('logs', exist_ok=True)
                heartbeat_data = {
                    'timestamp': datetime.now().isoformat(),
                    'heartbeat_count': self.heartbeat_count,
                    'uptime_seconds': uptime,
                    'status': 'alive',
                    'platform': 'Railway'
                }
                
                with open('logs/railway_heartbeat.json', 'w') as f:
                    json.dump(heartbeat_data, f)
                
                time.sleep(300)  # Every 5 minutes
                
            except Exception as e:
                print(f"Heartbeat error: {e}")
                time.sleep(60)
    
    def activity_loop(self):
        """Generate activity to prevent Railway sleep"""
        while self.running:
            try:
                # Write activity file
                activity_file = f'logs/railway_activity_{datetime.now().strftime("%Y%m%d")}.log'
                with open(activity_file, 'a') as f:
                    f.write(f"{datetime.now().isoformat()}: Railway bot active\n")
                
                # CPU activity to prevent sleep
                dummy = sum(i * i for i in range(1000))
                
                time.sleep(180)  # Every 3 minutes
                
            except Exception as e:
                print(f"Activity error: {e}")
                time.sleep(120)
    
    def stop_keepalive(self):
        """Stop keep-alive system"""
        self.running = False
        print("🛑 Railway keep-alive system stopped")

class RailwayBotManager:
    """Main bot manager for Railway deployment"""
    
    def __init__(self):
        self.bot_process = None
        self.health_server = None
        self.keepalive_system = RailwayKeepAliveSystem()
        self.running = False
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n🛑 Received shutdown signal ({signum})")
        self.graceful_shutdown()
        sys.exit(0)
    
    def start_health_server(self):
        """Start HTTP health server for Railway"""
        try:
            port = int(os.getenv('PORT', 8501))
            
            def run_health_server():
                # Start health server on a different port to avoid conflict with Streamlit
                health_port = port + 1000  # Use a different port for health checks
                try:
                    server = HTTPServer(('0.0.0.0', health_port), RailwayHealthHandler)
                    self.health_server = server
                    print(f"💓 Railway health server started on port {health_port}")
                    server.serve_forever()
                except Exception as e:
                    print(f"Health server error: {e}")
            
            health_thread = threading.Thread(target=run_health_server, daemon=True)
            health_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Failed to start health server: {e}")
            return False
    
    def start_main_bot(self):
        """Start your existing hybrid_bot.py"""
        try:
            # Get Railway port
            port = os.getenv('PORT', '8501')
            
            # Start your existing hybrid_bot.py with Streamlit
            cmd = [
                sys.executable, '-m', 'streamlit', 'run',
                'hybrid_bot.py',
                '--server.port', port,
                '--server.address', '0.0.0.0',
                '--server.headless', 'true',
                '--server.enableCORS', 'false',
                '--server.enableXsrfProtection', 'false'
            ]
            
            print(f"🚀 Starting main bot: {' '.join(cmd)}")
            
            self.bot_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            print(f"✅ Main bot started with PID: {self.bot_process.pid}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start main bot: {e}")
            return False
    
    def monitor_main_bot(self):
        """Monitor your main bot process"""
        restart_count = 0
        max_restarts = 10
        
        while self.running:
            try:
                if self.bot_process:
                    # Check if process is still running
                    poll_result = self.bot_process.poll()
                    
                    if poll_result is not None:
                        # Process has terminated
                        print(f"⚠️ Main bot process terminated with code: {poll_result}")
                        
                        if restart_count < max_restarts:
                            restart_count += 1
                            print(f"🔄 Restarting main bot (attempt {restart_count}/{max_restarts})")
                            
                            time.sleep(10)  # Wait before restart
                            
                            if self.start_main_bot():
                                print("✅ Main bot restarted successfully")
                            else:
                                print("❌ Failed to restart main bot")
                        else:
                            print("❌ Maximum restart attempts reached. Stopping.")
                            break
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(60)
    
    def run_forever(self):
        """Main run loop for Railway"""
        global start_time
        start_time = datetime.now()
        
        try:
            self.running = True
            
            print("🚀 Railway Bot Manager Starting...")
            print(f"Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'unknown')}")
            print(f"Port: {os.getenv('PORT', '8501')}")
            
            # Ensure logs directory exists
            os.makedirs('logs', exist_ok=True)
            
            # Start keep-alive system
            self.keepalive_system.start_keepalive()
            
            # Start health server (optional - Streamlit will handle main traffic)
            # self.start_health_server()
            
            # Start your main bot
            if not self.start_main_bot():
                print("❌ Failed to start main bot. Exiting.")
                return
            
            # Monitor the main bot
            monitor_thread = threading.Thread(target=self.monitor_main_bot, daemon=True)
            monitor_thread.start()
            
            print("✅ All systems started successfully")
            
            # Main loop - keep the process alive
            while self.running:
                try:
                    time.sleep(60)
                    
                    # Log periodic status
                    uptime = (datetime.now() - start_time).total_seconds()
                    if uptime % 3600 < 60:  # Every hour
                        print(f"📊 Railway status: Running for {uptime/3600:.1f} hours")
                    
                except KeyboardInterrupt:
                    print("Keyboard interrupt received")
                    break
                except Exception as e:
                    print(f"Main loop error: {e}")
                    time.sleep(60)
        
        except Exception as e:
            print(f"Fatal error in run_forever: {e}")
        
        finally:
            self.graceful_shutdown()
    
    def graceful_shutdown(self):
        """Gracefully shutdown all systems"""
        print("🛑 Initiating graceful shutdown...")
        self.running = False
        
        # Stop keep-alive system
        self.keepalive_system.stop_keepalive()
        
        # Stop main bot process
        if self.bot_process:
            try:
                print("Terminating main bot process...")
                self.bot_process.terminate()
                self.bot_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print("Force killing main bot process...")
                self.bot_process.kill()
            except Exception as e:
                print(f"Error stopping main bot: {e}")
        
        # Stop health server
        if self.health_server:
            try:
                self.health_server.shutdown()
            except:
                pass
        
        uptime = (datetime.now() - start_time).total_seconds() if 'start_time' in globals() else 0
        print(f"✅ Railway bot stopped after {uptime:.0f} seconds")

def main():
    """Main entry point for Railway"""
    print("🎯 Railway Crypto Trading Bot Deployment Manager")
    print("=" * 60)
    
    # Validate environment
    required_env = ['BINANCE_API_KEY', 'BINANCE_API_SECRET']
    missing_env = [var for var in required_env if not os.getenv(var)]
    
    if missing_env:
        print(f"⚠️ Warning: Missing environment variables: {missing_env}")
        print("Set these in Railway environment variables for full functionality.")
    
    # Start the bot manager
    bot_manager = RailwayBotManager()
    bot_manager.run_forever()

if __name__ == "__main__":
    main()
