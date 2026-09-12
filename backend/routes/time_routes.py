"""
Time Entry MVP — horas faturáveis (PMS must-have 2026).
CRUD JWT + resumo de minutos / valor estimado + fatura a partir de horas.
"""

from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import Client, Invoice, Matter, TimeEntry, User, get_db
from routes.finance_routes import generate_invoice_number
from security import get_current_user, rate_limit
from security.xss_protection import sanitize_plain_text
from services.activity_feed_service import log_activity

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/time", tags=["Time Entries"])


class TimeEntryCreate(BaseModel):
    description: str = Field(..., min_length=1)
    minutes: int = Field(..., gt=0, le=24 * 60)
    hourly_rate: Optional[float] = Field(None, ge=0)
    billable: bool = True
    work_date: Optional[date] = None
    matter_id: Optional[int] = None
    client_id: Optional[int] = None


class TimeEntryUpdate(BaseModel):
    description: Optional[str] = Field(None, min_length=1)
    minutes: Optional[int] = Field(None, gt=0, le=24 * 60)
    hourly_rate: Optional[float] = Field(None, ge=0)
    billable: Optional[bool] = None
    work_date: Optional[date] = None
    matter_id: Optional[int] = None
    client_id: Optional[int] = None


class TimeEntriesInvoiceRequest(BaseModel):
    entry_ids: Optional[List[int]] = None
    client_id: Optional[int] = None
    matter_id: Optional[int] = None
    due_days: int = Field(7, ge=1, le=90)


def _entry_amount(entry: TimeEntry) -> float:
    if not entry.billable or entry.hourly_rate is None or not entry.minutes:
        return 0.0
    amount = (entry.minutes / 60.0) * float(entry.hourly_rate)
    return round(amount, 2) if amount > 0 else 0.0


def _get_owned_entry(db: Session, entry_id: int, user_id: int) -> TimeEntry:
    entry = (
        db.query(TimeEntry)
        .filter(TimeEntry.id == entry_id, TimeEntry.user_id == user_id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry não encontrado")
    return entry


def _validate_client_ownership(
    db: Session, client_id: Optional[int], user_id: int
) -> Optional[int]:
    if client_id is None:
        return None
    client = (
        db.query(Client)
        .filter(Client.id == client_id, Client.user_id == user_id)
        .first()
    )
    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="client_id inválido ou não pertence ao usuário",
        )
    return client_id


def _validate_matter_ownership(
    db: Session, matter_id: Optional[int], user_id: int
) -> Optional[int]:
    if matter_id is None:
        return None
    matter = (
        db.query(Matter)
        .filter(Matter.id == matter_id, Matter.user_id == user_id)
        .first()
    )
    if not matter:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="matter_id inválido ou não pertence ao usuário",
        )
    return matter_id


def _parse_work_date(value: Optional[date]) -> date:
    return value or date.today()


