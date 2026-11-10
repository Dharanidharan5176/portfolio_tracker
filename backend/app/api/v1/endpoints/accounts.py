from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.schemas.account import AccountCreate, AccountResponse
from backend.app.services.portfolio_service import portfolio_service

router = APIRouter()

@router.get("", response_model=List[AccountResponse])
def list_accounts(portfolio_id: Optional[int] = None, db: Session = Depends(get_db)):
    return portfolio_service.get_accounts(db, portfolio_id=portfolio_id)

@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
    return portfolio_service.create_account(db, payload)

