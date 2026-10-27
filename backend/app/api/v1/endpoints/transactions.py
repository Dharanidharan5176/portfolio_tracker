from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from backend.app.db.session import get_db
from backend.app.db.models.transaction import Transaction
from backend.app.db.models.instrument import Instrument
from backend.app.schemas.transaction import TransactionCreate, TransactionPreview, TransactionResponse
from backend.app.services.transaction_service import transaction_service
from backend.app.core.errors import NotFoundError

router = APIRouter()

@router.get("")
def list_transactions(
    portfolio_id: Optional[int] = Query(None),
    account_id: Optional[int] = Query(None),
    symbol: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = select(Transaction).outerjoin(Instrument)
    conditions = []

    if portfolio_id:
        conditions.append(Transaction.portfolio_id == portfolio_id)
    if account_id:
        conditions.append(Transaction.account_id == account_id)
    if symbol:
        conditions.append(Instrument.canonical_symbol == symbol.strip().upper())
    if type:
        conditions.append(Transaction.type == type.upper())
    if from_date:
        conditions.append(Transaction.trade_date >= from_date)
    if to_date:
        conditions.append(Transaction.trade_date <= to_date)

    if conditions:
        query = query.where(and_(*conditions))

    total = len(db.scalars(query).all())
    items = db.scalars(query.order_by(Transaction.trade_date.desc(), Transaction.id.desc()).offset(offset).limit(limit)).all()

    # Format response
    result_items = []
    for tx in items:
        resp = TransactionResponse.model_validate(tx)
        if tx.instrument:
            resp.symbol = tx.instrument.canonical_symbol
        result_items.append(resp)

    return {"items": result_items, "total": total, "limit": limit, "offset": offset}

@router.post("/preview", response_model=TransactionPreview)
def preview_transaction(payload: TransactionCreate, db: Session = Depends(get_db)):
    return transaction_service.preview_transaction(db, payload)

@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db)):
    tx = transaction_service.create_transaction(db, payload)
    resp = TransactionResponse.model_validate(tx)
    if tx.instrument:
        resp.symbol = tx.instrument.canonical_symbol
    return resp

@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    tx = db.get(Transaction, transaction_id)
    if not tx:
        raise NotFoundError(f"Transaction with ID {transaction_id} not found.")
    resp = TransactionResponse.model_validate(tx)
    if tx.instrument:
        resp.symbol = tx.instrument.canonical_symbol
    return resp

@router.post("/{transaction_id}/reverse", response_model=TransactionResponse)
def reverse_transaction(transaction_id: int, reason: str = "User reversal", db: Session = Depends(get_db)):
    rev_tx = transaction_service.reverse_transaction(db, transaction_id, reason=reason)
    resp = TransactionResponse.model_validate(rev_tx)
    if rev_tx.instrument:
        resp.symbol = rev_tx.instrument.canonical_symbol
    return resp
