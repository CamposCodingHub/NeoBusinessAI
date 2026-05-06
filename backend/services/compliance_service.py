"""
Compliance Service
===================
Serviço de LGPD e compliance de dados.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import json

from models.user import User
from models.document import Document
from models.audit_log import AuditLog, AuditAction, AuditSeverity


class ConsentType(str):
    """Tipos de consentimento"""
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    DATA_PROCESSING = "data_processing"
    EMAIL_COMMUNICATIONS = "email_communications"


class ComplianceService:
    """Serviço de compliance LGPD"""
    
    @staticmethod
    def record_consent(
        db: Session,
        user_id: str,
        consent_type: str,
        granted: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Registra consentimento do usuário.
        
        Args:
            db: Sessão do banco
            user_id: ID do usuário
            consent_type: Tipo de consentimento
            granted: Se consentimento foi concedido
            ip_address: IP do request
            user_agent: User-Agent
        """
        # TODO: Criar modelo Consent
        # Por enquanto, log em audit
        AuditLog.create(
            user_id=user_id,
            action=AuditAction.EMAIL_VERIFY if consent_type == ConsentType.EMAIL_COMMUNICATIONS else AuditAction.USER_UPDATE,
            severity=AuditSeverity.INFO,
            description=f"Consent {'granted' if granted else 'revoked'}: {consent_type}",
            metadata={
                "consent_type": consent_type,
                "granted": granted,
                "ip_address": ip_address
            }
        )
    
    @staticmethod
    def export_user_data(db: Session, user_id: str) -> Dict[str, Any]:
        """
        Exporta todos os dados do usuário (LGPD - Direito de Portabilidade).
        
        Args:
            db: Sessão do banco
            user_id: ID do usuário
            
        Returns:
            Dict com todos os dados do usuário
        """
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        # Coletar dados do usuário
        user_data = {
            "profile": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "phone": user.phone,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            },
            "documents": [],
            "audit_logs": [],
            "subscriptions": []
        }
        
        # Coletar documentos
        documents = db.query(Document).filter(Document.user_id == user_id).all()
        for doc in documents:
            user_data["documents"].append({
                "id": str(doc.id),
                "filename": doc.filename,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "deleted_at": doc.deleted_at.isoformat() if doc.deleted_at else None
            })
        
        # Coletar logs de auditoria (últimos 90 dias)
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        audit_logs = db.query(AuditLog).filter(
            AuditLog.user_id == user_id,
            AuditLog.created_at >= cutoff_date
        ).all()
        
        for log in audit_logs:
            user_data["audit_logs"].append({
                "action": log.action.value if hasattr(log.action, 'value') else log.action,
                "description": log.description,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "ip_address": str(log.ip_address) if log.ip_address else None
            })
        
        # Coletar assinaturas
        from models.subscription import Subscription
        subscriptions = db.query(Subscription).filter(Subscription.user_id == user_id).all()
        for sub in subscriptions:
            user_data["subscriptions"].append({
                "id": str(sub.id),
                "plan_tier": sub.plan_tier,
                "status": sub.status.value if hasattr(sub.status, 'value') else sub.status,
                "created_at": sub.created_at.isoformat() if sub.created_at else None
            })
        
        # Log de exportação
        AuditLog.create(
            user_id=user_id,
            action=AuditAction.USER_UPDATE,
            severity=AuditSeverity.INFO,
            description="User data exported (GDPR/LGPD)",
            metadata={"export_type": "full"}
        )
        
        return user_data
    
    @staticmethod
    def delete_user_data(db: Session, user_id: str, hard_delete: bool = False) -> bool:
        """
        Deleta dados do usuário (LGPD - Direito ao Esquecimento).
        
        Args:
            db: Sessão do banco
            user_id: ID do usuário
            hard_delete: Se True, deleta permanentemente. Se False, apenas marca como deletado.
            
        Returns:
            True se deletado com sucesso
        """
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        if hard_delete:
            # Deletar permanentemente (cuidado!)
            # Deletar documentos do storage
            from services.storage_service import storage_service
            documents = db.query(Document).filter(Document.user_id == user_id).all()
            
            for doc in documents:
                if doc.storage_key:
                    storage_service.delete_file(doc.storage_key)
            
            # Deletar registros do banco
            db.query(Document).filter(Document.user_id == user_id).delete()
            db.query(AuditLog).filter(AuditLog.user_id == user_id).delete()
            db.delete(user)
            
        else:
            # Soft delete (recomendado)
            user.email = f"deleted_{user.id}@deleted.local"
            user.full_name = "Deleted User"
            user.phone = None
            user.password_hash = "DELETED"
            user.is_active = False
            user.deleted_at = datetime.utcnow()
            
            # Anonimizar documentos
            documents = db.query(Document).filter(Document.user_id == user_id).all()
            for doc in documents:
                doc.filename = "DELETED"
                doc.original_filename = "DELETED"
                doc.ocr_text = None
                doc.extracted_data = {}
                doc.deleted_at = datetime.utcnow()
        
        db.commit()
        
        # Log de deleção
        AuditLog.create(
            user_id=user_id,
            action=AuditAction.USER_DELETE,
            severity=AuditSeverity.CRITICAL,
            description=f"User data {'hard' if hard_delete else 'soft'} deleted (GDPR/LGPD)",
            metadata={"hard_delete": hard_delete}
        )
        
        return True
    
    @staticmethod
    def anonymize_document(db: Session, document_id: str) -> bool:
        """
        Anonimiza documento mantendo metadados mínimos.
        
        Args:
            db: Sessão do banco
            document_id: ID do documento
            
        Returns:
            True se anonimizado com sucesso
        """
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Documento não encontrado")
        
        # Anonimizar conteúdo
        document.filename = "ANONYMIZED"
        document.original_filename = "ANONYMIZED"
        document.ocr_text = None
        document.extracted_data = {}
        document.entities = []
        document.key_points = []
        document.summary = None
        document.analysis = {}
        
        # Manter apenas metadados essenciais
        document.metadata = {
            "anonymized_at": datetime.utcnow().isoformat(),
            "anonymized": True
        }
        
        db.commit()
        
        return True
    
    @staticmethod
    def get_retention_policy() -> Dict[str, int]:
        """
        Retorna política de retenção de dados (em dias).
        
        Returns:
            Dict com tempos de retenção por tipo de dado
        """
        return {
            "user_profile": 2555,  # 7 anos após conta deletada
            "documents": 1825,  # 5 anos
            "audit_logs": 2555,  # 7 anos
            "payment_data": 2555,  # 7 anos (fiscal)
            "consent_records": 2555,  # 7 anos
            "analytics_data": 730,  # 2 anos
        }
    
    @staticmethod
    def check_data_retention(db: Session) -> list:
        """
        Verifica dados que devem ser retidos ou deletados.
        
        Args:
            db: Sessão do banco
            
        Returns:
            Lista de dados expirados
        """
        retention_policy = ComplianceService.get_retention_policy()
        expired_data = []
        
        # TODO: Implementar verificação de retenção
        # Por enquanto, retorna vazio
        
        return expired_data


# Singleton instance
compliance_service = ComplianceService()
