"""
Security Intelligence Layer - Anomaly Detector
===============================================
Detecção inteligente de anomalias e padrões de ataque.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    BRUTE_FORCE = "brute_force"
    DISTRIBUTED_ATTACK = "distributed_attack"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    UNUSUAL_HOUR = "unusual_hour"
    NEW_COUNTRY = "new_country"
    RAPID_FIRE = "rapid_fire"
    CREDENTIAL_STUFFING = "credential_stuffing"
    ACCOUNT_TAKEOVER = "account_takeover"
    BOT_DETECTED = "bot_detected"
    TOR_EXIT_NODE = "tor_exit_node"


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Anomaly:
    """Representa uma anomalia detectada"""
    type: AnomalyType
    severity: Severity
    description: str
    timestamp: datetime
    affected_users: List[str]
    affected_ips: List[str]
    confidence: float  # 0.0 a 1.0
    data: Dict[str, Any]
    recommended_action: str


class AnomalyDetector:
    """
    Detector de anomalias de segurança
    """
    
    def __init__(self, sil):
        self.sil = sil
        
        # Baselines estatísticos
        self._baseline_attempts_per_minute = 10
        self._baseline_failure_rate = 0.3
        self._baseline_unique_ips_per_hour = 50
        
        # Histórico para análise de tendências
        self._hourly_stats: List[Dict] = []
        
        # Lista de IPs TOR conhecidos (simplificado)
        self._tor_exit_nodes: set = set()
        
        # Padrões de bots conhecidos
        self._bot_signatures = [
            "python-requests",
            "curl",
            "wget",
            "scrapy",
            "selenium",
            "phantomjs",
            "headless"
        ]
        
        logger.info("🔍 Anomaly Detector inicializado")
    
    def detect_anomalies(self) -> List[Anomaly]:
        """Executa todas as detecções de anomalias"""
        anomalies = []
        
        # Coletar dados atuais
        metrics = self.sil.monitor.collect_metrics()
        
        # Executar detecções
        detectors = [
            self._detect_brute_force,
            self._detect_distributed_attack,
            self._detect_rapid_fire,
            self._detect_credential_stuffing,
            self._detect_bot_activity,
            self._detect_unusual_patterns,
            self._detect_tor_usage,
        ]
        
        for detector in detectors:
            try:
                result = detector(metrics)
                if result:
                    anomalies.append(result)
            except Exception as e:
                logger.error(f"❌ Erro em detector {detector.__name__}: {e}")
        
        # Análise comportamental de usuários
        user_anomalies = self._analyze_user_behaviors()
        anomalies.extend(user_anomalies)
        
        return anomalies
    
    def check_immediate_threat(self, email: str, ip: str) -> bool:
        """Verifica se há ameaça imediata (para uso em tempo real)"""
        # Verificações rápidas para bloqueio imediato
        
        # 1. Verificar se é TOR
        if self._is_tor_exit_node(ip):
            logger.warning(f"🧅 TOR detectado: {ip}")
            return True
        
        # 2. Verificar padrão de velocidade extrema
        if self._is_rapid_fire(ip):
            return True
        
        # 3. Verificar lista negra
        if ip in self._tor_exit_nodes:
            return True
        
        return False
    
    def _detect_brute_force(self, metrics: Dict) -> Optional[Anomaly]:
        """Detecta tentativas de brute force"""
        failed_1m = metrics.get('failed_1m', 0)
        attempts_1m = metrics.get('attempts_1m', 0)
        
        # Critérios para brute force
        if failed_1m > 20:  # Mais de 20 falhas em 1 minuto
            failure_rate = failed_1m / max(attempts_1m, 1)
            
            if failure_rate > 0.8:  # 80% de falhas
                return Anomaly(
                    type=AnomalyType.BRUTE_FORCE,
                    severity=Severity.CRITICAL if failed_1m > 50 else Severity.HIGH,
                    description=f"Possível ataque de força bruta: {failed_1m} falhas/min",
                    timestamp=datetime.utcnow(),
                    affected_users=[],
                    affected_ips=[],  # Preencher com análise real
                    confidence=0.9,
                    data={'failed_attempts': failed_1m, 'failure_rate': failure_rate},
                    recommended_action="Ativar bloqueio de emergência e CAPTCHA"
                )
        
        return None
    
    def _detect_distributed_attack(self, metrics: Dict) -> Optional[Anomaly]:
        """Detecta ataques distribuídos (DDoS de login)"""
        unique_ips = metrics.get('unique_ips_1h', 0)
        attempts_1h = metrics.get('attempts_1h', 0)
        
        # Se muitos IPs diferentes tentando logar
        if unique_ips > 100 and attempts_1h > 500:
            avg_attempts_per_ip = attempts_1h / unique_ips
            
            # Se cada IP faz poucas tentativas (evade rate limiting por IP)
            if avg_attempts_per_ip < 10:
                return Anomaly(
                    type=AnomalyType.DISTRIBUTED_ATTACK,
                    severity=Severity.CRITICAL,
                    description=f"Ataque distribuído detectado: {unique_ips} IPs, {attempts_1h} tentativas",
                    timestamp=datetime.utcnow(),
                    affected_users=[],
                    affected_ips=[],
                    confidence=0.85,
                    data={'unique_ips': unique_ips, 'total_attempts': attempts_1h},
                    recommended_action="Ativar proteção DDoS e análise de padrões"
                )
        
        return None
    
    def _detect_rapid_fire(self, metrics: Dict) -> Optional[Anomaly]:
        """Detecta tentativas em sequência muito rápida"""
        # Analisar timestamps das tentativas recentes
        recent_attempts = list(self.sil.monitor._attempts_1m)
        
        if len(recent_attempts) < 5:
            return None
        
        # Calcular intervalos entre tentativas
        intervals = []
        for i in range(1, len(recent_attempts)):
            delta = (recent_attempts[i].timestamp - recent_attempts[i-1].timestamp).total_seconds()
            intervals.append(delta)
        
        if not intervals:
            return None
        
        avg_interval = statistics.mean(intervals)
        
        # Se média < 0.5 segundos = bot
        if avg_interval < 0.5:
            return Anomaly(
                type=AnomalyType.RAPID_FIRE,
                severity=Severity.HIGH,
                description=f"Tentativas em sequência muito rápida (avg: {avg_interval:.2f}s)",
                timestamp=datetime.utcnow(),
                affected_users=[],
                affected_ips=[a.ip_address for a in recent_attempts[-10:]],
                confidence=0.95,
                data={'avg_interval': avg_interval, 'total_attempts': len(recent_attempts)},
                recommended_action="Bloquear IPs e ativar CAPTCHA"
            )
        
        return None
    
    def _detect_credential_stuffing(self, metrics: Dict) -> Optional[Anomaly]:
        """Detecta credential stuffing (senhas vazadas)"""
        # Verificar padrão: muitos emails diferentes, senhas variadas, IPs diferentes
        recent_attempts = list(self.sil.monitor._attempts_5m)
        
        if len(recent_attempts) < 20:
            return None
        
        unique_emails = set(a.email for a in recent_attempts)
        unique_ips = set(a.ip_address for a in recent_attempts)
        
        # Se muitos emails diferentes de poucos IPs
        if len(unique_emails) > 15 and len(unique_ips) < 5:
            return Anomaly(
                type=AnomalyType.CREDENTIAL_STUFFING,
                severity=Severity.CRITICAL,
                description=f"Possível credential stuffing: {len(unique_emails)} emails de {len(unique_ips)} IPs",
                timestamp=datetime.utcnow(),
                affected_users=list(unique_emails),
                affected_ips=list(unique_ips),
                confidence=0.8,
                data={'unique_emails': len(unique_emails), 'unique_ips': len(unique_ips)},
                recommended_action="Bloquear IPs, notificar usuários afetados, forçar reset de senha"
            )
        
        return None
    
    def _detect_bot_activity(self, metrics: Dict) -> Optional[Anomaly]:
        """Detecta atividade de bots por User-Agent"""
        recent_attempts = list(self.sil.monitor._attempts_5m)
        
        bot_attempts = []
        for attempt in recent_attempts:
            ua = attempt.user_agent.lower()
            if any(sig in ua for sig in self._bot_signatures):
                bot_attempts.append(attempt)
        
        if len(bot_attempts) > 5:
            unique_ips = set(a.ip_address for a in bot_attempts)
            return Anomaly(
                type=AnomalyType.BOT_DETECTED,
                severity=Severity.MEDIUM,
                description=f"Atividade de bot detectada: {len(bot_attempts)} tentativas",
                timestamp=datetime.utcnow(),
                affected_users=[],
                affected_ips=list(unique_ips),
                confidence=0.9,
                data={'bot_attempts': len(bot_attempts), 'user_agents': list(set(a.user_agent for a in bot_attempts))},
                recommended_action="Bloquear User-Agents de bot, ativar fingerprinting"
            )
        
        return None
    
    def _detect_unusual_patterns(self, metrics: Dict) -> Optional[Anomaly]:
        """Detecta padrões estatisticamente anômalos"""
        # Comparar com baseline histórico
        current_failure_rate = metrics.get('failed_1m', 0) / max(metrics.get('attempts_1m', 1), 1)
        
        if current_failure_rate > self._baseline_failure_rate * 3:  # 3x o normal
            return Anomaly(
                type=AnomalyType.SUSPICIOUS_PATTERN,
                severity=Severity.HIGH,
                description=f"Taxa de falha anormal: {current_failure_rate:.1%} (baseline: {self._baseline_failure_rate:.1%})",
                timestamp=datetime.utcnow(),
                affected_users=[],
                affected_ips=[],
                confidence=0.75,
                data={'current_rate': current_failure_rate, 'baseline': self._baseline_failure_rate},
                recommended_action="Investigar causas e reforçar monitoramento"
            )
        
        return None
    
    def _detect_tor_usage(self, metrics: Dict) -> Optional[Anomaly]:
        """Detecta uso de rede TOR"""
        # Verificar IPs recentes contra lista de nós TOR
        recent_ips = set(a.ip_address for a in self.sil.monitor._attempts_5m)
        
        tor_ips = recent_ips.intersection(self._tor_exit_nodes)
        
        if tor_ips:
            return Anomaly(
                type=AnomalyType.TOR_EXIT_NODE,
                severity=Severity.HIGH,
                description=f"Acesso via TOR detectado: {len(tor_ips)} IPs",
                timestamp=datetime.utcnow(),
                affected_users=[],
                affected_ips=list(tor_ips),
                confidence=0.95,
                data={'tor_ips': list(tor_ips)},
                recommended_action="Bloquear acesso TOR ou exigir verificação adicional"
            )
        
        return None
    
    def _analyze_user_behaviors(self) -> List[Anomaly]:
        """Analisa comportamentos individuais de usuários"""
        anomalies = []
        
        # Obter todos os usuários com tentativas recentes
        recent_attempts = list(self.sil.monitor._attempts_1h)
        users = set(a.email for a in recent_attempts)
        
        for user in users:
            user_anomalies = self._analyze_single_user(user)
            anomalies.extend(user_anomalies)
        
        return anomalies
    
    def _analyze_single_user(self, email: str) -> List[Anomaly]:
        """Analisa comportamento de usuário específico"""
        anomalies = []
        
        patterns = self.sil.monitor.get_login_patterns(email, hours=24)
        
        if patterns.get('status') != 'ok':
            return anomalies
        
        # 1. Detectar novo país
        if patterns.get('unique_countries', 0) > 0:
            # Verificar último login
            user_attempts = [a for a in self.sil.monitor._attempts_1h if a.email == email]
            if user_attempts:
                last_attempt = user_attempts[-1]
                risk = self.sil.monitor.analyze_geolocation_risk(
                    email, 
                    last_attempt.ip_address,
                    last_attempt.country
                )
                
                if risk > 0.5:
                    anomalies.append(Anomaly(
                        type=AnomalyType.NEW_COUNTRY,
                        severity=Severity.MEDIUM,
                        description=f"Login de novo país: {last_attempt.country}",
                        timestamp=datetime.utcnow(),
                        affected_users=[email],
                        affected_ips=[last_attempt.ip_address],
                        confidence=risk,
                        data={'country': last_attempt.country, 'risk_score': risk},
                        recommended_action="Enviar notificação ao usuário, exigir 2FA"
                    ))
        
        # 2. Detectar horário incomum
        if patterns.get('peak_hours'):
            peak_hour = max(patterns['peak_hours'].items(), key=lambda x: x[1])[0]
            current_hour = datetime.utcnow().hour
            
            # Se login for em horário muito diferente do usual
            if abs(current_hour - peak_hour) > 8:
                anomalies.append(Anomaly(
                    type=AnomalyType.UNUSUAL_HOUR,
                    severity=Severity.LOW,
                    description=f"Login em horário incomum (usual: {peak_hour}h, atual: {current_hour}h)",
                    timestamp=datetime.utcnow(),
                    affected_users=[email],
                    affected_ips=[],
                    confidence=0.6,
                    data={'usual_hour': peak_hour, 'current_hour': current_hour},
                    recommended_action="Monitorar, notificar se repetir"
                ))
        
        return anomalies
    
    def _is_tor_exit_node(self, ip: str) -> bool:
        """Verifica se IP é nó de saída TOR"""
        return ip in self._tor_exit_nodes
    
    def _is_rapid_fire(self, ip: str) -> bool:
        """Verifica se IP está fazendo tentativas muito rápidas"""
        with self.sil.monitor._lock:
            attempts = self.sil.monitor._ip_attempts.get(ip, [])
            if len(attempts) < 5:
                return False
            
            # Verificar últimas 5 tentativas
            recent = attempts[-5:]
            if len(recent) < 5:
                return False
            
            time_span = (recent[-1] - recent[0]).total_seconds()
            return time_span < 2.0  # 5 tentativas em menos de 2 segundos
    
    def update_baseline(self):
        """Atualiza baselines estatísticos"""
        # Calcular médias das últimas 24h
        # (Simplificado - em produção usar dados históricos)
        pass
    
    def get_threat_intelligence(self) -> Dict:
        """Retorna inteligência de ameaças atual"""
        return {
            'known_tor_nodes': len(self._tor_exit_nodes),
            'bot_signatures': len(self._bot_signatures),
            'baseline_failure_rate': self._baseline_failure_rate,
            'active_anomalies': len(self.detect_anomalies())
        }
