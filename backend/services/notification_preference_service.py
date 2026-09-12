"""Preferências de alerta de prazos + preview do digest (sem envio real)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from database import Deadline, NotificationPreference

DEFAULT_DAYS_BEFORE = 3


def get_or_create_notification_preference(
    db: Session, user_id: int
) -> NotificationPreference:
    """Retorna preferências do usuário; cria defaults se ainda não existir."""
    pref = (
        db.query(NotificationPreference)
        .filter(NotificationPreference.user_id == int(user_id))
        .first()
    )
    if pref:
        return pref

    pref = NotificationPreference(
        user_id=int(user_id),
        email_enabled=True,
        whatsapp_enabled=False,
        days_before=DEFAULT_DAYS_BEFORE,
        quiet_hours_start=None,
        quiet_hours_end=None,
    )
    db.add(pref)
    db.commit()
    db.refresh(pref)
    return pref


def update_notification_preference(
    db: Session,
    user_id: int,
    *,
    email_enabled: Optional[bool] = None,
    whatsapp_enabled: Optional[bool] = None,
    days_before: Optional[int] = None,
    quiet_hours_start: Optional[int] = None,
    quiet_hours_end: Optional[int] = None,
    clear_quiet_hours: bool = False,
) -> NotificationPreference:
    """Atualiza campos fornecidos; get-or-create se necessário."""
    pref = get_or_create_notification_preference(db, user_id)

    if email_enabled is not None:
        pref.email_enabled = bool(email_enabled)
    if whatsapp_enabled is not None:
        pref.whatsapp_enabled = bool(whatsapp_enabled)
    if days_before is not None:
        pref.days_before = int(days_before)
    if clear_quiet_hours:
        pref.quiet_hours_start = None
        pref.quiet_hours_end = None
    else:
        if quiet_hours_start is not None:
            pref.quiet_hours_start = quiet_hours_start
        if quiet_hours_end is not None:
            pref.quiet_hours_end = quiet_hours_end

    pref.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(pref)
    return pref


def list_deadlines_needing_alert(
    db: Session, user_id: int, days_before: Optional[int] = None
) -> List[Deadline]:
    """
    Prazos pendentes do usuário com due_date até agora + days_before.

    Inclui atrasados (due_date no passado). Não envia email — só lista candidatos.
    """
    if days_before is None:
        pref = (
            db.query(NotificationPreference)
            .filter(NotificationPreference.user_id == int(user_id))
            .first()
        )
        days_before = int(pref.days_before) if pref else DEFAULT_DAYS_BEFORE

    days = max(0, int(days_before))
    cutoff = datetime.utcnow() + timedelta(days=days)

    return (
        db.query(Deadline)
        .filter(
            Deadline.user_id == int(user_id),
            Deadline.is_completed == False,  # noqa: E712
            Deadline.due_date.isnot(None),
            Deadline.due_date <= cutoff,
        )
        .order_by(Deadline.due_date.asc())
        .all()
    )
