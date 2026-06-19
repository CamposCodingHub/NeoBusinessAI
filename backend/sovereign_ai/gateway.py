"""Roteamento local-first, failover e auditoria de inferencia."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, Iterable, List

from config import settings
from database import AIInferenceEvent, SessionLocal

from .providers import (
    AIProviderError,
    OllamaNativeProvider,
    OpenAICompatibleProvider,
)
from .runtime import provider_runtime
from .security import sanitize_model_output

logger = logging.getLogger(__name__)


class SovereignAIGateway:
    """Ponto unico de entrada para todos os modelos de linguagem."""

    def __init__(self, providers: List[OpenAICompatibleProvider] | None = None):
        self.providers = providers or self._build_providers()

    @staticmethod
    def _build_providers() -> List[OpenAICompatibleProvider]:
        providers = [
            OllamaNativeProvider(
                name="local-primary",
                base_url=settings.LOCAL_AI_BASE_URL,
                api_key=settings.LOCAL_AI_API_KEY,
                local=True,
                timeout_seconds=settings.LOCAL_AI_TIMEOUT_SECONDS,
                max_retries=settings.LOCAL_AI_MAX_RETRIES,
            )
        ]
        if settings.LOCAL_AI_SECONDARY_URL:
            providers.append(
                OpenAICompatibleProvider(
                    name="local-secondary",
                    base_url=settings.LOCAL_AI_SECONDARY_URL,
                    api_key=settings.LOCAL_AI_API_KEY,
                    local=True,
                    timeout_seconds=settings.LOCAL_AI_TIMEOUT_SECONDS,
                    max_retries=settings.LOCAL_AI_MAX_RETRIES,
                )
            )
        if settings.AI_EXTERNAL_FALLBACK_ENABLED and settings.GROQ_API_KEY:
            providers.append(
                OpenAICompatibleProvider(
                    name="groq",
                    base_url="https://api.groq.com/openai/v1",
                    api_key=settings.GROQ_API_KEY,
                    local=False,
                    timeout_seconds=120,
                    max_retries=1,
                )
            )
        return providers

    @property
    def provider_names(self) -> List[str]:
        return [provider.name for provider in self.providers]

    def _is_deep_request(
        self,
        requested_model: str,
        messages: Iterable[Dict[str, Any]],
        max_tokens: int,
    ) -> bool:
        del requested_model
        if max_tokens >= 3000:
            return True
        system_text = " ".join(
            str(message.get("content") or "")
            for message in messages
            if message.get("role") == "system"
        ).lower()
        return any(
            marker in system_text
            for marker in (
                "pesquisa profissional profunda",
                "pesquisador senior juridico",
            )
        )

    @staticmethod
    def _is_professional_request(
        messages: Iterable[Dict[str, Any]],
    ) -> bool:
        system_text = " ".join(
            str(message.get("content") or "")
            for message in messages
            if message.get("role") == "system"
        ).lower()
        return any(
            marker in system_text
            for marker in (
                "copiloto de pesquisa juridica",
                "modo de trabalho profissional",
                "fontes oficiais",
                "dominio profissional",
            )
        )

    @staticmethod
    def _is_quick_professional_request(
        messages: Iterable[Dict[str, Any]],
    ) -> bool:
        system_text = " ".join(
            str(message.get("content") or "")
            for message in messages
            if message.get("role") == "system"
        ).lower()
        return "consulta profissional rapida" in system_text

    def _ordered_providers(self) -> List[OpenAICompatibleProvider]:
        local = [provider for provider in self.providers if provider.local]
        external = [provider for provider in self.providers if not provider.local]
        if settings.AI_ROUTING_POLICY == "external_first":
            return [*external, *local]
        if settings.AI_ROUTING_POLICY == "local_only":
            return local
        return [*local, *external]

    async def create_chat_completion(self, **kwargs):
        requested_model = str(kwargs.get("model") or "")
        messages = list(kwargs.get("messages") or [])
        max_tokens = int(kwargs.get("max_tokens") or 1400)
        deep = self._is_deep_request(requested_model, messages, max_tokens)
        professional = self._is_professional_request(messages)
        quick_professional = (
            professional
            and not deep
            and self._is_quick_professional_request(messages)
        )
        route = (
            "deep_legal"
            if deep
            else "quick_legal"
            if quick_professional
            else "balanced_legal"
            if professional
            else "fast_general"
        )
        local_model = (
            settings.LOCAL_AI_DEEP_MODEL
            if deep
            else settings.LOCAL_AI_QUICK_MODEL
            if quick_professional
            else settings.LOCAL_AI_BALANCED_MODEL
            if professional
            else settings.LOCAL_AI_FAST_MODEL
        )
        request_id = uuid.uuid4().hex
        attempts = []
        last_error: Exception | None = None

        for index, provider in enumerate(self._ordered_providers()):
            if not provider_runtime.allows_request(provider.name):
                attempts.append(
                    {"provider": provider.name, "status": "circuit_open"}
                )
                continue
            actual_request_model = (
                local_model if provider.local else requested_model
            )
            started = time.perf_counter()
            try:
                completion = await provider.complete(
                    model=actual_request_model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=float(kwargs.get("temperature") or 0.2),
                    top_p=float(kwargs.get("top_p") or 0.9),
                    extra={
                        "keep_alive": settings.LOCAL_AI_KEEP_ALIVE,
                        "num_ctx": (
                            settings.LOCAL_AI_CONTEXT_TOKENS
                            if deep or (professional and not quick_professional)
                            else min(
                                settings.LOCAL_AI_CONTEXT_TOKENS,
                                4096,
                            )
                        ),
                    },
                )
                (
                    completion.content,
                    output_guardrail_blocked,
                ) = sanitize_model_output(messages, completion.content)
                completion.raw_metadata[
                    "output_guardrail_blocked"
                ] = output_guardrail_blocked
                provider_runtime.record_success(provider.name)
                fallback_used = index > 0
                attempts.append(
                    {
                        "provider": provider.name,
                        "model": completion.model,
                        "status": "success",
                        "latency_ms": completion.latency_ms,
                    }
                )
                self._persist_event(
                    request_id=request_id,
                    provider=provider,
                    route=route,
                    requested_model=requested_model,
                    actual_model=completion.model,
                    status="success",
                    latency_ms=completion.latency_ms,
                    usage=completion.usage,
                    fallback_used=fallback_used,
                    attempts=attempts,
                )
                completion.request_id = request_id
                completion.raw_metadata["attempts"] = attempts
                return completion.as_openai_response(
                    requested_model=requested_model,
                    route=route,
                    fallback_used=fallback_used,
                )
            except Exception as exc:
                last_error = exc
                provider_runtime.record_failure(provider.name, exc)
                latency_ms = int((time.perf_counter() - started) * 1000)
                attempts.append(
                    {
                        "provider": provider.name,
                        "model": actual_request_model,
                        "status": "error",
                        "error": str(exc)[:300],
                        "latency_ms": latency_ms,
                    }
                )
                self._persist_event(
                    request_id=request_id,
                    provider=provider,
                    route=route,
                    requested_model=requested_model,
                    actual_model=actual_request_model,
                    status="error",
                    latency_ms=latency_ms,
                    error=exc,
                    fallback_used=index > 0,
                    attempts=attempts,
                )
                logger.warning(
                    "Falha no provedor %s para rota %s: %s",
                    provider.name,
                    route,
                    exc,
                )

        if isinstance(last_error, AIProviderError):
            raise last_error
        raise AIProviderError(
            "Nenhum servidor de IA local esta disponivel",
            provider="gateway",
            code="all_providers_unavailable",
        ) from last_error

    async def health(self) -> Dict[str, Any]:
        health_results = []
        for provider in self.providers:
            health_results.append(await provider.health())
        healthy = [item for item in health_results if item.status == "healthy"]
        return {
            "status": (
                "healthy"
                if healthy
                else "unhealthy"
            ),
            "routing_policy": settings.AI_ROUTING_POLICY,
            "sovereign_enabled": settings.AI_SOVEREIGN_ENABLED,
            "external_fallback_enabled": settings.AI_EXTERNAL_FALLBACK_ENABLED,
            "models": {
                "fast": settings.LOCAL_AI_FAST_MODEL,
                "quick": settings.LOCAL_AI_QUICK_MODEL,
                "balanced": settings.LOCAL_AI_BALANCED_MODEL,
                "deep": settings.LOCAL_AI_DEEP_MODEL,
                "embedding": settings.LOCAL_AI_EMBEDDING_MODEL,
            },
            "providers": [
                {
                    "name": item.provider,
                    "endpoint": item.endpoint,
                    "status": item.status,
                    "latency_ms": item.latency_ms,
                    "models": item.models,
                    "error": item.error,
                }
                for item in health_results
            ],
            "circuits": provider_runtime.snapshot(self.provider_names),
        }

    @staticmethod
    def _persist_event(
        *,
        request_id: str,
        provider: OpenAICompatibleProvider,
        route: str,
        requested_model: str,
        actual_model: str,
        status: str,
        latency_ms: int,
        usage=None,
        error: Exception | None = None,
        fallback_used: bool,
        attempts: List[Dict[str, Any]],
    ) -> None:
        try:
            from metrics import track_ai_provider_request

            track_ai_provider_request(
                provider=provider.name,
                model=actual_model,
                route=route,
                status=status,
                latency_ms=latency_ms,
                prompt_tokens=getattr(usage, "prompt_tokens", 0),
                completion_tokens=getattr(usage, "completion_tokens", 0),
            )
        except Exception:
            logger.debug("Metricas de IA indisponiveis", exc_info=True)

        db = SessionLocal()
        try:
            db.add(
                AIInferenceEvent(
                    request_id=request_id,
                    provider=provider.name,
                    endpoint=provider.endpoint,
                    route=route,
                    requested_model=requested_model,
                    actual_model=actual_model,
                    status=status,
                    error_code=str(getattr(error, "code", "")) or None,
                    error_message=str(error)[:1000] if error else None,
                    latency_ms=latency_ms,
                    prompt_tokens=getattr(usage, "prompt_tokens", 0),
                    completion_tokens=getattr(usage, "completion_tokens", 0),
                    total_tokens=getattr(usage, "total_tokens", 0),
                    estimated_cost_usd=0 if provider.local else None,
                    fallback_used=fallback_used,
                    custom_data={"attempts": attempts},
                )
            )
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Falha ao persistir auditoria de inferencia")
        finally:
            db.close()


sovereign_ai_gateway = SovereignAIGateway()
