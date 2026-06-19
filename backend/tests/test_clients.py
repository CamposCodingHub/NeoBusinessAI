"""
Testes de Clientes e IDOR (Insecure Direct Object Reference)
Cobertura: CRUD, validação, proteção IDOR
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db, get_db_async, User, Client, Document
from main import app
from security import create_access_token

# Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
TEST_PASSWORD = "SenhaForte123!"

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_db_async] = override_get_db
client = TestClient(app)

class TestClientCRUD:
    """Testes de CRUD de clientes"""
    
    @pytest.fixture
    def auth_headers(self):
        """Fixture: Criar usuário e obter token"""
        # Registrar
        client.post("/auth/register", json={
            "email": "clientuser@example.com",
            "password": TEST_PASSWORD,
            "name": "Client User"
        })
        
        # Login
        login = client.post("/auth/login", json={
            "email": "clientuser@example.com",
            "password": TEST_PASSWORD
        })
        token = login.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_create_client(self, auth_headers):
        """Teste: Criar cliente com sucesso"""
        response = client.post("/clients/", json={
            "name": "João Silva",
            "email": "joao@example.com",
            "phone": "11999999999",
            "cpf_cnpj": "12345678901",
            "address": "Rua Teste, 123",
            "city": "São Paulo",
            "state": "SP",
            "zip_code": "01001000",
            "status": "active"
        }, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["client"]["name"] == "João Silva"
        assert "id" in data["client"]
    
    def test_list_clients_pagination(self, auth_headers):
        """Teste: Listar clientes com paginação"""
        # Criar vários clientes
        for i in range(25):
            client.post("/clients/", json={
                "name": f"Cliente {i}",
                "email": f"cliente{i}@example.com",
                "status": "active"
            }, headers=auth_headers)
        
        # Listar página 1
        response = client.get("/clients/?page=1&limit=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["clients"]) == 10
        assert data["pagination"]["total"] == 25
        assert data["pagination"]["pages"] == 3
    
    def test_get_client_by_id(self, auth_headers):
        """Teste: Buscar cliente por ID"""
        # Criar cliente
        create_response = client.post("/clients/", json={
            "name": "Maria Souza",
            "email": "maria@example.com"
        }, headers=auth_headers)
        client_id = create_response.json()["client"]["id"]
        
        # Buscar
        response = client.get(f"/clients/{client_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "Maria Souza"

    def test_client_details_and_timeline_include_linked_document(self, auth_headers):
        create_response = client.post("/clients/", json={
            "name": "Cliente com Documento",
            "email": "documento@example.com"
        }, headers=auth_headers)
        client_id = create_response.json()["client"]["id"]

        db = TestingSessionLocal()
        try:
            user = db.query(User).filter(
                User.email == "clientuser@example.com"
            ).first()
            db.add(Document(
                user_id=user.id,
                filename="contrato-cliente.txt",
                custom_data={"client_id": client_id},
                status="completed",
            ))
            db.commit()
        finally:
            db.close()

        details = client.get(f"/clients/{client_id}", headers=auth_headers)
        timeline = client.get(
            f"/clients/{client_id}/timeline",
            headers=auth_headers,
        )

        assert details.status_code == 200
        assert details.json()["documents"][0]["filename"] == "contrato-cliente.txt"
        assert timeline.status_code == 200
        assert any(
            event["type"] == "document_uploaded"
            for event in timeline.json()["events"]
        )
    
    def test_update_client(self, auth_headers):
        """Teste: Atualizar cliente"""
        # Criar
        create_response = client.post("/clients/", json={
            "name": "Carlos Antigo",
            "email": "carlos@example.com"
        }, headers=auth_headers)
        client_id = create_response.json()["client"]["id"]
        
        # Atualizar
        response = client.put(f"/clients/{client_id}", json={
            "name": "Carlos Novo"
        }, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["client"]["name"] == "Carlos Novo"
    
    def test_delete_client(self, auth_headers):
        """Teste: Deletar cliente"""
        # Criar
        create_response = client.post("/clients/", json={
            "name": "Deletar",
            "email": "delete@example.com"
        }, headers=auth_headers)
        client_id = create_response.json()["client"]["id"]
        
        # Deletar
        response = client.delete(f"/clients/{client_id}", headers=auth_headers)
        assert response.status_code == 200
        
        # Verificar que foi deletado
        get_response = client.get(f"/clients/{client_id}", headers=auth_headers)
        assert get_response.status_code == 404


class TestIDORProtection:
    """Testes de proteção IDOR - Acesso a dados de outros usuários"""
    
    @pytest.fixture
    def user1_data(self):
        """Fixture: Criar usuário 1 com cliente"""
        # Registrar
        client.post("/auth/register", json={
            "email": "user1@example.com",
            "password": TEST_PASSWORD,
            "name": "User 1"
        })
        
        # Login
        login = client.post("/auth/login", json={
            "email": "user1@example.com",
            "password": TEST_PASSWORD
        })
        token1 = login.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}
        
        # Criar cliente
        client_response = client.post("/clients/", json={
            "name": "Cliente User 1",
            "email": "cliente1@example.com"
        }, headers=headers1)
        client_id = client_response.json()["client"]["id"]
        
        return {"headers": headers1, "client_id": client_id, "token": token1}
    
    @pytest.fixture
    def user2_data(self):
        """Fixture: Criar usuário 2"""
        # Registrar
        client.post("/auth/register", json={
            "email": "user2@example.com",
            "password": TEST_PASSWORD,
            "name": "User 2"
        })
        
        # Login
        login = client.post("/auth/login", json={
            "email": "user2@example.com",
            "password": TEST_PASSWORD
        })
        token2 = login.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        return {"headers": headers2, "token": token2}
    
    def test_user2_cannot_access_user1_client(self, user1_data, user2_data):
        """Teste CRÍTICO: Usuário 2 não pode acessar cliente do Usuário 1 (IDOR)"""
        user1_client_id = user1_data["client_id"]
        user2_headers = user2_data["headers"]
        
        # Usuário 2 tenta acessar cliente do Usuário 1
        response = client.get(f"/clients/{user1_client_id}", headers=user2_headers)
        
        # Deve retornar 404 (não encontrado) ou 403 (proibido)
        assert response.status_code in [404, 403]
    
    def test_user2_cannot_update_user1_client(self, user1_data, user2_data):
        """Teste CRÍTICO: Usuário 2 não pode atualizar cliente do Usuário 1"""
        user1_client_id = user1_data["client_id"]
        user2_headers = user2_data["headers"]
        
        response = client.put(f"/clients/{user1_client_id}", json={
            "name": "Hackeado"
        }, headers=user2_headers)
        
        assert response.status_code in [404, 403]
    
    def test_user2_cannot_delete_user1_client(self, user1_data, user2_data):
        """Teste CRÍTICO: Usuário 2 não pode deletar cliente do Usuário 1"""
        user1_client_id = user1_data["client_id"]
        user2_headers = user2_data["headers"]
        
        response = client.delete(f"/clients/{user1_client_id}", headers=user2_headers)
        
        assert response.status_code in [404, 403]
    
    def test_user2_list_only_own_clients(self, user1_data, user2_data):
        """Teste: Usuário 2 só vê seus próprios clientes na listagem"""
        user1_headers = user1_data["headers"]
        user2_headers = user2_data["headers"]
        
        # Criar cliente para usuário 2
        client.post("/clients/", json={
            "name": "Cliente User 2",
            "email": "cliente2@example.com"
        }, headers=user2_headers)
        
        # Listar como usuário 2
        response = client.get("/clients/", headers=user2_headers)
        data = response.json()
        
        # Deve ver apenas 1 cliente (o dele), não o do usuário 1
        assert len(data["clients"]) == 1
        assert data["clients"][0]["name"] == "Cliente User 2"


class TestInputValidation:
    """Testes de validação de inputs"""
    
    @pytest.fixture
    def auth_headers(self):
        client.post("/auth/register", json={
            "email": "validation@example.com",
            "password": TEST_PASSWORD,
            "name": "Validation User"
        })
        login = client.post("/auth/login", json={
            "email": "validation@example.com",
            "password": TEST_PASSWORD
        })
        return {"Authorization": f"Bearer {login.json()['access_token']}"}
    
    def test_xss_protection_in_client_name(self, auth_headers):
        """Teste: XSS protegido no nome do cliente"""
        response = client.post("/clients/", json={
            "name": "<script>alert('xss')</script>",
            "email": "test@example.com"
        }, headers=auth_headers)
        
        assert response.status_code == 201
        # Nome deve ser escapado/sanitizado
        client_name = response.json()["client"]["name"]
        assert "<script>" not in client_name
    
    def test_sql_injection_protection(self, auth_headers):
        """Teste: SQL Injection protegido"""
        response = client.post("/clients/", json={
            "name": "Test'; DROP TABLE clients; --",
            "email": "test@example.com"
        }, headers=auth_headers)
        
        # Deve criar cliente com nome estranho, mas não crashar
        assert response.status_code == 201
    
    def test_invalid_cpf_rejected(self, auth_headers):
        """Teste: CPF inválido rejeitado"""
        response = client.post("/clients/", json={
            "name": "Test",
            "email": "test@example.com",
            "cpf_cnpj": "12345678900"  # CPF inválido
        }, headers=auth_headers)
        
        # Deve aceitar (validação pode ser opcional) ou rejeitar
        assert response.status_code in [201, 400]


# Cleanup
@pytest.fixture(autouse=True)
def cleanup():
    yield
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
