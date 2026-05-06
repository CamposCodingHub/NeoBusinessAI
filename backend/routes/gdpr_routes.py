"""
Rotas LGPD (Lei Geral de Proteção de Dados)
Exportação e deleção de dados pessoais
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime
import json

from database import get_db, User, Client, Document, Invoice, Deadline, ActivityLog
from security import get_current_user, require_role, Role
from security.audit_logger import audit_logger

router = APIRouter(prefix="/gdpr", tags=["LGPD Compliance"])


@router.get("/export/my-data", response_model=Dict[str, Any])
async def export_my_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exporta todos os dados pessoais do usuário (Portabilidade LGPD)
    Retorna JSON completo com todos os dados
    """
    user_id = current_user.id
    
    # Coletar dados do usuário
    user_data = {
        "user_info": {
            "id": user_id,
            "email": current_user.email,
            "name": current_user.name,
            "role": current_user.role,
            "plan_tier": current_user.plan_tier,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None,
        },
        "export_metadata": {
            "exported_at": datetime.utcnow().isoformat(),
            "format_version": "1.0",
            "legal_basis": "LGPD Art. 18 (Portabilidade)"
        }
    }
    
    # Clientes
    clients = db.query(Client).filter(Client.user_id == user_id).all()
    user_data["clients"] = [{
        "id": c.id,
        "name": c.name,
        "email": c.email,
        "phone": c.phone,  # Descriptografado pelo to_dict()
        "cpf_cnpj": c.cpf_cnpj,  # Descriptografado
        "address": c.address,  # Descriptografado
        "city": c.city,
        "state": c.state,
        "zip_code": c.zip_code,  # Descriptografado
        "status": c.status,
        "payment_day": c.payment_day,
        "notes": c.notes,
        "created_at": c.created_at.isoformat() if c.created_at else None
    } for c in clients]
    
    # Documentos
    documents = db.query(Document).filter(Document.user_id == user_id).all()
    user_data["documents"] = [{
        "id": d.id,
        "filename": d.filename,
        "title": d.title,
        "file_type": d.file_type,
        "file_size": d.file_size,
        "status": d.status,
        "content_preview": d.content[:500] if d.content else None,  # Limitar conteúdo
        "metadata": d.metadata,
        "created_at": d.created_at.isoformat() if d.created_at else None
    } for d in documents]
    
    # Faturas
    invoices = db.query(Invoice).filter(Invoice.user_id == user_id).all()
    user_data["invoices"] = [{
        "id": inv.id,
        "invoice_number": inv.invoice_number,
        "client_id": inv.client_id,
        "description": inv.description,
        "total_amount": inv.total_cents / 100,
        "status": inv.status,
        "due_date": inv.due_date.isoformat() if inv.due_date else None,
        "created_at": inv.created_at.isoformat() if inv.created_at else None
    } for inv in invoices]
    
    # Prazos
    deadlines = db.query(Deadline).filter(Deadline.user_id == user_id).all()
    user_data["deadlines"] = [{
        "id": dl.id,
        "description": dl.description,
        "due_date": dl.due_date.isoformat() if dl.due_date else None,
        "urgency": dl.urgency,
        "is_completed": dl.is_completed,
        "notes": dl.notes,
        "created_at": dl.created_at.isoformat() if dl.created_at else None
    } for dl in deadlines]
    
    # Logs de atividade (últimos 90 dias)
    recent_logs = db.query(ActivityLog).filter(
        ActivityLog.user_id == user_id,
        ActivityLog.created_at >= datetime.utcnow().replace(day=1)  # Último mês
    ).order_by(ActivityLog.created_at.desc()).limit(100).all()
    
    user_data["activity_logs"] = [{
        "id": log.id,
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "details": log.details,
        "created_at": log.created_at.isoformat() if log.created_at else None
    } for log in recent_logs]
    
    # Log da exportação (auditoria LGPD)
    audit_logger.log(
        user_id=user_id,
        action="data_export",
        resource_type="user_data",
        resource_id=user_id,
        details={"format": "JSON", "records_count": len(clients) + len(documents) + len(invoices)}
    )
    
    return user_data


