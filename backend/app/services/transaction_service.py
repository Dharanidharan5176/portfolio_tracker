from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from backend.app.db.models.portfolio import Portfolio
from backend.app.db.models.account import Account
from backend.app.db.models.instrument import Instrument
from backend.app.db.models.transaction import Transaction, CashLedgerEntry
from backend.app.schemas.transaction import TransactionCreate, TransactionPreview
from backend.app.core.errors import NotFoundError, ValidationError, LedgerIntegrityError
from backend.app.services.audit_service import audit_service

def to_money(val: Decimal | int | float | str) -> Decimal:
    if val is None:
        return Decimal("0.00")
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def to_qty(val: Decimal | int | float | str | None) -> Decimal:
    if val is None:
        return Decimal("0.0000")
    return Decimal(str(val)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

class TransactionService:
    @staticmethod
    def get_or_create_instrument(
        db: Session,
        symbol: str,
        display_name: Optional[str] = None,
        asset_type: str = "equity",
        quote_currency: str = "INR"
    ) -> Instrument:
        clean_sym = symbol.strip().upper()
        inst = db.scalar(select(Instrument).where(Instrument.canonical_symbol == clean_sym))
        if not inst:
            inst = Instrument(
                canonical_symbol=clean_sym,
                display_name=display_name or clean_sym,
                asset_type=asset_type,
                quote_currency=quote_currency.upper(),
                metadata_source="manual"
            )
            db.add(inst)
            db.flush()
        return inst

    @staticmethod
    def get_current_position(
        db: Session,
        portfolio_id: int,
        instrument_id: int,
        as_of: Optional[date] = None
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Calculates (quantity, cost_basis, average_cost) using Average Cost method.
        """
        query = select(Transaction).where(
            Transaction.portfolio_id == portfolio_id,
            Transaction.instrument_id == instrument_id,
            Transaction.is_reversed == False
        )
        if as_of:
            query = query.where(Transaction.trade_date <= as_of)
        query = query.order_by(Transaction.trade_date.asc(), Transaction.id.asc())

        txs = db.scalars(query).all()
        qty = Decimal("0.0000")
        total_cost = Decimal("0.00")

        for tx in txs:
            t_qty = to_qty(tx.quantity)
            t_fee = to_money(tx.fee)
            t_tax = to_money(tx.tax)
            t_gross = to_money(tx.gross_amount)

            if tx.type == "BUY":
                buy_cost = t_gross + t_fee + t_tax
                qty += t_qty
                total_cost += buy_cost
            elif tx.type == "SELL":
                if qty > 0:
                    avg_cost_unit = total_cost / qty
                    cost_of_sold = (t_qty * avg_cost_unit).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    qty -= t_qty
                    total_cost -= cost_of_sold
                    if qty <= 0:
                        qty = Decimal("0.0000")
                        total_cost = Decimal("0.00")
                else:
                    qty -= t_qty
            elif tx.type == "SPLIT":
                # If quantity specifies split multiplier ratio, e.g. 2 for 2:1
                if t_qty > 0:
                    qty = qty * t_qty
                    # total_cost remains unchanged

        avg_cost = (total_cost / qty).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP) if qty > 0 else Decimal("0.0000")
        return qty, total_cost, avg_cost

    @staticmethod
    def get_account_cash(
        db: Session,
        account_id: int,
        as_of: Optional[date] = None
    ) -> Decimal:
        """
        Calculates authoritative cash balance from CashLedgerEntries.
        """
        query = select(CashLedgerEntry).where(CashLedgerEntry.account_id == account_id)
        if as_of:
            query = query.where(CashLedgerEntry.effective_date <= as_of)
        
        entries = db.scalars(query).all()
        return sum((to_money(e.amount) for e in entries), Decimal("0.00"))

    @staticmethod
    def preview_transaction(db: Session, payload: TransactionCreate) -> TransactionPreview:
        txn_type = payload.type.upper()
        warnings: List[str] = []

        qty = to_qty(payload.quantity)
        unit_price = to_qty(payload.unit_price) if payload.unit_price is not None else None
        fee = to_money(payload.fee)
        tax = to_money(payload.tax)

        if payload.gross_amount is not None:
            gross = to_money(payload.gross_amount)
        elif unit_price is not None and qty > 0:
            gross = to_money(qty * unit_price)
        else:
            gross = Decimal("0.00")

        current_qty, current_cost, _ = (Decimal("0.0000"), Decimal("0.00"), Decimal("0.0000"))
        if payload.instrument_id:
            current_qty, current_cost, _ = TransactionService.get_current_position(
                db, payload.portfolio_id, payload.instrument_id, as_of=payload.trade_date
            )

        net_cash_impact = Decimal("0.00")
        cost_basis_impact = Decimal("0.00")
        new_quantity = current_qty

        if txn_type == "BUY":
            total_outlay = gross + fee + tax
            net_cash_impact = -total_outlay
            cost_basis_impact = total_outlay
            new_quantity = current_qty + qty
        elif txn_type == "SELL":
            net_proceeds = gross - fee - tax
            net_cash_impact = net_proceeds
            if qty > current_qty:
                warnings.append(f"Oversell warning: selling {qty} shares but only {current_qty} currently held.")
            if current_qty > 0:
                cost_basis_impact = -(qty * (current_cost / current_qty)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            new_quantity = current_qty - qty
        elif txn_type == "CASH_DEPOSIT":
            net_cash_impact = gross
        elif txn_type == "CASH_WITHDRAWAL":
            net_cash_impact = -(gross + fee)
        elif txn_type in ("DIVIDEND", "INTEREST"):
            net_cash_impact = gross - fee - tax
        elif txn_type in ("FEE", "TAX_WITHHOLDING"):
            net_cash_impact = -gross

        # Cash check
        current_cash = TransactionService.get_account_cash(db, payload.account_id, as_of=payload.trade_date)
        if (current_cash + net_cash_impact) < Decimal("0.00"):
            warnings.append(f"Resulting cash balance will be negative: {to_money(current_cash + net_cash_impact)} {payload.currency}")

        return TransactionPreview(
            trade_date=payload.trade_date,
            type=txn_type,
            symbol=payload.symbol,
            quantity=qty,
            unit_price=unit_price,
            gross_amount=gross,
            fee=fee,
            tax=tax,
            net_cash_impact=net_cash_impact,
            estimated_cost_basis_impact=cost_basis_impact,
            new_quantity_balance=new_quantity,
            warnings=warnings
        )

    @staticmethod
    def create_transaction(db: Session, payload: TransactionCreate, allow_negative_holdings: bool = False) -> Transaction:
        txn_type = payload.type.upper()
        valid_types = {
            "BUY", "SELL", "CASH_DEPOSIT", "CASH_WITHDRAWAL", "DIVIDEND", "INTEREST",
            "FEE", "TAX_WITHHOLDING", "SPLIT", "MERGER_ADJUSTMENT", "TRANSFER_IN",
            "TRANSFER_OUT", "CORRECTION_REVERSAL"
        }
        if txn_type not in valid_types:
            raise ValidationError(f"Invalid transaction type '{txn_type}'. Supported: {', '.join(sorted(valid_types))}")

        # Validate accounts and portfolio
        account = db.get(Account, payload.account_id)
        if not account or account.portfolio_id != payload.portfolio_id:
            raise ValidationError("Account does not belong to the specified portfolio.")

        # Resolve instrument
        inst_id = payload.instrument_id
        if not inst_id and payload.symbol:
            inst = TransactionService.get_or_create_instrument(db, payload.symbol, quote_currency=payload.currency)
            inst_id = inst.id

        qty = to_qty(payload.quantity)
        unit_price = to_qty(payload.unit_price) if payload.unit_price is not None else None
        fee = to_money(payload.fee)
        tax = to_money(payload.tax)

        if payload.gross_amount is not None:
            gross = to_money(payload.gross_amount)
        elif unit_price is not None and qty > 0:
            gross = to_money(qty * unit_price)
        else:
            gross = Decimal("0.00")

        # Type-specific validation and cash amount calculations
        if txn_type in ("BUY", "SELL"):
            if not inst_id:
                raise ValidationError(f"Symbol or instrument_id is required for {txn_type} transactions.")
            if qty <= Decimal("0.0000"):
                raise ValidationError("Quantity must be positive for BUY/SELL transactions.")
            if unit_price is None or unit_price < Decimal("0.0000"):
                raise ValidationError("Unit price must be non-negative for BUY/SELL transactions.")

        if txn_type == "SELL" and not allow_negative_holdings and inst_id:
            cur_qty, _, _ = TransactionService.get_current_position(db, payload.portfolio_id, inst_id, as_of=payload.trade_date)
            if qty > cur_qty:
                raise LedgerIntegrityError(f"Cannot sell {qty} units; only {cur_qty} units available on {payload.trade_date}.")

        # Determine net cash impact
        if txn_type == "BUY":
            net_amount = -(gross + fee + tax)
            entry_type = "BUY_OUTFLOW"
        elif txn_type == "SELL":
            net_amount = (gross - fee - tax)
            entry_type = "SELL_INFLOW"
        elif txn_type == "CASH_DEPOSIT":
            net_amount = gross
            entry_type = "DEPOSIT"
        elif txn_type == "CASH_WITHDRAWAL":
            net_amount = -(gross + fee)
            entry_type = "WITHDRAWAL"
        elif txn_type in ("DIVIDEND", "INTEREST"):
            net_amount = gross - fee - tax
            entry_type = txn_type
        elif txn_type in ("FEE", "TAX_WITHHOLDING"):
            net_amount = -gross
            entry_type = txn_type
        else: # SPLIT, etc.
            net_amount = Decimal("0.00")
            entry_type = txn_type

        tx = Transaction(
            portfolio_id=payload.portfolio_id,
            account_id=payload.account_id,
            instrument_id=inst_id,
            type=txn_type,
            trade_date=payload.trade_date,
            settlement_date=payload.settlement_date,
            quantity=qty if qty > 0 else None,
            unit_price=unit_price,
            gross_amount=gross,
            fee=fee,
            tax=tax,
            net_amount=net_amount,
            currency=payload.currency.upper(),
            fx_rate=payload.fx_rate,
            external_ref=payload.external_ref,
            notes=payload.notes,
            source="manual"
        )
        db.add(tx)
        db.flush()

        # Create authoritative CashLedgerEntry if net_amount != 0
        if net_amount != Decimal("0.00"):
            cash_entry = CashLedgerEntry(
                account_id=tx.account_id,
                transaction_id=tx.id,
                effective_date=tx.trade_date,
                amount=net_amount,
                currency=tx.currency,
                entry_type=entry_type
            )
            db.add(cash_entry)

        audit_service.log(
            db,
            action=f"CREATE_TRANSACTION_{txn_type}",
            entity_type="transaction",
            entity_id=tx.id,
            after_state={
                "type": tx.type,
                "amount": str(tx.gross_amount),
                "quantity": str(tx.quantity),
                "net_amount": str(tx.net_amount)
            }
        )

        db.commit()
        db.refresh(tx)
        return tx

    @staticmethod
    def reverse_transaction(db: Session, transaction_id: int, reason: str = "User reversal") -> Transaction:
        orig = db.get(Transaction, transaction_id)
        if not orig:
            raise NotFoundError(f"Transaction {transaction_id} not found.")
        if orig.is_reversed:
            raise ValidationError(f"Transaction {transaction_id} is already reversed.")

        orig.is_reversed = True

        # Create reversing transaction
        rev_tx = Transaction(
            portfolio_id=orig.portfolio_id,
            account_id=orig.account_id,
            instrument_id=orig.instrument_id,
            type="CORRECTION_REVERSAL",
            trade_date=date.today(),
            settlement_date=date.today(),
            quantity=-orig.quantity if orig.quantity else None,
            unit_price=orig.unit_price,
            gross_amount=-orig.gross_amount,
            fee=-orig.fee,
            tax=-orig.tax,
            net_amount=-orig.net_amount,
            currency=orig.currency,
            fx_rate=orig.fx_rate,
            external_ref=f"REV-{orig.id}",
            correction_of_id=orig.id,
            notes=f"Reversal of txn #{orig.id}. Reason: {reason}",
            source="system_reversal"
        )
        db.add(rev_tx)
        db.flush()

        # Reversing cash entry
        if orig.net_amount != Decimal("0.00"):
            rev_cash = CashLedgerEntry(
                account_id=rev_tx.account_id,
                transaction_id=rev_tx.id,
                effective_date=rev_tx.trade_date,
                amount=-orig.net_amount,
                currency=rev_tx.currency,
                entry_type="REVERSAL"
            )
            db.add(rev_cash)

        audit_service.log(
            db,
            action="REVERSE_TRANSACTION",
            entity_type="transaction",
            entity_id=orig.id,
            reason=reason,
            after_state={"reversal_transaction_id": rev_tx.id}
        )
        db.commit()
        db.refresh(rev_tx)
        return rev_tx

transaction_service = TransactionService()

