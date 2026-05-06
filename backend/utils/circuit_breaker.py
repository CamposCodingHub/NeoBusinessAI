"""
Circuit Breaker Pattern - Proteção contra falhas em cascata
"""

import time
from enum import Enum
from typing import Callable, Any, Optional
from functools import wraps

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if recovered

class CircuitBreaker:
    """
    Circuit Breaker para proteger contra falhas em APIs externas
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
        success_threshold: int = 2
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.success_threshold = success_threshold
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_error = None
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Executa função protegida pelo circuit breaker
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise CircuitBreakerOpen(
                    f"Circuit '{self.name}' is OPEN. Last error: {self.last_error}"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure(e)
            raise
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Executa função assíncrona protegida pelo circuit breaker
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise CircuitBreakerOpen(
                    f"Circuit '{self.name}' is OPEN. Last error: {self.last_error}"
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure(e)
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Verifica se deve tentar reset após timeout"""
        if self.last_failure_time is None:
            return True
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
    
    def _on_success(self):
        """Handler para sucesso"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
        else:
            self.failure_count = 0
    
    def _on_failure(self, error: Exception):
        """Handler para falha"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.last_error = str(error)
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    def get_state(self) -> Dict[str, Any]:
        """Retorna estado atual do circuit breaker"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "last_error": self.last_error
        }

class CircuitBreakerOpen(Exception):
    """Exceção quando circuit breaker está aberto"""
    pass

# Instâncias globais de circuit breakers
circuit_breakers = {
    "groq": CircuitBreaker("groq", failure_threshold=3, recovery_timeout=30),
    "twilio": CircuitBreaker("twilio", failure_threshold=5, recovery_timeout=60),
    "stripe": CircuitBreaker("stripe", failure_threshold=3, recovery_timeout=60),
}

def get_circuit_breaker(name: str) -> CircuitBreaker:
    """Obtém ou cria circuit breaker"""
    if name not in circuit_breakers:
        circuit_breakers[name] = CircuitBreaker(name)
    return circuit_breakers[name]

def with_circuit_breaker(name: str):
    """Decorator para usar circuit breaker em funções"""
    def decorator(func: Callable):
        breaker = get_circuit_breaker(name)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await breaker.call_async(func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        
        # Detect if function is async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
