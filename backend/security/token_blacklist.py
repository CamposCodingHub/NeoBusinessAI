"""
JWT token blacklist com degradacao elegante.
Se Redis nao estiver disponivel, o sistema continua autenticando sem ruido excessivo.
"""

import logging
import os
import time

import redis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class TokenBlacklist:
    """Gerencia blacklist de tokens JWT e refresh tokens."""

    def __init__(self):
        self.redis_client = None
        self.is_available = False
        self._warning_logged = False
        self._memory_blacklist = {}
        self._memory_refresh_tokens = {}
        self._last_connection_attempt = 0.0
        self._retry_interval_seconds = 30
        self._initialize_client()

    def _cleanup_memory_store(self, store: dict):
        now = time.time()
        expired = [key for key, expires_at in store.items() if expires_at <= now]
        for key in expired:
            store.pop(key, None)

    def _initialize_client(self):
        self._last_connection_attempt = time.time()
        try:
            client = redis.from_url(
                REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
            client.ping()
            self.redis_client = client
            self.is_available = True
            self._warning_logged = False
            logger.info("Token blacklist conectada ao Redis com sucesso.")
        except Exception as exc:
            self.redis_client = None
            self.is_available = False
            self._log_unavailable_once(
                f"Redis indisponivel para token blacklist. Sistema segue em modo degradado. Erro: {exc}"
            )

    def _ensure_connection(self):
        if self.is_available and self.redis_client:
            return
        if (
            time.time() - self._last_connection_attempt
            >= self._retry_interval_seconds
        ):
            self._initialize_client()

    def _log_unavailable_once(self, message: str):
        if not self._warning_logged:
            logger.warning(message)
            self._warning_logged = True

    def _disable_temporarily(self, exc: Exception):
        self.redis_client = None
        self.is_available = False
        self._log_unavailable_once(
            f"Token blacklist entrou em modo degradado por falha no Redis: {exc}"
        )

    def add_to_blacklist(self, token: str, expires_in: int = 3600) -> bool:
        self._ensure_connection()
        if not self.is_available or not self.redis_client:
            self._memory_blacklist[token] = time.time() + expires_in
            return True

        try:
            key = f"blacklist:token:{token}"
            self.redis_client.setex(key, expires_in, "revoked")
            return True
        except Exception as exc:
            self._disable_temporarily(exc)
            self._memory_blacklist[token] = time.time() + expires_in
            return True

    def is_blacklisted(self, token: str) -> bool:
        self._cleanup_memory_store(self._memory_blacklist)
        if token in self._memory_blacklist:
            return True

        self._ensure_connection()
        if not self.is_available or not self.redis_client:
            return False

        try:
            key = f"blacklist:token:{token}"
            return self.redis_client.exists(key) > 0
        except Exception as exc:
            self._disable_temporarily(exc)
            return token in self._memory_blacklist

    def add_refresh_token(
        self, refresh_token: str, user_id: int, expires_in: int = 604800
    ) -> bool:
        self._ensure_connection()
        if not self.is_available or not self.redis_client:
            key = f"refresh_token:{user_id}:{refresh_token}"
            self._memory_refresh_tokens[key] = time.time() + expires_in
            return True

        try:
            key = f"refresh_token:{user_id}:{refresh_token}"
            self.redis_client.setex(key, expires_in, "valid")
            return True
        except Exception as exc:
            self._disable_temporarily(exc)
            key = f"refresh_token:{user_id}:{refresh_token}"
            self._memory_refresh_tokens[key] = time.time() + expires_in
            return True

    def is_refresh_token_valid(self, refresh_token: str, user_id: int) -> bool:
        self._cleanup_memory_store(self._memory_refresh_tokens)
        key = f"refresh_token:{user_id}:{refresh_token}"
        if key in self._memory_refresh_tokens:
            return True

        self._ensure_connection()
        if not self.is_available or not self.redis_client:
            return False

        try:
            return self.redis_client.exists(key) > 0
        except Exception as exc:
            self._disable_temporarily(exc)
            return key in self._memory_refresh_tokens

    def revoke_refresh_token(self, refresh_token: str, user_id: int) -> bool:
        key = f"refresh_token:{user_id}:{refresh_token}"
        self._memory_refresh_tokens.pop(key, None)

        self._ensure_connection()
        if not self.is_available or not self.redis_client:
            return True

        try:
            self.redis_client.delete(key)
            return True
        except Exception as exc:
            self._disable_temporarily(exc)
            return True

    def revoke_all_user_tokens(self, user_id: int) -> bool:
        prefix = f"refresh_token:{user_id}:"
        keys_to_remove = [key for key in self._memory_refresh_tokens if key.startswith(prefix)]
        for key in keys_to_remove:
            self._memory_refresh_tokens.pop(key, None)

        self._ensure_connection()
        if not self.is_available or not self.redis_client:
            return True

        try:
            pattern = f"{prefix}*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            return True
        except Exception as exc:
            self._disable_temporarily(exc)
            return True


token_blacklist = TokenBlacklist()


def blacklist_token(token: str, expires_in: int = 3600) -> bool:
    return token_blacklist.add_to_blacklist(token, expires_in)


def is_token_blacklisted(token: str) -> bool:
    return token_blacklist.is_blacklisted(token)


def add_refresh_token(
    refresh_token: str, user_id: int, expires_in: int = 604800
) -> bool:
    return token_blacklist.add_refresh_token(refresh_token, user_id, expires_in)


def is_refresh_token_valid(refresh_token: str, user_id: int) -> bool:
    return token_blacklist.is_refresh_token_valid(refresh_token, user_id)


def revoke_refresh_token(refresh_token: str, user_id: int) -> bool:
    return token_blacklist.revoke_refresh_token(refresh_token, user_id)


def revoke_all_user_tokens(user_id: int) -> bool:
    return token_blacklist.revoke_all_user_tokens(user_id)
