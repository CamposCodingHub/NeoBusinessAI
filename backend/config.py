"""
Centralized application settings with strict validation.
"""

import sys
from functools import lru_cache
from typing import Optional

from pydantic import ConfigDict, Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings validated at startup."""

    DATABASE_URL: str = Field(
        default="postgresql://user:pass@localhost:5432/db",
        description="PostgreSQL connection string",
    )

    GROQ_API_KEY: Optional[str] = Field(
        default=None,
        description="Groq API key opcional para contingencia externa",
    )
    OPENAI_API_KEY: Optional[str] = Field(None, description="OpenAI API key (optional)")
    ANTHROPIC_API_KEY: Optional[str] = Field(None, description="Anthropic API key (optional)")

    AI_SOVEREIGN_ENABLED: bool = Field(
        True,
        description="Prioriza inferencia local soberana",
    )
    AI_ROUTING_POLICY: str = Field(
        "local_only",
        description="Politica: local_only, local_first ou external_first",
    )
    LOCAL_AI_BASE_URL: str = Field(
        "http://127.0.0.1:11434/v1",
        description="Endpoint OpenAI-compatible local principal",
    )
    LOCAL_AI_SECONDARY_URL: Optional[str] = Field(
        None,
        description="Endpoint local secundario para alta disponibilidade",
    )
    LOCAL_AI_API_KEY: str = Field("ollama")
    LOCAL_AI_FAST_MODEL: str = Field("qwen2.5-coder:1.5b")
    LOCAL_AI_QUICK_MODEL: str = Field("lex-juridica-instant:1.5b")
    LOCAL_AI_BALANCED_MODEL: str = Field("lex-juridica-rapida:3b")
    LOCAL_AI_DEEP_MODEL: str = Field("lex-juridica:14b")
    LOCAL_AI_EMBEDDING_MODEL: str = Field("nomic-embed-text")
    LOCAL_AI_TIMEOUT_SECONDS: int = Field(1200, ge=10, le=3600)
    LOCAL_AI_MAX_RETRIES: int = Field(0, ge=0, le=5)
    LOCAL_AI_KEEP_ALIVE: str = Field("15m")
    LOCAL_AI_CONTEXT_TOKENS: int = Field(8192, ge=1024, le=131072)
    AI_EXTERNAL_FALLBACK_ENABLED: bool = Field(False)
    AI_CIRCUIT_FAILURE_THRESHOLD: int = Field(3, ge=1, le=20)
    AI_CIRCUIT_RECOVERY_SECONDS: int = Field(120, ge=10, le=3600)
    AI_KNOWLEDGE_TOP_K: int = Field(6, ge=1, le=20)
    AI_KNOWLEDGE_MIN_SCORE: float = Field(0.18, ge=0, le=1)
    AI_LAZY_EMBED_BATCH: int = Field(8, ge=0, le=48)
    AI_REALTIME_OFFICIAL_SEARCH_ENABLED: bool = Field(True)
    AI_REALTIME_OFFICIAL_SEARCH_MAX_RESULTS: int = Field(5, ge=1, le=10)
    AI_REALTIME_OFFICIAL_SEARCH_CACHE_SECONDS: int = Field(
        600,
        ge=60,
        le=86400,
    )

    FIREBASE_PROJECT_ID: str = Field(
        default="default-project-id",
        description="Firebase project ID",
    )
    FIREBASE_PRIVATE_KEY: str = Field(
        default="-----BEGIN PRIVATE KEY-----\ndefault\n-----END PRIVATE KEY-----",
        description="Firebase private key (JSON)",
    )
    FIREBASE_CLIENT_EMAIL: str = Field(
        default="default@default.iam.gserviceaccount.com",
        description="Firebase client email",
    )

    STRIPE_SECRET_KEY: Optional[str] = Field(None, description="Stripe secret key")
    STRIPE_PUBLISHABLE_KEY: Optional[str] = Field(None, description="Stripe publishable key")
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(None, description="Stripe webhook secret")

    SMTP_SERVER: Optional[str] = Field(None, description="SMTP server")
    SMTP_PORT: Optional[int] = Field(587, description="SMTP port")
    SMTP_USERNAME: Optional[str] = Field(None, description="SMTP username")
    SMTP_PASSWORD: Optional[str] = Field(None, description="SMTP password")

    REDIS_URL: Optional[str] = Field(None, description="Redis connection string")

    ENVIRONMENT: str = Field(
        "development",
        description="Environment: development, staging, production, test",
    )
    DEBUG: bool = Field(False, description="Debug mode")
    LOG_LEVEL: str = Field("INFO", description="Log level")

    SECRET_KEY: str = Field(
        default="default_secret_key_with_at_least_32_chars",
        description="Secret key para JWT (minimo 32 caracteres)",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, description="Token expiration in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(7, description="Refresh token expiration in days")

    MAX_FILE_SIZE_MB: int = Field(50, description="Maximum file size in MB")
    MAX_DOCUMENTS_PER_USER: int = Field(100, description="Max documents per user")
    MAX_PDF_PAGES: int = Field(500, ge=1, le=2000)
    MAX_OCR_PAGES: int = Field(100, ge=1, le=500)
    MAX_EXTRACTED_TEXT_CHARS: int = Field(2_000_000, ge=10_000, le=10_000_000)
    MAX_IMAGE_PIXELS: int = Field(40_000_000, ge=1_000_000, le=200_000_000)

    CORS_ORIGINS: str = Field("*", description="CORS origins (comma-separated)")

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def database_must_be_supported(cls, value: str) -> str:
        if not (value.startswith("sqlite") or value.startswith("postgresql")):
            raise ValueError(
                "Apenas PostgreSQL é suportado. "
                "Formato: postgresql://user:pass@host:port/dbname"
            )
        return value

    @field_validator("GROQ_API_KEY")
    @classmethod
    def groq_key_must_be_valid(cls, value: Optional[str]) -> Optional[str]:
        if value is None or not value.strip():
            return None
        if len(value) < 20:
            raise ValueError("GROQ_API_KEY inválida")
        return value

    @field_validator("AI_ROUTING_POLICY")
    @classmethod
    def ai_routing_policy_must_be_valid(cls, value: str) -> str:
        normalized = value.strip().lower()
        valid = {"local_only", "local_first", "external_first"}
        if normalized not in valid:
            raise ValueError(f"AI_ROUTING_POLICY deve ser um de: {sorted(valid)}")
        return normalized

    @field_validator("FIREBASE_PRIVATE_KEY")
    @classmethod
    def firebase_key_must_be_valid(cls, value: str) -> str:
        if not value or "-----BEGIN PRIVATE KEY-----" not in value:
            raise ValueError("FIREBASE_PRIVATE_KEY inválida. Deve ser uma chave PEM completa.")
        return value

    @field_validator("DEBUG", mode="before")
    @classmethod
    def normalize_debug_flag(cls, value):
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        normalized = str(value).strip().lower()
        truthy = {"1", "true", "yes", "on", "debug", "development", "dev"}
        falsy = {"0", "false", "no", "off", "release", "prod", "production"}
        if normalized in truthy:
            return True
        if normalized in falsy:
            return False
        raise ValueError("DEBUG deve ser booleano ou um alias valido como true/false, dev/release")

    @field_validator("ENVIRONMENT")
    @classmethod
    def environment_must_be_valid(cls, value: str) -> str:
        valid_envs = {"development", "staging", "production", "test"}
        normalized = value.lower()
        if normalized not in valid_envs:
            raise ValueError(f"ENVIRONMENT deve ser um de: {sorted(valid_envs)}")
        return normalized

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_strong(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("SECRET_KEY deve ter pelo menos 32 caracteres")
        return value

    @model_validator(mode="after")
    def database_must_match_environment(self):
        if self.DATABASE_URL.startswith("sqlite") and self.ENVIRONMENT != "test":
            raise ValueError(
                "SQLite não é permitido em produção. "
                "Use PostgreSQL: postgresql://user:pass@host:port/dbname"
            )
        return self


@lru_cache()
def get_settings() -> Settings:
    try:
        return Settings()
    except Exception as exc:
        sys.stderr.write("=" * 80 + "\n")
        sys.stderr.write("ERRO CRITICO: Configuracao invalida\n")
        sys.stderr.write("=" * 80 + "\n")
        sys.stderr.write(f"Erro: {exc}\n")
        sys.stderr.write("\nPor favor, verifique seu arquivo .env\n")
        sys.stderr.write("Use .env.example como referencia\n")
        sys.stderr.write("=" * 80 + "\n")
        raise


settings = get_settings()


if __name__ == "__main__":
    print("Configuracao validada com sucesso!")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Database: {settings.DATABASE_URL[:20]}...")
    print(f"Firebase Project: {settings.FIREBASE_PROJECT_ID}")
