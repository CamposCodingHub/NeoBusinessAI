"""
Testes: /protocols — números de petição protocolada (JWT + ownership).
"""

import os
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_protocols.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, CourtProtocol, User, get_db  # noqa: E402
from routes.protocols_routes import router as protocols_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_protocols.db"
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
app.include_router(protocols_router)
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
    return _make_user("proto.owner@example.com", "Proto Owner")


@pytest.fixture
def stranger():
    return _make_user("proto.stranger@example.com", "Stranger")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def stranger_headers(stranger):
    return _headers_for(stranger)


def test_list_empty(auth_headers):
    r = client.get("/protocols", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["count"] == 0


def test_create_and_list(auth_headers):
    r = client.post(
        "/protocols",
        headers=auth_headers,
        json={
            "title": "Contestação",
            "protocol_number": "2026.001.999",
            "system": "pje",
            "court": "TJSP",
            "filed_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert r.status_code == 201
    proto = r.json()["protocol"]
    assert proto["protocol_number"] == "2026.001.999"
    assert proto["status"] == "pending"

    listed = client.get("/protocols?pending_only=true", headers=auth_headers)
    assert listed.status_code == 200
    assert listed.json()["count"] >= 1


def test_patch_status_and_ownership(auth_headers, stranger_headers):
    created = client.post(
        "/protocols",
        headers=auth_headers,
        json={
            "title": "Réplica",
            "protocol_number": "ABC-123",
            "system": "esaj",
        },
    )
    assert created.status_code == 201
    pid = created.json()["protocol"]["id"]

    denied = client.patch(
        f"/protocols/{pid}/status",
        headers=stranger_headers,
        json={"status": "confirmed"},
    )
    assert denied.status_code == 404

    ok = client.patch(
        f"/protocols/{pid}/status",
        headers=auth_headers,
        json={"status": "confirmed"},
    )
    assert ok.status_code == 200
    assert ok.json()["protocol"]["status"] == "confirmed"


def test_invalid_system(auth_headers):
    r = client.post(
        "/protocols",
        headers=auth_headers,
        json={
            "title": "X",
            "protocol_number": "1",
            "system": "hack",
        },
    )
    assert r.status_code == 400
