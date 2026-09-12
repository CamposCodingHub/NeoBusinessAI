"""
Testes de preferências de alerta de prazos + digest preview.
App mínimo — evita import pesado de main.
"""

import os
from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_notification_prefs.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, Deadline, NotificationPreference, User, get_db  # noqa: E402
from routes.notification_routes import router as notification_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402
from services.notification_preference_service import (  # noqa: E402
    list_deadlines_needing_alert,
)

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_notification_prefs.db"
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
    finally:
        db.close()


app = FastAPI()
app.include_router(notification_router)
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


def _add_deadline(user_id: int, days_offset: int, completed: bool = False) -> Deadline:
    db = TestingSessionLocal()
    try:
        dl = Deadline(
            user_id=user_id,
            days=abs(days_offset),
            due_date=datetime.utcnow() + timedelta(days=days_offset),
            urgency="high",
            context="Teste",
            description=f"Prazo em {days_offset}d",
            is_completed=completed,
        )
        db.add(dl)
        db.commit()
        db.refresh(dl)
        return dl
    finally:
        db.close()


@pytest.fixture
def owner():
    return _make_user("alerts.owner@example.com", "Alerts Owner")


@pytest.fixture
def other():
    return _make_user("alerts.other@example.com", "Other Firm")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def other_auth_headers(other):
    return _headers_for(other)


class TestNotificationPreferences:
    def test_get_creates_defaults(self, auth_headers, owner):
        res = client.get("/notifications/preferences", headers=auth_headers)
        assert res.status_code == 200, res.text
        pref = res.json()["preferences"]
        assert pref["user_id"] == owner.id
        assert pref["email_enabled"] is True
        assert pref["whatsapp_enabled"] is False
        assert pref["days_before"] == 3
        assert pref["quiet_hours_start"] is None
        assert pref["quiet_hours_end"] is None

        db = TestingSessionLocal()
        try:
            row = (
                db.query(NotificationPreference)
                .filter(NotificationPreference.user_id == owner.id)
                .first()
            )
            assert row is not None
        finally:
            db.close()

    def test_put_updates_preferences(self, auth_headers, owner):
        res = client.put(
            "/notifications/preferences",
            json={
                "email_enabled": False,
                "whatsapp_enabled": True,
                "days_before": 7,
                "quiet_hours_start": 22,
                "quiet_hours_end": 7,
            },
            headers=auth_headers,
        )
        assert res.status_code == 200, res.text
        pref = res.json()["preferences"]
        assert pref["email_enabled"] is False
        assert pref["whatsapp_enabled"] is True
        assert pref["days_before"] == 7
        assert pref["quiet_hours_start"] == 22
        assert pref["quiet_hours_end"] == 7

        again = client.get("/notifications/preferences", headers=auth_headers)
        assert again.json()["preferences"]["days_before"] == 7

    def test_put_rejects_invalid_days_before(self, auth_headers):
        res = client.put(
            "/notifications/preferences",
            json={"days_before": 999},
            headers=auth_headers,
        )
        assert res.status_code == 422

    def test_deadline_digest_preview(self, auth_headers, owner, other, other_auth_headers):
        client.put(
            "/notifications/preferences",
            json={"days_before": 3, "email_enabled": True},
            headers=auth_headers,
        )

        _add_deadline(owner.id, days_offset=1)
        _add_deadline(owner.id, days_offset=2)
        _add_deadline(owner.id, days_offset=10)  # fora da janela
        _add_deadline(owner.id, days_offset=1, completed=True)
        _add_deadline(other.id, days_offset=1)  # outro tenant

        digest = client.get("/notifications/deadline-digest", headers=auth_headers)
        assert digest.status_code == 200, digest.text
        body = digest.json()
        assert body["preview"] is True
        assert body["would_send"] is True
        assert "email" in body["channels"]
        assert body["count"] == 2
        assert all(d["is_completed"] is False for d in body["deadlines"])

        # IDOR: outro user não vê prazos do owner
        other_digest = client.get(
            "/notifications/deadline-digest", headers=other_auth_headers
        )
        assert other_digest.status_code == 200
        other_ids = {d["id"] for d in other_digest.json()["deadlines"]}
        owner_ids = {d["id"] for d in body["deadlines"]}
        assert owner_ids.isdisjoint(other_ids)

    def test_list_deadlines_needing_alert_helper(self, owner):
        _add_deadline(owner.id, days_offset=0)
        _add_deadline(owner.id, days_offset=5)

        db = TestingSessionLocal()
        try:
            within_3 = list_deadlines_needing_alert(db, owner.id, days_before=3)
            assert len(within_3) >= 1
            assert all(
                dl.due_date <= datetime.utcnow() + timedelta(days=3)
                for dl in within_3
            )

            within_7 = list_deadlines_needing_alert(db, owner.id, days_before=7)
            assert len(within_7) >= len(within_3)
        finally:
            db.close()

    def test_auth_required(self):
        assert client.get("/notifications/preferences").status_code == 401
        assert client.get("/notifications/deadline-digest").status_code == 401
        assert (
            client.put(
                "/notifications/preferences", json={"days_before": 5}
            ).status_code
            == 401
        )
