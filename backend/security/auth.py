"""
Sistema de Autenticação JWT
===========================
Autenticação segura com tokens JWT, refresh tokens e controle de acesso baseado em papéis (RBAC).
"""

import jwt
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt
import os
import secrets
import logging

# Configuração de logging
logger = logging.getLogger(__name__)

# Configurações JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Usar bcrypt diretamente (evita incompatibilidade passlib+bcrypt)

# Schema de segurança HTTP Bearer
security = HTTPBearer(auto_error=False)


class Role(str, Enum):
    """Papéis de usuário para RBAC"""
    USER = "user"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    ADMIN = "admin"


class TokenData:
    """Estrutura de dados do token"""
    def __init__(self, user_id: str, role: Role, permissions: list):
        self.user_id = user_id
        self.role = role
        self.permissions = permissions

    @property
    def id(self):
        """Compatibilidade com rotas legadas que esperam `current_user.id`."""
        try:
            return int(self.user_id)
        except (TypeError, ValueError):
            return self.user_id


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha corresponde ao hash - trunca em 72 bytes para bcrypt"""
    try:
        # Converte para bytes se necessário
        if isinstance(plain_password, str):
            plain_password = plain_password.encode('utf-8')
        # bcrypt trunca em 72 bytes, então precisamos truncar na verificação também
        if len(plain_password) > 72:
            plain_password = plain_password[:72]
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Gera hash seguro da senha usando bcrypt"""
    if isinstance(password, str):
        password = password.encode('utf-8')
    # Gera salt e hash
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password, salt)
    return hashed.decode('utf-8')


def create_access_token(
    user_id: str,
    role: Role = Role.USER,
    permissions: list = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Cria token JWT de acesso
    
    Args:
        user_id: ID único do usuário
        role: Papel do usuário (Role enum)
        permissions: Lista de permissões específicas
    
    Returns:
        Token JWT assinado
    """
    if permissions is None:
        permissions = []
    
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    payload = {
        "sub": str(user_id),  # Subject (user_id)
        "role": role.value,
        "permissions": permissions,
        "exp": expire,
        "iat": datetime.utcnow(),  # Issued at
        "jti": secrets.token_urlsafe(16),  # JWT ID único
        "type": "access"
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Access token criado para usuário: {user_id}")
    return token


def create_refresh_token(user_id: str) -> str:
    """
    Cria token de refresh para renovação de acesso
    
    Args:
        user_id: ID único do usuário
    
    Returns:
        Refresh token
    """
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": secrets.token_urlsafe(16),
        "type": "refresh"
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Refresh token criado para usuário: {user_id}")
    return token


def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """
    Verifica e decodifica token JWT
    
    Args:
        token: Token JWT
        token_type: Tipo esperado (access/refresh)
    
    Returns:
        Payload decodificado
    
    Raises:
        HTTPException: Se token inválido ou expirado
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verificar tipo de token
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=401,
                detail=f"Tipo de token inválido. Esperado: {token_type}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar se há subject
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Token inválido: sem identificação de usuário",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> TokenData:
    """
    Dependência FastAPI para obter usuário atual a partir do token
    
    Usage:
        @app.get("/protected")
        async def protected_route(current_user: TokenData = Depends(get_current_user)):
            return {"user_id": current_user.user_id}
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Cabeçalho de autorização ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar se token está na blacklist (revogado)
    from security.token_blacklist import is_token_blacklisted
    if is_token_blacklisted(credentials.credentials):
        raise HTTPException(
            status_code=401,
            detail="Token revogado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = verify_token(credentials.credentials, token_type="access")
    
    return TokenData(
        user_id=payload["sub"],
        role=Role(payload.get("role", "user")),
        permissions=payload.get("permissions", [])
    )


def require_auth(func):
    """
    Decorator para exigir autenticação em rotas
    
    Usage:
        @app.get("/admin-only")
        @require_auth
        async def admin_route(current_user: TokenData = Depends(get_current_user)):
            return {"message": "Acesso permitido"}
    """
    async def wrapper(*args, current_user: TokenData = Depends(get_current_user), **kwargs):
        return await func(*args, current_user=current_user, **kwargs)
    return wrapper


def require_role(required_role: Role):
    """
    Cria dependência para exigir papel específico
    
    Usage:
        @app.get("/admin-only")
        async def admin_only(
            current_user: TokenData = Depends(require_role(Role.ADMIN))
        ):
            return {"message": "Acesso administrativo"}
    """
    async def role_checker(
        current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        # Hierarquia de papéis (admin > enterprise > premium > user)
        role_hierarchy = {
            Role.USER: 1,
            Role.PREMIUM: 2,
            Role.ENTERPRISE: 3,
            Role.ADMIN: 4
        }
        
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=403,
                detail=f"Acesso negado. Requerido: {required_role.value}"
            )
        
        return current_user
    
    return role_checker


def require_permission(permission: str):
    """
    Cria dependência para exigir permissão específica
    
    Usage:
        @app.post("/documents/delete")
        async def delete_doc(
            current_user: TokenData = Depends(require_permission("documents:delete"))
        ):
            return {"message": "Documento deletado"}
    """
    async def permission_checker(
        current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        if permission not in current_user.permissions and current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=403,
                detail=f"Permissão negada: {permission}"
            )
        return current_user
    
    return permission_checker


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Optional[TokenData]:
    """
    Obtém usuário se autenticado, ou None se não autenticado
    Útil para rotas que funcionam para usuários logados e anônimos
    """
    if not credentials:
        return None
    
    try:
        payload = verify_token(credentials.credentials, token_type="access")
        return TokenData(
            user_id=payload["sub"],
            role=Role(payload.get("role", "user")),
            permissions=payload.get("permissions", [])
        )
    except HTTPException:
        return None


# Funções utilitárias para hash seguro de dados sensíveis
def hash_sensitive_data(data: str) -> str:
    """Hash SHA-256 para dados sensíveis (logs, etc)"""
    import hashlib
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def generate_secure_id() -> str:
    """Gera ID seguro criptograficamente"""
    return secrets.token_urlsafe(32)


# Configuração de CORS seguro
def get_cors_origins() -> list:
    """Retorna origens CORS permitidas (produção)"""
    origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    return [origin.strip() for origin in origins_str.split(",")]


# Headers de segurança
def get_security_headers() -> dict:
    """Retorna headers de segurança recomendados"""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
    }
