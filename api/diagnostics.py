from pathlib import Path

from fastapi import APIRouter

router = APIRouter()


@router.get("/__version")
def version():
    """Expose the deployed commit version (from VERSION file)."""
    p = Path("/app/VERSION")
    return {"version": p.read_text().strip() if p.exists() else "unknown"}
