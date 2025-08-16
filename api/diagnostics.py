from fastapi import APIRouter
from pathlib import Path

router = APIRouter()

@router.get("/__version")
def version():
    """Expose the deployed commit version (from VERSION file)."""
    p = Path("/app/VERSION")
    return {"version": p.read_text().strip() if p.exists() else "unknown"}