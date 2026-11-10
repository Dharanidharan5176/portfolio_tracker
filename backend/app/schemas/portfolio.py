from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class PortfolioBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    base_currency: str = Field("INR", min_length=3, max_length=3)
    timezone: str = Field("Asia/Kolkata")
    benchmark_symbol: Optional[str] = None
    notes: Optional[str] = None

class PortfolioCreate(PortfolioBase):
    pass

class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    base_currency: Optional[str] = None
    timezone: Optional[str] = None
    benchmark_symbol: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class PortfolioResponse(PortfolioBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

