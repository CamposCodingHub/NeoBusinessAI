"""
Celery Configuration - LexScan IA
Configuração centralizada do Celery + Redis
"""

import os

# Redis Configuration
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Celery Configuration
celery_config = {
    'broker_url': REDIS_URL,
    'result_backend': REDIS_URL,
    'broker_connection_retry_on_startup': True,
    'broker_transport_options': {'visibility_timeout': 3600},
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'America/Sao_Paulo',
    'enable_utc': True,
    'task_track_started': True,
    'task_acks_late': True,
    'task_reject_on_worker_lost': True,
    'task_time_limit': 600,  # 10 minutos
    'task_soft_time_limit': 300,  # 5 minutos (warning)
    'worker_prefetch_multiplier': 1,
    'worker_max_tasks_per_child': 1000,
    'broker_connection_max_retries': 10,
    'result_expires': 86400,
}

# Task Routes (opcional - para priorização)
task_routes = {
    'tasks.system_health_probe': {'queue': 'celery'},
    'tasks.process_document_async': {'queue': 'processing'},
    'tasks.process_document_path_async': {'queue': 'processing'},
    'tasks.process_deep_research_job': {'queue': 'processing'},
    'tasks.index_document_knowledge_async': {'queue': 'maintenance'},
    'tasks.generate_report_async': {'queue': 'reports'},
    'tasks.send_email_async': {'queue': 'notifications'},
    'tasks.check_and_notify_deadlines': {'queue': 'notifications'},
    'tasks.cleanup_old_documents': {'queue': 'maintenance'},
}
