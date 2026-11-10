from datetime import datetime, timezone
from sqlalchemy import Integer, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base

class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    canonical_symbol: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(50), default="equity", nullable=False) # 'equity', 'etf', 'mutual_fund', 'crypto', 'bond', 'cash'
    exchange: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quote_currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    isin: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    metadata_source: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    transactions = relationship("Transaction", back_populates="instrument")
    prices = relationship("PriceObservation", back_populates="instrument", cascade="all, delete-orphan")
    corporate_actions = relationship("CorporateAction", back_populates="instrument", cascade="all, delete-orphan")

