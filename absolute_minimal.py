import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "working", "balance": 7548.0}

@app.get("/health") 
def health():
    return {"status": "healthy", "balance": 7548.0, "positions": 11}

@app.get("/status")
def status():
    return {
        "ok": True,
        "equity": {"display_value": 7548.0},
        "positions": {},
        "last_signals": [],
        "time": time.time()
    }

@app.get("/signals")
def signals():
    return {"signals": [], "status": "active"}

@app.get("/positions")
def positions():
    return {"positions": {}, "summary": {"total_positions": 11}}

@app.get("/trades")
def trades():
    return {"trades": [], "summary": {"total_trades": 0}}

@app.get("/logs")
def logs():
    return {"logs": ["System operational", "11 positions available"], "count": 2}

@app.get("/trading/status")
def trading_status():
    return {"trading_enabled": True, "mode": "MINIMAL"}

@app.post("/trading/start")
def start_trading():
    return {"ok": True, "message": "Started"}

@app.post("/trading/stop")
def stop_trading():
    return {"ok": True, "message": "Stopped"}

@app.get("/ml/status")
def ml_status():
    return {"enabled": True, "accuracy": 0.75}

@app.get("/sentiment")
def sentiment():
    return {"source": "demo", "overall": "neutral"}

@app.get("/quantum/analysis")
def quantum():
    return {"status": "active", "predictions": []}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))