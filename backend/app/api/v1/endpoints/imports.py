from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, Response, status
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.db.session import get_db
from backend.app.db.models.import_batch import ImportBatch
from backend.app.schemas.import_schema import CSVPreviewResponse, ImportConfirmRequest, ImportBatchResponse
from backend.app.services.import_service import import_service
from backend.app.core.errors import NotFoundError, ValidationError
from backend.app.core.security import sanitize_filename

router = APIRouter()

@router.get("", response_model=List[ImportBatchResponse])
def list_import_batches(db: Session = Depends(get_db)):
    query = select(ImportBatch).order_by(ImportBatch.id.desc())
    return list(db.scalars(query).all())

@router.get("/templates/{template_type}")
def get_template(template_type: str):
    root = Path(__file__).resolve().parent.parent.parent.parent.parent
    if template_type == "transactions":
        file_path = root / "data" / "templates" / "transactions_sample.csv"
    elif template_type == "prices":
        file_path = root / "data" / "templates" / "prices_sample.csv"
    else:
        raise NotFoundError("Unknown template type. Use 'transactions' or 'prices'.")

    if not file_path.exists():
        raise NotFoundError("Template file not found.")

    return FileResponse(
        path=str(file_path),
        media_type="text/csv",
        filename=f"{template_type}_template.csv"
    )

@router.post("/preview", response_model=CSVPreviewResponse)
async def preview_csv(
    file: UploadFile = File(...),
    source_type: str = Form("transactions")
):
    safe_name = sanitize_filename(file.filename or "upload.csv")
    content_bytes = await file.read()
    content = content_bytes.decode("utf-8-sig", errors="replace")
    
    return import_service.parse_preview(
        content=content,
        filename=safe_name,
        source_type=source_type
    )

@router.post("/confirm", response_model=ImportBatchResponse, status_code=status.HTTP_201_CREATED)
async def confirm_import(
    file: UploadFile = File(...),
    portfolio_id: int = Form(...),
    account_id: int = Form(...),
    source_type: str = Form("transactions"),
    column_mapping: str = Form("{}"), # JSON string
    policy: str = Form("atomic"),
    skip_duplicates: bool = Form(True),
    db: Session = Depends(get_db)
):
    import json
    try:
        mapping_dict = json.loads(column_mapping)
    except Exception:
        mapping_dict = {}

    safe_name = sanitize_filename(file.filename or "upload.csv")
    content_bytes = await file.read()
    content = content_bytes.decode("utf-8-sig", errors="replace")

    req = ImportConfirmRequest(
        portfolio_id=portfolio_id,
        account_id=account_id,
        source_type=source_type,
        column_mapping=mapping_dict,
        skip_duplicates=skip_duplicates,
        policy=policy
    )

    return import_service.confirm_import(db, content, safe_name, req)

@router.get("/{batch_id}", response_model=ImportBatchResponse)
def get_import_batch(batch_id: int, db: Session = Depends(get_db)):
    batch = db.get(ImportBatch, batch_id)
    if not batch:
        raise NotFoundError(f"Import batch {batch_id} not found.")
    return batch
