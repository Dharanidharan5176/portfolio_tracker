from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from backend.app.db.models.portfolio import Portfolio
from backend.app.db.models.account import Account
from backend.app.db.models.instrument import Instrument
from backend.app.db.models.transaction import Transaction
from backend.app.db.models.market_data import PriceObservation
from backend.app.db.models.audit import DataQualityIssue, Notification
from backend.app.services.valuation_service import valuation_service, STALE_PRICE_DAYS_THRESHOLD
from backend.app.services.transaction_service import transaction_service
from backend.app.services.audit_service import audit_service

class DataQualityService:
    @staticmethod
    def run_all_checks(db: Session, portfolio_id: Optional[int] = None) -> List[DataQualityIssue]:
        portfolios = [db.get(Portfolio, portfolio_id)] if portfolio_id else db.scalars(select(Portfolio).where(Portfolio.status == "active")).all()
        detected_issues: List[DataQualityIssue] = []

        now = datetime.now(timezone.utc)

        for p in portfolios:
            if not p:
                continue

            # 1. Check Cash Integrity (negative cash balances)
            accounts = db.scalars(select(Account).where(Account.portfolio_id == p.id, Account.status == "active")).all()
            for acc in accounts:
                cash = transaction_service.get_account_cash(db, acc.id)
                if cash < Decimal("0.00"):
                    issue = DataQualityService.record_or_update_issue(
                        db,
                        issue_key=f"neg_cash_acc_{acc.id}",
                        severity="error",
                        category="negative_cash",
                        entity_type="account",
                        entity_id=acc.id,
                        details=f"Account '{acc.name}' has unexplained negative cash balance: {cash} {acc.currency}. Deposit funds or correct ledger entries."
                    )
                    detected_issues.append(issue)

            # 2. Check Holdings: Missing or Stale Prices
            holdings = valuation_service.get_portfolio_holdings(db, p.id)
            for h in holdings:
                if h.quality_status == "missing_price":
                    issue = DataQualityService.record_or_update_issue(
                        db,
                        issue_key=f"missing_price_inst_{h.instrument_id}",
                        severity="error",
                        category="missing_price",
                        entity_type="instrument",
                        entity_id=h.instrument_id,
                        details=f"Instrument '{h.symbol}' held in '{p.name}' ({h.quantity} units) has no price observation. Valuation is incomplete."
                    )
                    detected_issues.append(issue)
                elif h.quality_status == "stale":
                    issue = DataQualityService.record_or_update_issue(
                        db,
                        issue_key=f"stale_price_inst_{h.instrument_id}",
                        severity="warning",
                        category="stale_price",
                        entity_type="instrument",
                        entity_id=h.instrument_id,
                        details=f"Instrument '{h.symbol}' price observation is over {STALE_PRICE_DAYS_THRESHOLD} days old. Valuation may be outdated."
                    )
                    detected_issues.append(issue)

            # 3. Check for Duplicate Transactions (same date, symbol, account, quantity, amount)
            txs = db.scalars(select(Transaction).where(Transaction.portfolio_id == p.id, Transaction.is_reversed == False)).all()
            fingerprints: Dict[str, List[int]] = {}
            for t in txs:
                fp = f"{t.trade_date}_{t.account_id}_{t.instrument_id}_{t.type}_{t.quantity}_{t.gross_amount}"
                fingerprints.setdefault(fp, []).append(t.id)

            for fp, tx_ids in fingerprints.items():
                if len(tx_ids) > 1:
                    issue = DataQualityService.record_or_update_issue(
                        db,
                        issue_key=f"dup_tx_{'_'.join(map(str, tx_ids))}",
                        severity="warning",
                        category="duplicate_txn",
                        entity_type="transaction",
                        entity_id=tx_ids[0],
                        details=f"Potential duplicate transactions detected: #{', #'.join(map(str, tx_ids))} share identical date, type, quantity and amount."
                    )
                    detected_issues.append(issue)

        db.commit()
        return detected_issues

    @staticmethod
    def record_or_update_issue(
        db: Session,
        issue_key: str,
        severity: str,
        category: str,
        entity_type: str,
        entity_id: Optional[int],
        details: str
    ) -> DataQualityIssue:
        now = datetime.now(timezone.utc)
        existing = db.scalar(select(DataQualityIssue).where(DataQualityIssue.issue_key == issue_key))
        if existing:
            existing.last_seen = now
            existing.details = details
            if existing.status == "resolved":
                existing.status = "open" # Re-open if problem re-detected
            db.flush()
            return existing
        else:
            issue = DataQualityIssue(
                issue_key=issue_key,
                severity=severity,
                category=category,
                entity_type=entity_type,
                entity_id=entity_id,
                first_seen=now,
                last_seen=now,
                status="open",
                details=details
            )
            db.add(issue)
            db.flush()

            # Create in-app notification
            notif = Notification(
                dedupe_key=f"notif_{issue_key}",
                category=category,
                severity=severity,
                title=f"Data Issue: {category.replace('_', ' ').title()}",
                message=details,
                related_entity_type=entity_type,
                related_entity_id=entity_id,
                status="unread",
                created_at=now
            )
            db.add(notif)
            db.flush()
            return issue

    @staticmethod
    def resolve_issue(db: Session, issue_id: int, reason: str) -> DataQualityIssue:
        issue = db.get(DataQualityIssue, issue_id)
        if not issue:
            from backend.app.core.errors import NotFoundError
            raise NotFoundError(f"Data quality issue #{issue_id} not found.")

        issue.status = "resolved"
        issue.resolution_note = reason
        audit_service.log(
            db,
            action="RESOLVE_DATA_QUALITY_ISSUE",
            entity_type="data_quality_issue",
            entity_id=issue.id,
            reason=reason,
            after_state={"issue_key": issue.issue_key, "status": "resolved"}
        )
        db.commit()
        db.refresh(issue)
        return issue

data_quality_service = DataQualityService()
