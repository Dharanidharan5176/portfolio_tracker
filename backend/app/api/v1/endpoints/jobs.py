from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.db.session import get_db
from backend.app.db.models.audit import JobRun
from backend.app.services.scheduler_service import scheduler_service
from backend.app.core.errors import NotFoundError

router = APIRouter()

@router.get("")
def list_jobs(db: Session = Depends(get_db)):
    return list(db.scalars(select(JobRun).order_by(JobRun.started_at.desc()).limit(50)).all())

@router.post("/run-validation")
def trigger_validation_job():
    run = scheduler_service.run_validation_job()
    return {"job_id": run.id, "status": run.status, "counts": run.counts}
