"""
Prometheus Metrics para Monitoramento
=======================================
Métricas customizadas para observabilidade
Integração com Prometheus + Grafana
"""

from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
from prometheus_client import start_http_server as prometheus_start_http_server
from typing import Optional
import logging

logger = logging.getLogger(__name__)


# Registry customizado para não conflitar com outros
registry = CollectorRegistry()


# ==================== COUNTERS ====================
# Contadores para eventos que só aumentam

document_processed_total = Counter(
    'documents_processed_total',
    'Total de documentos processados',
    ['status', 'document_type'],
    registry=registry
)

api_requests_total = Counter(
    'api_requests_total',
    'Total de requisições à API',
    ['endpoint', 'method', 'status'],
    registry=registry
)

ai_responses_total = Counter(
    'ai_responses_total',
    'Total de respostas de IA geradas',
    ['model', 'style', 'has_legal_entities'],
    registry=registry
)

ai_provider_requests_total = Counter(
    "ai_provider_requests_total",
    "Tentativas de inferencia por provedor",
    ["provider", "model", "route", "status"],
    registry=registry,
)

ai_provider_tokens_total = Counter(
    "ai_provider_tokens_total",
    "Tokens processados por provedor e tipo",
    ["provider", "model", "token_type"],
    registry=registry,
)

ocr_operations_total = Counter(
    'ocr_operations_total',
    'Total de operações de OCR',
    ['status', 'engine'],
    registry=registry
)

cache_hits_total = Counter(
    'cache_hits_total',
    'Total de hits no cache',
    ['cache_type'],
    registry=registry
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total de misses no cache',
    ['cache_type'],
    registry=registry
)

user_registrations_total = Counter(
    'user_registrations_total',
    'Total de registros de usuários',
    ['plan_tier'],
    registry=registry
)

# ==================== HISTOGRAMS ====================
# Histogramas para medir latência e distribuição

