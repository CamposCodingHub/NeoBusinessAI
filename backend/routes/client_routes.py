"""
Módulo de Clientes - JurisFlow AI
Gestão completa de clientes do escritório
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from database import get_db, Client, User, Invoice, Document
from security import get_current_user, rate_limit
from security.xss_protection import sanitize_plain_text, sanitize_dict
from utils.validators import validate_cpf, validate_cnpj, format_cpf, format_cnpj

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/clients", tags=["Clientes"])


@router.get("/")
@rate_limit(requests_per_minute=60)
async def list_clients(
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista todos os clientes do usuário (paginado)"""
    query = db.query(Client).filter(Client.user_id == current_user.id)
    
    if status:
        query = query.filter(Client.status == status)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Client.name.ilike(search_filter)) |
            (Client.email.ilike(search_filter)) |
            (Client.cpf_cnpj.ilike(search_filter))
        )
    
    # Total count for pagination
    total = query.count()
    
    # Apply pagination
    clients = query.order_by(Client.name.asc()).offset((page - 1) * limit).limit(limit).all()
    
    return {
        "clients": [c.to_dict() for c in clients],
        "pagination": {
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit,
            "limit": limit
        }
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=20)
async def create_client(
    client_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cria um novo cliente"""
    try:
        # Sanitizar inputs contra XSS
        client = Client(
            user_id=current_user.id,
            name=sanitize_plain_text(client_data.get("name")),
            email=sanitize_plain_text(client_data.get("email")),
            city=sanitize_plain_text(client_data.get("city")),
            state=sanitize_plain_text(client_data.get("state")),
            notes=sanitize_plain_text(client_data.get("notes")),
            status=sanitize_plain_text(client_data.get("status", "active")),
            payment_day=client_data.get("payment_day", 10)
        )
        
        # Criptografar dados sensíveis
        client.set_sensitive_data(
            phone=client_data.get("phone"),
            cpf_cnpj=client_data.get("cpf_cnpj"),
            address=client_data.get("address"),
            zip_code=client_data.get("zip_code")
        )
        
        db.add(client)
        db.commit()
        db.refresh(client)
        
        logger.info(f"Cliente criado: {client.id} - {client.name}")
        
        return {
            "message": "Cliente criado com sucesso",
            "client": client.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Erro ao criar cliente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar cliente: {str(e)}"
        )


@router.get("/{client_id}")
@rate_limit(requests_per_minute=60)
async def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna detalhes de um cliente com histórico"""
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Buscar documentos relacionados
    documents = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.custom_data["client_id"].as_integer() == client_id,
    ).all()
    
    # Buscar faturas
    invoices = db.query(Invoice).filter(
        Invoice.client_id == client_id,
        Invoice.user_id == current_user.id
    ).order_by(Invoice.created_at.desc()).all()
    
    result = client.to_dict()
    result["documents"] = [{"id": d.id, "filename": d.filename, "status": d.status} for d in documents]
    result["invoices"] = [inv.to_dict() for inv in invoices]
    result["total_billed"] = sum([inv.total_cents for inv in invoices if inv.status == "paid"]) / 100
    result["outstanding_amount"] = sum([inv.total_cents for inv in invoices if inv.status in ["pending", "overdue"]]) / 100
    
    return result


@router.put("/{client_id}")
@rate_limit(requests_per_minute=30)
async def update_client(
    client_id: int,
    update_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualiza dados do cliente"""
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Update fields (campos não sensíveis) com sanitização XSS
    for field in ["name", "email", "city", "state", "notes", "status", "payment_day"]:
        if field in update_data:
            value = update_data[field]
            # Sanitizar campos de texto
            if field in ["name", "email", "city", "state", "status"]:
                value = sanitize_plain_text(value)
            setattr(client, field, value)
    
    # Criptografar campos sensíveis se fornecidos
    sensitive_data = {}
    if "phone" in update_data:
        sensitive_data["phone"] = update_data["phone"]
    if "cpf_cnpj" in update_data:
        sensitive_data["cpf_cnpj"] = update_data["cpf_cnpj"]
    if "address" in update_data:
        sensitive_data["address"] = update_data["address"]
    if "zip_code" in update_data:
        sensitive_data["zip_code"] = update_data["zip_code"]
    
    if sensitive_data:
        client.set_sensitive_data(**sensitive_data)
    
    db.commit()
    db.refresh(client)
    
    return {
        "message": "Cliente atualizado com sucesso",
        "client": client.to_dict()
    }


@router.delete("/{client_id}")
@rate_limit(requests_per_minute=10)
async def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove um cliente"""
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    db.delete(client)
    db.commit()
    
    return {"message": "Cliente removido com sucesso"}


@router.get("/{client_id}/timeline")
async def get_client_timeline(
    client_id: int,
    limit: int = Query(50, description="Número máximo de eventos"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna timeline de atividades do cliente"""
    # Verifica se cliente existe e pertence ao usuário
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    events = []
    
    # Criação do cliente
    events.append({
        "type": "client_created",
        "date": client.created_at.isoformat(),
        "title": "Cliente cadastrado",
        "description": f"Cliente {client.name} foi cadastrado no sistema"
    })
    
    # Documentos
    documents = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.custom_data["client_id"].as_integer() == client_id,
    ).order_by(Document.created_at.desc()).limit(limit).all()
    
    for doc in documents:
        events.append({
            "type": "document_uploaded",
            "date": doc.created_at.isoformat(),
            "title": "Documento adicionado",
            "description": f"Documento '{doc.filename}' foi enviado"
        })
    
    # Faturas
    invoices = db.query(Invoice).filter(
        Invoice.client_id == client_id,
        Invoice.user_id == current_user.id
    ).order_by(Invoice.created_at.desc()).limit(limit).all()
    
    for inv in invoices:
        events.append({
            "type": "invoice_created" if inv.status == "pending" else "invoice_paid",
            "date": inv.created_at.isoformat(),
            "title": "Fatura gerada" if inv.status == "pending" else "Pagamento recebido",
            "description": f"R$ {inv.total_cents / 100:.2f} - {inv.description}",
            "amount": inv.total_cents / 100,
            "status": inv.status
        })
    
    # Ordenar por data (mais recente primeiro)
    events.sort(key=lambda x: x["date"], reverse=True)
    
    return {
        "client_id": client_id,
        "client_name": client.name,
        "events": events[:limit],
        "total_events": len(events)
    }
