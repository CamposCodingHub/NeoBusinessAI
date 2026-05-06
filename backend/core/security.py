"""
Security Utilities
==================
JWT, password hashing, e utilitários de segurança.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash de senha usando bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica senha contra hash - trunca em 72 bytes para bcrypt"""
    # bcrypt trunca senhas em 72 bytes, então precisamos truncar na verificação também
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        plain_password = password_bytes[:72].decode('utf-8', errors='ignore')
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: str,
    tenant_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Cria JWT access token.
    
    Args:
        user_id: ID do usuário
        tenant_id: ID do tenant
        role: Role do usuário
        expires_delta: Delta de expiração customizado
        
    Returns:
        JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verifica e decodifica JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Payload decodificado
        
    Raises:
        HTTPException: Se token inválido ou expirado
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Verificar tipo de token
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tipo de token inválido"
            )
        
        return payload
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {str(e)}"
        )


def create_refresh_token_payload(user_id: str) -> str:
    """Cria payload para refresh token (não JWT, apenas hash)"""
    import secrets
    return secrets.token_urlsafe(64)


def sanitize_filename(filename: str) -> str:
    """
    Sanitiza nome de arquivo para evitar path traversal.
    
    Args:
        filename: Nome original do arquivo
        
    Returns:
        Nome sanitizado
    """
    import re
    import os
    
    # Remove path traversal
    filename = os.path.basename(filename)
    
    # Remove caracteres perigosos
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Limita tamanho
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255 - len(ext)] + ext
    
    return filename


def validate_email(email: str) -> bool:
    """
    Valida formato de email.
    
    Args:
        email: Email a validar
        
    Returns:
        True se válido, False caso contrário
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def sanitize_html(html: str) -> str:
    """
    Sanitiza HTML para prevenir XSS.
    
    Args:
        html: HTML a sanitizar
        
    Returns:
        HTML sanitizado
    """
    from bleach import clean
    return clean(
        html,
        tags=['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li'],
        attributes={'a': ['href', 'title']},
        strip=True
    )


def sanitize_sql(query: str) -> str:
    """
    Detecta tentativas de SQL injection.
    
    Args:
        query: Query SQL
        
    Returns:
        Query sanitizada ou raises exception se detectado injection
        
    Raises:
        ValueError: Se detectado SQL injection
    """
    sql_keywords = [
        'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER',
        'CREATE', 'TRUNCATE', 'EXEC', 'EXECUTE', 'UNION',
        '--', '/*', '*/', ';', 'xp_', 'sp_'
    ]
    
    query_upper = query.upper()
    
    for keyword in sql_keywords:
        if keyword in query_upper:
            raise ValueError(f"SQL injection detected: {keyword}")
    
    return query


def generate_secure_token(length: int = 32) -> str:
    """Gera token criptograficamente seguro"""
    import secrets
    return secrets.token_urlsafe(length)


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str
) -> bool:
    """
    Verifica assinatura de webhook (HMAC-SHA256).
    
    Args:
        payload: Payload do webhook
        signature: Assinatura recebida
        secret: Segredo do webhook
        
    Returns:
        True se assinatura válida
    """
    import hmac
    import hashlib
    
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)
