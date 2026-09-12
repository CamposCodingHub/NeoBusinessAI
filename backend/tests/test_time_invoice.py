"""
Testes: criar Invoice draft a partir de time entries faturáveis.
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_time_invoice.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, Client, Invoice, TimeEntry, User, get_db  # noqa: E402
from routes.time_routes import router as time_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_time_invoice.db"
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
app.include_router(time_router)
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


def _make_client(user_id: int, name: str = "Cliente Teste") -> Client:
    db = TestingSessionLocal()
    try:
        c = Client(user_id=user_id, name=name, email=f"{name.lower().replace(' ', '.')}@ex.com")
        db.add(c)
        db.commit()
        db.refresh(c)
        return c
    finally:
        db.close()


def _headers_for(user: User) -> dict:
    token = create_access_token(user_id=str(user.id), role=Role.USER)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def owner():
    return _make_user("invoice.owner@example.com", "Invoice Owner")


@pytest.fixture
def other():
    return _make_user("invoice.other@example.com", "Other Firm")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def other_auth_headers(other):
    return _headers_for(other)


def _create_entry(headers, **kwargs):
    payload = {
        "description": kwargs.get("description", "Trabalho jurídico"),
        "minutes": kwargs.get("minutes", 60),
        "hourly_rate": kwargs.get("hourly_rate", 200.0),
        "billable": kwargs.get("billable", True),
    }
    if "client_id" in kwargs:
        payload["client_id"] = kwargs["client_id"]
    if "matter_id" in kwargs:
        payload["matter_id"] = kwargs["matter_id"]
    resp = client.post("/time/entries", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()["entry"]


class TestTimeInvoice:
    def test_invoice_from_entry_ids(self, auth_headers):
        e1 = _create_entry(auth_headers, description="A", minutes=60, hourly_rate=300.0)
        e2 = _create_entry(auth_headers, description="B", minutes=30, hourly_rate=300.0)
        # 60min*300 + 30min*300 = 300 + 150 = 450

        resp = client.post(
            "/time/entries/invoice",
            json={"entry_ids": [e1["id"], e2["id"]]},
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["total"] == 450.0
        assert data["entries_count"] == 2
        assert set(data["entry_ids"]) == {e1["id"], e2["id"]}
        assert data["invoice"]["status"] == "pending"
        assert data["invoice"]["total"] == 450.0
        assert data["invoice"]["invoice_type"] == "time_entries"

        listed = client.get("/time/entries", headers=auth_headers)
        by_id = {e["id"]: e for e in listed.json()["entries"]}
        assert by_id[e1["id"]]["invoiced_at"] is not None
        assert by_id[e2["id"]]["invoiced_at"] is not None

        db = TestingSessionLocal()
        try:
            inv = db.query(Invoice).filter(Invoice.id == data["invoice"]["id"]).first()
            assert inv is not None
            assert inv.user_id is not None
            assert inv.total_cents == 45000
        finally:
            db.close()

    def test_invoice_skips_zero_rate_and_non_billable(self, auth_headers):
        with_rate = _create_entry(
            auth_headers, description="Com taxa", minutes=60, hourly_rate=100.0
        )
        no_rate = _create_entry(
            auth_headers, description="Sem taxa", minutes=60, hourly_rate=None
        )
        # Explicit null rate via DB for no_rate — API may omit; patch if needed
        db = TestingSessionLocal()
        try:
            entry = db.query(TimeEntry).filter(TimeEntry.id == no_rate["id"]).first()
            entry.hourly_rate = None
            db.commit()
        finally:
            db.close()

        non_bill = _create_entry(
            auth_headers,
            description="Não faturável",
            minutes=60,
            hourly_rate=100.0,
            billable=False,
        )

        resp = client.post(
            "/time/entries/invoice",
            json={"entry_ids": [with_rate["id"], no_rate["id"], non_bill["id"]]},
            headers=auth_headers,
        )
        # non_billable / already filtered out of query → 404 for missing ids
        assert resp.status_code == 404

        resp_ok = client.post(
            "/time/entries/invoice",
            json={"entry_ids": [with_rate["id"], no_rate["id"]]},
            headers=auth_headers,
        )
        assert resp_ok.status_code == 201, resp_ok.text
        assert resp_ok.json()["total"] == 100.0
        assert resp_ok.json()["entries_count"] == 1
        assert resp_ok.json()["entry_ids"] == [with_rate["id"]]

    def test_invoice_by_client_uninvoiced(self, owner, auth_headers):
        cl = _make_client(owner.id, "Cliente Fatura")
        e1 = _create_entry(
            auth_headers,
            description="Cliente 1h",
            minutes=60,
            hourly_rate=250.0,
            client_id=cl.id,
        )
        e2 = _create_entry(
            auth_headers,
            description="Cliente 2h",
            minutes=120,
            hourly_rate=250.0,
            client_id=cl.id,
        )
        # other client should not be included
        other_cl = _make_client(owner.id, "Outro Cliente")
        _create_entry(
            auth_headers,
            description="Outro",
            minutes=60,
            hourly_rate=250.0,
            client_id=other_cl.id,
        )

        resp = client.post(
            "/time/entries/invoice",
            json={"client_id": cl.id},
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        # 250 + 500 = 750
        assert data["total"] == 750.0
        assert set(data["entry_ids"]) == {e1["id"], e2["id"]}
        assert data["invoice"]["client_id"] == cl.id

        # Second call: already invoiced → nothing left
        again = client.post(
            "/time/entries/invoice",
            json={"client_id": cl.id},
            headers=auth_headers,
        )
        assert again.status_code == 400

    def test_idor_cannot_invoice_other_user_entries(
        self, auth_headers, other_auth_headers
    ):
        entry = _create_entry(
            auth_headers, description="Privado", minutes=60, hourly_rate=200.0
        )
        resp = client.post(
            "/time/entries/invoice",
            json={"entry_ids": [entry["id"]]},
            headers=other_auth_headers,
        )
        assert resp.status_code == 404

        # Owner still can
        ok = client.post(
            "/time/entries/invoice",
            json={"entry_ids": [entry["id"]]},
            headers=auth_headers,
        )
        assert ok.status_code == 201, ok.text

    def test_auth_required(self):
        assert (
            client.post(
                "/time/entries/invoice",
                json={"entry_ids": [1]},
            ).status_code
            in (401, 403)
        )

    def test_requires_entry_ids_or_client_matter(self, auth_headers):
        resp = client.post(
            "/time/entries/invoice",
            json={},
            headers=auth_headers,
        )
        assert resp.status_code == 400
