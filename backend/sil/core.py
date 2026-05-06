"""
Security Intelligence Layer - Core
==================================
Orquestrador principal do sistema de auto-auditoria contínua.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import threading
import time

from .monitor import LoginMonitor
from .detector import AnomalyDetector
from .autotest import SecurityAutoTester
from .ai_engine import SecurityAI
from .alerts import AlertManager
from .reporter import SecurityReporter
from .autocorrect import AutoCorrectEngine
from .simulator import AttackSimulator

logger = logging.getLogger(__name__)


class SecurityStatus(Enum):
    STABLE = "stable"
    ALERT = "alert"
    CRITICAL = "critical"
    MAINTENANCE = "maintenance"


@dataclass
class SecurityMetrics:
    """Métricas de segurança em tempo real"""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    login_attempts_1m: int = 0
    login_attempts_5m: int = 0
    login_attempts_1h: int = 0
    failed_logins_1m: int = 0
    failed_logins_5m: int = 0
    blocked_ips: int = 0
    active_attacks: int = 0
    security_score: float = 10.0
    status: SecurityStatus = SecurityStatus.STABLE
    last_attack: Optional[datetime] = None
    anomaly_count: int = 0
    auto_tests_passed: int = 0
    auto_tests_failed: int = 0
    corrections_applied: int = 0


class SecurityIntelligenceLayer:
    """
    Camada de Inteligência de Segurança - Sistema autônomo de proteção
    """
    
    def __init__(self, db_session=None):
        self.db = db_session
        self.is_running = False
        self.metrics = SecurityMetrics()
        self._lock = threading.RLock()
        
        # Componentes
        self.monitor = LoginMonitor(self)
        self.detector = AnomalyDetector(self)
        self.autotest = SecurityAutoTester(self)
        self.ai_engine = SecurityAI(self)
        self.alerts = AlertManager(self)
        self.reporter = SecurityReporter(self)
        self.autocorrect = AutoCorrectEngine(self)
        self.simulator = AttackSimulator(self)
        
        # Threads de monitoramento
        self._threads = []
        self._stop_event = threading.Event()
        
        logger.info("🛡️ Security Intelligence Layer inicializado")
    
    def start_monitoring(self):
        """Inicia monitoramento contínuo 24/7"""
        if self.is_running:
            logger.warning("SIL já está rodando")
            return
        
        self.is_running = True
        self._stop_event.clear()
        
        # Iniciar threads de monitoramento
        threads_config = [
            (self._monitoring_loop, "SIL-Monitor", 5),      # A cada 5 segundos
            (self._detection_loop, "SIL-Detector", 10),     # A cada 10 segundos
            (self._ai_analysis_loop, "SIL-AI", 60),         # A cada 1 minuto
            (self._autotest_loop, "SIL-AutoTest", 3600),    # A cada 1 hora
            (self._reporting_loop, "SIL-Reporter", 86400),  # A cada 24 horas
        ]
        
        for target, name, interval in threads_config:
            thread = threading.Thread(
                target=self._run_loop,
                args=(target, interval, name),
                name=name,
                daemon=True
            )
            thread.start()
            self._threads.append(thread)
            logger.info(f"🚀 Thread {name} iniciada (intervalo: {interval}s)")
        
        logger.info("✅ SIL iniciado - Monitoramento 24/7 ativo")
        self.alerts.send_alert(
            level="info",
            title="SIL Iniciado",
            message="Security Intelligence Layer iniciado com sucesso"
        )
    
    def stop_monitoring(self):
        """Para monitoramento"""
        logger.info("🛑 Parando SIL...")
        self._stop_event.set()
        self.is_running = False
        
        for thread in self._threads:
            thread.join(timeout=5)
        
        self._threads.clear()
        logger.info("✅ SIL parado")
    
    def _run_loop(self, target_func, interval, name):
        """Wrapper para loops de monitoramento"""
        while not self._stop_event.is_set():
            try:
                target_func()
            except Exception as e:
                logger.error(f"❌ Erro em {name}: {e}")
                self.alerts.send_alert(
                    level="error",
                    title=f"Erro em {name}",
                    message=str(e)
                )
            
            # Aguardar próximo ciclo
            self._stop_event.wait(interval)
    
    def _monitoring_loop(self):
        """Loop de monitoramento contínuo (a cada 5s)"""
        # Coletar métricas de login
        metrics = self.monitor.collect_metrics()
        
        with self._lock:
            self.metrics.login_attempts_1m = metrics.get('attempts_1m', 0)
            self.metrics.failed_logins_1m = metrics.get('failed_1m', 0)
            self.metrics.blocked_ips = metrics.get('blocked_ips', 0)
        
        # Verificar limites críticos
        if self.metrics.failed_logins_1m > 50:
            self._handle_critical_attack()
    
    def _detection_loop(self):
        """Loop de detecção de anomalias (a cada 10s)"""
        # Analisar padrões
        anomalies = self.detector.detect_anomalies()
        
        if anomalies:
            with self._lock:
                self.metrics.anomaly_count += len(anomalies)
                self.metrics.last_attack = datetime.utcnow()
            
            for anomaly in anomalies:
                self._handle_anomaly(anomaly)
    
    def _ai_analysis_loop(self):
        """Loop de análise de IA (a cada 1min)"""
        # Análise preditiva
        predictions = self.ai_engine.analyze_threats()
        
        if predictions.get('risk_score', 0) > 0.7:
            self._handle_predicted_attack(predictions)
        
        # Atualizar score de segurança
        with self._lock:
            self.metrics.security_score = self.ai_engine.calculate_security_score()
    
    def _autotest_loop(self):
        """Loop de auto-testes (a cada 1h)"""
        logger.info("🧪 Iniciando auto-testes programados")
        
        results = self.autotest.run_all_tests()
        
        with self._lock:
            self.metrics.auto_tests_passed = results.get('passed', 0)
            self.metrics.auto_tests_failed = results.get('failed', 0)
        
        # Se falhou, tentar auto-correção
        if results.get('failed', 0) > 0:
            for failure in results.get('failures', []):
                self.autocorrect.attempt_fix(failure)
    
    def _reporting_loop(self):
        """Loop de relatórios (a cada 24h)"""
        logger.info("📊 Gerando relatório diário")
        
        report = self.reporter.generate_daily_report()
        
        # Enviar para admins
        self.alerts.send_report(report)
        
        logger.info("✅ Relatório diário gerado e enviado")
    
    def _handle_anomaly(self, anomaly: Dict[str, Any]):
        """Processa anomalia detectada"""
        severity = anomaly.get('severity', 'low')
        
        if severity == 'critical':
            self._enter_critical_mode(anomaly)
        elif severity == 'high':
            self._enter_alert_mode(anomaly)
        
        # Enviar alerta
        self.alerts.send_alert(
            level=severity,
            title=f"Anomalia Detectada: {anomaly.get('type')}",
            message=anomaly.get('description'),
            data=anomaly
        )
    
    def _handle_critical_attack(self):
        """Resposta a ataque crítico em andamento"""
        logger.critical("🚨 ATAQUE CRÍTICO DETECTADO!")
        
        with self._lock:
            self.metrics.status = SecurityStatus.CRITICAL
            self.metrics.active_attacks += 1
        
        # Ações imediatas
        self.autocorrect.emergency_lockdown()
        
        # Alertar admins
        self.alerts.send_alert(
            level="critical",
            title="🚨 ATAQUE CRÍTICO EM ANDAMENTO",
            message="Múltiplas falhas de login detectadas. Sistema em modo de proteção.",
            channels=['email', 'sms', 'webhook']
        )
    
    def _handle_predicted_attack(self, predictions: Dict):
        """Resposta a ataque predito pela IA"""
        logger.warning(f"⚠️ Ataque predito: {predictions}")
        
        # Reforçar proteção preventivamente
        self.autocorrect.strengthen_defenses(predictions)
        
        self.alerts.send_alert(
            level="warning",
            title="⚠️ Ataque Previsto pela IA",
            message=f"Risco: {predictions.get('risk_score', 0):.2%}",
            data=predictions
        )
    
    def _enter_critical_mode(self, anomaly: Dict):
        """Ativa modo crítico de segurança"""
        with self._lock:
            self.metrics.status = SecurityStatus.CRITICAL
        
        logger.critical(f"🚨 MODO CRÍTICO ATIVADO: {anomaly}")
        
        # Ações de emergência
        self.monitor.emergency_rate_limit()
        self.autocorrect.apply_emergency_patches()
    
    def _enter_alert_mode(self, anomaly: Dict):
        """Ativa modo de alerta"""
        with self._lock:
            if self.metrics.status != SecurityStatus.CRITICAL:
                self.metrics.status = SecurityStatus.ALERT
        
        logger.warning(f"⚠️ MODO ALERTA: {anomaly}")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Retorna métricas atuais"""
        with self._lock:
            return {
                "timestamp": self.metrics.timestamp.isoformat(),
                "status": self.metrics.status.value,
                "security_score": self.metrics.security_score,
                "login_attempts_1m": self.metrics.login_attempts_1m,
                "login_attempts_5m": self.metrics.login_attempts_5m,
                "failed_logins_1m": self.metrics.failed_logins_1m,
                "blocked_ips": self.metrics.blocked_ips,
                "active_attacks": self.metrics.active_attacks,
                "anomaly_count": self.metrics.anomaly_count,
                "last_attack": self.metrics.last_attack.isoformat() if self.metrics.last_attack else None,
                "auto_tests": {
                    "passed": self.metrics.auto_tests_passed,
                    "failed": self.metrics.auto_tests_failed
                },
                "corrections_applied": self.metrics.corrections_applied
            }
    
    def record_login_attempt(self, email: str, ip: str, success: bool, 
                            metadata: Optional[Dict] = None):
        """Registra tentativa de login para análise"""
        self.monitor.record_attempt(email, ip, success, metadata)
        
        # Verificar imediatamente se é anomalia
        if not success:
            is_suspicious = self.detector.check_immediate_threat(email, ip)
            if is_suspicious:
                self._handle_anomaly({
                    'type': 'suspicious_login',
                    'severity': 'high',
                    'description': f'Tentativa suspeita de login: {email} from {ip}',
                    'data': {'email': email, 'ip': ip}
                })
    
    def run_simulation(self, attack_type: str) -> Dict:
        """Executa simulação de ataque controlada"""
        return self.simulator.run_simulation(attack_type)


# Singleton instance
_sil_instance: Optional[SecurityIntelligenceLayer] = None


def get_sil(db_session=None) -> SecurityIntelligenceLayer:
    """Retorna instância singleton do SIL"""
    global _sil_instance
    if _sil_instance is None:
        _sil_instance = SecurityIntelligenceLayer(db_session)
    return _sil_instance
