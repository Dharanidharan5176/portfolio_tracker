from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from backend.app.db.models.portfolio import Portfolio
from backend.app.db.models.transaction import Transaction
from backend.app.services.valuation_service import valuation_service
from backend.app.services.transaction_service import to_money

class PerformanceService:
    @staticmethod
    def calculate_twr(
        db: Session,
        portfolio_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Calculates Time-Weighted Return (TWR) by segmenting periods bounded by external cash flows.
        """
        portfolio = db.get(Portfolio, portfolio_id)
        if not portfolio:
            return {"status": "error", "message": "Portfolio not found"}

        # Get all external cash flow dates (CASH_DEPOSIT, CASH_WITHDRAWAL)
        cash_tx_query = select(Transaction).where(
            Transaction.portfolio_id == portfolio_id,
            Transaction.type.in_(["CASH_DEPOSIT", "CASH_WITHDRAWAL"]),
            Transaction.is_reversed == False
        )
        if start_date:
            cash_tx_query = cash_tx_query.where(Transaction.trade_date >= start_date)
        if end_date:
            cash_tx_query = cash_tx_query.where(Transaction.trade_date <= end_date)

        cash_txs = db.scalars(cash_tx_query.order_by(Transaction.trade_date.asc())).all()

        # Check all transaction dates
        all_tx_dates = db.scalars(
            select(Transaction.trade_date)
            .where(Transaction.portfolio_id == portfolio_id, Transaction.is_reversed == False)
            .distinct()
            .order_by(Transaction.trade_date.asc())
        ).all()

        if not all_tx_dates:
            return {
                "status": "insufficient_data",
                "message": "No transaction history recorded for performance evaluation.",
                "twr_pct": None,
                "sub_periods": []
            }

        effective_start = start_date or all_tx_dates[0]
        effective_end = end_date or date.today()

        if effective_start >= effective_end:
            return {
                "status": "insufficient_data",
                "message": "Start date must precede end date for multi-period returns.",
                "twr_pct": None,
                "sub_periods": []
            }

        # Build sub-periods
        cf_dates = sorted(list(set([t.trade_date for t in cash_txs if effective_start <= t.trade_date <= effective_end])))
        boundary_dates = sorted(list(set([effective_start] + cf_dates + [effective_end])))

        sub_periods = []
        compound_factor = Decimal("1.000000")

        for idx in range(len(boundary_dates) - 1):
            p_start = boundary_dates[idx]
            p_end = boundary_dates[idx + 1]

            val_start = Decimal(valuation_service.get_portfolio_valuation_summary(db, portfolio_id, as_of=p_start)["total_portfolio_value"])
            val_end = Decimal(valuation_service.get_portfolio_valuation_summary(db, portfolio_id, as_of=p_end)["total_portfolio_value"])

            # Sum net cash flows occurring on p_end
            net_cf = sum(
                (t.net_amount for t in cash_txs if t.trade_date == p_end),
                Decimal("0.00")
            )

            # R_i = (val_end - net_cf) / val_start - 1 (if val_start > 0)
            if val_start > Decimal("0.00"):
                r_i = ((val_end - net_cf) / val_start) - Decimal("1.000000")
                sub_periods.append({
                    "start": p_start.isoformat(),
                    "end": p_end.isoformat(),
                    "start_value": str(val_start),
                    "end_value": str(val_end),
                    "cash_flow": str(net_cf),
                    "return_pct": str((r_i * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
                })
                compound_factor *= (Decimal("1.000000") + r_i)
            elif (val_end - net_cf) > Decimal("0.00") and net_cf > Decimal("0.00"):
                # Initial capital deployment
                sub_periods.append({
                    "start": p_start.isoformat(),
                    "end": p_end.isoformat(),
                    "start_value": str(val_start),
                    "end_value": str(val_end),
                    "cash_flow": str(net_cf),
                    "return_pct": "0.00"
                })

        final_twr = ((compound_factor - Decimal("1.000000")) * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return {
            "status": "valid",
            "method": "TWR (Daily valuation / cash-flow boundary sub-periods)",
            "base_currency": portfolio.base_currency,
            "start_date": effective_start.isoformat(),
            "end_date": effective_end.isoformat(),
            "twr_pct": str(final_twr),
            "sub_periods": sub_periods,
            "warnings": []
        }

    @staticmethod
    def calculate_drawdown(
        db: Session,
        portfolio_id: int
    ) -> Dict[str, Any]:
        """
        Calculates drawdown series from all historical transaction dates.
        """
        all_tx_dates = db.scalars(
            select(Transaction.trade_date)
            .where(Transaction.portfolio_id == portfolio_id, Transaction.is_reversed == False)
            .distinct()
            .order_by(Transaction.trade_date.asc())
        ).all()

        if len(all_tx_dates) < 2:
            return {"max_drawdown_pct": "0.00", "series": []}

        series = []
        peak = Decimal("0.00")
        max_dd = Decimal("0.00")

        for d in all_tx_dates:
            val = Decimal(valuation_service.get_portfolio_valuation_summary(db, portfolio_id, as_of=d)["total_portfolio_value"])
            if val > peak:
                peak = val
            dd = Decimal("0.00")
            if peak > Decimal("0.00"):
                dd = (((val - peak) / peak) * Decimal("100.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if dd < max_dd:
                max_dd = dd

            series.append({
                "date": d.isoformat(),
                "portfolio_value": str(val),
                "peak_value": str(peak),
                "drawdown_pct": str(dd)
            })

        return {
            "max_drawdown_pct": str(max_dd),
            "series": series
        }

performance_service = PerformanceService()
