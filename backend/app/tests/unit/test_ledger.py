from datetime import date
from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.db.base import Base
from backend.app.db.models.portfolio import Portfolio
from backend.app.db.models.account import Account
from backend.app.schemas.portfolio import PortfolioCreate
from backend.app.schemas.transaction import TransactionCreate
from backend.app.services.portfolio_service import portfolio_service
from backend.app.services.transaction_service import transaction_service
from backend.app.core.errors import LedgerIntegrityError

@pytest.fixture
def db_session():
    # In-memory SQLite for fast deterministic tests
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()

def test_ledger_buy_sell_and_cash_flow(db_session):
    # 1. Create portfolio and default account
    portfolio = portfolio_service.create_portfolio(
        db_session,
        PortfolioCreate(name="Retirement", base_currency="INR", timezone="Asia/Kolkata")
    )
    account = portfolio.accounts[0]

    # 2. Deposit Cash: 10,000 INR
    dep_tx = transaction_service.create_transaction(
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
    assert dep_tx.net_amount == Decimal("10000.00")
    cash_bal = transaction_service.get_account_cash(db_session, account.id)
    assert cash_bal == Decimal("10000.00")

    # 3. Buy 10 shares of INFY at 1,000 INR each with 10 INR fee
    buy1 = transaction_service.create_transaction(
        db_session,
        TransactionCreate(
            portfolio_id=portfolio.id,
            account_id=account.id,
            symbol="INFY",
            type="BUY",
            trade_date=date(2026, 1, 2),
            quantity=Decimal("10.0000"),
            unit_price=Decimal("1000.0000"),
            fee=Decimal("10.00"),
            currency="INR"
        )
    )
    # Total outlay = 10 * 1000 + 10 = 10010.00
    assert buy1.net_amount == Decimal("-10010.00")
    cash_bal = transaction_service.get_account_cash(db_session, account.id)
    assert cash_bal == Decimal("-10.00") # 10000 - 10010

    qty, cost, avg_cost = transaction_service.get_current_position(db_session, portfolio.id, buy1.instrument_id)
    assert qty == Decimal("10.0000")
    assert cost == Decimal("10010.00")
    assert avg_cost == Decimal("1001.0000")

    # 4. Buy 10 more shares of INFY at 1,200 INR each with 10 INR fee
    buy2 = transaction_service.create_transaction(
        db_session,
        TransactionCreate(
            portfolio_id=portfolio.id,
            account_id=account.id,
            symbol="INFY",
            type="BUY",
            trade_date=date(2026, 1, 3),
            quantity=Decimal("10.0000"),
            unit_price=Decimal("1200.0000"),
            fee=Decimal("10.00"),
            currency="INR"
        )
    )
    # Total outlay = 12000 + 10 = 12010.00.
    # Total cost = 10010 + 12010 = 22020.00. Total qty = 20. Avg cost = 1101.0000
    qty, cost, avg_cost = transaction_service.get_current_position(db_session, portfolio.id, buy1.instrument_id)
    assert qty == Decimal("20.0000")
    assert cost == Decimal("22020.00")
    assert avg_cost == Decimal("1101.0000")

    # 5. Sell 5 shares of INFY at 1,500 INR each with 15 INR fee
    # Net proceeds = (5 * 1500) - 15 = 7500 - 15 = 7485.00
    sell1 = transaction_service.create_transaction(
        db_session,
        TransactionCreate(
            portfolio_id=portfolio.id,
            account_id=account.id,
            symbol="INFY",
            type="SELL",
            trade_date=date(2026, 1, 5),
            quantity=Decimal("5.0000"),
            unit_price=Decimal("1500.0000"),
            fee=Decimal("15.00"),
            currency="INR"
        )
    )
    assert sell1.net_amount == Decimal("7485.00")
    # Remaining shares = 15. Remaining cost basis = 22020 - (5 * 1101) = 22020 - 5505 = 16515.00
    qty, cost, avg_cost = transaction_service.get_current_position(db_session, portfolio.id, buy1.instrument_id)
    assert qty == Decimal("15.0000")
    assert cost == Decimal("16515.00")
    assert avg_cost == Decimal("1101.0000")

def test_oversell_blocking(db_session):
    portfolio = portfolio_service.create_portfolio(
        db_session,
        PortfolioCreate(name="Growth", base_currency="INR")
    )
    account = portfolio.accounts[0]

    # Buy 2 shares
    transaction_service.create_transaction(
        db_session,
        TransactionCreate(
            portfolio_id=portfolio.id,
            account_id=account.id,
            symbol="TCS",
            type="BUY",
            trade_date=date(2026, 1, 1),
            quantity=Decimal("2.0000"),
            unit_price=Decimal("3000.0000"),
            currency="INR"
        )
    )

    # Attempt to sell 5 shares should raise LedgerIntegrityError
    with pytest.raises(LedgerIntegrityError):
        transaction_service.create_transaction(
            db_session,
            TransactionCreate(
                portfolio_id=portfolio.id,
                account_id=account.id,
                symbol="TCS",
                type="SELL",
                trade_date=date(2026, 1, 2),
                quantity=Decimal("5.0000"),
                unit_price=Decimal("3100.0000"),
                currency="INR"
            )
        )

def test_split_and_reversal(db_session):
    portfolio = portfolio_service.create_portfolio(
        db_session,
        PortfolioCreate(name="Tech", base_currency="INR")
    )
    account = portfolio.accounts[0]

    # Buy 10 shares of AAPL at 150 each -> Cost 1500
    buy = transaction_service.create_transaction(
        db_session,
        TransactionCreate(
            portfolio_id=portfolio.id,
            account_id=account.id,
            symbol="AAPL",
            type="BUY",
            trade_date=date(2026, 1, 1),
            quantity=Decimal("10.0000"),
            unit_price=Decimal("150.0000"),
            currency="INR"
        )
    )
    qty, cost, avg_cost = transaction_service.get_current_position(db_session, portfolio.id, buy.instrument_id)
    assert qty == Decimal("10.0000")
    assert cost == Decimal("1500.00")
    assert avg_cost == Decimal("150.0000")

    # 2-for-1 Split (multiplier 2.0)
    split = transaction_service.create_transaction(
        db_session,
        TransactionCreate(
            portfolio_id=portfolio.id,
            account_id=account.id,
            symbol="AAPL",
            type="SPLIT",
            trade_date=date(2026, 1, 10),
            quantity=Decimal("2.0000"), # 2x multiplier
            currency="INR"
        )
    )
    qty, cost, avg_cost = transaction_service.get_current_position(db_session, portfolio.id, buy.instrument_id)
    assert qty == Decimal("20.0000")
    assert cost == Decimal("1500.00") # Total cost preserved
    assert avg_cost == Decimal("75.0000") # Unit cost halved

    # Reversal of split
    rev = transaction_service.reverse_transaction(db_session, split.id, reason="Undo split test")
    assert rev.is_reversed is False
    assert split.is_reversed is True

    # Position back to 10 shares
    qty, cost, avg_cost = transaction_service.get_current_position(db_session, portfolio.id, buy.instrument_id)
    assert qty == Decimal("10.0000")
    assert cost == Decimal("1500.00")
    assert avg_cost == Decimal("150.0000")

