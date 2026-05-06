"""
Security Intelligence Layer - Alert Manager
============================================
Sistema de alertas e notificações de segurança.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    DASHBOARD = "dashboard"
    LOG = "log"


@dataclass
class SecurityAlert:
    """Representa um alerta de segurança"""
    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    channels: List[AlertChannel] = field(default_factory=lambda: [AlertChannel.DASHBOARD])
    data: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


class AlertManager:
    """
    Gerenciador de alertas de segurança
    """
    
    def __init__(self, sil):
        self.sil = sil
        self._alerts: List[SecurityAlert] = []
        self._alert_counter = 0
        
        # Configurações
        self._admin_emails = ["admin@neobusiness.ai", "security@neobusiness.ai"]
        self._webhook_url = None  # Configurar em produção
        
        # Canais ativos por severidade
        self._channel_config = {
            AlertLevel.INFO: [AlertChannel.DASHBOARD, AlertChannel.LOG],
            AlertLevel.WARNING: [AlertChannel.DASHBOARD, AlertChannel.LOG, AlertChannel.EMAIL],
            AlertLevel.ERROR: [AlertChannel.DASHBOARD, AlertChannel.LOG, AlertChannel.EMAIL, AlertChannel.WEBHOOK],
            AlertLevel.CRITICAL: [AlertChannel.DASHBOARD, AlertChannel.LOG, AlertChannel.EMAIL, 
                                AlertChannel.SMS, AlertChannel.WEBHOOK]
        }
        
        logger.info("🔔 Alert Manager inicializado")
    
    def send_alert(self, level: str, title: str, message: str,
                  data: Optional[Dict] = None, channels: Optional[List[str]] = None):
        """Envia um alerta de segurança"""
        
        # Converter level string para enum
        try:
            alert_level = AlertLevel(level.lower())
        except ValueError:
            alert_level = AlertLevel.INFO
        
        # Gerar ID único
        self._alert_counter += 1
        alert_id = f"SEC-{datetime.utcnow().strftime('%Y%m%d')}-{self._alert_counter:04d}"
        
        # Determinar canais
        if channels:
            alert_channels = [AlertChannel(c) for c in channels]
        else:
            alert_channels = self._channel_config.get(alert_level, [AlertChannel.DASHBOARD])
        
        # Criar alerta
        alert = SecurityAlert(
            id=alert_id,
            level=alert_level,
            title=title,
            message=message,
            timestamp=datetime.utcnow(),
            channels=alert_channels,
            data=data or {}
        )
        
        # Armazenar
        self._alerts.append(alert)
        
        # Limitar histórico
        if len(self._alerts) > 1000:
            self._alerts = self._alerts[-1000:]
        
        # Enviar para cada canal
        for channel in alert_channels:
            try:
                self._send_to_channel(alert, channel)
            except Exception as e:
                logger.error(f"❌ Erro ao enviar alerta para {channel}: {e}")
        
        # Log
        log_func = getattr(logger, alert_level.value, logger.info)
        log_func(f"🚨 ALERTA [{alert_id}] {title}: {message}")
        
        return alert_id
    
    def _send_to_channel(self, alert: SecurityAlert, channel: AlertChannel):
        """Envia alerta para canal específico"""
        if channel == AlertChannel.LOG:
            self._send_to_log(alert)
        elif channel == AlertChannel.DASHBOARD:
            self._send_to_dashboard(alert)
        elif channel == AlertChannel.EMAIL:
            self._send_email(alert)
        elif channel == AlertChannel.SMS:
            self._send_sms(alert)
        elif channel == AlertChannel.WEBHOOK:
            self._send_webhook(alert)
    
    def _send_to_log(self, alert: SecurityAlert):
        """Registra no log do sistema"""
        log_entry = {
            'alert_id': alert.id,
            'level': alert.level.value,
            'title': alert.title,
            'message': alert.message,
            'timestamp': alert.timestamp.isoformat(),
            'data': alert.data
        }
        
        # Em produção, salvar no banco ou Elasticsearch
        logger.warning(f"SECURITY ALERT: {json.dumps(log_entry)}")
    
    def _send_to_dashboard(self, alert: SecurityAlert):
        """Disponibiliza no dashboard"""
        # O dashboard já lê de self._alerts
        pass
    
    def _send_email(self, alert: SecurityAlert):
        """Envia email para admins"""
        # Implementação simplificada
        # Em produção usar SendGrid/AWS SES
        
        subject = f"[{alert.level.value.upper()}] NeoBusiness AI - {alert.title}"
        
        body = f"""
