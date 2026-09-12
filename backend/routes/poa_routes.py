"""
Procurações / mandatos — validade operacional do escritório.

Local JWT CRUD. Not a cartório registry and not a legal opinion on powers scope.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import PowerOfAttorney, get_db
from security import get_current_user, rate_limit
from security.xss_protection import sanitize_plain_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/poa", tags=["Procurações"])

VALID_STATUSES = frozenset({"active", "expired", "revoked"})


class PoaCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    client_id: Optional[int] = None
    matter_id: Optional[int] = None
    granted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=4000)
    status: str = Field("active", max_length=20)


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


def _sync_expired(row: PowerOfAttorney, now: Optional[datetime] = None) -> bool:
    """Mark active rows past expires_at as expired (operational flag only)."""
    if row.status != "active" or row.expires_at is None:
        return False
    reference = now or _now()
    expires = _as_aware(row.expires_at)
    if expires is not None and expires < reference:
        row.status = "expired"
        return True
    return False


def _get_owned(db: Session, poa_id: int, user_id: int) -> PowerOfAttorney:
    row = (
        db.query(PowerOfAttorney)
        .filter(PowerOfAttorney.id == poa_id, PowerOfAttorney.user_id == user_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Procuração não encontrada")
    return row


@router.get("")
@rate_limit(requests_per_minute=60)
async def list_poa(
    status_filter: Optional[str] = Query(None, alias="status"),
    expiring_within_days: Optional[int] = Query(None, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Lista procurações do usuário; opcionalmente as que vencem em N dias."""
    user_id = _uid(current_user)
    now = _now()
    query = db.query(PowerOfAttorney).filter(PowerOfAttorney.user_id == user_id)
    rows = query.order_by(PowerOfAttorney.expires_at.asc()).all()

    dirty = False
    for row in rows:
        if _sync_expired(row, now):
            dirty = True
    if dirty:
        db.commit()
        for row in rows:
            db.refresh(row)

    if status_filter:
        if status_filter not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail="status inválido")
        rows = [r for r in rows if r.status == status_filter]

    if expiring_within_days is not None:
        horizon = now + timedelta(days=expiring_within_days)
        filtered = []
        for row in rows:
            if row.status != "active" or row.expires_at is None:
                continue
            expires = _as_aware(row.expires_at)
            if expires is not None and now <= expires <= horizon:
                filtered.append(row)
        rows = filtered

    return {
        "success": True,
        "powers": [r.to_dict() for r in rows],
        "count": len(rows),
    }


@router.get("/expiring")
@rate_limit(requests_per_minute=60)
async def list_expiring(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Atalho: procurações ativas que vencem nos próximos `days` dias."""
    return await list_poa(
        status_filter=None,
        expiring_within_days=days,
        db=db,
        current_user=current_user,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=30)
async def create_poa(
    payload: PoaCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    status_value = (payload.status or "active").strip().lower()
    if status_value not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="status inválido")

    title = sanitize_plain_text(payload.title).strip()
    if not title:
        raise HTTPException(status_code=400, detail="title obrigatório")

    notes = sanitize_plain_text(payload.notes) if payload.notes else None
    row = PowerOfAttorney(
        user_id=_uid(current_user),
        client_id=payload.client_id,
        matter_id=payload.matter_id,
        title=title,
        status=status_value,
        granted_at=_as_aware(payload.granted_at),
        expires_at=_as_aware(payload.expires_at),
        notes=notes,
    )
    _sync_expired(row)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"success": True, "power": row.to_dict()}


@router.post("/{poa_id}/revoke")
@rate_limit(requests_per_minute=30)
async def revoke_poa(
    poa_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = _get_owned(db, poa_id, _uid(current_user))
    row.status = "revoked"
    db.commit()
    db.refresh(row)
    return {"success": True, "power": row.to_dict()}
