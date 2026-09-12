"""
Testes do Time Entry MVP — horas faturáveis
CRUD JWT + summary (app mínimo — evita import pesado de main).
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_time.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, TimeEntry, User, get_db  # noqa: E402
from routes.time_routes import router as time_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_time.db"
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
app.include_router(time_router)
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
    return _make_user("time.owner@example.com", "Time Owner")


@pytest.fixture
def other():
    return _make_user("time.other@example.com", "Other Firm")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def other_auth_headers(other):
    return _headers_for(other)


class TestTimeRoutes:
    def test_create_and_list_entries(self, auth_headers):
        created = client.post(
            "/time/entries",
            json={
                "description": "Revisão de contrato",
                "minutes": 90,
                "hourly_rate": 400.0,
                "billable": True,
                "work_date": "2026-09-11",
            },
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        body = created.json()
        assert body["entry"]["description"] == "Revisão de contrato"
        assert body["entry"]["minutes"] == 90
        assert body["entry"]["billable"] is True
        assert body["entry"]["estimated_amount"] == 600.0

        listed = client.get("/time/entries", headers=auth_headers)
        assert listed.status_code == 200
        data = listed.json()
        assert data["pagination"]["total"] >= 1
        assert any(e["description"] == "Revisão de contrato" for e in data["entries"])

    def test_patch_entry(self, auth_headers):
        created = client.post(
            "/time/entries",
            json={"description": "Audiência prep", "minutes": 60, "hourly_rate": 350},
            headers=auth_headers,
        )
        entry_id = created.json()["entry"]["id"]

        patched = client.patch(
            f"/time/entries/{entry_id}",
            json={"minutes": 120, "description": "Audiência prep + follow-up"},
            headers=auth_headers,
        )
        assert patched.status_code == 200, patched.text
        assert patched.json()["entry"]["minutes"] == 120
        assert "follow-up" in patched.json()["entry"]["description"]

    def test_summary_billable_amount(self, auth_headers):
        client.post(
            "/time/entries",
            json={
                "description": "Billable A",
                "minutes": 60,
                "hourly_rate": 200.0,
                "billable": True,
            },
            headers=auth_headers,
        )
        client.post(
            "/time/entries",
            json={
                "description": "Non-billable B",
                "minutes": 30,
                "hourly_rate": 200.0,
                "billable": False,
            },
            headers=auth_headers,
        )

        summary = client.get("/time/summary", headers=auth_headers)
        assert summary.status_code == 200, summary.text
        data = summary.json()
        assert data["total_minutes"] >= 90
        assert data["billable_minutes"] >= 60
        assert data["billable_amount_estimate"] >= 200.0

    def test_delete_entry(self, auth_headers):
        created = client.post(
            "/time/entries",
            json={"description": "Temp entry", "minutes": 15},
            headers=auth_headers,
        )
        entry_id = created.json()["entry"]["id"]

        deleted = client.delete(f"/time/entries/{entry_id}", headers=auth_headers)
        assert deleted.status_code == 200

        listed = client.get("/time/entries", headers=auth_headers)
        ids = [e["id"] for e in listed.json()["entries"]]
        assert entry_id not in ids

    def test_idor_other_user_cannot_access(self, auth_headers, other_auth_headers):
        created = client.post(
            "/time/entries",
            json={"description": "Privado do owner", "minutes": 45, "hourly_rate": 100},
            headers=auth_headers,
        )
        entry_id = created.json()["entry"]["id"]

        get_other = client.patch(
            f"/time/entries/{entry_id}",
            json={"minutes": 99},
            headers=other_auth_headers,
        )
        assert get_other.status_code == 404

        delete_other = client.delete(
            f"/time/entries/{entry_id}", headers=other_auth_headers
        )
        assert delete_other.status_code == 404

    def test_auth_required(self):
        assert client.get("/time/entries").status_code in (401, 403)
        assert client.get("/time/summary").status_code in (401, 403)
        assert (
            client.post(
                "/time/entries",
                json={"description": "x", "minutes": 10},
            ).status_code
            in (401, 403)
        )

    def test_invalid_minutes_rejected(self, auth_headers):
        bad = client.post(
            "/time/entries",
            json={"description": "Zero minutes", "minutes": 0},
            headers=auth_headers,
        )
        assert bad.status_code == 422
