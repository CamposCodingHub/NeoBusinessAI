"""
Checklist documental do caso — o que ainda falta do cliente.

Local JWT CRUD. Not a document management system and not OCR intake.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import MatterDocItem, get_db
from security import get_current_user, rate_limit
from security.xss_protection import sanitize_plain_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/matter-docs", tags=["Checklist documental"])

VALID_STATUSES = frozenset({"pending", "received", "waived"})


class MatterDocCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    client_id: Optional[int] = None
    matter_id: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=4000)
    status: str = Field("pending", max_length=20)


class MatterDocStatusPatch(BaseModel):
    status: str = Field(..., min_length=1, max_length=20)


def _uid(current_user) -> int:
    return int(current_user.id)


def _get_owned(db: Session, item_id: int, user_id: int) -> MatterDocItem:
    row = (
        db.query(MatterDocItem)
        .filter(MatterDocItem.id == item_id, MatterDocItem.user_id == user_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return row


@router.get("")
@rate_limit(requests_per_minute=60)
async def list_matter_docs(
    status_filter: Optional[str] = Query(None, alias="status"),
    pending_only: bool = Query(False),
    matter_id: Optional[int] = None,
    client_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Lista itens de checklist documental do usuário."""
    q = db.query(MatterDocItem).filter(MatterDocItem.user_id == _uid(current_user))
    if pending_only:
        q = q.filter(MatterDocItem.status == "pending")
    elif status_filter:
        if status_filter not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail="status inválido")
        q = q.filter(MatterDocItem.status == status_filter)
    if matter_id is not None:
        q = q.filter(MatterDocItem.matter_id == matter_id)
    if client_id is not None:
        q = q.filter(MatterDocItem.client_id == client_id)
    rows = q.order_by(MatterDocItem.id.desc()).all()
    pending = sum(1 for r in rows if r.status == "pending")
    return {
        "success": True,
        "items": [r.to_dict() for r in rows],
        "count": len(rows),
        "pending_count": pending,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=30)
async def create_matter_doc(
    payload: MatterDocCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    status_value = (payload.status or "pending").strip().lower()
    if status_value not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="status inválido")

    title = sanitize_plain_text(payload.title).strip()
    if not title:
        raise HTTPException(status_code=400, detail="title obrigatório")

    notes = sanitize_plain_text(payload.notes) if payload.notes else None
    row = MatterDocItem(
        user_id=_uid(current_user),
        client_id=payload.client_id,
        matter_id=payload.matter_id,
        title=title,
        status=status_value,
        notes=notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"success": True, "item": row.to_dict()}


@router.patch("/{item_id}/status")
@rate_limit(requests_per_minute=60)
async def patch_matter_doc_status(
    item_id: int,
    payload: MatterDocStatusPatch,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = _get_owned(db, item_id, _uid(current_user))
    status_value = payload.status.strip().lower()
    if status_value not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="status inválido")
    row.status = status_value
    db.commit()
    db.refresh(row)
    return {"success": True, "item": row.to_dict()}


# Seed helpers (static titles — methodological, not legal advice)
DEFAULT_INTAKE_TITLES = (
    "RG / identidade",
    "CPF",
    "Comprovante de residência",
    "Procuração assinada",
    "Contrato / documentos do negócio",
)


@router.post("/seed-intake", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=10)
async def seed_intake_checklist(
    matter_id: Optional[int] = None,
    client_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Cria checklist básico de intake (títulos estáticos)."""
    user_id = _uid(current_user)
    created = []
    for title in DEFAULT_INTAKE_TITLES:
        row = MatterDocItem(
            user_id=user_id,
            client_id=client_id,
            matter_id=matter_id,
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
