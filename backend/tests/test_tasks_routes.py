"""
Testes: /tasks — checklist operacional (JWT + ownership).
"""

import os
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_tasks_routes.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, OfficeTask, User, get_db  # noqa: E402
from routes.tasks_routes import router as tasks_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_tasks_routes.db"
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
app.include_router(tasks_router)
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
    return _make_user("tasks.owner@example.com", "Tasks Owner")


@pytest.fixture
def stranger():
    return _make_user("tasks.stranger@example.com", "Stranger")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def stranger_headers(stranger):
    return _headers_for(stranger)


class TestTasksRoutes:
    def test_requires_auth(self):
        resp = client.get("/tasks")
        assert resp.status_code in (401, 403)

    def test_create_list_complete(self, auth_headers, owner):
        due = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        create = client.post(
            "/tasks",
            headers=auth_headers,
            json={
                "title": "Protocolar petição",
                "due_at": due,
                "priority": "high",
            },
        )
        assert create.status_code == 201, create.text
        body = create.json()["task"]
        assert body["status"] == "open"
        assert body["user_id"] == owner.id
        tid = body["id"]

        listed = client.get("/tasks?open_only=true", headers=auth_headers)
        assert listed.status_code == 200
        assert any(t["id"] == tid for t in listed.json()["tasks"])

        done = client.patch(
            f"/tasks/{tid}/status",
            headers=auth_headers,
            json={"status": "done"},
        )
        assert done.status_code == 200
        assert done.json()["task"]["status"] == "done"
        assert done.json()["task"]["completed_at"] is not None

    def test_ownership_isolation(self, auth_headers, stranger_headers):
        create = client.post(
            "/tasks",
            headers=auth_headers,
            json={"title": "Só do dono"},
        )
        assert create.status_code == 201
        tid = create.json()["task"]["id"]

        listed = client.get("/tasks", headers=stranger_headers)
        assert listed.status_code == 200
        assert tid not in [t["id"] for t in listed.json()["tasks"]]

        patch = client.patch(
            f"/tasks/{tid}/status",
            headers=stranger_headers,
            json={"status": "done"},
        )
        assert patch.status_code == 404
        assert OfficeTask is not None
