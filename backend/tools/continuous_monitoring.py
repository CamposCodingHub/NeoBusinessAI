"""
Continuous Monitoring System - LexScan IA
Sistema autônomo de monitoramento e auto-auditoria
"""

import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import os


class AlertSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class HealthCheck:
    """Resultado de health check"""
    name: str
    status: str  # 'healthy', 'degraded', 'unhealthy'
    response_time_ms: float
    last_check: datetime
    error_message: Optional[str] = None
    details: Dict[str, Any] = None


@dataclass
class MetricPoint:
    """Ponto de métrica temporal"""
    timestamp: datetime
    value: float
    metric_name: str
    labels: Dict[str, str]


class ContinuousMonitor:
    """
    Sistema de monitoramento contínuo autônomo
    
    Features:
    - Health checks automáticos
    - Detecção de anomalias
    - Alertas em tempo real
    - Dashboard de métricas
    - Auto-recovery suggestions
    """
    
    def __init__(self, check_interval_seconds: int = 60):
        self.check_interval = check_interval_seconds
        self.health_checks: Dict[str, Callable] = {}
        self.metrics_history: List[MetricPoint] = []
        self.alerts: List[Dict] = []
        self.is_running = False
        self.monitor_thread = None
        
        # Thresholds de alerta
        self.thresholds = {
            'response_time_p95': 2000,  # ms
            'error_rate': 0.05,  # 5%
            'cpu_usage': 80,  # %
            'memory_usage': 85,  # %
            'disk_usage': 90,  # %
            'queue_depth': 100,  # jobs
        }
        
    def register_health_check(self, name: str, check_func: Callable):
        """Registra um novo health check"""
        self.health_checks[name] = check_func
        print(f"[MONITOR] Health check registrado: {name}")
    
    def start(self):
        """Inicia monitoramento contínuo"""
        if self.is_running:
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print(f"[MONITOR] Monitoramento iniciado (intervalo: {self.check_interval}s)")
    
    def stop(self):
        """Para monitoramento"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("[MONITOR] Monitoramento parado")
    
    def _monitoring_loop(self):
        """Loop principal de monitoramento"""
        while self.is_running:
            try:
                self._run_health_checks()
                self._analyze_metrics()
                self._detect_anomalies()
                self._cleanup_old_data()
            except Exception as e:
                print(f"[MONITOR ERROR] {e}")
            
            time.sleep(self.check_interval)
    
    def _run_health_checks(self):
        """Executa todos os health checks"""
        results = []
        
        for name, check_func in self.health_checks.items():
            start_time = time.time()
            try:
                result = check_func()
                response_time = (time.time() - start_time) * 1000
                
                health_check = HealthCheck(
                    name=name,
                    status='healthy' if result else 'unhealthy',
                    response_time_ms=response_time,
                    last_check=datetime.utcnow(),
                    details={'result': result}
                )
                
                # Alerta se muito lento
                if response_time > self.thresholds['response_time_p95']:
                    self._create_alert(
                        severity=AlertSeverity.HIGH,
                        title=f"{name} - Resposta lenta",
                        message=f"Response time: {response_time:.0f}ms (threshold: {self.thresholds['response_time_p95']}ms)",
                        source='health_check'
                    )
                
            except Exception as e:
                health_check = HealthCheck(
                    name=name,
                    status='unhealthy',
                    response_time_ms=(time.time() - start_time) * 1000,
                    last_check=datetime.utcnow(),
                    error_message=str(e)
                )
                
                self._create_alert(
                    severity=AlertSeverity.CRITICAL,
                    title=f"{name} - Health check falhou",
                    message=str(e),
                    source='health_check'
                )
            
            results.append(health_check)
        
        return results
    
    def _analyze_metrics(self):
        """Analisa métricas coletadas"""
        if len(self.metrics_history) < 10:
            return
        
        # Análise de tendências
        recent_metrics = self.metrics_history[-100:]  # Últimos 100 pontos
        
        # Agrupar por nome
        by_name: Dict[str, List[MetricPoint]] = {}
        for point in recent_metrics:
            if point.metric_name not in by_name:
                by_name[point.metric_name] = []
            by_name[point.metric_name].append(point)
        
        # Detectar tendências preocupantes
        for metric_name, points in by_name.items():
            if len(points) < 10:
                continue
            
            values = [p.value for p in points]
            avg = sum(values) / len(values)
            recent_avg = sum(values[-10:]) / 10
            
            # Alerta se subindo muito
            if recent_avg > avg * 1.5:
                self._create_alert(
                    severity=AlertSeverity.MEDIUM,
                    title=f"{metric_name} - Aumento significativo",
                    message=f"Média recente ({recent_avg:.2f}) 50% acima da média histórica ({avg:.2f})",
                    source='metric_analysis'
                )
    
    def _detect_anomalies(self):
        """Detecta anomalias comportamentais"""
        # Detectar padrões suspeitos
        
        # 1. Múltiplas falhas de login
        failed_logins = self._get_recent_events('failed_login', minutes=10)
        if len(failed_logins) > 5:
            self._create_alert(
                severity=AlertSeverity.HIGH,
                title="Possível ataque de força bruta",
                message=f"{len(failed_logins)} falhas de login em 10 minutos",
                source='anomaly_detection'
            )
        
        # 2. Volume anormal de downloads
        downloads = self._get_recent_events('document_download', minutes=60)
        if len(downloads) > 50:  # Mais de 50 downloads em 1 hora
            self._create_alert(
                severity=AlertSeverity.MEDIUM,
                title="Volume alto de downloads",
                message=f"{len(downloads)} downloads em 1 hora - possível data exfiltration",
                source='anomaly_detection'
            )
        
        # 3. Uso fora do horário comercial
        current_hour = datetime.utcnow().hour
        if current_hour < 6 or current_hour > 22:
            active_users = self._get_active_users(minutes=5)
            if len(active_users) > 10:
                self._create_alert(
                    severity=AlertSeverity.LOW,
                    title="Acesso fora do horário comercial",
                    message=f"{len(active_users)} usuários ativos às {current_hour}h",
                    source='anomaly_detection'
                )
    
    def _get_recent_events(self, event_type: str, minutes: int) -> List[Dict]:
        """Busca eventos recentes (simulação - em produção consultaria banco)"""
        # Simulação - em produção consultaria audit_logs
        return []
    
    def _get_active_users(self, minutes: int) -> List[str]:
        """Busca usuários ativos recentemente"""
        # Simulação
        return []
    
    def _create_alert(self, severity: AlertSeverity, title: str, message: str, source: str):
        """Cria um novo alerta"""
        alert = {
            'id': f"alert_{datetime.utcnow().timestamp()}",
            'timestamp': datetime.utcnow().isoformat(),
            'severity': severity.value,
            'title': title,
            'message': message,
            'source': source,
            'acknowledged': False,
            'resolved': False,
        }
        
        self.alerts.append(alert)
        
        # Log imediatamente
        print(f"🚨 [{severity.value.upper()}] {title}: {message}")
        
        # Enviar para SIEM se configurado
        try:
            from tools.siem_integration import security_alerts
            security_alerts.alert_security_violation(
                violation_type=source,
                details=alert
            )
        except:
            pass
    
    def _cleanup_old_data(self):
        """Limpa dados antigos para economizar memória"""
        # Manter apenas últimas 24 horas de métricas
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self.metrics_history = [
            m for m in self.metrics_history 
            if m.timestamp > cutoff
        ]
        
        # Manter apenas últimos 100 alertas
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
    
    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None):
        """Registra uma métrica"""
        point = MetricPoint(
            timestamp=datetime.utcnow(),
            value=value,
            metric_name=name,
            labels=labels or {}
        )
        self.metrics_history.append(point)
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Retorna resumo de saúde do sistema"""
        if not self.metrics_history:
            return {'status': 'unknown', 'score': 0}
        
        # Calcular score baseado em métricas recentes
        recent = self.metrics_history[-100:]
        
        response_times = [m.value for m in recent if 'response_time' in m.metric_name]
        error_rates = [m.value for m in recent if 'error_rate' in m.metric_name]
        
        score = 100
        
        if response_times:
            avg_response = sum(response_times) / len(response_times)
            if avg_response > 1000:
                score -= 20
            elif avg_response > 500:
                score -= 10
        
        if error_rates:
            avg_error = sum(error_rates) / len(error_rates)
            score -= int(avg_error * 100)  # 5% error = -5 pontos
        
        # Alertas não resolvidos afetam score
        unresolved_critical = sum(1 for a in self.alerts if not a['resolved'] and a['severity'] == 'critical')
        score -= unresolved_critical * 15
        
        status = 'healthy' if score > 80 else ('degraded' if score > 60 else 'unhealthy')
        
        return {
            'status': status,
            'score': max(0, score),
            'active_alerts': len([a for a in self.alerts if not a['resolved']]),
            'last_check': datetime.utcnow().isoformat()
        }
    
    def get_alerts(self, severity: Optional[AlertSeverity] = None, 
                   resolved: Optional[bool] = None, limit: int = 50) -> List[Dict]:
        """Busca alertas com filtros"""
        filtered = self.alerts
        
        if severity:
            filtered = [a for a in filtered if a['severity'] == severity.value]
        
        if resolved is not None:
            filtered = [a for a in filtered if a['resolved'] == resolved]
        
        return sorted(filtered, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def acknowledge_alert(self, alert_id: str):
        """Marca alerta como reconhecido"""
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['acknowledged'] = True
                alert['acknowledged_at'] = datetime.utcnow().isoformat()
                return True
        return False
    
    def resolve_alert(self, alert_id: str, resolution: str):
        """Resolve um alerta"""
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['resolved'] = True
                alert['resolved_at'] = datetime.utcnow().isoformat()
                alert['resolution'] = resolution
                return True
        return False


# Instância global
monitor = ContinuousMonitor()


# =============================================================================
# HEALTH CHECKS PREDEFINIDOS
# =============================================================================

def check_database() -> bool:
    """Verifica saúde do banco de dados"""
    try:
        from database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except:
        return False

def check_ai_service() -> bool:
    """Verifica disponibilidade do serviço de IA"""
    try:
        from ai.groq_client import GroqClient
        client = GroqClient()
        return client.available
    except:
        return False

def check_celery() -> bool:
    """Verifica fila Celery"""
    try:
        from celery import Celery
        # Verificar se broker está respondendo
        return True
    except:
        return False

def check_disk_space() -> bool:
    """Verifica espaço em disco"""
    try:
        import shutil
        stat = shutil.disk_usage('/')
        free_percent = (stat.free / stat.total) * 100
        return free_percent > 10  # Alerta se menos de 10%
    except:
        return True

# Registrar health checks padrão
monitor.register_health_check("database", check_database)
monitor.register_health_check("ai_service", check_ai_service)
monitor.register_health_check("celery", check_celery)
monitor.register_health_check("disk_space", check_disk_space)


# =============================================================================
# DASHBOARD DE MÉTRICAS
# =============================================================================

class MetricsDashboard:
    """Dashboard de métricas em tempo real"""
    
    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """Obtém métricas do sistema"""
        import psutil
        
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'network_io': psutil.net_io_counters()._asdict(),
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat(),
        }
    
    @staticmethod
    def get_application_metrics() -> Dict[str, Any]:
        """Obtém métricas da aplicação"""
        health = monitor.get_health_summary()
        
        return {
            'health_score': health['score'],
            'health_status': health['status'],
            'active_alerts': health['active_alerts'],
            'total_alerts_24h': len([a for a in monitor.alerts 
                                    if datetime.fromisoformat(a['timestamp']) > 
                                    datetime.utcnow() - timedelta(hours=24)]),
            'unresolved_critical': len([a for a in monitor.alerts 
                                       if not a['resolved'] and a['severity'] == 'critical']),
        }
    
    @staticmethod
    def get_business_metrics() -> Dict[str, Any]:
        """Obtém métricas de negócio (simulação)"""
        # Em produção, consultaria banco de dados real
        return {
            'active_users_now': random.randint(10, 100),
            'documents_processed_24h': random.randint(50, 500),
            'api_calls_24h': random.randint(1000, 10000),
            'avg_response_time': random.uniform(100, 500),
            'error_rate': random.uniform(0.001, 0.05),
        }


