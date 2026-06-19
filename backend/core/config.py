"""
Core Configuration
==================
Configurações centralizadas com suporte a múltiplos ambientes.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "NeoBusiness AI"
    VERSION: str = "2.0.0"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/neobusiness"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Storage (R2/S3)
    STORAGE_BUCKET: str = "neobusiness-documents"
    STORAGE_REGION: str = "auto"
    STORAGE_ACCESS_KEY: str = ""
    STORAGE_SECRET_KEY: str = ""
    STORAGE_ENDPOINT: str = ""
    
    # Mercado Pago
    MERCADO_PAGO_ACCESS_TOKEN: str = ""
    MERCADO_PAGO_WEBHOOK_SECRET: str = ""
    MERCADO_PAGO_PUBLIC_KEY: str = ""
    
    # AI (OpenAI/Anthropic)
    AI_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    AI_MODEL: str = "gpt-4-turbo-preview"
    AI_MAX_TOKENS: int = 4096
    AI_TEMPERATURE: float = 0.7
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@neobusiness.ai"
    
    # Rate Limiting
    RATE_LIMIT_LOGIN_ATTEMPTS: int = 5
    RATE_LIMIT_LOGIN_WINDOW: int = 900  # 15 minutos
    RATE_LIMIT_API_REQUESTS: int = 1000
    RATE_LIMIT_API_WINDOW: int = 60  # 1 minuto
    RATE_LIMIT_AI_REQUESTS: int = 100
    RATE_LIMIT_AI_WINDOW: int = 60
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://neobusiness.ai",
    ]
    
    # Observability
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_ENABLED: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Feature Flags
    ENABLE_REGISTRATION: bool = True
    ENABLE_BILLING: bool = True
    ENABLE_AI: bool = True
    
@lru_cache()
def get_settings() -> Settings:
    """Retorna configurações cached"""
    return Settings()


settings = get_settings()
