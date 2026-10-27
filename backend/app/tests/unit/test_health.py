from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_basic_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["local_only"] is True

def test_system_health():
    res = client.get("/api/v1/system/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["database_connected"] is True
    assert data["local_first_enforced"] is True

def test_dashboard_endpoint():
    res = client.get("/api/v1/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "total_portfolio_value" in data or "portfolio_value" in data
