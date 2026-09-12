"""Testes do screening automático de conflito de interesse (Intake)."""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_conflict_check.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, Client, Lead, Matter, User, get_db  # noqa: E402
from routes.intake_routes import router as intake_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402
from services.conflict_check_service import (  # noqa: E402
    normalize_phone,
    names_match,
    screen_conflicts,
)

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_conflict_check.db"
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
    return _make_user("conflict.owner@example.com", "Conflict Owner")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


class TestConflictHelpers:
    def test_normalize_phone_digits_only(self):
        assert normalize_phone("(11) 98888-7777") == "11988887777"

    def test_names_fuzzy_match(self):
        from services.conflict_check_service import normalize_text

        a = normalize_text("João Silva")
        b = normalize_text("Joao Silva")
        ok, score = names_match(a, b)
        assert ok is True
        assert score >= 0.88
        ok2, _ = names_match(
            normalize_text("Maria Oliveira"),
            normalize_text("Maria Oliveira Santos"),
        )
        assert ok2 is True


class TestConflictScreeningRoutes:
    def test_create_flags_conflict_against_existing_client(self, auth_headers, owner):
        db = TestingSessionLocal()
        try:
            existing = Client(
                user_id=owner.id,
                name="Pedro Almeida",
                email="pedro.almeida@example.com",
                status="active",
            )
            existing.set_sensitive_data(phone="11999998888")
            db.add(existing)
            db.commit()
        finally:
            db.close()

        created = client.post(
            "/intake/leads",
            json={
                "name": "Pedro Almeida",
                "email": "outro@example.com",
                "phone": "11911112222",
            },
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        lead = created.json()["lead"]
        assert lead["conflict_flag"] is True
        assert lead["conflict_detail"]
        assert "client#" in lead["conflict_detail"]
        assert lead["notes"] and "[CONFLICT]" in lead["notes"]

        blocked = client.post(
            f"/intake/leads/{lead['id']}/convert",
            headers=auth_headers,
        )
        assert blocked.status_code == 409

    def test_create_flags_conflict_by_email_or_phone(self, auth_headers, owner):
        db = TestingSessionLocal()
        try:
            existing = Client(
                user_id=owner.id,
                name="Cliente Unico XYZ",
                email="match.email@example.com",
                status="active",
            )
            existing.set_sensitive_data(phone="21987654321")
            db.add(existing)
            db.commit()
        finally:
            db.close()

        by_email = client.post(
            "/intake/leads",
            json={
                "name": "Nome Diferente",
                "email": "MATCH.EMAIL@example.com",
            },
            headers=auth_headers,
        )
        assert by_email.status_code == 201
        assert by_email.json()["lead"]["conflict_flag"] is True
        assert "email" in (by_email.json()["lead"]["conflict_detail"] or "")

        by_phone = client.post(
            "/intake/leads",
            json={
                "name": "Outro Nome",
                "phone": "(21) 98765-4321",
            },
            headers=auth_headers,
        )
        assert by_phone.status_code == 201
        assert by_phone.json()["lead"]["conflict_flag"] is True
        assert "phone" in (by_phone.json()["lead"]["conflict_detail"] or "")

    def test_patch_flags_conflict_against_matter_and_lead(self, auth_headers, owner):
        db = TestingSessionLocal()
        try:
            db.add(
                Matter(
                    user_id=owner.id,
                    title="Ação cível",
                    opposing_party="Rival Corp SA",
                    status="open",
                )
            )
            db.add(
                Lead(
                    user_id=owner.id,
                    name="Lead Existente Fone",
                    email="existente@example.com",
                    phone="1133334444",
                    status="new",
                )
            )
            db.commit()
        finally:
            db.close()

        created = client.post(
            "/intake/leads",
            json={"name": "Prospect Limpo", "email": "limpo@example.com"},
            headers=auth_headers,
        )
        assert created.status_code == 201
        lead_id = created.json()["lead"]["id"]
        assert created.json()["lead"]["conflict_flag"] is False

        patched = client.patch(
            f"/intake/leads/{lead_id}",
            json={"name": "Rival Corp SA"},
            headers=auth_headers,
        )
        assert patched.status_code == 200, patched.text
        body = patched.json()["lead"]
        assert body["conflict_flag"] is True
        assert "matter#" in (body["conflict_detail"] or "")

        # service unit: lead phone match excludes self
        db = TestingSessionLocal()
        try:
            screen = screen_conflicts(
                db,
                owner.id,
                name="X",
                phone="11 3333-4444",
                exclude_lead_id=lead_id,
            )
            assert screen.has_conflict is True
            assert any(m.source == "lead" and m.field == "phone" for m in screen.matches)
        finally:
            db.close()
