"""
Proteção CSRF (Cross-Site Request Forgery)
Tokens CSRF para rotas de mutação
"""

import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from fastapi import HTTPException, Request, Header
from typing import Optional

# Tempo de expiração do token CSRF (1 hora)
CSRF_TOKEN_EXPIRY = 3600  # segundos

# Em produção, usar Redis. Aqui usando dicionário em memória para simplicidade
_csrf_tokens = {}

def generate_csrf_token(session_id: str) -> str:
    """
    Gera um novo token CSRF para a sessão
    """
    token = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(seconds=CSRF_TOKEN_EXPIRY)
    
    _csrf_tokens[session_id] = {
        "token": token,
        "expiry": expiry,
        "used": False
    }
    
    return token

def validate_csrf_token(session_id: str, token: str) -> bool:
    """
    Valida se o token CSRF é válido para a sessão
    """
    if not session_id or not token:
        return False
    
    stored = _csrf_tokens.get(session_id)
    if not stored:
        return False
    
    # Verificar expiração
    if datetime.utcnow() > stored["expiry"]:
        # Limpar token expirado
        del _csrf_tokens[session_id]
        return False
    
    # Verificar se token corresponde
    if not hmac.compare_digest(stored["token"], token):
        return False
    
    # Marcar como usado (one-time use)
    stored["used"] = True
    
    return True

def clear_csrf_token(session_id: str):
    """
    Remove o token CSRF da sessão (logout)
    """
    if session_id in _csrf_tokens:
        del _csrf_tokens[session_id]

def get_csrf_token(session_id: str) -> Optional[str]:
    """
    Retorna o token CSRF existente ou gera novo
    """
    stored = _csrf_tokens.get(session_id)
    
    if stored and datetime.utcnow() < stored["expiry"]:
        return stored["token"]
    
    # Gerar novo se não existe ou expirou
    return generate_csrf_token(session_id)

# Decorador para verificar CSRF em rotas de mutação
async def verify_csrf_token(
    request: Request,
    x_csrf_token: Optional[str] = Header(None, alias="X-CSRF-Token")
) -> bool:
    """
    Verifica token CSRF em requisições de mutação
    Usar como dependência nas rotas POST/PUT/DELETE/PATCH
    """
    # Obter session_id do token JWT ou cookie
    auth_header = request.headers.get("Authorization", "")
    session_id = None
    
    if auth_header.startswith("Bearer "):
        # Usar parte do token como session_id
        token = auth_header[7:]
        session_id = hashlib.sha256(token.encode()).hexdigest()[:32]
    
    if not session_id:
        raise HTTPException(
            status_code=403,
            detail="CSRF: Sessão não identificada"
        )
    
    if not x_csrf_token:
        raise HTTPException(
            status_code=403,
            detail="CSRF: Token não fornecido (header X-CSRF-Token necessário)"
        )
    
    if not validate_csrf_token(session_id, x_csrf_token):
        raise HTTPException(
            status_code=403,
            detail="CSRF: Token inválido ou expirado"
        )
    
    return True

# Middleware para verificar CSRF automaticamente em mutações
class CSRFMiddleware:
    def __init__(self, app, exempt_paths=None):
        self.app = app
        self.exempt_paths = exempt_paths or [
            "/auth/login",
            "/auth/register",
            "/auth/refresh",
            "/health",
            "/docs",
            "/openapi.json"
        ]
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Verificar apenas métodos de mutação
            if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
                path = request.url.path
                
                # Pular paths isentos
                if any(path.startswith(exempt) for exempt in self.exempt_paths):
                    await self.app(scope, receive, send)
                    return
                
                # Verificar CSRF token
                try:
                    await verify_csrf_token(request)
                except HTTPException as e:
                    # Retornar erro JSON
                    response_body = f'{{"detail": "{e.detail}"}}'.encode()
                    await send({
                        "type": "http.response.start",
                        "status": e.status_code,
                        "headers": [(b"content-type", b"application/json")]
                    })
                    await send({
                        "type": "http.response.body",
                        "body": response_body
                    })
                    return
        
        await self.app(scope, receive, send)
