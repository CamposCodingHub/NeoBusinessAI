"""
Testes: /matter-docs — checklist documental (JWT + ownership).
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_matter_docs.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, MatterDocItem, User, get_db  # noqa: E402
from routes.matter_docs_routes import router as matter_docs_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_matter_docs.db"
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
app.include_router(matter_docs_router)
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
    return _make_user("docs.owner@example.com", "Docs Owner")


@pytest.fixture
def stranger():
    return _make_user("docs.stranger@example.com", "Stranger")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def stranger_headers(stranger):
    return _headers_for(stranger)


class TestMatterDocs:
    def test_requires_auth(self):
        resp = client.get("/matter-docs")
        assert resp.status_code in (401, 403)

    def test_create_seed_mark_received(self, auth_headers, owner):
        create = client.post(
            "/matter-docs",
            headers=auth_headers,
            json={"title": "Contrato social", "notes": "versão consolidada"},
        )
        assert create.status_code == 201, create.text
        item = create.json()["item"]
        assert item["user_id"] == owner.id
        assert item["status"] == "pending"
        iid = item["id"]

        seed = client.post("/matter-docs/seed-intake", headers=auth_headers)
        assert seed.status_code == 201
        assert seed.json()["count"] == 5

        listed = client.get("/matter-docs?pending_only=true", headers=auth_headers)
        assert listed.status_code == 200
        assert listed.json()["pending_count"] >= 6

        done = client.patch(
            f"/matter-docs/{iid}/status",
            headers=auth_headers,
            json={"status": "received"},
        )
        assert done.status_code == 200
        assert done.json()["item"]["status"] == "received"

    def test_ownership_isolation(self, auth_headers, stranger_headers):
        create = client.post(
            "/matter-docs",
            headers=auth_headers,
            json={"title": "Só do dono"},
        )
        assert create.status_code == 201
        iid = create.json()["item"]["id"]

        listed = client.get("/matter-docs", headers=stranger_headers)
        assert listed.status_code == 200
        assert iid not in [x["id"] for x in listed.json()["items"]]

        patch = client.patch(
            f"/matter-docs/{iid}/status",
            headers=stranger_headers,
            json={"status": "waived"},
        )
        assert patch.status_code == 404
        assert MatterDocItem is not None
