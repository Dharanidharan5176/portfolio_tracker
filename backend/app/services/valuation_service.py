from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from backend.app.db.models.portfolio import Portfolio
from backend.app.db.models.account import Account
from backend.app.db.models.instrument import Instrument
from backend.app.db.models.transaction import Transaction
from backend.app.db.models.market_data import PriceObservation, FXObservation
from backend.app.services.transaction_service import transaction_service, to_money, to_qty

STALE_PRICE_DAYS_THRESHOLD = 5

class HoldingValuation:
    def __init__(
        self,
        instrument_id: int,
        symbol: str,
        display_name: str,
        asset_type: str,
        quantity: Decimal,
        average_cost: Decimal,
        cost_basis: Decimal,
        latest_price: Optional[Decimal],
        price_date: Optional[datetime],
        market_value: Optional[Decimal],
        unrealized_pnl: Optional[Decimal],
        unrealized_pnl_pct: Optional[Decimal],
        weight: Optional[Decimal],
        currency: str,
        quality_status: str,
        is_manual_override: bool = False,
        warnings: Optional[List[str]] = None
    ):
        self.instrument_id = instrument_id
        self.symbol = symbol
        self.display_name = display_name
        self.asset_type = asset_type
        self.quantity = quantity
        self.average_cost = average_cost
        self.cost_basis = cost_basis
        self.latest_price = latest_price
        self.price_date = price_date
        self.market_value = market_value
        self.unrealized_pnl = unrealized_pnl
        self.unrealized_pnl_pct = unrealized_pnl_pct
        self.weight = weight
        self.currency = currency
        self.quality_status = quality_status
        self.is_manual_override = is_manual_override
        self.warnings = warnings or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "symbol": self.symbol,
            "display_name": self.display_name,
            "asset_type": self.asset_type,
            "quantity": str(self.quantity),
            "average_cost": str(self.average_cost),
            "cost_basis": str(self.cost_basis),
            "latest_price": str(self.latest_price) if self.latest_price is not None else None,
            "price_date": self.price_date.isoformat() if self.price_date else None,
            "market_value": str(self.market_value) if self.market_value is not None else None,
            "unrealized_pnl": str(self.unrealized_pnl) if self.unrealized_pnl is not None else None,
            "unrealized_pnl_pct": str(self.unrealized_pnl_pct) if self.unrealized_pnl_pct is not None else None,
            "weight": str(self.weight) if self.weight is not None else "0.00",
            "currency": self.currency,
            "quality_status": self.quality_status,
            "is_manual_override": self.is_manual_override,
            "warnings": self.warnings
        }

