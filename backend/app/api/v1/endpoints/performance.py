from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.db.session import get_db
from backend.app.db.models.portfolio import Portfolio
from backend.app.services.performance_service import performance_service

router = APIRouter()

@router.get("")
def get_performance(
    portfolio_id: Optional[int] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    method: str = Query("twr"),
    db: Session = Depends(get_db)
):
    target_p_id = portfolio_id
    if not target_p_id:
        p = db.scalar(select(Portfolio).where(Portfolio.status == "active"))
        if p:
            target_p_id = p.id
        else:
            return {"status": "insufficient_data", "message": "No active portfolio found."}

    twr_res = performance_service.calculate_twr(db, target_p_id, start_date=from_date, end_date=to_date)
    dd_res = performance_service.calculate_drawdown(db, target_p_id)

    return {
        **twr_res,
        "max_drawdown_pct": dd_res["max_drawdown_pct"],
        "drawdown_series": dd_res["series"]
    }
