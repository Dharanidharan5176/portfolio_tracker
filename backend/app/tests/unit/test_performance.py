from datetime import date, datetime, timezone
from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.base import Base
from backend.app.db.models.market_data import PriceObservation
from backend.app.schemas.portfolio import PortfolioCreate
from backend.app.schemas.transaction import TransactionCreate
from backend.app.services.portfolio_service import portfolio_service
from backend.app.services.transaction_service import transaction_service
from backend.app.services.performance_service import performance_service
from backend.app.services.report_service import report_service

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()

def test_twr_handles_external_cash_flows(db_session):
    portfolio = portfolio_service.create_portfolio(
        db_session,
        PortfolioCreate(name="Perf Port", base_currency="INR")
    )
    account = portfolio.accounts[0]

    # Day 1: Deposit 10,000 INR
    transaction_service.create_transaction(
        db_session,
        TransactionCreate(
            portfolio_id=portfolio.id,
            account_id=account.id,
            type="CASH_DEPOSIT",
            trade_date=date(2026, 1, 1),
            gross_amount=Decimal("10000.00"),
            currency="INR"
        )
    )

    # Day 1: Buy 10 shares of XYZ at 1,000 each -> cash 0, stock 10,000
    buy = transaction_service.create_transaction(
        db_session,
        TransactionCreate(
            portfolio_id=portfolio.id,
            account_id=account.id,
            symbol="XYZ",
            type="BUY",
            trade_date=date(2026, 1, 1),
            quantity=Decimal("10.0000"),
            unit_price=Decimal("1000.0000"),
            currency="INR"
        )
    )

    # Price on Day 1 is 1000
    db_session.add(PriceObservation(
        instrument_id=buy.instrument_id,
        observed_at=datetime(2026, 1, 1, 15, 30, tzinfo=timezone.utc),
        price=Decimal("1000.0000"),
        currency="INR",
        provider="manual_csv",
        quality_status="valid",
        imported_at=datetime.now(timezone.utc)
    ))
    db_session.commit()

    # Day 5: XYZ rises to 1,200 -> portfolio worth 12,000 (20% return)
    db_session.add(PriceObservation(
        instrument_id=buy.instrument_id,
        observed_at=datetime(2026, 1, 5, 15, 30, tzinfo=timezone.utc),
        price=Decimal("1200.0000"),
        currency="INR",
        provider="manual_csv",
        quality_status="valid",
        imported_at=datetime.now(timezone.utc)
    ))
    db_session.commit()

    # Day 5: External Cash Deposit of 50,000 INR
    # Portfolio value jumps from 12,000 to 62,000.
    # Simple calculation would falsely claim huge return; TWR must remain exactly +20%!
    transaction_service.create_transaction(
        db_session,
        TransactionCreate(
            portfolio_id=portfolio.id,
            account_id=account.id,
            type="CASH_DEPOSIT",
            trade_date=date(2026, 1, 5),
            gross_amount=Decimal("50000.00"),
            currency="INR"
        )
    )

    twr_result = performance_service.calculate_twr(
        db_session,
        portfolio.id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 5)
    )

    assert twr_result["status"] == "valid"
    assert twr_result["twr_pct"] == "20.00"

def test_report_generation_and_sanitization(db_session):
    portfolio = portfolio_service.create_portfolio(
        db_session,
        PortfolioCreate(name="Sanitize Test", base_currency="INR")
    )
    account = portfolio.accounts[0]

    # Potentially malicious formula notes
    transaction_service.create_transaction(
        db_session,
        TransactionCreate(
            portfolio_id=portfolio.id,
            account_id=account.id,
            type="CASH_DEPOSIT",
            trade_date=date(2026, 1, 1),
            gross_amount=Decimal("1000.00"),
            currency="INR",
            notes="=cmd|' /C calc'!A0"
        )
    )

    data = report_service.generate_transactions_report(db_session, portfolio.id)
    csv_str = report_service.transactions_to_csv(data)
    assert "'=cmd|' /C calc'!A0" in csv_str # Properly escaped against spreadsheet formula injection
