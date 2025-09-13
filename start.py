#!/usr/bin/env python3
"""
Simple startup script for Render deployment
Ensures the correct application starts regardless of configuration
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main startup function"""
    try:
        logger.info("🚨 Starting Emergency Stable System...")
        
        # Use emergency system that always works
        from emergency_fix import app
        import uvicorn
        
        port = int(os.getenv("PORT", "8000"))
        host = os.getenv("HOST", "0.0.0.0")
        
        logger.info(f"🌐 Starting server on {host}:{port}")
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()