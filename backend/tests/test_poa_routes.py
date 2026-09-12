"""
Testes: Procurações (POA) — JWT + ownership + vencimento.
"""

import os
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_poa_routes.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, PowerOfAttorney, User, get_db  # noqa: E402
from routes.poa_routes import router as poa_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_poa_routes.db"
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
app.include_router(poa_router)
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
    return _make_user("poa.owner@example.com", "POA Owner")


@pytest.fixture
def stranger():
    return _make_user("poa.stranger@example.com", "Stranger")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def stranger_headers(stranger):
    return _headers_for(stranger)


class TestPoaRoutes:
    def test_requires_auth(self):
        resp = client.get("/poa")
        assert resp.status_code in (401, 403)

    def test_create_list_expiring_revoke(self, auth_headers, owner):
        soon = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
        create = client.post(
            "/poa",
            headers=auth_headers,
            json={
                "title": "Procuração ad judicia",
                "expires_at": soon,
                "notes": "Escopo limitado ao processo X",
            },
        )
        assert create.status_code == 201, create.text
        body = create.json()
        assert body["success"] is True
        rid = body["power"]["id"]
        assert body["power"]["status"] == "active"
        assert body["power"]["user_id"] == owner.id

        listed = client.get("/poa", headers=auth_headers)
        assert listed.status_code == 200
        assert listed.json()["count"] >= 1

        expiring = client.get("/poa/expiring?days=30", headers=auth_headers)
        assert expiring.status_code == 200
        ids = [p["id"] for p in expiring.json()["powers"]]
        assert rid in ids

        revoked = client.post(f"/poa/{rid}/revoke", headers=auth_headers)
        assert revoked.status_code == 200
        assert revoked.json()["power"]["status"] == "revoked"

    def test_auto_expire_on_create(self, auth_headers):
        past = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        create = client.post(
            "/poa",
            headers=auth_headers,
            json={"title": "Mandato vencido", "expires_at": past},
        )
        assert create.status_code == 201
        rid = create.json()["power"]["id"]
        assert create.json()["power"]["status"] == "expired"

        listed = client.get("/poa?status=expired", headers=auth_headers)
        assert listed.status_code == 200
        ids = [p["id"] for p in listed.json()["powers"]]
        assert rid in ids

    def test_ownership_isolation(self, auth_headers, stranger_headers):
        create = client.post(
            "/poa",
            headers=auth_headers,
            json={"title": "Só do dono"},
        )
        assert create.status_code == 201
        rid = create.json()["power"]["id"]

        listed = client.get("/poa", headers=stranger_headers)
        assert listed.status_code == 200
        ids = [p["id"] for p in listed.json()["powers"]]
        assert rid not in ids

        revoke = client.post(f"/poa/{rid}/revoke", headers=stranger_headers)
        assert revoke.status_code == 404

        assert PowerOfAttorney is not None
