# api/admin.py
import os, asyncio, json, time, html
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Header, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse

router = APIRouter()

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "").strip()

# Defaults (can be overridden by env or per-request form/JSON)
DEFAULTS = {
    "symbols": os.getenv("TRAIN_SYMBOLS", os.getenv("TRADE_SYMBOLS", "BTC/USDT,ETH/USDT,BNB/USDT,ADA/USDT")),
    "timeframe": os.getenv("TRAIN_TIMEFRAME", "1h"),
    "bars": int(os.getenv("TRAIN_BARS", "2000")),
    "label_horizon": int(os.getenv("LABEL_HORIZON", "12")),
    "label_threshold_bps": int(float(os.getenv("LABEL_THRESHOLD_BP", "15"))),  # 15 bps default
    "val_split": float(os.getenv("VAL_SPLIT", "0.2")),
    "rate_limit_sleep": float(os.getenv("RATE_LIMIT_SLEEP", "0.8")),
    "thresh_target": os.getenv("THRESH_TARGET", "f1"),
    "model_out": os.getenv("MODEL_XGB_PATH", "models/xgb_model.pkl"),
    "model_meta": os.getenv("MODEL_META_PATH", "models/xgb_meta.json"),
}

def ok_token(header_val: Optional[str], fallback: Optional[str]) -> bool:
    """
    Accept either Authorization: Bearer <token> or token provided via form/query 'token'.
    """
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

def to_bool(v: Any, default: bool = False) -> bool:
    if v is None: return default
    s = str(v).strip().lower()
    return s not in ("0", "false", "off", "", "none")

def normalize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(DEFAULTS)
    if not payload:
        return out
    # Accept both camel and snake; keep it simple
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
        key = mapping.get(k, None)
        if key is None:
            continue
        if key in ("bars", "label_horizon", "label_threshold_bps"):
            try: out[key] = int(v)
            except: pass
        elif key in ("val_split", "rate_limit_sleep"):
            try: out[key] = float(v)
            except: pass
        else:
            out[key] = str(v)
    return out

@router.get("/ml/status")
def ml_status():
    """Report whether trained files exist and show meta/threshold if available."""
    model_path = DEFAULTS["model_out"]
    meta_path  = DEFAULTS["model_meta"]
    exists_model = os.path.exists(model_path)
    exists_meta  = os.path.exists(meta_path)
    meta = {}
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

