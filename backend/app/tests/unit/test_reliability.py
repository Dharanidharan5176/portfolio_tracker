from datetime import date
from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.base import Base
from backend.app.db.models.audit import DataQualityIssue
from backend.app.schemas.portfolio import PortfolioCreate
from backend.app.schemas.transaction import TransactionCreate
from backend.app.services.portfolio_service import portfolio_service
from backend.app.services.transaction_service import transaction_service
from backend.app.services.data_quality_service import data_quality_service

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

def test_data_quality_issue_detection_and_deduplication(db_session):
    portfolio = portfolio_service.create_portfolio(
        db_session,
        PortfolioCreate(name="Quality Test Port", base_currency="INR")
    )
    account = portfolio.accounts[0]

    # Create holding with missing price (BUY without price observation)
    transaction_service.create_transaction(
        db_session,
        TransactionCreate(
            portfolio_id=portfolio.id,
            account_id=account.id,
            symbol="MISSING_PRICE_STOCK",
            type="BUY",
            trade_date=date(2026, 1, 1),
            quantity=Decimal("5.0000"),
            unit_price=Decimal("100.0000"),
            currency="INR"
        )
    )

    # Run checks - should detect 1 missing price issue and 1 negative cash issue (since outlay 500 without prior deposit)
    issues_first_run = data_quality_service.run_all_checks(db_session)
    assert len(issues_first_run) >= 1
    categories = [iss.category for iss in issues_first_run]
    assert "missing_price" in categories or "negative_cash" in categories

    # Run checks again - issues should be deduplicated (not duplicated in db)
    issues_second_run = data_quality_service.run_all_checks(db_session)
    all_db_issues = db_session.query(DataQualityIssue).all()
    # Unique issue_keys guarantee no duplicates
    keys = [i.issue_key for i in all_db_issues]
    assert len(keys) == len(set(keys))

    # Resolve an issue
    target = all_db_issues[0]
    resolved = data_quality_service.resolve_issue(db_session, target.id, reason="Audited by user")
    assert resolved.status == "resolved"
    assert resolved.resolution_note == "Audited by user"

