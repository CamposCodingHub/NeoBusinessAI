"""LGPD / compliance stubs — WhatsApp consent."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import User, get_db
from security import get_current_user, rate_limit
from services.whatsapp_consent_service import (
    VALID_SOURCES,
    grant_consent,
    list_consents,
    revoke_consent,
)

router = APIRouter(prefix="/compliance", tags=["Compliance"])


class WhatsAppConsentCreate(BaseModel):
    client_id: Optional[int] = None
    phone: Optional[str] = Field(None, max_length=80)
    source: str = Field("manual", max_length=50)


class WhatsAppConsentRevoke(BaseModel):
    consent_id: Optional[int] = None
    client_id: Optional[int] = None
    phone: Optional[str] = Field(None, max_length=80)


def _uid(current_user: User) -> int:
    return int(current_user.id)


@router.post("/whatsapp-consent", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=60)
async def create_whatsapp_consent(
    payload: WhatsAppConsentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.client_id is None and not (payload.phone or "").strip():
        raise HTTPException(
            status_code=400,
            detail="informe client_id ou phone",
        )
    src = (payload.source or "manual").strip().lower()
    if src not in VALID_SOURCES:
        raise HTTPException(status_code=400, detail="source deve ser intake|manual")
    try:
        row = grant_consent(
            db,
            _uid(current_user),
            client_id=payload.client_id,
            phone=payload.phone,
            source=src,
        )
        db.commit()
        db.refresh(row)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"consent": row.to_dict()}


@router.get("/whatsapp-consent")
@rate_limit(requests_per_minute=60)
async def get_whatsapp_consent(
    client_id: Optional[int] = Query(None),
    include_revoked: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = list_consents(
        db,
        _uid(current_user),
        client_id=client_id,
        include_revoked=include_revoked,
    )
    return {"consents": items, "count": len(items)}


@router.post("/whatsapp-consent/revoke")
@rate_limit(requests_per_minute=30)
async def revoke_whatsapp_consent(
    payload: WhatsAppConsentRevoke,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.consent_id is None and payload.client_id is None and not (
        payload.phone or ""
    ).strip():
        raise HTTPException(
            status_code=400,
            detail="informe consent_id, client_id ou phone",
        )
    try:
        rows = revoke_consent(
            db,
            _uid(current_user),
            consent_id=payload.consent_id,
            client_id=payload.client_id,
            phone=payload.phone,
        )
        db.commit()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not rows:
        raise HTTPException(status_code=404, detail="consentimento ativo nao encontrado")
    return {
        "revoked": [r.to_dict() for r in rows],
        "count": len(rows),
    }
