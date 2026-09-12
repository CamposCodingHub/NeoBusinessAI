"""
Testes: DJEn/intimação monitoring stub — JWT + ownership.
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_monitor_routes.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import (  # noqa: E402
    Base,
    IntimacaoEvent,
    MonitoredProcess,
    User,
    get_db,
)
from routes.monitor_routes import router as monitor_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_monitor_routes.db"
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
app.include_router(monitor_router)
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
    return _make_user("monitor.owner@example.com", "Monitor Owner")


@pytest.fixture
def stranger():
    return _make_user("monitor.stranger@example.com", "Stranger")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def stranger_headers(stranger):
    return _headers_for(stranger)


class TestMonitorRoutes:
    def test_create_and_list_processes(self, owner, auth_headers):
        created = client.post(
            "/monitor/processes",
            json={
                "process_number": "0001234-56.2024.8.26.0100",
                "court": "TJSP",
                "oab_number": "SP123456",
            },
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        body = created.json()["process"]
        assert body["process_number"] == "0001234-56.2024.8.26.0100"
        assert body["court"] == "TJSP"
        assert body["status"] == "active"
        assert body["user_id"] == owner.id
        assert "stub" in created.json().get("note", "").lower()

        listed = client.get("/monitor/processes", headers=auth_headers)
        assert listed.status_code == 200, listed.text
        data = listed.json()
        assert data["count"] >= 1
        assert any(p["id"] == body["id"] for p in data["processes"])

    def test_poll_stub_creates_fake_event(self, auth_headers):
        created = client.post(
            "/monitor/processes",
            json={"process_number": "1111111-11.2024.8.26.0001"},
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        proc_id = created.json()["process"]["id"]

        polled = client.post(
            f"/monitor/processes/{proc_id}/poll-stub", headers=auth_headers
        )
        assert polled.status_code == 200, polled.text
        payload = polled.json()
        event = payload["event"]
        assert event["source"] == "stub"
        assert "[STUB]" in event["title"]
        assert "stub" in (event["summary"] or "").lower() or "NÃO" in (event["summary"] or "")
        assert payload["process"]["last_checked_at"] is not None
        assert "stub" in payload.get("note", "").lower()

        events = client.get(
            f"/monitor/processes/{proc_id}/events", headers=auth_headers
        )
        assert events.status_code == 200, events.text
        assert events.json()["count"] >= 1
        assert any(e["id"] == event["id"] for e in events.json()["events"])

    def test_acknowledge_event(self, auth_headers):
        created = client.post(
            "/monitor/processes",
            json={"process_number": "2222222-22.2024.8.26.0002"},
            headers=auth_headers,
        )
        proc_id = created.json()["process"]["id"]
        polled = client.post(
            f"/monitor/processes/{proc_id}/poll-stub", headers=auth_headers
        )
        event_id = polled.json()["event"]["id"]
        assert polled.json()["event"]["acknowledged"] is False

        acked = client.post(f"/monitor/events/{event_id}/ack", headers=auth_headers)
        assert acked.status_code == 200, acked.text
        assert acked.json()["event"]["acknowledged"] is True

    def test_idor_other_user_gets_404(self, auth_headers, stranger_headers):
        created = client.post(
            "/monitor/processes",
            json={"process_number": "3333333-33.2024.8.26.0003"},
            headers=auth_headers,
        )
        proc_id = created.json()["process"]["id"]
        polled = client.post(
            f"/monitor/processes/{proc_id}/poll-stub", headers=auth_headers
        )
        event_id = polled.json()["event"]["id"]

        assert (
            client.post(
                f"/monitor/processes/{proc_id}/poll-stub", headers=stranger_headers
            ).status_code
            == 404
        )
        assert (
            client.get(
                f"/monitor/processes/{proc_id}/events", headers=stranger_headers
            ).status_code
            == 404
        )
        assert (
            client.post(
                f"/monitor/events/{event_id}/ack", headers=stranger_headers
            ).status_code
            == 404
        )

    def test_auth_required(self):
        assert client.get("/monitor/processes").status_code in (401, 403)
        assert client.post(
            "/monitor/processes",
            json={"process_number": "0000000-00.2024.8.26.0000"},
        ).status_code in (401, 403)