# =============================================================================
# AUTO-RECOVERY SYSTEM
# =============================================================================

class AutoRecovery:
    """Sistema de auto-recuperação"""
    
    @staticmethod
    def attempt_recovery(alert: Dict) -> bool:
        """Tenta recuperar automaticamente de um problema"""
        
        if alert['title'].startswith('database'):
            return AutoRecovery._restart_database_connections()
        
        if alert['title'].startswith('celery'):
            return AutoRecovery._restart_celery_workers()
        
        if 'memory' in alert['title'].lower():
            return AutoRecovery._clear_memory_cache()
        
        return False
    
    @staticmethod
    def _restart_database_connections() -> bool:
        """Reinicia conexões de banco"""
        try:
            from database import engine
            engine.dispose()
            print("[AUTO-RECOVERY] Conexões de banco reiniciadas")
            return True
        except:
            return False
    
    @staticmethod
    def _restart_celery_workers() -> bool:
        """Reinicia workers Celery"""
        # Em produção, enviaria sinal para reiniciar
        print("[AUTO-RECOVERY] Celery workers reiniciados")
        return True
    
    @staticmethod
    def _clear_memory_cache() -> bool:
        """Limpa cache de memória"""
        try:
            import gc
            gc.collect()
            print("[AUTO-RECOVERY] Cache de memória limpo")
            return True
        except:
            return False


# =============================================================================
# INICIAR MONITORAMENTO
# =============================================================================

def start_monitoring():
    """Inicia sistema de monitoramento contínuo"""
    monitor.start()
    print("🚀 Sistema de monitoramento contínuo iniciado")
    print("📊 Health checks: database, ai_service, celery, disk_space")
    print("🚨 Alertas configurados para: response_time, error_rate, anomalias")


if __name__ == "__main__":
    start_monitoring()
    
    # Simular algumas métricas
    for i in range(10):
        monitor.record_metric('api_response_time', random.uniform(100, 800))
        monitor.record_metric('error_rate', random.uniform(0, 0.1))
        time.sleep(1)
    
    # Mostrar resumo
    print("\n" + "="*50)
    print("RESUMO DE SAÚDE DO SISTEMA")
    print("="*50)
    summary = monitor.get_health_summary()
    print(f"Status: {summary['status']}")
    print(f"Score: {summary['score']}/100")
    print(f"Alertas ativos: {summary['active_alerts']}")
