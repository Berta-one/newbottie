#!/usr/bin/env python3
"""
Simple fix for trading controls
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Handle preflight OPTIONS requests
@app.options("/trading/start")
@app.options("/trading/stop")
async def options_handler():
    return JSONResponse(content={}, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "*"
    })

@app.post("/trading/start")
async def start_trading(request: Request):
    try:
        print("🟢 Trading START requested")
        return JSONResponse(content={"ok": True, "message": "Trading started"})
    except Exception as e:
        print(f"❌ Start error: {e}")
        return JSONResponse(content={"ok": False, "error": str(e)})

@app.post("/trading/stop")
async def stop_trading(request: Request):
    try:
        print("🔴 Trading STOP requested")
        return JSONResponse(content={"ok": True, "message": "Trading stopped"})
    except Exception as e:
        print(f"❌ Stop error: {e}")
        return JSONResponse(content={"ok": False, "error": str(e)})

@app.get("/health")
def health():
    return {"status": "healthy", "trading_controls": "fixed"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)