Alerta de Segurança
==================

ID: {alert.id}
Nível: {alert.level.value.upper()}
Título: {alert.title}
Mensagem: {alert.message}
Data: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

Dados Adicionais:
{json.dumps(alert.data, indent=2, default=str)}

---
NeoBusiness AI Security Intelligence Layer
        """
        
        # Simular envio
        logger.info(f"📧 Email enviado para {self._admin_emails}: {subject}")
        
        # Em produção:
        # send_email(to=self._admin_emails, subject=subject, body=body)
    
    def _send_sms(self, alert: SecurityAlert):
        """Envia SMS para admins (apenas crítico)"""
        if alert.level != AlertLevel.CRITICAL:
            return
        
        message = f"🚨 NEOBUSINESS ALERT: {alert.title}. {alert.message[:100]}"
        
        # Simular envio
        logger.info(f"📱 SMS enviado: {message}")
        
        # Em produção usar Twilio
    
    def _send_webhook(self, alert: SecurityAlert):
        """Envia para webhook externo (Slack, PagerDuty, etc)"""
        if not self._webhook_url:
            return
        
        payload = {
            'alert_id': alert.id,
            'level': alert.level.value,
            'title': alert.title,
            'message': alert.message,
            'timestamp': alert.timestamp.isoformat(),
            'system': 'NeoBusiness AI',
            'data': alert.data
        }
        
        # Simular envio
        logger.info(f"🌐 Webhook enviado para {self._webhook_url}")
        
        # Em produção:
        # requests.post(self._webhook_url, json=payload, timeout=5)
    
    def send_report(self, report: Dict):
        """Envia relatório por email"""
        subject = f"📊 Relatório de Segurança - {report.get('date', 'Hoje')}"
        
        body = f"""
Relatório de Segurança - NeoBusiness AI
========================================

Período: {report.get('period', 'Últimas 24h')}
Gerado em: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Resumo:
-------
Status Geral: {report.get('overall_status', 'N/A')}
Score de Segurança: {report.get('security_score', 0):.1f}/10
Tentativas de Login: {report.get('login_attempts', 0)}
Ataques Bloqueados: {report.get('blocked_attacks', 0)}
Anomalias Detectadas: {report.get('anomalies', 0)}

Detalhes completos disponíveis no dashboard.

---
NeoBusiness AI Security Intelligence Layer
        """
        
        logger.info(f"📧 Relatório enviado por email: {subject}")
    
    def get_active_alerts(self, level: Optional[str] = None) -> List[Dict]:
        """Retorna alertas ativos"""
        alerts = self._alerts
        
        if level:
            alerts = [a for a in alerts if a.level.value == level.lower()]
        
        # Ordenar por timestamp (mais recentes primeiro)
        alerts = sorted(alerts, key=lambda x: x.timestamp, reverse=True)
        
        return [
            {
                'id': a.id,
                'level': a.level.value,
                'title': a.title,
                'message': a.message,
                'timestamp': a.timestamp.isoformat(),
                'data': a.data,
                'acknowledged': a.acknowledged,
                'channels': [c.value for c in a.channels]
            }
            for a in alerts[-100:]  # Últimos 100
        ]
    
    def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        """Marca alerta como reconhecido"""
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_by = user
                alert.acknowledged_at = datetime.utcnow()
                logger.info(f"✅ Alerta {alert_id} reconhecido por {user}")
                return True
        return False
    
    def clear_old_alerts(self, hours: int = 24):
        """Limpa alertas antigos"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        old_count = len([a for a in self._alerts if a.timestamp < cutoff])
        self._alerts = [a for a in self._alerts if a.timestamp >= cutoff]
        
        logger.info(f"🧹 {old_count} alertas antigos removidos")
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de alertas"""
        stats = {
            'total_24h': 0,
            'by_level': {},
            'by_channel': {},
            'unacknowledged': 0
        }
        
        cutoff = datetime.utcnow() - timedelta(hours=24)
        
        for alert in self._alerts:
            if alert.timestamp >= cutoff:
                stats['total_24h'] += 1
                
                # Por nível
                level = alert.level.value
                stats['by_level'][level] = stats['by_level'].get(level, 0) + 1
                
                # Por canal
                for channel in alert.channels:
                    ch = channel.value
                    stats['by_channel'][ch] = stats['by_channel'].get(ch, 0) + 1
                
                # Não reconhecidos
                if not alert.acknowledged:
                    stats['unacknowledged'] += 1
        
        return stats