@router.get("/admin/ui", response_class=HTMLResponse)
def admin_ui(request: Request):
    """
    A tiny HTML control panel:
    - paste ADMIN_TOKEN
    - set training options
    - click 'Train' and see quick feedback
    """
    d = DEFAULTS
    html_page = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Bottie Admin</title>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; padding: 18px; max-width: 900px; margin: auto; }}
    input, select, button, textarea {{ padding: 10px; font-size: 16px; width: 100%; box-sizing: border-box; margin-top: 6px; }}
    label {{ font-weight: 600; display: block; margin-top: 14px; }}
    .row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
    .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin-top: 16px; }}
    .ok {{ color: #0a7a0a; }} .warn {{ color: #a66a00; }} .bad {{ color: #b00020; }}
    .btn {{ background:#1f6feb; color:#fff; border:0; border-radius:8px; cursor:pointer; }}
    .btn:disabled {{ background:#999; cursor:not-allowed; }}
    code {{ background:#f6f8fa; padding:2px 6px; border-radius:4px; }}
  </style>
</head>
<body>
  <h1>🤖 Bottie Admin</h1>
  <p>Trigger server-side training and check ML status without any console.</p>

  <div class="card">
    <label>Admin Token</label>
    <input id="token" type="password" placeholder="Paste ADMIN_TOKEN here"/>
    <div class="row">
      <div>
        <label>Symbols (comma)</label>
        <input id="symbols" value="{html.escape(d['symbols'])}">
      </div>
      <div>
        <label>Timeframe</label>
        <input id="timeframe" value="{html.escape(d['timeframe'])}">
      </div>
    </div>
    <div class="row">
      <div>
        <label>Bars</label>
        <input id="bars" type="number" value="{int(d['bars'])}">
      </div>
      <div>
        <label>Label Horizon (bars)</label>
        <input id="label_horizon" type="number" value="{int(d['label_horizon'])}">
      </div>
    </div>
    <div class="row">
      <div>
        <label>Label Threshold (bps)</label>
        <input id="label_threshold_bps" type="number" value="{int(d['label_threshold_bps'])}">
      </div>
      <div>
        <label>Val Split</label>
        <input id="val_split" type="number" step="0.05" value="{float(d['val_split'])}">
      </div>
    </div>
    <div class="row">
      <div>
        <label>Rate Limit Sleep (s)</label>
        <input id="rate_limit_sleep" type="number" step="0.1" value="{float(d['rate_limit_sleep'])}">
      </div>
      <div>
        <label>Threshold Target</label>
        <select id="thresh_target">
          <option value="f1" {"selected" if d["thresh_target"].lower()=="f1" else ""}>F1</option>
          <option value="youden" {"selected" if d["thresh_target"].lower()=="youden" else ""}>Youden (TPR-FPR)</option>
          <option value="precision@recall>=0.60">Precision@Recall≥0.60</option>
        </select>
      </div>
    </div>
    <div class="row">
      <div>
        <label>Model Path</label>
        <input id="model_out" value="{html.escape(d['model_out'])}">
      </div>
      <div>
        <label>Meta Path</label>
        <input id="model_meta" value="{html.escape(d['model_meta'])}">
      </div>
    </div>
    <button class="btn" id="btnTrain">Train Now</button>
    <pre id="out" style="white-space:pre-wrap;margin-top:12px;"></pre>
  </div>

  <div class="card" id="mlBox">
    <h3>ML Status</h3>
    <button class="btn" id="btnStatus">Refresh</button>
    <pre id="mlStatus" style="white-space:pre-wrap;margin-top:8px;"></pre>
  </div>

<script>
const $ = (id) => document.getElementById(id);
async function call(url, method, token, body) {{
  const headers = {{"Content-Type":"application/json"}};
  if (token) headers["Authorization"] = "Bearer " + token;
  const res = await fetch(url, {{
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined
  }});
  const txt = await res.text();
  try {{ return {{ ok: res.ok, data: JSON.parse(txt) }}; }} catch(e) {{ return {{ ok: res.ok, data: txt }}; }}
}}
$("btnTrain").onclick = async () => {{
  const payload = {{
    symbols: $("symbols").value,
    timeframe: $("timeframe").value,
    bars: parseInt($("bars").value || "2000"),
    label_horizon: parseInt($("label_horizon").value || "12"),
    label_threshold_bps: parseInt($("label_threshold_bps").value || "15"),
    val_split: parseFloat($("val_split").value || "0.2"),
    rate_limit_sleep: parseFloat($("rate_limit_sleep").value || "0.8"),
    thresh_target: $("thresh_target").value,
    model_out: $("model_out").value,
    model_meta: $("model_meta").value
  }};
  const token = $("token").value;
  $("out").textContent = "Starting training…";
  const res = await call("/admin/train", "POST", token, payload);
  $("out").textContent = JSON.stringify(res.data, null, 2);
}};
$("btnStatus").onclick = async () => {{
  const res = await call("/ml/status", "GET");
  $("mlStatus").textContent = JSON.stringify(res.data, null, 2);
}};
</script>
</body>
</html>
"""
    return HTMLResponse(content=html_page)

@router.post("/admin/train")
async def trigger_train(request: Request, authorization: Optional[str] = Header(None)):
    """
    Start server-side training via POSTed JSON body (from the Admin UI).
    """
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    token_from_body = (payload or {}).get("token")
    if not ok_token(authorization, token_from_body):
        raise HTTPException(status_code=401, detail="Unauthorized")

    cfg = normalize_payload(payload or {})
    os.makedirs("models", exist_ok=True)

    # Build env string overrides for the subprocess (safe & explicit)
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
    # One shell command exporting vars and running the trainer
    cmd = " ".join(env_parts) + " python scripts/train_from_exchange.py"

    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )

    # Stream a short preview so you get immediate feedback
    lines = []
    try:
        for _ in range(24):
            line = await asyncio.wait_for(proc.stdout.readline(), timeout=2.0)
            if not line: break
            lines.append(line.decode("utf-8", "ignore").rstrip())
    except asyncio.TimeoutError:
        pass

    return {
        "pid": proc.pid,
        "started_at": time.time(),
        "cmd": cmd,
        "preview": lines[-12:],
        "hint": "Open /logs/last to follow along; model saved to MODEL_OUT on completion."
    }