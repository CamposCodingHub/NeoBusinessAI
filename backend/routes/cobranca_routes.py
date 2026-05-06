"""
Régua de Cobrança Completa
Módulo 4 - Automação de cobranças
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from database import get_db, Invoice, Client, User
from security import get_current_user

router = APIRouter(prefix="/cobranca", tags=["Régua de Cobrança"])

@router.get("/dashboard")
async def cobranca_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dashboard de cobranças"""
    today = datetime.utcnow()
    
    # Contadores
    total_pending = db.query(Invoice).filter(
        Invoice.user_id == current_user.id,
        Invoice.status == "pending"
    ).count()
    
    total_overdue = db.query(Invoice).filter(
        Invoice.user_id == current_user.id,
        Invoice.status == "overdue"
    ).count()
    
    # Cobranças desta semana
    this_week = today + timedelta(days=7)
    due_this_week = db.query(Invoice).filter(
        Invoice.user_id == current_user.id,
        Invoice.status == "pending",
        Invoice.due_date <= this_week
    ).all()
    
    return {
        "summary": {
            "total_pending": total_pending,
            "total_overdue": total_overdue,
            "due_this_week": len(due_this_week),
            "total_amount_pending": sum(inv.total_cents for inv in due_this_week) / 100 if due_this_week else 0
        },
        "due_this_week": [{
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "client_name": db.query(Client).filter(Client.id == inv.client_id).first().name if inv.client_id else "N/A",
            "amount": inv.total_cents / 100,
            "due_date": inv.due_date.isoformat() if inv.due_date else None
        } for inv in due_this_week],
        "automation_status": {
            "enabled": False,
            "last_run": None,
            "next_run": None,
            "message": "Automação de cobrança em desenvolvimento - integrar com WhatsApp e Email"
        }
    }

@router.get("/automation/rules")
async def get_automation_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Regras de automação da régua de cobrança"""
    return {
        "rules": [
            {
                "id": 1,
                "name": "Lembrete 5 dias antes",
                "trigger": "5_days_before_due",
                "action": "send_reminder_whatsapp",
                "template": "lembrete_vencimento",
                "enabled": False
            },
            {
                "id": 2,
                "name": "Aviso no vencimento",
                "trigger": "on_due_date",
                "action": "send_warning_whatsapp",
                "template": "aviso_vencimento",
                "enabled": False
            },
            {
                "id": 3,
                "name": "Cobrança 3 dias após",
                "trigger": "3_days_after_due",
                "action": "send_collection_whatsapp",
                "template": "cobranca_amigavel",
                "enabled": False
            },
            {
                "id": 4,
                "name": "Cobrança 7 dias após",
                "trigger": "7_days_after_due",
                "action": "send_collection_email_and_whatsapp",
                "template": "cobranca_formal",
                "enabled": False
            },
            {
                "id": 5,
                "name": "Aviso jurídico 15 dias",
                "trigger": "15_days_after_due",
                "action": "send_legal_notice",
                "template": "aviso_juridico",
                "enabled": False
            }
        ]
    }

@router.post("/manual-reminder/{invoice_id}")
async def send_manual_reminder(
    invoice_id: int,
    channel: str = "whatsapp",  # whatsapp, email
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Envia lembrete manual de cobrança"""
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user.id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Fatura não encontrada")
    
    # Placeholder - integrar com WhatsApp/Email
    return {
        "success": True,
        "invoice_id": invoice_id,
        "channel": channel,
        "sent_at": datetime.utcnow().isoformat(),
        "message": f"Lembrete enviado via {channel} (integração em desenvolvimento)"
    }

@router.get("/history")
async def cobranca_history(
    client_id: Optional[int] = None,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Histórico de ações de cobrança"""
    return {
        "actions": [],
        "filters": {"client_id": client_id, "days": days},
        "message": "Histórico de cobrança em desenvolvimento"
    }
