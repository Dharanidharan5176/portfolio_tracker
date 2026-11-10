from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class AccountBase(BaseModel):
    portfolio_id: int
    name: str = Field(..., min_length=1, max_length=100)
    account_type: str = Field("brokerage", description="brokerage, bank, manual")
    institution_label: str = Field(..., min_length=1, max_length=100)
    currency: str = Field("INR", min_length=3, max_length=3)

class AccountCreate(AccountBase):
    pass

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    account_type: Optional[str] = None
    institution_label: Optional[str] = None
    status: Optional[str] = None

class AccountResponse(AccountBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

