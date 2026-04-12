#!/usr/bin/env python3
"""
Smoke tests for api.routes_grid (aligned with current router surface).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.update(
    {
        "TRADE_CONF_FLOOR": "0.40",
        "TRADE_CONF_CEIL": "0.85",
        "GRID_MAX_COLS": "80",
        "EMA_WEIGHT": "0.4",
        "ML_WEIGHT": "0.3",
        "ML_ENABLED": "1",
        "QUANTUM_ENABLED": "0",
        "SENTIMENT_ENABLED": "1",
    }
)


def test_api_routes():
    from api.routes_grid import grid_matrix, portfolio_assets, scan_assets

    result = grid_matrix()
    assert "rows" in result and "cols" in result and "matrix" in result
    assert result["rows"] == [] and result["cols"] == []

    assert portfolio_assets() == {"assets": []}
    assert scan_assets() == {"assets": []}
