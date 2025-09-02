"""Compatibility shim for legacy deployments.

This module exposes the FastAPI `app` object from `api.app` so that
older `uvicorn` start commands referencing `api_real_integrated:app`
continue to work.
"""

from api.app import app

__all__ = ["app"]

