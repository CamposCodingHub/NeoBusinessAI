"""
Cache Manager Inteligente
=========================
Cache multi-nível com Redis para performance
Estratégias: LRU, TTL, Cache por hash de documento
"""

import json
import hashlib
import pickle
from typing import Any, Optional, Dict, List
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Gerenciador de cache multi-nível
    - Nível 1: Memória (LRU)
    - Nível 2: Redis (persistente)
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_client = None
        self.memory_cache: Dict[str, Any] = {}
        self.memory_cache_size = 1000
        self.enabled = True
        
        if redis_url:
            try:
                import redis
                self.redis_client = redis.from_url(redis_url, decode_responses=False)
                self.redis_client.ping()
                logger.info("✅ Redis cache connected")
            except Exception as e:
                logger.warning(f"Redis connection failed, using memory cache only: {e}")
    
    def _generate_key(self, prefix: str, *args) -> str:
        """Gera chave de cache baseada nos argumentos"""
        key_parts = [prefix]
        for arg in args:
            if isinstance(arg, (str, int, float)):
                key_parts.append(str(arg))
            elif isinstance(arg, (dict, list)):
                key_parts.append(hashlib.md5(json.dumps(arg, sort_keys=True).encode()).hexdigest())
            else:
                key_parts.append(hashlib.md5(str(arg).encode()).hexdigest())
        return ":".join(key_parts)
    
    def get(self, prefix: str, *args) -> Optional[Any]:
        """Obtém valor do cache"""
        if not self.enabled:
            return None
        
        key = self._generate_key(prefix, *args)
        
        # Tenta cache de memória primeiro
        if key in self.memory_cache:
            logger.debug(f"Cache HIT (memory): {key}")
            return self.memory_cache[key]
        
        # Tenta Redis
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    logger.debug(f"Cache HIT (redis): {key}")
                    # Deserializa
                    try:
                        return pickle.loads(value)
                    except:
                        return value
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")
        
        logger.debug(f"Cache MISS: {key}")
        return None
    
    def set(self, prefix: str, *args, value: Any, ttl: int = 3600):
        """Define valor no cache"""
        if not self.enabled:
            return
        
        key = self._generate_key(prefix, *args)
        
        # Cache de memória
        if len(self.memory_cache) >= self.memory_cache_size:
            # Remove item mais antigo (simplificado)
            self.memory_cache.pop(next(iter(self.memory_cache)))
        self.memory_cache[key] = value
        
        # Redis
        if self.redis_client:
            try:
                serialized = pickle.dumps(value)
                self.redis_client.setex(key, ttl, serialized)
                logger.debug(f"Cache SET (redis): {key} (TTL: {ttl}s)")
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")
    
    def delete(self, prefix: str, *args):
        """Remove valor do cache"""
        key = self._generate_key(prefix, *args)
        
        # Remove de memória
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        # Remove do Redis
        if self.redis_client:
            try:
                self.redis_client.delete(key)
                logger.debug(f"Cache DELETE: {key}")
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")
    
    def invalidate_pattern(self, pattern: str):
        """Invalida todos os caches que correspondem ao padrão"""
        if self.redis_client:
            try:
                keys = self.redis_client.keys(f"*{pattern}*")
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Invalidated {len(keys)} cache entries matching: {pattern}")
            except Exception as e:
                logger.warning(f"Redis pattern delete failed: {e}")
        
        # Invalida cache de memória
        keys_to_delete = [k for k in self.memory_cache.keys() if pattern in k]
        for key in keys_to_delete:
            del self.memory_cache[key]
    
    def clear_all(self):
        """Limpa todo o cache"""
        self.memory_cache.clear()
        
        if self.redis_client:
            try:
                self.redis_client.flushdb()
                logger.info("✅ All cache cleared")
            except Exception as e:
                logger.warning(f"Redis flush failed: {e}")


class DocumentCache(CacheManager):
    """Cache especializado para documentos"""
    
    def cache_ocr_result(self, document_hash: str, ocr_result: Dict, ttl: int = 86400):
        """Cache resultado de OCR por hash do documento (24h)"""
        self.set("ocr", document_hash, value=ocr_result, ttl=ttl)
    
    def get_ocr_result(self, document_hash: str) -> Optional[Dict]:
        """Obtém resultado de OCR cacheado"""
        return self.get("ocr", document_hash)
    
    def cache_extraction_result(self, document_hash: str, extraction: Dict, ttl: int = 3600):
        """Cache resultado de extração semântica (1h)"""
        self.set("extraction", document_hash, value=extraction, ttl=ttl)
    
    def get_extraction_result(self, document_hash: str) -> Optional[Dict]:
        """Obtém resultado de extração cacheado"""
        return self.get("extraction", document_hash)
    
    def cache_ai_response(self, prompt_hash: str, response: str, ttl: int = 1800):
        """Cache resposta de IA (30min)"""
        self.set("ai", prompt_hash, value=response, ttl=ttl)
    
    def get_ai_response(self, prompt_hash: str) -> Optional[str]:
        """Obtém resposta de IA cacheada"""
        return self.get("ai", prompt_hash)


class UserCache(CacheManager):
    """Cache especializado para usuários"""
    
    def cache_user_data(self, user_id: int, user_data: Dict, ttl: int = 300):
        """Cache dados do usuário (5min)"""
        self.set("user", user_id, value=user_data, ttl=ttl)
    
    def get_user_data(self, user_id: int) -> Optional[Dict]:
        """Obtém dados do usuário cacheados"""
        return self.get("user", user_id)
    
    def cache_user_documents(self, user_id: int, documents: List, ttl: int = 60):
        """Cache lista de documentos do usuário (1min)"""
        self.set("docs", user_id, value=documents, ttl=ttl)
    
    def get_user_documents(self, user_id: int) -> Optional[List]:
        """Obtém documentos do usuário cacheados"""
        return self.get("docs", user_id)
    
    def invalidate_user(self, user_id: int):
        """Invalida todos os caches do usuário"""
        self.invalidate_pattern(f"user:{user_id}")
        self.invalidate_pattern(f"docs:{user_id}")


# Instâncias globais
from config import settings

cache_manager = CacheManager(settings.REDIS_URL)
document_cache = DocumentCache(settings.REDIS_URL)
user_cache = UserCache(settings.REDIS_URL)
