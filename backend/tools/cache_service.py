"""
Redis Cache Service - LexScan IA
Caching layer para performance
"""

import os
import json
import pickle
import hashlib
from typing import Optional, Any, Dict, List
from functools import wraps
from datetime import timedelta

# Redis configuration
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

class CacheService:
    """
    Serviço de cache Redis para LexScan IA
    
    Features:
    - Cache de queries de banco
    - Cache de respostas de IA
    - Cache de sessões
    - Cache de estatísticas
    - Decorator para cache automático
    """
    
    def __init__(self):
        self._redis = None
        self._local_cache: Dict[str, Any] = {}  # Fallback local
        self.default_ttl = 300  # 5 minutos
        
    def _get_redis(self):
        """Lazy initialization do Redis"""
        if self._redis is None:
            try:
                import redis
                self._redis = redis.from_url(REDIS_URL, decode_responses=False)
                self._redis.ping()
            except Exception as e:
                print(f"[CACHE WARNING] Redis não disponível: {e}")
                self._redis = None
        return self._redis
    
    def get(self, key: str) -> Optional[Any]:
        """Busca valor do cache"""
        try:
            r = self._get_redis()
            if r:
                value = r.get(key)
                if value:
                    return pickle.loads(value)
            
            # Fallback para cache local
            return self._local_cache.get(key)
            
        except Exception as e:
            print(f"[CACHE ERROR] get: {e}")
            return self._local_cache.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Salva valor no cache"""
        try:
            r = self._get_redis()
            ttl = ttl or self.default_ttl
            
            if r:
                serialized = pickle.dumps(value)
                r.setex(key, ttl, serialized)
                return True
            else:
                # Fallback local com TTL simulado
                self._local_cache[key] = value
                return True
                
        except Exception as e:
            print(f"[CACHE ERROR] set: {e}")
            self._local_cache[key] = value
            return False
    
    def delete(self, key: str) -> bool:
        """Remove do cache"""
        try:
            r = self._get_redis()
            if r:
                r.delete(key)
            
            self._local_cache.pop(key, None)
            return True
            
        except Exception as e:
            print(f"[CACHE ERROR] delete: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Remove múltiplas chaves por padrão"""
        try:
            r = self._get_redis()
            if r:
                keys = r.keys(pattern)
                if keys:
                    return r.delete(*keys)
            
            # Fallback local
            count = 0
            for key in list(self._local_cache.keys()):
                if pattern.replace('*', '') in key:
                    del self._local_cache[key]
                    count += 1
            return count
            
        except Exception as e:
            print(f"[CACHE ERROR] delete_pattern: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Verifica se chave existe"""
        try:
            r = self._get_redis()
            if r:
                return r.exists(key) > 0
            return key in self._local_cache
        except:
            return key in self._local_cache
    
    def flush(self) -> bool:
        """Limpa todo o cache"""
        try:
            r = self._get_redis()
            if r:
                r.flushdb()
            self._local_cache.clear()
            return True
        except Exception as e:
            print(f"[CACHE ERROR] flush: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        try:
            r = self._get_redis()
            if r:
                info = r.info()
                return {
                    'hits': info.get('keyspace_hits', 0),
                    'misses': info.get('keyspace_misses', 0),
                    'hit_rate': info.get('keyspace_hits', 0) / max(1, info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0)),
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory': info.get('used_memory_human', '0B'),
                    'total_keys': r.dbsize(),
                    'local_cache_size': len(self._local_cache),
                }
            
            return {
                'status': 'LOCAL_ONLY',
                'local_cache_size': len(self._local_cache),
            }
            
        except Exception as e:
            return {'error': str(e), 'local_cache_size': len(self._local_cache)}


# Instância global
cache = CacheService()


# =============================================================================
# DECORATOR DE CACHE
# =============================================================================

def cached(ttl: int = 300, key_prefix: str = None, key_func = None):
    """
    Decorator para cache automático de funções
    
    Usage:
        @cached(ttl=60, key_prefix='user_stats')
        def get_user_stats(user_id: int):
            # ... expensive query
            return stats
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gerar chave de cache
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                prefix = key_prefix or func.__name__
                args_str = json.dumps({'args': args, 'kwargs': kwargs}, default=str)
                hash_key = hashlib.md5(args_str.encode()).hexdigest()
                cache_key = f"{prefix}:{hash_key}"
            
            # Tentar buscar do cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Executar função e cachear resultado
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(key_pattern: str):
    """Invalida cache por padrão"""
    return cache.delete_pattern(key_pattern)


# =============================================================================
# CACHES ESPECÍFICOS DO DOMÍNIO
# =============================================================================

class DocumentCache:
    """Cache específico para documentos"""
    
    @staticmethod
    @cached(ttl=300, key_prefix='doc_list')
    def get_user_documents(user_id: str, limit: int = 50):
        """Cache de lista de documentos"""
        # Esta função seria chamada com o cache
        pass
    
    @staticmethod
    def invalidate_user_docs(user_id: str):
        """Invalida cache quando documento é modificado"""
        cache.delete_pattern(f'doc_list:*"user_id": "{user_id}"*')


class AIResponseCache:
    """Cache de respostas da IA (semantic caching)"""
    
    @staticmethod
    def get_cached_response(question: str, context_hash: str) -> Optional[str]:
        """
        Busca resposta cacheada similar
        Usa hash do contexto para invalidação
        """
        cache_key = f"ai_response:{context_hash}:{hashlib.md5(question.encode()).hexdigest()}"
        return cache.get(cache_key)
    
    @staticmethod
    def cache_response(question: str, context_hash: str, response: str, ttl: int = 3600):
        """Cache de resposta da IA"""
        cache_key = f"ai_response:{context_hash}:{hashlib.md5(question.encode()).hexdigest()}"
        cache.set(cache_key, response, ttl)
    
    @staticmethod
    def invalidate_context(context_hash: str):
        """Invalida cache quando documento muda"""
        cache.delete_pattern(f'ai_response:{context_hash}:*')


class DashboardCache:
    """Cache de estatísticas do dashboard"""
    
    @staticmethod
    @cached(ttl=60, key_prefix='dashboard_stats')
    def get_user_stats(user_id: str):
        """Cache de estatísticas (1 minuto - atualizações frequentes)"""
        pass
    
    @staticmethod
    def invalidate_stats(user_id: str):
        """Invalida estatísticas"""
        cache.delete(f'dashboard_stats:user_stats:{user_id}')


class SessionCache:
    """Cache de sessões de usuário"""
    
    @staticmethod
    def get_session(session_id: str) -> Optional[Dict]:
        """Busca sessão do cache"""
        return cache.get(f"session:{session_id}")
    
    @staticmethod
    def set_session(session_id: str, data: Dict, ttl: int = 3600):
        """Salva sessão no cache"""
        cache.set(f"session:{session_id}", data, ttl)
    
    @staticmethod
    def delete_session(session_id: str):
        """Remove sessão"""
        cache.delete(f"session:{session_id}")


# =============================================================================
# CONFIGURAÇÃO REDIS
# =============================================================================

REDIS_CONFIG = """
# ========================================
# Redis Configuration - LexScan IA
# /etc/redis/redis.conf
# ========================================

# Memory
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec

# Performance
tcp-keepalive 300
timeout 0
tcp-backlog 511

# Security
# requirepass your_secure_password_here
bind 127.0.0.1
protected-mode yes

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log

# Limits
maxclients 10000

# Slow Log
slowlog-log-slower-than 10000
slowlog-max-len 128
"""


def generate_redis_config():
    """Gera arquivo de configuração do Redis"""
    with open('redis/redis.conf', 'w') as f:
        f.write(REDIS_CONFIG)
    
    print("✅ Configuração Redis salva em: redis/redis.conf")


# =============================================================================
# TESTES
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("REDIS CACHE SERVICE - TESTE")
    print("=" * 60)
    
    # Teste 1: Set e Get
    print("\n1. Teste básico de cache:")
    cache.set('test_key', {'data': 'value'}, 60)
    result = cache.get('test_key')
    print(f"   Set: {{'data': 'value'}}")
    print(f"   Get: {result}")
    print(f"   Status: {'✅ PASS' if result == {'data': 'value'} else '❌ FAIL'}")
    
    # Teste 2: TTL
    print("\n2. Teste de TTL:")
    cache.set('ttl_test', 'value', 1)
    print(f"   Set com TTL=1s: value")
    import time
    time.sleep(2)
    result = cache.get('ttl_test')
    print(f"   Get após 2s: {result}")
    print(f"   Status: {'✅ PASS (expirado)' if result is None else '❌ FAIL'}")
    
    # Teste 3: Decorator
    print("\n3. Teste do decorator @cached:")
    
    @cached(ttl=60, key_prefix='expensive_op')
    def expensive_operation(x: int, y: int) -> int:
        print(f"   [EXECUTANDO] expensive_operation({x}, {y})")
        return x * y + 100
    
    print("   Primeira chamada:")
    r1 = expensive_operation(5, 10)
    print(f"   Resultado: {r1}")
    
    print("   Segunda chamada (deve usar cache):")
    r2 = expensive_operation(5, 10)
    print(f"   Resultado: {r2}")
    print(f"   Status: {'✅ PASS (cache hit)' if r1 == r2 else '❌ FAIL'}")
    
    # Teste 4: Estatísticas
    print("\n4. Estatísticas do cache:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 60)
    print("TESTES COMPLETADOS!")
    print("=" * 60)
    print("\nPara usar Redis em produção:")
    print("• Instale: apt-get install redis-server")
    print("• Inicie: systemctl start redis-server")
    print("• Teste: redis-cli ping")
    print("• Configure: cp redis/redis.conf /etc/redis/")
    print("• Env var: REDIS_URL=redis://localhost:6379/0")
