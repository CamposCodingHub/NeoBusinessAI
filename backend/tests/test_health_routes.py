"""Testes dos diagnosticos de infraestrutura."""

from routes.health_routes import check_celery, check_external_apis
from tasks import app as celery_app


class FakeConnection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def connect(self):
        return None


class FakeInspector:
    def __init__(self, workers):
        self.workers = workers

    def ping(self):
        return self.workers


def test_celery_health_requires_a_worker(monkeypatch):
    monkeypatch.setattr(
        celery_app,
        "connection_for_read",
        lambda: FakeConnection(),
    )
    monkeypatch.setattr(
        celery_app.control,
        "inspect",
        lambda timeout: FakeInspector({}),
    )

    result = check_celery()

    assert result["status"] == "degraded"
    assert result["workers"] == 0


def test_celery_health_reports_responding_workers(monkeypatch):
    monkeypatch.setattr(
        celery_app,
        "connection_for_read",
        lambda: FakeConnection(),
    )
    monkeypatch.setattr(
        celery_app.control,
        "inspect",
        lambda timeout: FakeInspector({
            "worker-b": {"ok": "pong"},
            "worker-a": {"ok": "pong"},
        }),
    )

    result = check_celery()

    assert result["status"] == "healthy"
    assert result["workers"] == 2
    assert result["worker_names"] == ["worker-a", "worker-b"]


def test_external_health_reports_recent_generation_failure(monkeypatch):
    from ai.premium_conversational_engine import PROVIDER_RUNTIME_STATE

    class FakeResponse:
        status_code = 200

    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_key_with_enough_characters")
    monkeypatch.setenv("AI_EXTERNAL_FALLBACK_ENABLED", "true")
    monkeypatch.setattr(
        "requests.get",
        lambda *args, **kwargs: FakeResponse(),
    )
    PROVIDER_RUNTIME_STATE.update(
        {
            "status": "degraded",
            "last_failure_at": __import__("time").time(),
            "last_error": "429 quota exceeded",
            "last_model": "llama-3.3-70b-versatile",
        }
    )

    result = check_external_apis()

    assert result["groq"]["status"] == "degraded"
    assert result["groq"]["models_endpoint"] == "healthy"
