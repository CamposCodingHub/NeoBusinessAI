"""Contratos internos independentes de fornecedor."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, Dict, List


@dataclass
class AIUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    @classmethod
    def from_payload(cls, payload: Dict[str, Any] | None) -> "AIUsage":
        payload = payload or {}
        prompt = int(payload.get("prompt_tokens") or 0)
        completion = int(payload.get("completion_tokens") or 0)
        total = int(payload.get("total_tokens") or prompt + completion)
        return cls(prompt, completion, total)


@dataclass
class ProviderCompletion:
    provider: str
    model: str
    content: str
    finish_reason: str = "stop"
    usage: AIUsage = field(default_factory=AIUsage)
    latency_ms: int = 0
    request_id: str = ""
    endpoint: str = ""
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def as_openai_response(
        self,
        requested_model: str,
        route: str,
        fallback_used: bool,
    ) -> SimpleNamespace:
        """Adapta o resultado ao contrato consumido pelo motor existente."""
        response = SimpleNamespace(
            id=self.request_id,
            model=self.model,
            provider=self.provider,
            requested_model=requested_model,
            route=route,
            fallback_used=fallback_used,
            latency_ms=self.latency_ms,
            usage=SimpleNamespace(
                prompt_tokens=self.usage.prompt_tokens,
                completion_tokens=self.usage.completion_tokens,
                total_tokens=self.usage.total_tokens,
            ),
            choices=[
                SimpleNamespace(
                    finish_reason=self.finish_reason,
                    message=SimpleNamespace(content=self.content),
                )
            ],
        )
        response.sovereign_metadata = {
            "provider": self.provider,
            "endpoint": self.endpoint,
            "route": route,
            "fallback_used": fallback_used,
            "latency_ms": self.latency_ms,
            **self.raw_metadata,
        }
        return response


@dataclass
class ProviderHealth:
    provider: str
    endpoint: str
    status: str
    latency_ms: int
    models: List[str] = field(default_factory=list)
    error: str = ""

