"""
Monitoramento e Observabilidade
================================
Sentry para error tracking, métricas customizadas
"""

import logging
import os
import time
from functools import wraps
from typing import Callable, Any, Optional
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class MonitoringManager:
    """
    Gerenciador de monitoramento
    - Error tracking com Sentry
    - Métricas de performance
    - Health checks
    """
    
    def __init__(self, sentry_dsn: Optional[str] = None):
        self.sentry_dsn = sentry_dsn
        self.metrics = {}
        self.enabled = True
        
        if sentry_dsn:
            try:
                import sentry_sdk
                sentry_sdk.init(
                    dsn=sentry_dsn,
                    traces_sample_rate=0.1,
                    profiles_sample_rate=0.1,
                    environment="production"
                )
                logger.info("✅ Sentry monitoring initialized")
            except ImportError:
                logger.warning("sentry-sdk not installed, monitoring disabled")
                self.enabled = False
            except Exception as e:
                logger.warning(f"Sentry initialization failed: {e}")
                self.enabled = False
    
    def track_error(self, error: Exception, context: Optional[dict] = None):
        """Rastreia erro no Sentry"""
        if not self.enabled:
            return
        
        try:
            import sentry_sdk
            with sentry_sdk.push_scope() as scope:
                if context:
                    for key, value in context.items():
                        scope.set_extra(key, value)
                sentry_sdk.capture_exception(error)
                logger.error(f"Error tracked: {error}")
        except Exception as e:
            logger.warning(f"Failed to track error: {e}")
    
    def track_message(self, message: str, level: str = "info", context: Optional[dict] = None):
        """Rastreia mensagem no Sentry"""
        if not self.enabled:
            return
        
        try:
            import sentry_sdk
            with sentry_sdk.push_scope() as scope:
                if context:
                    for key, value in context.items():
                        scope.set_extra(key, value)
                sentry_sdk.capture_message(message, level=level)
                logger.info(f"Message tracked: {message}")
        except Exception as e:
            logger.warning(f"Failed to track message: {e}")
    
    def increment_metric(self, metric_name: str, value: float = 1.0, tags: Optional[dict] = None):
        """Incrementa métrica"""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = {'value': 0, 'count': 0, 'tags': {}}
        
        self.metrics[metric_name]['value'] += value
        self.metrics[metric_name]['count'] += 1
        if tags:
            self.metrics[metric_name]['tags'].update(tags)
    
    def timing(self, metric_name: str, tags: Optional[dict] = None):
        """Decorator para medir tempo de execução"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    self.increment_metric(f"{metric_name}.duration", duration, tags)
                    self.increment_metric(f"{metric_name}.success", 1, tags)
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    self.increment_metric(f"{metric_name}.duration", duration, tags)
                    self.increment_metric(f"{metric_name}.error", 1, tags)
                    self.track_error(e, {'metric': metric_name, 'duration': duration})
                    raise
            return wrapper
        return decorator
    
    @contextmanager
    def track_operation(self, operation_name: str, tags: Optional[dict] = None):
        """Context manager para rastrear operações"""
        start_time = time.time()
        try:
            yield
            duration = time.time() - start_time
            self.increment_metric(f"{operation_name}.duration", duration, tags)
            self.increment_metric(f"{operation_name}.success", 1, tags)
        except Exception as e:
            duration = time.time() - start_time
            self.increment_metric(f"{operation_name}.duration", duration, tags)
            self.increment_metric(f"{operation_name}.error", 1, tags)
            self.track_error(e, {'operation': operation_name, 'duration': duration})
            raise
    
    def get_metrics_summary(self) -> dict:
        """Retorna resumo de métricas"""
        return {
            'metrics': self.metrics,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def health_check(self) -> dict:
        """Health check do sistema"""
        health = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {}
        }
        
        # Check Sentry
        health['checks']['sentry'] = {
            'status': 'connected' if self.enabled else 'disabled',
            'dsn_configured': bool(self.sentry_dsn)
        }
        
        # Check Database
        try:
            from database import engine
            engine.connect()
            health['checks']['database'] = {'status': 'connected'}
        except Exception as e:
            health['checks']['database'] = {'status': 'error', 'error': str(e)}
            health['status'] = 'unhealthy'
        
        # Check Redis
        try:
            from cache_manager import cache_manager
            if cache_manager.redis_client:
                cache_manager.redis_client.ping()
                health['checks']['redis'] = {'status': 'connected'}
            else:
                health['checks']['redis'] = {'status': 'disabled'}
        except Exception as e:
            health['checks']['redis'] = {'status': 'error', 'error': str(e)}
        
        return health


# Instância global
from config import settings

monitoring = MonitoringManager(
    sentry_dsn=getattr(settings, 'SENTRY_DSN', None) or os.getenv('SENTRY_DSN')
)


# Decorators convenientes
def track_error(context: Optional[dict] = None):
    """Decorator para rastrear erros"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                monitoring.track_error(e, context or {})
                raise
        return wrapper
    return decorator


def track_timing(metric_name: str, tags: Optional[dict] = None):
    """Decorator para rastrear tempo de execução"""
    return monitoring.timing(metric_name, tags)
