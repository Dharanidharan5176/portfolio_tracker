import csv
import io
from datetime import datetime, date, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.core.security import sanitize_csv_cell
from backend.app.db.models.portfolio import Portfolio
from backend.app.db.models.transaction import Transaction
from backend.app.db.models.instrument import Instrument
from backend.app.db.models.audit import DataQualityIssue
from backend.app.services.valuation_service import valuation_service
from backend.app.services.transaction_service import transaction_service

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

report_service = ReportService()
