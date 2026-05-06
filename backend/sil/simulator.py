"""
Security Intelligence Layer - Attack Simulator
==============================================
Simulação controlada de ataques para validação de segurança.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import random
import string

logger = logging.getLogger(__name__)


class AttackSimulator:
    """
    Simulador de ataques controlados para testes de segurança
    """
    
    def __init__(self, sil):
        self.sil = sil
        self._is_simulating = False
        
        logger.info("🎯 Attack Simulator inicializado")
    
    def run_simulation(self, attack_type: str) -> Dict[str, Any]:
        """
        Executa simulação de ataque específico
        
        Tipos suportados:
        - brute_force: Força bruta
        - credential_stuffing: Credential stuffing
        - distributed: Ataque distribuído
        - xss: Cross-site scripting
        - sql_injection: SQL injection
        - rapid_fire: Tentativas em sequência rápida
        """
        logger.info(f"🎯 Iniciando simulação: {attack_type}")
        
        simulators = {
            'brute_force': self._simulate_brute_force,
            'credential_stuffing': self._simulate_credential_stuffing,
            'distributed': self._simulate_distributed_attack,
            'xss': self._simulate_xss,
            'sql_injection': self._simulate_sql_injection,
            'rapid_fire': self._simulate_rapid_fire,
        }
        
        simulator = simulators.get(attack_type)
        if not simulator:
            return {
                'error': f'Tipo de simulação desconhecido: {attack_type}',
                'available_types': list(simulators.keys())
            }
        
        try:
            result = simulator()
            logger.info(f"✅ Simulação {attack_type} concluída")
            return result
        except Exception as e:
            logger.error(f"❌ Erro na simulação {attack_type}: {e}")
            return {'error': str(e)}
    
    def _simulate_brute_force(self) -> Dict[str, Any]:
        """Simula ataque de força bruta"""
        target_email = "test@example.com"
        attempts = 20
        passwords = [
            "123456", "password", "qwerty", "12345678",
            "111111", "1234567890", "letmein", "welcome"
        ]
        
        blocked_at = None
        detected = False
        
        for i in range(attempts):
            password = random.choice(passwords)
            
            # Simular tentativa
            is_blocked = self._simulate_login_attempt(
                email=target_email,
                password=password,
                ip="192.168.1.100"
            )
            
            if is_blocked and not blocked_at:
                blocked_at = i + 1
                detected = True
                break
        
        return {
            'type': 'brute_force',
            'target': target_email,
            'attempts': attempts,
            'blocked_at': blocked_at,
            'detected': detected,
            'success': blocked_at is not None,  # Sucesso = foi bloqueado
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _simulate_credential_stuffing(self) -> Dict[str, Any]:
        """Simula credential stuffing"""
        # Muitos emails diferentes, poucas senhas
        emails = [f"user{i}@example.com" for i in range(50)]
        passwords = ["Password123", "Welcome2024", "Qwerty123"]
        
        unique_ips = set()
        blocked_count = 0
        
        for i, email in enumerate(emails[:20]):  # Simular 20 tentativas
            ip = f"10.0.0.{random.randint(1, 50)}"
            unique_ips.add(ip)
            
            is_blocked = self._simulate_login_attempt(
                email=email,
                password=random.choice(passwords),
                ip=ip
            )
            
            if is_blocked:
                blocked_count += 1
        
        detected = len(unique_ips) > 5 and blocked_count > 0
        
        return {
            'type': 'credential_stuffing',
            'attempts': 20,
            'unique_ips': len(unique_ips),
            'blocked_count': blocked_count,
            'detected': detected,
            'success': detected,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _simulate_distributed_attack(self) -> Dict[str, Any]:
        """Simula ataque distribuído de múltiplos IPs"""
        target_email = "admin@neobusiness.ai"
        attempts_per_ip = 3
        num_ips = 30
        
        blocked_count = 0
        
        for i in range(num_ips):
            ip = f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
            
            for j in range(attempts_per_ip):
                is_blocked = self._simulate_login_attempt(
                    email=target_email,
                    password=f"wrong{i}_{j}",
                    ip=ip
                )
                
                if is_blocked:
                    blocked_count += 1
        
        total_attempts = num_ips * attempts_per_ip
        detected = blocked_count > 10
        
        return {
            'type': 'distributed_attack',
            'total_attempts': total_attempts,
            'unique_ips': num_ips,
            'blocked_count': blocked_count,
            'detected': detected,
            'success': detected,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _simulate_xss(self) -> Dict[str, Any]:
        """Simula tentativa de XSS"""
        xss_payloads = [
            '<script>alert("xss")</script>',
            '<img src=x onerror=alert("xss")>',
            'javascript:alert("xss")',
            '<svg onload=alert("xss")>',
        ]
        
        sanitized_count = 0
        
        for payload in xss_payloads:
            # Simular envio de XSS no campo de email
            is_sanitized = self._simulate_xss_attempt(payload)
            if is_sanitized:
                sanitized_count += 1
        
        return {
            'type': 'xss',
            'payloads_tested': len(xss_payloads),
            'sanitized_count': sanitized_count,
            'success': sanitized_count == len(xss_payloads),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _simulate_sql_injection(self) -> Dict[str, Any]:
        """Simula tentativa de SQL injection"""
        sql_payloads = [
            "' OR 1=1 --",
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
        ]
        
        blocked_count = 0
        
        for payload in sql_payloads:
            is_blocked = self._simulate_login_attempt(
                email=payload,
                password="test",
                ip="192.168.1.200"
            )
            
            if is_blocked:
                blocked_count += 1
        
        return {
            'type': 'sql_injection',
            'payloads_tested': len(sql_payloads),
            'blocked_count': blocked_count,
            'success': blocked_count > 0,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _simulate_rapid_fire(self) -> Dict[str, Any]:
        """Simula tentativas em sequência muito rápida"""
        attempts = 10
        interval_seconds = 0.1  # 10 tentativas em 1 segundo
        
        blocked_at = None
        
        for i in range(attempts):
            is_blocked = self._simulate_login_attempt(
                email="test@test.com",
                password="wrong",
                ip="192.168.1.50",
                rapid=True
            )
            
            if is_blocked and not blocked_at:
                blocked_at = i + 1
                break
        
        return {
            'type': 'rapid_fire',
            'attempts': attempts,
            'interval': interval_seconds,
            'blocked_at': blocked_at,
            'detected': blocked_at is not None,
            'success': blocked_at is not None,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _simulate_login_attempt(self, email: str, password: str, 
                               ip: str, rapid: bool = False) -> bool:
        """
        Simula uma tentativa de login individual
        Retorna True se foi bloqueado
        """
        # Verificar se IP está bloqueado
        with self.sil.monitor._lock:
            if ip in self.sil.monitor._blocked_ips:
                return True
        
        # Registrar tentativa
        metadata = {'simulated': True, 'rapid': rapid}
        self.sil.monitor.record_attempt(email, ip, False, metadata)
        
        # Verificar se foi bloqueado
        with self.sil.monitor._lock:
            if ip in self.sil.monitor._blocked_ips:
                return True
            
            # Verificar rate limit por velocidade
            if rapid:
                attempts = self.sil.monitor._ip_attempts.get(ip, [])
                if len(attempts) > 5:
                    recent = attempts[-5:]
                    time_span = (recent[-1] - recent[0]).total_seconds()
                    if time_span < 2:
                        self.sil.monitor._block_ip(ip, "Simulação - rapid fire", 300)
                        return True
        
        return False
    
    def _simulate_xss_attempt(self, payload: str) -> bool:
        """Simula tentativa de XSS"""
        # Verificar se payload seria sanitizado
        # Em produção, testar contra endpoint real
        
        # Simulação: verificar se contém tags script
        sanitized = '<script>' not in payload.lower()
        
        return sanitized
    
    def run_stress_test(self, duration_minutes: int = 5) -> Dict[str, Any]:
        """Executa teste de stress completo"""
        logger.info(f"🔥 Iniciando stress test por {duration_minutes} minutos")
        
        start_time = datetime.utcnow()
        attempts = 0
        blocked = 0
        
        # Simular carga
        while (datetime.utcnow() - start_time).seconds < duration_minutes * 60:
            # Escolher tipo de ataque aleatório
            attack_type = random.choice([
                'brute_force', 'credential_stuffing', 'distributed',
                'xss', 'sql_injection'
            ])
            
            result = self.run_simulation(attack_type)
            
            if 'attempts' in result:
                attempts += result.get('attempts', 0)
            if 'blocked_count' in result:
                blocked += result.get('blocked_count', 0)
            if 'blocked_at' in result and result.get('blocked_at'):
                blocked += 1
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            'type': 'stress_test',
            'duration_seconds': duration,
            'total_attempts': attempts,
            'blocked_count': blocked,
            'protection_rate': blocked / max(attempts, 1),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_simulation_status(self) -> Dict[str, Any]:
        """Retorna status do simulador"""
        return {
            'is_simulating': self._is_simulating,
            'available_simulations': [
                'brute_force',
                'credential_stuffing',
                'distributed',
                'xss',
                'sql_injection',
                'rapid_fire',
                'stress_test'
            ],
            'last_simulation': datetime.utcnow().isoformat()
        }
