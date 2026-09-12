"""WhatsApp LGPD consent stub helpers."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from database import WhatsAppConsent

VALID_SOURCES = frozenset({"intake", "manual"})
CONSENT_REQUIRED_CODE = "WHATSAPP_CONSENT_REQUIRED"


def normalize_phone(phone: Optional[str]) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if digits and not digits.startswith("55") and len(digits) <= 11:
        digits = "55" + digits
    return digits


def hash_phone(phone: Optional[str]) -> Optional[str]:
    digits = normalize_phone(phone)
    if not digits:
        return None
    return hashlib.sha256(digits.encode("utf-8")).hexdigest()


def _active_query(db: Session, user_id: int):
    return (
        db.query(WhatsAppConsent)
        .filter(
            WhatsAppConsent.user_id == int(user_id),
            WhatsAppConsent.channel == "whatsapp",
            WhatsAppConsent.revoked_at.is_(None),
        )
    )


def has_active_consent(
    db: Session,
    user_id: int,
    *,
    client_id: Optional[int] = None,
    phone: Optional[str] = None,
) -> bool:
    """True if an active WhatsApp consent matches client_id and/or phone_hash."""
    q = _active_query(db, user_id)
    phone_h = hash_phone(phone)
    if client_id is not None:
        by_client = q.filter(WhatsAppConsent.client_id == int(client_id)).first()
        if by_client:
            return True
    if phone_h:
        by_phone = q.filter(WhatsAppConsent.phone_hash == phone_h).first()
        if by_phone:
            return True
    return False


def grant_consent(
    db: Session,
    user_id: int,
    *,
    client_id: Optional[int] = None,
    phone: Optional[str] = None,
    source: str = "manual",
) -> WhatsAppConsent:
    src = (source or "manual").strip().lower()
    if src not in VALID_SOURCES:
        raise ValueError("source must be intake|manual")

    phone_digits = normalize_phone(phone) or None
    phone_h = hash_phone(phone)

    existing = None
    q = _active_query(db, user_id)
    if client_id is not None:
        existing = q.filter(WhatsAppConsent.client_id == int(client_id)).first()
    if existing is None and phone_h:
        existing = q.filter(WhatsAppConsent.phone_hash == phone_h).first()

    now = datetime.now(timezone.utc)
    if existing:
        existing.consented_at = now
        existing.source = src
        existing.revoked_at = None
        if phone_digits:
            existing.phone = phone_digits
            existing.phone_hash = phone_h
        if client_id is not None:
            existing.client_id = int(client_id)
        db.flush()
        return existing

    row = WhatsAppConsent(
        user_id=int(user_id),
        client_id=int(client_id) if client_id is not None else None,
        phone=phone_digits,
        phone_hash=phone_h,
        consented_at=now,
        channel="whatsapp",
        source=src,
        revoked_at=None,
    )
    db.add(row)
    db.flush()
    return row


def revoke_consent(
    db: Session,
    user_id: int,
    *,
    consent_id: Optional[int] = None,
    client_id: Optional[int] = None,
    phone: Optional[str] = None,
) -> List[WhatsAppConsent]:
    q = _active_query(db, user_id)
    if consent_id is not None:
        q = q.filter(WhatsAppConsent.id == int(consent_id))
    elif client_id is not None:
        q = q.filter(WhatsAppConsent.client_id == int(client_id))
    elif phone:
        phone_h = hash_phone(phone)
        if not phone_h:
            return []
        q = q.filter(WhatsAppConsent.phone_hash == phone_h)
    else:
        raise ValueError("consent_id, client_id or phone required to revoke")

    rows = q.all()
    now = datetime.now(timezone.utc)
    for row in rows:
        row.revoked_at = now
    db.flush()
    return rows


def list_consents(
    db: Session,
    user_id: int,
    *,
    client_id: Optional[int] = None,
    include_revoked: bool = False,
) -> List[Dict[str, Any]]:
    q = db.query(WhatsAppConsent).filter(WhatsAppConsent.user_id == int(user_id))
    if client_id is not None:
        q = q.filter(WhatsAppConsent.client_id == int(client_id))
    if not include_revoked:
        q = q.filter(WhatsAppConsent.revoked_at.is_(None))
    rows = q.order_by(WhatsAppConsent.consented_at.desc()).all()
    return [r.to_dict() for r in rows]
