"""
Testes: Agenda / audiências stub — JWT + ownership + from/to filter.
"""

import os
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_agenda_routes.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import (  # noqa: E402
    Base,
    Hearing,
    HearingPrepItem,
    User,
    get_db,
)
from routes.agenda_routes import router as agenda_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_agenda_routes.db"
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
app.include_router(agenda_router)
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
    return _make_user("agenda.owner@example.com", "Agenda Owner")


@pytest.fixture
def stranger():
    return _make_user("agenda.stranger@example.com", "Stranger")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def stranger_headers(stranger):
    return _headers_for(stranger)


class TestAgendaHearings:
    def test_create_and_list_hearings(self, owner, auth_headers):
        when = datetime(2026, 9, 15, 14, 0, tzinfo=timezone.utc)
        created = client.post(
            "/agenda/hearings",
            json={
                "title": "Audiência trabalhista — reclamante",
                "hearing_at": when.isoformat(),
                "location": "Fórum Central, sala 12",
                "notes": "Levar procuração",
            },
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        body = created.json()["hearing"]
        assert body["title"].startswith("Audiência trabalhista")
        assert body["status"] == "scheduled"
        assert body["user_id"] == owner.id
        assert body["location"] == "Fórum Central, sala 12"
        assert Hearing is not None

        listed = client.get("/agenda/hearings", headers=auth_headers)
        assert listed.status_code == 200, listed.text
        data = listed.json()
        assert data["count"] >= 1
        assert any(h["id"] == body["id"] for h in data["hearings"])

    def test_list_from_to_filter(self, auth_headers):
        base = datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)
        early = client.post(
            "/agenda/hearings",
            json={
                "title": "Compromisso cedo",
                "hearing_at": base.isoformat(),
            },
            headers=auth_headers,
        )
        late = client.post(
            "/agenda/hearings",
            json={
                "title": "Compromisso tarde",
                "hearing_at": (base + timedelta(days=10)).isoformat(),
            },
            headers=auth_headers,
        )
        assert early.status_code == 201 and late.status_code == 201

        window = client.get(
            "/agenda/hearings",
            params={
                "from": (base - timedelta(hours=1)).isoformat(),
                "to": (base + timedelta(days=1)).isoformat(),
            },
            headers=auth_headers,
        )
        assert window.status_code == 200, window.text
        titles = [h["title"] for h in window.json()["hearings"]]
        assert "Compromisso cedo" in titles
        assert "Compromisso tarde" not in titles

    def test_patch_status(self, auth_headers):
        created = client.post(
            "/agenda/hearings",
            json={
                "title": "Conciliação",
                "hearing_at": datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc).isoformat(),
            },
            headers=auth_headers,
        )
        hearing_id = created.json()["hearing"]["id"]

        patched = client.patch(
            f"/agenda/hearings/{hearing_id}",
            json={"status": "done"},
            headers=auth_headers,
        )
        assert patched.status_code == 200, patched.text
        assert patched.json()["hearing"]["status"] == "done"

        bad = client.patch(
            f"/agenda/hearings/{hearing_id}",
            json={"status": "nope"},
            headers=auth_headers,
        )
        assert bad.status_code == 400

    def test_idor_other_user_gets_404(self, auth_headers, stranger_headers):
        created = client.post(
            "/agenda/hearings",
            json={
                "title": "Privada",
                "hearing_at": datetime(2026, 12, 1, 11, 0, tzinfo=timezone.utc).isoformat(),
            },
            headers=auth_headers,
        )
        hearing_id = created.json()["hearing"]["id"]

        assert (
            client.patch(
                f"/agenda/hearings/{hearing_id}",
                json={"status": "cancelled"},
                headers=stranger_headers,
            ).status_code
            == 404
        )

    def test_auth_required(self):
        assert client.get("/agenda/hearings").status_code in (401, 403)
        assert client.post(
            "/agenda/hearings",
            json={
                "title": "Sem auth",
                "hearing_at": datetime(2026, 9, 20, 10, 0, tzinfo=timezone.utc).isoformat(),
            },
        ).status_code in (401, 403)

    def test_hearing_prep_seed_and_complete(self, auth_headers, stranger_headers):
        created = client.post(
            "/agenda/hearings",
            json={
                "title": "Audiência com prep",
                "hearing_at": datetime(2026, 10, 1, 14, 0, tzinfo=timezone.utc).isoformat(),
            },
            headers=auth_headers,
        )
        assert created.status_code == 201
        hid = created.json()["hearing"]["id"]

        seed = client.post(f"/agenda/hearings/{hid}/prep/seed", headers=auth_headers)
        assert seed.status_code == 201, seed.text
        assert seed.json()["count"] == 5
        item_id = seed.json()["items"][0]["id"]

        listed = client.get(f"/agenda/hearings/{hid}/prep", headers=auth_headers)
        assert listed.status_code == 200
        assert listed.json()["pending_count"] == 5

        done = client.patch(
            f"/agenda/prep/{item_id}/status",
            headers=auth_headers,
            json={"status": "done"},
        )
        assert done.status_code == 200
        assert done.json()["item"]["status"] == "done"

        # stranger cannot see prep
        assert (
            client.get(f"/agenda/hearings/{hid}/prep", headers=stranger_headers).status_code
            == 404
        )
        assert HearingPrepItem is not None
