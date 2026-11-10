from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.db.session import get_db
from backend.app.db.models.instrument import Instrument
from backend.app.db.models.portfolio import Portfolio
from backend.app.db.models.transaction import Transaction
from backend.app.db.models.market_data import PriceObservation
from backend.app.services.valuation_service import valuation_service
from backend.app.services.transaction_service import transaction_service, to_qty, to_money
from backend.app.services.audit_service import audit_service
from backend.app.core.errors import NotFoundError, ValidationError

router = APIRouter()

class ManualPriceEntry(BaseModel):
    instrument_id: int
    observed_at: datetime
    price: Decimal
    currency: str = "INR"
    notes: Optional[str] = None

@router.get("")
def list_holdings(
    portfolio_id: Optional[int] = Query(None),
    as_of: Optional[date] = Query(None),
    asset_type: Optional[str] = Query(None),
    stale_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    target_portfolio_id = portfolio_id
    if not target_portfolio_id:
        first = db.scalar(select(Portfolio).where(Portfolio.status == "active"))
        if first:
            target_portfolio_id = first.id
        else:
            return []

    holdings = valuation_service.get_portfolio_holdings(db, target_portfolio_id, as_of=as_of)
    dict_holdings = [h.to_dict() for h in holdings]

    if asset_type:
        dict_holdings = [h for h in dict_holdings if h["asset_type"].lower() == asset_type.lower()]
    if stale_only:
        dict_holdings = [h for h in dict_holdings if h["quality_status"] in ("stale", "missing_price")]

    return dict_holdings

@router.get("/{instrument_id}")
def get_holding_detail(
    instrument_id: int,
    portfolio_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    inst = db.get(Instrument, instrument_id)
    if not inst:
        raise NotFoundError(f"Instrument {instrument_id} not found.")

    target_portfolio_id = portfolio_id
    if not target_portfolio_id:
        first = db.scalar(select(Portfolio).where(Portfolio.status == "active"))
        if first:
            target_portfolio_id = first.id

    qty, cost, avg_cost = (Decimal("0.0000"), Decimal("0.00"), Decimal("0.0000"))
    if target_portfolio_id:
        qty, cost, avg_cost = transaction_service.get_current_position(db, target_portfolio_id, instrument_id)

    # Price history
    prices = db.scalars(
        select(PriceObservation)
        .where(PriceObservation.instrument_id == instrument_id)
        .order_by(PriceObservation.observed_at.desc())
        .limit(100)
    ).all()

    # Transaction history
    tx_query = select(Transaction).where(Transaction.instrument_id == instrument_id)
    if target_portfolio_id:
        tx_query = tx_query.where(Transaction.portfolio_id == target_portfolio_id)
    txs = db.scalars(tx_query.order_by(Transaction.trade_date.desc())).all()

    latest_p = prices[0].price if prices else None
    market_val = to_money(qty * latest_p) if (latest_p is not None and qty > 0) else None

    return {
        "instrument": {
            "id": inst.id,
            "canonical_symbol": inst.canonical_symbol,
            "display_name": inst.display_name,
            "asset_type": inst.asset_type,
            "exchange": inst.exchange,
            "quote_currency": inst.quote_currency,
            "sector": inst.sector
        },
        "position": {
            "quantity": str(qty),
            "average_cost": str(avg_cost),
            "cost_basis": str(cost),
            "market_value": str(market_val) if market_val is not None else None,
            "latest_price": str(latest_p) if latest_p is not None else None,
            "price_count": len(prices)
        },
        "price_history": [
            {
                "id": p.id,
                "observed_at": p.observed_at.isoformat(),
                "price": str(p.price),
                "currency": p.currency,
                "provider": p.provider,
                "is_manual_override": p.is_manual_override,
                "quality_status": p.quality_status
            }
            for p in prices
        ],
        "transaction_history": [
            {
                "id": t.id,
                "type": t.type,
                "trade_date": t.trade_date.isoformat(),
                "quantity": str(t.quantity) if t.quantity else None,
                "unit_price": str(t.unit_price) if t.unit_price else None,
                "gross_amount": str(t.gross_amount),
                "net_amount": str(t.net_amount),
                "is_reversed": t.is_reversed
            }
            for t in txs
        ]
    }

@router.post("/prices", status_code=status.HTTP_201_CREATED)
def record_manual_price(payload: ManualPriceEntry, db: Session = Depends(get_db)):
    inst = db.get(Instrument, payload.instrument_id)
    if not inst:
        raise NotFoundError(f"Instrument {payload.instrument_id} not found.")

    obs = PriceObservation(
        instrument_id=inst.id,
        observed_at=payload.observed_at,
        price=payload.price,
        currency=payload.currency.upper(),
        provider="manual_entry",
        quality_status="valid",
        is_manual_override=True,
        imported_at=datetime.now(timezone.utc)
    )
    db.add(obs)
    db.flush()

    audit_service.log(
        db,
        action="MANUAL_PRICE_OVERRIDE",
        entity_type="price_observation",
        entity_id=obs.id,
        after_state={"symbol": inst.canonical_symbol, "price": str(obs.price), "observed_at": obs.observed_at.isoformat()},
        reason=payload.notes or "User manual price observation entry"
    )
    db.commit()
    db.refresh(obs)

    return {
        "id": obs.id,
        "instrument_id": obs.instrument_id,
        "symbol": inst.canonical_symbol,
        "price": str(obs.price),
        "observed_at": obs.observed_at.isoformat(),
        "is_manual_override": obs.is_manual_override
    }

