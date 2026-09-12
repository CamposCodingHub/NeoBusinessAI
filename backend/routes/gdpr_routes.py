"""
Rotas LGPD (Lei Geral de Proteção de Dados)
Exportação e deleção de dados pessoais do escritório autenticado.
"""

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import (
    ActivityLog,
    Client,
    Deadline,
    Document,
    Invoice,
    User,
    get_db,
)
from security import get_current_user
from security.audit_logger import audit_logger
from services.compliance_service import ComplianceService

router = APIRouter(prefix="/gdpr", tags=["LGPD Compliance"])


def _resolve_user(db: Session, current_user) -> User:
    """Carrega User ORM a partir do TokenData JWT."""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user


def _build_export(db: Session, current_user) -> Dict[str, Any]:
    user = _resolve_user(db, current_user)
    package = ComplianceService.export_user_data(db, user.id)
    try:
        audit_logger.log_data_export(
            user_id=int(user.id),
            data_types=[
                "profile",
                "clients_count",
                "documents",
                "invoices_summary",
                "chat_messages_count",
                "leads_count",
                "matters_count",
            ],
        )
    except Exception:
        pass
    return package


@router.get("/export", response_model=Dict[str, Any])
async def export_my_data_get(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Exporta pacote JSON LGPD/GDPR do usuário autenticado (GET).
    Metadados de documentos (sem texto completo); contagens e resumos best-effort.
    """
    return _build_export(db, current_user)


@router.post("/export", response_model=Dict[str, Any])
async def export_my_data_post(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Exporta pacote JSON LGPD/GDPR do usuário autenticado (POST).
    Mesmo payload de GET /gdpr/export.
    """
    return _build_export(db, current_user)


@router.get("/export/my-data", response_model=Dict[str, Any])
async def export_my_data_legacy(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Alias legado — mesmo pacote de GET /gdpr/export."""
    return _build_export(db, current_user)


@router.delete("/delete/my-data", response_model=Dict[str, Any])
async def delete_my_data(
    confirm_delete: bool = False,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Deleta/anonimiza dados pessoais do usuário (Direito ao Esquecimento LGPD).
    REQUER confirmação explícita.
    """
    if not confirm_delete:
        raise HTTPException(
            status_code=400,
            detail="Deleção requer confirm_delete=true. Esta ação é IRREVERSÍVEL.",
        )

    user = _resolve_user(db, current_user)
    user_id = user.id
    user_email = user.email

    try:
        audit_logger.log_data_deletion(
            user_id=int(user_id),
            resource_type="user_data",
            resource_id=int(user_id),
            reason=f"requested_by={user_email}",
        )

        clients_count = db.query(Client).filter(Client.user_id == user_id).count()
        documents_count = (
            db.query(Document).filter(Document.user_id == user_id).count()
        )
        invoices_count = (
            db.query(Invoice).filter(Invoice.user_id == user_id).count()
        )
        deadlines_count = (
            db.query(Deadline).filter(Deadline.user_id == user_id).count()
        )

        db.query(ActivityLog).filter(ActivityLog.user_id == user_id).delete(
            synchronize_session=False
        )
        db.query(Invoice).filter(Invoice.user_id == user_id).delete(
            synchronize_session=False
        )
        db.query(Deadline).filter(Deadline.user_id == user_id).delete(
            synchronize_session=False
        )

        documents = db.query(Document).filter(Document.user_id == user_id).all()
        for doc in documents:
            doc.status = "deleted"
            doc.content = None
            doc.text_content = None
            doc.custom_data = {
                "deleted": True,
                "deleted_at": datetime.utcnow().isoformat(),
            }

        clients = db.query(Client).filter(Client.user_id == user_id).all()
        for client_row in clients:
            client_row.name = f"[ANONIMIZADO-{client_row.id}]"
            client_row.email = None
            client_row.phone = None
            client_row.cpf_cnpj = None
            client_row.address = None
            client_row.notes = None
            client_row.status = "anonymized"

        user.email = f"[DELETED-{user_id}]@deleted.jurisflow"
        user.name = f"[USUÁRIO DELETADO - {user_id}]"
        user.password_hash = "[DELETED]"
        user.is_active = False
        user.phone = None

        db.commit()

        return {
            "message": "Dados pessoais deletados com sucesso",
            "status": "anonymized",
            "deleted_records": {
                "clients": clients_count,
                "documents": documents_count,
                "invoices": invoices_count,
                "deadlines": deadlines_count,
            },
            "note": (
                "Clientes anonimizados. Documentos marcados como deletados. "
                "Dados do usuário anonimizados."
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        audit_logger.log_security_event(
            event_type="data_deletion_failed",
            user_id=int(user_id),
            details={"error": str(e)},
            severity="error",
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao deletar dados: {str(e)}",
        )


@router.get("/audit-log/access", response_model=List[Dict[str, Any]])
async def get_data_access_log(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Retorna log de acesso aos dados pessoais (Transparência LGPD)."""
    logs = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.user_id == current_user.id,
            ActivityLog.action.in_(
                [
                    "client_viewed",
                    "document_viewed",
                    "invoice_viewed",
                    "data_export",
                    "data_deletion_request",
                    "login",
                    "logout",
                ]
            ),
        )
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": log.id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
