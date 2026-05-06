"""
Security Middleware para FastAPI
===================================
Middleware de segurança completo para proteção da aplicação.
"""

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging
import re
from typing import Optional

from security.auth import get_security_headers, get_cors_origins
from security.rate_limiter import _rate_limiter, API_RATE_LIMIT
from security.sanitizers import sanitize_input

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware de segurança principal
    Adiciona headers de segurança, rate limiting e logging
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.cors_origins = get_cors_origins()
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Gerar request ID para tracking
        request_id = f"{int(time.time() * 1000)}-{id(request)}"
        request.state.request_id = request_id
        
        try:
            # 1. Verificar CORS preflight
            if request.method == "OPTIONS":
                return self._handle_preflight(request)
            
            # 2. Verificar origem (CORS)
            origin = request.headers.get("origin")
            if origin and origin not in self.cors_origins:
                logger.warning(f"CORS blocked: {origin}")
                raise HTTPException(status_code=403, detail="Origem não permitida")
            
            # 3. Verificar Content-Type para POST/PUT/PATCH
            if request.method in ["POST", "PUT", "PATCH"]:
                content_type = request.headers.get("content-type", "")
                if not self._is_valid_content_type(content_type):
                    logger.warning(f"Invalid Content-Type: {content_type}")
                    raise HTTPException(status_code=415, detail="Content-Type não suportado")
            
            # 4. Rate limiting global por IP
            client_ip = self._get_client_ip(request)
            allowed, rate_info = _rate_limiter.check_rate_limit(
                f"ip:{client_ip}",
                API_RATE_LIMIT
            )
            
            if not allowed:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return Response(
                    content='{"detail":"Rate limit excedido"}',
                    status_code=429,
                    headers={
                        "Content-Type": "application/json",
                        "Retry-After": str(rate_info.get('retry_after', 60)),
                        **get_security_headers()
                    }
                )
            
            # 5. Verificar User-Agent suspeito
            user_agent = request.headers.get("user-agent", "")
            if self._is_suspicious_ua(user_agent):
                logger.warning(f"Suspicious User-Agent: {user_agent[:50]}")
            
            # 6. Sanitizar headers de entrada
            request = self._sanitize_request_headers(request)
            
            # 7. Log da requisição (sanitizado)
            self._log_request(request, client_ip)
            
            # 8. Processar requisição
            response = await call_next(request)
            
            # 9. Adicionar headers de segurança
            response.headers.update(get_security_headers())
            
            # 10. Adicionar headers de rate limit
            if 'remaining' in rate_info:
                response.headers['X-RateLimit-Limit'] = str(rate_info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(rate_info['remaining'])
            
            # 11. Adicionar CORS headers
            if origin and origin in self.cors_origins:
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Access-Control-Allow-Credentials'] = 'true'
            
            # 12. Log da resposta
            duration = time.time() - start_time
            self._log_response(request, response, duration)
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in security middleware: {e}", exc_info=True)
            return Response(
                content='{"detail":"Erro interno"}',
                status_code=500,
                headers=get_security_headers()
            )
    
    def _handle_preflight(self, request: Request) -> Response:
        """Responde a requisições OPTIONS (preflight)"""
        origin = request.headers.get("origin")
        
        if origin and origin not in self.cors_origins:
            raise HTTPException(status_code=403, detail="Origem não permitida")
        
        headers = {
            **get_security_headers(),
            'Access-Control-Allow-Origin': origin or '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
            'Access-Control-Allow-Headers': 'Authorization, Content-Type, X-Requested-With',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Max-Age': '86400',
        }
        
        return Response(content='', status_code=200, headers=headers)
    
    def _is_valid_content_type(self, content_type: str) -> bool:
        """Verifica se Content-Type é válido"""
        allowed_types = [
            'application/json',
            'application/x-www-form-urlencoded',
            'multipart/form-data',
            'text/plain',
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats',
        ]
        return any(allowed in content_type for allowed in allowed_types)
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtém IP do cliente considerando proxies"""
        # Verificar headers de proxy
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Pegar primeiro IP da lista
            return forwarded.split(',')[0].strip()
        
        real_ip = request.headers.get("X-Real-Ip")
        if real_ip:
            return real_ip
        
        # Fallback para conexão direta
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _is_suspicious_ua(self, user_agent: str) -> bool:
        """Detecta User-Agents suspeitos"""
        suspicious_patterns = [
            r'sqlmap',
            r'nikto',
            r'nessus',
            r'burp',
            r'dirbuster',
            r'gobuster',
            r'nmap',
            r'masscan',
            r'zgrab',
            r'w3af',
            r'arachni',
            r'owasp',
            r'wget',
            r'curl',
        ]
        ua_lower = user_agent.lower()
        return any(re.search(pattern, ua_lower) for pattern in suspicious_patterns)
    
    def _sanitize_request_headers(self, request: Request) -> Request:
        """Sanitiza headers de entrada"""
        # Sanitizar query parameters
        for key, value in request.query_params.items():
            if isinstance(value, str):
                request.query_params._dict[key] = sanitize_input(value, max_length=1000)
        
        return request
    
    def _log_request(self, request: Request, client_ip: str):
        """Log da requisição (com dados sensíveis mascarados)"""
        # Mascarar dados sensíveis no path
        path = request.url.path
        if '/email/' in path or '/documents/' in path:
            path = re.sub(r'(/[\w-]+){2,}$', '/...', path)
        
        logger.info(
            f"Request {request.state.request_id}: "
            f"{request.method} {path} - "
            f"IP: {self._mask_ip(client_ip)}"
        )
    
    def _log_response(self, request: Request, response: Response, duration: float):
        """Log da resposta"""
        logger.info(
            f"Response {request.state.request_id}: "
            f"Status {response.status_code} - "
            f"Duration: {duration:.3f}s"
        )
    
    def _mask_ip(self, ip: str) -> str:
        """Mascara IP para logging"""
        if '.' in ip:  # IPv4
            parts = ip.split('.')
            return f"{parts[0]}.{parts[1]}.*.*"
        return ip[:10] + "..."


class CORSMiddleware:
    """Middleware CORS customizado"""
    
    def __init__(self, app: ASGIApp, allow_origins: list = None):
        self.app = app
        self.allow_origins = allow_origins or get_cors_origins()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        origin = request.headers.get("origin")
        
        if origin and origin not in self.allow_origins:
            response = Response(
                content='{"detail":"Origem não permitida"}',
                status_code=403
            )
            await response(scope, receive, send)
            return
        
        await self.app(scope, receive, send)


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware para validação adicional de requisições
    """
    
    async def dispatch(self, request: Request, call_next):
        # Verificar tamanho do body para POST/PUT
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("content-length")
            if content_length:
                size = int(content_length)
                if size > 50 * 1024 * 1024:  # 50MB
                    raise HTTPException(status_code=413, detail="Payload muito grande")
        
        # Verificar query string
        if len(str(request.query_params)) > 2000:
            raise HTTPException(status_code=414, detail="Query string muito longa")
        
        return await call_next(request)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware para auditoria de segurança
    Loga todas as ações importantes
    """
    
    async def dispatch(self, request: Request, call_next):
        # Lista de endpoints sensíveis que precisam de log de auditoria
        sensitive_endpoints = [
            '/login',
            '/register',
            '/password-reset',
            '/documents/delete',
            '/admin',
        ]
        
        path = request.url.path
        should_audit = any(path.startswith(endpoint) for endpoint in sensitive_endpoints)
        
        if should_audit:
            client_ip = self._get_client_ip(request)
            user_id = getattr(request.state, 'user_id', 'anonymous')
            
            logger.warning(
                f"AUDIT: {request.method} {path} - "
                f"User: {user_id} - "
                f"IP: {client_ip}"
            )
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(',')[0].strip()
        
        real_ip = request.headers.get("X-Real-Ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"


# Função helper para aplicar todos os middlewares
def setup_security_middleware(app):
    """
    Configura todos os middlewares de segurança na aplicação FastAPI
    
    Usage:
        from fastapi import FastAPI
        from middleware.security_middleware import setup_security_middleware
        
        app = FastAPI()
        setup_security_middleware(app)
    """
    # Ordem é importante: primeiro os mais externos
    
    # 1. CORS (se necessário - FastAPI já tem built-in)
    from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware
    app.add_middleware(
        FastAPICORSMiddleware,
        allow_origins=get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 2. Request Validation
    app.add_middleware(RequestValidationMiddleware)
    
    # 3. Audit Logging
    app.add_middleware(AuditMiddleware)
    
    # 4. Security (rate limiting, headers, CORS)
    app.add_middleware(SecurityMiddleware)
    
    logger.info("Security middlewares configured successfully")
