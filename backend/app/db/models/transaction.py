from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import Integer, String, Text, Date, DateTime, Numeric, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    portfolio_id: Mapped[int] = mapped_column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    instrument_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("instruments.id"), nullable=True, index=True)
    
    # Types: BUY, SELL, CASH_DEPOSIT, CASH_WITHDRAWAL, DIVIDEND, INTEREST, FEE, TAX_WITHHOLDING, SPLIT, MERGER_ADJUSTMENT, TRANSFER_IN, TRANSFER_OUT, CORRECTION_REVERSAL
    type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    settlement_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    fee: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"), nullable=False)
    tax: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"), nullable=False)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False) # Cash effect for this transaction
    
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    fx_rate: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("1.0000"), nullable=False)
    
    external_ref: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)
    import_batch_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("import_batches.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Audit & Reversal
    correction_of_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("transactions.id"), nullable=True)
    is_reversed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    portfolio = relationship("Portfolio", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
    instrument = relationship("Instrument", back_populates="transactions")
    cash_entries = relationship("CashLedgerEntry", back_populates="transaction", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_tx_portfolio_date", "portfolio_id", "trade_date"),
        Index("ix_tx_account_date", "account_id", "trade_date"),
    )

class CashLedgerEntry(Base):
    """
    Authoritative transactional cash movement entry, strictly generated alongside transactions.
    """
    __tablename__ = "cash_ledger_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_id: Mapped[int] = mapped_column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False) # Positive = credit, Negative = debit
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    entry_type: Mapped[str] = mapped_column(String(50), nullable=False) # 'DEPOSIT', 'WITHDRAWAL', 'BUY_OUTFLOW', 'SELL_INFLOW', 'DIVIDEND', 'FEE', etc.
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    account = relationship("Account", back_populates="cash_entries")
    transaction = relationship("Transaction", back_populates="cash_entries")

