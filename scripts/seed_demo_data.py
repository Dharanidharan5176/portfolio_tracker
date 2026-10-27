import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.db.session import SessionLocal
from backend.app.db.models.market_data import PriceObservation
from backend.app.schemas.portfolio import PortfolioCreate
from backend.app.schemas.transaction import TransactionCreate
from backend.app.services.portfolio_service import portfolio_service
from backend.app.services.transaction_service import transaction_service

def main():
    print("Seeding synthetic Demo Portfolio...")
    db = SessionLocal()
    try:
        # Check if already exists
        existing = portfolio_service.get_portfolios(db, include_archived=True)
        demo_port = next((p for p in existing if "Demo" in p.name), None)

        if not demo_port:
            demo_port = portfolio_service.create_portfolio(
                db,
                PortfolioCreate(
                    name="Demo Portfolio (Synthetic)",
                    base_currency="INR",
                    timezone="Asia/Kolkata",
                    benchmark_symbol="^NSEI",
                    notes="Synthetic sandbox portfolio for testing features. Never mixed with real accounts."
                )
            )

        account = demo_port.accounts[0]

        # 1. Cash Deposit: 100,000 INR
        transaction_service.create_transaction(
            db,
            TransactionCreate(
                portfolio_id=demo_port.id,
                account_id=account.id,
                type="CASH_DEPOSIT",
                trade_date=date(2026, 1, 1),
                gross_amount=Decimal("100000.00"),
                currency="INR",
                notes="Synthetic opening capital"
            )
        )

        # 2. Buy INFY: 25 shares @ 1,450.00 INR + 20 fee
        tx_infy = transaction_service.create_transaction(
            db,
            TransactionCreate(
                portfolio_id=demo_port.id,
                account_id=account.id,
                symbol="INFY",
                type="BUY",
                trade_date=date(2026, 1, 5),
                quantity=Decimal("25.0000"),
                unit_price=Decimal("1450.0000"),
                fee=Decimal("20.00"),
                currency="INR",
                notes="Synthetic purchase"
            )
        )

        # 3. Buy TCS: 10 shares @ 3,600.00 INR + 30 fee
        tx_tcs = transaction_service.create_transaction(
            db,
            TransactionCreate(
                portfolio_id=demo_port.id,
                account_id=account.id,
                symbol="TCS",
                type="BUY",
                trade_date=date(2026, 1, 8),
                quantity=Decimal("10.0000"),
                unit_price=Decimal("3600.0000"),
                fee=Decimal("30.00"),
                currency="INR",
                notes="Synthetic purchase"
            )
        )

        # 4. Dividend from INFY: 500 INR
        transaction_service.create_transaction(
            db,
            TransactionCreate(
                portfolio_id=demo_port.id,
                account_id=account.id,
                symbol="INFY",
                type="DIVIDEND",
                trade_date=date(2026, 1, 20),
                gross_amount=Decimal("500.00"),
                tax=Decimal("50.00"),
                currency="INR",
                notes="Synthetic interim dividend"
            )
        )

        # Add price observations for today
        now = datetime.now(timezone.utc)
        db.add(PriceObservation(
            instrument_id=tx_infy.instrument_id,
            observed_at=now,
            price=Decimal("1580.0000"),
            currency="INR",
            provider="manual_csv",
            quality_status="valid",
            imported_at=now
        ))
        db.add(PriceObservation(
            instrument_id=tx_tcs.instrument_id,
            observed_at=now,
            price=Decimal("3850.0000"),
            currency="INR",
            provider="manual_csv",
            quality_status="valid",
            imported_at=now
        ))
        db.commit()

        print("Synthetic demo data seeded successfully!")
        print(f" - Portfolio ID: {demo_port.id} ({demo_port.name})")
        print(" - Holdings: INFY (25 units), TCS (10 units)")
        print(" - Cash balance adjusted in local ledger.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
