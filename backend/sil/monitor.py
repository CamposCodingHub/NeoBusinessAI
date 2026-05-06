"""
Security Intelligence Layer - Login Monitor
===========================================
Monitoramento contínuo de tentativas de login em tempo real.
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import deque, defaultdict
from dataclasses import dataclass, field
import threading
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class LoginAttempt:
    """Registro de tentativa de login"""
    timestamp: datetime
    email: str
    ip_address: str
    success: bool
    user_agent: str = ""
    device_fingerprint: str = ""
    country: str = ""
    city: str = ""
    metadata: Dict = field(default_factory=dict)


class LoginMonitor:
    """
    Monitor contínuo de atividades de login
    """
    
    def __init__(self, sil):
        self.sil = sil
        self._lock = threading.RLock()
        
        # Buffers circulares para análise em tempo real
        self._attempts_1m: deque = deque(maxlen=1000)  # Últimos 1000 em 1 min
        self._attempts_5m: deque = deque(maxlen=5000)  # Últimos 5000 em 5 min
        self._attempts_1h: deque = deque(maxlen=50000)  # Última hora
        
        # Trackers
        self._ip_attempts: Dict[str, List[datetime]] = defaultdict(list)
        self._user_attempts: Dict[str, List[datetime]] = defaultdict(list)
        self._blocked_ips: Dict[str, datetime] = {}
        self._suspicious_ips: set = set()
        
        # Métricas
        self._total_attempts = 0
        self._total_success = 0
        self._total_failed = 0
        
        # Dispositivos conhecidos por usuário
        self._known_devices: Dict[str, set] = defaultdict(set)
        
        logger.info("👁️ Login Monitor inicializado")
    
    def record_attempt(self, email: str, ip: str, success: bool, 
                      metadata: Optional[Dict] = None) -> bool:
        """
        Registra uma tentativa de login
        Retorna: True se permitido, False se bloqueado
        """
        now = datetime.utcnow()
        
        # Criar registro
        attempt = LoginAttempt(
            timestamp=now,
            email=email.lower().strip(),
            ip_address=ip,
            success=success,
            user_agent=metadata.get('user_agent', ''),
            device_fingerprint=metadata.get('device_fingerprint', ''),
            country=metadata.get('country', ''),
            city=metadata.get('city', ''),
            metadata=metadata or {}
        )
        
        with self._lock:
            # Adicionar aos buffers
            self._attempts_1m.append(attempt)
            self._attempts_5m.append(attempt)
            self._attempts_1h.append(attempt)
            
            # Atualizar trackers
            self._ip_attempts[ip].append(now)
            self._user_attempts[email].append(now)
            
            # Atualizar métricas
            self._total_attempts += 1
            if success:
                self._total_success += 1
                # Registrar dispositivo conhecido
                if attempt.device_fingerprint:
                    self._known_devices[email].add(attempt.device_fingerprint)
            else:
                self._total_failed += 1
            
            # Limpar entradas antigas dos trackers
            self._cleanup_old_entries(now)
        
        # Verificar se deve bloquear
        should_block, reason = self._should_block(attempt)
        
        if should_block:
            self._block_ip(ip, reason)
            logger.warning(f"🚫 IP bloqueado: {ip} - {reason}")
            return False
        
        # Verificar se é novo dispositivo
        if success and attempt.device_fingerprint:
            is_new = self._is_new_device(email, attempt.device_fingerprint)
            if is_new:
                logger.info(f"📱 Novo dispositivo detectado: {email} from {ip}")
                self.sil.alerts.send_alert(
                    level="info",
                    title="Novo Dispositivo",
                    message=f"Login de novo dispositivo: {email}",
                    data={'email': email, 'ip': ip, 'device': attempt.device_fingerprint}
                )
        
        return True
    
    def _should_block(self, attempt: LoginAttempt) -> Tuple[bool, str]:
        """Determina se tentativa deve ser bloqueada"""
        ip = attempt.ip_address
        email = attempt.email
        now = datetime.utcnow()
        
        with self._lock:
            # 1. Verificar se IP já está bloqueado
            if ip in self._blocked_ips:
                blocked_until = self._blocked_ips[ip]
                if now < blocked_until:
                    remaining = (blocked_until - now).seconds
                    return True, f"IP bloqueado por {remaining}s"
                else:
                    del self._blocked_ips[ip]
            
            # 2. Verificar tentativas por IP (1 minuto)
            ip_recent = [t for t in self._ip_attempts[ip] 
                        if now - t < timedelta(minutes=1)]
            if len(ip_recent) > 10:  # Mais de 10 tentativas em 1 min
                return True, "Rate limit excedido (10/min)"
            
            # 3. Verificar tentativas falhas por usuário
            user_recent = [t for t in self._user_attempts[email]
                          if now - t < timedelta(minutes=5)]
            if len(user_recent) > 5:  # Mais de 5 tentativas em 5 min
                return True, "Muitas tentativas para este usuário"
            
            # 4. Verificar padrão distribuído (ataque coordenado)
            if self._detect_distributed_attack(email, ip):
                return True, "Possível ataque distribuído detectado"
            
            # 5. Verificar IP suspeito
            if ip in self._suspicious_ips:
                return True, "IP em lista de suspeitos"
        
        return False, ""
    
    def _detect_distributed_attack(self, email: str, ip: str) -> bool:
        """Detecta tentativas distribuídas de vários IPs contra mesmo usuário"""
        # Verificar se múltiplos IPs diferentes tentaram mesmo usuário
        with self._lock:
            user_history = list(self._attempts_5m)
            
            # Filtrar tentativas para este email
            user_attempts = [a for a in user_history if a.email == email]
            
            # Contar IPs únicos
            unique_ips = set(a.ip_address for a in user_attempts)
            
            # Se mais de 5 IPs diferentes em 5 minutos = suspeito
            if len(unique_ips) > 5:
                logger.critical(f"🚨 Ataque distribuído detectado: {email} - {len(unique_ips)} IPs")
                return True
        
        return False
    
    def _block_ip(self, ip: str, reason: str, duration: int = 3600):
        """Bloqueia um IP"""
        with self._lock:
            blocked_until = datetime.utcnow() + timedelta(seconds=duration)
            self._blocked_ips[ip] = blocked_until
            
            # Alertar
            self.sil.alerts.send_alert(
                level="warning",
                title="IP Bloqueado",
                message=f"IP {ip} bloqueado: {reason}",
                data={'ip': ip, 'reason': reason, 'duration': duration}
            )
    
    def _is_new_device(self, email: str, device_fingerprint: str) -> bool:
        """Verifica se é um novo dispositivo para o usuário"""
        with self._lock:
            known = self._known_devices.get(email, set())
            return device_fingerprint not in known
    
    def _cleanup_old_entries(self, now: datetime):
        """Remove entradas antigas dos trackers"""
        cutoff_1h = now - timedelta(hours=1)
        
        # Limpar IPs
        for ip in list(self._ip_attempts.keys()):
            self._ip_attempts[ip] = [t for t in self._ip_attempts[ip] if t > cutoff_1h]
            if not self._ip_attempts[ip]:
                del self._ip_attempts[ip]
        
        # Limpar usuários
        for user in list(self._user_attempts.keys()):
            self._user_attempts[user] = [t for t in self._user_attempts[user] if t > cutoff_1h]
            if not self._user_attempts[user]:
                del self._user_attempts[user]
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Coleta métricas atuais"""
        with self._lock:
            now = datetime.utcnow()
            
            # Contar tentativas recentes
            attempts_1m = len([a for a in self._attempts_1m 
                              if now - a.timestamp < timedelta(minutes=1)])
            failed_1m = len([a for a in self._attempts_1m 
                           if not a.success and now - a.timestamp < timedelta(minutes=1)])
            
            return {
                'attempts_1m': attempts_1m,
                'attempts_5m': len(self._attempts_5m),
                'attempts_1h': len(self._attempts_1h),
                'failed_1m': failed_1m,
                'blocked_ips': len(self._blocked_ips),
                'suspicious_ips': len(self._suspicious_ips),
                'total_attempts': self._total_attempts,
                'total_success': self._total_success,
                'total_failed': self._total_failed,
                'success_rate': self._total_success / max(self._total_attempts, 1),
                'unique_users_1h': len(set(a.email for a in self._attempts_1h)),
                'unique_ips_1h': len(set(a.ip_address for a in self._attempts_1h))
            }
    
    def get_blocked_ips(self) -> List[Dict]:
        """Retorna lista de IPs bloqueados"""
        with self._lock:
            now = datetime.utcnow()
            return [
                {
                    'ip': ip,
                    'blocked_until': until.isoformat(),
                    'remaining_seconds': max(0, (until - now).seconds)
                }
                for ip, until in self._blocked_ips.items()
            ]
    
    def unblock_ip(self, ip: str) -> bool:
        """Desbloqueia um IP manualmente"""
        with self._lock:
            if ip in self._blocked_ips:
                del self._blocked_ips[ip]
                logger.info(f"✅ IP desbloqueado: {ip}")
                return True
        return False
    
    def emergency_rate_limit(self):
        """Ativa rate limit de emergência (modo crítico)"""
        logger.critical("🔒 Rate limit de emergência ativado")
        
        # Reduzir limites drasticamente
        with self._lock:
            # Bloquear todos os IPs com mais de 2 tentativas falhas recentes
            now = datetime.utcnow()
            for ip, attempts in self._ip_attempts.items():
                recent_failures = len([t for t in attempts 
                                      if now - t < timedelta(minutes=5)])
                if recent_failures >= 2:
                    self._block_ip(ip, "Emergência - múltiplas falhas", duration=7200)
    
    def get_login_patterns(self, email: str, hours: int = 24) -> Dict:
        """Analisa padrões de login de um usuário"""
        with self._lock:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            
            user_attempts = [a for a in self._attempts_1h 
                           if a.email == email and a.timestamp > cutoff]
            
            if not user_attempts:
                return {'status': 'no_data'}
            
            # Análise de padrões
            ips = set(a.ip_address for a in user_attempts)
            devices = set(a.device_fingerprint for a in user_attempts if a.device_fingerprint)
            countries = set(a.country for a in user_attempts if a.country)
            
            success_count = sum(1 for a in user_attempts if a.success)
            failure_count = len(user_attempts) - success_count
            
            # Horários de pico
            hours_distribution = defaultdict(int)
            for a in user_attempts:
                hours_distribution[a.timestamp.hour] += 1
            
            return {
                'status': 'ok',
                'total_attempts': len(user_attempts),
                'success': success_count,
                'failures': failure_count,
                'unique_ips': len(ips),
                'unique_devices': len(devices),
                'unique_countries': len(countries),
                'peak_hours': dict(hours_distribution),
                'known_devices': list(self._known_devices.get(email, set()))
            }
    
    def analyze_geolocation_risk(self, email: str, current_ip: str, 
                                 current_country: str) -> float:
        """Analisa risco baseado em geolocalização"""
        with self._lock:
            # Obter países históricos do usuário
            user_attempts = [a for a in self._attempts_1h if a.email == email]
            known_countries = set(a.country for a in user_attempts if a.country)
            
            if not known_countries:
                return 0.0  # Primeiro login, sem baseline
            
            if current_country not in known_countries:
                # Login de novo país!
                logger.warning(f"🌍 Login de novo país: {email} from {current_country}")
                return 0.7  # Risco alto
            
            return 0.1  # Risco baixo (país conhecido)
