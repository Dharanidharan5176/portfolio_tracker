from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

class TransactionBase(BaseModel):
    portfolio_id: int
    account_id: int
    instrument_id: Optional[int] = None
    symbol: Optional[str] = None # Helper for creation
    type: str = Field(..., description="BUY, SELL, CASH_DEPOSIT, CASH_WITHDRAWAL, DIVIDEND, INTEREST, FEE, TAX_WITHHOLDING, SPLIT, TRANSFER_IN, TRANSFER_OUT, CORRECTION_REVERSAL")
    trade_date: date
    settlement_date: Optional[date] = None
    quantity: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    gross_amount: Optional[Decimal] = None
    fee: Decimal = Decimal("0.00")
    tax: Decimal = Decimal("0.00")
    currency: str = Field("INR", min_length=3, max_length=3)
    fx_rate: Decimal = Decimal("1.0000")
    external_ref: Optional[str] = None
    notes: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionPreview(BaseModel):
    trade_date: date
    type: str
    symbol: Optional[str]
    quantity: Optional[Decimal]
    unit_price: Optional[Decimal]
    gross_amount: Decimal
    fee: Decimal
    tax: Decimal
    net_cash_impact: Decimal
    estimated_cost_basis_impact: Decimal
    new_quantity_balance: Decimal
    warnings: List[str] = []

class TransactionResponse(BaseModel):
    id: int
    portfolio_id: int
    account_id: int
    instrument_id: Optional[int]
    symbol: Optional[str] = None
    type: str
    trade_date: date
    settlement_date: Optional[date]
    quantity: Optional[Decimal]
    unit_price: Optional[Decimal]
    gross_amount: Decimal
    fee: Decimal
    tax: Decimal
    net_amount: Decimal
    currency: str
    fx_rate: Decimal
    external_ref: Optional[str]
    source: str
    notes: Optional[str]
    correction_of_id: Optional[int]
    is_reversed: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

