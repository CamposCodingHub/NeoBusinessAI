"""
Testes do stub de contrato de honorários (engagement letter).
App mínimo — evita import pesado de main.
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_engagement_letter.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, Client, Matter, User, get_db  # noqa: E402
from routes.legal_routes import (  # noqa: E402
    build_engagement_letter_markdown,
    router as legal_router,
)
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_engagement_letter.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()
app.include_router(legal_router)
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
    return _make_user("engagement.owner@example.com", "Dr. Engagement Owner")


@pytest.fixture
def other():
    return _make_user("engagement.other@example.com", "Other Firm")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def other_auth_headers(other):
    return _headers_for(other)


@pytest.fixture
def owned_client(owner):
    db = TestingSessionLocal()
    try:
        row = Client(
            user_id=owner.id,
            name="Cliente Honorários",
            email="cli.honorarios@example.com",
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row
    finally:
        db.close()


@pytest.fixture
def foreign_client(other):
    db = TestingSessionLocal()
    try:
        row = Client(
            user_id=other.id,
            name="Cliente Alheio",
            email="foreign@example.com",
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row
    finally:
        db.close()


@pytest.fixture
def owned_matter(owner, owned_client):
    db = TestingSessionLocal()
    try:
        row = Matter(
            user_id=owner.id,
            client_id=owned_client.id,
            title="Ação Cível Demo",
            practice_area="Cível",
            status="open",
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row
    finally:
        db.close()


class TestEngagementLetterTemplate:
    def test_template_includes_client_and_fee(self):
        md = build_engagement_letter_markdown(
            client_name="Maria Silva",
            attorney_name="Dr. João",
            scope="Assessoria trabalhista preventiva",
            fee_type="hourly",
            amount=None,
            hourly_rate=450.0,
            matter_title="Caso X",
        )
        assert "Maria Silva" in md
        assert "Honorários por hora" in md
        assert "450" in md
        assert "Caso X" in md
        assert "Assessoria trabalhista preventiva" in md


class TestEngagementLetterRoutes:
    def test_hourly_draft_returns_markdown(self, auth_headers, owned_client, owned_matter):
        resp = client.post(
            "/legal/engagement-letter",
            json={
                "client_id": owned_client.id,
                "matter_id": owned_matter.id,
                "fee_type": "hourly",
                "hourly_rate": 500.0,
                "scope": "Defesa em reclamação trabalhista",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "draft_markdown" in body
        assert "Cliente Honorários" in body["draft_markdown"]
        assert "Ação Cível Demo" in body["draft_markdown"]
        assert "revisar com advogado" in body["warnings"]
        assert body["fee_type"] == "hourly"

    def test_flat_draft_and_missing_amount_warning(self, auth_headers, owned_client):
        resp = client.post(
            "/legal/engagement-letter",
            json={
                "client_id": owned_client.id,
                "fee_type": "flat",
                "scope": "Elaboração de contrato societário",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "Honorários fixos" in body["draft_markdown"]
        assert any("amount" in w for w in body["warnings"])

    def test_rejects_foreign_client(self, auth_headers, foreign_client):
        resp = client.post(
            "/legal/engagement-letter",
            json={
                "client_id": foreign_client.id,
                "fee_type": "contingency",
                "amount": 20.0,
                "scope": "Ação indenizatória",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 404, resp.text

    def test_requires_auth(self, owned_client):
        resp = client.post(
            "/legal/engagement-letter",
            json={
                "client_id": owned_client.id,
                "fee_type": "hourly",
                "hourly_rate": 300.0,
                "scope": "Consulta",
            },
        )
        assert resp.status_code in (401, 403)
