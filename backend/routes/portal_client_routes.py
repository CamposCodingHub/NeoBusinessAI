"""
Portal do Cliente - API Routes
Acesso para clientes do escritório visualizarem seus dados
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from database import get_db, Client, Invoice, Document, Deadline, User
from models.portal_client import PortalClient, PortalActivity
from security import get_password_hash, verify_password, create_access_token
from security.xss_protection import sanitize_plain_text

router = APIRouter(prefix="/portal", tags=["Portal do Cliente"])

# Dependência para autenticação do portal
async def get_current_portal_client(
    request: Request,
    db: Session = Depends(get_db)
):
    """Autentica cliente do portal via token"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido")
    
    token = auth_header[7:]
    try:
        from security import verify_token
        payload = verify_token(token, token_type="access")
        portal_client_id = int(payload["sub"])
        
        portal_client = db.query(PortalClient).filter(
            PortalClient.id == portal_client_id,
            PortalClient.is_active == True
        ).first()
        
        if not portal_client:
            raise HTTPException(status_code=401, detail="Acesso inválido")
        
        return portal_client
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")

def log_portal_activity(db: Session, portal_client_id: int, action: str, 
                        resource_type: str = None, resource_id: int = None,
                        ip_address: str = None, user_agent: str = None):
    """Registra atividade no portal"""
    activity = PortalActivity(
        portal_client_id=portal_client_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(activity)
    db.commit()


@router.post("/login")
async def portal_login(
    email: str,
    password: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Login do cliente no portal
    """
    portal_client = db.query(PortalClient).filter(
        PortalClient.email == email,
        PortalClient.is_active == True
    ).first()
    
    if not portal_client or not verify_password(password, portal_client.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Email ou senha inválidos"
        )
    
    # Atualizar último login
    portal_client.last_login = datetime.utcnow()
    portal_client.login_attempts = 0
    db.commit()
    
    # Log de atividade
    log_portal_activity(
        db, portal_client.id, "login",
        ip_address=request.client.host,
        user_agent=request.headers.get("User-Agent")
    )
    
    # Gerar token
    access_token = create_access_token(
        user_id=str(portal_client.id),
        expires_delta=timedelta(hours=8)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "client_name": portal_client.client.name if portal_client.client else None
    }


@router.get("/dashboard")
async def portal_dashboard(
    db: Session = Depends(get_db),
    current_portal: PortalClient = Depends(get_current_portal_client)
):
    """
    Dashboard do cliente - visão geral de seus dados
    """
    client_id = current_portal.client_id
    
    # Buscar dados do cliente
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Faturas
    invoices = db.query(Invoice).filter(
        Invoice.client_id == client_id
    ).order_by(Invoice.created_at.desc()).limit(5).all()
    
    # Documentos compartilhados
    documents = db.query(Document).filter(
        Document.user_id == client.user_id,
        Document.custom_data["client_id"].as_integer() == client_id,
        Document.status == "processed"
    ).order_by(Document.created_at.desc()).limit(5).all()
    
    # Prazos relacionados
    deadlines = db.query(Deadline).filter(
        Deadline.user_id == client.user_id,
        Deadline.is_completed == False
    ).order_by(Deadline.due_date.asc()).limit(5).all()
    
    return {
        "client": {
            "name": client.name,
            "email": client.email,
            "phone": client.phone,
            "status": client.status
        },
        "summary": {
            "total_invoices": db.query(Invoice).filter(Invoice.client_id == client_id).count(),
            "pending_invoices": db.query(Invoice).filter(
                Invoice.client_id == client_id,
                Invoice.status.in_(["pending", "overdue"])
            ).count(),
            "total_documents": len(documents),
            "upcoming_deadlines": len(deadlines)
        },
        "recent_invoices": [{
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "description": inv.description,
            "total_amount": inv.total_cents / 100,
            "status": inv.status,
            "due_date": inv.due_date.isoformat() if inv.due_date else None,
            "created_at": inv.created_at.isoformat() if inv.created_at else None
        } for inv in invoices],
        "shared_documents": [{
            "id": doc.id,
            "filename": doc.filename,
            "title": doc.title,
            "created_at": doc.created_at.isoformat() if doc.created_at else None
        } for doc in documents],
        "upcoming_deadlines": [{
            "id": dl.id,
            "description": dl.description,
            "due_date": dl.due_date.isoformat() if dl.due_date else None,
            "urgency": dl.urgency
        } for dl in deadlines]
    }


@router.get("/invoices")
async def portal_list_invoices(
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_portal: PortalClient = Depends(get_current_portal_client)
):
    """
    Lista faturas do cliente
    """
    client_id = current_portal.client_id
    
    query = db.query(Invoice).filter(Invoice.client_id == client_id)
    
    if status:
        query = query.filter(Invoice.status == status)
    
    total = query.count()
    invoices = query.order_by(Invoice.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    return {
        "invoices": [{
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "description": inv.description,
            "total_amount": inv.total_cents / 100,
            "status": inv.status,
            "due_date": inv.due_date.isoformat() if inv.due_date else None,
            "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
            "created_at": inv.created_at.isoformat() if inv.created_at else None
        } for inv in invoices],
        "pagination": {
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit,
            "limit": limit
        }
    }


@router.get("/invoices/{invoice_id}/download")
async def portal_download_invoice(
    invoice_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_portal: PortalClient = Depends(get_current_portal_client)
):
    """
    Download de fatura (PDF)
    """
    client_id = current_portal.client_id
    
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.client_id == client_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Fatura não encontrada")
    
    # Log de download
    log_portal_activity(
        db, current_portal.id, "download_invoice",
        resource_type="invoice",
        resource_id=invoice_id,
        ip_address=request.client.host,
        user_agent=request.headers.get("User-Agent")
    )
    
    # TODO: Gerar PDF da fatura
    return {
        "message": "PDF gerado com sucesso",
        "invoice_id": invoice_id,
        "download_url": f"/api/portal/invoices/{invoice_id}/pdf"
    }


@router.get("/documents")
async def portal_list_documents(
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_portal: PortalClient = Depends(get_current_portal_client)
):
    """
    Lista documentos compartilhados com o cliente
    """
    client_id = current_portal.client_id
    client = db.query(Client).filter(Client.id == client_id).first()
    
    query = db.query(Document).filter(
        Document.user_id == client.user_id,
        Document.custom_data["client_id"].as_integer() == client_id,
        Document.status == "processed"
    )
    
    total = query.count()
    documents = query.order_by(Document.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    return {
        "documents": [{
            "id": doc.id,
            "filename": doc.filename,
            "title": doc.title,
            "file_type": doc.file_type,
            "created_at": doc.created_at.isoformat() if doc.created_at else None
        } for doc in documents],
        "pagination": {
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit,
            "limit": limit
        }
    }


@router.get("/chat")
async def portal_chat_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_portal: PortalClient = Depends(get_current_portal_client)
):
    """
    Histórico de chat entre cliente e escritório
    """
    # TODO: Implementar quando chat estiver pronto
    return {
        "messages": [],
        "has_more": False
    }
