"""
Testes: /operations/today — painel do dia (JWT + ownership).
"""

import os
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_ops_today.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import (  # noqa: E402
    Base,
    Deadline,
    Hearing,
    PowerOfAttorney,
    User,
    get_db_async,
)
from routes.operations_routes import router as operations_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ops_today.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db_async():
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    finally:
        db.close()


app = FastAPI()
app.include_router(operations_router)
app.dependency_overrides[get_db_async] = override_get_db_async
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
    return _make_user("today.owner@example.com", "Today Owner")


@pytest.fixture
def stranger():
    return _make_user("today.stranger@example.com", "Stranger")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def stranger_headers(stranger):
    return _headers_for(stranger)


class TestOperationsToday:
    def test_requires_auth(self):
        resp = client.get("/operations/today")
        assert resp.status_code in (401, 403)

    def test_aggregates_owned_items(self, owner, auth_headers, stranger):
        now = datetime.now(timezone.utc)
        db = TestingSessionLocal()
        try:
            db.add(
                Deadline(
                    user_id=owner.id,
                    description="Contestação",
                    due_date=now.replace(hour=18),
                    urgency="high",
                    is_completed=False,
                )
            )
            db.add(
                Hearing(
                    user_id=owner.id,
                    title="Audiência conciliação",
                    hearing_at=now + timedelta(days=1),
                    status="scheduled",
                )
            )
            db.add(
                PowerOfAttorney(
                    user_id=owner.id,
                    title="Ad judicia",
                    status="active",
                    expires_at=now + timedelta(days=10),
                )
            )
            # Stranger noise — must not leak
            db.add(
                Deadline(
                    user_id=stranger.id,
                    description="Segredo",
                    due_date=now.replace(hour=12),
                    is_completed=False,
                )
            )
            db.commit()
        finally:
            db.close()

        resp = client.get("/operations/today", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        descs = [d.get("description") for d in data["deadlines"]["due_today"]]
        descs += [d.get("description") for d in data["deadlines"]["upcoming"]]
        descs += [d.get("description") for d in data["deadlines"]["overdue"]]
        assert "Contestação" in descs
        assert "Segredo" not in descs
        assert data["hearings_count"] >= 1
        assert any(h["title"].startswith("Audiência") for h in data["hearings"])
        assert data["powers_expiring_count"] >= 1
