"""
Intake / Lead Pipeline — MVP
Captação comercial com status kanban e conversão para Client.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import Client, Lead, User, get_db
from security import get_current_user, rate_limit
from security.xss_protection import sanitize_plain_text
from services.activity_feed_service import log_activity
from services.conflict_check_service import (
    apply_conflict_on_create,
    apply_conflict_on_update,
    screen_conflicts,
)

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/intake", tags=["Intake"])

VALID_STATUSES = frozenset({"new", "qualified", "meeting", "won", "lost"})


class LeadCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    practice_area: Optional[str] = Field(None, max_length=120)
    source: Optional[str] = Field(None, max_length=120)
    status: str = Field("new", max_length=50)
    notes: Optional[str] = None
    conflict_flag: bool = False


class LeadUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    practice_area: Optional[str] = Field(None, max_length=120)
    source: Optional[str] = Field(None, max_length=120)
    status: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    conflict_flag: Optional[bool] = None


def _sanitize_optional(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = sanitize_plain_text(value)
    return cleaned if cleaned else None


def _validate_status(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"status inválido; use um de: {', '.join(sorted(VALID_STATUSES))}",
        )
    return normalized


def _get_owned_lead(db: Session, lead_id: int, user_id: int) -> Lead:
    lead = (
        db.query(Lead)
        .filter(Lead.id == lead_id, Lead.user_id == user_id)
        .first()
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return lead


@router.get("/leads")
@rate_limit(requests_per_minute=60)
async def list_leads(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    practice_area: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista leads do escritório (dono = user autenticado)."""
    query = db.query(Lead).filter(Lead.user_id == current_user.id)

    if status_filter:
        query = query.filter(Lead.status == _validate_status(status_filter))

    if practice_area:
        query = query.filter(Lead.practice_area.ilike(f"%{practice_area.strip()}%"))

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            (Lead.name.ilike(term))
            | (Lead.email.ilike(term))
            | (Lead.phone.ilike(term))
        )

    total = query.count()
    leads = (
        query.order_by(Lead.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "leads": [lead.to_dict() for lead in leads],
        "pagination": {
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit if total else 0,
            "limit": limit,
        },
    }


@router.post("/leads", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=30)
async def create_lead(
    payload: LeadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cria um novo lead de intake."""
    lead_status = _validate_status(payload.status) or "new"
    name = sanitize_plain_text(payload.name)
    if not name:
        raise HTTPException(status_code=400, detail="name é obrigatório")

    lead = Lead(
        user_id=current_user.id,
        name=name,
        email=_sanitize_optional(payload.email),
        phone=_sanitize_optional(payload.phone),
        practice_area=_sanitize_optional(payload.practice_area),
        source=_sanitize_optional(payload.source) or "manual",
        status=lead_status,
        notes=_sanitize_optional(payload.notes),
        conflict_flag=bool(payload.conflict_flag),
    )
    screen = screen_conflicts(
        db,
        current_user.id,
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
    )
    apply_conflict_on_create(lead, screen, manual_flag=bool(payload.conflict_flag))
    db.add(lead)
    db.commit()
    db.refresh(lead)
    try:
        log_activity(
            db,
            current_user.id,
            "intake.lead_create",
            f"Lead criado: {lead.name}",
            entity_type="lead",
            entity_id=lead.id,
        )
    except Exception:
        pass
    logger.info(
        "Lead criado: %s (user=%s conflict=%s)",
        lead.id,
        current_user.id,
        lead.conflict_flag,
    )
    return {"message": "Lead criado com sucesso", "lead": lead.to_dict()}


@router.patch("/leads/{lead_id}")
@rate_limit(requests_per_minute=40)
async def update_lead(
    lead_id: int,
    payload: LeadUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atualiza campos do lead (status kanban, notas, conflito, etc.)."""
    lead = _get_owned_lead(db, lead_id, current_user.id)
    data = payload.model_dump(exclude_unset=True)

    if "status" in data:
        data["status"] = _validate_status(data["status"])

    for field in ("name", "email", "phone", "practice_area", "source", "notes"):
        if field in data and data[field] is not None:
            if field == "name":
                cleaned = sanitize_plain_text(data[field])
                if not cleaned:
                    raise HTTPException(status_code=400, detail="name inválido")
                data[field] = cleaned
            else:
                data[field] = _sanitize_optional(data[field])

    manual_flag = data.pop("conflict_flag", None) if "conflict_flag" in data else None

    for key, value in data.items():
        setattr(lead, key, value)

    screen = screen_conflicts(
        db,
        current_user.id,
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        exclude_lead_id=lead.id,
    )
    apply_conflict_on_update(lead, screen, manual_flag=manual_flag)

    lead.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(lead)
    return {"message": "Lead atualizado", "lead": lead.to_dict()}


@router.post("/leads/{lead_id}/convert")
@rate_limit(requests_per_minute=20)
async def convert_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Converte lead em Client (modelo existente).
    Bloqueia se conflict_flag=True. Marca lead como won.
    """
    lead = _get_owned_lead(db, lead_id, current_user.id)

    if lead.conflict_flag:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Lead marcado com conflito de interesse; remova o flag antes de converter",
        )

    if lead.status == "won":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lead já convertido (status=won)",
        )

    if lead.status == "lost":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lead perdido não pode ser convertido",
        )

    client = Client(
        user_id=current_user.id,
        name=lead.name,
        email=lead.email,
        notes=lead.notes,
        status="active",
    )
    if lead.phone:
        client.set_sensitive_data(phone=lead.phone)

    practice_note = ""
    if lead.practice_area:
        practice_note = f"[Intake] Área: {lead.practice_area}"
    if lead.source:
        practice_note = (
            f"{practice_note} | Fonte: {lead.source}" if practice_note else f"[Intake] Fonte: {lead.source}"
        )
    if practice_note:
        client.notes = f"{practice_note}\n{client.notes or ''}".strip()

    lead.status = "won"
    lead.updated_at = datetime.now(timezone.utc)

    db.add(client)
    db.commit()
    db.refresh(client)
    db.refresh(lead)

    logger.info("Lead %s convertido em Client %s", lead.id, client.id)
    return {
        "message": "Lead convertido em cliente",
        "lead": lead.to_dict(),
        "client": client.to_dict(),
    }
