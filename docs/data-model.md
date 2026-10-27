# Local Portfolio Tracker — Data Model Specification

## 1. Relational Entities

### Portfolio
Logical container for segregated investment strategies or tax accounts.
- `id` (INTEGER, PK, Autoincrement)
- `name` (VARCHAR, Unique, Not Null)
- `base_currency` (VARCHAR(3), Default 'INR')
- `timezone` (VARCHAR, Default 'Asia/Kolkata')
- `benchmark_symbol` (VARCHAR, Nullable)
- `status` (VARCHAR, 'active' | 'archived')
- `notes` (TEXT, Nullable)
- `created_at` (DATETIME, Not Null)
- `updated_at` (DATETIME, Not Null)

### Account
Specific financial accounts (e.g. Brokerage, Bank Account).
- `id` (INTEGER, PK, Autoincrement)
- `portfolio_id` (INTEGER, FK -> Portfolio.id, Not Null)
- `name` (VARCHAR, Not Null)
- `account_type` (VARCHAR, 'brokerage' | 'bank' | 'manual')
- `institution_label` (VARCHAR, Not Null)
- `currency` (VARCHAR(3), Not Null)
- `status` (VARCHAR, 'active' | 'archived')
- `created_at` (DATETIME, Not Null)
- `updated_at` (DATETIME, Not Null)

### Instrument
Tradable securities or assets.
- `id` (INTEGER, PK, Autoincrement)
- `canonical_symbol` (VARCHAR, Unique, Not Null)
- `display_name` (VARCHAR, Not Null)
- `asset_type` (VARCHAR, 'equity' | 'etf' | 'mutual_fund' | 'crypto' | 'bond' | 'cash')
- `exchange` (VARCHAR, Nullable)
- `quote_currency` (VARCHAR(3), Not Null)
- `isin` (VARCHAR, Nullable)
- `metadata_source` (VARCHAR, Default 'manual')
- `sector` (VARCHAR, Nullable)
- `is_active` (BOOLEAN, Default True)
- `created_at` (DATETIME, Not Null)
- `updated_at` (DATETIME, Not Null)

### Transaction
The immutable ledger of financial actions.
- `id` (INTEGER, PK, Autoincrement)
- `portfolio_id` (INTEGER, FK -> Portfolio.id, Not Null)
- `account_id` (INTEGER, FK -> Account.id, Not Null)
- `instrument_id` (INTEGER, FK -> Instrument.id, Nullable)
- `type` (VARCHAR, 'BUY' | 'SELL' | 'CASH_DEPOSIT' | 'CASH_WITHDRAWAL' | 'DIVIDEND' | 'INTEREST' | 'FEE' | 'TAX_WITHHOLDING' | 'SPLIT' | 'MERGER_ADJUSTMENT' | 'TRANSFER_IN' | 'TRANSFER_OUT' | 'CORRECTION_REVERSAL')
- `trade_date` (DATE, Not Null)
- `settlement_date` (DATE, Nullable)
- `quantity` (NUMERIC/DECIMAL, Nullable)
- `unit_price` (NUMERIC/DECIMAL, Nullable)
- `gross_amount` (NUMERIC/DECIMAL, Not Null)
- `fee` (NUMERIC/DECIMAL, Default 0.0)
- `tax` (NUMERIC/DECIMAL, Default 0.0)
- `net_amount` (NUMERIC/DECIMAL, Not Null)
- `currency` (VARCHAR(3), Not Null)
- `fx_rate` (NUMERIC/DECIMAL, Default 1.0)
- `external_ref` (VARCHAR, Nullable)
- `source` (VARCHAR, Default 'manual')
- `import_batch_id` (INTEGER, FK -> ImportBatch.id, Nullable)
- `notes` (TEXT, Nullable)
- `correction_of_id` (INTEGER, FK -> Transaction.id, Nullable)
- `is_reversed` (BOOLEAN, Default False)
- `created_at` (DATETIME, Not Null)
- `updated_at` (DATETIME, Not Null)

### CashLedgerEntry
Derivation or transactional counterpart for auditable cash tracking.
- `id` (INTEGER, PK, Autoincrement)
- `account_id` (INTEGER, FK -> Account.id, Not Null)
- `transaction_id` (INTEGER, FK -> Transaction.id, Not Null)
- `effective_date` (DATE, Not Null)
- `amount` (NUMERIC/DECIMAL, Not Null) # Positive = credit, Negative = debit
- `currency` (VARCHAR(3), Not Null)
- `entry_type` (VARCHAR, Not Null)
- `created_at` (DATETIME, Not Null)

