"""Compatibility shim for legacy deployments.

This module exposes the FastAPI `app` object from the absolute minimal script.
"""

# Import from our absolute minimal script that works
from absolute_minimal import app

__all__ = ["app"]

