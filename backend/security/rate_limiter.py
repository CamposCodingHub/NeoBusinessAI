"""
Rate Limiting Module
====================
Proteção contra DDoS, brute force e uso excessivo da API.
"""

import time
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from functools import wraps
import logging

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuração de rate limiting"""
    requests_per_minute: int = 60
    burst_size: int = 10  # Requests permitidos em burst
    block_duration_minutes: int = 15
    
    # Limites específicos por endpoint
    CHAT_LIMIT: int = 30  # Mensagens por minuto
    UPLOAD_LIMIT: int = 10  # Uploads por minuto
    LOGIN_LIMIT: int = 5  # Tentativas de login por minuto
    SEARCH_LIMIT: int = 60  # Buscas por minuto


class TokenBucket:
    """
    Implementação do algoritmo Token Bucket para rate limiting
    
    Permite bursts de tráfego enquanto controla a média
    """
    
    def __init__(self, capacity: int, fill_rate: float):
        """
        Args:
            capacity: Capacidade máxima do bucket (burst)
            fill_rate: Taxa de preenchimento (tokens por segundo)
        """
        self.capacity = capacity
        self.tokens = capacity
        self.fill_rate = fill_rate
        self.last_update = time.time()
        self.lock = None  # Para thread-safety (implementar se necessário)
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Tenta consumir tokens do bucket
        
        Returns:
            True se consumo permitido, False caso contrário
        """
        now = time.time()
        
        # Recarregar tokens baseado no tempo passado
        elapsed = now - self.last_update
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.fill_rate
        )
        self.last_update = now
        
        # Verificar se há tokens suficientes
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def get_remaining(self) -> int:
        """Retorna número de tokens disponíveis"""
        self._refill()
        return int(self.tokens)
    
    def get_reset_time(self) -> float:
        """Retorna segundos até ter 1 token disponível"""
        if self.tokens >= 1:
            return 0
        return (1 - self.tokens) / self.fill_rate
    
    def _refill(self):
        """Recarrega tokens baseado no tempo"""
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.fill_rate
        )
        self.last_update = now


class RateLimiter:
    """
    Gerenciador de rate limiting por usuário/IP
    """
    
    def __init__(self):
        # Buckets por identificador (user_id ou IP)
        self.buckets: Dict[str, TokenBucket] = {}
        # Track de IPs bloqueados
        self.blocked: Dict[str, float] = {}
        
        # Configurações padrão
        self.default_config = RateLimitConfig()
    
    def is_blocked(self, identifier: str) -> Tuple[bool, Optional[float]]:
        """
        Verifica se identificador está bloqueado
        
        Returns:
            Tuple (is_blocked, seconds_remaining)
        """
        if identifier not in self.blocked:
            return False, None
        
        block_time = self.blocked[identifier]
        elapsed = time.time() - block_time
        block_duration = self.default_config.block_duration_minutes * 60
        
        if elapsed > block_duration:
            # Desbloquear
            del self.blocked[identifier]
            return False, None
        
        remaining = block_duration - elapsed
        return True, remaining
    
    def block(self, identifier: str):
        """Bloqueia identificador"""
        self.blocked[identifier] = time.time()
        logger.warning(f"Rate limit exceeded - blocked: {identifier}")
    
    def get_bucket(self, identifier: str, config: Optional[RateLimitConfig] = None) -> TokenBucket:
        """Obtém ou cria bucket para identificador"""
        if identifier not in self.buckets:
            config = config or self.default_config
            # Taxa: requests_per_minute / 60 = tokens por segundo
            fill_rate = config.requests_per_minute / 60.0
            self.buckets[identifier] = TokenBucket(
                capacity=config.burst_size,
                fill_rate=fill_rate
            )
        
        return self.buckets[identifier]
    
    def check_rate_limit(
        self,
        identifier: str,
        config: Optional[RateLimitConfig] = None
    ) -> Tuple[bool, Dict]:
        """
        Verifica se requisição está dentro do rate limit
        
        Returns:
            Tuple (allowed, info_dict)
            info_dict contém: remaining, reset_time, limit
        """
        # Verificar bloqueio
        is_blocked, remaining_block = self.is_blocked(identifier)
        if is_blocked:
            return False, {
                "allowed": False,
                "blocked": True,
                "retry_after": int(remaining_block),
                "message": f"Bloqueado. Tente novamente em {int(remaining_block)}s"
            }
        
        # Obter bucket
        bucket = self.get_bucket(identifier, config)
        
        # Tentar consumir token
        if bucket.consume():
            remaining = bucket.get_remaining()
            reset_time = bucket.get_reset_time()
            
            return True, {
                "allowed": True,
                "remaining": remaining,
                "limit": config.requests_per_minute if config else self.default_config.requests_per_minute,
                "reset_after": int(reset_time)
            }
        else:
            # Bloquear por exceder limite
            self.block(identifier)
            block_duration = self.default_config.block_duration_minutes * 60
            
            return False, {
                "allowed": False,
                "blocked": True,
                "retry_after": block_duration,
                "message": f"Rate limit excedido. Bloqueado por {self.default_config.block_duration_minutes} minutos"
            }
    
    def cleanup_old_buckets(self, max_age_minutes: int = 60):
        """Limpa buckets antigos para liberar memória"""
        cutoff = time.time() - (max_age_minutes * 60)
        to_remove = [
            ident for ident, bucket in self.buckets.items()
            if bucket.last_update < cutoff
        ]
        for ident in to_remove:
            del self.buckets[ident]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old rate limit buckets")


