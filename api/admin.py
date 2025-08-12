# api/admin.py
import os, asyncio, shlex, time
from typing import Optional
from fastapi import APIRouter, HTTPException, Header

router = APIRouter()

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

def _ok_token(token: Optional[str]) -> bool:
    if not ADMIN_TOKEN:
        return False
    # Accept either "Bearer <token>" or raw token
    if not token:
        return False
    token = token.strip()
    return token == ADMIN_TOKEN or token.replace("Bearer ", "") == ADMIN_TOKEN

@router.post("/train")
async def trigger_train(authorization: Optional[str] = Header(None)):
    if not _ok_token(authorization):
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Ensure paths exist
    os.makedirs("models", exist_ok=True)
    os.makedirs("scripts", exist_ok=True)

    cmd = "python scripts/train_from_exchange.py"
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    # Read a few lines immediately for feedback
    started = time.time()
    lines = []
    try:
        for _ in range(20):  # ~first chunk
            line = await asyncio.wait_for(proc.stdout.readline(), timeout=2.0)
            if not line:
                break
            lines.append(line.decode("utf-8", "ignore").rstrip())
    except asyncio.TimeoutError:
        pass

    return {
        "pid": proc.pid,
        "started_at": started,
        "stdout_preview": lines[-10:]
    }