@router.delete("/delete/my-data", response_model=Dict[str, str])
async def delete_my_data(
    confirm_delete: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deleta todos os dados pessoais do usuário (Direito ao Esquecimento LGPD)
    REQUER CONFIRMAÇÃO explícita
    """
    if not confirm_delete:
        raise HTTPException(
            status_code=400,
            detail="Deleção requer confirm_delete=true. Esta ação é IRREVERSÍVEL."
        )
    
    user_id = current_user.id
    user_email = current_user.email
    
    try:
        # Log da solicitação de deleção
        audit_logger.log(
            user_id=user_id,
            action="data_deletion_request",
            resource_type="user_data",
            resource_id=user_id,
            details={"requested_by": user_email}
        )
        
        # Contar registros antes de deletar (para auditoria)
        clients_count = db.query(Client).filter(Client.user_id == user_id).count()
        documents_count = db.query(Document).filter(Document.user_id == user_id).count()
        invoices_count = db.query(Invoice).filter(Invoice.user_id == user_id).count()
        deadlines_count = db.query(Deadline).filter(Deadline.user_id == user_id).count()
        
        # Deletar em ordem (respeitando FKs)
        # 1. Activity Logs
        db.query(ActivityLog).filter(ActivityLog.user_id == user_id).delete(synchronize_session=False)
        
        # 2. Invoices
        db.query(Invoice).filter(Invoice.user_id == user_id).delete(synchronize_session=False)
        
        # 3. Deadlines
        db.query(Deadline).filter(Deadline.user_id == user_id).delete(synchronize_session=False)
        
        # 4. Documents (manter arquivos físicos por segurança, apenas marcar como deletados)
        documents = db.query(Document).filter(Document.user_id == user_id).all()
        for doc in documents:
            doc.status = "deleted"
            doc.content = None  # Remover conteúdo indexado
            doc.metadata = {"deleted": True, "deleted_at": datetime.utcnow().isoformat()}
        
        # 5. Clients - Anonimizar em vez de deletar (preservar integridade referencial)
        clients = db.query(Client).filter(Client.user_id == user_id).all()
        for client in clients:
            client.name = f"[ANONIMIZADO-{client.id}]"
            client.email = None
            client.phone = None
            client.cpf_cnpj = None
            client.address = None
            client.notes = None
            client.status = "anonymized"
        
        # 6. Anonimizar usuário (não deletar para preservar logs de auditoria)
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.email = f"[DELETED-{user_id}]@deleted.jurisflow"
            user.name = f"[USUÁRIO DELETADO - {user_id}]"
            user.password_hash = "[DELETED]"
            user.is_active = False
            user.phone = None
        
        db.commit()
        
        # Log da deleção concluída
        audit_logger.log(
            user_id=user_id,
            action="data_deletion_completed",
            resource_type="user_data",
            resource_id=user_id,
            details={
                "clients_anonymized": clients_count,
                "documents_marked_deleted": documents_count,
                "invoices_deleted": invoices_count,
                "deadlines_deleted": deadlines_count
            }
        )
        
        return {
            "message": "Dados pessoais deletados com sucesso",
            "status": "anonymized",
            "deleted_records": {
                "clients": clients_count,
                "documents": documents_count,
                "invoices": invoices_count,
                "deadlines": deadlines_count
            },
            "note": "Cliente e faturas foram removidos. Documentos marcados como deletados. Dados do usuário anonimizados."
        }
        
    except Exception as e:
        db.rollback()
        audit_logger.log(
            user_id=user_id,
            action="data_deletion_failed",
            resource_type="user_data",
            resource_id=user_id,
            details={"error": str(e)}
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao deletar dados: {str(e)}"
        )


@router.get("/audit-log/access", response_model=List[Dict[str, Any]])
async def get_data_access_log(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna log de acesso aos dados pessoais (Transparência LGPD)
    """
    logs = db.query(ActivityLog).filter(
        ActivityLog.user_id == current_user.id,
        ActivityLog.action.in_([
            "client_viewed", "document_viewed", "invoice_viewed",
            "data_export", "data_deletion_request", "login", "logout"
        ])
    ).order_by(ActivityLog.created_at.desc()).limit(limit).all()
    
    return [{
        "id": log.id,
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "created_at": log.created_at.isoformat() if log.created_at else None
    } for log in logs]
