import uuid
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_system_audit_events():
    res = client.get("/api/v1/system/audit-events?limit=10&offset=0")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)

def test_settings_get_and_patch():
    # GET settings
    get_res = client.get("/api/v1/settings")
    assert get_res.status_code == 200
    data = get_res.json()
    assert "base_currency" in data
    assert "market_data_provider" in data

    # PATCH settings
    patch_res = client.patch("/api/v1/settings", json={
        "timezone": "UTC",
        "stale_price_days": 14,
        "invalid_key_should_reject": "ignored"
    })
    assert patch_res.status_code == 200
    patch_data = patch_res.json()
    assert patch_data["updated"]["timezone"] == "UTC"
    assert patch_data["updated"]["stale_price_days"] == "14"
    assert "invalid_key_should_reject" in patch_data["rejected"]

def test_instruments_endpoints():
    sym = f"TEST_{uuid.uuid4().hex[:6].upper()}"
    # Create instrument
    create_res = client.post("/api/v1/instruments", json={
        "canonical_symbol": sym,
        "display_name": "Test Integration Asset",
        "asset_type": "equity",
        "quote_currency": "INR",
        "sector": "Technology"
    })
    assert create_res.status_code == 201
    inst_data = create_res.json()
    assert inst_data["canonical_symbol"] == sym
    inst_id = inst_data["id"]

    # Conflict on duplicate
    dup_res = client.post("/api/v1/instruments", json={
        "canonical_symbol": sym,
        "display_name": "Duplicate Asset",
        "asset_type": "equity"
    })
    assert dup_res.status_code == 409

    # Get by ID
    get_res = client.get(f"/api/v1/instruments/{inst_id}")
    assert get_res.status_code == 200
    assert get_res.json()["canonical_symbol"] == sym

    # List instruments with search
    list_res = client.get(f"/api/v1/instruments?search={sym}")
    assert list_res.status_code == 200
    results = list_res.json()
    assert any(x["canonical_symbol"] == sym for x in results)

def test_reports_income_and_data_quality():
    # Income JSON
    inc_res = client.get("/api/v1/reports/income?format=json")
    assert inc_res.status_code == 200
    inc_data = inc_res.json()
    assert inc_data["report_name"] == "Cash Flows & Income Summary"
    assert "summary" in inc_data

    # Income CSV
    inc_csv = client.get("/api/v1/reports/income?format=csv")
    assert inc_csv.status_code == 200
    assert "text/csv" in inc_csv.headers["content-type"]
    assert "Income & Cash Flows Report" in inc_csv.text

    # Data Quality JSON
    dq_res = client.get("/api/v1/reports/data-quality?format=json")
    assert dq_res.status_code == 200
    dq_data = dq_res.json()
    assert dq_data["report_name"] == "Data Quality & Integrity Report"
    assert "total_issues" in dq_data

    # Data Quality CSV
    dq_csv = client.get("/api/v1/reports/data-quality?format=csv")
    assert dq_csv.status_code == 200
    assert "text/csv" in dq_csv.headers["content-type"]
    assert "Data Quality & Integrity Report" in dq_csv.text
