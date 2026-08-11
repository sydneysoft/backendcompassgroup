from sqlalchemy.orm import Session

from app.models import AuditLog


def audit(db: Session, *, event_type: str, entity_type: str, entity_id: str, payload: dict | None = None) -> None:
    db.add(
        AuditLog(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload or {},
        )
    )
