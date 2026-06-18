"""
Configuração Centralizada com Validação Rigorosa
===============================================
Valida todas as variáveis de ambiente no startup.
Falha rápido se configuração estiver incompleta.
"""

import os
from typing import Optional
from pydantic import BaseSettings, Field, validator
from functools import lru_cache


class Settings(BaseSettings):
    """Configurações da aplicação com validação"""
    
    # ==================== DATABASE ====================
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    
    @validator('DATABASE_URL')
    def database_must_be_postgres(cls, v):
        """SQLite não é permitido em produção"""
        if v.startswith('sqlite'):
            raise ValueError(
                'SQLite não é permitido em produção. '
                'Use PostgreSQL: postgresql://user:pass@host:port/dbname'
            )
        if not v.startswith('postgresql'):
            raise ValueError(
                'Apenas PostgreSQL é suportado. '
                'Formato: postgresql://user:pass@host:port/dbname'
            )
        return v
    
    # ==================== AI / LLM ====================
    GROQ_API_KEY: str = Field(..., description="Groq API key para IA")
    OPENAI_API_KEY: Optional[str] = Field(None, description="OpenAI API key (opcional)")
    ANTHROPIC_API_KEY: Optional[str] = Field(None, description="Anthropic API key (opcional)")
    
    @validator('GROQ_API_KEY')
    def groq_key_must_be_valid(cls, v):
        if not v or len(v) < 20:
            raise ValueError('GROQ_API_KEY inválida')
        return v
    
    # ==================== FIREBASE ====================
    FIREBASE_PROJECT_ID: str = Field(..., description="Firebase project ID")
    FIREBASE_PRIVATE_KEY: str = Field(..., description="Firebase private key (JSON)")
    FIREBASE_CLIENT_EMAIL: str = Field(..., description="Firebase client email")
    
    @validator('FIREBASE_PRIVATE_KEY')
    def firebase_key_must_be_valid(cls, v):
        if not v or '-----BEGIN PRIVATE KEY-----' not in v:
            raise ValueError('FIREBASE_PRIVATE_KEY inválida. Deve ser uma chave PEM completa.')
        return v
    
    # ==================== STRIPE (Pagamentos) ====================
    STRIPE_SECRET_KEY: Optional[str] = Field(None, description="Stripe secret key")
    STRIPE_PUBLISHABLE_KEY: Optional[str] = Field(None, description="Stripe publishable key")
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(None, description="Stripe webhook secret")
    
    # ==================== SMTP (Email) ====================
    SMTP_SERVER: Optional[str] = Field(None, description="SMTP server (ex: smtp.gmail.com)")
    SMTP_PORT: Optional[int] = Field(587, description="SMTP port")
    SMTP_USERNAME: Optional[str] = Field(None, description="SMTP username")
    SMTP_PASSWORD: Optional[str] = Field(None, description="SMTP password")
    
    # ==================== REDIS (Cache) ====================
    REDIS_URL: Optional[str] = Field(None, description="Redis connection string")
    
    # ==================== APLICAÇÃO ====================
    ENVIRONMENT: str = Field("development", description="Environment: development, staging, production")
    DEBUG: bool = Field(False, description="Debug mode")
    LOG_LEVEL: str = Field("INFO", description="Log level: DEBUG, INFO, WARNING, ERROR")
    
    @validator('ENVIRONMENT')
    def environment_must_be_valid(cls, v):
        valid_envs = ['development', 'staging', 'production']
        if v.lower() not in valid_envs:
            raise ValueError(f'ENVIRONMENT deve ser um de: {valid_envs}')
        return v.lower()
    
    # ==================== SEGURANÇA ====================
    SECRET_KEY: str = Field(..., description="Secret key para JWT (mínimo 32 caracteres)")
    
    @validator('SECRET_KEY')
    def secret_key_must_be_strong(cls, v):
        if len(v) < 32:
            raise ValueError('SECRET_KEY deve ter pelo menos 32 caracteres')
        return v
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, description="Token expiration in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(7, description="Refresh token expiration in days")
    
    # ==================== LIMITES ====================
    MAX_FILE_SIZE_MB: int = Field(50, description="Maximum file size in MB")
    MAX_DOCUMENTS_PER_USER: int = Field(100, description="Max documents per user (free tier)")
    
    # ==================== CORS ====================
    CORS_ORIGINS: str = Field("*", description="CORS origins (comma-separated)")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna configurações validadas (cached).
    Falha imediatamente se configuração estiver inválida.
    """
    try:
        return Settings()
    except Exception as e:
        print("=" * 80)
        print("❌ ERRO CRÍTICO: Configuração inválida")
        print("=" * 80)
        print(f"Erro: {e}")
        print("\nPor favor, verifique seu arquivo .env")
        print("Use .env.example como referência")
        print("=" * 80)
        raise


# Exportar instância única
settings = get_settings()

# Validar no import
if __name__ == "__main__":
    print("✅ Configuração validada com sucesso!")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Database: {settings.DATABASE_URL[:20]}...")
    print(f"Firebase Project: {settings.FIREBASE_PROJECT_ID}")
