"""
Blacklist de Tokens JWT - Invalidação em Logout
Usa Redis para armazenar tokens revogados
"""

import redis
import os
from datetime import datetime
from typing import Optional

# Configuração Redis
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

class TokenBlacklist:
    """Gerencia blacklist de tokens JWT"""
    
    def __init__(self):
        try:
            self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            self.is_available = True
        except Exception as e:
            print(f"[TokenBlacklist] Redis não disponível: {e}")
            self.redis_client = None
            self.is_available = False
    
    def add_to_blacklist(self, token: str, expires_in: int = 3600) -> bool:
        """
        Adiciona token à blacklist
        expires_in: tempo em segundos até expiração natural do token
        """
        if not self.is_available or not self.redis_client:
            # Fallback: não conseguimos invalidar o token
            print(f"[TokenBlacklist] AVISO: Token não adicionado à blacklist (Redis indisponível)")
            return False
        
        try:
            # Usar JWT ID ou hash do token como chave
            key = f"blacklist:token:{token}"
            self.redis_client.setex(key, expires_in, "revoked")
            print(f"[TokenBlacklist] Token adicionado à blacklist (expira em {expires_in}s)")
            return True
        except Exception as e:
            print(f"[TokenBlacklist] Erro ao adicionar token: {e}")
            return False
    
    def is_blacklisted(self, token: str) -> bool:
        """Verifica se token está na blacklist"""
        if not self.is_available or not self.redis_client:
            # Se Redis não disponível, assumir que token é válido
            return False
        
        try:
            key = f"blacklist:token:{token}"
            return self.redis_client.exists(key) > 0
        except Exception as e:
            print(f"[TokenBlacklist] Erro ao verificar token: {e}")
            return False
    
    def add_refresh_token(self, refresh_token: str, user_id: int, expires_in: int = 604800) -> bool:
        """
        Armazena refresh token válido
        expires_in: 7 dias padrão (604800 segundos)
        """
        if not self.is_available or not self.redis_client:
            return False
        
        try:
            key = f"refresh_token:{user_id}:{refresh_token}"
            self.redis_client.setex(key, expires_in, "valid")
            return True
        except Exception as e:
            print(f"[TokenBlacklist] Erro ao armazenar refresh token: {e}")
            return False
    
    def is_refresh_token_valid(self, refresh_token: str, user_id: int) -> bool:
        """Verifica se refresh token é válido"""
        if not self.is_available or not self.redis_client:
            # Se Redis não disponível, aceitar o token (degradado)
            return True
        
        try:
            key = f"refresh_token:{user_id}:{refresh_token}"
            return self.redis_client.exists(key) > 0
        except Exception as e:
            print(f"[TokenBlacklist] Erro ao verificar refresh token: {e}")
            return True  # Degradado: aceitar em caso de falha
    
    def revoke_refresh_token(self, refresh_token: str, user_id: int) -> bool:
        """Revoga um refresh token específico"""
        if not self.is_available or not self.redis_client:
            return False
        
        try:
            key = f"refresh_token:{user_id}:{refresh_token}"
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"[TokenBlacklist] Erro ao revogar refresh token: {e}")
            return False
    
    def revoke_all_user_tokens(self, user_id: int) -> bool:
        """Revoga todos os tokens de um usuário (logout de todos dispositivos)"""
        if not self.is_available or not self.redis_client:
            return False
        
        try:
            # Buscar todos os refresh tokens do usuário
            pattern = f"refresh_token:{user_id}:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            return True
        except Exception as e:
            print(f"[TokenBlacklist] Erro ao revogar tokens do usuário: {e}")
            return False

# Instância global
token_blacklist = TokenBlacklist()

# Funções de conveniência
def blacklist_token(token: str, expires_in: int = 3600) -> bool:
    """Adiciona token à blacklist"""
    return token_blacklist.add_to_blacklist(token, expires_in)

def is_token_blacklisted(token: str) -> bool:
    """Verifica se token está na blacklist"""
    return token_blacklist.is_blacklisted(token)
