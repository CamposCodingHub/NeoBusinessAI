"""
Audit Logging System - LexScan IA
Registra todas as ações de usuários para compliance e segurança
"""

import json
import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import os

# Configuração
LOG_LEVEL = os.environ.get('AUDIT_LOG_LEVEL', 'INFO')
LOG_RETENTION_DAYS = int(os.environ.get('AUDIT_LOG_RETENTION_DAYS', '365'))


class AuditEventType(Enum):
    """Tipos de eventos de auditoria"""
    # Autenticação
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    
    # Documentos
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_VIEW = "document_view"
    DOCUMENT_DELETE = "document_delete"
    DOCUMENT_DOWNLOAD = "document_download"
    
    # Chat/IA
    CHAT_MESSAGE = "chat_message"
    AI_REQUEST = "ai_request"
    AI_RESPONSE = "ai_response"
    
    # Email
    EMAIL_CONNECT = "email_connect"
    EMAIL_DISCONNECT = "email_disconnect"
    EMAIL_SEND = "email_send"
    EMAIL_RECEIVE = "email_receive"
    
    # Admin/Config
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    SETTINGS_CHANGE = "settings_change"
    
    # Segurança
    SECURITY_VIOLATION = "security_violation"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    
    # Sistema
    SYSTEM_ERROR = "system_error"
    BACKUP_CREATED = "backup_created"
    DATA_EXPORT = "data_export"


class AuditSeverity(Enum):
    """Níveis de severidade"""
    LOW = "low"           # Info normal
    MEDIUM = "medium"     # Atenção necessária
    HIGH = "high"         # Revisar urgente
    CRITICAL = "critical" # Ação imediata


