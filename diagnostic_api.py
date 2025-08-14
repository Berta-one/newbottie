#!/usr/bin/env python3
"""
Diagnostic API to check what's wrong with Render deployment
"""

import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Bottie Diagnostic API", version="1.0.0")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "bottie-diagnostic",
        "time": time.time(),
        "message": "Diagnostic API is running"
    }

@app.get("/health")
def health():
    return {
        "status": "UP",
        "service": "bottie-diagnostic",
        "time": int(time.time())
    }

@app.get("/status")
def status():
    """Diagnostic status endpoint"""
    try:
        # Check environment variables
        env_vars = {
            "ENVIRONMENT": os.getenv('ENVIRONMENT', 'NOT_SET'),
            "TRADE_ENABLED": os.getenv('TRADE_ENABLED', 'NOT_SET'),
            "PORT": os.getenv('PORT', 'NOT_SET'),
            "BINANCE_API_KEY_LENGTH": len(os.getenv('BINANCE_API_KEY', '')) if os.getenv('BINANCE_API_KEY') else 0,
            "BINANCE_API_SECRET_LENGTH": len(os.getenv('BINANCE_API_SECRET', '')) if os.getenv('BINANCE_API_SECRET') else 0
        }
        
        # Check dependencies
        dependencies = {}
        try:
            import ccxt
            dependencies["ccxt"] = "✅ Available"
        except Exception as e:
            dependencies["ccxt"] = f"❌ Error: {e}"
            
        try:
            import pandas
            dependencies["pandas"] = "✅ Available"
        except Exception as e:
            dependencies["pandas"] = f"❌ Error: {e}"
            
        try:
            import numpy
            dependencies["numpy"] = "✅ Available"
        except Exception as e:
            dependencies["numpy"] = f"❌ Error: {e}"
        
        return {
            "ok": True,
            "service": "bottie-diagnostic",
            "time": time.time(),
            "environment_variables": env_vars,
            "dependencies": dependencies,
            "diagnostic": "All systems check"
        }
        
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "time": time.time(),
            "service": "bottie-diagnostic"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
