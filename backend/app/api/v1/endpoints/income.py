from datetime import date
from decimal import Decimal
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from backend.app.db.session import get_db
from backend.app.db.models.portfolio import Portfolio
from backend.app.db.models.transaction import Transaction
from backend.app.db.models.instrument import Instrument
from backend.app.services.transaction_service import to_money

router = APIRouter()

@router.get("")
def get_income(
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
            return {"total_income": "0.00", "by_type": {}, "by_month": [], "items": []}

    conditions = [
        Transaction.portfolio_id == target_p_id,
        Transaction.type.in_(["DIVIDEND", "INTEREST", "FEE", "TAX_WITHHOLDING", "CASH_DEPOSIT", "CASH_WITHDRAWAL"]),
        Transaction.is_reversed == False
    ]
    if from_date:
        conditions.append(Transaction.trade_date >= from_date)
    if to_date:
        conditions.append(Transaction.trade_date <= to_date)

    txs = db.scalars(select(Transaction).where(and_(*conditions)).order_by(Transaction.trade_date.desc())).all()

    total_dividends = Decimal("0.00")
    total_interest = Decimal("0.00")
    total_fees = Decimal("0.00")
    total_taxes = Decimal("0.00")
    by_month_dict: Dict[str, Decimal] = {}

    items = []
    for t in txs:
        amt = to_money(t.gross_amount)
        month_key = t.trade_date.strftime("%Y-%m")
        sym = t.instrument.canonical_symbol if t.instrument else "-"

        if t.type == "DIVIDEND":
            total_dividends += amt
            by_month_dict[month_key] = by_month_dict.get(month_key, Decimal("0.00")) + amt
        elif t.type == "INTEREST":
            total_interest += amt
            by_month_dict[month_key] = by_month_dict.get(month_key, Decimal("0.00")) + amt
        elif t.type == "FEE":
            total_fees += amt
        elif t.type == "TAX_WITHHOLDING":
            total_taxes += amt

        items.append({
            "id": t.id,
            "type": t.type,
            "trade_date": t.trade_date.isoformat(),
            "symbol": sym,
            "gross_amount": str(t.gross_amount),
            "fee": str(t.fee),
            "tax": str(t.tax),
            "net_amount": str(t.net_amount),
            "currency": t.currency,
            "notes": t.notes
        })

    total_net_income = total_dividends + total_interest - total_fees - total_taxes

    by_month = [
        {"month": m, "income": str(val)}
        for m, val in sorted(by_month_dict.items(), reverse=True)
    ]

    return {
        "portfolio_id": target_p_id,
        "total_net_income": str(total_net_income),
        "total_dividends": str(total_dividends),
        "total_interest": str(total_interest),
        "total_fees": str(total_fees),
        "total_taxes": str(total_taxes),
        "by_month": by_month,
        "items": items
    }
