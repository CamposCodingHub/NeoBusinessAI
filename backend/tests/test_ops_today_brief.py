"""
Testes: /operations/today/brief — markdown matinal.
"""

import os
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_ops_today_brief.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, Deadline, User, get_db_async  # noqa: E402
from routes.operations_routes import router as operations_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ops_today_brief.db"
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


@pytest.fixture
def auth_headers():
    owner = _make_user("brief.owner@example.com", "Brief Owner")
    token = create_access_token(user_id=str(owner.id), role=Role.USER)
    db = TestingSessionLocal()
    try:
        db.add(
            Deadline(
                user_id=owner.id,
                description="Contestação",
                due_date=datetime.now(timezone.utc).replace(hour=17),
                urgency="high",
                is_completed=False,
            )
        )
        db.commit()
    finally:
        db.close()
    return {"Authorization": f"Bearer {token}"}


class TestTodayBrief:
    def test_requires_auth(self):
        resp = client.get("/operations/today/brief")
        assert resp.status_code in (401, 403)

    def test_markdown_brief(self, auth_headers):
        resp = client.get("/operations/today/brief", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        md = data["markdown"]
        assert "# Briefing operacional" in md
        assert "## Prazos" in md
        assert "Contestação" in md
