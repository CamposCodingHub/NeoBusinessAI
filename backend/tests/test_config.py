"""
Testes de Configuração
Valida que todas as variáveis de ambiente obrigatórias estão configuradas
"""

import pytest
from config import Settings, get_settings


def test_database_url_must_be_postgres():
    """Testa que SQLite não é permitido"""
    with pytest.raises(ValueError, match="SQLite não é permitido"):
        Settings(
            DATABASE_URL="sqlite:///test.db",
            GROQ_API_KEY="test_key_12345678901234567890",
            FIREBASE_PROJECT_ID="test-project",
            FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
            FIREBASE_CLIENT_EMAIL="test@test.com",
            SECRET_KEY="test_secret_key_minimum_32_characters"
        )


def test_database_url_must_be_valid_format():
    """Testa que apenas formato PostgreSQL é aceito"""
    with pytest.raises(ValueError, match="Apenas PostgreSQL é suportado"):
        Settings(
            DATABASE_URL="mysql://user:pass@localhost/db",
            GROQ_API_KEY="test_key_12345678901234567890",
            FIREBASE_PROJECT_ID="test-project",
            FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
            FIREBASE_CLIENT_EMAIL="test@test.com",
            SECRET_KEY="test_secret_key_minimum_32_characters"
        )


def test_groq_key_must_be_valid():
    """Testa que GROQ_API_KEY deve ter tamanho mínimo"""
    with pytest.raises(ValueError, match="GROQ_API_KEY inválida"):
        Settings(
            DATABASE_URL="postgresql://user:pass@localhost/db",
            GROQ_API_KEY="short",
            FIREBASE_PROJECT_ID="test-project",
            FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
            FIREBASE_CLIENT_EMAIL="test@test.com",
            SECRET_KEY="test_secret_key_minimum_32_characters"
        )


def test_firebase_private_key_must_be_valid():
    """Testa que FIREBASE_PRIVATE_KEY deve ser formato PEM"""
    with pytest.raises(ValueError, match="FIREBASE_PRIVATE_KEY inválida"):
        Settings(
            DATABASE_URL="postgresql://user:pass@localhost/db",
            GROQ_API_KEY="test_key_12345678901234567890",
            FIREBASE_PROJECT_ID="test-project",
            FIREBASE_PRIVATE_KEY="invalid_key",
            FIREBASE_CLIENT_EMAIL="test@test.com",
            SECRET_KEY="test_secret_key_minimum_32_characters"
        )


def test_secret_key_must_be_strong():
    """Testa que SECRET_KEY deve ter pelo menos 32 caracteres"""
    with pytest.raises(ValueError, match="SECRET_KEY deve ter pelo menos 32 caracteres"):
        Settings(
            DATABASE_URL="postgresql://user:pass@localhost/db",
            GROQ_API_KEY="test_key_12345678901234567890",
            FIREBASE_PROJECT_ID="test-project",
            FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
            FIREBASE_CLIENT_EMAIL="test@test.com",
            SECRET_KEY="short"
        )


def test_environment_must_be_valid():
    """Testa que ENVIRONMENT deve ser um valor válido"""
    with pytest.raises(ValueError, match="ENVIRONMENT deve ser um de"):
        Settings(
            DATABASE_URL="postgresql://user:pass@localhost/db",
            GROQ_API_KEY="test_key_12345678901234567890",
            FIREBASE_PROJECT_ID="test-project",
            FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
            FIREBASE_CLIENT_EMAIL="test@test.com",
            SECRET_KEY="test_secret_key_minimum_32_characters",
            ENVIRONMENT="invalid"
        )


def test_valid_config():
    """Testa que configuração válida é aceita"""
    settings = Settings(
        DATABASE_URL="postgresql://user:pass@localhost/db",
        GROQ_API_KEY="test_key_12345678901234567890",
        FIREBASE_PROJECT_ID="test-project",
        FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
        FIREBASE_CLIENT_EMAIL="test@test.com",
        SECRET_KEY="test_secret_key_minimum_32_characters"
    )
    assert settings.DATABASE_URL == "postgresql://user:pass@localhost/db"
    assert settings.GROQ_API_KEY == "test_key_12345678901234567890"
    assert settings.FIREBASE_PROJECT_ID == "test-project"