# Instância global do rate limiter
_rate_limiter = RateLimiter()


def rate_limit(
    requests_per_minute: int = 60,
    burst_size: int = 10,
    block_duration: int = 15,
    identifier_func = None
):
    """
    Decorator para aplicar rate limiting em funções
    
    Usage:
        @rate_limit(requests_per_minute=30)
        async def chat_endpoint(request: Request):
            # ...
    
    Args:
        requests_per_minute: Limite de requisições por minuto
        burst_size: Tamanho do burst permitido
        block_duration: Duração do bloqueio em minutos
        identifier_func: Função para extrair identificador (user_id ou IP)
    """
    def decorator(func):
        config = RateLimitConfig(
            requests_per_minute=requests_per_minute,
            burst_size=burst_size,
            block_duration_minutes=block_duration
        )
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extrair identificador
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            else:
                # Tentar extrair de request
                request = kwargs.get('request') or (args[0] if args else None)
                if request:
                    # Tentar obter user_id do request state
                    identifier = getattr(request.state, 'user_id', None)
                    if not identifier:
                        # Fallback para IP
                        identifier = request.client.host if request.client else 'unknown'
                else:
                    identifier = 'unknown'
            
            # Verificar rate limit
            allowed, info = _rate_limiter.check_rate_limit(identifier, config)
            
            if not allowed:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429,  # Too Many Requests
                    detail=info.get('message', 'Rate limit excedido'),
                    headers={
                        'Retry-After': str(info.get('retry_after', 60)),
                        'X-RateLimit-Limit': str(config.requests_per_minute),
                        'X-RateLimit-Remaining': '0',
                    }
                )
            
            # Adicionar headers de rate limit na resposta
            response = await func(*args, **kwargs)
            
            # Se for Response object, adicionar headers
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
            
            return response
        
        return wrapper
    return decorator


def check_rate_limit(
    identifier: str,
    requests_per_minute: int = 60,
    burst_size: int = 10,
    max_requests: int = None,
    window_seconds: int = None
) -> Tuple[bool, Dict]:
    """
    Função standalone para verificar rate limit
    
    Suporta dois formatos de chamada:
    1. check_rate_limit(identifier, requests_per_minute=60, burst_size=10)
    2. check_rate_limit(identifier, max_requests=100, window_seconds=60)
    
    Usage:
        allowed, info = check_rate_limit(user_id, requests_per_minute=30)
        if not allowed:
            raise HTTPException(status_code=429, detail=info['message'])
    """
    # Compatibilidade: se max_requests/window_seconds fornecidos, converter
    if max_requests is not None and window_seconds is not None:
        # Converter window_seconds (em segundos) para requests_per_minute
        requests_per_minute = int(max_requests * 60 / window_seconds)
        # burst_size como 20% do max_requests, mínimo 5
        burst_size = max(5, int(max_requests * 0.2))
    
    config = RateLimitConfig(
        requests_per_minute=requests_per_minute,
        burst_size=burst_size
    )
    return _rate_limiter.check_rate_limit(identifier, config)


# Configurações específicas por tipo de endpoint
CHAT_RATE_LIMIT = RateLimitConfig(
    requests_per_minute=30,  # 30 mensagens por minuto
    burst_size=5,
    block_duration_minutes=5
)

UPLOAD_RATE_LIMIT = RateLimitConfig(
    requests_per_minute=10,  # 10 uploads por minuto
    burst_size=3,
    block_duration_minutes=10
)

LOGIN_RATE_LIMIT = RateLimitConfig(
    requests_per_minute=5,  # 5 tentativas por minuto
    burst_size=3,
    block_duration_minutes=30
)

SEARCH_RATE_LIMIT = RateLimitConfig(
    requests_per_minute=60,
    burst_size=10,
    block_duration_minutes=5
)

API_RATE_LIMIT = RateLimitConfig(
    requests_per_minute=120,
    burst_size=20,
    block_duration_minutes=15
)
