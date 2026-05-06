"""
Audit Logger - Sistema de Auditoria para LGPD/Compliance
Registra todas as operações críticas para auditoria
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Configuração do logger de auditoria
audit_logger = logging.getLogger("audit")

class AuditLogger:
    """Logger de auditoria para operações sensíveis (LGPD)"""
    
    @staticmethod
    def log_data_access(
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ):
        """Registra acesso a dados (LGPD)"""
        audit_logger.info(f"[DATA_ACCESS] user={user_id} action={action} resource={resource_type}:{resource_id} ip={ip_address} details={details}")
    
    @staticmethod
    def log_data_export(
        user_id: int,
        data_types: list,
        ip_address: Optional[str] = None
    ):
        """Registra exportação de dados (LGPD)"""
        audit_logger.warning(f"[DATA_EXPORT] user={user_id} types={data_types} ip={ip_address}")
    
    @staticmethod
    def log_data_deletion(
        user_id: int,
        resource_type: str,
        resource_id: int,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """Registra deleção de dados (LGPD)"""
        audit_logger.warning(f"[DATA_DELETION] user={user_id} resource={resource_type}:{resource_id} reason={reason} ip={ip_address}")
    
    @staticmethod
    def log_security_event(
        event_type: str,
        user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        severity: str = "info"
    ):
        """Registra evento de segurança"""
        log_method = getattr(audit_logger, severity, audit_logger.info)
        log_method(f"[SECURITY] type={event_type} user={user_id} ip={ip_address} details={details}")

# Instância global
audit_logger = AuditLogger()
