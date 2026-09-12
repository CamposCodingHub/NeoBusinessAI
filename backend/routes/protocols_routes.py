"""
Protocolos judiciais — números de petição (PJe / e-SAJ / etc.).

Local JWT CRUD. Não sincroniza com tribunal; evita perder o comprovante.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import CourtProtocol, get_db
from security import get_current_user, rate_limit
from security.xss_protection import sanitize_plain_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/protocols", tags=["Protocolos"])

VALID_STATUSES = frozenset({"pending", "confirmed", "returned", "archived"})
VALID_SYSTEMS = frozenset({"pje", "esaj", "projudi", "tj", "outro"})


class ProtocolCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    protocol_number: str = Field(..., min_length=1, max_length=120)
    system: str = Field("outro", max_length=40)
    court: Optional[str] = Field(None, max_length=255)
    client_id: Optional[int] = None
    matter_id: Optional[int] = None
    filed_at: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=4000)
    status: str = Field("pending", max_length=20)


class ProtocolStatusPatch(BaseModel):
    status: str = Field(..., min_length=1, max_length=20)


def _uid(current_user) -> int:
    return int(current_user.id)


def _as_aware(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _get_owned(db: Session, item_id: int, user_id: int) -> CourtProtocol:
    row = (
        db.query(CourtProtocol)
        .filter(CourtProtocol.id == item_id, CourtProtocol.user_id == user_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Protocolo não encontrado")
    return row


@router.get("")
@rate_limit(requests_per_minute=60)
async def list_protocols(
    status_filter: Optional[str] = Query(None, alias="status"),
    pending_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Lista protocolos do usuário."""
    q = db.query(CourtProtocol).filter(CourtProtocol.user_id == _uid(current_user))
    if pending_only:
        q = q.filter(CourtProtocol.status == "pending")
    elif status_filter:
        if status_filter not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail="status inválido")
        q = q.filter(CourtProtocol.status == status_filter)
    rows = q.order_by(CourtProtocol.filed_at.desc(), CourtProtocol.id.desc()).all()
    return {
        "success": True,
        "protocols": [r.to_dict() for r in rows],
        "count": len(rows),
    }


@router.post("", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=30)
async def create_protocol(
    payload: ProtocolCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    status_value = (payload.status or "pending").strip().lower()
    system = (payload.system or "outro").strip().lower()
    if status_value not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="status inválido")
    if system not in VALID_SYSTEMS:
        raise HTTPException(status_code=400, detail="system inválido")

    title = sanitize_plain_text(payload.title).strip()
    number = sanitize_plain_text(payload.protocol_number).strip()
    if not title or not number:
        raise HTTPException(status_code=400, detail="title e protocol_number obrigatórios")

    court = sanitize_plain_text(payload.court).strip() if payload.court else None
    notes = sanitize_plain_text(payload.notes) if payload.notes else None
    row = CourtProtocol(
        user_id=_uid(current_user),
        client_id=payload.client_id,
        matter_id=payload.matter_id,
        title=title,
        protocol_number=number,
        system=system,
        court=court or None,
        status=status_value,
        filed_at=_as_aware(payload.filed_at),
        notes=notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"success": True, "protocol": row.to_dict()}


@router.patch("/{protocol_id}/status")
@rate_limit(requests_per_minute=60)
async def patch_protocol_status(
    protocol_id: int,
    payload: ProtocolStatusPatch,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = _get_owned(db, protocol_id, _uid(current_user))
    status_value = payload.status.strip().lower()
    if status_value not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="status inválido")
    row.status = status_value
    db.commit()
    db.refresh(row)
    return {"success": True, "protocol": row.to_dict()}
