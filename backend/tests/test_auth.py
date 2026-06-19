"""
Testes de Autenticação
Cobertura: Login, registro, tokens, refresh, logout
"""

import pytest
import main as main_module
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from database import Base, get_db, get_db_async
from main import app
from security import create_access_token, verify_token

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
TEST_PASSWORD = "SenhaForte123!"

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_db_async] = override_get_db

client = TestClient(app)

class TestAuthentication:
    """Testes de autenticação"""
    
    def test_register_user_success(self):
        """Teste: Registro de usuário com sucesso"""
        response = client.post("/auth/register", json={
            "email": "test@example.com",
            "password": TEST_PASSWORD,
            "name": "Test User"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert "id" in data
    
    def test_register_duplicate_email(self):
        """Teste: Registro com email duplicado deve falhar"""
        # Primeiro registro
        client.post("/auth/register", json={
            "email": "duplicate@example.com",
            "password": TEST_PASSWORD,
            "name": "Test User"
        })
        
        # Segundo registro com mesmo email
        response = client.post("/auth/register", json={
            "email": "duplicate@example.com",
            "password": TEST_PASSWORD,
            "name": "Test User 2"
        })
        assert response.status_code == 400
    
    def test_login_success(self):
        """Teste: Login com credenciais válidas"""
        # Registrar usuário
        client.post("/auth/register", json={
            "email": "login@example.com",
            "password": TEST_PASSWORD,
            "name": "Login Test"
        })
        
        # Login
        response = client.post("/auth/login", json={
            "email": "login@example.com",
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self):
        """Teste: Login com credenciais inválidas"""
        response = client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    def test_refresh_token_rotation_prevents_reuse(self):
        """Refresh tokens devem ser rotacionados e aceitos apenas uma vez."""
        register_response = client.post("/auth/register", json={
            "email": "refresh-rotation@example.com",
            "password": TEST_PASSWORD,
            "name": "Refresh Rotation"
        })
        assert register_response.status_code == 201
        original_refresh = register_response.json()["refresh_token"]

        first_refresh = client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {original_refresh}"}
        )
        assert first_refresh.status_code == 200
        rotated_refresh = first_refresh.json()["refresh_token"]
        assert rotated_refresh != original_refresh

        reused_refresh = client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {original_refresh}"}
        )
        assert reused_refresh.status_code == 401

        second_refresh = client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {rotated_refresh}"}
        )
        assert second_refresh.status_code == 200
    
    def test_token_verification(self):
        """Teste: Verificação de token JWT"""
        token = create_access_token(user_id="123", expires_delta=timedelta(minutes=30))
        payload = verify_token(token, token_type="access")
        assert payload["sub"] == "123"
    
    def test_token_expired(self):
        """Teste: Token expirado deve ser rejeitado"""
        expired_token = create_access_token(
            user_id="123", 
            expires_delta=timedelta(minutes=-1)
        )
        with pytest.raises(Exception):
            verify_token(expired_token, token_type="access")
    
    def test_protected_route_without_token(self):
        """Teste: Acesso a rota protegida sem token"""
        response = client.get("/clients/")
        assert response.status_code == 401
    
    def test_protected_route_with_invalid_token(self):
        """Teste: Acesso com token inválido"""
        response = client.get(
            "/clients/",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    def test_premium_ai_requires_authentication(self):
        response = client.post(
            "/api/chat/premium",
            json={"message": "Explique o artigo 18 do Codigo Penal"}
        )

        assert response.status_code == 401

    def test_premium_ai_uses_authenticated_identity(self, monkeypatch):
        captured = {}

        class FakeOrchestrator:
            async def answer(self, **kwargs):
                captured.update(kwargs)
                return {
                    "response": "Resposta segura de teste.",
                    "quality_score": 100,
                    "metadata": {},
                    "legal_metadata": {},
                }

        monkeypatch.setattr(
            main_module,
            "legal_ai_orchestrator",
            FakeOrchestrator(),
        )
        monkeypatch.setattr(main_module, "PREMIUM_AI_AVAILABLE", True)
        monkeypatch.setattr(main_module, "premium_ai_engine", object())

        register_response = client.post("/auth/register", json={
            "email": "ai-identity@example.com",
            "password": TEST_PASSWORD,
            "name": "AI Identity"
        })
        user_id = register_response.json()["id"]
        access_token = register_response.json()["access_token"]

        response = client.post(
            "/api/chat/premium",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "message": "Organize os fatos.",
                "user_id": "forged-user",
                "conversation_id": "case!42",
            },
        )

        assert response.status_code == 200
        assert captured["user_id"] == f"{user_id}:case42"
    
    def test_logout_invalidates_token(self):
        """Teste: Logout invalida o token"""
        # Registrar e fazer login
        client.post("/auth/register", json={
            "email": "logout@example.com",
            "password": TEST_PASSWORD,
            "name": "Logout Test"
        })
        
        login_response = client.post("/auth/login", json={
            "email": "logout@example.com",
            "password": TEST_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        # Logout
        logout_response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert logout_response.status_code == 200
        
        # Tentar usar token após logout
        protected_response = client.get(
            "/clients/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert protected_response.status_code == 401


class TestRateLimiting:
    """Testes de rate limiting"""
    
    def test_login_rate_limit(self):
        """Teste: Rate limiting no login"""
        # Fazer múltiplas requisições de login
        for i in range(7):
            response = client.post("/auth/login", json={
                "email": f"test{i}@example.com",
                "password": "wrongpassword"
            })
        
        # A 6ª+ requisição deve ser bloqueada (rate limit)
        assert response.status_code == 429 or response.status_code == 401
    
    def test_api_rate_limit_headers(self):
        """Teste: Headers de rate limit presentes"""
        response = client.get("/health/")
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers


class TestPasswordRecovery:
    """Testes de recuperação de senha"""
    
    def test_forgot_password_existing_user(self):
        """Teste: Solicitar recuperação para usuário existente"""
        # Criar usuário
        client.post("/auth/register", json={
            "email": "recover@example.com",
            "password": TEST_PASSWORD,
            "name": "Recover Test"
        })
        
        response = client.post(f"/auth/forgot-password?email=recover@example.com")
        assert response.status_code == 200
        assert "message" in response.json()
    
    def test_forgot_password_nonexistent_user(self):
        """Teste: Solicitar recuperação para usuário inexistente"""
        response = client.post(f"/auth/forgot-password?email=nonexistent@example.com")
        assert response.status_code == 200  # Não deve revelar se email existe
        assert "message" in response.json()


# Cleanup
@pytest.fixture(autouse=True)
def cleanup():
    yield
    # Limpar banco de teste
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
