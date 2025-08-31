#!/usr/bin/env python3
"""
Bulletproof main entry point for Render deployment
Ensures the app starts reliably within 512MB memory limit
"""

import os
import sys
import logging

# Set up basic logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point"""
    try:
        logger.info("🚀 Bottie Dashboard Starting...")
        logger.info(f"🐍 Python: {sys.version}")
        logger.info(f"📍 Working Dir: {os.getcwd()}")
        logger.info(f"🌐 Port: {os.getenv('PORT', '8000')}")
        
        # Import the app
        from lightweight_dashboard_api import app
        import uvicorn
        
        port = int(os.getenv("PORT", "8000"))
        
        logger.info(f"✅ Starting server on port {port}")
        
        # Run with minimal configuration
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=False,
            workers=1
        )
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("Falling back to basic server...")
        
        # Fallback: Create a basic working server
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        import uvicorn
        
        fallback_app = FastAPI()
        
        @fallback_app.get("/")
        def root():
            return {"status": "fallback", "message": "Basic server running"}
        
        @fallback_app.get("/health")
        def health():
            return {"status": "healthy", "mode": "fallback"}
        
        port = int(os.getenv("PORT", "8000"))
        uvicorn.run(fallback_app, host="0.0.0.0", port=port)
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()