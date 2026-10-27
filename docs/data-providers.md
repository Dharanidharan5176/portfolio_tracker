# Local Portfolio Tracker — Market Data Providers

## 1. Provider Abstraction
All price and FX observation ingestion occurs via the `MarketDataProvider` abstract base class located in `backend/app/providers/base.py`.

```python
class MarketDataProvider(ABC):
    @abstractmethod
    async def get_latest_prices(self, symbols: list[str]) -> list[PriceRecord]: ...

    @abstractmethod
    async def get_historical_prices(self, symbol: str, start_date: date, end_date: date) -> list[PriceRecord]: ...

    @abstractmethod
    async def get_fx_rates(self, pairs: list[tuple[str, str]], dates: list[date]) -> list[FXRecord]: ...

    @abstractmethod
    async def get_provider_health(self) -> ProviderHealthStatus: ...
```

## 2. Supported Providers
1. **Manual CSV (`manual_csv`) [Default]**:
   - Requires zero internet connectivity, zero API keys, and zero telemetry.
   - Prices are imported via CSV files or entered manually through the UI.
   - Price observation status marked with `provider='manual_csv'`.
2. **Pluggable Web Providers (Future / Optional)**:
   - When configured, API keys are read strictly from environment variables (e.g. `MARKET_DATA_API_KEY`), never stored in plaintext in the database.
   - External requests are rate-limited with exponential backoff and strictly logged (redacting secrets).
