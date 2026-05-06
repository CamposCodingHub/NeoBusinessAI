"""
Testes de Integração
Cobertura: Fluxos completos, APIs externas (mock)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from database import Base, get_db
from main import app

# Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class TestCompleteWorkflow:
    """Testes de fluxo completo"""
    
    @pytest.fixture
    def auth_headers(self):
        """Fixture: Autenticar usuário"""
        client.post("/auth/register", json={
            "email": "workflow@example.com",
            "password": "testpassword123",
            "name": "Workflow User"
        })
        login = client.post("/auth/login", json={
            "email": "workflow@example.com",
            "password": "testpassword123"
        })
        return {"Authorization": f"Bearer {login.json()['access_token']}"}
    
    def test_complete_client_workflow(self, auth_headers):
        """Teste: Fluxo completo de cliente (criar → atualizar → deletar)"""
        # 1. Criar cliente
        create = client.post("/clients/", json={
            "name": "Cliente Completo",
            "email": "completo@example.com",
            "phone": "11999999999",
            "status": "active"
        }, headers=auth_headers)
        assert create.status_code == 201
        client_id = create.json()["client"]["id"]
        
        # 2. Buscar cliente
        get = client.get(f"/clients/{client_id}", headers=auth_headers)
        assert get.status_code == 200
        assert get.json()["name"] == "Cliente Completo"
        
        # 3. Atualizar cliente
        update = client.put(f"/clients/{client_id}", json={
            "name": "Cliente Atualizado"
        }, headers=auth_headers)
        assert update.status_code == 200
        
        # 4. Criar fatura para o cliente
        invoice = client.post("/invoices/", json={
            "client_id": client_id,
            "description": "Serviços advocatícios",
            "total_cents": 500000,  # R$ 5.000,00
            "due_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }, headers=auth_headers)
        assert invoice.status_code == 201
        invoice_id = invoice.json()["id"]
        
        # 5. Criar prazo relacionado
        deadline = client.post("/deadlines/", json={
            "description": "Audiência - Cliente Completo",
            "due_date": (datetime.utcnow() + timedelta(days=15)).isoformat(),
            "urgency": "high",
            "notes": "Preparar documentação"
        }, headers=auth_headers)
        assert deadline.status_code == 201
        
        # 6. Verificar timeline do cliente
        timeline = client.get(f"/clients/{client_id}/timeline", headers=auth_headers)
        assert timeline.status_code == 200
        assert len(timeline.json()["events"]) > 0
        
        # 7. Deletar cliente
        delete = client.delete(f"/clients/{client_id}", headers=auth_headers)
        assert delete.status_code == 200
    
    def test_invoice_payment_workflow(self, auth_headers):
        """Teste: Fluxo de pagamento de fatura"""
        # Criar cliente
        client_resp = client.post("/clients/", json={
            "name": "Cliente Pagamento",
            "email": "pagamento@example.com"
        }, headers=auth_headers)
        client_id = client_resp.json()["client"]["id"]
        
        # Criar fatura
        invoice = client.post("/invoices/", json={
            "client_id": client_id,
            "description": "Pagamento teste",
            "total_cents": 100000,
            "due_date": (datetime.utcnow() + timedelta(days=10)).isoformat()
        }, headers=auth_headers)
        invoice_id = invoice.json()["id"]
        
        # Verificar status inicial
        assert invoice.json()["status"] == "pending"
        
        # Marcar como paga
        pay = client.patch(f"/invoices/{invoice_id}/mark-paid", headers=auth_headers)
        assert pay.status_code == 200
        assert pay.json()["status"] == "paid"
        
        # Verificar no dashboard financeiro
        dashboard = client.get("/invoices/dashboard", headers=auth_headers)
        assert dashboard.status_code == 200
        assert dashboard.json()["total_paid"] > 0


class TestErrorHandling:
    """Testes de tratamento de erros"""
    
    def test_404_error_format(self):
        """Teste: Formato de erro 404"""
        response = client.get("/nonexistent-route")
        assert response.status_code == 404
        # Deve retornar JSON, não HTML
        assert "application/json" in response.headers.get("content-type", "")
    
    def test_validation_error_format(self):
        """Teste: Formato de erro de validação"""
        response = client.post("/auth/register", json={
            "email": "invalid-email",  # Email inválido
            "password": "123",  # Senha muito curta
            "name": ""
        })
        assert response.status_code in [400, 422]
        data = response.json()
        assert "detail" in data or "message" in data
    
    def test_authentication_error_format(self):
        """Teste: Formato de erro de autenticação"""
        response = client.get("/clients/", headers={
            "Authorization": "Bearer invalid_token"
        })
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


class TestPaginationAndFiltering:
    """Testes de paginação e filtros"""
    
    @pytest.fixture
    def auth_headers(self):
        client.post("/auth/register", json={
            "email": "pagination@example.com",
            "password": "testpassword123",
            "name": "Pagination User"
        })
        login = client.post("/auth/login", json={
            "email": "pagination@example.com",
            "password": "testpassword123"
        })
        return {"Authorization": f"Bearer {login.json()['access_token']}"}
    
    def test_client_pagination(self, auth_headers):
        """Teste: Paginação de clientes"""
        # Criar 25 clientes
        for i in range(25):
            client.post("/clients/", json={
                "name": f"Cliente Pag {i}",
                "email": f"pag{i}@example.com",
                "status": "active"
            }, headers=auth_headers)
        
        # Página 1
        page1 = client.get("/clients/?page=1&limit=10", headers=auth_headers)
        assert len(page1.json()["clients"]) == 10
        assert page1.json()["pagination"]["page"] == 1
        
        # Página 2
        page2 = client.get("/clients/?page=2&limit=10", headers=auth_headers)
        assert len(page2.json()["clients"]) == 10
        assert page2.json()["pagination"]["page"] == 2
        
        # Página 3 (deve ter 5)
        page3 = client.get("/clients/?page=3&limit=10", headers=auth_headers)
        assert len(page3.json()["clients"]) == 5
    
    def test_client_filtering_by_status(self, auth_headers):
        """Teste: Filtro de clientes por status"""
        # Criar ativos e inativos
        for i in range(5):
            client.post("/clients/", json={
                "name": f"Ativo {i}",
                "email": f"ativo{i}@example.com",
                "status": "active"
            }, headers=auth_headers)
        
        for i in range(3):
            client.post("/clients/", json={
                "name": f"Inativo {i}",
                "email": f"inativo{i}@example.com",
                "status": "inactive"
            }, headers=auth_headers)
        
        # Filtrar ativos
        ativos = client.get("/clients/?status=active", headers=auth_headers)
        assert ativos.json()["pagination"]["total"] == 5
        
        # Filtrar inativos
        inativos = client.get("/clients/?status=inactive", headers=auth_headers)
        assert inativos.json()["pagination"]["total"] == 3
    
    def test_client_search(self, auth_headers):
        """Teste: Busca de clientes"""
        # Criar clientes
        client.post("/clients/", json={
            "name": "João Silva",
            "email": "joao@example.com"
        }, headers=auth_headers)
        
        client.post("/clients/", json={
            "name": "Maria Souza",
            "email": "maria@example.com"
        }, headers=auth_headers)
        
        # Buscar por "João"
        search = client.get("/clients/?search=João", headers=auth_headers)
        assert len(search.json()["clients"]) == 1
        assert search.json()["clients"][0]["name"] == "João Silva"


# Cleanup
@pytest.fixture(autouse=True)
def cleanup():
    yield
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
