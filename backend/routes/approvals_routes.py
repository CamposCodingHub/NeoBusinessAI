"""
Outbound message approvals — human gate before WhatsApp send.
AI agents must not auto-send to clients without professional approval (2026).
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import OutboundMessageApproval, User, get_db
from security import get_current_user, rate_limit
from security.xss_protection import sanitize_plain_text
from services.whatsapp_consent_service import (
    CONSENT_REQUIRED_CODE,
    has_active_consent,
)
from services.outbound_approval_service import (
    VALID_SOURCES,
    VALID_STATUSES,
    queue_whatsapp_for_approval,
    try_send_whatsapp,
)

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/approvals", tags=["Approvals"])


class OutboundCreate(BaseModel):
    recipient: str = Field(..., min_length=8, max_length=80)
    body: str = Field(..., min_length=1, max_length=4000)
    source: str = Field("manual", max_length=50)
    related_matter_id: Optional[int] = None
    channel: str = Field("whatsapp", max_length=50)


def _validate_source(value: Optional[str]) -> str:
    normalized = (value or "manual").strip().lower()
    if normalized not in VALID_SOURCES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"source inválido; use um de: {', '.join(sorted(VALID_SOURCES))}",
        )
    return normalized


def _validate_status_filter(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"status inválido; use um de: {', '.join(sorted(VALID_STATUSES))}",
        )
    return normalized


def _get_owned(db: Session, approval_id: int, user_id: int) -> OutboundMessageApproval:
    row = (
        db.query(OutboundMessageApproval)
        .filter(
            OutboundMessageApproval.id == approval_id,
            OutboundMessageApproval.user_id == user_id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Aprovação não encontrada")
    return row


@router.get("/outbound")
@rate_limit(requests_per_minute=60)
async def list_outbound_approvals(
    status_filter: Optional[str] = Query("pending", alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista aprovações outbound do escritório (default: pending)."""
    query = db.query(OutboundMessageApproval).filter(
        OutboundMessageApproval.user_id == current_user.id
    )
    st = _validate_status_filter(status_filter)
    if st:
        query = query.filter(OutboundMessageApproval.status == st)

    total = query.count()
    rows = (
        query.order_by(OutboundMessageApproval.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return {
        "approvals": [row.to_dict() for row in rows],
        "pagination": {
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit if total else 0,
            "limit": limit,
        },
    }


@router.post("/outbound", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=30)
async def create_outbound_approval(
    payload: OutboundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cria mensagem outbound pendente de aprovação humana."""
    if (payload.channel or "whatsapp").strip().lower() != "whatsapp":
        raise HTTPException(status_code=400, detail="channel suportado: whatsapp")

    body = sanitize_plain_text(payload.body) or ""
    if not body.strip():
        raise HTTPException(status_code=400, detail="body é obrigatório")

    try:
        row = queue_whatsapp_for_approval(
            db,
            user_id=current_user.id,
            recipient=payload.recipient,
            body=body,
            source=_validate_source(payload.source),
            related_matter_id=payload.related_matter_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    db.flush()
    return {"approval": row.to_dict()}


@router.post("/outbound/{approval_id}/approve")
@rate_limit(requests_per_minute=30)
async def approve_outbound(
    approval_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aprova e tenta enviar via Twilio/WhatsApp; senão marca approved (simulado)."""
    row = _get_owned(db, approval_id, current_user.id)
    if row.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"somente pending pode ser aprovado (status atual: {row.status})",
        )

    # Soft LGPD gate: only when approve path attempts send/simulation
    if not has_active_consent(db, current_user.id, phone=row.recipient):
        raise HTTPException(
            status_code=403,
            detail={
                "code": CONSENT_REQUIRED_CODE,
                "message": (
                    "Consentimento WhatsApp (LGPD) ausente para este destinatario. "
                    "Registre em POST /compliance/whatsapp-consent antes de enviar."
                ),
            },
        )

    row.decided_at = datetime.now(timezone.utc)
    send_result = try_send_whatsapp(db, current_user.id, row.recipient, row.body)

    if send_result.get("sent"):
        row.status = "sent"
        row.error = None
        note = "Enviado via WhatsApp"
    elif send_result.get("simulated"):
        row.status = "approved"
        row.error = send_result.get("note") or "Envio simulado — WhatsApp não configurado"
        note = row.error
    else:
        row.status = "failed"
        row.error = send_result.get("error") or "Falha no envio"
        note = row.error

    db.flush()
    return {
        "approval": row.to_dict(),
        "send": {
            "sent": bool(send_result.get("sent")),
            "simulated": bool(send_result.get("simulated")),
            "note": note,
            "provider_message_id": send_result.get("provider_message_id"),
        },
    }


@router.post("/outbound/{approval_id}/reject")
@rate_limit(requests_per_minute=30)
async def reject_outbound(
    approval_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rejeita mensagem outbound — não envia ao cliente."""
    row = _get_owned(db, approval_id, current_user.id)
    if row.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"somente pending pode ser rejeitado (status atual: {row.status})",
        )

    row.status = "rejected"
    row.decided_at = datetime.now(timezone.utc)
    row.error = None
    db.flush()
    return {"approval": row.to_dict()}
