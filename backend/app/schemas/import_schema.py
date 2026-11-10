from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class CSVPreviewRow(BaseModel):
    row_number: int
    raw_data: Dict[str, str]
    parsed_data: Optional[Dict[str, Any]] = None
    is_valid: bool = True
    is_duplicate: bool = False
    errors: List[str] = []
    warnings: List[str] = []

class CSVPreviewResponse(BaseModel):
    batch_id: Optional[int] = None
    file_name: str
    file_hash: str
    source_type: str # 'transactions' or 'prices'
    detected_headers: List[str]
    suggested_mapping: Dict[str, str]
    total_rows: int
    valid_rows_count: int
    error_rows_count: int
    duplicate_rows_count: int
    rows: List[CSVPreviewRow]

class ImportConfirmRequest(BaseModel):
    portfolio_id: int
    account_id: int
    source_type: str = "transactions" # 'transactions' or 'prices'
    column_mapping: Dict[str, str]
    skip_duplicates: bool = True
    policy: str = "atomic" # 'atomic' or 'skip_errors'

class ImportBatchResponse(BaseModel):
    id: int
    file_name: str
    file_hash: str
    source_type: str
    status: str
    total_rows: int
    imported_rows: int
    failed_rows: int
    started_at: datetime
    completed_at: Optional[datetime]
    error_report_path: Optional[str]

