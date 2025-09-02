# api/admin.py
"""FastAPI admin router for model training and status monitoring."""

import asyncio
import html
import json
import os
import time
from typing import Any, Dict, Optional, Set

from fastapi import APIRouter, HTTPException, Header, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

router = APIRouter()

# ── Security ──────────────────────────────────────────────────────────────────
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "").strip()

def _ok_token(header_val: Optional[str], fallback: Optional[str]) -> bool:
    token = ADMIN_TOKEN
    if not token:
        return False
    if header_val:
        hv = header_val.strip()
        if hv.lower().startswith("bearer "):
            hv = hv[7:].strip()
        if hv == token:
            return True
    if fallback and fallback.strip() == token:
        return True
    return False

# ── Defaults (overridable via env or request) ─────────────────────────────────
DEFAULTS = {
    "symbols": os.getenv("TRAIN_SYMBOLS", os.getenv("TRADE_SYMBOLS", "BTC/USDT,ETH/USDT,BNB/USDT,ADA/USDT")),
    "timeframe": os.getenv("TRAIN_TIMEFRAME", "1h"),
    "bars": int(os.getenv("TRAIN_BARS", "2000")),
    "label_horizon": int(os.getenv("LABEL_HORIZON", "12")),
    "label_threshold_bps": int(float(os.getenv("LABEL_THRESHOLD_BP", "15"))),
    "val_split": float(os.getenv("VAL_SPLIT", "0.2")),
    "rate_limit_sleep": float(os.getenv("RATE_LIMIT_SLEEP", "0.8")),
    "thresh_target": os.getenv("THRESH_TARGET", "f1"),
    "model_out": os.getenv("MODEL_XGB_PATH", "models/xgb_model.pkl"),
    "model_meta": os.getenv("MODEL_META_PATH", "models/xgb_meta.json"),
}

# ── Automation knobs ──────────────────────────────────────────────────────────
ML_AUTO_TRAIN         = os.getenv("ML_AUTO_TRAIN", "0").lower() in ("1","true","yes")
ML_TRAIN_EVERY_HOURS  = float(os.getenv("ML_TRAIN_EVERY_HOURS", "12"))
ML_TRAIN_AT_START     = os.getenv("ML_TRAIN_AT_START", "1").lower() in ("1","true","yes")
ML_WS_BUFFER          = int(os.getenv("ML_WS_BUFFER", "500"))

# ── WS hub & training state ───────────────────────────────────────────────────
_WS_CLIENTS: Set[WebSocket] = set()
_TRAINING_LOCK = asyncio.Lock()
_TRAINING_RUNNING = False

async def _ws_broadcast(msg: Dict[str, Any]) -> None:
    dead = []
    data = json.dumps(msg, ensure_ascii=False)
    for ws in list(_WS_CLIENTS):
        try:
            await ws.send_text(data)
        except Exception:
            dead.append(ws)
    for d in dead:
        try: _WS_CLIENTS.remove(d)
        except: pass

def _normalize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(DEFAULTS)
    if not payload:
        return out
    mapping = {
        "symbols": "symbols",
        "timeframe": "timeframe",
        "bars": "bars",
        "label_horizon": "label_horizon",
        "label_threshold_bps": "label_threshold_bps",
        "val_split": "val_split",
        "rate_limit_sleep": "rate_limit_sleep",
        "thresh_target": "thresh_target",
        "model_out": "model_out",
        "model_meta": "model_meta",
    }
    for k, v in payload.items():
        if k not in mapping: 
            continue
        key = mapping[k]
        if key in ("bars","label_horizon","label_threshold_bps"):
            try: out[key] = int(v)
            except: pass
        elif key in ("val_split","rate_limit_sleep"):
            try: out[key] = float(v)
            except: pass
        else:
            out[key] = str(v)
    return out

