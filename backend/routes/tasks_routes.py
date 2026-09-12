"""
Tarefas do escritório — checklist operacional diário.

Local JWT CRUD. Not a court deadline and not a project-management suite.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import OfficeTask, get_db
from security import get_current_user, rate_limit
from security.xss_protection import sanitize_plain_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["Tarefas"])

VALID_STATUSES = frozenset({"open", "done", "cancelled"})
VALID_PRIORITIES = frozenset({"low", "medium", "high"})


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    client_id: Optional[int] = None
    matter_id: Optional[int] = None
    due_at: Optional[datetime] = None
    priority: str = Field("medium", max_length=20)
    notes: Optional[str] = Field(None, max_length=4000)
    status: str = Field("open", max_length=20)


class TaskStatusPatch(BaseModel):
    status: str = Field(..., min_length=1, max_length=20)


def _uid(current_user) -> int:
    return int(current_user.id)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _get_owned(db: Session, task_id: int, user_id: int) -> OfficeTask:
    row = (
        db.query(OfficeTask)
        .filter(OfficeTask.id == task_id, OfficeTask.user_id == user_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return row


@router.get("")
@rate_limit(requests_per_minute=60)
async def list_tasks(
    status_filter: Optional[str] = Query(None, alias="status"),
    open_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Lista tarefas do usuário (filtro opcional por status)."""
    user_id = _uid(current_user)
    q = db.query(OfficeTask).filter(OfficeTask.user_id == user_id)
    if open_only:
        q = q.filter(OfficeTask.status == "open")
    elif status_filter:
        if status_filter not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail="status inválido")
        q = q.filter(OfficeTask.status == status_filter)
    rows = q.order_by(OfficeTask.due_at.asc(), OfficeTask.id.desc()).all()
    return {
        "success": True,
        "tasks": [r.to_dict() for r in rows],
        "count": len(rows),
    }


@router.post("", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=30)
async def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    status_value = (payload.status or "open").strip().lower()
    priority = (payload.priority or "medium").strip().lower()
    if status_value not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="status inválido")
    if priority not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail="priority inválida")

    title = sanitize_plain_text(payload.title).strip()
    if not title:
        raise HTTPException(status_code=400, detail="title obrigatório")

    notes = sanitize_plain_text(payload.notes) if payload.notes else None
    row = OfficeTask(
        user_id=_uid(current_user),
        client_id=payload.client_id,
        matter_id=payload.matter_id,
        title=title,
        status=status_value,
        priority=priority,
        due_at=_as_aware(payload.due_at),
        notes=notes,
        completed_at=_now() if status_value == "done" else None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"success": True, "task": row.to_dict()}


@router.patch("/{task_id}/status")
@rate_limit(requests_per_minute=60)
async def patch_task_status(
    task_id: int,
    payload: TaskStatusPatch,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = _get_owned(db, task_id, _uid(current_user))
    status_value = payload.status.strip().lower()
    if status_value not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="status inválido")
    row.status = status_value
    row.completed_at = _now() if status_value == "done" else None
    db.commit()
    db.refresh(row)
    return {"success": True, "task": row.to_dict()}
