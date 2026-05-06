"""
Health Check Routes - Monitoramento de Saúde do Sistema
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
import redis
import os
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
        from celery import Celery
        celery_app = Celery('tasks')
        # Tentar conectar ao broker
        with celery_app.connection() as conn:
            conn.connect()
        return {"status": "healthy", "message": "Celery disponível"}
    except Exception as e:
        return {"status": "degraded", "message": f"Celery não disponível: {str(e)}"}

def check_external_apis() -> Dict[str, Any]:
    """Verifica APIs externas"""
    results = {}
    
    # Groq API
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
                results["groq"] = {"status": "healthy"}
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
    
    # Determinar status geral
    all_healthy = all(
        check.get("status") == "healthy" 
        for check in [checks["database"], checks["redis"]]
    )
    
    any_unhealthy = any(
        check.get("status") == "unhealthy"
        for check in checks.values()
        if isinstance(check, dict) and "status" in check
    )
    
    if any_unhealthy:
        overall_status = "unhealthy"
    elif all_healthy:
        overall_status = "healthy"
    else:
        overall_status = "degraded"
    
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
