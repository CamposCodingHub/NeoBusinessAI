"""
Agenda / audiências stub — compromissos diários do advogado.

Local JWT CRUD only. Not a calendar sync (Google/Outlook) and not a court feed.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import Hearing, HearingPrepItem, HearingWitness, get_db
from security import get_current_user, rate_limit
from security.xss_protection import sanitize_plain_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agenda", tags=["Agenda / Hearings"])

VALID_STATUSES = frozenset({"scheduled", "done", "cancelled"})
VALID_PREP_STATUSES = frozenset({"pending", "done", "waived"})
VALID_WITNESS_STATUSES = frozenset({"pending", "confirmed", "waived"})
DEFAULT_PREP_TITLES = (
    "Procuração válida",
    "RG / documento do cliente",
    "Peças essenciais impressas/PDF",
    "Testemunhas confirmadas",
    "Chegar 30 min antes / sala",
)


class HearingCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    hearing_at: datetime
    location: Optional[str] = Field(None, max_length=255)
    client_id: Optional[int] = None
    matter_id: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=4000)
    status: str = Field("scheduled", max_length=20)


class HearingStatusPatch(BaseModel):
    status: str = Field(..., min_length=1, max_length=20)


def _uid(current_user) -> int:
    return int(current_user.id)


def _parse_bound(value: Optional[str], label: str) -> Optional[datetime]:
    if value is None or not str(value).strip():
        return None
    raw = str(value).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{label} inválido — use ISO datetime",
        ) from exc


def _get_owned(db: Session, hearing_id: int, user_id: int) -> Hearing:
    row = (
        db.query(Hearing)
        .filter(Hearing.id == hearing_id, Hearing.user_id == user_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Audiência não encontrada")
    return row


@router.get("/hearings")
@rate_limit(requests_per_minute=60)
async def list_hearings(
    from_at: Optional[str] = Query(None, alias="from"),
    to_at: Optional[str] = Query(None, alias="to"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Lista audiências/compromissos do usuário (filtro opcional from/to em hearing_at)."""
    user_id = _uid(current_user)
    query = db.query(Hearing).filter(Hearing.user_id == user_id)

    start = _parse_bound(from_at, "from")
    end = _parse_bound(to_at, "to")
    if start is not None:
        query = query.filter(Hearing.hearing_at >= start)
    if end is not None:
        query = query.filter(Hearing.hearing_at <= end)

    items = query.order_by(Hearing.hearing_at.asc()).all()
    return {
        "success": True,
        "hearings": [h.to_dict() for h in items],
        "count": len(items),
    }


@router.post("/hearings", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=30)
async def create_hearing(
    payload: HearingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Cria audiência/compromisso na agenda."""
    user_id = _uid(current_user)
    title = (sanitize_plain_text(payload.title) or "").strip()
    if len(title) < 1:
        raise HTTPException(status_code=400, detail="title inválido")

    status_val = (payload.status or "scheduled").strip().lower()
    if status_val not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="status deve ser scheduled, done ou cancelled",
        )

    location = sanitize_plain_text(payload.location) if payload.location else None
    notes = sanitize_plain_text(payload.notes) if payload.notes else None

    row = Hearing(
        user_id=user_id,
        client_id=payload.client_id,
        matter_id=payload.matter_id,
        title=title[:255],
        location=(location[:255] if location else None),
        hearing_at=payload.hearing_at,
        status=status_val,
        notes=notes,
    )
    db.add(row)
    db.flush()
    db.refresh(row)
    logger.info("Hearing criado: %s (user=%s)", row.id, user_id)
    return {"success": True, "hearing": row.to_dict()}


@router.patch("/hearings/{hearing_id}")
@rate_limit(requests_per_minute=60)
async def patch_hearing_status(
    hearing_id: int,
    payload: HearingStatusPatch,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Atualiza apenas o status (scheduled | done | cancelled)."""
    user_id = _uid(current_user)
    row = _get_owned(db, hearing_id, user_id)

    status_val = (payload.status or "").strip().lower()
    if status_val not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="status deve ser scheduled, done ou cancelled",
        )

    row.status = status_val
    db.flush()
    db.refresh(row)
    return {"success": True, "hearing": row.to_dict()}


class PrepStatusPatch(BaseModel):
    status: str = Field(..., min_length=1, max_length=20)


