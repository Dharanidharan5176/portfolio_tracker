import csv
import io
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from backend.app.core.security import sanitize_csv_cell
from backend.app.db.models.portfolio import Portfolio
from backend.app.db.models.transaction import Transaction
from backend.app.db.models.instrument import Instrument
from backend.app.db.models.audit import DataQualityIssue
from backend.app.services.valuation_service import valuation_service
from backend.app.services.transaction_service import transaction_service, to_money

class ReportService:
    @staticmethod
    def generate_holdings_report(db: Session, portfolio_id: int) -> Dict[str, Any]:
        p = db.get(Portfolio, portfolio_id)
        holdings = valuation_service.get_portfolio_holdings(db, portfolio_id)
        return {
            "report_name": "Holdings Snapshot",
            "portfolio_name": p.name if p else "Unknown",
            "base_currency": p.base_currency if p else "INR",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "items": [h.to_dict() for h in holdings]
        }

    @staticmethod
    def holdings_to_csv(data: Dict[str, Any]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["# Local Portfolio Tracker - Holdings Snapshot Report"])
        writer.writerow([f"# Generated At: {data['generated_at']}"])
        writer.writerow([f"# Portfolio: {data['portfolio_name']} ({data['base_currency']})"])
        writer.writerow([])
        writer.writerow([
            "Symbol", "Display Name", "Asset Type", "Quantity", "Average Cost",
            "Cost Basis", "Latest Price", "Market Value", "Unrealized PnL", "PnL %", "Weight %", "Status"
        ])
        for it in data.get("items", []):
            writer.writerow([
                sanitize_csv_cell(it["symbol"]),
                sanitize_csv_cell(it["display_name"]),
                sanitize_csv_cell(it["asset_type"]),
                sanitize_csv_cell(it["quantity"]),
                sanitize_csv_cell(it["average_cost"]),
                sanitize_csv_cell(it["cost_basis"]),
                sanitize_csv_cell(it["latest_price"]),
                sanitize_csv_cell(it["market_value"]),
                sanitize_csv_cell(it["unrealized_pnl"]),
                sanitize_csv_cell(it["unrealized_pnl_pct"]),
                sanitize_csv_cell(it["weight"]),
                sanitize_csv_cell(it["quality_status"]),
            ])
        return output.getvalue()

    @staticmethod
    def generate_transactions_report(db: Session, portfolio_id: int) -> Dict[str, Any]:
        p = db.get(Portfolio, portfolio_id)
        txs = db.scalars(
            select(Transaction)
            .where(Transaction.portfolio_id == portfolio_id)
            .order_by(Transaction.trade_date.desc(), Transaction.id.desc())
        ).all()

        items = []
        for t in txs:
            sym = t.instrument.canonical_symbol if t.instrument else "-"
            items.append({
                "id": t.id,
                "trade_date": t.trade_date.isoformat(),
                "type": t.type,
                "symbol": sym,
                "quantity": str(t.quantity) if t.quantity else "",
                "unit_price": str(t.unit_price) if t.unit_price else "",
                "gross_amount": str(t.gross_amount),
                "fee": str(t.fee),
                "tax": str(t.tax),
                "net_amount": str(t.net_amount),
                "currency": t.currency,
                "external_ref": t.external_ref or "",
                "notes": t.notes or "",
                "is_reversed": t.is_reversed
            })

        return {
            "report_name": "Transaction Ledger Audit",
            "portfolio_name": p.name if p else "Unknown",
            "base_currency": p.base_currency if p else "INR",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "items": items
        }

    @staticmethod
    def transactions_to_csv(data: Dict[str, Any]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["# Local Portfolio Tracker - Transaction Ledger Audit Report"])
        writer.writerow([f"# Generated At: {data['generated_at']}"])
        writer.writerow([f"# Portfolio: {data['portfolio_name']} ({data['base_currency']})"])
        writer.writerow([])
        writer.writerow([
            "ID", "Trade Date", "Type", "Symbol", "Quantity", "Unit Price",
            "Gross Amount", "Fee", "Tax", "Net Amount", "Currency", "External Ref", "Notes", "Is Reversed"
        ])
        for it in data.get("items", []):
            writer.writerow([
                sanitize_csv_cell(it["id"]),
                sanitize_csv_cell(it["trade_date"]),
                sanitize_csv_cell(it["type"]),
                sanitize_csv_cell(it["symbol"]),
                sanitize_csv_cell(it["quantity"]),
                sanitize_csv_cell(it["unit_price"]),
                sanitize_csv_cell(it["gross_amount"]),
                sanitize_csv_cell(it["fee"]),
                sanitize_csv_cell(it["tax"]),
                sanitize_csv_cell(it["net_amount"]),
                sanitize_csv_cell(it["currency"]),
                sanitize_csv_cell(it["external_ref"]),
                sanitize_csv_cell(it["notes"]),
                sanitize_csv_cell(it["is_reversed"]),
            ])
        return output.getvalue()

    @staticmethod
    def generate_income_report(db: Session, portfolio_id: int) -> Dict[str, Any]:
        p = db.get(Portfolio, portfolio_id)
        txs = db.scalars(
            select(Transaction)
            .where(
                and_(
                    Transaction.portfolio_id == portfolio_id,
                    Transaction.type.in_(["DIVIDEND", "INTEREST", "FEE", "TAX_WITHHOLDING", "CASH_DEPOSIT", "CASH_WITHDRAWAL"]),
                    Transaction.is_reversed == False
                )
            )
            .order_by(Transaction.trade_date.desc(), Transaction.id.desc())
        ).all()

        total_dividends = Decimal("0.00")
        total_interest = Decimal("0.00")
        total_fees = Decimal("0.00")
        total_taxes = Decimal("0.00")

        items = []
        for t in txs:
            amt = to_money(t.gross_amount)
            if t.type == "DIVIDEND":
                total_dividends += amt
            elif t.type == "INTEREST":
                total_interest += amt
            elif t.type == "FEE":
                total_fees += amt
            elif t.type == "TAX_WITHHOLDING":
                total_taxes += amt

            sym = t.instrument.canonical_symbol if t.instrument else "-"
            items.append({
                "id": t.id,
                "trade_date": t.trade_date.isoformat(),
                "type": t.type,
                "symbol": sym,
                "gross_amount": str(t.gross_amount),
                "fee": str(t.fee),
                "tax": str(t.tax),
                "net_amount": str(t.net_amount),
                "currency": t.currency,
                "notes": t.notes or ""
            })

        net_income = total_dividends + total_interest - total_fees - total_taxes

        return {
            "report_name": "Cash Flows & Income Summary",
            "portfolio_name": p.name if p else "Unknown",
            "base_currency": p.base_currency if p else "INR",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_net_income": str(net_income),
                "total_dividends": str(total_dividends),
                "total_interest": str(total_interest),
                "total_fees": str(total_fees),
                "total_taxes": str(total_taxes),
            },
            "items": items
        }

    @staticmethod
    def income_to_csv(data: Dict[str, Any]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["# Local Portfolio Tracker - Income & Cash Flows Report"])
        writer.writerow([f"# Generated At: {data['generated_at']}"])
        writer.writerow([f"# Portfolio: {data['portfolio_name']} ({data['base_currency']})"])
        sumry = data.get("summary", {})
        writer.writerow([f"# Net Income: {sumry.get('total_net_income', '0.00')}, Dividends: {sumry.get('total_dividends', '0.00')}, Interest: {sumry.get('total_interest', '0.00')}, Fees: {sumry.get('total_fees', '0.00')}, Taxes: {sumry.get('total_taxes', '0.00')}"])
        writer.writerow([])
        writer.writerow(["ID", "Trade Date", "Type", "Symbol", "Gross Amount", "Fee", "Tax", "Net Amount", "Currency", "Notes"])
        for it in data.get("items", []):
            writer.writerow([
                sanitize_csv_cell(it["id"]),
                sanitize_csv_cell(it["trade_date"]),
                sanitize_csv_cell(it["type"]),
                sanitize_csv_cell(it["symbol"]),
                sanitize_csv_cell(it["gross_amount"]),
                sanitize_csv_cell(it["fee"]),
                sanitize_csv_cell(it["tax"]),
                sanitize_csv_cell(it["net_amount"]),
                sanitize_csv_cell(it["currency"]),
                sanitize_csv_cell(it["notes"]),
            ])
        return output.getvalue()

    @staticmethod
    def generate_data_quality_report(db: Session, portfolio_id: int) -> Dict[str, Any]:
        p = db.get(Portfolio, portfolio_id)
        issues = db.scalars(
            select(DataQualityIssue)
            .order_by(DataQualityIssue.last_seen.desc())
        ).all()

        items = []
        for i in issues:
            items.append({
                "id": i.id,
                "issue_key": i.issue_key,
                "severity": i.severity,
                "category": i.category,
                "entity_type": i.entity_type or "",
                "entity_id": i.entity_id or "",
                "first_seen": i.first_seen.isoformat(),
                "last_seen": i.last_seen.isoformat(),
                "status": i.status,
                "details": i.details or "",
                "resolution_note": i.resolution_note or ""
            })

        return {
            "report_name": "Data Quality & Integrity Report",
            "portfolio_name": p.name if p else "All Portfolios",
            "base_currency": p.base_currency if p else "INR",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_issues": len(items),
            "open_issues": sum(1 for it in items if it["status"] == "open"),
            "items": items
        }

    @staticmethod
    def data_quality_to_csv(data: Dict[str, Any]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["# Local Portfolio Tracker - Data Quality & Integrity Report"])
        writer.writerow([f"# Generated At: {data['generated_at']}"])
        writer.writerow([f"# Open Issues: {data.get('open_issues', 0)} / Total: {data.get('total_issues', 0)}"])
        writer.writerow([])
        writer.writerow(["ID", "Severity", "Category", "Status", "Entity Type", "Entity ID", "First Seen", "Last Seen", "Details", "Resolution Note"])
        for it in data.get("items", []):
            writer.writerow([
                sanitize_csv_cell(it["id"]),
                sanitize_csv_cell(it["severity"]),
                sanitize_csv_cell(it["category"]),
                sanitize_csv_cell(it["status"]),
                sanitize_csv_cell(it["entity_type"]),
                sanitize_csv_cell(it["entity_id"]),
                sanitize_csv_cell(it["first_seen"]),
                sanitize_csv_cell(it["last_seen"]),
                sanitize_csv_cell(it["details"]),
                sanitize_csv_cell(it["resolution_note"]),
            ])
        return output.getvalue()

report_service = ReportService()
