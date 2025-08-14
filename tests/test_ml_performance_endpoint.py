import os
import sys
from fastapi.testclient import TestClient

# Ensure the repository root is on sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import api.app as app_module


def test_ml_performance_endpoint_returns_200():
    # Disable exchange initialization during tests
    app_module.EXCHANGE_AVAILABLE = False
    with TestClient(app_module.app) as client:
        response = client.get("/ml/performance")
    assert response.status_code == 200
    body = response.json()
    assert "history" in body
    assert isinstance(body["history"], list)
