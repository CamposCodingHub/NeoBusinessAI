"""
Testes: /matter-notes — anotações do caso (JWT + ownership).
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_matter_notes.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, MatterNote, User, get_db  # noqa: E402
from routes.matter_notes_routes import router as matter_notes_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_matter_notes.db"
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
app.include_router(matter_notes_router)
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
    return _make_user("notes.owner@example.com", "Notes Owner")


@pytest.fixture
def stranger():
    return _make_user("notes.stranger@example.com", "Stranger")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def stranger_headers(stranger):
    return _headers_for(stranger)


class TestMatterNotes:
    def test_requires_auth(self):
        resp = client.get("/matter-notes")
        assert resp.status_code in (401, 403)

    def test_create_pin_delete(self, auth_headers, owner):
        create = client.post(
            "/matter-notes",
            headers=auth_headers,
            json={
                "body": "Cliente pediu prazo para juntar extratos até sexta.",
                "pinned": True,
            },
        )
        assert create.status_code == 201, create.text
        note = create.json()["note"]
        assert note["user_id"] == owner.id
        assert note["pinned"] is True
        nid = note["id"]

        listed = client.get("/matter-notes", headers=auth_headers)
        assert listed.status_code == 200
        assert any(n["id"] == nid for n in listed.json()["notes"])

        unpin = client.patch(
            f"/matter-notes/{nid}/pin",
            headers=auth_headers,
            json={"pinned": False},
        )
        assert unpin.status_code == 200
        assert unpin.json()["note"]["pinned"] is False

        deleted = client.delete(f"/matter-notes/{nid}", headers=auth_headers)
        assert deleted.status_code == 200
        assert deleted.json()["deleted_id"] == nid

    def test_ownership_isolation(self, auth_headers, stranger_headers):
        create = client.post(
            "/matter-notes",
            headers=auth_headers,
            json={"body": "Segredo do dono"},
        )
        assert create.status_code == 201
        nid = create.json()["note"]["id"]

        listed = client.get("/matter-notes", headers=stranger_headers)
        assert listed.status_code == 200
        assert nid not in [n["id"] for n in listed.json()["notes"]]

        delete = client.delete(f"/matter-notes/{nid}", headers=stranger_headers)
        assert delete.status_code == 404
        assert MatterNote is not None