class ValuationService:
    @staticmethod
    def get_portfolio_holdings(
        db: Session,
        portfolio_id: int,
        as_of: Optional[date] = None
    ) -> List[HoldingValuation]:
        portfolio = db.get(Portfolio, portfolio_id)
        if not portfolio:
            return []

        # Find all distinct instruments traded in this portfolio
        inst_ids = db.scalars(
            select(Transaction.instrument_id)
            .where(
                Transaction.portfolio_id == portfolio_id,
                Transaction.instrument_id.isnot(None),
                Transaction.is_reversed == False
            )
            .distinct()
        ).all()

        holdings: List[HoldingValuation] = []
        as_of_dt = datetime.combine(as_of or date.today(), datetime.max.time()).replace(tzinfo=timezone.utc)

        for i_id in inst_ids:
            if not i_id:
                continue
            inst = db.get(Instrument, i_id)
            if not inst:
                continue

            qty, cost_basis, avg_cost = transaction_service.get_current_position(
                db, portfolio_id, i_id, as_of=as_of
            )
            if qty <= Decimal("0.0000"):
                continue # Skip zero positions for current holdings

            # Find latest price observation on or before as_of
            obs = db.scalar(
                select(PriceObservation)
                .where(
                    PriceObservation.instrument_id == i_id,
                    PriceObservation.observed_at <= as_of_dt
                )
                .order_by(PriceObservation.observed_at.desc())
            )

            price: Optional[Decimal] = None
            price_date: Optional[datetime] = None
            quality = "valid"
            warnings = []
            is_override = False

            if not obs:
                quality = "missing_price"
                warnings.append("No price observation recorded.")
            else:
                price = obs.price
                price_date = obs.observed_at
                is_override = obs.is_manual_override
                # Check staleness
                obs_date = obs.observed_at.date() if isinstance(obs.observed_at, datetime) else obs.observed_at
                target_date = as_of or date.today()
                if (target_date - obs_date).days > STALE_PRICE_DAYS_THRESHOLD:
                    quality = "stale"
                    warnings.append(f"Price is stale ({(target_date - obs_date).days} days old).")

            # Currency / FX conversion
            fx_rate = Decimal("1.0000")
            if inst.quote_currency != portfolio.base_currency:
                fx = db.scalar(
                    select(FXObservation)
                    .where(
                        FXObservation.base_currency == inst.quote_currency,
                        FXObservation.quote_currency == portfolio.base_currency,
                        FXObservation.observed_at <= as_of_dt
                    )
                    .order_by(FXObservation.observed_at.desc())
                )
                if not fx:
                    quality = "missing_fx"
                    warnings.append(f"Missing FX rate {inst.quote_currency}->{portfolio.base_currency}.")
                    fx_rate = None
                else:
                    fx_rate = fx.rate

            market_val: Optional[Decimal] = None
            unrealized: Optional[Decimal] = None
            unrealized_pct: Optional[Decimal] = None

            if price is not None and fx_rate is not None:
                market_val = to_money(qty * price * fx_rate)
                unrealized = to_money(market_val - cost_basis)
                if cost_basis > Decimal("0.00"):
                    unrealized_pct = ((unrealized / cost_basis) * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                else:
                    unrealized_pct = Decimal("0.00")

            holdings.append(HoldingValuation(
                instrument_id=inst.id,
                symbol=inst.canonical_symbol,
                display_name=inst.display_name,
                asset_type=inst.asset_type,
                quantity=qty,
                average_cost=avg_cost,
                cost_basis=cost_basis,
                latest_price=price,
                price_date=price_date,
                market_value=market_val,
                unrealized_pnl=unrealized,
                unrealized_pnl_pct=unrealized_pct,
                weight=Decimal("0.00"), # Will compute after total
                currency=portfolio.base_currency,
                quality_status=quality,
                is_manual_override=is_override,
                warnings=warnings
            ))

        # Calculate total holdings market value
        total_mkt = sum((h.market_value for h in holdings if h.market_value is not None), Decimal("0.00"))
        if total_mkt > Decimal("0.00"):
            for h in holdings:
                if h.market_value is not None:
                    h.weight = ((h.market_value / total_mkt) * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return holdings

    @staticmethod
    def get_portfolio_valuation_summary(
        db: Session,
        portfolio_id: int,
        as_of: Optional[date] = None
    ) -> Dict[str, Any]:
        portfolio = db.get(Portfolio, portfolio_id)
        if not portfolio:
            return {}

        holdings = ValuationService.get_portfolio_holdings(db, portfolio_id, as_of=as_of)

        total_holdings_value = sum((h.market_value for h in holdings if h.market_value is not None), Decimal("0.00"))
        total_cost_basis = sum((h.cost_basis for h in holdings), Decimal("0.00"))
        total_unrealized_pnl = sum((h.unrealized_pnl for h in holdings if h.unrealized_pnl is not None), Decimal("0.00"))

        # Cash balance across accounts in portfolio
        accounts = db.scalars(select(Account).where(Account.portfolio_id == portfolio_id, Account.status == "active")).all()
        total_cash = sum((transaction_service.get_account_cash(db, acc.id, as_of=as_of) for acc in accounts), Decimal("0.00"))

        total_portfolio_value = total_holdings_value + total_cash

        total_unrealized_pct = Decimal("0.00")
        if total_cost_basis > Decimal("0.00"):
            total_unrealized_pct = ((total_unrealized_pnl / total_cost_basis) * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Realized P&L from historical sells
        # Query SELL transactions
        sells = db.scalars(
            select(Transaction).where(
                Transaction.portfolio_id == portfolio_id,
                Transaction.type == "SELL",
                Transaction.is_reversed == False
            )
        ).all()
        # Approximate or detailed realized P&L sum
        total_realized_pnl = Decimal("0.00")
        for s in sells:
            # Net proceeds minus average cost allocation
            cur_qty, cur_cost, cur_avg = transaction_service.get_current_position(db, portfolio_id, s.instrument_id, as_of=s.trade_date)
            cost_of_shares = (to_qty(s.quantity) * cur_avg).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            pnl = to_money(s.net_amount - cost_of_shares)
            total_realized_pnl += pnl

        # Overall freshness status
        has_missing = any(h.quality_status == "missing_price" for h in holdings)
        has_stale = any(h.quality_status == "stale" for h in holdings)
        if has_missing:
            freshness = "Valuation incomplete (missing prices)"
        elif has_stale:
            freshness = "Warning: Some prices are stale"
        elif len(holdings) == 0:
            freshness = "No active holdings"
        else:
            freshness = "Prices up to date"

        return {
            "portfolio_id": portfolio_id,
            "portfolio_name": portfolio.name,
            "base_currency": portfolio.base_currency,
            "as_of": (as_of or date.today()).isoformat(),
            "total_portfolio_value": str(total_portfolio_value),
            "holdings_market_value": str(total_holdings_value),
            "invested_cost_basis": str(total_cost_basis),
            "unrealized_pnl": str(total_unrealized_pnl),
            "unrealized_pnl_pct": str(total_unrealized_pct),
            "realized_pnl": str(total_realized_pnl),
            "cash_balance": str(total_cash),
            "data_freshness": freshness,
            "holdings_count": len(holdings),
            "holdings": [h.to_dict() for h in holdings]
        }

valuation_service = ValuationService()
