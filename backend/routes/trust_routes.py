"""
Trust accounting stub (IOLTA-style client funds ledger).

NOT real banking / NOT PIX / NOT bank integration — pragmatic ledger only.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import TrustAccount, TrustLedgerEntry, get_db
from security import get_current_user, rate_limit
from security.xss_protection import sanitize_plain_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trust", tags=["Trust Accounting"])

VALID_ENTRY_TYPES = frozenset({"deposit", "withdrawal", "transfer", "adjustment"})


class TrustAccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    currency: str = Field("BRL", max_length=10)
    organization_id: Optional[int] = None


class TrustEntryCreate(BaseModel):
    entry_type: str = Field(..., max_length=30)
    amount: float = Field(..., gt=0)
    memo: Optional[str] = Field(None, max_length=2000)
    client_id: Optional[int] = None
    matter_id: Optional[int] = None


def _uid(current_user) -> int:
    return int(current_user.id)


def _get_owned_account(
    db: Session, account_id: int, user_id: int
) -> TrustAccount:
    account = (
        db.query(TrustAccount)
        .filter(TrustAccount.id == account_id, TrustAccount.user_id == user_id)
        .first()
    )
    if not account:
        raise HTTPException(status_code=404, detail="Conta trust não encontrada")
    return account


def _balance_from_type_totals(by_type: dict) -> float:
    """deposits − withdrawals − transfers (+ adjustments). Transfer = transfer-out."""
    deposits = float(by_type.get("deposit", 0.0) or 0.0)
    withdrawals = float(by_type.get("withdrawal", 0.0) or 0.0)
    transfers = float(by_type.get("transfer", 0.0) or 0.0)
    adjustments = float(by_type.get("adjustment", 0.0) or 0.0)
    return round(deposits - withdrawals - transfers + adjustments, 2)


def _compute_balance(db: Session, account_id: int) -> float:
    """balance = sum(deposits) - sum(withdrawals) - sum(transfers) + sum(adjustments signed).

    For this stub, transfer is treated as transfer-out (reduces balance).
    Adjustment amount is applied as signed: callers should pass positive amount;
    we add deposit-style and subtract if entry_type were negative — here amount > 0
    and adjustment increases balance (pragmatic stub). Use withdrawal for decreases.
    """
    rows = (
        db.query(TrustLedgerEntry.entry_type, func.coalesce(func.sum(TrustLedgerEntry.amount), 0.0))
        .filter(TrustLedgerEntry.trust_account_id == account_id)
        .group_by(TrustLedgerEntry.entry_type)
        .all()
    )
    by_type = {etype: float(total or 0) for etype, total in rows}
    return _balance_from_type_totals(by_type)


def _compute_reconcile(db: Session, account_id: int) -> dict:
    """Three-way stub: book vs client subtotals vs unallocated (client_id IS NULL).

    Not a bank feed — book_balance is the ledger only.
    """
    book_balance = _compute_balance(db, account_id)

    # Per-client totals (client_id not null)
    client_rows = (
        db.query(
            TrustLedgerEntry.client_id,
            TrustLedgerEntry.entry_type,
            func.coalesce(func.sum(TrustLedgerEntry.amount), 0.0),
        )
        .filter(
            TrustLedgerEntry.trust_account_id == account_id,
            TrustLedgerEntry.client_id.isnot(None),
        )
        .group_by(TrustLedgerEntry.client_id, TrustLedgerEntry.entry_type)
        .all()
    )
    by_client: dict[int, dict] = {}
    for client_id, etype, total in client_rows:
        bucket = by_client.setdefault(int(client_id), {})
        bucket[etype] = float(total or 0)

    client_subtotals = [
        {"client_id": cid, "balance": _balance_from_type_totals(types)}
        for cid, types in sorted(by_client.items())
    ]

    # Unallocated = entries with client_id null
    unalloc_rows = (
        db.query(TrustLedgerEntry.entry_type, func.coalesce(func.sum(TrustLedgerEntry.amount), 0.0))
        .filter(
            TrustLedgerEntry.trust_account_id == account_id,
            TrustLedgerEntry.client_id.is_(None),
        )
        .group_by(TrustLedgerEntry.entry_type)
        .all()
    )
    unallocated_balance = _balance_from_type_totals(
        {etype: float(total or 0) for etype, total in unalloc_rows}
    )

    return {
        "book_balance": book_balance,
        "client_subtotals": client_subtotals,
        "unallocated_balance": unallocated_balance,
        "as_of": datetime.now(timezone.utc).isoformat(),
        "note": "stub — not bank feed",
    }


@router.post("/accounts", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=30)
async def create_trust_account(
    payload: TrustAccountCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Cria conta de custódia (ledger local — sem banco/PIX)."""
    user_id = _uid(current_user)
    name = sanitize_plain_text(payload.name) or ""
    if len(name) < 1:
        raise HTTPException(status_code=400, detail="name inválido")

    currency = (sanitize_plain_text(payload.currency) or "BRL").strip().upper()[:10]
    account = TrustAccount(
        user_id=user_id,
        organization_id=payload.organization_id,
        name=name,
        currency=currency or "BRL",
    )
    db.add(account)
    db.flush()
    db.refresh(account)
    return {"success": True, "account": account.to_dict()}


