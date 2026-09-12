"""
Testes: TeamInvite stub (POST/GET/revoke/accept) — ownership JWT + IDOR-safe.
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_team_invites.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, TeamInvite, User, get_db  # noqa: E402
from routes.team_routes import router as team_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_team_invites.db"
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
app.include_router(team_router)
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
    return _make_user("team.owner@example.com", "Team Owner")


@pytest.fixture
def other():
    return _make_user("team.other@example.com", "Other Firm")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def other_auth_headers(other):
    return _headers_for(other)


class TestTeamInvites:
    def test_create_and_list_invites(self, owner, auth_headers):
        created = client.post(
            "/team/invites",
            json={"email": "colleague@example.com", "role": "user"},
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        body = created.json()["invite"]
        assert body["email"] == "colleague@example.com"
        assert body["status"] == "pending"
        assert body["owner_user_id"] == owner.id
        assert body["token"]  # token returned once on create
        assert body["role"] == "user"

        listed = client.get("/team/invites", headers=auth_headers)
        assert listed.status_code == 200, listed.text
        data = listed.json()
        assert data["count"] >= 1
        assert any(i["id"] == body["id"] for i in data["invites"])
        # list must not leak tokens
        assert all("token" not in i for i in data["invites"])

    def test_idor_list_and_revoke(self, owner, auth_headers, other_auth_headers):
        created = client.post(
            "/team/invites",
            json={"email": "secret@example.com", "role": "admin"},
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        invite_id = created.json()["invite"]["id"]

        other_list = client.get("/team/invites", headers=other_auth_headers)
        assert other_list.status_code == 200
        assert all(i["id"] != invite_id for i in other_list.json()["invites"])

        revoke_idor = client.post(
            f"/team/invites/{invite_id}/revoke",
            headers=other_auth_headers,
        )
        assert revoke_idor.status_code == 404

        db = TestingSessionLocal()
        try:
            stored = db.query(TeamInvite).filter(TeamInvite.id == invite_id).first()
            assert stored.status == "pending"
        finally:
            db.close()

    def test_accept_creates_stub_user(self, auth_headers):
        created = client.post(
            "/team/invites",
            json={"email": "new.member@example.com", "role": "user"},
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        token = created.json()["invite"]["token"]

        accepted = client.post(
            "/team/invites/accept",
            json={"token": token},
        )
        assert accepted.status_code == 200, accepted.text
        body = accepted.json()
        assert body["invite"]["status"] == "accepted"
        assert body["invite"]["accepted_at"]
        assert body["created_stub"] is True
        assert body["linked_user_id"]
        assert "Stub" in (body.get("note") or "")

        db = TestingSessionLocal()
        try:
            stub = db.query(User).filter(User.email == "new.member@example.com").first()
            assert stub is not None
            assert stub.id == body["linked_user_id"]
        finally:
            db.close()

    def test_accept_links_existing_user(self, auth_headers):
        existing = _make_user("already@example.com", "Already Here")
        created = client.post(
            "/team/invites",
            json={"email": "already@example.com", "role": "user"},
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        token = created.json()["invite"]["token"]

        accepted = client.post(
            "/team/invites/accept",
            json={"token": token},
        )
        assert accepted.status_code == 200, accepted.text
        body = accepted.json()
        assert body["created_stub"] is False
        assert body["linked_user_id"] == existing.id
        assert "existente" in (body.get("note") or "").lower()

    def test_auth_required_for_owner_routes(self):
        assert client.get("/team/invites").status_code in (401, 403)
        assert client.post(
            "/team/invites",
            json={"email": "x@example.com"},
        ).status_code in (401, 403)
        assert client.post("/team/invites/99/revoke").status_code in (401, 403)

    def test_owner_can_revoke_pending(self, auth_headers):
        created = client.post(
            "/team/invites",
            json={"email": "revoke.me@example.com", "role": "user"},
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        invite_id = created.json()["invite"]["id"]

        revoked = client.post(
            f"/team/invites/{invite_id}/revoke",
            headers=auth_headers,
        )
        assert revoked.status_code == 200, revoked.text
        assert revoked.json()["invite"]["status"] == "revoked"
