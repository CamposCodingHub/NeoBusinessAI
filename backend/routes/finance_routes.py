"""
Módulo Financeiro - JurisFlow AI
Gestão de faturas, receitas e controle de inadimplência
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
import hashlib
import hmac
import logging
import os
import random
import secrets
import string

from database import get_db, Invoice, Client, User, NfseDraft, CostAdvance, TimeEntry
from security import get_current_user
from services.activity_feed_service import log_activity
from services.pix_payment_service import create_pix_charge
from services.collection_plan_service import (
    EOAB_DISCLAIMER,
    build_collection_plan_for_invoice,
    build_collection_plans,
)
from services.tax_calendar_service import build_tax_calendar
from services.tax_reform_checklist_service import build_tax_reform_checklist

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/finance", tags=["Financeiro"])
compat_router = APIRouter(prefix="/invoices", tags=["Financeiro"])

try:
    from tools.stripe_manager import stripe_manager
except Exception:  # pragma: no cover - ambiente sem stripe
    stripe_manager = None


def generate_invoice_number():
    """Gera número de fatura único: FAT-2025-XXXXX"""
    year = datetime.utcnow().year
    random_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"FAT-{year}-{random_code}"


def _payment_stub_secret() -> str:
    return (
        os.getenv("JWT_SECRET_KEY")
        or os.getenv("SECRET_KEY")
        or "lexscan-dev-payment-stub-secret-key"
    )


def _build_stub_payment_url(invoice_id: int) -> tuple:
    """URL stub assinada + token armazenável (caminho PIX local)."""
    token = secrets.token_urlsafe(24)
    sig = hmac.new(
        _payment_stub_secret().encode("utf-8"),
        f"{invoice_id}:{token}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:16]
    signed = f"{token}.{sig}"
    url = f"https://pay.lexscan.local/i/{invoice_id}?token={signed}"
    return url, signed


def _try_stripe_invoice_checkout(invoice: Invoice, client_email: Optional[str]) -> Optional[str]:
    """Retorna checkout_url Stripe se configurado; caso contrário None."""
    if stripe_manager is None:
        return None
    try:
        if not stripe_manager.is_configured():
            return None
        result = stripe_manager.create_invoice_checkout_session(
            amount_cents=invoice.total_cents or 0,
            invoice_id=invoice.id,
            invoice_number=invoice.invoice_number or "",
            description=invoice.description or "",
            customer_email=client_email,
        )
        if result.get("success") and result.get("checkout_url"):
            return result["checkout_url"]
        logger.info(
            "Stripe checkout indisponível para fatura %s: %s",
            invoice.id,
            result.get("error"),
        )
    except Exception as exc:  # pragma: no cover
        logger.warning("Falha Stripe invoice checkout: %s", exc)
    return None


@compat_router.get("/")
@router.get("/invoices")
async def list_invoices(
    status: Optional[str] = Query(None, description="pending, paid, overdue, cancelled"),
    client_id: Optional[int] = Query(None),
    days: Optional[int] = Query(None, description="Faturas dos últimos N dias"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista todas as faturas do usuário (paginado)"""
    query = db.query(Invoice).filter(Invoice.user_id == current_user.id)
    
    if status:
        query = query.filter(Invoice.status == status)
    
    if client_id:
        query = query.filter(Invoice.client_id == client_id)
    
    if days:
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = query.filter(Invoice.created_at >= cutoff)
    
    # Total count for pagination
    total = query.count()
    
    # Apply pagination
    invoices = query.order_by(Invoice.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    # Enriquecer com dados do cliente
    result = []
    for inv in invoices:
        inv_dict = inv.to_dict()
        if inv.client_id:
            client = db.query(Client).filter(Client.id == inv.client_id).first()
            inv_dict["client_name"] = client.name if client else "Cliente não encontrado"
        else:
            inv_dict["client_name"] = "Sem cliente vinculado"
        result.append(inv_dict)
    
    return {
        "invoices": result,
        "pagination": {
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit,
            "limit": limit
        }
    }


@compat_router.post("/", status_code=status.HTTP_201_CREATED)
@router.post("/invoices", status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cria uma nova fatura"""
    try:
        if invoice_data.get("total_cents") is not None:
            total_cents = int(invoice_data.get("total_cents", 0))
            amount_cents = int(invoice_data.get("amount_cents", total_cents))
            discount_cents = int(invoice_data.get("discount_cents", max(0, amount_cents - total_cents)))
        else:
            amount_value = invoice_data.get("amount")
            if amount_value is None:
                amount_value = invoice_data.get("total", 0)
            discount_value = invoice_data.get("discount", 0)
            amount_cents = int(float(amount_value or 0) * 100)
            discount_cents = int(float(discount_value or 0) * 100)
            total_cents = amount_cents - discount_cents
        
        # Calcular data de vencimento
        due_days = invoice_data.get("due_days", 7)
        due_date = invoice_data.get("due_date")
        if due_date:
            if isinstance(due_date, str):
                due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
        else:
            due_date = datetime.utcnow() + timedelta(days=due_days)
        
        invoice = Invoice(
            user_id=current_user.id,
            client_id=invoice_data.get("client_id"),
            document_id=invoice_data.get("document_id"),
            invoice_number=generate_invoice_number(),
            description=invoice_data.get("description", ""),
            amount_cents=amount_cents,
            discount_cents=discount_cents,
            total_cents=total_cents,
            due_date=due_date,
            invoice_type=invoice_data.get("invoice_type", "service"),
            status="pending",
            payment_method=invoice_data.get("payment_method", "boleto")
        )
        
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        
        logger.info(f"Fatura criada: {invoice.invoice_number} - R$ {total_cents/100}")

        invoice_payload = invoice.to_dict()
        return {
            "message": "Fatura criada com sucesso",
            "id": invoice.id,
            "status": invoice.status,
            **invoice_payload,
            "invoice": invoice_payload,
        }
        
    except Exception as e:
        logger.error(f"Erro ao criar fatura: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar fatura: {str(e)}"
        )


@compat_router.post("/{invoice_id}/payment-link")
@router.post("/invoices/{invoice_id}/payment-link")
async def create_invoice_payment_link(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Gera link de pagamento para a fatura (Stripe se configurado; senão stub PIX/local).
    Ownership: somente o dono da fatura (JWT).
    """
    invoice = (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id, Invoice.user_id == current_user.id)
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Fatura não encontrada")

    if invoice.status == "cancelled":
        raise HTTPException(
            status_code=400, detail="Não é possível gerar link para fatura cancelada"
        )

    client_email = None
    if invoice.client_id:
        client = (
            db.query(Client)
            .filter(Client.id == invoice.client_id, Client.user_id == current_user.id)
            .first()
        )
        if client:
            client_email = client.email

    stripe_url = _try_stripe_invoice_checkout(invoice, client_email)
    if stripe_url:
        invoice.payment_url = stripe_url
        invoice.payment_method = invoice.payment_method or "stripe"
        provider = "stripe"
    else:
        pix = create_pix_charge(
            amount_cents=int(invoice.total_cents or 0),
            description=invoice.description
            or f"Fatura {invoice.invoice_number}",
            client_ref=f"invoice:{invoice.id}",
        )
        stub_url, token = _build_stub_payment_url(invoice.id)
        invoice.payment_url = stub_url
        invoice.payment_reference = pix.get("txid") or token
        invoice.payment_method = invoice.payment_method or "pix"
        provider = pix.get("provider") or "stub"
        pix_payload = pix

    db.commit()
    db.refresh(invoice)

    try:
        log_activity(
            db,
            current_user.id,
            "finance.payment_link",
            f"Link de pagamento gerado ({provider}) para fatura {invoice.invoice_number}",
            entity_type="invoice",
            entity_id=invoice.id,
        )
    except Exception:
        pass

    result = {
        "payment_url": invoice.payment_url,
        "provider": provider,
        "invoice_id": invoice.id,
    }
    if provider != "stripe":
        result["pix"] = pix_payload
    return result


@compat_router.patch("/{invoice_id}/mark-paid")
@router.patch("/invoices/{invoice_id}/pay")
async def mark_invoice_paid(
    invoice_id: int,
    payment_data: dict = {},
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marca fatura como paga"""
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user.id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Fatura não encontrada")
    
    invoice.status = "paid"
    invoice.paid_at = datetime.utcnow()
    
    if payment_data.get("payment_method"):
        invoice.payment_method = payment_data["payment_method"]
    
    db.commit()
    db.refresh(invoice)
    
    invoice_payload = invoice.to_dict()
    return {
        "message": "Fatura marcada como paga",
        "id": invoice.id,
        "status": invoice.status,
        **invoice_payload,
        "invoice": invoice_payload,
    }


@compat_router.patch("/{invoice_id}/cancel")
@router.patch("/invoices/{invoice_id}/cancel")
async def cancel_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancela uma fatura"""
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user.id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Fatura não encontrada")
    
    if invoice.status == "paid":
        raise HTTPException(status_code=400, detail="Não é possível cancelar fatura já paga")
    
    invoice.status = "cancelled"
    db.commit()
    db.refresh(invoice)
    
    invoice_payload = invoice.to_dict()
    return {
        "message": "Fatura cancelada",
        "id": invoice.id,
        "status": invoice.status,
        **invoice_payload,
        "invoice": invoice_payload,
    }


@compat_router.delete("/{invoice_id}")
@router.delete("/invoices/{invoice_id}")
async def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove uma fatura"""
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user.id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Fatura não encontrada")
    
    db.delete(invoice)
    db.commit()
    
    return {"message": "Fatura removida com sucesso"}


@compat_router.get("/dashboard")
@router.get("/dashboard")
async def get_finance_dashboard(
    period_days: int = Query(30, description="Período em dias para análise"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna dashboard financeiro completo"""
    now = datetime.utcnow()
    cutoff = now - timedelta(days=period_days)
    
    # Receitas no período
    period_invoices = db.query(Invoice).filter(
        Invoice.user_id == current_user.id,
        Invoice.created_at >= cutoff
    )
    
    total_billed = db.query(func.sum(Invoice.total_cents)).filter(
        Invoice.user_id == current_user.id,
        Invoice.status == "paid"
    ).scalar() or 0
    
    total_pending = db.query(func.sum(Invoice.total_cents)).filter(
        Invoice.user_id == current_user.id,
        Invoice.status == "pending"
    ).scalar() or 0
    
    total_overdue = db.query(func.sum(Invoice.total_cents)).filter(
        Invoice.user_id == current_user.id,
        Invoice.status == "overdue"
    ).scalar() or 0
    
    # Contagem por status
    paid_count = db.query(Invoice).filter(
        Invoice.user_id == current_user.id,
        Invoice.status == "paid"
    ).count()
    
    pending_count = db.query(Invoice).filter(
        Invoice.user_id == current_user.id,
        Invoice.status == "pending"
    ).count()
    
    overdue_count = db.query(Invoice).filter(
        Invoice.user_id == current_user.id,
        Invoice.status == "overdue"
    ).count()
    
    # Projeção mensal (últimos 6 meses)
    monthly_revenue = []
    for i in range(5, -1, -1):
        month_start = now.replace(day=1) - timedelta(days=i*30)
        month_end = month_start + timedelta(days=30)
        
        month_paid = db.query(func.sum(Invoice.total_cents)).filter(
            Invoice.user_id == current_user.id,
            Invoice.status == "paid",
            Invoice.paid_at >= month_start,
            Invoice.paid_at < month_end
        ).scalar() or 0
        
        monthly_revenue.append({
            "month": month_start.strftime("%Y-%m"),
            "month_name": month_start.strftime("%b/%Y"),
            "revenue": month_paid / 100
        })
    
    # Top devedores
    top_debtors_query = db.query(
        Client.id,
        Client.name,
        func.sum(Invoice.total_cents).label("total_debt")
    ).join(Invoice, Invoice.client_id == Client.id).filter(
        Client.user_id == current_user.id,
        Invoice.status.in_(["pending", "overdue"])
    ).group_by(Client.id).order_by(func.sum(Invoice.total_cents).desc()).limit(5).all()
    
    top_debtors = [
        {
            "client_id": d.id,
            "client_name": d.name,
            "debt": d.total_debt / 100
        }
        for d in top_debtors_query
    ]
    
    return {
        "total_paid": total_billed / 100,
        "total_pending": total_pending / 100,
        "total_overdue": total_overdue / 100,
        "total_outstanding": (total_pending + total_overdue) / 100,
        "summary": {
            "total_billed": total_billed / 100,
            "total_pending": total_pending / 100,
            "total_overdue": total_overdue / 100,
            "total_outstanding": (total_pending + total_overdue) / 100
        },
        "counts": {
            "paid": paid_count,
            "pending": pending_count,
            "overdue": overdue_count,
            "total": paid_count + pending_count + overdue_count
        },
        "monthly_revenue": monthly_revenue,
        "top_debtors": top_debtors,
        "period_days": period_days
    }




@router.get("/aging")
async def get_receivables_aging(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Aging de contas a receber (BI light).
    Agrupa faturas abertas (pending/overdue) em buckets por dias desde due_date
    (fallback: created_at). Valores em BRL.
    """
    now = datetime.utcnow()
    open_statuses = ("pending", "overdue")
    invoices = (
        db.query(Invoice)
        .filter(
            Invoice.user_id == current_user.id,
            Invoice.status.in_(open_statuses),
        )
        .all()
    )

    buckets = {
        "current": 0.0,
        "d31_60": 0.0,
        "d61_90": 0.0,
        "d90_plus": 0.0,
    }
    total_open = 0.0

    for inv in invoices:
        amount = (inv.total_cents or 0) / 100.0
        total_open += amount
        ref = inv.due_date or inv.created_at or now
        # naive vs aware: normalize to naive utc for subtraction
        if getattr(ref, "tzinfo", None) is not None:
            ref = ref.replace(tzinfo=None)
        days = max(0, (now - ref).days)
        if days <= 30:
            buckets["current"] += amount
        elif days <= 60:
            buckets["d31_60"] += amount
        elif days <= 90:
            buckets["d61_90"] += amount
        else:
            buckets["d90_plus"] += amount

    # round for stable JSON
    buckets = {k: round(v, 2) for k, v in buckets.items()}
    return {
        "buckets": buckets,
        "total_open": round(total_open, 2),
        "currency": "BRL",
    }



@router.get("/profitability")
async def get_client_profitability(
    limit: int = Query(25, ge=1, le=100, description="Top N clients by activity"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Estimativa operacional de rentabilidade por cliente (stub).
    Soma faturas paid/pending, valor de horas billable e custas nao reembolsadas.
    Nao e balanco contabil.
    """
    NOTE = "estimativa operacional — nao e balanco contábil"
    uid = current_user.id
    by_client: dict = {}

    def _bucket(cid, name: str):
        key = cid if cid is not None else "_none"
        if key not in by_client:
            by_client[key] = {
                "client_id": cid,
                "client_name": name,
                "invoiced": 0.0,
                "time_value": 0.0,
                "costs_open": 0.0,
            }
        return by_client[key]

    def _client_name(cid):
        if cid is None:
            return "Sem cliente"
        try:
            client = db.query(Client).filter(Client.id == cid, Client.user_id == uid).first()
            return client.name if client else f"Cliente #{cid}"
        except Exception:
            return f"Cliente #{cid}"

    # Invoices: paid + pending (best-effort)
    try:
        inv_statuses = ("paid", "pending")
        invoices = (
            db.query(Invoice)
            .filter(Invoice.user_id == uid, Invoice.status.in_(inv_statuses))
            .all()
        )
        for inv in invoices:
            cid = getattr(inv, "client_id", None)
            row = _bucket(cid, _client_name(cid))
            cents = getattr(inv, "total_cents", None)
            if cents is not None:
                row["invoiced"] += (cents or 0) / 100.0
            else:
                amt = getattr(inv, "total", None) or getattr(inv, "amount", 0) or 0
                row["invoiced"] += float(amt)
    except Exception as exc:
        logger.warning("profitability invoices soft-fail: %s", exc)

    # Time entries billable value (best-effort)
    try:
        entries = db.query(TimeEntry).filter(TimeEntry.user_id == uid).all()
        for entry in entries:
            billable = getattr(entry, "billable", True)
            if billable is False:
                continue
            rate = getattr(entry, "hourly_rate", None)
            minutes = getattr(entry, "minutes", None)
            if rate is None or not minutes:
                continue
            cid = getattr(entry, "client_id", None)
            row = _bucket(cid, _client_name(cid))
            row["time_value"] += (float(minutes) / 60.0) * float(rate)
    except Exception as exc:
        logger.warning("profitability time soft-fail: %s", exc)

    # Unreimbursed cost advances (best-effort)
    try:
        advances = (
            db.query(CostAdvance)
            .filter(CostAdvance.user_id == uid, CostAdvance.status == "advanced")
            .all()
        )
        for adv in advances:
            cid = getattr(adv, "client_id", None)
            row = _bucket(cid, _client_name(cid))
            row["costs_open"] += float(getattr(adv, "amount", 0) or 0)
    except Exception as exc:
        logger.warning("profitability costs soft-fail: %s", exc)

    clients = []
    for row in by_client.values():
        invoiced = round(row["invoiced"], 2)
        time_value = round(row["time_value"], 2)
        costs_open = round(row["costs_open"], 2)
        # Prefer billed cash; fall back to WIP time if nothing invoiced yet
        revenue = invoiced if invoiced > 0 else time_value
        clients.append({
            "client_id": row["client_id"],
            "client_name": row["client_name"],
            "invoiced": invoiced,
            "time_value": time_value,
            "costs_open": costs_open,
            "rough_margin": round(revenue - costs_open, 2),
        })

    clients.sort(
        key=lambda c: (c["invoiced"] + c["time_value"] + c["costs_open"]),
        reverse=True,
    )
    clients = clients[:limit]

    return {
        "clients": clients,
        "note": NOTE,
    }


@router.get("/overdue/list")
async def get_overdue_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista faturas atrasadas para régua de cobrança"""
    now = datetime.utcnow()
    
    overdue = db.query(Invoice).filter(
        Invoice.user_id == current_user.id,
        Invoice.status == "overdue"
    ).order_by(Invoice.due_date.asc()).all()
    
    result = []
    for inv in overdue:
        days_overdue = (now - inv.due_date).days if inv.due_date else 0
        
        # Determinar estágio da régua
        if days_overdue <= 3:
            stage = "friendly"  # Lembrete amigável
            action = "Enviar lembrete"
        elif days_overdue <= 10:
            stage = "second_notice"  # Segundo aviso
            action = "Segundo aviso formal"
        elif days_overdue <= 30:
            stage = "formal"  # Aviso formal
            action = "Aviso formal de inadimplência"
        else:
            stage = "urgent"  # Ação urgente
            action = "Alerta ao advogado para ação judicial"
        
        inv_dict = inv.to_dict()
        inv_dict["days_overdue"] = days_overdue
        inv_dict["collection_stage"] = stage
        inv_dict["suggested_action"] = action
        
        if inv.client_id:
            client = db.query(Client).filter(Client.id == inv.client_id).first()
            inv_dict["client_name"] = client.name if client else "Desconhecido"
            inv_dict["client_phone"] = client.phone if client else None
        
        result.append(inv_dict)
    
    return {
        "overdue_invoices": result,
        "count": len(result),
        "total_overdue": sum([inv["total"] for inv in result])
    }


@compat_router.post("/{invoice_id}/send-reminder")
@router.post("/invoices/{invoice_id}/send-reminder")
async def send_invoice_reminder(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Envia lembrete de cobrança (simulado)"""
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user.id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Fatura não encontrada")
    
    if invoice.status == "paid":
        raise HTTPException(status_code=400, detail="Fatura já está paga")
    
    # Marcar que lembrete foi enviado
    invoice.reminder_sent = True
    invoice.reminder_sent_at = datetime.utcnow()
    db.commit()
    
    client = db.query(Client).filter(Client.id == invoice.client_id).first()
    client_name = client.name if client else "Cliente"
    
    return {
        "message": "Lembrete de cobrança enviado (simulado)",
        "invoice_id": invoice_id,
        "client": client_name,
        "amount": invoice.total_cents / 100,
        "reminder_date": invoice.reminder_sent_at.isoformat()
    }


billing_router = APIRouter(prefix="/billing", tags=["Billing"])


@billing_router.post("/pix-charge")
async def create_billing_pix_charge(
    payload: dict,
    current_user: User = Depends(get_current_user),
):
    """
    Cria cobrança PIX via provider configurável (stub|asaas).
    JWT obrigatório. Sem chaves live necessárias no modo stub.
    """
    try:
        amount_cents = int(payload.get("amount_cents", 0))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="amount_cents inválido")
    if amount_cents <= 0:
        raise HTTPException(status_code=400, detail="amount_cents deve ser > 0")

    description = str(payload.get("description") or "Cobrança PIX")
    client_ref = str(
        payload.get("client_ref") or f"user:{current_user.id}"
    )

    result = create_pix_charge(amount_cents, description, client_ref)
    if result.get("status") == "not_configured":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=result.get("error") or "PIX provider not configured",
        )
    return result



# ---------------------------------------------------------------------------
# NFS-e stub (NAO e integracao com prefeitura)
# ---------------------------------------------------------------------------

@billing_router.post("/nfse", status_code=status.HTTP_201_CREATED)
async def create_nfse_draft(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cria rascunho NFS-e (stub)."""
    client_name = str(payload.get("client_name") or "").strip()
    service_description = str(payload.get("service_description") or "").strip()
    if not client_name or not service_description:
        raise HTTPException(
            status_code=400,
            detail="client_name e service_description sao obrigatorios",
        )
    try:
        amount = float(payload.get("amount", 0))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="amount invalido")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="amount deve ser > 0")

    invoice_id = payload.get("invoice_id")
    if invoice_id is not None:
        try:
            invoice_id = int(invoice_id)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="invoice_id invalido")
        inv = (
            db.query(Invoice)
            .filter(Invoice.id == invoice_id, Invoice.user_id == current_user.id)
            .first()
        )
        if not inv:
            raise HTTPException(status_code=404, detail="Fatura nao encontrada")

    draft = NfseDraft(
        user_id=current_user.id,
        invoice_id=invoice_id,
        client_name=client_name,
        service_description=service_description,
        amount=amount,
        status="draft",
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft.to_dict()


@billing_router.get("/nfse")
async def list_nfse_drafts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista rascunhos NFS-e do usuario (stub)."""
    rows = (
        db.query(NfseDraft)
        .filter(NfseDraft.user_id == current_user.id)
        .order_by(NfseDraft.created_at.desc())
        .all()
    )
    return {"items": [r.to_dict() for r in rows], "count": len(rows)}


@billing_router.post("/nfse/{nfse_id}/issue-stub")
async def issue_nfse_stub(
    nfse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Emite NFS-e ficticia: status=issued_stub + number_stub NFS-e-STUB-XXXX.
    NAO chama API de prefeitura.
    """
    draft = (
        db.query(NfseDraft)
        .filter(NfseDraft.id == nfse_id, NfseDraft.user_id == current_user.id)
        .first()
    )
    if not draft:
        raise HTTPException(status_code=404, detail="NFS-e draft nao encontrado")
    if draft.status == "cancelled":
        raise HTTPException(status_code=400, detail="NFS-e cancelada")
    if draft.status == "issued_stub" and draft.number_stub:
        return draft.to_dict()

    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    draft.status = "issued_stub"
    draft.number_stub = f"NFS-e-STUB-{code}"
    db.commit()
    db.refresh(draft)
    return draft.to_dict()


# ---------------------------------------------------------------------------
# Ethical collection plan (régua ética — stub EOAB) + Cost advances (custas)
# ---------------------------------------------------------------------------

@router.get("/collection-plan")
async def get_collection_plan(
    invoice_id: Optional[int] = Query(None, description="Optional invoice id"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Suggested ethical dunning steps for open invoices.
    Stages: D-3 reminder, D0 due, D+3 gentle, D+7 formal notice.
    Does NOT send messages — planning stub with EOAB disclaimer.
    """
    open_statuses = ("pending", "overdue")
    query = db.query(Invoice).filter(
        Invoice.user_id == current_user.id,
        Invoice.status.in_(open_statuses),
    )
    if invoice_id is not None:
        query = query.filter(Invoice.id == invoice_id)
        invoice = query.first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Fatura não encontrada ou já liquidada")
        plan = build_collection_plan_for_invoice(invoice)
        if invoice.client_id:
            client = db.query(Client).filter(Client.id == invoice.client_id).first()
            if client:
                plan["client_name"] = client.name
        return {
            "plans": [plan],
            "count": 1,
            "disclaimer": EOAB_DISCLAIMER,
            "currency": "BRL",
        }

    invoices = query.order_by(Invoice.due_date.asc()).all()
    plans = build_collection_plans(invoices)
    # enrich names
    client_ids = {p.get("client_id") for p in plans if p.get("client_id")}
    names = {}
    if client_ids:
        for c in db.query(Client).filter(Client.id.in_(client_ids)).all():
            names[c.id] = c.name
    for p in plans:
        cid = p.get("client_id")
        p["client_name"] = names.get(cid) if cid else None

    return {
        "plans": plans,
        "count": len(plans),
        "disclaimer": EOAB_DISCLAIMER,
        "currency": "BRL",
    }


VALID_COST_STATUSES = frozenset({"advanced", "reimbursed", "written_off"})


@router.get("/cost-advances")
async def list_cost_advances(
    status_filter: Optional[str] = Query(None, alias="status"),
    client_id: Optional[int] = Query(None),
    matter_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista adiantamentos de custas do usuário."""
    q = db.query(CostAdvance).filter(CostAdvance.user_id == current_user.id)
    if status_filter:
        q = q.filter(CostAdvance.status == status_filter)
    if client_id is not None:
        q = q.filter(CostAdvance.client_id == client_id)
    if matter_id is not None:
        q = q.filter(CostAdvance.matter_id == matter_id)
    rows = q.order_by(CostAdvance.created_at.desc()).all()
    return {"items": [r.to_dict() for r in rows], "count": len(rows)}


@router.post("/cost-advances", status_code=status.HTTP_201_CREATED)
async def create_cost_advance(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Registra adiantamento de custas."""
    description = (payload.get("description") or "").strip()
    if not description:
        raise HTTPException(status_code=400, detail="description é obrigatório")
    try:
        amount = float(payload.get("amount", 0))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="amount inválido")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="amount deve ser > 0")

    st = (payload.get("status") or "advanced").strip().lower()
    if st not in VALID_COST_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"status inválido; use: {', '.join(sorted(VALID_COST_STATUSES))}",
        )

    row = CostAdvance(
        user_id=current_user.id,
        client_id=payload.get("client_id"),
        matter_id=payload.get("matter_id"),
        description=description[:500],
        amount=amount,
        status=st,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row.to_dict()


@router.get("/cost-advances/{advance_id}")
async def get_cost_advance(
    advance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = (
        db.query(CostAdvance)
        .filter(CostAdvance.id == advance_id, CostAdvance.user_id == current_user.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Adiantamento não encontrado")
    return row.to_dict()


@router.patch("/cost-advances/{advance_id}")
async def update_cost_advance(
    advance_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = (
        db.query(CostAdvance)
        .filter(CostAdvance.id == advance_id, CostAdvance.user_id == current_user.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Adiantamento não encontrado")

    if "description" in payload:
        desc = (payload.get("description") or "").strip()
        if not desc:
            raise HTTPException(status_code=400, detail="description não pode ser vazio")
        row.description = desc[:500]
    if "amount" in payload:
        try:
            amount = float(payload["amount"])
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="amount inválido")
        if amount <= 0:
            raise HTTPException(status_code=400, detail="amount deve ser > 0")
        row.amount = amount
    if "status" in payload:
        st = (payload.get("status") or "").strip().lower()
        if st not in VALID_COST_STATUSES:
            raise HTTPException(status_code=400, detail="status inválido")
        row.status = st
    if "client_id" in payload:
        row.client_id = payload.get("client_id")
    if "matter_id" in payload:
        row.matter_id = payload.get("matter_id")

    db.commit()
    db.refresh(row)
    return row.to_dict()


@router.delete("/cost-advances/{advance_id}", status_code=status.HTTP_200_OK)
async def delete_cost_advance(
    advance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = (
        db.query(CostAdvance)
        .filter(CostAdvance.id == advance_id, CostAdvance.user_id == current_user.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Adiantamento não encontrado")
    db.delete(row)
    db.commit()
    return {"ok": True, "id": advance_id}



@router.get("/tax-calendar")
async def get_tax_calendar(
    month: Optional[str] = Query(
        None,
        description="Competencia YYYY-MM (lembretes metodologicos; nao e API RFB)",
    ),
    current_user: User = Depends(get_current_user),
):
    """
    Monthly tax obligations reminder stub for accountants.

    Methodological checklist only — NOT a real RFB/municipal calendar API.
    No invented tax rates or exact statutory due days.
    """
    _ = current_user  # JWT required; calendar is methodological (not per-user data)
    try:
        return build_tax_calendar(month)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.get("/tax-reform-checklist")
async def get_tax_reform_checklist(
    current_user: User = Depends(get_current_user),
):
    """
    Static Reforma Tributaria / eSocial-DCTFWeb methodological checklist.

    Same content as Contador help on /ajuda. NOT legal advice; no invented
    rates or exact statutory due dates as facts.
    """
    _ = current_user  # JWT required; payload is static methodological help
    return build_tax_reform_checklist()

