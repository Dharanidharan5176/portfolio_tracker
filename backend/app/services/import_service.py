import csv
import hashlib
import io
import json
from datetime import datetime, date, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from backend.app.core.config import settings
from backend.app.core.errors import AppError, ValidationError
from backend.app.db.models.import_batch import ImportBatch
from backend.app.db.models.transaction import Transaction
from backend.app.db.models.instrument import Instrument
from backend.app.db.models.market_data import PriceObservation
from backend.app.schemas.import_schema import CSVPreviewResponse, CSVPreviewRow, ImportConfirmRequest
from backend.app.schemas.transaction import TransactionCreate
from backend.app.services.transaction_service import transaction_service, to_money, to_qty
from backend.app.services.audit_service import audit_service

STANDARD_TXN_MAPPING = {
    "date": "trade_date",
    "trade_date": "trade_date",
    "transaction_date": "trade_date",
    "settlement_date": "settlement_date",
    "symbol": "symbol",
    "ticker": "symbol",
    "type": "type",
    "transaction_type": "type",
    "action": "type",
    "quantity": "quantity",
    "shares": "quantity",
    "qty": "quantity",
    "price": "unit_price",
    "unit_price": "unit_price",
    "rate": "unit_price",
    "amount": "gross_amount",
    "gross_amount": "gross_amount",
    "fee": "fee",
    "fees": "fee",
    "tax": "tax",
    "taxes": "tax",
    "currency": "currency",
    "fx_rate": "fx_rate",
    "ref": "external_ref",
    "external_ref": "external_ref",
    "external_reference": "external_ref",
    "notes": "notes",
    "description": "notes"
}

STANDARD_PRICE_MAPPING = {
    "symbol": "symbol",
    "ticker": "symbol",
    "date": "price_date",
    "price_date": "price_date",
    "price": "close_price",
    "close_price": "close_price",
    "close": "close_price",
    "currency": "currency",
    "source": "source",
    "provider": "source"
}