document_processing_duration = Histogram(
    'document_processing_duration_seconds',
    'Duração do processamento de documentos',
    ['stage'],  # ingestion, normalization, ocr, extraction, validation
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
    registry=registry
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'Duração das requisições à API',
    ['endpoint', 'method'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=registry
)

ai_response_duration = Histogram(
    'ai_response_duration_seconds',
    'Duração das respostas de IA',
    ['model', 'style'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0],
    registry=registry
)

ai_provider_latency = Histogram(
    "ai_provider_latency_seconds",
    "Latencia de inferencia por provedor",
    ["provider", "model", "route"],
    buckets=[0.5, 1, 2, 5, 10, 20, 40, 90, 180, 600],
    registry=registry,
)

database_query_duration = Histogram(
    'database_query_duration_seconds',
    'Duração de queries ao banco de dados',
    ['operation', 'table'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5],
    registry=registry
)

# ==================== GAUGES ====================
# Gauges para valores que podem subir e descer

active_users = Gauge(
    'active_users',
    'Número de usuários ativos',
    registry=registry
)

documents_in_queue = Gauge(
    'documents_in_queue',
    'Número de documentos na fila de processamento',
    registry=registry
)

processing_queue_size = Gauge(
    'processing_queue_size',
    'Tamanho da fila de processamento',
    registry=registry
)

memory_usage_bytes = Gauge(
    'memory_usage_bytes',
    'Uso de memória em bytes',
    registry=registry
)

cpu_usage_percent = Gauge(
    'cpu_usage_percent',
    'Uso de CPU em percentual',
    registry=registry
)

disk_usage_percent = Gauge(
    'disk_usage_percent',
    'Uso de disco em percentual',
    registry=registry
)

cache_size = Gauge(
    'cache_size',
    'Tamanho do cache em itens',
    ['cache_type'],
    registry=registry
)

# ==================== INFO ====================
# Informações estáticas sobre a aplicação

app_info = Info(
    'application_info',
    'Informações da aplicação',
    registry=registry
)


# ==================== FUNÇÕES DE MEDIÇÃO ====================

def track_document_processing(stage: str, duration: float, status: str = "success", document_type: str = "unknown"):
    """Rastreia processamento de documento"""
    document_processed_total.labels(status=status, document_type=document_type).inc()
    document_processing_duration.labels(stage=stage).observe(duration)


def track_api_request(endpoint: str, method: str, status: int, duration: float):
    """Rastreia requisição à API"""
    api_requests_total.labels(endpoint=endpoint, method=method, status=status).inc()
    api_request_duration.labels(endpoint=endpoint, method=method).observe(duration)


def track_ai_response(model: str, style: str, duration: float, has_legal_entities: bool = False):
    """Rastreia resposta de IA"""
    ai_responses_total.labels(model=model, style=style, has_legal_entities=has_legal_entities).inc()
    ai_response_duration.labels(model=model, style=style).observe(duration)


def track_ai_provider_request(
    *,
    provider: str,
    model: str,
    route: str,
    status: str,
    latency_ms: int,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
):
    ai_provider_requests_total.labels(
        provider=provider,
        model=model,
        route=route,
        status=status,
    ).inc()
    ai_provider_latency.labels(
        provider=provider,
        model=model,
        route=route,
    ).observe(max(0, latency_ms) / 1000)
    ai_provider_tokens_total.labels(
        provider=provider,
        model=model,
        token_type="prompt",
    ).inc(max(0, prompt_tokens))
    ai_provider_tokens_total.labels(
        provider=provider,
        model=model,
        token_type="completion",
    ).inc(max(0, completion_tokens))


def track_ocr_operation(status: str, engine: str = "tesseract"):
    """Rastreia operação de OCR"""
    ocr_operations_total.labels(status=status, engine=engine).inc()


def track_cache_hit(cache_type: str):
    """Rastreia hit no cache"""
    cache_hits_total.labels(cache_type=cache_type).inc()


def track_cache_miss(cache_type: str):
    """Rastreia miss no cache"""
    cache_misses_total.labels(cache_type=cache_type).inc()


def track_user_registration(plan_tier: str):
    """Rastreia registro de usuário"""
    user_registrations_total.labels(plan_tier=plan_tier).inc()


def update_active_users(count: int):
    """Atualiza contador de usuários ativos"""
    active_users.set(count)


def update_documents_in_queue(count: int):
    """Atualiza contador de documentos na fila"""
    documents_in_queue.set(count)


def update_cache_size(cache_type: str, size: int):
    """Atualiza tamanho do cache"""
    cache_size.labels(cache_type=cache_type).set(size)


def update_system_metrics(memory_bytes: int, cpu_percent: float, disk_percent: float):
    """Atualiza métricas do sistema"""
    memory_usage_bytes.set(memory_bytes)
    cpu_usage_percent.set(cpu_percent)
    disk_usage_percent.set(disk_percent)


def set_app_info(version: str, environment: str, deployment: str):
    """Define informações da aplicação"""
    app_info.info({
        'version': version,
        'environment': environment,
        'deployment': deployment
    })


# ==================== EXPORTADOR ====================

def get_metrics() -> str:
    """Retorna métricas em formato Prometheus"""
    return generate_latest(registry)


def start_metrics_server(port: int = 9090):
    """Inicia servidor HTTP para métricas"""
    try:
        prometheus_start_http_server(port, registry=registry)
        logger.info(f"✅ Prometheus metrics server iniciado na porta {port}")
    except Exception as e:
        logger.error(f"❌ Falha ao iniciar metrics server: {e}")


# ==================== DECORADORES ====================

def timed_api_request(endpoint: str, method: str = "GET"):
    """Decorator para medir tempo de requisição API"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start = time.time()
            try:
                result = func(*args, **kwargs)
                status = 200
                return result
            except Exception as e:
                status = 500
                raise
            finally:
                duration = time.time() - start
                track_api_request(endpoint, method, status, duration)
        return wrapper
    return decorator


def timed_ai_response(model: str = "groq"):
    """Decorator para medir tempo de resposta de IA"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            import time
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                style = result.get('style', 'unknown')
                has_entities = len(result.get('v2_metadata', {}).get('legal_entities_detected', {})) > 0
                duration = time.time() - start
                track_ai_response(model, style, duration, has_entities)
                return result
            except Exception as e:
                duration = time.time() - start
                track_ai_response(model, 'error', duration, False)
                raise
        return wrapper
    return decorator


# ==================== INICIALIZAÇÃO ====================

def init_metrics(version: str = "1.0.0", environment: str = "development"):
    """Inicializa métricas"""
    set_app_info(version, environment, "production")
    logger.info("✅ Prometheus metrics inicializadas")
