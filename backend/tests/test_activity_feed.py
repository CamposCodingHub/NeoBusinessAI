"""
Testes: firm activity feed (ActivityEvent + GET /operations/activity).
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_activity_feed.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import ActivityEvent, Base, User, get_db_async  # noqa: E402
from routes.operations_routes import router as operations_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402
from services.activity_feed_service import log_activity  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_activity_feed.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


async def override_get_db_async():
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
    return _make_user("activity.owner@example.com", "Activity Owner")


@pytest.fixture
def other():
    return _make_user("activity.other@example.com", "Other Firm")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def other_auth_headers(other):
    return _headers_for(other)


class TestActivityFeed:
    def test_log_activity_persists(self, owner):
        db = TestingSessionLocal()
        try:
            log_activity(
                db,
                owner.id,
                "intake.lead_create",
                "Lead criado: Acme",
                entity_type="lead",
                entity_id=42,
            )
            row = (
                db.query(ActivityEvent)
                .filter(
                    ActivityEvent.user_id == owner.id,
                    ActivityEvent.action == "intake.lead_create",
                )
                .order_by(ActivityEvent.id.desc())
                .first()
            )
            assert row is not None
            assert row.summary == "Lead criado: Acme"
            assert row.entity_type == "lead"
            assert row.entity_id == 42
        finally:
            db.close()

    def test_get_activity_returns_own_events(self, owner, auth_headers):
        db = TestingSessionLocal()
        try:
            log_activity(db, owner.id, "matter.create", "Matter X", "matter", 1)
            log_activity(db, owner.id, "team.invite", "Convite Y", "team_invite", 2)
        finally:
            db.close()

        resp = client.get("/operations/activity", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["count"] >= 2
        actions = {e["action"] for e in body["events"]}
        assert "matter.create" in actions
        assert "team.invite" in actions
        assert all(e["user_id"] == owner.id for e in body["events"])
        assert len(body["events"]) <= 50

    def test_activity_idor_and_auth(self, owner, other, auth_headers, other_auth_headers):
        db = TestingSessionLocal()
        try:
            log_activity(
                db,
                owner.id,
                "finance.payment_link",
                "Link secreto do owner",
                "invoice",
                99,
            )
        finally:
            db.close()

        assert client.get("/operations/activity").status_code in (401, 403)

        other_resp = client.get("/operations/activity", headers=other_auth_headers)
        assert other_resp.status_code == 200
        other_events = other_resp.json()["events"]
        assert all(e["user_id"] == other.id for e in other_events)
        assert not any(e.get("summary") == "Link secreto do owner" for e in other_events)

        owner_resp = client.get("/operations/activity", headers=auth_headers)
        assert owner_resp.status_code == 200
        assert any(
            e.get("summary") == "Link secreto do owner" for e in owner_resp.json()["events"]
        )

    def test_log_activity_best_effort_never_raises(self, owner):
        """Helper engole falhas (ex.: sessão inválida) sem propagar."""
        class _BrokenSession:
            def add(self, *_a, **_k):
                raise RuntimeError("db down")

            def commit(self):
                raise RuntimeError("db down")

            def rollback(self):
                pass

        log_activity(_BrokenSession(), owner.id, "time.invoice", "não deve quebrar")


class TestOperationsShortcuts:
    def test_shortcuts_include_daytime_modules(self, auth_headers):
        from routes.operations_routes import OPERATIONS_SHORTCUTS

        paths = {item["path"] for item in OPERATIONS_SHORTCUTS}
        for required in (
            "/dashboard/activity",
            "/dashboard/orgs",
            "/dashboard/trust",
            "/dashboard/esign",
            "/dashboard/monitor",
            "/dashboard/finance",
        ):
            assert required in paths

        resp = client.get("/operations/shortcuts", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "shortcuts" in body
        assert len(body["shortcuts"]) >= 6

