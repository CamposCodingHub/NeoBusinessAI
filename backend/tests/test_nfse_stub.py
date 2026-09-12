"""
Testes: NFS-e stub — POST/GET /billing/nfse + issue-stub (JWT).
NAO integra prefeitura.
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_nfse_stub.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, NfseDraft, User, get_db  # noqa: E402
from routes.finance_routes import billing_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_nfse_stub.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(billing_router)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def _make_user(email: str, name: str) -> User:
    db = TestingSessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return existing
        user = User(email=email, name=name, password_hash="x", role="user")
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def _headers_for(user: User) -> dict:
    token = create_access_token(user_id=str(user.id), role=Role.USER)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def owner():
    return _make_user("nfse.owner@example.com", "Nfse Owner")


@pytest.fixture
def stranger():
    return _make_user("nfse.stranger@example.com", "Stranger")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


class TestNfseStub:
    def test_create_and_list_nfse(self, owner, auth_headers):
        created = client.post(
            "/billing/nfse",
            headers=auth_headers,
            json={
                "client_name": "Cliente Stub",
                "service_description": "Honorarios advocaticios",
                "amount": 1500.50,
            },
        )
        assert created.status_code == 201
        body = created.json()
        assert body["status"] == "draft"
        assert body["client_name"] == "Cliente Stub"
        assert body["amount"] == 1500.50
        assert body["number_stub"] is None
        assert body["user_id"] == owner.id

        listed = client.get("/billing/nfse", headers=auth_headers)
        assert listed.status_code == 200
        data = listed.json()
        assert data["count"] >= 1
        assert any(i["id"] == body["id"] for i in data["items"])

    def test_issue_stub_sets_number(self, auth_headers):
        created = client.post(
            "/billing/nfse",
            headers=auth_headers,
            json={
                "client_name": "Emitir LTDA",
                "service_description": "Consultoria",
                "amount": 200.0,
            },
        )
        assert created.status_code == 201
        nfse_id = created.json()["id"]

        issued = client.post(
            f"/billing/nfse/{nfse_id}/issue-stub",
            headers=auth_headers,
        )
        assert issued.status_code == 200
        body = issued.json()
        assert body["status"] == "issued_stub"
        assert body["number_stub"]
        assert body["number_stub"].startswith("NFS-e-STUB-")

    def test_issue_stub_ownership(self, auth_headers, stranger):
        created = client.post(
            "/billing/nfse",
            headers=auth_headers,
            json={
                "client_name": "Privado",
                "service_description": "Servico",
                "amount": 10.0,
            },
        )
        nfse_id = created.json()["id"]
        stranger_headers = _headers_for(stranger)
        resp = client.post(
            f"/billing/nfse/{nfse_id}/issue-stub",
            headers=stranger_headers,
        )
        assert resp.status_code == 404

    def test_create_requires_jwt(self):
        resp = client.post(
            "/billing/nfse",
            json={
                "client_name": "X",
                "service_description": "Y",
                "amount": 1.0,
            },
        )
        assert resp.status_code in (401, 403)
