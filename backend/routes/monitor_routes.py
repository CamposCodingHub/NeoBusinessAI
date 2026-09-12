"""
DJEn / intimação monitoring stub.

NOT real CNJ scrape, NOT official DJEn API — local fake poll only.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import IntimacaoEvent, MonitoredProcess, get_db
from security import get_current_user, rate_limit
from security.xss_protection import sanitize_plain_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitor", tags=["DJEn Monitor Stub"])

VALID_STATUSES = frozenset({"active", "paused"})


class ProcessCreate(BaseModel):
    process_number: str = Field(..., min_length=1, max_length=80)
    court: Optional[str] = Field(None, max_length=120)
    oab_number: Optional[str] = Field(None, max_length=40)
    organization_id: Optional[int] = None
    status: str = Field("active", max_length=20)


def _uid(current_user) -> int:
    return int(current_user.id)


def _get_owned_process(
    db: Session, process_id: int, user_id: int
) -> MonitoredProcess:
    proc = (
        db.query(MonitoredProcess)
        .filter(MonitoredProcess.id == process_id, MonitoredProcess.user_id == user_id)
        .first()
    )
    if not proc:
        raise HTTPException(status_code=404, detail="Processo monitorado não encontrado")
    return proc


def _get_owned_event(
    db: Session, event_id: int, user_id: int
) -> IntimacaoEvent:
    event = (
        db.query(IntimacaoEvent)
        .join(
            MonitoredProcess,
            IntimacaoEvent.monitored_process_id == MonitoredProcess.id,
        )
        .filter(IntimacaoEvent.id == event_id, MonitoredProcess.user_id == user_id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Evento de intimação não encontrado")
    return event


@router.post("/processes", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=30)
async def create_process(
    payload: ProcessCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Cadastra processo para monitoramento stub (sem DJEn real)."""
    user_id = _uid(current_user)
    process_number = (sanitize_plain_text(payload.process_number) or "").strip()
    if len(process_number) < 1:
        raise HTTPException(status_code=400, detail="process_number inválido")

    status_val = (payload.status or "active").strip().lower()
    if status_val not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="status deve ser active ou paused",
        )

    court = sanitize_plain_text(payload.court) if payload.court else None
    oab = sanitize_plain_text(payload.oab_number) if payload.oab_number else None

    proc = MonitoredProcess(
        user_id=user_id,
        organization_id=payload.organization_id,
        process_number=process_number[:80],
        court=(court[:120] if court else None),
        oab_number=(oab[:40] if oab else None),
        status=status_val,
    )
    db.add(proc)
    db.flush()
    db.refresh(proc)
    return {
        "success": True,
        "process": proc.to_dict(),
        "note": "stub — no real DJEn / CNJ scrape",
    }


@router.get("/processes")
@rate_limit(requests_per_minute=60)
async def list_processes(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = _uid(current_user)
    items = (
        db.query(MonitoredProcess)
        .filter(MonitoredProcess.user_id == user_id)
        .order_by(MonitoredProcess.created_at.desc())
        .all()
    )
    return {
        "success": True,
        "processes": [p.to_dict() for p in items],
        "count": len(items),
    }


@router.post("/processes/{process_id}/poll-stub")
@rate_limit(requests_per_minute=30)
async def poll_stub(
    process_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Cria 1 IntimacaoEvent fake (claramente stub) e atualiza last_checked_at."""
    user_id = _uid(current_user)
    proc = _get_owned_process(db, process_id, user_id)

    now = datetime.now(timezone.utc)
    stub_ref = f"stub-djen-{uuid.uuid4().hex[:12]}"
    event = IntimacaoEvent(
        monitored_process_id=proc.id,
        title=f"[STUB] Intimação fictícia — {proc.process_number}",
        summary=(
            "Evento GERADO PELO STUB local. "
            "NÃO veio do DJEn, CNJ DataJud, nem de qualquer tribunal. "
            "Use apenas para testar o fluxo de monitoramento."
        ),
        published_at=now,
        source="stub",
        raw_ref=stub_ref,
        acknowledged=False,
    )
    proc.last_checked_at = now
    db.add(event)
    db.flush()
    db.refresh(event)
    db.refresh(proc)
    return {
        "success": True,
        "event": event.to_dict(),
        "process": proc.to_dict(),
        "note": "stub poll — fake intimação only; no real DJEn/API",
    }


@router.get("/processes/{process_id}/events")
@rate_limit(requests_per_minute=60)
async def list_events(
    process_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = _uid(current_user)
    _get_owned_process(db, process_id, user_id)
    items = (
        db.query(IntimacaoEvent)
        .filter(IntimacaoEvent.monitored_process_id == process_id)
        .order_by(IntimacaoEvent.created_at.desc())
        .all()
    )
    return {
        "success": True,
        "events": [e.to_dict() for e in items],
        "count": len(items),
    }


@router.post("/events/{event_id}/ack")
@rate_limit(requests_per_minute=60)
async def acknowledge_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = _uid(current_user)
    event = _get_owned_event(db, event_id, user_id)
    event.acknowledged = True
    db.flush()
    db.refresh(event)
    return {"success": True, "event": event.to_dict()}
