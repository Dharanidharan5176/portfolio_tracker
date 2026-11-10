from datetime import date, datetime, timedelta, timezone
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
from backend.app.services.valuation_service import valuation_service

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

def test_valuation_calculation_and_staleness(db_session):
    portfolio = portfolio_service.create_portfolio(
        db_session,
        PortfolioCreate(name="Valuation Port", base_currency="INR")
    )
    account = portfolio.accounts[0]

    # Buy 10 shares of HDFC at 1,500 each + 10 fee -> Cost basis = 15,010.00
    buy = transaction_service.create_transaction(
        db_session,
        TransactionCreate(
            portfolio_id=portfolio.id,
            account_id=account.id,
            symbol="HDFCBANK",
            type="BUY",
            trade_date=date(2026, 1, 1),
            quantity=Decimal("10.0000"),
            unit_price=Decimal("1500.0000"),
            fee=Decimal("10.00"),
            currency="INR"
        )
    )

    # 1. Before any price is added: quality status is 'missing_price'
    holdings = valuation_service.get_portfolio_holdings(db_session, portfolio.id, as_of=date(2026, 1, 1))
    assert len(holdings) == 1
    h = holdings[0]
    assert h.symbol == "HDFCBANK"
    assert h.quality_status == "missing_price"
    assert h.market_value is None

    # 2. Add an observation from 10 days ago -> Should be marked 'stale'
    old_date = datetime.now(timezone.utc) - timedelta(days=10)
    obs_old = PriceObservation(
        instrument_id=buy.instrument_id,
        observed_at=old_date,
        price=Decimal("1600.0000"),
        currency="INR",
        provider="manual_csv",
        quality_status="valid",
        imported_at=datetime.now(timezone.utc)
    )
    db_session.add(obs_old)
    db_session.commit()

    holdings = valuation_service.get_portfolio_holdings(db_session, portfolio.id)
    assert holdings[0].quality_status == "stale"
    assert holdings[0].market_value == Decimal("16000.00") # 10 * 1600
    assert holdings[0].unrealized_pnl == Decimal("990.00") # 16000 - 15010

    # 3. Add a fresh observation for today at 1,700.00
    fresh_date = datetime.now(timezone.utc)
    obs_fresh = PriceObservation(
        instrument_id=buy.instrument_id,
        observed_at=fresh_date,
        price=Decimal("1700.0000"),
        currency="INR",
        provider="manual_entry",
        quality_status="valid",
        is_manual_override=True,
        imported_at=datetime.now(timezone.utc)
    )
    db_session.add(obs_fresh)
    db_session.commit()

    summary = valuation_service.get_portfolio_valuation_summary(db_session, portfolio.id)
    assert summary["data_freshness"] == "Prices up to date"
    assert summary["invested_cost_basis"] == "15010.00"
    assert summary["holdings_market_value"] == "17000.00"
    assert summary["unrealized_pnl"] == "1990.00"
    assert summary["holdings"][0]["quality_status"] == "valid"
    assert summary["holdings"][0]["is_manual_override"] is True

