import json
from datetime import datetime, timezone
from typing import Optional, Any
from sqlalchemy.orm import Session
from backend.app.db.models.audit import AuditEvent

class AuditService:
    @staticmethod
    def log(
        db: Session,
        action: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        before_state: Optional[Any] = None,
        after_state: Optional[Any] = None,
        reason: Optional[str] = None,
        actor: str = "local_user",
        correlation_id: Optional[str] = None,
    ) -> AuditEvent:
        event = AuditEvent(
            timestamp=datetime.now(timezone.utc),
            actor=actor,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_state=json.dumps(before_state, default=str) if before_state is not None else None,
            after_state=json.dumps(after_state, default=str) if after_state is not None else None,
            reason=reason,
            correlation_id=correlation_id,
        )
        db.add(event)
        return event

audit_service = AuditService()
