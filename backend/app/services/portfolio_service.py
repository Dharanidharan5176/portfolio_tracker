from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.app.db.models.portfolio import Portfolio
from backend.app.db.models.account import Account
from backend.app.db.models.transaction import Transaction
from backend.app.schemas.portfolio import PortfolioCreate, PortfolioUpdate
from backend.app.schemas.account import AccountCreate, AccountUpdate
from backend.app.core.errors import NotFoundError, ConflictError, AppError
from backend.app.services.audit_service import audit_service

class PortfolioService:
    @staticmethod
    def get_portfolios(db: Session, include_archived: bool = False) -> List[Portfolio]:
        query = select(Portfolio)
        if not include_archived:
            query = query.where(Portfolio.status == "active")
        return list(db.scalars(query).all())

    @staticmethod
    def get_portfolio(db: Session, portfolio_id: int) -> Portfolio:
        portfolio = db.get(Portfolio, portfolio_id)
        if not portfolio:
            raise NotFoundError(f"Portfolio with ID {portfolio_id} not found.")
        return portfolio

    @staticmethod
    def create_portfolio(db: Session, payload: PortfolioCreate) -> Portfolio:
        existing = db.scalar(select(Portfolio).where(Portfolio.name == payload.name))
        if existing:
            raise ConflictError(f"A portfolio named '{payload.name}' already exists.")
        
        portfolio = Portfolio(
            name=payload.name,
            base_currency=payload.base_currency.upper(),
            timezone=payload.timezone,
            benchmark_symbol=payload.benchmark_symbol,
            notes=payload.notes,
            status="active"
        )
        db.add(portfolio)
        db.flush()

        # Create a default cash/brokerage account
        default_account = Account(
            portfolio_id=portfolio.id,
            name=f"{portfolio.name} Default Account",
            account_type="brokerage",
            institution_label="Primary",
            currency=portfolio.base_currency,
            status="active"
        )
        db.add(default_account)
        db.flush()

        audit_service.log(
            db,
            action="CREATE_PORTFOLIO",
            entity_type="portfolio",
            entity_id=portfolio.id,
            after_state={"name": portfolio.name, "currency": portfolio.base_currency}
        )
        db.commit()
        db.refresh(portfolio)
        return portfolio

    @staticmethod
    def update_portfolio(db: Session, portfolio_id: int, payload: PortfolioUpdate) -> Portfolio:
        portfolio = PortfolioService.get_portfolio(db, portfolio_id)
        before = {"name": portfolio.name, "status": portfolio.status, "currency": portfolio.base_currency}
        
        if payload.name is not None and payload.name != portfolio.name:
            dup = db.scalar(select(Portfolio).where(Portfolio.name == payload.name))
            if dup:
                raise ConflictError(f"A portfolio named '{payload.name}' already exists.")
            portfolio.name = payload.name

        if payload.base_currency is not None:
            portfolio.base_currency = payload.base_currency.upper()
        if payload.timezone is not None:
            portfolio.timezone = payload.timezone
        if payload.benchmark_symbol is not None:
            portfolio.benchmark_symbol = payload.benchmark_symbol
        if payload.notes is not None:
            portfolio.notes = payload.notes
        if payload.status is not None:
            portfolio.status = payload.status

        audit_service.log(
            db,
            action="UPDATE_PORTFOLIO",
            entity_type="portfolio",
            entity_id=portfolio.id,
            before_state=before,
            after_state={"name": portfolio.name, "status": portfolio.status, "currency": portfolio.base_currency}
        )
        db.commit()
        db.refresh(portfolio)
        return portfolio

    @staticmethod
    def archive_portfolio(db: Session, portfolio_id: int) -> Portfolio:
        portfolio = PortfolioService.get_portfolio(db, portfolio_id)
        portfolio.status = "archived"
        audit_service.log(
            db,
            action="ARCHIVE_PORTFOLIO",
            entity_type="portfolio",
            entity_id=portfolio.id,
            reason="User requested archival"
        )
        db.commit()
        db.refresh(portfolio)
        return portfolio

    # Accounts
    @staticmethod
    def get_accounts(db: Session, portfolio_id: Optional[int] = None) -> List[Account]:
        query = select(Account).where(Account.status == "active")
        if portfolio_id:
            query = query.where(Account.portfolio_id == portfolio_id)
        return list(db.scalars(query).all())

    @staticmethod
    def create_account(db: Session, payload: AccountCreate) -> Account:
        PortfolioService.get_portfolio(db, payload.portfolio_id)
        existing = db.scalar(
            select(Account).where(
                Account.portfolio_id == payload.portfolio_id,
                Account.name == payload.name
            )
        )
        if existing:
            raise ConflictError(f"Account '{payload.name}' already exists in this portfolio.")

        account = Account(
            portfolio_id=payload.portfolio_id,
            name=payload.name,
            account_type=payload.account_type,
            institution_label=payload.institution_label,
            currency=payload.currency.upper(),
            status="active"
        )
        db.add(account)
        db.flush()

        audit_service.log(
            db,
            action="CREATE_ACCOUNT",
            entity_type="account",
            entity_id=account.id,
            after_state={"portfolio_id": account.portfolio_id, "name": account.name}
        )
        db.commit()
        db.refresh(account)
        return account

portfolio_service = PortfolioService()
