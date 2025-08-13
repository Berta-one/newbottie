#!/usr/bin/env python3
"""
Emergency simplified API for Bottie - basic functionality only
"""

import os
import time
from typing import Dict, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Simple app with essential endpoints only
app = FastAPI(title="Bottie API (Emergency Mode)", version="2.0.0")

# Very permissive CORS for debugging
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "service": "bottie-emergency", "time": time.time()}

@app.get("/health")
def health():
    return {
        "status": "UP",
        "ok": True,
        "service": "bottie-emergency",
        "time": int(time.time()),
        "exchange": "binance",
        "primary_quote": "USDT",
        "equity": 10000.0,
        "quantum": {"enabled": False},
        "ml": {"enabled": False, "loaded": False},
        "sentiment": {"enabled": False}
    }

@app.get("/status")
def status():
    return {
        "ok": True,
        "equity": 10000.0,
        "positions": {
            "BTCUSDT": {"quantity": 0.025, "entry_price": 45180.0, "pnl": 1.25},
            "ETHUSDT": {"quantity": -1.5, "entry_price": 2895.50, "pnl": -2.10}
        },
        "signals": ["BUY BTCUSDT", "HOLD ETHUSDT"],
        "time": time.time(),
        "total_pnl": -0.85,
        "active_trades": 2
    }

@app.get("/grid/matrix")
def grid_matrix():
    # Sample grid data for demo purposes
    sample_grid = [
        {"symbol": "BTCUSDT", "price": 45230.50, "change": 2.3, "volume": 1200000, "confidence": 0.75},
        {"symbol": "ETHUSDT", "price": 2890.75, "change": -1.2, "volume": 850000, "confidence": 0.68},
        {"symbol": "ADAUSDT", "price": 0.485, "change": 3.1, "volume": 45000000, "confidence": 0.82},
        {"symbol": "DOTUSDT", "price": 7.23, "change": 0.8, "volume": 12000000, "confidence": 0.71}
    ]
    return {
        "grid": sample_grid,
        "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT"],
        "timestamp": time.time(),
        "status": "emergency_mode",
        "min_conf": 0.0
    }

@app.get("/signals")
def signals():
    # Sample trading signals for demo
    sample_signals = [
        {
            "symbol": "BTCUSDT",
            "signal": "BUY",
            "confidence": 0.78,
            "price": 45230.50,
            "timestamp": time.time() - 300,
            "reason": "Golden cross detected"
        },
        {
            "symbol": "ETHUSDT", 
            "signal": "HOLD",
            "confidence": 0.65,
            "price": 2890.75,
            "timestamp": time.time() - 180,
            "reason": "Consolidation phase"
        }
    ]
    return sample_signals

@app.get("/sentiment/articles")
def sentiment_articles():
    # Sample sentiment data for demo
    sample_articles = [
        {
            "title": "Bitcoin breaks resistance at $45k",
            "sentiment": 0.72,
            "source": "CryptoNews",
            "timestamp": time.time() - 1800,
            "impact": "positive"
        },
        {
            "title": "Ethereum network upgrade shows promise",
            "sentiment": 0.65,
            "source": "BlockTech",
            "timestamp": time.time() - 3600,
            "impact": "positive"
        }
    ]
    return {
        "articles": sample_articles,
        "source": "emergency",
        "timestamp": time.time(),
        "overall_sentiment": 0.68
    }

@app.get("/trades")
def trades():
    # Sample recent trades for demo
    sample_trades = [
        {
            "id": "1001",
            "symbol": "BTCUSDT",
            "side": "BUY",
            "quantity": 0.025,
            "price": 45180.0,
            "timestamp": time.time() - 3600,
            "pnl": 1.25,
            "status": "FILLED"
        },
        {
            "id": "1002", 
            "symbol": "ETHUSDT",
            "side": "SELL",
            "quantity": 1.5,
            "price": 2895.50,
            "timestamp": time.time() - 7200,
            "pnl": -2.10,
            "status": "FILLED"
        }
    ]
    return sample_trades

@app.get("/logs/last")
def logs_last():
    return {
        "logs": ["Emergency mode active - basic endpoints only"],
        "timestamp": time.time()
    }

@app.get("/ml/status")
def ml_status():
    return {
        "enabled": False,
        "loaded": False,
        "model_path": None,
        "performance": {}
    }

@app.get("/quantum/details")
def quantum_details():
    return {
        "enabled": False,
        "backend": "emergency",
        "circuits": {}
    }

@app.get("/quantum/analysis")
def quantum_analysis():
    return {
        "enabled": False,
        "analysis": {}
    }

@app.get("/performance/analysis")
def performance_analysis():
    return {
        "timeframe": "24h",
        "metrics": {},
        "brier_score": 0.5
    }

# Debug endpoints for frontend compatibility
@app.get("/debug/auth")
def debug_auth():
    return {
        "auth_available": True,
        "default_user": "admin",
        "status": "emergency_mode_active"
    }

@app.post("/debug/test-login")
def debug_test_login(request: dict):
    return {
        "success": True,
        "message": "Debug login successful",
        "user": {"username": "admin", "role": "admin"},
        "access_token": "debug-token-12345"
    }

@app.post("/debug/reset-passwords")
def debug_reset_passwords(request: dict):
    return {
        "success": True,
        "message": "Passwords reset in debug mode",
        "admin_password": "Diego1234!"
    }

@app.post("/auth/login")
def auth_login(request: dict):
    username = request.get("username", "")
    password = request.get("password", "")
    
    if username == "admin" and password == "Diego1234!":
        return {
            "access_token": "emergency-auth-token",
            "token_type": "bearer",
            "username": "admin",
            "role": "admin"
        }
    else:
        return {"error": "Invalid credentials"}, 401

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
