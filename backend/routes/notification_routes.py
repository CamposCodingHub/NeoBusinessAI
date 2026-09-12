"""
Preferências de notificação de prazos + preview do digest.
Não envia email/WhatsApp neste MVP — só configura e pré-visualiza.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import User, get_db
from security import get_current_user, rate_limit
from services.notification_preference_service import (
    get_or_create_notification_preference,
    list_deadlines_needing_alert,
    update_notification_preference,
)

router = APIRouter(prefix="/notifications", tags=["Notificações"])


class NotificationPreferenceUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    whatsapp_enabled: Optional[bool] = None
    days_before: Optional[int] = Field(None, ge=0, le=90)
    quiet_hours_start: Optional[int] = Field(None, ge=0, le=23)
    quiet_hours_end: Optional[int] = Field(None, ge=0, le=23)
    # true = limpar quiet hours (nullable)
    clear_quiet_hours: Optional[bool] = False


def _validate_quiet_hours(start: Optional[int], end: Optional[int]) -> None:
    if start is None and end is None:
        return
    if (start is None) != (end is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="quiet_hours_start e quiet_hours_end devem ser ambos definidos ou ambos nulos",
        )


@router.get("/preferences")
@rate_limit(requests_per_minute=60)
async def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """GET preferências; cria defaults se ainda não existirem."""
    pref = get_or_create_notification_preference(db, current_user.id)
    return {"preferences": pref.to_dict()}


@router.put("/preferences")
@rate_limit(requests_per_minute=30)
async def put_preferences(
    payload: NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atualiza preferências de alerta de prazos."""
    clear = bool(payload.clear_quiet_hours)
    if not clear:
        # Se o cliente manda explicitamente nulls via clear flag; senão valida pares
        if payload.quiet_hours_start is not None or payload.quiet_hours_end is not None:
            _validate_quiet_hours(payload.quiet_hours_start, payload.quiet_hours_end)

    pref = update_notification_preference(
        db,
        current_user.id,
        email_enabled=payload.email_enabled,
        whatsapp_enabled=payload.whatsapp_enabled,
        days_before=payload.days_before,
        quiet_hours_start=payload.quiet_hours_start,
        quiet_hours_end=payload.quiet_hours_end,
        clear_quiet_hours=clear,
    )
    return {"preferences": pref.to_dict()}


@router.get("/deadline-digest")
@rate_limit(requests_per_minute=30)
async def deadline_digest_preview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Preview do digest: o que seria enviado conforme preferências.
    Não dispara e-mail/WhatsApp.
    """
    pref = get_or_create_notification_preference(db, current_user.id)
    deadlines = list_deadlines_needing_alert(
        db, current_user.id, days_before=pref.days_before
    )

    channels = []
    if pref.email_enabled:
        channels.append("email")
    if pref.whatsapp_enabled:
        channels.append("whatsapp")

    return {
        "preview": True,
        "would_send": bool(channels) and len(deadlines) > 0,
        "channels": channels,
        "preferences": pref.to_dict(),
        "deadlines": [dl.to_dict() for dl in deadlines],
        "count": len(deadlines),
        "note": "Preview only — no email/WhatsApp sent",
    }
