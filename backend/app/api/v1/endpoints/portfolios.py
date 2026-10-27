from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.schemas.portfolio import PortfolioCreate, PortfolioUpdate, PortfolioResponse
from backend.app.services.portfolio_service import portfolio_service

router = APIRouter()

@router.get("", response_model=List[PortfolioResponse])
def list_portfolios(include_archived: bool = False, db: Session = Depends(get_db)):
    return portfolio_service.get_portfolios(db, include_archived=include_archived)

@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
def create_portfolio(payload: PortfolioCreate, db: Session = Depends(get_db)):
    return portfolio_service.create_portfolio(db, payload)

@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    return portfolio_service.get_portfolio(db, portfolio_id)

@router.patch("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(portfolio_id: int, payload: PortfolioUpdate, db: Session = Depends(get_db)):
    return portfolio_service.update_portfolio(db, portfolio_id, payload)

@router.delete("/{portfolio_id}", response_model=PortfolioResponse)
def archive_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    return portfolio_service.archive_portfolio(db, portfolio_id)
