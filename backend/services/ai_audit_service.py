"""Persistencia best-effort da trilha de auditoria Lex (compliance 2026).

Falha de DB nunca propaga: o chat premium deve continuar mesmo se o audit
nao for gravado.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from database import AIAuditEvent

logger = logging.getLogger(__name__)

MESSAGE_PREVIEW_LEN = 200
RESPONSE_PREVIEW_LEN = 300


def _preview(text: Any, limit: int) -> str:
    raw = str(text or "").strip()
    if len(raw) <= limit:
        return raw
    return raw[:limit]


def persist_lex_audit(
    db: Session,
    *,
    user_id: int,
    conversation_id: Optional[str],
    message: Any,
    response: Any,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    legal_area: Optional[str] = None,
    grounding_status: Optional[str] = None,
    requires_human_review: bool = False,
) -> Optional[AIAuditEvent]:
    """Grava um AIAuditEvent. Retorna None se falhar (sem raise)."""
    try:
        event = AIAuditEvent(
            user_id=int(user_id),
            conversation_id=(str(conversation_id or "default")[:128] or "default"),
            message_preview=_preview(message, MESSAGE_PREVIEW_LEN),
            response_preview=_preview(response, RESPONSE_PREVIEW_LEN),
            model=(str(model)[:160] if model else None),
            provider=(str(provider)[:80] if provider else None),
            legal_area=(str(legal_area)[:120] if legal_area else None),
            grounding_status=(
                str(grounding_status)[:80] if grounding_status else None
            ),
            requires_human_review=bool(requires_human_review),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    except Exception as exc:
        try:
            db.rollback()
        except Exception:
            pass
        logger.warning("AI audit persist failed (chat continues): %s", exc)
        return None
