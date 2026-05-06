"""
Módulo de Segurança NeoBusiness AI
=====================================
Autenticação, autorização, sanitização e proteção contra ataques.
"""

from .auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    require_auth,
    require_role,
    Role,
    get_password_hash,
    verify_password
)

from .sanitizers import (
    sanitize_input,
    sanitize_sql,
    sanitize_html,
    validate_email,
    validate_uuid,
    validate_file_path
)

from .rate_limiter import (
    rate_limit,
    RateLimitConfig,
    check_rate_limit,
    _rate_limiter,
    API_RATE_LIMIT,
    CHAT_RATE_LIMIT,
    UPLOAD_RATE_LIMIT,
    LOGIN_RATE_LIMIT
)

from .validators import (
    validate_schema,
    DocumentUploadSchema,
    ChatMessageSchema,
    UserCreateSchema,
    UserLoginSchema
)

__all__ = [
    # Auth
    'create_access_token',
    'create_refresh_token',
    'verify_token',
    'get_current_user',
    'require_auth',
    'require_role',
    'Role',
    'get_password_hash',
    'verify_password',
    # Sanitizers
    'sanitize_input',
    'sanitize_sql',
    'sanitize_html',
    'validate_email',
    'validate_uuid',
    'validate_file_path',
    # Rate Limiting
    'rate_limit',
    'RateLimitConfig',
    'check_rate_limit',
    '_rate_limiter',
    'API_RATE_LIMIT',
    'CHAT_RATE_LIMIT',
    'UPLOAD_RATE_LIMIT',
    'LOGIN_RATE_LIMIT',
    # Validators
    'validate_schema',
    'DocumentUploadSchema',
    'ChatMessageSchema',
    'UserCreateSchema',
    'UserLoginSchema',
]
