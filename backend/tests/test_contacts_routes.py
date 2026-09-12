"""
Testes: /contacts/logs — atendimentos (JWT + ownership).
"""

import os
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_contacts_routes.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, ClientContactLog, User, get_db  # noqa: E402
from routes.contacts_routes import router as contacts_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_contacts_routes.db"
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
app.include_router(contacts_router)
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
    return _make_user("contacts.owner@example.com", "Contacts Owner")


@pytest.fixture
def stranger():
    return _make_user("contacts.stranger@example.com", "Stranger")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def stranger_headers(stranger):
    return _headers_for(stranger)


class TestContactsRoutes:
    def test_requires_auth(self):
        resp = client.get("/contacts/logs")
        assert resp.status_code in (401, 403)

    def test_create_and_list(self, auth_headers, owner):
        create = client.post(
            "/contacts/logs",
            headers=auth_headers,
            json={
                "subject": "Retorno sobre prazo de contestação",
                "channel": "whatsapp",
                "summary": "Cliente pediu cópia da petição; enviei PDF.",
                "contacted_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert create.status_code == 201, create.text
        body = create.json()["log"]
        assert body["user_id"] == owner.id
        assert body["channel"] == "whatsapp"
        lid = body["id"]

        listed = client.get("/contacts/logs", headers=auth_headers)
        assert listed.status_code == 200
        assert any(x["id"] == lid for x in listed.json()["logs"])

    def test_invalid_channel(self, auth_headers):
        resp = client.post(
            "/contacts/logs",
            headers=auth_headers,
            json={"subject": "x", "channel": "carrier-pigeon"},
        )
        assert resp.status_code == 400

    def test_ownership_isolation(self, auth_headers, stranger_headers):
        create = client.post(
            "/contacts/logs",
            headers=auth_headers,
            json={"subject": "Privado", "channel": "phone"},
        )
        assert create.status_code == 201
        lid = create.json()["log"]["id"]

        listed = client.get("/contacts/logs", headers=stranger_headers)
        assert listed.status_code == 200
        assert lid not in [x["id"] for x in listed.json()["logs"]]
        assert ClientContactLog is not None
