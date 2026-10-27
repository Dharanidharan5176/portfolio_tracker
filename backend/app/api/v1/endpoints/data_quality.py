from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.db.session import get_db
from backend.app.db.models.audit import DataQualityIssue
from backend.app.services.data_quality_service import data_quality_service

router = APIRouter()

@router.get("/issues")
def list_issues(
    status_filter: Optional[str] = Query(None), # 'open', 'resolved'
    severity: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = select(DataQualityIssue)
    if status_filter:
        query = query.where(DataQualityIssue.status == status_filter)
    if severity:
        query = query.where(DataQualityIssue.severity == severity)
    return list(db.scalars(query.order_by(DataQualityIssue.last_seen.desc())).all())

@router.post("/run")
def trigger_validation_checks(db: Session = Depends(get_db)):
    issues = data_quality_service.run_all_checks(db)
    return {"status": "completed", "issues_detected": len(issues)}

@router.post("/issues/{issue_id}/resolve")
def resolve_issue(issue_id: int, reason: str = Query("User resolved"), db: Session = Depends(get_db)):
    return data_quality_service.resolve_issue(db, issue_id, reason)
