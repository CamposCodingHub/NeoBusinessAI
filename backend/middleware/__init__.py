"""
Middleware Package
==================
Middlewares para FastAPI
"""

from .security_middleware import (
    SecurityMiddleware,
    CORSMiddleware,
    RequestValidationMiddleware,
    AuditMiddleware,
    setup_security_middleware,
)

# Aliases for older imports
SecurityHeadersMiddleware = SecurityMiddleware
setup_security_headers_middleware = setup_security_middleware

__all__ = [
    "SecurityMiddleware",
    "SecurityHeadersMiddleware",
    "CORSMiddleware",
    "RequestValidationMiddleware",
    "AuditMiddleware",
    "setup_security_middleware",
    "setup_security_headers_middleware",
]