class AuditLogger:
    """
    Sistema de logging de auditoria
    
    Features:
    - Log imutável com hash chain
    - Exportação para SIEM
    - Retenção configurável
    - Busca e análise
    """
    
    def __init__(self):
        self._memory_logs: List[Dict] = []  # Buffer em memória
        self._last_hash: Optional[str] = None  # Para hash chain
        
    def log(
        self,
        event_type: AuditEventType,
        user_id: Optional[str],
        user_email: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.LOW,
        success: bool = True
    ) -> str:
        """
        Registra um evento de auditoria
        
        Args:
            event_type: Tipo do evento
            user_id: ID do usuário
            user_email: Email do usuário
            action: Ação realizada
            resource_type: Tipo de recurso (document, user, etc)
            resource_id: ID do recurso
            details: Detalhes adicionais
            ip_address: IP do cliente
            user_agent: User agent
            severity: Nível de severidade
            success: Se a ação teve sucesso
            
        Returns:
            log_id: ID único do log
        """
        # Gerar ID único
        log_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Criar entrada de log
        log_entry = {
            'log_id': log_id,
            'timestamp': timestamp,
            'event_type': event_type.value,
            'severity': severity.value,
            'user_id': self._hash_sensitive(user_id) if user_id else None,  # Pseudonimizado
            'user_email': self._mask_email(user_email) if user_email else None,  # Masked
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'details': self._sanitize_details(details),
            'ip_address': self._anonymize_ip(ip_address) if ip_address else None,  # Anonimizado
            'user_agent': user_agent[:100] if user_agent else None,
            'success': success,
            'session_id': None,  # Pode ser adicionado depois
        }
        
        # Adicionar hash chain para imutabilidade
        log_entry['previous_hash'] = self._last_hash
        log_entry['hash'] = self._calculate_hash(log_entry)
        self._last_hash = log_entry['hash']
        
        # Salvar
        self._save_log(log_entry)
        
        # Log críticos também vão para stderr
        if severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL]:
            self._alert_critical(log_entry)
        
        return log_id
    
    def _calculate_hash(self, log_entry: Dict) -> str:
        """Calcula hash SHA-256 da entrada de log"""
        # Remove hash atual para calcular
        entry_copy = {k: v for k, v in log_entry.items() if k != 'hash'}
        entry_str = json.dumps(entry_copy, sort_keys=True, default=str)
        return hashlib.sha256(entry_str.encode()).hexdigest()
    
    def _hash_sensitive(self, value: str) -> str:
        """Pseudonimiza dados sensíveis"""
        if not value:
            return None
        return hashlib.sha256(value.encode()).hexdigest()[:16]
    
    def _mask_email(self, email: str) -> str:
        """Mascara email: user@example.com -> u***@example.com"""
        if not email or '@' not in email:
            return email
        
        local, domain = email.split('@')
        if len(local) <= 2:
            masked_local = '*' * len(local)
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        
        return f"{masked_local}@{domain}"
    
    def _anonymize_ip(self, ip: str) -> str:
        """Anonimiza IP: 192.168.1.1 -> 192.168.x.x"""
        if not ip:
            return None
        
        parts = ip.split('.')
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.x.x"
        return ip
    
    def _sanitize_details(self, details: Dict) -> Dict:
        """Remove dados sensíveis dos detalhes"""
        sensitive_keys = ['password', 'token', 'secret', 'credit_card', 'ssn', 'cpf']
        
        sanitized = {}
        for key, value in details.items():
            if any(s in key.lower() for s in sensitive_keys):
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_details(value)
            elif isinstance(value, str) and len(value) > 1000:
                sanitized[key] = value[:1000] + '...[TRUNCATED]'
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _save_log(self, log_entry: Dict):
        """Salva log (implementação pode ser PostgreSQL, Elasticsearch, etc)"""
        # Por enquário, salva em memória + arquivo
        self._memory_logs.append(log_entry)
        
        # Também salva em arquivo JSONL
        log_file = f"logs/audit_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
        os.makedirs('logs', exist_ok=True)
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry, default=str) + '\n')
    
    def _alert_critical(self, log_entry: Dict):
        """Alerta para eventos críticos"""
        import sys
        print(
            f"\n🚨 CRITICAL AUDIT EVENT: {log_entry['event_type']} | "
            f"{log_entry['action']} | {log_entry['timestamp']}\n",
            file=sys.stderr
        )
    
    def query_logs(
        self,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[AuditSeverity] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Consulta logs de auditoria
        
        Args:
            event_type: Filtrar por tipo de evento
            user_id: Filtrar por usuário
            resource_type: Filtrar por tipo de recurso
            start_time: Data inicial
            end_time: Data final
            severity: Nível de severidade
            limit: Máximo de resultados
            
        Returns:
            Lista de logs
        """
        results = []
        
        for log in reversed(self._memory_logs):  # Mais recentes primeiro
            if len(results) >= limit:
                break
            
            # Aplicar filtros
            if event_type and log['event_type'] != event_type.value:
                continue
            if user_id and log['user_id'] != self._hash_sensitive(user_id):
                continue
            if resource_type and log['resource_type'] != resource_type:
                continue
            if severity and log['severity'] != severity.value:
                continue
            
            results.append(log)
        
        return results
    
    def get_user_activity(
        self,
        user_id: str,
        start_time: Optional[datetime] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Obtém resumo de atividade de um usuário
        
        Returns:
            Dict com estatísticas de atividade
        """
        logs = self.query_logs(user_id=user_id, start_time=start_time, limit=limit)
        
        if not logs:
            return {
                'user_id': user_id,
                'activity_count': 0,
                'last_activity': None,
                'events_by_type': {},
                'recent_actions': []
            }
        
        events_by_type = {}
        for log in logs:
            et = log['event_type']
            events_by_type[et] = events_by_type.get(et, 0) + 1
        
        return {
            'user_id': user_id,
            'activity_count': len(logs),
            'last_activity': logs[0]['timestamp'],
            'events_by_type': events_by_type,
            'recent_actions': [
                {
                    'time': log['timestamp'],
                    'action': log['action'],
                    'resource': log['resource_type'],
                    'success': log['success']
                }
                for log in logs[:10]
            ]
        }
    
    def detect_anomalies(self, user_id: Optional[str] = None) -> List[Dict]:
        """
        Detecta atividades anômalas
        
        Returns:
            Lista de anomalias detectadas
        """
        anomalies = []
        
        # Busca logs recentes
        logs = self.query_logs(
            start_time=datetime.utcnow() - __import__('datetime').timedelta(hours=24),
            limit=1000
        )
        
        # Detectar: Múltiplas falhas de login
        failed_logins = [l for l in logs if l['event_type'] == AuditEventType.LOGIN_FAILED.value]
        if len(failed_logins) > 5:
            anomalies.append({
                'type': 'multiple_failed_logins',
                'severity': 'high',
                'count': len(failed_logins),
                'description': f'{len(failed_logins)} tentativas de login falhas nas últimas 24h'
            })
        
        # Detectar: Acesso fora do horário comercial
        suspicious_access = []
        for log in logs:
            hour = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')).hour
            if hour < 6 or hour > 22:  # Fora do horário comercial
                if log['event_type'] in [AuditEventType.DOCUMENT_VIEW.value, AuditEventType.DOCUMENT_DOWNLOAD.value]:
                    suspicious_access.append(log)
        
        if len(suspicious_access) > 3:
            anomalies.append({
                'type': 'after_hours_access',
                'severity': 'medium',
                'count': len(suspicious_access),
                'description': f'{len(suspicious_access)} acessos fora do horário comercial'
            })
        
        # Detectar: Volume anormal de downloads
        downloads = [l for l in logs if l['event_type'] == AuditEventType.DOCUMENT_DOWNLOAD.value]
        if len(downloads) > 20:  # Mais de 20 downloads em 24h
            anomalies.append({
                'type': 'mass_download',
                'severity': 'high',
                'count': len(downloads),
                'description': f'{len(downloads)} downloads detectados - possível data exfiltration'
            })
        
        return anomalies
    
    def export_to_json(self, filepath: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None):
        """Exporta logs para JSON (para SIEM)"""
        logs = self.query_logs(start_time=start_time, end_time=end_time, limit=10000)
        
        with open(filepath, 'w') as f:
            json.dump({
                'export_time': datetime.utcnow().isoformat(),
                'log_count': len(logs),
                'logs': logs
            }, f, indent=2, default=str)
        
        return len(logs)


# Instância global
audit_logger = AuditLogger()


# =============================================================================
# DECORATOR PARA AUTO-LOGGING
# =============================================================================

def audit_log(
    event_type: AuditEventType,
    action: str,
    resource_type: str,
    get_resource_id=None,
    get_user_id=None,
    severity: AuditSeverity = AuditSeverity.LOW
):
    """
    Decorator para logar automaticamente chamadas de endpoint
    
    Usage:
        @app.get("/api/documents/{doc_id}")
        @audit_log(
            event_type=AuditEventType.DOCUMENT_VIEW,
            action="view_document",
            resource_type="document",
            get_resource_id=lambda **kwargs: kwargs.get('doc_id'),
            severity=AuditSeverity.LOW
        )
        async def get_document(doc_id: int, user_email: str = None):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Capturar info da request se disponível
            user_email = kwargs.get('user_email')
            doc_id = get_resource_id(**kwargs) if get_resource_id else None
            
            try:
                result = await func(*args, **kwargs)
                success = True
                
                # Tentar extrair status code
                if hasattr(result, 'status_code'):
                    success = result.status_code < 400
                
            except Exception as e:
                success = False
                raise
            finally:
                # Logar a ação
                audit_logger.log(
                    event_type=event_type,
                    user_id=None,
                    user_email=user_email,
                    action=action,
                    resource_type=resource_type,
                    resource_id=str(doc_id) if doc_id else None,
                    details={'args': str(args), 'kwargs': {k: v for k, v in kwargs.items() if k != 'password'}},
                    severity=severity if success else AuditSeverity.MEDIUM,
                    success=success
                )
            
            return result
        
        return wrapper
    return decorator


# =============================================================================
# TESTES
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("AUDIT LOGGER - TESTE")
    print("=" * 60)
    
    # Teste 1: Log simples
    print("\n1. Teste de logging básico:")
    log_id = audit_logger.log(
        event_type=AuditEventType.DOCUMENT_UPLOAD,
        user_id="user_123",
        user_email="john.doe@example.com",
        action="upload_document",
        resource_type="document",
        resource_id="doc_456",
        details={"filename": "contract.pdf", "size": 1024},
        ip_address="192.168.1.100",
        severity=AuditSeverity.LOW,
        success=True
    )
    print(f"   ✅ Log criado: {log_id}")
    
    # Teste 2: Email masking
    print("\n2. Teste de mascaramento de email:")
    print(f"   Original: john.doe@example.com")
    print(f"   Masked: {audit_logger._mask_email('john.doe@example.com')}")
    
    # Teste 3: IP anonymization
    print("\n3. Teste de anonimização de IP:")
    print(f"   Original: 192.168.1.100")
    print(f"   Anonymized: {audit_logger._anonymize_ip('192.168.1.100')}")
    
    # Teste 4: Query
    print("\n4. Teste de consulta:")
    logs = audit_logger.query_logs(event_type=AuditEventType.DOCUMENT_UPLOAD, limit=5)
    print(f"   Encontrados {len(logs)} logs de upload")
    
    print("\n" + "=" * 60)
    print("TESTES COMPLETADOS!")
    print("=" * 60)
