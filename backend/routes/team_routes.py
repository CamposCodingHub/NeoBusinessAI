"""
Gestão de Equipe e Tarefas
Módulo 2 - Implementação Simplificada
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db, User
from security import get_current_user, require_role, Role

router = APIRouter(prefix="/team", tags=["Gestão de Equipe"])

# Modelo simplificado de membro da equipe (usando User existente)

@router.get("/members")
async def list_team_members(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista membros da equipe do escritório"""
    # Retorna usuários do mesmo "tenant" (simplificado)
    members = db.query(User).filter(
        User.id != current_user.id,
        User.is_active == True
    ).all()
    
    return {
        "members": [{
            "id": m.id,
            "name": m.name,
            "email": m.email,
            "role": m.role,
            "created_at": m.created_at.isoformat() if m.created_at else None
        } for m in members],
        "count": len(members)
    }

@router.get("/tasks")
async def list_team_tasks(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista tarefas da equipe"""
    # Placeholder - integrar com sistema de tarefas quando implementado
    return {
        "tasks": [],
        "message": "Módulo de tarefas em desenvolvimento",
        "status": "placeholder"
    }

@router.get("/productivity")
async def team_productivity(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN))
):
    """Dashboard de produtividade da equipe (apenas admin)"""
    return {
        "period_days": days,
        "metrics": {
            "total_clients": 0,
            "documents_processed": 0,
            "invoices_generated": 0,
            "deadlines_met": 0
        },
        "members": [],
        "message": "Módulo de produtividade em desenvolvimento"
    }
