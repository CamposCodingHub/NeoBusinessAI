"""
Security Intelligence Layer - Security Auto-Tester
=================================================
Auto-testes periódicos de segurança simulando ataques reais.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import requests
import json

logger = logging.getLogger(__name__)


class TestType(Enum):
    LOGIN_VALID = "login_valid"
    LOGIN_INVALID = "login_invalid"
    BRUTE_FORCE_SIM = "brute_force_simulation"
    SQL_INJECTION = "sql_injection"
    XSS_INPUT = "xss_input"
    ROUTE_BYPASS = "route_bypass"
    SESSION_HIJACK = "session_hijack"
    RATE_LIMIT = "rate_limit"
    MULTI_USER = "multi_user_simulation"


class TestResult(Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class SecurityTest:
    """Representa um teste de segurança"""
    type: TestType
    name: str
    description: str
    payload: Dict[str, Any]
    expected_result: str
    actual_result: Optional[str] = None
    result: TestResult = TestResult.ERROR
    execution_time_ms: float = 0.0
    timestamp: datetime = None
    details: Dict[str, Any] = None


class SecurityAutoTester:
    """
    Testador automático de segurança
    """
    
    def __init__(self, sil):
        self.sil = sil
        self.api_url = "http://localhost:8000"  # URL do backend
        
        logger.info("🧪 Security Auto-Tester inicializado")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Executa toda a bateria de testes"""
        logger.info("🚀 Iniciando bateria completa de auto-testes")
        
        tests = [
            self._test_login_valid,
            self._test_login_invalid,
            self._test_brute_force_protection,
            self._test_sql_injection,
            self._test_xss_protection,
            self._test_route_protection,
            self._test_rate_limiting,
            self._test_multi_user_isolation,
        ]
        
        results = []
        passed = 0
        failed = 0
        
        for test_func in tests:
            try:
                test = test_func()
                results.append(test)
                
                if test.result == TestResult.PASSED:
                    passed += 1
                    logger.info(f"✅ {test.name}: PASSOU")
                else:
                    failed += 1
                    logger.warning(f"❌ {test.name}: FALHOU - {test.actual_result}")
                
            except Exception as e:
                logger.error(f"💥 Erro em {test_func.__name__}: {e}")
                failed += 1
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total': len(results),
            'passed': passed,
            'failed': failed,
            'success_rate': passed / max(len(results), 1),
            'tests': results,
            'failures': [t for t in results if t.result != TestResult.PASSED]
        }
    
    def _test_login_valid(self) -> SecurityTest:
        """Testa login com credenciais válidas"""
        test = SecurityTest(
            type=TestType.LOGIN_VALID,
            name="Login Válido",
            description="Simula login com credenciais corretas",
            payload={'email': 'test@example.com', 'password': 'test123'},
            expected_result="Login bem-sucedido com tokens"
        )
        
        try:
            # Simular requisição de login
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={'email': 'admin@neobusiness.ai', 'password': 'Admin123!'},
                timeout=5
            )
            
            test.execution_time_ms = response.elapsed.total_seconds() * 1000
            test.timestamp = datetime.utcnow()
            
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data and 'user' in data:
                    test.actual_result = "Login bem-sucedido"
                    test.result = TestResult.PASSED
                    test.details = {'user_id': data.get('user', {}).get('id')}
                else:
                    test.actual_result = "Resposta incompleta"
                    test.result = TestResult.FAILED
            else:
                test.actual_result = f"Status: {response.status_code}"
                test.result = TestResult.FAILED
                
        except Exception as e:
            test.actual_result = f"Erro: {str(e)}"
            test.result = TestResult.ERROR
        
        return test
    
    def _test_login_invalid(self) -> SecurityTest:
        """Testa login com credenciais inválidas"""
        test = SecurityTest(
            type=TestType.LOGIN_INVALID,
            name="Login Inválido",
            description="Tenta login com senha errada",
            payload={'email': 'test@example.com', 'password': 'wrongpassword'},
            expected_result="Acesso negado com mensagem genérica"
        )
        
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={'email': 'test@example.com', 'password': 'wrongpassword'},
                timeout=5
            )
            
            test.execution_time_ms = response.elapsed.total_seconds() * 1000
            test.timestamp = datetime.utcnow()
            
            # Deve retornar 401
            if response.status_code == 401:
                data = response.json()
                # Mensagem deve ser genérica (não revelar se email existe)
                if 'incorretos' in data.get('detail', '').lower() or 'invalid' in data.get('detail', '').lower():
                    test.actual_result = "Acesso negado corretamente"
                    test.result = TestResult.PASSED
                else:
                    test.actual_result = "Mensagem pode revelar informação"
                    test.result = TestResult.WARNING
            else:
                test.actual_result = f"Status inesperado: {response.status_code}"
                test.result = TestResult.FAILED
                
        except Exception as e:
            test.actual_result = f"Erro: {str(e)}"
            test.result = TestResult.ERROR
        
        return test
    
    def _test_brute_force_protection(self) -> SecurityTest:
        """Testa proteção contra brute force"""
        test = SecurityTest(
            type=TestType.BRUTE_FORCE_SIM,
            name="Proteção Brute Force",
            description="Tenta múltiplos logins rápidos",
            payload={'attempts': 10, 'email': 'test@example.com'},
            expected_result="Rate limit ativado após várias tentativas"
        )
        
        try:
            blocked_count = 0
            
            # Fazer 10 tentativas rápidas
            for i in range(10):
                response = requests.post(
                    f"{self.api_url}/auth/login",
                    json={'email': f'test{i}@example.com', 'password': 'wrong'},
                    timeout=5
                )
                
                if response.status_code == 429:  # Too Many Requests
                    blocked_count += 1
            
            test.timestamp = datetime.utcnow()
            
            if blocked_count > 0:
                test.actual_result = f"Rate limit ativado ({blocked_count}/10)"
                test.result = TestResult.PASSED
                test.details = {'blocked_attempts': blocked_count}
            else:
                test.actual_result = "Nenhuma proteção detectada"
                test.result = TestResult.FAILED
                
        except Exception as e:
            test.actual_result = f"Erro: {str(e)}"
            test.result = TestResult.ERROR
        
        return test
    
    def _test_sql_injection(self) -> SecurityTest:
        """Testa proteção contra SQL injection"""
        test = SecurityTest(
            type=TestType.SQL_INJECTION,
            name="Proteção SQL Injection",
            description="Tenta SQL injection no campo de login",
            payload={'email': "' OR 1=1 --", 'password': 'anything'},
            expected_result="Input sanitizado, nenhuma vulnerabilidade"
        )
        
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={'email': "' OR 1=1 --", 'password': 'anything'},
                timeout=5
            )
            
            test.execution_time_ms = response.elapsed.total_seconds() * 1000
            test.timestamp = datetime.utcnow()
            
            # Não deve retornar 200 (login bem-sucedido)
            if response.status_code in [401, 400, 422]:
                test.actual_result = "SQL injection bloqueado"
                test.result = TestResult.PASSED
            elif response.status_code == 200:
                test.actual_result = "🚨 POSSÍVEL VULNERABILIDADE SQL INJECTION"
                test.result = TestResult.FAILED
            else:
                test.actual_result = f"Status: {response.status_code}"
                test.result = TestResult.WARNING
                
        except Exception as e:
            test.actual_result = f"Erro: {str(e)}"
            test.result = TestResult.ERROR
        
        return test
    
    def _test_xss_protection(self) -> SecurityTest:
        """Testa proteção contra XSS"""
        test = SecurityTest(
            type=TestType.XSS_INPUT,
            name="Proteção XSS",
            description="Tenta injetar script no campo de login",
            payload={'email': '<script>alert("xss")</script>', 'password': 'test'},
            expected_result="Script sanitizado ou bloqueado"
        )
        
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={'email': '<script>alert("xss")</script>', 'password': 'test'},
                timeout=5
            )
            
            test.timestamp = datetime.utcnow()
            
            # Verificar se script aparece na resposta
            response_text = response.text.lower()
            if '<script>' in response_text or 'alert(' in response_text:
                test.actual_result = "🚨 XSS NÃO PROTEGIDO - Script refletido"
                test.result = TestResult.FAILED
            else:
                test.actual_result = "XSS protegido"
                test.result = TestResult.PASSED
                
        except Exception as e:
            test.actual_result = f"Erro: {str(e)}"
            test.result = TestResult.ERROR
        
        return test
    
    def _test_route_protection(self) -> SecurityTest:
        """Testa proteção de rotas privadas"""
        test = SecurityTest(
            type=TestType.ROUTE_BYPASS,
            name="Proteção de Rotas",
            description="Tenta acessar dashboard sem autenticação",
            payload={'route': '/dashboard'},
            expected_result="Redirecionado para login ou 401"
        )
        
        try:
            response = requests.get(
                f"{self.api_url}/dashboard",
                timeout=5
            )
            
            test.timestamp = datetime.utcnow()
            
            # Deve retornar 401 ou redirecionar
            if response.status_code in [401, 403, 302, 307]:
                test.actual_result = "Rota protegida corretamente"
                test.result = TestResult.PASSED
            elif response.status_code == 200:
                test.actual_result = "🚨 ROTA NÃO PROTEGIDA - Acesso sem auth"
                test.result = TestResult.FAILED
            else:
                test.actual_result = f"Status: {response.status_code}"
                test.result = TestResult.WARNING
                
        except Exception as e:
            test.actual_result = f"Erro: {str(e)}"
            test.result = TestResult.ERROR
        
        return test
    
    def _test_rate_limiting(self) -> SecurityTest:
        """Testa rate limiting em endpoints"""
        test = SecurityTest(
            type=TestType.RATE_LIMIT,
            name="Rate Limiting",
            description="Testa limitação de requisições",
            payload={'requests': 20, 'endpoint': '/auth/login'},
            expected_result="Rate limit ativado após limite"
        )
        
        try:
            limited_count = 0
            
            # Fazer 20 requisições rápidas
            for i in range(20):
                response = requests.post(
                    f"{self.api_url}/auth/login",
                    json={'email': 'test@test.com', 'password': 'test'},
                    timeout=5
                )
                
                if response.status_code == 429:
                    limited_count += 1
            
            test.timestamp = datetime.utcnow()
            
            if limited_count > 0:
                test.actual_result = f"Rate limit funcionando ({limited_count}/20)"
                test.result = TestResult.PASSED
            else:
                test.actual_result = "Nenhum rate limiting detectado"
                test.result = TestResult.FAILED
                
        except Exception as e:
            test.actual_result = f"Erro: {str(e)}"
            test.result = TestResult.ERROR
        
        return test
    
    def _test_multi_user_isolation(self) -> SecurityTest:
        """Testa isolamento entre usuários"""
        test = SecurityTest(
            type=TestType.MULTI_USER,
            name="Isolamento Multi-Usuário",
            description="Verifica se usuários não acessam dados de outros",
            payload={'user1': 'user1@test.com', 'user2': 'user2@test.com'},
            expected_result="Dados isolados, sem vazamento"
        )
        
        # Este teste requer usuários reais criados
        # Simplificado para verificação básica
        
        test.timestamp = datetime.utcnow()
        test.actual_result = "Teste requer setup de múltiplos usuários"
        test.result = TestResult.WARNING
        
        return test
    
    def run_stress_test(self, duration_seconds: int = 60) -> Dict:
        """Executa teste de stress"""
        logger.info(f"🔥 Iniciando stress test por {duration_seconds}s")
        
        start_time = datetime.utcnow()
        requests_count = 0
        errors = 0
        
        # Simular carga
        while (datetime.utcnow() - start_time).seconds < duration_seconds:
            try:
                requests.post(
                    f"{self.api_url}/auth/login",
                    json={'email': 'stress@test.com', 'password': 'test'},
                    timeout=2
                )
                requests_count += 1
            except:
                errors += 1
        
        return {
            'duration': duration_seconds,
            'total_requests': requests_count,
            'errors': errors,
            'rps': requests_count / duration_seconds,
            'error_rate': errors / max(requests_count, 1)
        }
