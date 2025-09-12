"""Compatibility shim for legacy deployments.

This module exposes the FastAPI `app` object from the working deployment script.
"""

# Import from our working deployment script instead
from deploy_ready import app

__all__ = ["app"]

