from abc import ABC, abstractmethod
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from pydantic import BaseModel

class PriceRecord(BaseModel):
    symbol: str
    observed_at: datetime
    price: Decimal
    currency: str
    provider: str
    quality_status: str = "valid"
    source_record_id: Optional[str] = None

class FXRecord(BaseModel):
    base_currency: str
    quote_currency: str
    observed_at: datetime
    rate: Decimal
    provider: str
    quality_status: str = "valid"

class ProviderHealthStatus(BaseModel):
    provider_name: str
    is_available: bool
    status_message: str
    last_sync: Optional[datetime] = None

class MarketDataProvider(ABC):
    @abstractmethod
    def get_latest_prices(self, symbols: List[str]) -> List[PriceRecord]:
        pass

    @abstractmethod
    def get_historical_prices(self, symbol: str, start_date: date, end_date: date) -> List[PriceRecord]:
        pass

    @abstractmethod
    def get_fx_rates(self, pairs: List[Tuple[str, str]], dates: List[date]) -> List[FXRecord]:
        pass

    @abstractmethod
    def get_provider_health(self) -> ProviderHealthStatus:
        pass