async def _run_trainer(cfg: Dict[str, Any]) -> None:
    """
    Launch scripts/train_from_exchange.py with env overrides; stream stdout
    to WebSocket clients as JSON lines.
    """
    global _TRAINING_RUNNING
    if _TRAINING_RUNNING:
        await _ws_broadcast({"type": "train/status", "status": "busy"})
        return

    async with _TRAINING_LOCK:
        if _TRAINING_RUNNING:
            return
        _TRAINING_RUNNING = True

    try:
        os.makedirs("models", exist_ok=True)

        env_parts = [
            f'TRAIN_SYMBOLS="{cfg["symbols"]}"',
            f'TRAIN_TIMEFRAME="{cfg["timeframe"]}"',
            f'TRAIN_BARS={int(cfg["bars"])}',
            f'LABEL_HORIZON={int(cfg["label_horizon"])}',
            f'LABEL_THRESHOLD_BP={int(cfg["label_threshold_bps"])}',
            f'VAL_SPLIT={float(cfg["val_split"])}',
            f'RATE_LIMIT_SLEEP={float(cfg["rate_limit_sleep"])}',
            f'THRESH_TARGET="{cfg["thresh_target"]}"',
            f'MODEL_OUT="{cfg["model_out"]}"',
            f'MODEL_META="{cfg["model_meta"]}"',
        ]
        cmd = " ".join(env_parts) + " python scripts/train_from_exchange.py"
        await _ws_broadcast({"type":"train/start", "cmd": cmd, "cfg": cfg, "ts": time.time()})

        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )

        # stream output
        buf = []
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            s = line.decode("utf-8", "ignore").rstrip()
            buf.append(s)
            if len(buf) >= 5:
                await _ws_broadcast({"type":"train/log", "lines": buf})
                buf = []
        if buf:
            await _ws_broadcast({"type":"train/log", "lines": buf})

        code = await proc.wait()
        await _ws_broadcast({"type":"train/end", "code": code, "ts": time.time()})

        # Opportunistic: tell clients to refresh /ml/status
        await _ws_broadcast({"type":"ml/refresh"})

    except Exception as e:
        await _ws_broadcast({"type":"train/error", "error": str(e)})
    finally:
        _TRAINING_RUNNING = False

# ── HTTP Admin UI (optional, still no-console) ────────────────────────────────
@router.get("/admin/ui", response_class=HTMLResponse)
def admin_ui() -> HTMLResponse:
    d = DEFAULTS
    return HTMLResponse(f"""
<!doctype html><meta charset="utf-8"/>
<title>Bottie Admin</title>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<style>
 body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;max-width:920px;margin:auto;padding:16px}}
 label{{display:block;margin-top:10px;font-weight:600}}
 input,select,button{{width:100%;padding:10px;margin-top:6px}}
 .row{{display:grid;gap:12px;grid-template-columns:1fr 1fr}}
 .card{{border:1px solid #ddd;border-radius:8px;padding:14px;margin-top:14px}}
 pre{{background:#0b1020;color:#cfe3ff;border-radius:8px;padding:10px;white-space:pre-wrap}}
 .btn{{background:#1f6feb;color:#fff;border:0;border-radius:8px;cursor:pointer}}
</style>
<h1>🤖 Bottie Admin</h1>
<div class="card">
  <label>Admin Token</label>
  <input id="token" type="password" placeholder="Paste ADMIN_TOKEN"/>
  <div class="row">
    <div><label>Symbols</label><input id="symbols" value="{html.escape(d['symbols'])}"></div>
    <div><label>Timeframe</label><input id="timeframe" value="{html.escape(d['timeframe'])}"></div>
  </div>
  <div class="row">
    <div><label>Bars</label><input id="bars" type="number" value="{int(d['bars'])}"></div>
    <div><label>Label Horizon</label><input id="label_horizon" type="number" value="{int(d['label_horizon'])}"></div>
  </div>
  <div class="row">
    <div><label>Label Threshold (bps)</label><input id="label_threshold_bps" type="number" value="{int(d['label_threshold_bps'])}"></div>
    <div><label>Val Split</label><input id="val_split" type="number" step="0.05" value="{float(d['val_split'])}"></div>
  </div>
  <div class="row">
    <div><label>Rate Limit Sleep</label><input id="rate_limit_sleep" type="number" step="0.1" value="{float(d['rate_limit_sleep'])}"></div>
    <div><label>Threshold Target</label>
      <select id="thresh_target">
        <option value="f1" {"selected" if d["thresh_target"].lower()=="f1" else ""}>F1</option>
        <option value="youden" {"selected" if d["thresh_target"].lower()=="youden" else ""}>Youden</option>
        <option value="precision@recall>=0.60">Precision@Recall≥0.60</option>
      </select>
    </div>
  </div>
  <button id="btnConnect" class="btn">Connect WebSocket</button>
  <button id="btnTrain" class="btn">Train Now (WS)</button>
  <pre id="out"></pre>
</div>
<script>
let ws = null;
const $ = id => document.getElementById(id);
$("btnConnect").onclick = () => {{
  const token = $("token").value;
  if (!token) return $("out").textContent = "Please paste ADMIN_TOKEN first.";
  const proto = location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(proto + "://" + location.host + "/ws/admin");
  ws.onopen = () => {{
    ws.send(JSON.stringify({{type:"auth", token}}));
    $("out").textContent = "WS connected. Auth sent…";
  }};
  ws.onmessage = (ev) => {{
    try {{
      const msg = JSON.parse(ev.data);
      $("out").textContent += "\\n" + JSON.stringify(msg);
    }} catch (e) {{
      $("out").textContent += "\\n" + ev.data;
    }}
  }};
  ws.onclose = () => {{ $("out").textContent += "\\nWS closed"; }};
}};
$("btnTrain").onclick = () => {{
  if (!ws || ws.readyState !== 1) return $("out").textContent += "\\nWS not connected.";
  const payload = {{
    type: "train",
    symbols: $("symbols").value,
    timeframe: $("timeframe").value,
    bars: parseInt($("bars").value||"2000"),
    label_horizon: parseInt($("label_horizon").value||"12"),
    label_threshold_bps: parseInt($("label_threshold_bps").value||"15"),
    val_split: parseFloat($("val_split").value||"0.2"),
    rate_limit_sleep: parseFloat($("rate_limit_sleep").value||"0.8"),
    thresh_target: $("thresh_target").value
  }};
  ws.send(JSON.stringify(payload));
}};
</script>
""")

