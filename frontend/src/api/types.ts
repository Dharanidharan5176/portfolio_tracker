export interface HoldingItem {
  instrument_id: number;
  symbol: string;
  display_name: string;
  asset_type: string;
  quantity: string;
  average_cost: string;
  cost_basis: string;
  latest_price: string | null;
  price_date: string | null;
  market_value: string | null;
  unrealized_pnl: string | null;
  unrealized_pnl_pct: string | null;
  weight: string;
  currency: string;
  quality_status: 'valid' | 'stale' | 'missing_price' | 'missing_fx' | 'anomaly';
  is_manual_override: boolean;
  warnings: string[];
}

export interface DashboardSummary {
  portfolio_id: number | null;
  portfolio_name: string;
  base_currency: string;
  as_of: string;
  total_portfolio_value: string;
  holdings_market_value: string;
  invested_cost_basis: string;
  unrealized_pnl: string;
  unrealized_pnl_pct: string;
  realized_pnl: string;
  cash_balance: string;
  data_freshness: string;
  holdings_count: number;
  holdings: HoldingItem[];
  recent_activity: Array<{
    id: number;
    type: string;
    symbol: string;
    trade_date: string;
    quantity: string | null;
    gross_amount: string;
    net_amount: string;
    currency: string;
    is_reversed: boolean;
  }>;
  allocation_by_asset: Array<{
    name: string;
    value: string;
    weight: string;
  }>;
  value_history: Array<{
    date: string;
    portfolio_value: string;
    cost_basis: string;
  }>;
  unread_notifications_count: number;
  open_issues_count: number;
}

export interface Portfolio {
  id: number;
  name: string;
  base_currency: string;
  timezone: string;
  benchmark_symbol: string | null;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Account {
  id: number;
  portfolio_id: number;
  name: string;
  account_type: string;
  institution_label: string;
  currency: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface TransactionItem {
  id: number;
  portfolio_id: number;
  account_id: number;
  instrument_id: number | null;
  symbol: string | null;
  type: string;
  trade_date: string;
  settlement_date: string | null;
  quantity: string | null;
  unit_price: string | null;
  gross_amount: string;
  fee: string;
  tax: string;
  net_amount: string;
  currency: string;
  fx_rate: string;
  external_ref: string | null;
  source: string;
  notes: string | null;
  correction_of_id: number | null;
  is_reversed: boolean;
  created_at: string;
}

export interface TransactionPreview {
  trade_date: string;
  type: string;
  symbol: string | null;
  quantity: string | null;
  unit_price: string | null;
  gross_amount: string;
  fee: string;
  tax: string;
  net_cash_impact: string;
  estimated_cost_basis_impact: string;
  new_quantity_balance: string;
  warnings: string[];
}

export interface ImportPreviewRow {
  row_number: number;
  raw_data: Record<string, string>;
  parsed_data: Record<string, any> | null;
  is_valid: boolean;
  is_duplicate: boolean;
  errors: string[];
  warnings: string[];
}

export interface ImportPreviewResponse {
  batch_id: number | null;
  file_name: string;
  file_hash: string;
  source_type: string;
  detected_headers: string[];
  suggested_mapping: Record<string, string>;
  total_rows: number;
  valid_rows_count: number;
  error_rows_count: number;
  duplicate_rows_count: number;
  rows: ImportPreviewRow[];
}

