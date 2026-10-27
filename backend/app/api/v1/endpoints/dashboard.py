from fastapi import APIRouter
router = APIRouter()

@router.get("")
def get_dashboard():
    return {
        "portfolio_value": "0.00",
        "invested_cost_basis": "0.00",
        "unrealized_pnl": "0.00",
        "unrealized_pnl_pct": "0.00",
        "realized_pnl": "0.00",
        "cash_balance": "0.00",
        "data_freshness": "No active holdings recorded",
        "holdings": [],
        "allocation": [],
        "recent_activity": []
    }
