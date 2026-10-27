from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from backend.app.providers.base import MarketDataProvider, PriceRecord, FXRecord, ProviderHealthStatus
from backend.app.db.models.instrument import Instrument
from backend.app.db.models.market_data import PriceObservation, FXObservation

class ManualCSVProvider(MarketDataProvider):
    def __init__(self, db: Session):
        self.db = db

    def get_latest_prices(self, symbols: List[str]) -> List[PriceRecord]:
        clean_symbols = [s.strip().upper() for s in symbols]
        records: List[PriceRecord] = []
        for sym in clean_symbols:
            inst = self.db.scalar(select(Instrument).where(Instrument.canonical_symbol == sym))
            if not inst:
                continue
            obs = self.db.scalar(
                select(PriceObservation)
                .where(PriceObservation.instrument_id == inst.id)
                .order_by(PriceObservation.observed_at.desc())
            )
            if obs:
                records.append(PriceRecord(
                    symbol=sym,
                    observed_at=obs.observed_at,
                    price=obs.price,
                    currency=obs.currency,
                    provider=obs.provider,
                    quality_status=obs.quality_status
                ))
        return records

    def get_historical_prices(self, symbol: str, start_date: date, end_date: date) -> List[PriceRecord]:
        clean_sym = symbol.strip().upper()
        inst = self.db.scalar(select(Instrument).where(Instrument.canonical_symbol == clean_sym))
        if not inst:
            return []
        
        start_dt = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        obss = self.db.scalars(
            select(PriceObservation)
            .where(
                PriceObservation.instrument_id == inst.id,
                PriceObservation.observed_at >= start_dt,
                PriceObservation.observed_at <= end_dt
            )
            .order_by(PriceObservation.observed_at.asc())
        ).all()
        
        return [
            PriceRecord(
                symbol=clean_sym,
                observed_at=obs.observed_at,
                price=obs.price,
                currency=obs.currency,
                provider=obs.provider,
                quality_status=obs.quality_status
            )
            for obs in obss
        ]

    def get_fx_rates(self, pairs: List[Tuple[str, str]], dates: List[date]) -> List[FXRecord]:
        records: List[FXRecord] = []
        for base, quote in pairs:
            obss = self.db.scalars(
                select(FXObservation).where(
                    FXObservation.base_currency == base.upper(),
                    FXObservation.quote_currency == quote.upper()
                ).order_by(FXObservation.observed_at.desc())
            ).all()
            for obs in obss:
                records.append(FXRecord(
                    base_currency=obs.base_currency,
                    quote_currency=obs.quote_currency,
                    observed_at=obs.observed_at,
                    rate=obs.rate,
                    provider=obs.provider,
                    quality_status=obs.quality_status
                ))
        return records

    def get_provider_health(self) -> ProviderHealthStatus:
        latest = self.db.scalar(select(PriceObservation).order_by(PriceObservation.observed_at.desc()))
        return ProviderHealthStatus(
            provider_name="manual_csv",
            is_available=True,
            status_message="Offline local file & manual price entry active.",
            last_sync=latest.observed_at if latest else None
        )
