#!/usr/bin/env python3
"""
Railway Quantum Bot Integration
===============================

Integrates autonomous quantum bot with Railway deployment.
Runs both the dashboard and autonomous bot simultaneously.
"""

import os
import sys
import subprocess
import threading
import time
import signal
from datetime import datetime

class RailwayQuantumManager:
    """Manages both dashboard and autonomous bot on Railway"""
    
    def __init__(self):
        self.dashboard_process = None
        self.quantum_bot_process = None
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"🛑 Received signal {signum}, shutting down...")
        self.running = False
        self.stop_all_processes()
        sys.exit(0)
    
    def start_dashboard(self):
        """Start the Streamlit dashboard"""
        try:
            port = os.getenv('PORT', '8501')
            cmd = [
                'streamlit', 'run', 'hybrid_bot.py',
                '--server.port', port,
                '--server.address', '0.0.0.0',
                '--server.headless', 'true',
                '--server.enableCORS', 'false',
                '--server.enableXsrfProtection', 'false'
            ]
            
            print(f"🖥️ Starting dashboard on port {port}")
            self.dashboard_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start dashboard: {e}")
            return False
    
    def start_quantum_bot(self):
        """Start the autonomous quantum bot"""
        try:
            # Only start if auto-trading is enabled
            if os.getenv('AUTO_TRADE_ENABLED', 'false').lower() == 'true':
                print("🤖 Starting autonomous quantum bot")
                self.quantum_bot_process = subprocess.Popen(
                    ['python', 'autonomous_quantum_bot.py'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                return True
            else:
                print("⏸️ Autonomous bot disabled (AUTO_TRADE_ENABLED=false)")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start quantum bot: {e}")
            return False
    
    def monitor_processes(self):
        """Monitor both processes and restart if needed"""
        while self.running:
            try:
                # Check dashboard
                if self.dashboard_process and self.dashboard_process.poll() is not None:
                    print("⚠️ Dashboard process died, restarting...")
                    self.start_dashboard()
                
                # Check quantum bot
                if self.quantum_bot_process and self.quantum_bot_process.poll() is not None:
                    print("⚠️ Quantum bot process died, restarting...")
                    self.start_quantum_bot()
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(60)
    
    def stop_all_processes(self):
        """Stop all running processes"""
        if self.dashboard_process:
            try:
                self.dashboard_process.terminate()
                self.dashboard_process.wait(timeout=10)
                print("✅ Dashboard stopped")
            except:
                self.dashboard_process.kill()
        
        if self.quantum_bot_process:
            try:
                self.quantum_bot_process.terminate()
                self.quantum_bot_process.wait(timeout=10)
                print("✅ Quantum bot stopped")
            except:
                self.quantum_bot_process.kill()
    
    def run(self):
        """Main run method"""
        print("🚀 Railway Quantum Manager starting...")
        
        # Start dashboard
        if not self.start_dashboard():
            print("❌ Failed to start dashboard")
            return
        
        # Start quantum bot (if enabled)
        self.start_quantum_bot()
        
        # Start monitoring in background
        monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
        monitor_thread.start()
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("🛑 Shutdown requested")
            self.running = False
        finally:
            self.stop_all_processes()

def main():
    """Main function"""
    print("🌐 Railway Quantum Bot Manager")
    print(f"Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'local')}")
    print(f"Port: {os.getenv('PORT', '8501')}")
    print(f"Auto-trade: {os.getenv('AUTO_TRADE_ENABLED', 'false')}")
    
    manager = RailwayQuantumManager()
    manager.run()

if __name__ == "__main__":
    main()
