from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.db.session import get_db
from backend.app.db.models.portfolio import Portfolio
from backend.app.services.report_service import report_service
from backend.app.core.errors import NotFoundError

router = APIRouter()

@router.get("/{report_type}")
def get_report(
    report_type: str,
    portfolio_id: Optional[int] = Query(None),
    format: str = Query("json"), # 'json' or 'csv'
    db: Session = Depends(get_db)
):
    target_p_id = portfolio_id
    if not target_p_id:
        p = db.scalar(select(Portfolio).where(Portfolio.status == "active"))
        if p:
            target_p_id = p.id
        else:
            raise NotFoundError("No active portfolio found.")

    if report_type == "holdings":
        data = report_service.generate_holdings_report(db, target_p_id)
        if format == "csv":
            csv_text = report_service.holdings_to_csv(data)
            return PlainTextResponse(content=csv_text, media_type="text/csv")
        return data

    elif report_type == "transactions":
        data = report_service.generate_transactions_report(db, target_p_id)
        if format == "csv":
            csv_text = report_service.transactions_to_csv(data)
            return PlainTextResponse(content=csv_text, media_type="text/csv")
        return data

    else:
        raise NotFoundError(f"Report type '{report_type}' not recognized. Use 'holdings' or 'transactions'.")
