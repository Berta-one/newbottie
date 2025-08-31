#!/usr/bin/env python3
"""
Simple startup script for Bottie Lightweight Dashboard
Fixes Render crashes by using the working lightweight_dashboard_api.py directly
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point - simply run the lightweight dashboard"""
    try:
        logger.info("🚀 Starting Bottie Lightweight Dashboard")
        logger.info(f"📍 Working Directory: {os.getcwd()}")
        logger.info(f"🌐 Port: {os.getenv('PORT', '8000')}")
        logger.info(f"💾 Memory Limit: {os.getenv('MAX_MEMORY_MB', '400')}MB")
        logger.info(f"🎭 Demo Mode: {os.getenv('DEMO_MODE', '1')}")
        
        # Import and run the lightweight dashboard
        from lightweight_dashboard_api import app
        import uvicorn
        
        port = int(os.getenv("PORT", "8000"))
        
        logger.info("✅ Starting uvicorn server...")
        
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=port,
            log_level="info",
            access_log=False,  # Save memory
            workers=1
        )
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()