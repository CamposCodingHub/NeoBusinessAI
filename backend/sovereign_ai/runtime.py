"""Circuit breaker distribuido com fallback em memoria."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import asdict, dataclass
from typing import Dict, Optional

from config import settings


@dataclass
class CircuitState:
    failures: int = 0
    open_until: float = 0
    last_error: str = ""
    last_success_at: float = 0
    last_failure_at: float = 0

    @property
    def status(self) -> str:
        if self.open_until > time.time():
            return "open"
        if self.failures:
            return "degraded"
        return "closed"


class ProviderRuntimeRegistry:
    """Compartilha estado de falhas entre processos quando Redis esta ativo."""

    def __init__(self):
        self._memory: Dict[str, CircuitState] = {}
        self._lock = threading.Lock()
        self._redis = self._connect_redis()

    @staticmethod
    def _connect_redis():
        if not settings.REDIS_URL:
            return None
        try:
            import redis

            client = redis.from_url(
                settings.REDIS_URL,
                socket_connect_timeout=1,
                socket_timeout=1,
                decode_responses=True,
            )
            client.ping()
            return client
        except Exception:
            return None

    @staticmethod
    def _key(provider: str) -> str:
        return f"sovereign-ai:circuit:{provider}"

    def get(self, provider: str) -> CircuitState:
        if self._redis:
            try:
                payload = self._redis.get(self._key(provider))
                if payload:
                    return CircuitState(**json.loads(payload))
            except Exception:
                self._redis = None
        with self._lock:
            return self._memory.get(provider, CircuitState())

    def _save(self, provider: str, state: CircuitState) -> None:
        with self._lock:
            self._memory[provider] = state
        if self._redis:
            try:
                self._redis.set(
                    self._key(provider),
                    json.dumps(asdict(state)),
                    ex=max(settings.AI_CIRCUIT_RECOVERY_SECONDS * 4, 600),
                )
            except Exception:
                self._redis = None

    def allows_request(self, provider: str) -> bool:
        return self.get(provider).open_until <= time.time()

    def record_success(self, provider: str) -> None:
        self._save(
            provider,
            CircuitState(last_success_at=time.time()),
        )

    def record_failure(self, provider: str, error: Exception) -> CircuitState:
        state = self.get(provider)
        state.failures += 1
        state.last_error = str(error)[:500]
        state.last_failure_at = time.time()
        if state.failures >= settings.AI_CIRCUIT_FAILURE_THRESHOLD:
            state.open_until = (
                time.time() + settings.AI_CIRCUIT_RECOVERY_SECONDS
            )
        self._save(provider, state)
        return state

    def snapshot(self, providers: list[str]) -> Dict[str, Dict[str, object]]:
        result = {}
        for provider in providers:
            state = self.get(provider)
            result[provider] = {
                **asdict(state),
                "status": state.status,
                "allowed": state.open_until <= time.time(),
            }
        return result


provider_runtime = ProviderRuntimeRegistry()
