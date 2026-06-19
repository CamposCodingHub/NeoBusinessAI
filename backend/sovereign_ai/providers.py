"""Provedores HTTP compativeis com a API OpenAI."""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, Dict, Iterable

import httpx

from .contracts import AIUsage, ProviderCompletion, ProviderHealth


class AIProviderError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        provider: str,
        code: str = "provider_error",
        retryable: bool = False,
        retry_after: float = 0,
        status_code: int | None = None,
    ):
        super().__init__(message)
        self.provider = provider
        self.code = code
        self.retryable = retryable
        self.retry_after = retry_after
        self.status_code = status_code


class OpenAICompatibleProvider:
    """Cliente unico para Ollama, vLLM, llama.cpp e Groq."""

    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        api_key: str,
        local: bool,
        timeout_seconds: int,
        max_retries: int = 0,
    ):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.local = local
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    @property
    def endpoint(self) -> str:
        return f"{self.base_url}/chat/completions"

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def health(self) -> ProviderHealth:
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=self._headers(),
                )
                response.raise_for_status()
            models = [
                str(item.get("id"))
                for item in response.json().get("data", [])
                if item.get("id")
            ]
            return ProviderHealth(
                provider=self.name,
                endpoint=self.base_url,
                status="healthy",
                latency_ms=int((time.perf_counter() - started) * 1000),
                models=models,
            )
        except Exception as exc:
            return ProviderHealth(
                provider=self.name,
                endpoint=self.base_url,
                status="unhealthy",
                latency_ms=int((time.perf_counter() - started) * 1000),
                error=str(exc)[:500],
            )

    async def complete(
        self,
        *,
        model: str,
        messages: Iterable[Dict[str, Any]],
        max_tokens: int,
        temperature: float,
        top_p: float,
        extra: Dict[str, Any] | None = None,
    ) -> ProviderCompletion:
        payload = {
            "model": model,
            "messages": list(messages),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": False,
        }
        if self.local:
            payload["keep_alive"] = (extra or {}).get("keep_alive", "15m")

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            started = time.perf_counter()
            try:
                timeout = httpx.Timeout(
                    self.timeout_seconds,
                    connect=min(10, self.timeout_seconds),
                )
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        self.endpoint,
                        headers=self._headers(),
                        json=payload,
                    )
                if response.status_code >= 400:
                    raise self._response_error(response)
                data = response.json()
                choices = data.get("choices") or []
                if not choices:
                    raise AIProviderError(
                        "Resposta sem escolhas",
                        provider=self.name,
                        code="empty_response",
                    )
                choice = choices[0]
                content = str((choice.get("message") or {}).get("content") or "")
                if not content.strip():
                    raise AIProviderError(
                        "Resposta vazia",
                        provider=self.name,
                        code="empty_content",
                    )
                return ProviderCompletion(
                    provider=self.name,
                    model=str(data.get("model") or model),
                    content=content,
                    finish_reason=str(choice.get("finish_reason") or "stop"),
                    usage=AIUsage.from_payload(data.get("usage")),
                    latency_ms=int((time.perf_counter() - started) * 1000),
                    request_id=str(data.get("id") or uuid.uuid4().hex),
                    endpoint=self.endpoint,
                    raw_metadata={
                        "local": self.local,
                        "attempt": attempt + 1,
                    },
                )
            except AIProviderError as exc:
                last_error = exc
                if not exc.retryable or attempt >= self.max_retries:
                    raise
                await asyncio.sleep(
                    exc.retry_after or min(2 ** attempt, 5)
                )
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = AIProviderError(
                    str(exc),
                    provider=self.name,
                    code="network_error",
                    retryable=True,
                )
                if attempt >= self.max_retries:
                    raise last_error from exc
                await asyncio.sleep(min(2 ** attempt, 5))

        raise last_error or AIProviderError(
            "Falha desconhecida",
            provider=self.name,
        )

    def _response_error(self, response: httpx.Response) -> AIProviderError:
        try:
            payload = response.json()
            error = payload.get("error") or payload
            if isinstance(error, dict):
                message = str(error.get("message") or error)
                code = str(error.get("code") or response.status_code)
            else:
                message = str(error)
                code = str(response.status_code)
        except Exception:
            message = response.text[:500]
            code = str(response.status_code)
        retry_after = 0.0
        try:
            retry_after = float(response.headers.get("retry-after") or 0)
        except ValueError:
            pass
        return AIProviderError(
            message,
            provider=self.name,
            code=code,
            retryable=response.status_code in {408, 429, 498, 500, 502, 503, 504},
            retry_after=retry_after,
            status_code=response.status_code,
        )


