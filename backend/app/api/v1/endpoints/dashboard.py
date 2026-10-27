from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.db.session import get_db
from backend.app.db.models.portfolio import Portfolio
from backend.app.db.models.transaction import Transaction
from backend.app.db.models.audit import Notification, DataQualityIssue
from backend.app.services.valuation_service import valuation_service
from backend.app.services.transaction_service import to_money

router = APIRouter()

@router.get("")
def get_dashboard(
    portfolio_id: Optional[int] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    target_p_id = portfolio_id
    if not target_p_id:
        p = db.scalar(select(Portfolio).where(Portfolio.status == "active"))
        if p:
            target_p_id = p.id
        else:
            return {
                "portfolio_id": None,
                "portfolio_name": "No Active Portfolio",
                "base_currency": "INR",
                "as_of": date.today().isoformat(),
                "total_portfolio_value": "0.00",
                "holdings_market_value": "0.00",
                "invested_cost_basis": "0.00",
                "unrealized_pnl": "0.00",
                "unrealized_pnl_pct": "0.00",
                "realized_pnl": "0.00",
                "cash_balance": "0.00",
                "data_freshness": "No portfolio found. Create one to begin.",
                "holdings_count": 0,
                "holdings": [],
                "recent_activity": [],
                "allocation_by_asset": [],
                "value_history": [],
                "unread_notifications_count": 0,
                "open_issues_count": 0
            }

    summary = valuation_service.get_portfolio_valuation_summary(db, target_p_id, as_of=to_date)

    # Recent transactions
    recent_txs = db.scalars(
        select(Transaction)
        .where(Transaction.portfolio_id == target_p_id)
        .order_by(Transaction.trade_date.desc(), Transaction.id.desc())
        .limit(10)
    ).all()

    activity = []
    for t in recent_txs:
        sym = t.instrument.canonical_symbol if t.instrument else "-"
        activity.append({
            "id": t.id,
            "type": t.type,
            "symbol": sym,
            "trade_date": t.trade_date.isoformat(),
            "quantity": str(t.quantity) if t.quantity else None,
            "gross_amount": str(t.gross_amount),
            "net_amount": str(t.net_amount),
            "currency": t.currency,
            "is_reversed": t.is_reversed
        })

    # Allocation by asset class
    holdings = summary.get("holdings", [])
    asset_groups: Dict[str, Decimal] = {}
    total_val = Decimal(summary.get("total_portfolio_value", "0.00"))
    cash_val = Decimal(summary.get("cash_balance", "0.00"))
    if cash_val > Decimal("0.00"):
        asset_groups["Cash"] = cash_val

    for h in holdings:
        m_val = Decimal(h["market_value"]) if h.get("market_value") else Decimal(h["cost_basis"])
        atype = (h.get("asset_type") or "equity").title()
        asset_groups[atype] = asset_groups.get(atype, Decimal("0.00")) + m_val

    allocation_list = []
    for cat, val in asset_groups.items():
        weight = ((val / total_val) * Decimal("100.00")).quantize(Decimal("0.01")) if total_val > Decimal("0.00") else Decimal("0.00")
        allocation_list.append({
            "name": cat,
            "value": str(val),
            "weight": str(weight)
        })

    # Value history points (last 7 recorded transaction dates or simulated range)
    # Trace points
    history_points = []
    tx_dates = db.scalars(
        select(Transaction.trade_date)
        .where(Transaction.portfolio_id == target_p_id)
        .distinct()
        .order_by(Transaction.trade_date.asc())
    ).all()
    
    if tx_dates:
        for d in tx_dates[-15:]:
            pt_summary = valuation_service.get_portfolio_valuation_summary(db, target_p_id, as_of=d)
            history_points.append({
                "date": d.isoformat(),
                "portfolio_value": pt_summary["total_portfolio_value"],
                "cost_basis": pt_summary["invested_cost_basis"]
            })
    if not history_points:
        history_points.append({
            "date": date.today().isoformat(),
            "portfolio_value": summary["total_portfolio_value"],
            "cost_basis": summary["invested_cost_basis"]
        })

    # Unread notifications & open data quality issues count
    unread_notifs = db.scalars(select(Notification).where(Notification.status == "unread")).all()
    open_issues = db.scalars(select(DataQualityIssue).where(DataQualityIssue.status == "open")).all()

    summary["recent_activity"] = activity
    summary["allocation_by_asset"] = allocation_list
    summary["value_history"] = history_points
    summary["unread_notifications_count"] = len(unread_notifs)
    summary["open_issues_count"] = len(open_issues)

    return summary