class ImportService:
    @staticmethod
    def compute_hash(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def auto_detect_mapping(headers: List[str], source_type: str) -> Dict[str, str]:
        ref_dict = STANDARD_TXN_MAPPING if source_type == "transactions" else STANDARD_PRICE_MAPPING
        mapping = {}
        for h in headers:
            clean = h.strip().lower().replace(" ", "_")
            if clean in ref_dict:
                mapping[h] = ref_dict[clean]
        return mapping

    @staticmethod
    def parse_preview(
        content: str,
        filename: str,
        source_type: str = "transactions",
        user_mapping: Optional[Dict[str, str]] = None
    ) -> CSVPreviewResponse:
        file_bytes = content.encode("utf-8")
        file_hash = ImportService.compute_hash(file_bytes)

        # Detect delimiter
        sample = content[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample)
            delimiter = dialect.delimiter
        except Exception:
            delimiter = ","

        reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
        raw_headers = reader.fieldnames or []
        mapping = user_mapping or ImportService.auto_detect_mapping(raw_headers, source_type)

        preview_rows: List[CSVPreviewRow] = []
        valid_count = 0
        error_count = 0

        for idx, row in enumerate(reader, start=1):
            row_errors: List[str] = []
            row_warnings: List[str] = []
            parsed_data: Dict[str, Any] = {}

            # Map fields
            for raw_col, val in row.items():
                target_field = mapping.get(raw_col)
                if target_field:
                    parsed_data[target_field] = (val or "").strip()

            if source_type == "transactions":
                # Validate date
                raw_date = parsed_data.get("trade_date")
                if not raw_date:
                    row_errors.append("Missing required transaction date.")
                else:
                    try:
                        parsed_data["trade_date"] = date.fromisoformat(raw_date)
                    except ValueError:
                        row_errors.append(f"Invalid date format '{raw_date}'. Use YYYY-MM-DD.")

                # Validate type
                raw_type = (parsed_data.get("type") or "").upper()
                valid_types = {"BUY", "SELL", "CASH_DEPOSIT", "CASH_WITHDRAWAL", "DIVIDEND", "INTEREST", "FEE", "TAX_WITHHOLDING", "SPLIT"}
                if not raw_type:
                    row_errors.append("Missing transaction type.")
                elif raw_type not in valid_types:
                    row_errors.append(f"Unknown type '{raw_type}'. Supported: {', '.join(sorted(valid_types))}")
                else:
                    parsed_data["type"] = raw_type

                # Validate symbol
                if raw_type in ("BUY", "SELL", "SPLIT") and not parsed_data.get("symbol"):
                    row_errors.append(f"Symbol is required for {raw_type} transactions.")

                # Validate numeric fields
                for num_field in ["quantity", "unit_price", "gross_amount", "fee", "tax"]:
                    val_str = parsed_data.get(num_field)
                    if val_str:
                        try:
                            parsed_data[num_field] = Decimal(val_str)
                        except InvalidOperation:
                            row_errors.append(f"Field '{num_field}' contains unparseable number '{val_str}'.")

            else: # prices
                if not parsed_data.get("symbol"):
                    row_errors.append("Symbol is required.")
                raw_date = parsed_data.get("price_date")
                if not raw_date:
                    row_errors.append("Missing price_date.")
                else:
                    try:
                        parsed_data["price_date"] = date.fromisoformat(raw_date)
                    except ValueError:
                        row_errors.append(f"Invalid price date '{raw_date}'. Use YYYY-MM-DD.")
                raw_price = parsed_data.get("close_price")
                if not raw_price:
                    row_errors.append("Missing close_price.")
                else:
                    try:
                        parsed_data["close_price"] = Decimal(raw_price)
                    except InvalidOperation:
                        row_errors.append(f"Invalid price number '{raw_price}'.")

            is_valid = len(row_errors) == 0
            if is_valid:
                valid_count += 1
            else:
                error_count += 1

            preview_rows.append(CSVPreviewRow(
                row_number=idx,
                raw_data=dict(row),
                parsed_data=parsed_data if is_valid else None,
                is_valid=is_valid,
                is_duplicate=False,
                errors=row_errors,
                warnings=row_warnings
            ))

        return CSVPreviewResponse(
            file_name=filename,
            file_hash=file_hash,
            source_type=source_type,
            detected_headers=raw_headers,
            suggested_mapping=mapping,
            total_rows=len(preview_rows),
            valid_rows_count=valid_count,
            error_rows_count=error_count,
            duplicate_rows_count=0,
            rows=preview_rows
        )

    @staticmethod
    def confirm_import(
        db: Session,
        content: str,
        filename: str,
        req: ImportConfirmRequest
    ) -> ImportBatch:
        preview = ImportService.parse_preview(
            content=content,
            filename=filename,
            source_type=req.source_type,
            user_mapping=req.column_mapping
        )

        if req.policy == "atomic" and preview.error_rows_count > 0:
            raise ValidationError(
                f"Atomic import rejected: {preview.error_rows_count} rows have validation errors. Fix errors or choose 'skip_errors' policy.",
                details={"errors_count": preview.error_rows_count}
            )

        # Create batch record
        batch = ImportBatch(
            file_name=filename,
            file_hash=preview.file_hash,
            source_type=req.source_type,
            mapping_json=json.dumps(req.column_mapping),
            started_at=datetime.now(timezone.utc),
            status="pending",
            total_rows=preview.total_rows,
            imported_rows=0,
            failed_rows=0
        )
        db.add(batch)
        db.flush()

        imported_count = 0
        failed_count = 0
        error_report_rows = []

        if req.source_type == "transactions":
            for row in preview.rows:
                if not row.is_valid:
                    failed_count += 1
                    error_report_rows.append({
                        "row": row.row_number,
                        "errors": "; ".join(row.errors),
                        "raw_data": str(row.raw_data)
                    })
                    continue

                p = row.parsed_data
                # Duplicate check: external_ref or exact match
                ext_ref = p.get("external_ref")
                if ext_ref:
                    existing_tx = db.scalar(
                        select(Transaction).where(
                            Transaction.portfolio_id == req.portfolio_id,
                            Transaction.external_ref == ext_ref
                        )
                    )
                    if existing_tx:
                        if req.skip_duplicates:
                            continue
                        else:
                            raise ValidationError(f"Duplicate transaction with external_ref '{ext_ref}' found at row {row.row_number}.")

                try:
                    tx_create = TransactionCreate(
                        portfolio_id=req.portfolio_id,
                        account_id=req.account_id,
                        symbol=p.get("symbol"),
                        type=p.get("type"),
                        trade_date=p.get("trade_date"),
                        settlement_date=p.get("settlement_date"),
                        quantity=p.get("quantity"),
                        unit_price=p.get("unit_price"),
                        gross_amount=p.get("gross_amount"),
                        fee=p.get("fee", Decimal("0.00")),
                        tax=p.get("tax", Decimal("0.00")),
                        currency=p.get("currency") or "INR",
                        fx_rate=p.get("fx_rate", Decimal("1.0000")),
                        external_ref=ext_ref,
                        notes=p.get("notes")
                    )
                    tx = transaction_service.create_transaction(db, tx_create)
                    tx.import_batch_id = batch.id
                    tx.source = "csv_import"
                    imported_count += 1
                except Exception as ex:
                    failed_count += 1
                    error_report_rows.append({"row": row.row_number, "errors": str(ex), "raw_data": str(row.raw_data)})
                    if req.policy == "atomic":
                        db.rollback()
                        raise ValidationError(f"Import failed at row {row.row_number}: {ex}")

        else: # prices import
            for row in preview.rows:
                if not row.is_valid:
                    failed_count += 1
                    error_report_rows.append({"row": row.row_number, "errors": "; ".join(row.errors), "raw_data": str(row.raw_data)})
                    continue

                p = row.parsed_data
                try:
                    inst = transaction_service.get_or_create_instrument(
                        db, p["symbol"], quote_currency=p.get("currency", "INR")
                    )
                    obs_dt = datetime.combine(p["price_date"], datetime.min.time()).replace(tzinfo=timezone.utc)
                    obs = PriceObservation(
                        instrument_id=inst.id,
                        observed_at=obs_dt,
                        price=p["close_price"],
                        currency=p.get("currency", "INR").upper(),
                        provider=p.get("source") or "manual_csv",
                        quality_status="valid",
                        is_manual_override=False,
                        imported_at=datetime.now(timezone.utc)
                    )
                    db.add(obs)
                    imported_count += 1
                except Exception as ex:
                    failed_count += 1
                    error_report_rows.append({"row": row.row_number, "errors": str(ex), "raw_data": str(row.raw_data)})
                    if req.policy == "atomic":
                        db.rollback()
                        raise ValidationError(f"Price import failed at row {row.row_number}: {ex}")

        batch.imported_rows = imported_count
        batch.failed_rows = failed_count
        batch.status = "completed" if failed_count == 0 else ("partial" if imported_count > 0 else "failed")
        batch.completed_at = datetime.now(timezone.utc)

        # Write error report if failures
        if error_report_rows:
            report_name = f"error_report_batch_{batch.id}.csv"
            report_path = settings.data_path / "imports" / report_name
            with open(report_path, "w", newline="", encoding="utf-8") as rf:
                writer = csv.DictWriter(rf, fieldnames=["row", "errors", "raw_data"])
                writer.writeheader()
                writer.writerows(error_report_rows)
            batch.error_report_path = str(report_path)

        audit_service.log(
            db,
            action=f"IMPORT_{req.source_type.upper()}_CONFIRM",
            entity_type="import_batch",
            entity_id=batch.id,
            after_state={"imported": imported_count, "failed": failed_count, "status": batch.status}
        )

        db.commit()
        db.refresh(batch)
        return batch

import_service = ImportService()

