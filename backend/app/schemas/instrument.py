from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class InstrumentBase(BaseModel):
    canonical_symbol: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=150)
    asset_type: str = Field("equity", description="equity, etf, mutual_fund, crypto, bond, cash")
    exchange: Optional[str] = None
    quote_currency: str = Field("INR", min_length=3, max_length=3)
    isin: Optional[str] = None
    metadata_source: str = "manual"
    sector: Optional[str] = None

class InstrumentCreate(InstrumentBase):
    pass

class InstrumentResponse(InstrumentBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

