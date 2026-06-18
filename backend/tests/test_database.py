"""
Testes de Banco de Dados
Valida conexão e operações básicas do banco de dados
"""

import pytest
from sqlalchemy import create_engine
from database import Base, engine, SessionLocal, User, Document


def test_database_connection():
    """Testa que conexão com banco de dados funciona"""
    assert engine is not None
    assert str(engine.url).startswith("postgresql://")


def test_session_factory():
    """Testa que SessionLocal cria sessões corretamente"""
    session = SessionLocal()
    assert session is not None
    session.close()


def test_user_model():
    """Testa modelo User"""
    user = User(
        email="test@example.com",
        name="Test User",
        plan_tier="free"
    )
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.plan_tier == "free"
    assert user.is_active is True


def test_document_model():
    """Testa modelo Document"""
    doc = Document(
        user_id=1,
        filename="test.pdf",
        file_type="application/pdf",
        status="uploaded"
    )
    assert doc.filename == "test.pdf"
    assert doc.status == "uploaded"
    assert doc.deadlines == []
    assert doc.values == []


def test_user_to_dict():
    """Testa método to_dict do User"""
    user = User(
        email="test@example.com",
        name="Test User",
        plan_tier="professional"
    )
    user_dict = user.to_dict()
    assert "email" in user_dict
    assert "name" in user_dict
    assert "plan_tier" in user_dict
    assert user_dict["email"] == "test@example.com"
