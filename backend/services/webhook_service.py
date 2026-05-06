"""
Webhook Service
===============
Serviço para processamento seguro de webhooks com anti-replay.
"""

from typing import Optional
from datetime import datetime, timedelta
import redis
import json
import hashlib

from core.config import settings


class WebhookService:
    """Serviço de processamento de webhooks com anti-replay"""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.replay_window_seconds = 300  # 5 minutos
    
    def is_duplicate(self, request_id: str) -> bool:
        """
        Verifica se webhook já foi processado (anti-replay).
        
        Args:
            request_id: ID único do request
            
        Returns:
            True se duplicado, False se novo
        """
        key = f"webhook:processed:{request_id}"
        return self.redis_client.exists(key) > 0
    
    def mark_as_processed(self, request_id: str, payload: dict):
        """
        Marca webhook como processado.
        
        Args:
            request_id: ID único do request
            payload: Payload do webhook (para debugging)
        """
        key = f"webhook:processed:{request_id}"
        
        # Armazenar por 24 horas
        self.redis_client.setex(
            key,
            86400,  # 24 horas
            json.dumps({
                "processed_at": datetime.utcnow().isoformat(),
                "payload": payload
            })
        )
    
    def generate_webhook_id(self, payload: dict) -> str:
        """
        Gera ID único para webhook baseado no payload.
        
        Args:
            payload: Payload do webhook
            
        Returns:
            Hash único
        """
        payload_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(payload_str.encode()).hexdigest()
    
    def store_pending_webhook(self, webhook_id: str, payload: dict, ttl: int = 3600):
        """
        Armazena webhook pendente para retry.
        
        Args:
            webhook_id: ID do webhook
            payload: Payload
            ttl: Time to live em segundos
        """
        key = f"webhook:pending:{webhook_id}"
        self.redis_client.setex(
            key,
            ttl,
            json.dumps({
                "payload": payload,
                "created_at": datetime.utcnow().isoformat(),
                "retry_count": 0
            })
        )
    
    def get_pending_webhook(self, webhook_id: str) -> Optional[dict]:
        """
        Obtém webhook pendente.
        
        Args:
            webhook_id: ID do webhook
            
        Returns:
            Payload ou None
        """
        key = f"webhook:pending:{webhook_id}"
        data = self.redis_client.get(key)
        
        if data:
            return json.loads(data)
        return None
    
    def increment_retry_count(self, webhook_id: str):
        """
        Incrementa contador de retry.
        
        Args:
            webhook_id: ID do webhook
        """
        key = f"webhook:pending:{webhook_id}"
        data = self.redis_client.get(key)
        
        if data:
            parsed = json.loads(data)
            parsed["retry_count"] = parsed.get("retry_count", 0) + 1
            self.redis_client.setex(
                key,
                3600,
                json.dumps(parsed)
            )
    
    def delete_pending_webhook(self, webhook_id: str):
        """
        Remove webhook pendente após processamento bem-sucedido.
        
        Args:
            webhook_id: ID do webhook
        """
        key = f"webhook:pending:{webhook_id}"
        self.redis_client.delete(key)
    
    def get_retry_count(self, webhook_id: str) -> int:
        """
        Obtém número de retries.
        
        Args:
            webhook_id: ID do webhook
            
        Returns:
            Número de retries
        """
        webhook = self.get_pending_webhook(webhook_id)
        if webhook:
            return webhook.get("retry_count", 0)
        return 0


# Singleton instance
webhook_service = WebhookService()
