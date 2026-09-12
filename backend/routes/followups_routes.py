"""
Follow-ups — lembretes de retorno ao cliente.

Local JWT CRUD. Not a court deadline and not a calendar sync.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import FollowUp, get_db
from security import get_current_user, rate_limit
from security.xss_protection import sanitize_plain_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/followups", tags=["Follow-ups"])

VALID_STATUSES = frozenset({"open", "done", "cancelled"})


class FollowUpCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=255)
    due_at: datetime
    client_id: Optional[int] = None
    matter_id: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=4000)
    status: str = Field("open", max_length=20)


class FollowUpStatusPatch(BaseModel):
    status: str = Field(..., min_length=1, max_length=20)


def _uid(current_user) -> int:
    return int(current_user.id)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _get_owned(db: Session, item_id: int, user_id: int) -> FollowUp:
    row = (
        db.query(FollowUp)
        .filter(FollowUp.id == item_id, FollowUp.user_id == user_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Follow-up não encontrado")
    return row


@router.get("")
@rate_limit(requests_per_minute=60)
async def list_followups(
    status_filter: Optional[str] = Query(None, alias="status"),
    open_only: bool = Query(False),
    due_before: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Lista follow-ups do usuário."""
    q = db.query(FollowUp).filter(FollowUp.user_id == _uid(current_user))
    if open_only:
        q = q.filter(FollowUp.status == "open")
    elif status_filter:
        if status_filter not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail="status inválido")
        q = q.filter(FollowUp.status == status_filter)
    if due_before is not None:
        q = q.filter(FollowUp.due_at <= _as_aware(due_before))
    rows = q.order_by(FollowUp.due_at.asc(), FollowUp.id.desc()).all()
    return {
        "success": True,
        "followups": [r.to_dict() for r in rows],
        "count": len(rows),
    }


@router.post("", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=30)
async def create_followup(
    payload: FollowUpCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    status_value = (payload.status or "open").strip().lower()
    if status_value not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="status inválido")

    subject = sanitize_plain_text(payload.subject).strip()
    if not subject:
        raise HTTPException(status_code=400, detail="subject obrigatório")

    notes = sanitize_plain_text(payload.notes) if payload.notes else None
    row = FollowUp(
        user_id=_uid(current_user),
        client_id=payload.client_id,
        matter_id=payload.matter_id,
        subject=subject,
        status=status_value,
        due_at=_as_aware(payload.due_at),
        notes=notes,
        completed_at=_now() if status_value == "done" else None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"success": True, "followup": row.to_dict()}


@router.patch("/{followup_id}/status")
@rate_limit(requests_per_minute=60)
async def patch_followup_status(
    followup_id: int,
    payload: FollowUpStatusPatch,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = _get_owned(db, followup_id, _uid(current_user))
    status_value = payload.status.strip().lower()
    if status_value not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="status inválido")
    row.status = status_value
    row.completed_at = _now() if status_value == "done" else None
    db.commit()
    db.refresh(row)
    return {"success": True, "followup": row.to_dict()}
