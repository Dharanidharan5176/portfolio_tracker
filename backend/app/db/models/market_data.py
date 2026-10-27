from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Integer, String, Text, DateTime, Numeric, Boolean, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base

class PriceObservation(Base):
    __tablename__ = "price_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instrument_id: Mapped[int] = mapped_column(Integer, ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False, index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), default="manual_csv", nullable=False)
    source_record_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    quality_status: Mapped[str] = mapped_column(String(30), default="valid", nullable=False) # 'valid', 'stale', 'anomaly'
    is_manual_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    instrument = relationship("Instrument", back_populates="prices")

    __table_args__ = (
        Index("ix_price_inst_observed", "instrument_id", "observed_at"),
    )

class FXObservation(Base):
    __tablename__ = "fx_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    quote_currency: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), default="manual_csv", nullable=False)
    quality_status: Mapped[str] = mapped_column(String(30), default="valid", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("base_currency", "quote_currency", "observed_at", name="uq_fx_base_quote_date"),
    )

class CorporateAction(Base):
    __tablename__ = "corporate_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instrument_id: Mapped[int] = mapped_column(Integer, ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False) # 'SPLIT', 'MERGER', 'SPINOFF'
    effective_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    split_ratio: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True) # e.g. 2.0 for 2-for-1
    source: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)
    verification_status: Mapped[str] = mapped_column(String(30), default="unverified", nullable=False) # 'verified', 'unverified'
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    instrument = relationship("Instrument", back_populates="corporate_actions")
