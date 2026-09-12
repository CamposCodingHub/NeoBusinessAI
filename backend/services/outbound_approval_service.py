"""Human-approval gate for WhatsApp outbound messages.

AI agents and automated flows (lex / deadline / finance) must queue messages
for professional review instead of auto-sending to clients.

Production path (sim-real / finance / deadlines):
  call queue_whatsapp_for_approval(...) → status=pending → human approves
  via POST /approvals/outbound/{id}/approve → Twilio send (or simulated).
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from database import OutboundMessageApproval, WhatsAppConfig

logger = logging.getLogger(__name__)

VALID_SOURCES = frozenset({"lex", "deadline", "finance", "manual"})
VALID_STATUSES = frozenset({"pending", "approved", "rejected", "sent", "failed"})


def _normalize_phone(recipient: str) -> str:
    digits = re.sub(r"\D", "", recipient or "")
    if digits and not digits.startswith("55") and len(digits) <= 11:
        digits = "55" + digits
    return digits


def queue_whatsapp_for_approval(
    db: Session,
    user_id: int,
    recipient: str,
    body: str,
    source: str = "manual",
    related_matter_id: Optional[int] = None,
    *,
    commit: bool = False,
) -> OutboundMessageApproval:
    """Enqueue a WhatsApp outbound message as pending human approval.

    Used by finance/deadline/lex automation later — never sends immediately.
    """
    src = (source or "manual").strip().lower()
    if src not in VALID_SOURCES:
        src = "manual"

    cleaned_body = (body or "").strip()
    if not cleaned_body:
        raise ValueError("body is required")

    phone = _normalize_phone(recipient)
    if not phone:
        raise ValueError("recipient is required")

    row = OutboundMessageApproval(
        user_id=int(user_id),
        channel="whatsapp",
        recipient=phone,
        body=cleaned_body,
        status="pending",
        source=src,
        related_matter_id=related_matter_id,
    )
    db.add(row)
    db.flush()
    if commit:
        db.commit()
        db.refresh(row)
    logger.info(
        "Queued WhatsApp approval id=%s user=%s source=%s recipient=%s",
        row.id,
        user_id,
        src,
        phone,
    )
    return row


def try_send_whatsapp(
    db: Session,
    user_id: int,
    recipient: str,
    body: str,
) -> Dict[str, Any]:
    """Attempt Twilio/Evolution send using stored WhatsAppConfig.

    Returns dict with keys: sent (bool), simulated (bool), error (optional str),
    provider_message_id (optional).
    """
    config = (
        db.query(WhatsAppConfig)
        .filter(WhatsAppConfig.user_id == user_id, WhatsAppConfig.is_active == True)  # noqa: E712
        .first()
    )
    if not config:
        return {
            "sent": False,
            "simulated": True,
            "error": None,
            "note": "WhatsApp não configurado — aprovação registrada (envio simulado)",
        }

    phone = _normalize_phone(recipient)
    try:
        import requests
    except ImportError:
        return {
            "sent": False,
            "simulated": True,
            "error": None,
            "note": "requests indisponível — aprovação registrada (envio simulado)",
        }

    try:
        if config.provider == "twilio":
            if not (config.twilio_account_sid and config.twilio_auth_token and config.twilio_phone_number):
                return {
                    "sent": False,
                    "simulated": True,
                    "error": None,
                    "note": "Credenciais Twilio incompletas — envio simulado",
                }
            response = requests.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{config.twilio_account_sid}/Messages.json",
                auth=(config.twilio_account_sid, config.twilio_auth_token),
                data={
                    "From": f"whatsapp:{config.twilio_phone_number}",
                    "To": f"whatsapp:+{phone}",
                    "Body": body,
                },
                timeout=30,
            )
            if response.status_code == 201:
                sid = response.json().get("sid")
                return {"sent": True, "simulated": False, "provider_message_id": sid}
            return {
                "sent": False,
                "simulated": False,
                "error": f"Twilio error: {response.status_code}",
            }

        if config.provider == "evolution_api":
            if not (config.evolution_api_url and config.evolution_api_key and config.evolution_instance):
                return {
                    "sent": False,
                    "simulated": True,
                    "error": None,
                    "note": "Evolution API incompleta — envio simulado",
                }
            response = requests.post(
                f"{config.evolution_api_url}/message/sendText/{config.evolution_instance}",
                headers={"apikey": config.evolution_api_key},
                json={"number": phone, "text": body},
                timeout=30,
            )
            if response.status_code in (200, 201):
                mid = (response.json() or {}).get("key", {}).get("id")
                return {"sent": True, "simulated": False, "provider_message_id": mid}
            return {
                "sent": False,
                "simulated": False,
                "error": f"Evolution API error: {response.status_code}",
            }

        return {
            "sent": False,
            "simulated": True,
            "error": None,
            "note": f"Provider {config.provider} sem send implementado — envio simulado",
        }
    except Exception as exc:  # pragma: no cover - network failures
        logger.exception("WhatsApp send failed for user=%s", user_id)
        return {"sent": False, "simulated": False, "error": str(exc)}