@router.get("/hearings/{hearing_id}/prep")
@rate_limit(requests_per_minute=60)
async def list_hearing_prep(
    hearing_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Lista checklist de preparação da audiência (ownership via hearing)."""
    user_id = _uid(current_user)
    _get_owned(db, hearing_id, user_id)
    rows = (
        db.query(HearingPrepItem)
        .filter(
            HearingPrepItem.hearing_id == hearing_id,
            HearingPrepItem.user_id == user_id,
        )
        .order_by(HearingPrepItem.id.asc())
        .all()
    )
    pending = sum(1 for r in rows if r.status == "pending")
    return {
        "success": True,
        "items": [r.to_dict() for r in rows],
        "count": len(rows),
        "pending_count": pending,
    }


@router.post("/hearings/{hearing_id}/prep/seed", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=20)
async def seed_hearing_prep(
    hearing_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Cria checklist padrão de preparação (títulos estáticos)."""
    user_id = _uid(current_user)
    _get_owned(db, hearing_id, user_id)
    existing = (
        db.query(HearingPrepItem)
        .filter(
            HearingPrepItem.hearing_id == hearing_id,
            HearingPrepItem.user_id == user_id,
        )
        .count()
    )
    if existing > 0:
        raise HTTPException(
            status_code=400,
            detail="Checklist já existe para esta audiência",
        )
    created = []
    for title in DEFAULT_PREP_TITLES:
        row = HearingPrepItem(
            user_id=user_id,
            hearing_id=hearing_id,
            title=title,
            status="pending",
        )
        db.add(row)
        created.append(row)
    db.commit()
    for row in created:
        db.refresh(row)
    return {
        "success": True,
        "items": [r.to_dict() for r in created],
        "count": len(created),
    }


@router.patch("/prep/{item_id}/status")
@rate_limit(requests_per_minute=60)
async def patch_prep_status(
    item_id: int,
    payload: PrepStatusPatch,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = _uid(current_user)
    row = (
        db.query(HearingPrepItem)
        .filter(HearingPrepItem.id == item_id, HearingPrepItem.user_id == user_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Item de prep não encontrado")
    status_val = payload.status.strip().lower()
    if status_val not in VALID_PREP_STATUSES:
        raise HTTPException(status_code=400, detail="status inválido")
    row.status = status_val
    db.commit()
    db.refresh(row)
    return {"success": True, "item": row.to_dict()}



class WitnessCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=40)
    role: str = Field("testemunha", max_length=80)
    notes: Optional[str] = Field(None, max_length=2000)
    status: str = Field("pending", max_length=20)


class WitnessStatusPatch(BaseModel):
    status: str = Field(..., min_length=1, max_length=20)


@router.get("/hearings/{hearing_id}/witnesses")
@rate_limit(requests_per_minute=60)
async def list_hearing_witnesses(
    hearing_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Lista testemunhas da audiencia (ownership via hearing)."""
    user_id = _uid(current_user)
    _get_owned(db, hearing_id, user_id)
    rows = (
        db.query(HearingWitness)
        .filter(
            HearingWitness.hearing_id == hearing_id,
            HearingWitness.user_id == user_id,
        )
        .order_by(HearingWitness.id.asc())
        .all()
    )
    pending = sum(1 for r in rows if r.status == "pending")
    return {
        "success": True,
        "witnesses": [r.to_dict() for r in rows],
        "count": len(rows),
        "pending_count": pending,
    }


@router.post("/hearings/{hearing_id}/witnesses", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=30)
async def create_hearing_witness(
    hearing_id: int,
    payload: WitnessCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = _uid(current_user)
    _get_owned(db, hearing_id, user_id)
    status_value = (payload.status or "pending").strip().lower()
    if status_value not in VALID_WITNESS_STATUSES:
        raise HTTPException(status_code=400, detail="status invalido")
    name = (sanitize_plain_text(payload.name) or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name obrigatorio")
    phone = sanitize_plain_text(payload.phone).strip() if payload.phone else None
    role = (sanitize_plain_text(payload.role) or "testemunha").strip()[:80]
    notes = sanitize_plain_text(payload.notes) if payload.notes else None
    row = HearingWitness(
        user_id=user_id,
        hearing_id=hearing_id,
        name=name[:255],
        phone=(phone[:40] if phone else None),
        role=role or "testemunha",
        status=status_value,
        notes=notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"success": True, "witness": row.to_dict()}


@router.patch("/witnesses/{witness_id}/status")
@rate_limit(requests_per_minute=60)
async def patch_witness_status(
    witness_id: int,
    payload: WitnessStatusPatch,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = _uid(current_user)
    row = (
        db.query(HearingWitness)
        .filter(HearingWitness.id == witness_id, HearingWitness.user_id == user_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Testemunha nao encontrada")
    status_value = payload.status.strip().lower()
    if status_value not in VALID_WITNESS_STATUSES:
        raise HTTPException(status_code=400, detail="status invalido")
    row.status = status_value
    db.commit()
    db.refresh(row)
    return {"success": True, "witness": row.to_dict()}
