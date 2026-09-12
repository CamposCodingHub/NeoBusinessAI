"""
Testes: Electronic signature stub (ClickSign-style) — JWT + ownership.
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_esign_routes.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import (  # noqa: E402
    Base,
    ESignEnvelope,
    User,
    get_db,
)
from routes.esign_routes import router as esign_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_esign_routes.db"
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
        db.commit()
    finally:
        db.close()


app = FastAPI()
app.include_router(esign_router)
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
    return _make_user("esign.owner@example.com", "ESign Owner")


@pytest.fixture
def stranger():
    return _make_user("esign.stranger@example.com", "Stranger")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def stranger_headers(stranger):
    return _headers_for(stranger)


class TestESignRoutes:
    def test_create_and_list_envelopes(self, owner, auth_headers):
        created = client.post(
            "/esign/envelopes",
            json={
                "title": "Contrato Honorários",
                "signer_email": "cliente@example.com",
                "signer_name": "Cliente Teste",
            },
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        body = created.json()["envelope"]
        assert body["title"] == "Contrato Honorários"
        assert body["status"] == "draft"
        assert body["provider"] == "stub"
        assert body["user_id"] == owner.id
        assert body["signer_email"] == "cliente@example.com"

        listed = client.get("/esign/envelopes", headers=auth_headers)
        assert listed.status_code == 200, listed.text
        data = listed.json()
        assert data["count"] >= 1
        assert any(e["id"] == body["id"] for e in data["envelopes"])

    def test_send_and_mark_signed(self, auth_headers):
        created = client.post(
            "/esign/envelopes",
            json={
                "title": "NDA",
                "signer_email": "a@b.com",
                "signer_name": "Alice",
            },
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        env_id = created.json()["envelope"]["id"]

        sent = client.post(f"/esign/envelopes/{env_id}/send", headers=auth_headers)
        assert sent.status_code == 200, sent.text
        assert sent.json()["envelope"]["status"] == "sent"
        assert sent.json()["envelope"]["external_id"]

        signed = client.post(
            f"/esign/envelopes/{env_id}/mark-signed", headers=auth_headers
        )
        assert signed.status_code == 200, signed.text
        env = signed.json()["envelope"]
        assert env["status"] == "signed"
        assert env["signed_at"] is not None

    def test_idor_other_user_gets_404(self, auth_headers, stranger_headers):
        created = client.post(
            "/esign/envelopes",
            json={
                "title": "Private",
                "signer_email": "x@y.com",
                "signer_name": "X",
            },
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        env_id = created.json()["envelope"]["id"]

        for path in (
            f"/esign/envelopes/{env_id}/send",
            f"/esign/envelopes/{env_id}/mark-signed",
        ):
            resp = client.post(path, headers=stranger_headers)
            assert resp.status_code == 404, resp.text

    def test_auth_required(self):
        assert client.get("/esign/envelopes").status_code in (401, 403)
        assert client.post(
            "/esign/envelopes",
            json={"title": "X", "signer_email": "a@b.com", "signer_name": "A"},
        ).status_code in (401, 403)

    def test_invalid_email_rejected(self, auth_headers):
        bad = client.post(
            "/esign/envelopes",
            json={
                "title": "Bad",
                "signer_email": "not-an-email",
                "signer_name": "X",
            },
            headers=auth_headers,
        )
        assert bad.status_code == 400, bad.text
