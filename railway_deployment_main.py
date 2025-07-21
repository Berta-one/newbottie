#!/usr/bin/env python3
"""
Railway Deployment Main Entry Point
==================================

This file serves as the main entry point for Railway deployment while
preserving all your existing bot logic in hybrid_bot.py, main.py, etc.

Usage: Railway will start this file, which then runs your existing system.
"""

import os
import sys
import time
import threading
import subprocess
import signal
import json
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RailwayBot:
    """Main Railway deployment handler"""
    
    def __init__(self):
        self.process = None
        self.start_time = datetime.now()
        self.running = False
        
    def setup_environment(self):
        """Setup environment and directories"""
        try:
            # Create necessary directories
            for dir_name in ['logs', 'models', 'data']:
                Path(dir_name).mkdir(exist_ok=True)
                logger.info(f"✅ Created directory: {dir_name}")
            
            # Set environment variables
            os.environ['PYTHONPATH'] = '/app'
            os.environ['TZ'] = 'UTC'
            
            # Get Railway port
            port = os.environ.get('PORT', '8501')
            logger.info(f"🚀 Railway port: {port}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            return False
    
    def start_streamlit(self):
        """Start Streamlit application"""
        try:
            port = os.environ.get('PORT', '8501')
            
            # Streamlit command for Railway
            cmd = [
                'streamlit', 'run', 'hybrid_bot.py',
                '--server.port', str(port),
                '--server.address', '0.0.0.0',
                '--server.headless', 'true',
                '--server.enableCORS', 'false',
                '--server.enableXsrfProtection', 'false',
                '--server.enableWebsocketCompression', 'true'
            ]
            
            logger.info(f"🎯 Starting Streamlit: {' '.join(cmd)}")
            
            # Start process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Log output
            def log_output():
                if self.process:
                    for line in iter(self.process.stdout.readline, ''):
                        if line:
                            logger.info(f"STREAMLIT: {line.rstrip()}")
            
            # Start logging thread
            log_thread = threading.Thread(target=log_output, daemon=True)
            log_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start Streamlit: {e}")
            return False
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"🛑 Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)
    
    def shutdown(self):
        """Graceful shutdown"""
        self.running = False
        if self.process:
            logger.info("🔄 Terminating Streamlit process...")
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning("⚠️ Force killing process...")
                self.process.kill()
    
    def health_check(self):
        """Check application health"""
        try:
            if self.process and self.process.poll() is None:
                uptime = (datetime.now() - self.start_time).total_seconds()
                return {
                    'status': 'healthy',
                    'uptime_seconds': uptime,
                    'process_id': self.process.pid if self.process else None,
                    'timestamp': datetime.now().isoformat(),
                    'platform': 'Railway'
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': 'Process not running',
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def run(self):
        """Main run method"""
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        logger.info("🚀 Starting Railway Crypto Trading Bot...")
        
        # Setup environment
        if not self.setup_environment():
            sys.exit(1)
        
        # Start Streamlit
        if not self.start_streamlit():
            sys.exit(1)
        
        logger.info("✅ Bot started successfully on Railway!")
        
        # Keep alive and monitor
        try:
            while self.running:
                if self.process and self.process.poll() is not None:
                    logger.error("❌ Streamlit process died, restarting...")
                    if not self.start_streamlit():
                        logger.error("❌ Failed to restart, exiting...")
                        break
                
                time.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            logger.info("🛑 Keyboard interrupt received")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
        finally:
            self.shutdown()

def main():
    """Entry point for Railway"""
    try:
        # Log startup
        logger.info("=" * 50)
        logger.info("🚀 RAILWAY CRYPTO BOT STARTING")
        logger.info("=" * 50)
        
        # Check for required files
        required_files = ['hybrid_bot.py', 'requirements.txt']
        missing_files = [f for f in required_files if not os.path.exists(f)]
        
        if missing_files:
            logger.error(f"❌ Missing required files: {missing_files}")
            sys.exit(1)
        
        # Start the bot
        bot = RailwayBot()
        bot.run()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
