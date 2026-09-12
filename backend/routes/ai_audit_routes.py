"""Trilha de auditoria de respostas Lex — listagem JWT por usuario."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import AIAuditEvent, get_db
from security import get_current_user, rate_limit

router = APIRouter(prefix="/ai", tags=["AI Audit"])


@router.get("/audit")
@rate_limit(requests_per_minute=60)
async def list_ai_audit_events(
    limit: int = Query(50, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Ultimos eventos de auditoria Lex do usuario autenticado (max 50)."""
    user_id = int(current_user.user_id)
    events = (
        db.query(AIAuditEvent)
        .filter(AIAuditEvent.user_id == user_id)
        .order_by(AIAuditEvent.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "events": [event.to_dict() for event in events],
        "count": len(events),
    }