### PriceObservation
Historical and latest valuation prices for instruments.
- `id` (INTEGER, PK, Autoincrement)
- `instrument_id` (INTEGER, FK -> Instrument.id, Not Null)
- `observed_at` (DATETIME, Not Null)
- `price` (NUMERIC/DECIMAL, Not Null)
- `currency` (VARCHAR(3), Not Null)
- `provider` (VARCHAR, Not Null)
- `source_record_id` (VARCHAR, Nullable)
- `quality_status` (VARCHAR, 'valid' | 'stale' | 'anomaly' | 'unverified')
- `is_manual_override` (BOOLEAN, Default False)
- `imported_at` (DATETIME, Not Null)

### FXObservation
Currency exchange rates.
- `id` (INTEGER, PK, Autoincrement)
- `base_currency` (VARCHAR(3), Not Null)
- `quote_currency` (VARCHAR(3), Not Null)
- `observed_at` (DATETIME, Not Null)
- `rate` (NUMERIC/DECIMAL, Not Null)
- `provider` (VARCHAR, Not Null)
- `quality_status` (VARCHAR, Default 'valid')
- `created_at` (DATETIME, Not Null)

### CorporateAction
Splits, mergers, and capital adjustments.
- `id` (INTEGER, PK, Autoincrement)
- `instrument_id` (INTEGER, FK -> Instrument.id, Not Null)
- `type` (VARCHAR, 'SPLIT' | 'MERGER' | 'SPINOFF')
- `effective_date` (DATE, Not Null)
- `split_ratio` (NUMERIC/DECIMAL, Nullable)
- `source` (VARCHAR, Not Null)
- `verification_status` (VARCHAR, 'verified' | 'unverified')
- `notes` (TEXT, Nullable)
- `created_at` (DATETIME, Not Null)

### ImportBatch
Provenance tracking for batch CSV imports.
- `id` (INTEGER, PK, Autoincrement)
- `file_name` (VARCHAR, Not Null)
- `file_hash` (VARCHAR(64), Not Null) # SHA-256
- `source_type` (VARCHAR, 'transactions' | 'prices')
- `mapping_json` (TEXT, Nullable)
- `started_at` (DATETIME, Not Null)
- `completed_at` (DATETIME, Nullable)
- `status` (VARCHAR, 'pending' | 'completed' | 'failed' | 'partial')
- `total_rows` (INTEGER, Default 0)
- `imported_rows` (INTEGER, Default 0)
- `failed_rows` (INTEGER, Default 0)
- `error_report_path` (VARCHAR, Nullable)

### DataQualityIssue
Persistent queue of data integrity items.
- `id` (INTEGER, PK, Autoincrement)
- `issue_key` (VARCHAR, Unique, Not Null)
- `severity` (VARCHAR, 'critical' | 'error' | 'warning' | 'info')
- `category` (VARCHAR, 'stale_price' | 'missing_price' | 'missing_fx' | 'negative_quantity' | 'negative_cash' | 'duplicate_txn')
- `entity_type` (VARCHAR, Nullable)
- `entity_id` (INTEGER, Nullable)
- `first_seen` (DATETIME, Not Null)
- `last_seen` (DATETIME, Not Null)
- `status` (VARCHAR, 'open' | 'resolved' | 'dismissed')
- `details` (TEXT, Nullable)
- `resolution_note` (TEXT, Nullable)

### Notification
In-app notification system.
- `id` (INTEGER, PK, Autoincrement)
- `dedupe_key` (VARCHAR, Unique, Not Null)
- `category` (VARCHAR, Not Null)
- `severity` (VARCHAR, Not Null)
- `title` (VARCHAR, Not Null)
- `message` (TEXT, Not Null)
- `related_entity_type` (VARCHAR, Nullable)
- `related_entity_id` (INTEGER, Nullable)
- `status` (VARCHAR, 'unread' | 'read')
- `created_at` (DATETIME, Not Null)
- `read_at` (DATETIME, Nullable)

### JobRun
Scheduler execution log.
- `id` (INTEGER, PK, Autoincrement)
- `job_name` (VARCHAR, Not Null)
- `started_at` (DATETIME, Not Null)
- `finished_at` (DATETIME, Nullable)
- `status` (VARCHAR, 'running' | 'success' | 'failed' | 'skipped')
- `counts` (TEXT, Nullable)
- `error_summary` (TEXT, Nullable)
- `retry_count` (INTEGER, Default 0)

### AuditEvent
Append-only log of critical user/system actions.
- `id` (INTEGER, PK, Autoincrement)
- `timestamp` (DATETIME, Not Null)
- `actor` (VARCHAR, Default 'local_user')
- `action` (VARCHAR, Not Null)
- `entity_type` (VARCHAR, Not Null)
- `entity_id` (INTEGER, Nullable)
- `before_state` (TEXT, Nullable)
- `after_state` (TEXT, Nullable)
- `reason` (TEXT, Nullable)
- `correlation_id` (VARCHAR, Nullable)

### AppSetting & BackupRecord
- `AppSetting`: `key` (PK), `value`, `updated_at`
- `BackupRecord`: `id` (PK), `path`, `created_at`, `size_bytes`, `checksum`, `status`, `verified_at`
