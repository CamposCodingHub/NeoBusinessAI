"""Firm activity feed — best-effort observability writes."""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from database import ActivityEvent

logger = logging.getLogger(__name__)


def log_activity(
    db: Session,
    user_id: int,
    action: str,
    summary: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
) -> None:
    """Persist an ActivityEvent; swallow failures so callers stay unaffected."""
    try:
        event = ActivityEvent(
            user_id=int(user_id),
            action=str(action)[:100],
            summary=str(summary)[:500],
            entity_type=str(entity_type)[:50] if entity_type else None,
            entity_id=int(entity_id) if entity_id is not None else None,
        )
        db.add(event)
        db.commit()
    except Exception:
        logger.warning(
            "log_activity failed action=%s user_id=%s",
            action,
            user_id,
            exc_info=True,
        )
        try:
            db.rollback()
        except Exception:
            pass