@router.get("/entries")
@rate_limit(requests_per_minute=60)
async def list_time_entries(
    billable: Optional[bool] = Query(None),
    matter_id: Optional[int] = Query(None),
    client_id: Optional[int] = Query(None),
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista time entries do usuário autenticado."""
    query = db.query(TimeEntry).filter(TimeEntry.user_id == current_user.id)

    if billable is not None:
        query = query.filter(TimeEntry.billable == billable)
    if matter_id is not None:
        query = query.filter(TimeEntry.matter_id == matter_id)
    if client_id is not None:
        query = query.filter(TimeEntry.client_id == client_id)
    if from_date is not None:
        query = query.filter(TimeEntry.work_date >= from_date)
    if to_date is not None:
        query = query.filter(TimeEntry.work_date <= to_date)

    total = query.count()
    entries = (
        query.order_by(TimeEntry.work_date.desc(), TimeEntry.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "entries": [e.to_dict() for e in entries],
        "pagination": {
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit if total else 0,
            "limit": limit,
        },
    }


@router.post("/entries", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=30)
async def create_time_entry(
    payload: TimeEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cria um lançamento de horas."""
    description = sanitize_plain_text(payload.description)
    if not description:
        raise HTTPException(status_code=400, detail="description é obrigatória")

    client_id = _validate_client_ownership(db, payload.client_id, current_user.id)
    matter_id = _validate_matter_ownership(db, payload.matter_id, current_user.id)

    entry = TimeEntry(
        user_id=current_user.id,
        matter_id=matter_id,
        client_id=client_id,
        description=description,
        minutes=payload.minutes,
        hourly_rate=payload.hourly_rate,
        billable=payload.billable if payload.billable is not None else True,
        work_date=_parse_work_date(payload.work_date),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    logger.info("TimeEntry criado: %s (user=%s)", entry.id, current_user.id)
    return {"message": "Time entry criado com sucesso", "entry": entry.to_dict()}


@router.get("/summary")
@rate_limit(requests_per_minute=60)
async def time_summary(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    matter_id: Optional[int] = Query(None),
    client_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resumo: total de minutos e estimativa de valor faturável."""
    query = db.query(TimeEntry).filter(TimeEntry.user_id == current_user.id)

    if from_date is not None:
        query = query.filter(TimeEntry.work_date >= from_date)
    if to_date is not None:
        query = query.filter(TimeEntry.work_date <= to_date)
    if matter_id is not None:
        query = query.filter(TimeEntry.matter_id == matter_id)
    if client_id is not None:
        query = query.filter(TimeEntry.client_id == client_id)

    entries = query.all()
    total_minutes = sum(e.minutes or 0 for e in entries)
    billable_minutes = sum(e.minutes or 0 for e in entries if e.billable)
    non_billable_minutes = total_minutes - billable_minutes

    billable_amount = 0.0
    for e in entries:
        if e.billable and e.hourly_rate is not None and e.minutes:
            billable_amount += (e.minutes / 60.0) * float(e.hourly_rate)

    return {
        "total_entries": len(entries),
        "total_minutes": total_minutes,
        "billable_minutes": billable_minutes,
        "non_billable_minutes": non_billable_minutes,
        "billable_amount_estimate": round(billable_amount, 2),
        "total_hours": round(total_minutes / 60.0, 2),
        "billable_hours": round(billable_minutes / 60.0, 2),
    }


@router.patch("/entries/{entry_id}")
@rate_limit(requests_per_minute=40)
async def update_time_entry(
    entry_id: int,
    payload: TimeEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atualiza um time entry (ownership obrigatório)."""
    entry = _get_owned_entry(db, entry_id, current_user.id)
    data = payload.model_dump(exclude_unset=True)

    if "description" in data:
        description = sanitize_plain_text(data["description"] or "")
        if not description:
            raise HTTPException(status_code=400, detail="description é obrigatória")
        entry.description = description

    if "minutes" in data and data["minutes"] is not None:
        entry.minutes = data["minutes"]

    if "hourly_rate" in data:
        entry.hourly_rate = data["hourly_rate"]

    if "billable" in data and data["billable"] is not None:
        entry.billable = data["billable"]

    if "work_date" in data and data["work_date"] is not None:
        entry.work_date = data["work_date"]

    if "client_id" in data:
        entry.client_id = _validate_client_ownership(
            db, data["client_id"], current_user.id
        )

    if "matter_id" in data:
        entry.matter_id = _validate_matter_ownership(
            db, data["matter_id"], current_user.id
        )

    db.commit()
    db.refresh(entry)
    return {"message": "Time entry atualizado", "entry": entry.to_dict()}


@router.delete("/entries/{entry_id}")
@rate_limit(requests_per_minute=30)
async def delete_time_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove um time entry (ownership obrigatório)."""
    entry = _get_owned_entry(db, entry_id, current_user.id)
    db.delete(entry)
    db.commit()
    return {"message": "Time entry removido"}


@router.post("/entries/invoice", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=20)
async def create_invoice_from_time_entries(
    payload: TimeEntriesInvoiceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cria fatura (draft/pending) a partir de time entries faturáveis.
    - Com entry_ids: usa esses lançamentos billable do usuário (não faturados).
    - Sem entry_ids: todos os uninvoiced billable do client_id e/ou matter_id.
    """
    entry_ids = payload.entry_ids or None
    if entry_ids is not None and len(entry_ids) == 0:
        raise HTTPException(status_code=400, detail="entry_ids não pode ser vazio")

    client_id = _validate_client_ownership(db, payload.client_id, current_user.id)
    matter_id = _validate_matter_ownership(db, payload.matter_id, current_user.id)

    query = db.query(TimeEntry).filter(
        TimeEntry.user_id == current_user.id,
        TimeEntry.billable.is_(True),
        TimeEntry.invoiced_at.is_(None),
    )

    if entry_ids is not None:
        unique_ids = list(dict.fromkeys(entry_ids))
        entries = query.filter(TimeEntry.id.in_(unique_ids)).all()
        found_ids = {e.id for e in entries}
        missing = [eid for eid in unique_ids if eid not in found_ids]
        if missing:
            # IDOR / já faturado / inexistente — não vaza ownership
            raise HTTPException(
                status_code=404,
                detail="Um ou mais time entries não foram encontrados ou já estão faturados",
            )
    else:
        if client_id is None and matter_id is None:
            raise HTTPException(
                status_code=400,
                detail="Informe entry_ids ou client_id/matter_id",
            )
        if client_id is not None:
            query = query.filter(TimeEntry.client_id == client_id)
        if matter_id is not None:
            query = query.filter(TimeEntry.matter_id == matter_id)
        entries = query.order_by(TimeEntry.work_date.asc(), TimeEntry.id.asc()).all()

    billable_entries = []
    total_amount = 0.0
    for entry in entries:
        amount = _entry_amount(entry)
        if amount <= 0:
            continue
        billable_entries.append(entry)
        total_amount += amount

    if not billable_entries or total_amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Nenhum lançamento faturável com taxa horária encontrado",
        )

    total_amount = round(total_amount, 2)
    total_cents = int(round(total_amount * 100))
    now = datetime.now(timezone.utc)
    entry_id_list = [e.id for e in billable_entries]
    invoice_client_id = client_id
    if invoice_client_id is None:
        client_ids = {e.client_id for e in billable_entries if e.client_id is not None}
        if len(client_ids) == 1:
            invoice_client_id = next(iter(client_ids))

    description = (
        f"Fatura de horas ({len(billable_entries)} lançamentos): "
        f"entries={entry_id_list}"
    )
    if len(description) > 500:
        description = description[:497] + "..."

    invoice = Invoice(
        user_id=current_user.id,
        client_id=invoice_client_id,
        invoice_number=generate_invoice_number(),
        description=description,
        amount_cents=total_cents,
        discount_cents=0,
        total_cents=total_cents,
        due_date=now + timedelta(days=payload.due_days),
        invoice_type="time_entries",
        status="pending",
        payment_method="boleto",
    )
    db.add(invoice)

    for entry in billable_entries:
        entry.invoiced_at = now

    db.commit()
    db.refresh(invoice)

    try:
        log_activity(
            db,
            current_user.id,
            "time.invoice",
            f"Fatura de horas {invoice.invoice_number} ({len(billable_entries)} lançamentos)",
            entity_type="invoice",
            entity_id=invoice.id,
        )
    except Exception:
        pass

    logger.info(
        "Invoice from time: %s total=R$%.2f entries=%s user=%s",
        invoice.invoice_number,
        total_amount,
        entry_id_list,
        current_user.id,
    )

    invoice_payload = invoice.to_dict()
    return {
        "message": "Fatura criada a partir de time entries",
        "invoice": invoice_payload,
        "entry_ids": entry_id_list,
        "entries_count": len(billable_entries),
        "total": total_amount,
        **invoice_payload,
    }