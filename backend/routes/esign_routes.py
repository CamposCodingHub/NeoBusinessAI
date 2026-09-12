"""
Electronic signature stub (ClickSign-style).

NOT a real e-sign provider — local status machine only (draft → sent → signed).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import ESignEnvelope, get_db
from security import get_current_user, rate_limit
from security.xss_protection import sanitize_plain_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/esign", tags=["E-Sign Stub"])

VALID_STATUSES = frozenset({"draft", "sent", "signed", "cancelled"})


class EnvelopeCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    signer_email: str = Field(..., min_length=3, max_length=255)
    signer_name: str = Field(..., min_length=1, max_length=255)
    document_id: Optional[int] = None


def _uid(current_user) -> int:
    return int(current_user.id)


def _get_owned_envelope(
    db: Session, envelope_id: int, user_id: int
) -> ESignEnvelope:
    envelope = (
        db.query(ESignEnvelope)
        .filter(ESignEnvelope.id == envelope_id, ESignEnvelope.user_id == user_id)
        .first()
    )
    if not envelope:
        raise HTTPException(status_code=404, detail="Envelope não encontrado")
    return envelope


@router.post("/envelopes", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=30)
async def create_envelope(
    payload: EnvelopeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Cria envelope em draft (stub — sem provedor externo)."""
    user_id = _uid(current_user)
    title = sanitize_plain_text(payload.title) or ""
    if len(title) < 1:
        raise HTTPException(status_code=400, detail="title inválido")
    signer_name = sanitize_plain_text(payload.signer_name) or ""
    if len(signer_name) < 1:
        raise HTTPException(status_code=400, detail="signer_name inválido")
    signer_email = (sanitize_plain_text(payload.signer_email) or "").strip().lower()
    if "@" not in signer_email or len(signer_email) < 3:
        raise HTTPException(status_code=400, detail="signer_email inválido")

    envelope = ESignEnvelope(
        user_id=user_id,
        document_id=payload.document_id,
        title=title,
        status="draft",
        signer_email=signer_email[:255],
        signer_name=signer_name[:255],
        provider="stub",
        external_id=None,
    )
    db.add(envelope)
    db.flush()
    db.refresh(envelope)
    return {"success": True, "envelope": envelope.to_dict()}


@router.get("/envelopes")
@rate_limit(requests_per_minute=60)
async def list_envelopes(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = _uid(current_user)
    items = (
        db.query(ESignEnvelope)
        .filter(ESignEnvelope.user_id == user_id)
        .order_by(ESignEnvelope.created_at.desc())
        .all()
    )
    return {
        "success": True,
        "envelopes": [e.to_dict() for e in items],
        "count": len(items),
    }


@router.post("/envelopes/{envelope_id}/send")
@rate_limit(requests_per_minute=30)
async def send_envelope(
    envelope_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Stub send: draft → sent; assigns fake external_id."""
    user_id = _uid(current_user)
    envelope = _get_owned_envelope(db, envelope_id, user_id)
    if envelope.status == "cancelled":
        raise HTTPException(status_code=400, detail="Envelope cancelado")
    if envelope.status == "signed":
        raise HTTPException(status_code=400, detail="Envelope já assinado")
    if envelope.status not in ("draft", "sent"):
        raise HTTPException(status_code=400, detail=f"status inválido: {envelope.status}")

    envelope.status = "sent"
    if not envelope.external_id:
        envelope.external_id = f"stub-{uuid.uuid4().hex[:16]}"
    db.flush()
    db.refresh(envelope)
    return {
        "success": True,
        "envelope": envelope.to_dict(),
        "note": "stub — no real provider notification",
    }


@router.post("/envelopes/{envelope_id}/mark-signed")
@rate_limit(requests_per_minute=30)
async def mark_signed(
    envelope_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Stub mark-signed: sent → signed (or draft → signed for convenience)."""
    user_id = _uid(current_user)
    envelope = _get_owned_envelope(db, envelope_id, user_id)
    if envelope.status == "cancelled":
        raise HTTPException(status_code=400, detail="Envelope cancelado")
    if envelope.status == "signed":
        return {"success": True, "envelope": envelope.to_dict(), "note": "already signed"}

    if envelope.status not in ("draft", "sent"):
        raise HTTPException(status_code=400, detail=f"status inválido: {envelope.status}")

    envelope.status = "signed"
    envelope.signed_at = datetime.now(timezone.utc)
    if not envelope.external_id:
        envelope.external_id = f"stub-{uuid.uuid4().hex[:16]}"
    db.flush()
    db.refresh(envelope)
    return {
        "success": True,
        "envelope": envelope.to_dict(),
        "note": "stub — no real certificate / ICP-Brasil",
    }
