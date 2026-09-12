"""
Anotações internas do caso — contexto operacional do escritório.

Local JWT CRUD. Not a legal opinion and not a document vault.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import MatterNote, get_db
from security import get_current_user, rate_limit
from security.xss_protection import sanitize_plain_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/matter-notes", tags=["Anotações do caso"])


class NoteCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=8000)
    client_id: Optional[int] = None
    matter_id: Optional[int] = None
    pinned: bool = False


class NotePinPatch(BaseModel):
    pinned: bool


def _uid(current_user) -> int:
    return int(current_user.id)


def _get_owned(db: Session, note_id: int, user_id: int) -> MatterNote:
    row = (
        db.query(MatterNote)
        .filter(MatterNote.id == note_id, MatterNote.user_id == user_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Anotação não encontrada")
    return row


@router.get("")
@rate_limit(requests_per_minute=60)
async def list_matter_notes(
    matter_id: Optional[int] = None,
    client_id: Optional[int] = None,
    pinned_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Lista anotações internas do usuário (fixadas primeiro)."""
    q = db.query(MatterNote).filter(MatterNote.user_id == _uid(current_user))
    if matter_id is not None:
        q = q.filter(MatterNote.matter_id == matter_id)
    if client_id is not None:
        q = q.filter(MatterNote.client_id == client_id)
    if pinned_only:
        q = q.filter(MatterNote.pinned.is_(True))
    rows = (
        q.order_by(MatterNote.pinned.desc(), MatterNote.created_at.desc(), MatterNote.id.desc())
        .limit(limit)
        .all()
    )
    return {
        "success": True,
        "notes": [r.to_dict() for r in rows],
        "count": len(rows),
    }


@router.post("", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=30)
async def create_matter_note(
    payload: NoteCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    body = sanitize_plain_text(payload.body).strip()
    if not body:
        raise HTTPException(status_code=400, detail="body obrigatório")

    row = MatterNote(
        user_id=_uid(current_user),
        client_id=payload.client_id,
        matter_id=payload.matter_id,
        body=body,
        pinned=bool(payload.pinned),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"success": True, "note": row.to_dict()}


@router.patch("/{note_id}/pin")
@rate_limit(requests_per_minute=60)
async def patch_note_pin(
    note_id: int,
    payload: NotePinPatch,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = _get_owned(db, note_id, _uid(current_user))
    row.pinned = bool(payload.pinned)
    db.commit()
    db.refresh(row)
    return {"success": True, "note": row.to_dict()}


@router.delete("/{note_id}", status_code=status.HTTP_200_OK)
@rate_limit(requests_per_minute=30)
async def delete_matter_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = _get_owned(db, note_id, _uid(current_user))
    db.delete(row)
    db.commit()
    return {"success": True, "deleted_id": note_id}