# ── Simple status for current model files ─────────────────────────────────────
@router.get("/ml/status")
def ml_status() -> Dict[str, Any]:
    model_path = DEFAULTS["model_out"]
    meta_path  = DEFAULTS["model_meta"]
    meta = {}
    exists_model = os.path.exists(model_path)
    exists_meta  = os.path.exists(meta_path)
    if exists_meta:
        try:
            with open(meta_path, "r") as f:
                meta = json.load(f)
        except Exception as e:
            meta = {"error": f"meta_read_failed: {e}"}
    return {
        "model_path": model_path,
        "meta_path": meta_path,
        "model_exists": exists_model,
        "meta_exists": exists_meta,
        "meta": meta,
    }

# ── POST fallback (non-WS) ───────────────────────────────────────────────────
@router.post("/admin/train")
async def trigger_train(
    request: Request, authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    token_from_body = (payload or {}).get("token")
    if not _ok_token(authorization, token_from_body):
        raise HTTPException(status_code=401, detail="Unauthorized")

    cfg = _normalize_payload(payload or {})
    asyncio.create_task(_run_trainer(cfg))
    return {"accepted": True, "cfg": cfg, "ts": time.time()}

# ── WebSocket admin channel ──────────────────────────────────────────────────
@router.websocket("/ws/admin")
async def ws_admin(ws: WebSocket) -> None:
    await ws.accept()
    authed = False
    _WS_CLIENTS.add(ws)
    try:
        # first message must be auth
        first = await ws.receive_text()
        try:
            m = json.loads(first)
        except Exception:
            await ws.close(code=1008)
            return
        if m.get("type") != "auth" or not _ok_token(m.get("token"), None):
            await ws.send_text(json.dumps({"type":"auth","ok":False}))
            await ws.close(code=1008)
            return
        authed = True
        await ws.send_text(json.dumps({"type":"auth","ok":True}))

        # messages loop
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except Exception:
                continue
            if msg.get("type") == "train":
                cfg = _normalize_payload(msg)
                asyncio.create_task(_run_trainer(cfg))
                await ws.send_text(json.dumps({"type":"train/accepted","cfg":cfg}))
            else:
                await ws.send_text(json.dumps({"type":"warn","msg":"unknown action"}))
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await ws.send_text(json.dumps({"type":"error","msg":str(e)}))
        except Exception:
            pass
    finally:
        try: _WS_CLIENTS.remove(ws)
        except: pass

# ── Scheduler: first-boot & periodic auto-train ──────────────────────────────
async def _auto_train_scheduler() -> None:
    """
    If enabled:
      - run once at startup if model missing (or ML_TRAIN_AT_START=1)
      - then loop every ML_TRAIN_EVERY_HOURS hours
    """
    await asyncio.sleep(3.0)  # let the app boot
    cfg = dict(DEFAULTS)

    def model_missing():
        return not os.path.exists(cfg["model_out"]) or not os.path.exists(cfg["model_meta"])

    if ML_AUTO_TRAIN and (ML_TRAIN_AT_START or model_missing()):
        await _ws_broadcast({"type":"auto/train", "reason":"startup"})
        await _run_trainer(cfg)

    if ML_AUTO_TRAIN and ML_TRAIN_EVERY_HOURS > 0:
        interval = max(1.0, ML_TRAIN_EVERY_HOURS) * 3600.0
        while True:
            await asyncio.sleep(interval)
            await _ws_broadcast({"type":"auto/train", "reason":"interval"})
            await _run_trainer(cfg)

def wire_admin_startup(app: Any) -> None:
    """
    Call this from your app.py startup to activate auto-train scheduler.
    """
    if ML_AUTO_TRAIN or ML_TRAIN_AT_START:
        loop = asyncio.get_event_loop()
        loop.create_task(_auto_train_scheduler())
