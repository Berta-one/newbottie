# api/routes_grid.py
from fastapi import APIRouter, Query
from typing import Any, Dict
import time

router = APIRouter()
CROSS_WS = None # set by app.py

@router.get("/grid/matrix")
def grid_matrix(min_conf: float = Query(0.0, ge=0.0, le=1.0)) -> Dict[str, Any]:
    """Return matrix; frontend will apply min_conf client-side, but we expose it for future server filtering."""
    if not CROSS_WS:
        return {"rows": [], "cols": [], "matrix": {}, "ts": int(time.time()), "min_conf": float(min_conf)}
    snap = CROSS_WS.snapshot_matrix()
    snap["min_conf"] = float(min_conf)
    return snap

@router.get("/portfolio/assets")
def portfolio_assets() -> Dict[str, Any]:
    if not CROSS_WS:
        return {"assets": []}
    return {"assets": CROSS_WS.rows}

@router.get("/scan/assets")
def scan_assets() -> Dict[str, Any]:
    if not CROSS_WS:
        return {"assets": []}
    return {"assets": CROSS_WS.cols}
