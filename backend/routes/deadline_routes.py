"""
Módulo de Prazos Processuais - JurisFlow AI
Endpoints para gestão completa de prazos com alertas
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import uuid

from database import get_db, Deadline, User, Document
from security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/deadlines", tags=["Prazos"])


# ============================================
# ENDPOINTS CRUD
# ============================================

@router.get("/")
async def list_deadlines(
    status: Optional[str] = Query(None, description="Filter by status: pending, completed, all"),
    urgency: Optional[str] = Query(None, description="Filter by urgency: high, medium, low"),
    days_ahead: Optional[int] = Query(None, description="Filter deadlines within N days"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lista todos os prazos do usuário com filtros opcionais (paginado)
    """
    query = db.query(Deadline).filter(Deadline.user_id == current_user.id)
    
    # Filter by completion status
    if status == "pending":
        query = query.filter(Deadline.is_completed == False)
    elif status == "completed":
        query = query.filter(Deadline.is_completed == True)
    
    # Filter by urgency
    if urgency:
        query = query.filter(Deadline.urgency == urgency)
    
    # Filter by days ahead
    if days_ahead:
        cutoff = datetime.utcnow() + timedelta(days=days_ahead)
        query = query.filter(
            Deadline.due_date <= cutoff,
            Deadline.is_completed == False
        )
    
    # Total count for pagination
    total = query.count()
    
    # Apply pagination
    deadlines = query.order_by(Deadline.due_date.asc()).offset((page - 1) * limit).limit(limit).all()
    
    return {
        "deadlines": [dl.to_dict() for dl in deadlines],
        "pagination": {
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit,
            "limit": limit
        },
        "filters_applied": {
            "status": status,
            "urgency": urgency,
            "days_ahead": days_ahead
        }
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_deadline(
    deadline_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cria um novo prazo processual
    
    Expected JSON:
    {
        "description": "Responder contestação",
        "days": 15,
        "due_date": "2025-06-20T10:00:00",
        "urgency": "high",
        "context": "Processo 12345 - Cliente ABC",
        "document_id": 123  # opcional
    }
    """
    try:
        document_id = deadline_data.get("document_id")

        # Bancos locais antigos ainda podem exigir document_id.
        # Criamos um artefato tecnico minimo para manter o prazo manual funcional.
        if document_id is None:
            placeholder_document = Document(
                user_id=current_user.id,
                filename=f"prazo-manual-{uuid.uuid4().hex[:8]}.txt",
                original_filename="prazo-manual.txt",
                file_path=None,
                file_size=0,
                file_type=".txt",
                title=deadline_data.get("description") or "Prazo manual",
                status="uploaded",
                content={"source": "manual_deadline"},
                custom_data={"generated_by": "deadline_routes"},
            )
            db.add(placeholder_document)
            db.flush()
            document_id = placeholder_document.id

        # Parse due_date if provided
        due_date = None
        if "due_date" in deadline_data and deadline_data["due_date"]:
            if isinstance(deadline_data["due_date"], str):
                due_date = datetime.fromisoformat(deadline_data["due_date"].replace("Z", "+00:00"))
            else:
                due_date = deadline_data["due_date"]
        
        # If only days provided, calculate due_date
        elif "days" in deadline_data and deadline_data["days"]:
            due_date = datetime.utcnow() + timedelta(days=int(deadline_data["days"]))
        
        deadline = Deadline(
            user_id=current_user.id,
            document_id=document_id,
            description=deadline_data.get("description", ""),
            days=deadline_data.get("days"),
            due_date=due_date,
            urgency=deadline_data.get("urgency", "medium"),
            context=deadline_data.get("context", ""),
            is_completed=False
        )
        
        db.add(deadline)
        db.commit()
        db.refresh(deadline)
        
        logger.info(f"Prazo criado: ID {deadline.id} para usuário {current_user.id}")
        
        return {
            "message": "Prazo criado com sucesso",
            "deadline": deadline.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Erro ao criar prazo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar prazo: {str(e)}"
        )


@router.get("/{deadline_id}")
async def get_deadline(
    deadline_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna detalhes de um prazo específico"""
    deadline = db.query(Deadline).filter(
        Deadline.id == deadline_id,
        Deadline.user_id == current_user.id
    ).first()
    
    if not deadline:
        raise HTTPException(status_code=404, detail="Prazo não encontrado")
    
    return deadline.to_dict()


@router.put("/{deadline_id}")
async def update_deadline(
    deadline_id: int,
    update_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualiza um prazo existente"""
    deadline = db.query(Deadline).filter(
        Deadline.id == deadline_id,
        Deadline.user_id == current_user.id
    ).first()
    
    if not deadline:
        raise HTTPException(status_code=404, detail="Prazo não encontrado")
    
    # Update fields
    if "description" in update_data:
        deadline.description = update_data["description"]
    if "due_date" in update_data:
        if isinstance(update_data["due_date"], str):
            deadline.due_date = datetime.fromisoformat(update_data["due_date"].replace("Z", "+00:00"))
        else:
            deadline.due_date = update_data["due_date"]
    if "days" in update_data:
        deadline.days = update_data["days"]
    if "urgency" in update_data:
        deadline.urgency = update_data["urgency"]
    if "context" in update_data:
        deadline.context = update_data["context"]
    if "document_id" in update_data:
        deadline.document_id = update_data["document_id"]
    
    db.commit()
    db.refresh(deadline)
    
    return {
        "message": "Prazo atualizado com sucesso",
        "deadline": deadline.to_dict()
    }


@router.patch("/{deadline_id}/complete")
async def complete_deadline(
    deadline_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marca um prazo como concluído"""
    deadline = db.query(Deadline).filter(
        Deadline.id == deadline_id,
        Deadline.user_id == current_user.id
    ).first()
    
    if not deadline:
        raise HTTPException(status_code=404, detail="Prazo não encontrado")
    
    deadline.is_completed = True
    deadline.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(deadline)
    
    return {
        "message": "Prazo marcado como concluído",
        "deadline": deadline.to_dict()
    }


@router.delete("/{deadline_id}")
async def delete_deadline(
    deadline_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove um prazo"""
    deadline = db.query(Deadline).filter(
        Deadline.id == deadline_id,
        Deadline.user_id == current_user.id
    ).first()
    
    if not deadline:
        raise HTTPException(status_code=404, detail="Prazo não encontrado")
    
    db.delete(deadline)
    db.commit()
    
    return {"message": "Prazo removido com sucesso"}


# ============================================
# ENDPOINTS ESPECIALIZADOS
# ============================================

@router.get("/stats/overview")
async def get_deadline_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna estatísticas de prazos para o dashboard
    """
    now = datetime.utcnow()
    
    # Total counts
    total_query = db.query(Deadline).filter(Deadline.user_id == current_user.id)
    total = total_query.count()
    pending = total_query.filter(Deadline.is_completed == False).count()
    completed = total_query.filter(Deadline.is_completed == True).count()
    
    # Urgency breakdown (pending only)
    high_urgency = total_query.filter(
        Deadline.is_completed == False,
        Deadline.urgency == "high"
    ).count()
    medium_urgency = total_query.filter(
        Deadline.is_completed == False,
        Deadline.urgency == "medium"
    ).count()
    low_urgency = total_query.filter(
        Deadline.is_completed == False,
        Deadline.urgency == "low"
    ).count()
    
    # Time-based alerts
    today_end = now.replace(hour=23, minute=59, second=59)
    tomorrow_end = today_end + timedelta(days=1)
    week_end = now + timedelta(days=7)
    
    due_today = total_query.filter(
        Deadline.is_completed == False,
        Deadline.due_date <= today_end
    ).count()
    
    due_tomorrow = total_query.filter(
        Deadline.is_completed == False,
        Deadline.due_date > today_end,
        Deadline.due_date <= tomorrow_end
    ).count()
    
    due_this_week = total_query.filter(
        Deadline.is_completed == False,
        Deadline.due_date > tomorrow_end,
        Deadline.due_date <= week_end
    ).count()
    
    overdue = total_query.filter(
        Deadline.is_completed == False,
        Deadline.due_date < now
    ).count()
    
    return {
        "overview": {
            "total": total,
            "pending": pending,
            "completed": completed,
            "completion_rate": round((completed / total * 100), 1) if total > 0 else 0
        },
        "urgency": {
            "high": high_urgency,
            "medium": medium_urgency,
            "low": low_urgency
        },
        "alerts": {
            "overdue": overdue,
            "due_today": due_today,
            "due_tomorrow": due_tomorrow,
            "due_this_week": due_this_week
        }
    }


@router.get("/alerts/upcoming")
async def get_upcoming_alerts(
    days: int = Query(30, description="Days ahead to check"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna alertas de prazos próximos com níveis de urgência
    """
    now = datetime.utcnow()
    cutoff = now + timedelta(days=days)
    
    deadlines = db.query(Deadline).filter(
        Deadline.user_id == current_user.id,
        Deadline.is_completed == False,
        Deadline.due_date <= cutoff
    ).order_by(Deadline.due_date.asc()).all()
    
    alerts = []
    for dl in deadlines:
        days_until = (dl.due_date - now).days if dl.due_date else 999
        hours_until = (dl.due_date - now).total_seconds() / 3600 if dl.due_date else 9999
        
        # Determine alert level
        if days_until < 0:
            alert_level = "overdue"
            alert_message = f"ATRASADO: {abs(days_until)} dias"
        elif days_until == 0:
            alert_level = "critical"
            alert_message = "VENCE HOJE"
        elif days_until == 1:
            alert_level = "critical"
            alert_message = "VENCE AMANHÃ"
        elif days_until <= 3:
            alert_level = "high"
            alert_message = f"{days_until} dias restantes"
        elif days_until <= 7:
            alert_level = "medium"
            alert_message = f"{days_until} dias restantes"
        else:
            alert_level = "low"
            alert_message = f"{days_until} dias restantes"
        
        alerts.append({
            "deadline_id": dl.id,
            "description": dl.description,
            "due_date": dl.due_date.isoformat() if dl.due_date else None,
            "days_until": days_until,
            "hours_until": round(hours_until, 1),
            "urgency": dl.urgency,
            "alert_level": alert_level,
            "alert_message": alert_message,
            "context": dl.context
        })
    
    return {
        "alerts": alerts,
        "total_alerts": len(alerts),
        "critical_count": len([a for a in alerts if a["alert_level"] == "critical"]),
        "high_count": len([a for a in alerts if a["alert_level"] == "high"]),
        "overdue_count": len([a for a in alerts if a["alert_level"] == "overdue"])
    }


@router.post("/batch/calculate-due-date")
async def calculate_due_date(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calcula data de vencimento considerando dias úteis e feriados
    
    Expected:
    {
        "start_date": "2025-05-05",
        "days": 15,
        "consider_business_days": true
    }
    """
    from datetime import datetime
    
    start_date_str = data.get("start_date")
    days = data.get("days", 15)
    consider_business_days = data.get("consider_business_days", True)
    
    if start_date_str:
        start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
    else:
        start_date = datetime.utcnow()
    
    # Feriados brasileiros comuns (simplificado - pode ser expandido)
    holidays = [
        "01-01",  # Confraternização Universal
        "04-21",  # Tiradentes
        "05-01",  # Dia do Trabalho
        "09-07",  # Independência
        "10-12",  # Nossa Senhora Aparecida
        "11-02",  # Finados
        "11-15",  # Proclamação da República
        "12-25",  # Natal
    ]
    
    if consider_business_days:
        # Calculate business days (excluding weekends and holidays)
        current_date = start_date
        business_days_count = 0
        
        while business_days_count < days:
            current_date += timedelta(days=1)
            
            # Skip weekends
            if current_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                continue
            
            # Skip holidays (check MM-DD format)
            date_str = current_date.strftime("%m-%d")
            if date_str in holidays:
                continue
            
            business_days_count += 1
        
        due_date = current_date
    else:
        due_date = start_date + timedelta(days=days)
    
    return {
        "start_date": start_date.isoformat(),
        "days_requested": days,
        "consider_business_days": consider_business_days,
        "due_date": due_date.isoformat(),
        "is_business_day": due_date.weekday() < 5 and due_date.strftime("%m-%d") not in holidays
    }