class OllamaNativeProvider(OpenAICompatibleProvider):
    """Usa a API nativa para controlar thinking, contexto e keep-alive."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.native_base_url = self.base_url.removesuffix("/v1")

    @property
    def endpoint(self) -> str:
        return f"{self.native_base_url}/api/chat"

    async def health(self) -> ProviderHealth:
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{self.native_base_url}/api/tags"
                )
                response.raise_for_status()
            models = [
                str(item.get("name"))
                for item in response.json().get("models", [])
                if item.get("name")
            ]
            return ProviderHealth(
                provider=self.name,
                endpoint=self.native_base_url,
                status="healthy",
                latency_ms=int((time.perf_counter() - started) * 1000),
                models=models,
            )
        except Exception as exc:
            return ProviderHealth(
                provider=self.name,
                endpoint=self.native_base_url,
                status="unhealthy",
                latency_ms=int((time.perf_counter() - started) * 1000),
                error=str(exc)[:500],
            )

    async def complete(
        self,
        *,
        model: str,
        messages: Iterable[Dict[str, Any]],
        max_tokens: int,
        temperature: float,
        top_p: float,
        extra: Dict[str, Any] | None = None,
    ) -> ProviderCompletion:
        payload = {
            "model": model,
            "messages": list(messages),
            "stream": False,
            "think": False,
            "keep_alive": (extra or {}).get("keep_alive", "15m"),
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "num_ctx": int((extra or {}).get("num_ctx", 8192)),
            },
        }
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            started = time.perf_counter()
            try:
                timeout = httpx.Timeout(
                    self.timeout_seconds,
                    connect=min(10, self.timeout_seconds),
                )
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        self.endpoint,
                        json=payload,
                    )
                if response.status_code >= 400:
                    raise self._response_error(response)
                data = response.json()
                message = data.get("message") or {}
                content = str(message.get("content") or "")
                if not content.strip():
                    raise AIProviderError(
                        "Resposta vazia",
                        provider=self.name,
                        code="empty_content",
                    )
                prompt_tokens = int(data.get("prompt_eval_count") or 0)
                completion_tokens = int(data.get("eval_count") or 0)
                return ProviderCompletion(
                    provider=self.name,
                    model=str(data.get("model") or model),
                    content=content,
                    finish_reason=(
                        "stop" if data.get("done_reason") == "stop" else
                        str(data.get("done_reason") or "stop")
                    ),
                    usage=AIUsage(
                        prompt_tokens,
                        completion_tokens,
                        prompt_tokens + completion_tokens,
                    ),
                    latency_ms=int((time.perf_counter() - started) * 1000),
                    request_id=uuid.uuid4().hex,
                    endpoint=self.endpoint,
                    raw_metadata={
                        "local": True,
                        "attempt": attempt + 1,
                        "load_duration_ns": data.get("load_duration"),
                        "prompt_eval_duration_ns": data.get(
                            "prompt_eval_duration"
                        ),
                        "eval_duration_ns": data.get("eval_duration"),
                    },
                )
            except AIProviderError as exc:
                last_error = exc
                if not exc.retryable or attempt >= self.max_retries:
                    raise
                await asyncio.sleep(exc.retry_after or min(2 ** attempt, 5))
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = AIProviderError(
                    str(exc),
                    provider=self.name,
                    code="network_error",
                    retryable=True,
                )
                if attempt >= self.max_retries:
                    raise last_error from exc
                await asyncio.sleep(min(2 ** attempt, 5))
        raise last_error or AIProviderError(
            "Falha desconhecida",
            provider=self.name,
        )
