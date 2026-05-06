"""
Rate Limiting Service
======================
Implementação enterprise de rate limiting com Redis.
"""

from typing import Optional
import redis
import json
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from core.config import settings


class RateLimitService:
    """Serviço de rate limiting com Redis"""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """
        Verifica se request está dentro do rate limit.
        
        Args:
            key: Chave única (ex: "login:192.168.1.1")
            max_requests: Máximo de requests permitidos
            window_seconds: Janela de tempo em segundos
            
        Returns:
            True se permitido, False se excedido
        """
        try:
            # Pipeline para operações atômicas
            pipe = self.redis_client.pipeline()
            
            now = datetime.utcnow().timestamp()
            window_start = now - window_seconds
            
            # Remover entradas antigas
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Contar requests na janela
            pipe.zcard(key)
            
            # Adicionar request atual
            pipe.zadd(key, {str(now): now})
            
            # Definir expiração
            pipe.expire(key, window_seconds + 1)
            
            results = pipe.execute()
            current_count = results[1]
            
            return current_count < max_requests
            
        except Exception as e:
            # Se Redis falhar, permitir request (fail open)
            print(f"Rate limit error: {e}")
            return True
    
    async def get_rate_limit_info(
        self,
        key: str,
        window_seconds: int
    ) -> dict:
        """
        Obtém informações sobre rate limit atual.
        
        Returns:
            Dict com count, reset time, etc
        """
        try:
            now = datetime.utcnow().timestamp()
            window_start = now - window_seconds
            
            # Remover entradas antigas
            self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Contar requests
            count = self.redis_client.zcard(key)
            
            # Obter TTL
            ttl = self.redis_client.ttl(key)
            
            return {
                "count": count,
                "reset": int(ttl) if ttl > 0 else 0,
                "limit": count  # TODO: Obter limit do config
            }
            
        except Exception as e:
            return {"count": 0, "reset": 0, "limit": 0}
    
    async def check_login_rate_limit(self, ip_address: str) -> bool:
        """
        Verifica rate limit para login (anti-brute force).
        
        Args:
            ip_address: IP do request
            
        Returns:
            True se permitido, False se bloqueado
        """
        key = f"login:{ip_address}"
        return await self.check_rate_limit(
            key,
            settings.RATE_LIMIT_LOGIN_ATTEMPTS,
            settings.RATE_LIMIT_LOGIN_WINDOW
        )
    
    async def check_api_rate_limit(self, tenant_id: str) -> bool:
        """
        Verifica rate limit para API por tenant.
        
        Args:
            tenant_id: ID do tenant
            
        Returns:
            True se permitido, False se excedido
        """
        key = f"api:{tenant_id}"
        return await self.check_rate_limit(
            key,
            settings.RATE_LIMIT_API_REQUESTS,
            settings.RATE_LIMIT_API_WINDOW
        )
    
    async def check_ai_rate_limit(self, user_id: str) -> bool:
        """
        Verifica rate limit para AI por usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            True se permitido, False se excedido
        """
        key = f"ai:{user_id}"
        return await self.check_rate_limit(
            key,
            settings.RATE_LIMIT_AI_REQUESTS,
            settings.RATE_LIMIT_AI_WINDOW
        )
    
    async def block_ip(self, ip_address: str, duration_seconds: int = 3600):
        """
        Bloqueia IP por período específico.
        
        Args:
            ip_address: IP a bloquear
            duration_seconds: Duração do bloqueio
        """
        key = f"blocked:{ip_address}"
        self.redis_client.setex(key, duration_seconds, "1")
    
    async def is_ip_blocked(self, ip_address: str) -> bool:
        """
        Verifica se IP está bloqueado.
        
        Args:
            ip_address: IP a verificar
            
        Returns:
            True se bloqueado
        """
        key = f"blocked:{ip_address}"
        return self.redis_client.exists(key) > 0


# Singleton instance
rate_limit_service = RateLimitService()


async def check_rate_limit_or_raise(
    key: str,
    max_requests: int,
    window_seconds: int,
    error_message: str = "Rate limit exceeded"
):
    """
    Verifica rate limit e lança exception se excedido.
    
    Args:
        key: Chave única
        max_requests: Máximo de requests
        window_seconds: Janela de tempo
        error_message: Mensagem de erro
        
    Raises:
        HTTPException: Se rate limit excedido
    """
    allowed = await rate_limit_service.check_rate_limit(key, max_requests, window_seconds)
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_message
        )
