"""
SIEM Integration - LexScan IA
Integração com sistemas de monitoramento de segurança
"""

import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List
import os


class SIEMIntegration:
    """
    Integração com SIEM (Security Information and Event Management)
    
    Suporta:
    - Splunk
    - ELK Stack (Elasticsearch)
    - Datadog
    - Custom webhook
    """
    
    def __init__(self):
        self.provider = os.environ.get('SIEM_PROVIDER', 'none')
        self.endpoint = os.environ.get('SIEM_ENDPOINT')
        self.api_key = os.environ.get('SIEM_API_KEY')
        self.index = os.environ.get('SIEM_INDEX', 'lexscan-security')
        
    def send_event(
        self,
        event_type: str,
        severity: str,
        source: str,
        message: str,
        details: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Envia evento para o SIEM
        
        Args:
            event_type: Tipo do evento
            severity: critical, high, medium, low
            source: Origem do evento (ex: "api", "waf", "audit")
            message: Mensagem descritiva
            details: Detalhes adicionais
            timestamp: Quando ocorreu
            
        Returns:
            True se enviou com sucesso
        """
        if not self.endpoint:
            return False
        
        if not timestamp:
            timestamp = datetime.utcnow()
        
        event = {
            'timestamp': timestamp.isoformat(),
            'event_type': event_type,
            'severity': severity,
            'source': source,
            'message': message,
            'details': details,
            'service': 'lexscan-ai',
            'environment': os.environ.get('ENVIRONMENT', 'production')
        }
        
        try:
            if self.provider == 'splunk':
                return self._send_to_splunk(event)
            elif self.provider == 'elk':
                return self._send_to_elk(event)
            elif self.provider == 'datadog':
                return self._send_to_datadog(event)
            elif self.provider == 'webhook':
                return self._send_to_webhook(event)
            else:
                # Log local
                print(f"[SIEM] {json.dumps(event)}")
                return True
                
        except Exception as e:
            print(f"[SIEM ERROR] Failed to send event: {e}")
            return False
    
    def _send_to_splunk(self, event: Dict) -> bool:
        """Envia para Splunk HTTP Event Collector"""
        headers = {
            'Authorization': f'Splunk {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'event': event,
            'sourcetype': '_json',
            'index': self.index
        }
        
        response = requests.post(
            self.endpoint,
            headers=headers,
            json=payload,
            timeout=5
        )
        
        return response.status_code == 200
    
    def _send_to_elk(self, event: Dict) -> bool:
        """Envia para Elasticsearch"""
        headers = {
            'Content-Type': 'application/json'
        }
        
        if self.api_key:
            headers['Authorization'] = f'ApiKey {self.api_key}'
        
        index_name = f"{self.index}-{datetime.utcnow().strftime('%Y.%m.%d')}"
        url = f"{self.endpoint}/{index_name}/_doc"
        
        response = requests.post(
            url,
            headers=headers,
            json=event,
            timeout=5
        )
        
        return response.status_code in [200, 201]
    
    def _send_to_datadog(self, event: Dict) -> bool:
        """Envia para Datadog Logs"""
        headers = {
            'Content-Type': 'application/json',
            'DD-API-KEY': self.api_key
        }
        
        # Datadog usa formato diferente
        dd_event = {
            'ddsource': event['source'],
            'ddtags': f"env:{event['environment']},service:{event['service']}",
            'hostname': 'lexscan-api',
            'message': json.dumps(event),
            'service': event['service'],
            'status': event['severity']
        }
        
        response = requests.post(
            'https://http-intake.logs.datadoghq.com/v1/input',
            headers=headers,
            json=dd_event,
            timeout=5
        )
        
        return response.status_code == 200
    
    def _send_to_webhook(self, event: Dict) -> bool:
        """Envia para webhook customizado"""
        headers = {
            'Content-Type': 'application/json'
        }
        
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        
        response = requests.post(
            self.endpoint,
            headers=headers,
            json=event,
            timeout=5
        )
        
        return response.status_code == 200
    
    def send_security_alert(
        self,
        alert_type: str,
        description: str,
        affected_resources: List[str],
        recommended_action: str,
        severity: str = "high"
    ) -> bool:
        """
        Envia alerta de segurança
        
        Args:
            alert_type: Tipo do alerta (ex: "data_breach", "intrusion_attempt")
            description: Descrição do problema
            affected_resources: Lista de recursos afetados
            recommended_action: Ação recomendada
            severity: critical, high, medium, low
        """
        return self.send_event(
            event_type=f"security_alert_{alert_type}",
            severity=severity,
            source="security_monitoring",
            message=description,
            details={
                'alert_type': alert_type,
                'affected_resources': affected_resources,
                'recommended_action': recommended_action,
                'requires_immediate_action': severity in ['critical', 'high']
            }
        )
    
    def send_audit_event(
        self,
        user_id: str,
        action: str,
        resource: str,
        result: str,
        details: Dict[str, Any]
    ) -> bool:
        """
        Envia evento de auditoria
        """
        return self.send_event(
            event_type="audit_event",
            severity="low",
            source="audit_logger",
            message=f"User {user_id} performed {action} on {resource}",
            details={
                'user_id': user_id,
                'action': action,
                'resource': resource,
                'result': result,
                'details': details
            }
        )


# Instância global
siem = SIEMIntegration()


# =============================================================================
# INTEGRAÇÃO COM ALERTAS CLOUDFLARE
# =============================================================================

class CloudflareLogIntegration:
    """
    Processa logs do Cloudflare para o SIEM
    """
    
    @staticmethod
    def process_logflare_log(log_entry: Dict) -> Optional[Dict]:
        """
        Processa entrada de log do Cloudflare (via Logflare)
        
        Args:
            log_entry: Entrada de log do Cloudflare
            
        Returns:
            Evento formatado para SIEM ou None
        """
        # Extrair informações relevantes
        event = {
            'timestamp': log_entry.get('EdgeStartTimestamp'),
            'client_ip': log_entry.get('ClientIP'),
            'client_request_host': log_entry.get('ClientRequestHost'),
            'client_request_uri': log_entry.get('ClientRequestURI'),
            'edge_response_status': log_entry.get('EdgeResponseStatus'),
            'edge_start_timestamp': log_entry.get('EdgeStartTimestamp'),
            'ray_id': log_entry.get('RayID'),
            'security_level': log_entry.get('SecurityLevel'),
            'waf_action': log_entry.get('WAFAction'),
            'waf_rule_id': log_entry.get('WAFRuleID'),
            'waf_flags': log_entry.get('WAFflags'),
            'user_agent': log_entry.get('RequestHeaders', {}).get('user-agent'),
            'country': log_entry.get('EdgeResponseStatus'),  # CF-IPCountry
        }
        
        # Detectar eventos de segurança
        if event.get('waf_action') in ['block', 'challenge']:
            return {
                'event_type': 'waf_block',
                'severity': 'medium',
                'source': 'cloudflare_waf',
                'message': f"WAF {event['waf_action']} for request to {event['client_request_uri']}",
                'details': event
            }
        
        # Detectar erros
        if event.get('edge_response_status', 200) >= 500:
            return {
                'event_type': 'server_error',
                'severity': 'high',
                'source': 'cloudflare_edge',
                'message': f"Server error {event['edge_response_status']} for {event['client_request_uri']}",
                'details': event
            }
        
        return None


# =============================================================================
# ALERTAS AUTOMÁTICOS
# =============================================================================

class SecurityAlerts:
    """
    Sistema de alertas de segurança automatizados
    """
    
    def __init__(self):
        self.siem = SIEMIntegration()
    
    def alert_brute_force(self, ip_address: str, attempts: int, user_email: Optional[str]):
        """Alerta de tentativa de brute force"""
        self.siem.send_security_alert(
            alert_type="brute_force_attack",
            description=f"Detectadas {attempts} tentativas de login falhas do IP {ip_address}",
            affected_resources=[user_email] if user_email else [],
            recommended_action=f"Bloquear IP {ip_address} e revisar logs",
            severity="high"
        )
    
    def alert_data_exfiltration(self, user_id: str, downloads_count: int):
        """Alerta de possível data exfiltration"""
        self.siem.send_security_alert(
            alert_type="data_exfiltration",
            description=f"Usuário {user_id} baixou {downloads_count} documentos em curto período",
            affected_resources=[f"user:{user_id}"],
            recommended_action="Revisar atividade do usuário e verificar se há vazamento",
            severity="critical"
        )
    
    def alert_suspicious_access(self, user_id: str, ip_address: str, location: str):
        """Alerta de acesso suspeito (localização incomum)"""
        self.siem.send_security_alert(
            alert_type="suspicious_access",
            description=f"Acesso detectado de localização incomum: {location} (IP: {ip_address})",
            affected_resources=[f"user:{user_id}"],
            recommended_action="Verificar com usuário se o acesso foi legítimo",
            severity="medium"
        )
    
    def alert_security_violation(self, violation_type: str, details: Dict):
        """Alerta de violação de segurança (prompt injection, path traversal, etc)"""
        self.siem.send_security_alert(
            alert_type="security_violation",
            description=f"Tentativa de {violation_type} detectada e bloqueada",
            affected_resources=[],
            recommended_action="Revisar logs e considerar bloquear origem",
            severity="high"
        )


# Instância global
security_alerts = SecurityAlerts()


# =============================================================================
# DASHBOARD DE SEGURANÇA
# =============================================================================

class SecurityDashboard:
    """
    Gera métricas para dashboard de segurança
    """
    
    @staticmethod
    def get_security_metrics() -> Dict[str, Any]:
        """
        Obtém métricas de segurança
        
        Returns:
            Dict com métricas
        """
        # Isto seria implementado com queries ao banco de dados
        # Por enquanto, retorna estrutura
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'period': '24h',
            'metrics': {
                'total_requests': 0,  # Query do banco
                'blocked_requests': 0,  # Query do banco
                'blocked_percentage': 0.0,
                'unique_ips': 0,  # Query do banco
                'rate_limited': 0,  # Query do banco
                'security_violations': 0,  # Query do banco
                'failed_logins': 0,  # Query do banco
            },
            'top_threats': [],  # Query do banco
            'geo_distribution': {},  # Query do banco
            'alert_summary': {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0
            }
        }
    
    @staticmethod
    def get_recent_security_events(limit: int = 50) -> List[Dict]:
        """
        Obtém eventos de segurança recentes
        """
        # Query do banco de auditoria
        return []


# =============================================================================
# TESTES
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SIEM INTEGRATION - TESTE")
    print("=" * 60)
    
    # Teste 1: Envio de evento
    print("\n1. Teste de envio de evento:")
    result = siem.send_event(
        event_type="test_event",
        severity="low",
        source="test",
        message="Teste de integração SIEM",
        details={'test': True}
    )
    print(f"   {'✅ Enviado' if result else '⚠️  Não configurado'}")
    
    # Teste 2: Alerta de segurança
    print("\n2. Teste de alerta de segurança:")
    security_alerts.alert_brute_force(
        ip_address="192.168.1.100",
        attempts=10,
        user_email="test@example.com"
    )
    print("   ✅ Alerta gerado")
    
    print("\n" + "=" * 60)
    print("TESTES COMPLETADOS!")
    print("=" * 60)
