"""
Testes básicos do Intake / Leads MVP
CRUD JWT + conversão para Client (app mínimo — evita import pesado de main).
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_intake.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, Client, Lead, User, get_db  # noqa: E402
from routes.intake_routes import router as intake_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_intake.db"
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
app.include_router(intake_router)
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
    return _make_user("intake.owner@example.com", "Intake Owner")


@pytest.fixture
def other():
    return _make_user("intake.other@example.com", "Other Firm")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def other_auth_headers(other):
    return _headers_for(other)


class TestIntakeRoutes:
    def test_create_and_list_leads(self, auth_headers):
        created = client.post(
            "/intake/leads",
            json={
                "name": "Ana Lead",
                "email": "ana@example.com",
                "phone": "11988887777",
                "practice_area": "Trabalhista",
                "source": "site",
                "notes": "Primeiro contato",
            },
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        body = created.json()
        assert body["lead"]["name"] == "Ana Lead"
        assert body["lead"]["status"] == "new"
        assert body["lead"]["conflict_flag"] is False

        listed = client.get("/intake/leads", headers=auth_headers)
        assert listed.status_code == 200
        data = listed.json()
        assert data["pagination"]["total"] >= 1
        assert any(lead["name"] == "Ana Lead" for lead in data["leads"])

    def test_patch_status(self, auth_headers):
        created = client.post(
            "/intake/leads",
            json={"name": "Bruno Qualificado", "practice_area": "Cível"},
            headers=auth_headers,
        )
        lead_id = created.json()["lead"]["id"]

        patched = client.patch(
            f"/intake/leads/{lead_id}",
            json={"status": "qualified", "notes": "OK para reunião"},
            headers=auth_headers,
        )
        assert patched.status_code == 200, patched.text
        assert patched.json()["lead"]["status"] == "qualified"
        assert "reunião" in patched.json()["lead"]["notes"]

    def test_invalid_status_rejected(self, auth_headers):
        created = client.post(
            "/intake/leads",
            json={"name": "Status Inválido"},
            headers=auth_headers,
        )
        lead_id = created.json()["lead"]["id"]
        bad = client.patch(
            f"/intake/leads/{lead_id}",
            json={"status": "pipeline_xyz"},
            headers=auth_headers,
        )
        assert bad.status_code == 400

    def test_convert_creates_client(self, auth_headers, owner):
        created = client.post(
            "/intake/leads",
            json={
                "name": "Carla Convertida",
                "email": "carla@example.com",
                "phone": "11977776666",
                "practice_area": "Família",
                "source": "indicação",
            },
            headers=auth_headers,
        )
        lead_id = created.json()["lead"]["id"]

        converted = client.post(
            f"/intake/leads/{lead_id}/convert",
            headers=auth_headers,
        )
        assert converted.status_code == 200, converted.text
        payload = converted.json()
        assert payload["lead"]["status"] == "won"
        assert payload["client"]["name"] == "Carla Convertida"
        assert payload["client"]["email"] == "carla@example.com"
        assert "id" in payload["client"]

        db = TestingSessionLocal()
        try:
            client_row = (
                db.query(Client)
                .filter(Client.name == "Carla Convertida", Client.user_id == owner.id)
                .first()
            )
            assert client_row is not None
            lead_row = db.query(Lead).filter(Lead.id == lead_id).first()
            assert lead_row.status == "won"
        finally:
            db.close()

    def test_convert_blocked_by_conflict(self, auth_headers):
        created = client.post(
            "/intake/leads",
            json={"name": "Conflito Lead", "conflict_flag": True},
            headers=auth_headers,
        )
        lead_id = created.json()["lead"]["id"]
        blocked = client.post(
            f"/intake/leads/{lead_id}/convert",
            headers=auth_headers,
        )
        assert blocked.status_code == 409

    def test_idor_other_user_cannot_patch(self, auth_headers, other_auth_headers):
        created = client.post(
            "/intake/leads",
            json={"name": "Lead Privado"},
            headers=auth_headers,
        )
        lead_id = created.json()["lead"]["id"]

        denied = client.patch(
            f"/intake/leads/{lead_id}",
            json={"status": "meeting"},
            headers=other_auth_headers,
        )
        assert denied.status_code == 404

    def test_requires_auth(self):
        response = client.get("/intake/leads")
        assert response.status_code in (401, 403)
