"""
Atendimentos / contact log — CRM leve do escritório.

Local JWT CRUD. Not call recording and not WhatsApp sync.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import ClientContactLog, get_db
from security import get_current_user, rate_limit
from security.xss_protection import sanitize_plain_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contacts", tags=["Atendimentos"])

VALID_CHANNELS = frozenset({"phone", "whatsapp", "email", "in_person", "other"})


class ContactCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=255)
    channel: str = Field("phone", max_length=30)
    summary: Optional[str] = Field(None, max_length=8000)
    client_id: Optional[int] = None
    matter_id: Optional[int] = None
    contacted_at: Optional[datetime] = None


def _uid(current_user) -> int:
    return int(current_user.id)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


@router.get("/logs")
@rate_limit(requests_per_minute=60)
async def list_contact_logs(
    client_id: Optional[int] = None,
    matter_id: Optional[int] = None,
    channel: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Lista registros de atendimento do usuário."""
    q = db.query(ClientContactLog).filter(ClientContactLog.user_id == _uid(current_user))
    if client_id is not None:
        q = q.filter(ClientContactLog.client_id == client_id)
    if matter_id is not None:
        q = q.filter(ClientContactLog.matter_id == matter_id)
    if channel:
        if channel not in VALID_CHANNELS:
            raise HTTPException(status_code=400, detail="channel inválido")
        q = q.filter(ClientContactLog.channel == channel)
    rows = (
        q.order_by(ClientContactLog.contacted_at.desc(), ClientContactLog.id.desc())
        .limit(limit)
        .all()
    )
    return {
        "success": True,
        "logs": [r.to_dict() for r in rows],
        "count": len(rows),
    }


@router.post("/logs", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=30)
async def create_contact_log(
    payload: ContactCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    channel = (payload.channel or "phone").strip().lower()
    if channel not in VALID_CHANNELS:
        raise HTTPException(status_code=400, detail="channel inválido")

    subject = sanitize_plain_text(payload.subject).strip()
    if not subject:
        raise HTTPException(status_code=400, detail="subject obrigatório")

    summary = sanitize_plain_text(payload.summary) if payload.summary else None
    contacted_at = _as_aware(payload.contacted_at) or _now()

    row = ClientContactLog(
        user_id=_uid(current_user),
        client_id=payload.client_id,
        matter_id=payload.matter_id,
        channel=channel,
        subject=subject,
        summary=summary,
        contacted_at=contacted_at,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"success": True, "log": row.to_dict()}
