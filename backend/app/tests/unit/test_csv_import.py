from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.base import Base
from backend.app.schemas.portfolio import PortfolioCreate
from backend.app.schemas.import_schema import ImportConfirmRequest
from backend.app.services.portfolio_service import portfolio_service
from backend.app.services.import_service import import_service
from backend.app.core.errors import ValidationError

SAMPLE_VALID_CSV = """transaction_date,symbol,transaction_type,quantity,unit_price,gross_amount,fee,tax,currency,external_reference
2026-01-05,INFY,BUY,10,1200.00,12000.00,10.00,0.00,INR,IMPORT-TX-1
2026-01-06,TCS,BUY,5,3000.00,15000.00,15.00,0.00,INR,IMPORT-TX-2
"""

SAMPLE_INVALID_CSV = """transaction_date,symbol,transaction_type,quantity,unit_price,gross_amount,fee,tax,currency,external_reference
2026-99-99,INFY,BUY,10,1200.00,12000.00,10.00,0.00,INR,ERR-1
2026-01-05,,BUY,10,1200.00,12000.00,10.00,0.00,INR,ERR-2
2026-01-05,TCS,UNKNOWN_TYPE,10,1200.00,12000.00,10.00,0.00,INR,ERR-3
"""

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

def test_csv_preview_parsing():
    preview = import_service.parse_preview(SAMPLE_VALID_CSV, "test.csv", source_type="transactions")
    assert preview.total_rows == 2
    assert preview.valid_rows_count == 2
    assert preview.error_rows_count == 0
    assert "transaction_date" in preview.detected_headers
    assert preview.rows[0].parsed_data["symbol"] == "INFY"

def test_csv_preview_validation_errors():
    preview = import_service.parse_preview(SAMPLE_INVALID_CSV, "bad.csv", source_type="transactions")
    assert preview.total_rows == 3
    assert preview.valid_rows_count == 0
    assert preview.error_rows_count == 3
    assert any("Invalid date format" in e for e in preview.rows[0].errors)
    assert any("Symbol is required" in e for e in preview.rows[1].errors)
    assert any("Unknown type" in e for e in preview.rows[2].errors)

def test_import_confirm_and_atomic_policy(db_session):
    portfolio = portfolio_service.create_portfolio(db_session, PortfolioCreate(name="Import Port", base_currency="INR"))
    account = portfolio.accounts[0]

    # Atomic import with bad CSV must fail
    req_bad = ImportConfirmRequest(
        portfolio_id=portfolio.id,
        account_id=account.id,
        source_type="transactions",
        column_mapping=import_service.auto_detect_mapping(SAMPLE_INVALID_CSV.splitlines()[0].split(","), "transactions"),
        policy="atomic"
    )
    with pytest.raises(ValidationError):
        import_service.confirm_import(db_session, SAMPLE_INVALID_CSV, "bad.csv", req_bad)

    # Valid CSV import succeeds
    mapping = import_service.auto_detect_mapping(SAMPLE_VALID_CSV.splitlines()[0].split(","), "transactions")
    req_good = ImportConfirmRequest(
        portfolio_id=portfolio.id,
        account_id=account.id,
        source_type="transactions",
        column_mapping=mapping,
        policy="atomic"
    )
    batch = import_service.confirm_import(db_session, SAMPLE_VALID_CSV, "valid.csv", req_good)
    assert batch.status == "completed"
    assert batch.imported_rows == 2
    assert batch.failed_rows == 0

def test_price_csv_import(db_session):
    price_csv = """symbol,price_date,close_price,currency,source
INFY,2026-01-05,1210.50,INR,manual_csv
TCS,2026-01-05,3050.00,INR,manual_csv
"""
    mapping = import_service.auto_detect_mapping(["symbol", "price_date", "close_price", "currency", "source"], "prices")
    req = ImportConfirmRequest(
        portfolio_id=1,
        account_id=1,
        source_type="prices",
        column_mapping=mapping,
        policy="atomic"
    )
    batch = import_service.confirm_import(db_session, price_csv, "prices.csv", req)
    assert batch.status == "completed"
    assert batch.imported_rows == 2

