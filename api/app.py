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
        "positions": {},
        "signals": [],
        "time": time.time()
    }

@app.get("/grid/matrix")
def grid_matrix():
    return {
        "grid": [],
        "symbols": [],
        "timestamp": time.time(),
        "status": "emergency_mode"
    }

@app.get("/signals")
def signals():
    return []

@app.get("/sentiment/articles")
def sentiment_articles():
    return {
        "articles": [],
        "source": "emergency",
        "timestamp": time.time()
    }

@app.get("/trades")
def trades():
    return []

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

@app.post("/auth/login")
def auth_login():
    return {
        "access_token": "emergency-token",
        "token_type": "bearer",
        "username": "admin",
        "role": "admin"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
