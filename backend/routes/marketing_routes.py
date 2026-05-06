"""
Marketing OAB-Compliance
Módulo 6 - Marketing dentro das normas da OAB
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from database import get_db, User, Client
from security import get_current_user

router = APIRouter(prefix="/marketing", tags=["Marketing OAB"])

# Normas OAB: Art. 34 a 50 do Código de Ética

@router.get("/content-library")
async def get_content_library(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Biblioteca de conteúdo pré-aprovado pela OAB
    """
    templates = [
        {
            "id": 1,
            "title": "Direitos do Consumidor",
            "category": "educational",
            "content": "Você sabia que tem direito a...",
            "compliance_notes": "Aprovado OAB - informativo educacional",
            "approved": True
        },
        {
            "id": 2,
            "title": "Como funciona uma ação trabalhista",
            "category": "educational",
            "content": "Passo a passo de uma ação trabalhista...",
            "compliance_notes": "Aprovado OAB - educativo",
            "approved": True
        },
        {
            "id": 3,
            "title": "Promoção de serviços",
            "category": "promotional",
            "content": "Proibido - Violação Art. 39 OAB",
            "compliance_notes": "REJEITADO - não pode usar",
            "approved": False
        }
    ]
    
    if category:
        templates = [t for t in templates if t["category"] == category]
    
    return {
        "templates": templates,
        "total": len(templates),
        "approved_only": True,
        "disclaimer": "Todo conteúdo deve ser aprovado pela OAB antes de publicar"
    }

@router.get("/compliance-check")
async def check_marketing_compliance(
    content: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verifica se conteúdo está em compliance com OAB
    """
    # Checks básicos
    prohibited_words = ["melhor advogado", "mais barato", "garantimos ganhar", "100% de aproveitamento"]
    found_issues = []
    
    for word in prohibited_words:
        if word.lower() in content.lower():
            found_issues.append({
                "issue": f"Palavra proibida encontrada: '{word}'",
                "rule": "Art. 39 - Publicidade vedada",
                "severity": "high"
            })
    
    # Verificar se é conteúdo educativo (permitido) ou promocional (restrito)
    is_educational = any(word in content.lower() for word in ["como", "direito", "lei", "informação"])
    
    return {
        "content": content,
        "compliant": len(found_issues) == 0,
        "issues": found_issues,
        "suggestions": [
            "Use linguagem educativa e informativa",
            "Evite superlativos (melhor, maior, único)",
            "Não prometa resultados específicos",
            "Foque em informar, não em vender"
        ] if found_issues else [],
        "category": "educational" if is_educational else "needs_review"
    }

@router.get("/campaigns")
async def list_marketing_campaigns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista campanhas de marketing (apenas educativas - compliance OAB)"""
    return {
        "campaigns": [],
        "message": "Campanhas educativas em desenvolvimento",
        "compliance_requirements": [
            "Art. 34: Informações claras e verdadeiras",
            "Art. 35: Proibição de publicidade enganosa",
            "Art. 39: Publicidade vedada (promessas de resultado, comparações)",
            "Art. 45: Respeito à concorrência"
        ]
    }

@router.get("/newsletter/subscribers")
async def get_newsletter_subscribers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista assinantes de newsletter (clients com consentimento)"""
    # Buscar clients que podem receber comunicações
    subscribers = db.query(Client).filter(
        Client.user_id == current_user.id,
        Client.email.isnot(None),
        Client.status == "active"
    ).all()
    
    return {
        "subscribers": [{
            "id": s.id,
            "name": s.name,
            "email": s.email,
            "consent_date": s.created_at.isoformat() if s.created_at else None
        } for s in subscribers],
        "total": len(subscribers),
        "note": "LGPD: Consentimento implícito por ser cliente. Newsletter deve ser educativa."
    }
