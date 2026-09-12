"""
Testes: Trust accounting stub (IOLTA-style ledger) — JWT + ownership.
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_trust_routes.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import (  # noqa: E402
    Base,
    TrustAccount,
    TrustLedgerEntry,
    User,
    get_db,
)
from routes.trust_routes import router as trust_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_trust_routes.db"
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
app.include_router(trust_router)
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
    return _make_user("trust.owner@example.com", "Trust Owner")


@pytest.fixture
def stranger():
    return _make_user("trust.stranger@example.com", "Stranger")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def stranger_headers(stranger):
    return _headers_for(stranger)


class TestTrustRoutes:
    def test_create_and_list_accounts(self, owner, auth_headers):
        created = client.post(
            "/trust/accounts",
            json={"name": "IOLTA Principal", "currency": "BRL"},
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        body = created.json()["account"]
        assert body["name"] == "IOLTA Principal"
        assert body["currency"] == "BRL"
        assert body["user_id"] == owner.id

        listed = client.get("/trust/accounts", headers=auth_headers)
        assert listed.status_code == 200, listed.text
        data = listed.json()
        assert data["count"] >= 1
        assert any(a["id"] == body["id"] for a in data["accounts"])

    def test_ledger_entries_and_balance(self, auth_headers):
        created = client.post(
            "/trust/accounts",
            json={"name": "Ledger Test"},
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        account_id = created.json()["account"]["id"]

        dep = client.post(
            f"/trust/accounts/{account_id}/entries",
            json={"entry_type": "deposit", "amount": 1000.0, "memo": "Retainer"},
            headers=auth_headers,
        )
        assert dep.status_code == 201, dep.text
        assert dep.json()["balance"] == 1000.0

        wd = client.post(
            f"/trust/accounts/{account_id}/entries",
            json={"entry_type": "withdrawal", "amount": 200.0, "memo": "Fee transfer"},
            headers=auth_headers,
        )
        assert wd.status_code == 201, wd.text
        assert wd.json()["balance"] == 800.0

        tr = client.post(
            f"/trust/accounts/{account_id}/entries",
            json={"entry_type": "transfer", "amount": 50.0, "memo": "Transfer out"},
            headers=auth_headers,
        )
        assert tr.status_code == 201, tr.text
        assert tr.json()["balance"] == 750.0

        bal = client.get(f"/trust/accounts/{account_id}/balance", headers=auth_headers)
        assert bal.status_code == 200, bal.text
        assert bal.json()["balance"] == 750.0
        assert "not a bank" in bal.json()["disclaimer"].lower() or "PIX" in bal.json()["disclaimer"]

        ledger = client.get(f"/trust/accounts/{account_id}/ledger", headers=auth_headers)
        assert ledger.status_code == 200, ledger.text
        assert ledger.json()["count"] == 3
        assert ledger.json()["balance"] == 750.0

    def test_idor_other_user_gets_404(self, auth_headers, stranger_headers):
        created = client.post(
            "/trust/accounts",
            json={"name": "Private Trust"},
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        account_id = created.json()["account"]["id"]

        for path in (
            f"/trust/accounts/{account_id}/ledger",
            f"/trust/accounts/{account_id}/balance",
        ):
            resp = client.get(path, headers=stranger_headers)
            assert resp.status_code == 404, resp.text

        entry = client.post(
            f"/trust/accounts/{account_id}/entries",
            json={"entry_type": "deposit", "amount": 10},
            headers=stranger_headers,
        )
        assert entry.status_code == 404, entry.text

    def test_auth_required(self):
        assert client.get("/trust/accounts").status_code in (401, 403)
        assert client.post("/trust/accounts", json={"name": "X"}).status_code in (401, 403)

    def test_invalid_entry_type_and_amount(self, auth_headers):
        created = client.post(
            "/trust/accounts",
            json={"name": "Validation Trust"},
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        account_id = created.json()["account"]["id"]

        bad_type = client.post(
            f"/trust/accounts/{account_id}/entries",
            json={"entry_type": "pix", "amount": 10},
            headers=auth_headers,
        )
        assert bad_type.status_code == 400, bad_type.text

        bad_amount = client.post(
            f"/trust/accounts/{account_id}/entries",
            json={"entry_type": "deposit", "amount": 0},
            headers=auth_headers,
        )
        assert bad_amount.status_code == 422  # pydantic gt=0

    def test_adjustment_affects_balance(self, auth_headers):
        created = client.post(
            "/trust/accounts",
            json={"name": "Adj Trust"},
            headers=auth_headers,
        )
        account_id = created.json()["account"]["id"]
        client.post(
            f"/trust/accounts/{account_id}/entries",
            json={"entry_type": "deposit", "amount": 100},
            headers=auth_headers,
        )
        adj = client.post(
            f"/trust/accounts/{account_id}/entries",
            json={"entry_type": "adjustment", "amount": 25, "memo": "Correction"},
            headers=auth_headers,
        )
        assert adj.status_code == 201, adj.text
        assert adj.json()["balance"] == 125.0