@router.get("/accounts")
@rate_limit(requests_per_minute=60)
async def list_trust_accounts(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = _uid(current_user)
    accounts = (
        db.query(TrustAccount)
        .filter(TrustAccount.user_id == user_id)
        .order_by(TrustAccount.created_at.desc())
        .all()
    )
    items = []
    for acc in accounts:
        data = acc.to_dict()
        data["balance"] = _compute_balance(db, acc.id)
        items.append(data)
    return {"success": True, "accounts": items, "count": len(items)}


@router.post("/accounts/{account_id}/entries", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=60)
async def create_ledger_entry(
    account_id: int,
    payload: TrustEntryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = _uid(current_user)
    account = _get_owned_account(db, account_id, user_id)

    entry_type = (payload.entry_type or "").strip().lower()
    if entry_type not in VALID_ENTRY_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"entry_type inválido; use: {', '.join(sorted(VALID_ENTRY_TYPES))}",
        )
    if payload.amount is None or float(payload.amount) <= 0:
        raise HTTPException(status_code=400, detail="amount deve ser > 0")

    memo = sanitize_plain_text(payload.memo) if payload.memo else None
    entry = TrustLedgerEntry(
        trust_account_id=account.id,
        client_id=payload.client_id,
        matter_id=payload.matter_id,
        entry_type=entry_type,
        amount=float(payload.amount),
        memo=memo,
        created_by_user_id=user_id,
    )
    db.add(entry)
    db.flush()
    db.refresh(entry)
    return {
        "success": True,
        "entry": entry.to_dict(),
        "balance": _compute_balance(db, account.id),
    }


@router.get("/accounts/{account_id}/ledger")
@rate_limit(requests_per_minute=60)
async def get_ledger(
    account_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = _uid(current_user)
    account = _get_owned_account(db, account_id, user_id)
    entries = (
        db.query(TrustLedgerEntry)
        .filter(TrustLedgerEntry.trust_account_id == account.id)
        .order_by(TrustLedgerEntry.created_at.desc(), TrustLedgerEntry.id.desc())
        .all()
    )
    return {
        "success": True,
        "account": account.to_dict(),
        "entries": [e.to_dict() for e in entries],
        "count": len(entries),
        "balance": _compute_balance(db, account.id),
    }


@router.get("/accounts/{account_id}/balance")
@rate_limit(requests_per_minute=60)
async def get_balance(
    account_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = _uid(current_user)
    account = _get_owned_account(db, account_id, user_id)
    balance = _compute_balance(db, account.id)
    return {
        "success": True,
        "account_id": account.id,
        "currency": account.currency,
        "balance": balance,
        "formula": "deposits - withdrawals - transfers (+ adjustments)",
        "disclaimer": "Stub ledger only — not a bank balance / no PIX",
    }


@router.get("/accounts/{account_id}/reconcile")
@rate_limit(requests_per_minute=60)
async def get_reconcile(
    account_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Three-way reconciliation stub: book vs client subtotals vs unallocated.

    client_id null → unallocated_balance. Not a bank feed.
    """
    user_id = _uid(current_user)
    account = _get_owned_account(db, account_id, user_id)
    payload = _compute_reconcile(db, account.id)
    return {
        "success": True,
        "account_id": account.id,
        "currency": account.currency,
        **payload,
    }
