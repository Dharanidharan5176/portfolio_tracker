import os
import shutil
import tempfile
import uuid
from datetime import date
from decimal import Decimal
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_complete_end_to_end_smoke_lifecycle():
    # 1. Check system health
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "healthy"

    # 2. Create Portfolio
    unique_name = f"Smoke Test Portfolio {uuid.uuid4().hex[:6]}"
    p_res = client.post("/api/v1/portfolios", json={
        "name": unique_name,
        "base_currency": "INR",
        "timezone": "Asia/Kolkata"
    })
    assert p_res.status_code == 201
    portfolio = p_res.json()
    p_id = portfolio["id"]

    # 3. Get Account
    accs_res = client.get(f"/api/v1/accounts?portfolio_id={p_id}")
    assert accs_res.status_code == 200
    acc_id = accs_res.json()[0]["id"]

    # 4. Deposit Cash: 50,000 INR
    dep_res = client.post("/api/v1/transactions", json={
        "portfolio_id": p_id,
        "account_id": acc_id,
        "type": "CASH_DEPOSIT",
        "trade_date": "2026-01-01",
        "gross_amount": "50000.00",
        "currency": "INR"
    })
    assert dep_res.status_code == 201

    # 5. Buy 10 shares of RELIANCE @ 2,500 INR
    buy_res = client.post("/api/v1/transactions", json={
        "portfolio_id": p_id,
        "account_id": acc_id,
        "symbol": "RELIANCE",
        "type": "BUY",
        "trade_date": "2026-01-02",
        "quantity": "10.0",
        "unit_price": "2500.00",
        "fee": "25.00",
        "tax": "0.00",
        "currency": "INR"
    })
    assert buy_res.status_code == 201
    tx_buy = buy_res.json()
    inst_id = tx_buy["instrument_id"]

    # 6. Record manual price observation @ 2,800 INR
    price_res = client.post("/api/v1/holdings/prices", json={
        "instrument_id": inst_id,
        "observed_at": "2026-01-05T15:30:00Z",
        "price": "2800.00",
        "currency": "INR",
        "notes": "Closing price test"
    })
    assert price_res.status_code == 201

    # 7. Check Holdings
    holdings_res = client.get(f"/api/v1/holdings?portfolio_id={p_id}")
    assert holdings_res.status_code == 200
    holdings = holdings_res.json()
    assert len(holdings) == 1
    h = holdings[0]
    assert h["symbol"] == "RELIANCE"
    assert h["quantity"] == "10.0000"
    assert h["market_value"] == "28000.00"
    assert h["cost_basis"] == "25025.00"
    assert h["unrealized_pnl"] == "2975.00"

    # 8. Check Dashboard
    dash_res = client.get(f"/api/v1/dashboard?portfolio_id={p_id}")
    assert dash_res.status_code == 200
    dash = dash_res.json()
    assert dash["portfolio_id"] == p_id
    assert Decimal(dash["total_portfolio_value"]) > Decimal("0.00")
    assert len(dash["recent_activity"]) >= 2

    # 9. Export Reports
    rep_json = client.get(f"/api/v1/reports/holdings?portfolio_id={p_id}&format=json")
    assert rep_json.status_code == 200
    assert len(rep_json.json()["items"]) == 1

    rep_csv = client.get(f"/api/v1/reports/holdings?portfolio_id={p_id}&format=csv")
    assert rep_csv.status_code == 200
    assert "RELIANCE" in rep_csv.text

    # 10. Create Backup
    backup_res = client.post("/api/v1/backups?label=smoke_test")
    assert backup_res.status_code == 201
    b_data = backup_res.json()
    b_id = b_data["id"]
    assert b_data["status"] == "valid"
    assert os.path.exists(b_data["path"])

    # 11. Restore Verification
    restore_res = client.post(f"/api/v1/backups/{b_id}/restore?confirm=true")
    assert restore_res.status_code == 200
    assert restore_res.json()["status"] == "success"

    # Verify data after restore
    dash_post_restore = client.get(f"/api/v1/dashboard?portfolio_id={p_id}").json()
    assert dash_post_restore["portfolio_id"] == p_id
    assert dash_post_restore["holdings"][0]["symbol"] == "RELIANCE"
