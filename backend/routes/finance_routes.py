"""
Módulo Financeiro - JurisFlow AI
Gestão de faturas, receitas e controle de inadimplência
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import random
import string

from database import get_db, Invoice, Client, User
from security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/finance", tags=["Financeiro"])


def generate_invoice_number():
    """Gera número de fatura único: FAT-2025-XXXXX"""
    year = datetime.utcnow().year
    random_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"FAT-{year}-{random_code}"


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


@router.post("/invoices", status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cria uma nova fatura"""
    try:
        amount_cents = int(invoice_data.get("amount", 0) * 100)
        discount_cents = int(invoice_data.get("discount", 0) * 100)
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
        
        return {
            "message": "Fatura criada com sucesso",
            "invoice": invoice.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Erro ao criar fatura: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar fatura: {str(e)}"
        )


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
    
    return {
        "message": "Fatura marcada como paga",
        "invoice": invoice.to_dict()
    }


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
    
    return {
        "message": "Fatura cancelada",
        "invoice": invoice.to_dict()
    }


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
