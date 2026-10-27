from datetime import date
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_full_portfolio_and_transaction_flow():
    # 1. Create a portfolio
    res = client.post("/api/v1/portfolios", json={
        "name": "Integration Portfolio",
        "base_currency": "INR",
        "timezone": "Asia/Kolkata",
        "benchmark_symbol": "^NSEI"
    })
    assert res.status_code == 201
    portfolio = res.json()
    p_id = portfolio["id"]

    # 2. Get accounts for portfolio
    res = client.get(f"/api/v1/accounts?portfolio_id={p_id}")
    assert res.status_code == 200
    accounts = res.json()
    assert len(accounts) >= 1
    acc_id = accounts[0]["id"]

    # 3. Preview transaction
    preview_res = client.post("/api/v1/transactions/preview", json={
        "portfolio_id": p_id,
        "account_id": acc_id,
        "symbol": "RELIANCE",
        "type": "BUY",
        "trade_date": str(date.today()),
        "quantity": "5.0",
        "unit_price": "2500.00",
        "fee": "20.00",
        "tax": "5.00",
        "currency": "INR"
    })
    assert preview_res.status_code == 200
    preview = preview_res.json()
    assert preview["net_cash_impact"] == "-12525.00"

    # 4. Create transaction
    create_res = client.post("/api/v1/transactions", json={
        "portfolio_id": p_id,
        "account_id": acc_id,
        "symbol": "RELIANCE",
        "type": "BUY",
        "trade_date": str(date.today()),
        "quantity": "5.0",
        "unit_price": "2500.00",
        "fee": "20.00",
        "tax": "5.00",
        "currency": "INR"
    })
    assert create_res.status_code == 201
    tx = create_res.json()
    tx_id = tx["id"]
    assert tx["symbol"] == "RELIANCE"
    assert tx["net_amount"] == "-12525.00"

    # 5. List transactions with filter
    list_res = client.get(f"/api/v1/transactions?portfolio_id={p_id}&symbol=RELIANCE")
    assert list_res.status_code == 200
    data = list_res.json()
    assert data["total"] >= 1

    # 6. Reverse transaction
    rev_res = client.post(f"/api/v1/transactions/{tx_id}/reverse?reason=Wrong quantity entry")
    assert rev_res.status_code == 200
    rev_tx = rev_res.json()
    assert rev_tx["type"] == "CORRECTION_REVERSAL"
    assert rev_tx["net_amount"] == "12525.00"
