"""
Audit Log Model
===============
Modelo de auditoria para compliance e segurança.
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from core.database import Base


class AuditAction(str, enum.Enum):
    """Ações auditáveis"""
    # Auth
    LOGIN = "login"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFY = "email_verify"
    
    # Documents
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_VIEW = "document_view"
    DOCUMENT_DELETE = "document_delete"
    DOCUMENT_SHARE = "document_share"
    
    # AI
    AI_REQUEST = "ai_request"
    AI_GENERATION = "ai_generation"
    
    # Billing
    SUBSCRIPTION_CREATE = "subscription_create"
    SUBSCRIPTION_UPDATE = "subscription_update"
    SUBSCRIPTION_CANCEL = "subscription_cancel"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    
    # Admin
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_SUSPEND = "user_suspend"
    
    # Security
    SECURITY_ALERT = "security_alert"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


class AuditSeverity(str, enum.Enum):
    """Severidade do evento"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLog(Base):
    """Modelo de log de auditoria"""
    __tablename__ = 'audit_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    
    # Action
    action = Column(SQLEnum(AuditAction), nullable=False, index=True)
    severity = Column(SQLEnum(AuditSeverity), default=AuditSeverity.INFO, nullable=False)
    
    # Resource
    resource_type = Column(String(50))  # user, document, subscription, etc
    resource_id = Column(UUID(as_uuid=True))
    
    # Details
    description = Column(Text)
    custom_data = Column(JSONB, default={})
    
    # Request Info
    ip_address = Column(INET)
    user_agent = Column(Text)
    request_id = Column(String(100), index=True)
    
    # Changes (for update actions)
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    tenant = relationship("Tenant")
    user = relationship("User")
    
    def __repr__(self):
        return f"<AuditLog {self.action.value} (tenant={self.tenant_id})>"
    
    def to_dict(self):
        """Converte para dict serializável"""
        return {
            "id": str(self.id),
            "action": self.action.value if isinstance(self.action, AuditAction) else self.action,
            "severity": self.severity.value if isinstance(self.severity, AuditSeverity) else self.severity,
            "resource_type": self.resource_type,
            "resource_id": str(self.resource_id) if self.resource_id else None,
            "description": self.description,
            "ip_address": str(self.ip_address) if self.ip_address else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
