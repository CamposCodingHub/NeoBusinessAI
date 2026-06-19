"""
Health Check Routes - Monitoramento de Saúde do Sistema
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
import redis
import os
import time
from datetime import datetime
from typing import Dict, Any

router = APIRouter(prefix="/health", tags=["Health"])

# Redis connection
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

def check_redis() -> Dict[str, Any]:
    """Verifica conexão com Redis"""
    try:
        r = redis.from_url(REDIS_URL, socket_connect_timeout=2)
        r.ping()
        return {"status": "healthy", "message": "Redis conectado"}
    except Exception as e:
        return {"status": "unhealthy", "message": f"Redis erro: {str(e)}"}

def check_database() -> Dict[str, Any]:
    """Verifica conexão com banco de dados"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "healthy", "message": "PostgreSQL conectado"}
    except Exception as e:
        return {"status": "unhealthy", "message": f"DB erro: {str(e)}"}

def check_celery() -> Dict[str, Any]:
    """Verifica status do Celery"""
    try:
        from tasks import app as celery_app

        with celery_app.connection_for_read() as conn:
            conn.connect()

        workers = celery_app.control.inspect(timeout=1).ping() or {}
        if not workers:
            return {
                "status": "degraded",
                "message": "Broker conectado, mas nenhum worker respondeu",
                "workers": 0,
            }

        return {
            "status": "healthy",
            "message": "Broker e workers Celery conectados",
            "workers": len(workers),
            "worker_names": sorted(workers),
        }
    except Exception as e:
        return {"status": "degraded", "message": f"Celery não disponível: {str(e)}"}

def check_external_apis() -> Dict[str, Any]:
    """Verifica APIs externas"""
    results = {}

    sovereign_enabled = (
        os.getenv("AI_SOVEREIGN_ENABLED", "true").strip().lower()
        in {"1", "true", "yes", "on"}
    )
    if sovereign_enabled:
        try:
            import requests

            base_url = os.getenv(
                "LOCAL_AI_BASE_URL",
                "http://127.0.0.1:11434/v1",
            ).rstrip("/").removesuffix("/v1")
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            payload = response.json() if response.status_code == 200 else {}
            model_names = [
                item.get("name")
                for item in payload.get("models", [])
                if item.get("name")
            ]
            required_models = {
                os.getenv("LOCAL_AI_FAST_MODEL", "qwen2.5-coder:1.5b"),
                os.getenv(
                    "LOCAL_AI_QUICK_MODEL",
                    "lex-juridica-instant:1.5b",
                ),
                os.getenv(
                    "LOCAL_AI_BALANCED_MODEL",
                    "lex-juridica-rapida:3b",
                ),
                os.getenv("LOCAL_AI_DEEP_MODEL", "lex-juridica:14b"),
                os.getenv(
                    "LOCAL_AI_EMBEDDING_MODEL",
                    "nomic-embed-text",
                ),
            }
            missing = sorted(
                model
                for model in required_models
                if model not in model_names
                and not any(
                    available.startswith(f"{model}:")
                    for available in model_names
                )
            )
            results["sovereign_ai"] = {
                "status": (
                    "healthy"
                    if response.status_code == 200 and not missing
                    else "degraded"
                ),
                "endpoint": base_url,
                "models": model_names,
                "missing_models": missing,
                "routing_policy": os.getenv(
                    "AI_ROUTING_POLICY",
                    "local_only",
                ),
            }
        except Exception as exc:
            results["sovereign_ai"] = {
                "status": "unhealthy",
                "message": str(exc),
            }
    
    # Groq API
    external_fallback_enabled = (
        os.getenv("AI_EXTERNAL_FALLBACK_ENABLED", "false").strip().lower()
        in {"1", "true", "yes", "on"}
    )
    if not external_fallback_enabled:
        results["groq"] = {
            "status": "disabled",
            "message": "Contingencia externa desligada por politica local_only",
        }
        return results

    try:
        import requests
        GROQ_API_KEY = os.getenv('GROQ_API_KEY')
        if GROQ_API_KEY:
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
            response = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                from ai.premium_conversational_engine import (
                    PROVIDER_RUNTIME_STATE,
                )

                runtime_status = dict(PROVIDER_RUNTIME_STATE)
                recent_failure = (
                    runtime_status.get("status") == "degraded"
                    and runtime_status.get("last_failure_at")
                    and time.time() - runtime_status["last_failure_at"] < 900
                )
                results["groq"] = {
                    "status": "degraded" if recent_failure else "healthy",
                    "models_endpoint": "healthy",
                    "generation_runtime": runtime_status,
                }
            else:
                results["groq"] = {"status": "degraded", "code": response.status_code}
        else:
            results["groq"] = {"status": "unhealthy", "message": "API key não configurada"}
    except Exception as e:
        results["groq"] = {"status": "unhealthy", "message": str(e)}
    
    return results

@router.get("/")
async def health_check():
    """
    Health check básico - retorna status geral
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "jurisflow-api",
        "version": "1.0.0"
    }

@router.get("/detailed")
async def detailed_health_check():
    """
    Health check detalhado - verifica todos os componentes
    """
    checks = {
        "database": check_database(),
        "redis": check_redis(),
        "celery": check_celery(),
        "external_apis": check_external_apis()
    }
    
    component_checks = [
        checks["database"],
        checks["redis"],
        checks["celery"],
        *[
            check
            for check in checks["external_apis"].values()
            if check.get("status") != "disabled"
        ],
    ]
    any_unhealthy = any(
        check.get("status") == "unhealthy" for check in component_checks
    )
    any_degraded = any(
        check.get("status") == "degraded" for check in component_checks
    )

    if any_unhealthy:
        overall_status = "unhealthy"
    elif any_degraded:
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }

@router.get("/ready")
async def readiness_check():
    """
    Readiness check - verifica se pronto para receber tráfego
    """
    db_check = check_database()
    
    if db_check["status"] != "healthy":
        raise HTTPException(
            status_code=503,
            detail={"status": "not_ready", "reason": "database_unavailable"}
        )
    
    return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}

@router.get("/live")
async def liveness_check():
    """
    Liveness check - verifica se aplicação está viva
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}
