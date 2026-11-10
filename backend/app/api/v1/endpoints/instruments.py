from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.db.session import get_db
from backend.app.db.models.instrument import Instrument
from backend.app.schemas.instrument import InstrumentCreate, InstrumentResponse
from backend.app.core.errors import ConflictError, NotFoundError

router = APIRouter()

@router.get("", response_model=List[InstrumentResponse])
def list_instruments(
    asset_type: Optional[str] = Query(None),
    active_only: bool = Query(True),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    q = select(Instrument)
    if active_only:
        q = q.where(Instrument.is_active == True)
    if asset_type:
        q = q.where(Instrument.asset_type == asset_type)
    if search:
        term = f"%{search.strip().upper()}%"
        q = q.where(
            (Instrument.canonical_symbol.ilike(term)) | (Instrument.display_name.ilike(term))
        )
    return db.scalars(q.order_by(Instrument.canonical_symbol.asc())).all()

@router.get("/{instrument_id}", response_model=InstrumentResponse)
def get_instrument(instrument_id: int, db: Session = Depends(get_db)):
    inst = db.get(Instrument, instrument_id)
    if not inst:
        raise NotFoundError(f"Instrument with id {instrument_id} not found.")
    return inst

@router.post("", response_model=InstrumentResponse, status_code=status.HTTP_201_CREATED)
def create_instrument(payload: InstrumentCreate, db: Session = Depends(get_db)):
    clean_sym = payload.canonical_symbol.strip().upper()
    existing = db.scalar(select(Instrument).where(Instrument.canonical_symbol == clean_sym))
    if existing:
        raise ConflictError(f"Instrument '{clean_sym}' already exists.")

    inst = Instrument(
        canonical_symbol=clean_sym,
        display_name=payload.display_name.strip(),
        asset_type=payload.asset_type,
        exchange=payload.exchange,
        quote_currency=payload.quote_currency.upper(),
        isin=payload.isin,
        metadata_source=payload.metadata_source or "manual",
        sector=payload.sector,
        is_active=True
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst
