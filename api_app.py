from fastapi import FastAPI
import time

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}  # instead of the current {"ok": true, "service": ..., "time": ...}