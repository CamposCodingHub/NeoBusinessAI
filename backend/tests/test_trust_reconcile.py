"""
Testes: Trust three-way reconciliation stub (book / clients / unallocated).
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_trust_reconcile.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import (  # noqa: E402
    Base,
    User,
    get_db,
)
from routes.trust_routes import router as trust_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_trust_reconcile.db"
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
    return _make_user("trust.reconcile.owner@example.com", "Reconcile Owner")


@pytest.fixture
def stranger():
    return _make_user("trust.reconcile.stranger@example.com", "Stranger")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def stranger_headers(stranger):
    return _headers_for(stranger)


@pytest.fixture
def account_id(auth_headers):
    created = client.post(
        "/trust/accounts",
        json={"name": "Reconcile Stub"},
        headers=auth_headers,
    )
    assert created.status_code == 201, created.text
    return created.json()["account"]["id"]


class TestTrustReconcile:
    def test_reconcile_splits_client_and_unallocated(self, auth_headers, account_id):
        # Unallocated deposit
        r1 = client.post(
            f"/trust/accounts/{account_id}/entries",
            json={"entry_type": "deposit", "amount": 500.0, "memo": "Float"},
            headers=auth_headers,
        )
        assert r1.status_code == 201, r1.text

        # Client 11: deposit 1000, withdrawal 200 → 800
        r2 = client.post(
            f"/trust/accounts/{account_id}/entries",
            json={
                "entry_type": "deposit",
                "amount": 1000.0,
                "client_id": 11,
                "memo": "Retainer A",
            },
            headers=auth_headers,
        )
        assert r2.status_code == 201, r2.text
        r3 = client.post(
            f"/trust/accounts/{account_id}/entries",
            json={
                "entry_type": "withdrawal",
                "amount": 200.0,
                "client_id": 11,
                "memo": "Fee A",
            },
            headers=auth_headers,
        )
        assert r3.status_code == 201, r3.text

        # Client 22: deposit 300
        r4 = client.post(
            f"/trust/accounts/{account_id}/entries",
            json={
                "entry_type": "deposit",
                "amount": 300.0,
                "client_id": 22,
                "memo": "Retainer B",
            },
            headers=auth_headers,
        )
        assert r4.status_code == 201, r4.text

        resp = client.get(
            f"/trust/accounts/{account_id}/reconcile",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["book_balance"] == 1600.0  # 500 + 800 + 300
        assert body["unallocated_balance"] == 500.0
        assert body["note"] == "stub — not bank feed"
        assert "as_of" in body and body["as_of"]

        by_client = {row["client_id"]: row["balance"] for row in body["client_subtotals"]}
        assert by_client[11] == 800.0
        assert by_client[22] == 300.0
        # book = clients + unallocated
        assert round(
            sum(by_client.values()) + body["unallocated_balance"], 2
        ) == body["book_balance"]

    def test_reconcile_idor_and_empty_account(self, auth_headers, stranger_headers, account_id):
        empty = client.get(
            f"/trust/accounts/{account_id}/reconcile",
            headers=auth_headers,
        )
        assert empty.status_code == 200, empty.text
        body = empty.json()
        assert body["book_balance"] == 0.0
        assert body["unallocated_balance"] == 0.0
        assert body["client_subtotals"] == []
        assert body["note"] == "stub — not bank feed"

        forbidden = client.get(
            f"/trust/accounts/{account_id}/reconcile",
            headers=stranger_headers,
        )
        assert forbidden.status_code == 404, forbidden.text

        assert client.get(
            f"/trust/accounts/{account_id}/reconcile"
        ).status_code in (401, 403)
