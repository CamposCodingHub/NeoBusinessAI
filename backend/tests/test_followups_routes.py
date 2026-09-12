"""
Testes: /followups — lembretes de retorno (JWT + ownership).
"""

import os
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_followups.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, FollowUp, User, get_db  # noqa: E402
from routes.followups_routes import router as followups_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_followups.db"
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
app.include_router(followups_router)
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
    return _make_user("fu.owner@example.com", "FU Owner")


@pytest.fixture
def stranger():
    return _make_user("fu.stranger@example.com", "Stranger")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def stranger_headers(stranger):
    return _headers_for(stranger)


class TestFollowUps:
    def test_requires_auth(self):
        resp = client.get("/followups")
        assert resp.status_code in (401, 403)

    def test_create_list_complete(self, auth_headers, owner):
        due = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        create = client.post(
            "/followups",
            headers=auth_headers,
            json={
                "subject": "Retornar ligação sobre acordo",
                "due_at": due,
                "notes": "Cliente pediu 48h",
            },
        )
        assert create.status_code == 201, create.text
        body = create.json()["followup"]
        assert body["user_id"] == owner.id
        assert body["status"] == "open"
        fid = body["id"]

        listed = client.get("/followups?open_only=true", headers=auth_headers)
        assert listed.status_code == 200
        assert any(x["id"] == fid for x in listed.json()["followups"])

        done = client.patch(
            f"/followups/{fid}/status",
            headers=auth_headers,
            json={"status": "done"},
        )
        assert done.status_code == 200
        assert done.json()["followup"]["status"] == "done"
        assert done.json()["followup"]["completed_at"] is not None

    def test_ownership_isolation(self, auth_headers, stranger_headers):
        due = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        create = client.post(
            "/followups",
            headers=auth_headers,
            json={"subject": "Só do dono", "due_at": due},
        )
        assert create.status_code == 201
        fid = create.json()["followup"]["id"]

        listed = client.get("/followups", headers=stranger_headers)
        assert listed.status_code == 200
        assert fid not in [x["id"] for x in listed.json()["followups"]]

        patch = client.patch(
            f"/followups/{fid}/status",
            headers=stranger_headers,
            json={"status": "done"},
        )
        assert patch.status_code == 404
        assert FollowUp is not None
