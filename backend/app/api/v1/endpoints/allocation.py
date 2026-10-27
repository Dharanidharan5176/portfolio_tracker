from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.db.session import get_db
from backend.app.db.models.portfolio import Portfolio
from backend.app.db.models.account import Account
from backend.app.services.valuation_service import valuation_service

router = APIRouter()

@router.get("")
def get_allocation(
    portfolio_id: Optional[int] = Query(None),
    as_of: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    target_p_id = portfolio_id
    if not target_p_id:
        p = db.scalar(select(Portfolio).where(Portfolio.status == "active"))
        if p:
            target_p_id = p.id
        else:
            return {"by_asset_class": [], "by_holding": [], "by_account": [], "concentration": {}}

    summary = valuation_service.get_portfolio_valuation_summary(db, target_p_id, as_of=as_of)
    holdings = summary.get("holdings", [])
    total_val = Decimal(summary.get("total_portfolio_value", "0.00"))

    # By asset class
    asset_groups: Dict[str, Decimal] = {}
    cash_val = Decimal(summary.get("cash_balance", "0.00"))
    if cash_val > Decimal("0.00"):
        asset_groups["Cash"] = cash_val
    for h in holdings:
        m = Decimal(h["market_value"]) if h.get("market_value") else Decimal(h["cost_basis"])
        cat = (h.get("asset_type") or "equity").title()
        asset_groups[cat] = asset_groups.get(cat, Decimal("0.00")) + m

    by_asset = [
        {
            "category": cat,
            "market_value": str(val),
            "weight": str(((val / total_val) * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)) if total_val > 0 else "0.00"
        }
        for cat, val in asset_groups.items()
    ]

    # By holding
    by_holding = [
        {
            "symbol": h["symbol"],
            "display_name": h["display_name"],
            "market_value": h["market_value"] or h["cost_basis"],
            "weight": h["weight"]
        }
        for h in sorted(holdings, key=lambda x: Decimal(x["weight"]), reverse=True)
    ]

    # Concentration metrics
    top_1_weight = Decimal(by_holding[0]["weight"]) if by_holding else Decimal("0.00")
    top_5_weight = sum((Decimal(h["weight"]) for h in by_holding[:5]), Decimal("0.00"))

    return {
        "portfolio_id": target_p_id,
        "as_of": (as_of or date.today()).isoformat(),
        "total_value": str(total_val),
        "by_asset_class": by_asset,
        "by_holding": by_holding,
        "concentration": {
            "largest_holding_weight": str(top_1_weight),
            "top_5_holdings_weight": str(top_5_weight),
            "high_concentration_alert": top_1_weight > Decimal("25.00") or top_5_weight > Decimal("60.00")
        }
    }
