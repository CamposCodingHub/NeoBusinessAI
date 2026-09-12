"""
Testes: /finance/retainers — honorários antecipados (JWT + ownership + apply).
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_finance_retainers.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, Client, FeeRetainer, User, get_db  # noqa: E402
from routes.finance_routes import router as finance_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_finance_retainers.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(finance_router)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


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


def _make_client(user_id: int, name: str) -> Client:
    db = TestingSessionLocal()
    try:
        c = Client(user_id=user_id, name=name, status="active")
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
    return _make_user("retainers.owner@example.com", "Retainers Owner")


@pytest.fixture
def stranger():
    return _make_user("retainers.stranger@example.com", "Stranger")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def stranger_headers(stranger):
    return _headers_for(stranger)


@pytest.fixture
def owned_client(owner):
    return _make_client(owner.id, "Cliente Retainer")


class TestFeeRetainers:
    def test_requires_jwt(self):
        resp = client.get("/finance/retainers")
        assert resp.status_code in (401, 403)

    def test_create_and_list(self, owner, auth_headers, owned_client):
        created = client.post(
            "/finance/retainers",
            json={
                "client_id": owned_client.id,
                "amount": 5000.0,
                "notes": "Honorários antecipados — fase inicial",
            },
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        body = created.json()
        assert body["client_id"] == owned_client.id
        assert body["amount"] == 5000.0
        assert body["amount_applied"] == 0.0
        assert body["remaining"] == 5000.0
        assert body["status"] == "open"
        assert body["user_id"] == owner.id
        retainer_id = body["id"]

        listed = client.get("/finance/retainers", headers=auth_headers)
        assert listed.status_code == 200
        assert listed.json()["count"] >= 1
        assert any(i["id"] == retainer_id for i in listed.json()["items"])

    def test_apply_partial_then_exhaust(self, auth_headers, owned_client):
        created = client.post(
            "/finance/retainers",
            json={"client_id": owned_client.id, "amount": 1000},
            headers=auth_headers,
        )
        assert created.status_code == 201
        rid = created.json()["id"]

        partial = client.post(
            f"/finance/retainers/{rid}/apply",
            json={"amount": 400},
            headers=auth_headers,
        )
        assert partial.status_code == 200, partial.text
        p = partial.json()
        assert p["amount_applied"] == 400.0
        assert p["remaining"] == 600.0
        assert p["status"] == "partially_applied"

        exhaust = client.post(
            f"/finance/retainers/{rid}/apply",
            json={"amount": 600},
            headers=auth_headers,
        )
        assert exhaust.status_code == 200, exhaust.text
        e = exhaust.json()
        assert e["amount_applied"] == 1000.0
        assert e["remaining"] == 0.0
        assert e["status"] == "exhausted"

        over = client.post(
            f"/finance/retainers/{rid}/apply",
            json={"amount": 1},
            headers=auth_headers,
        )
        assert over.status_code == 400

    def test_apply_rejects_over_balance(self, auth_headers, owned_client):
        created = client.post(
            "/finance/retainers",
            json={"client_id": owned_client.id, "amount": 200},
            headers=auth_headers,
        )
        rid = created.json()["id"]

        bad = client.post(
            f"/finance/retainers/{rid}/apply",
            json={"amount": 250},
            headers=auth_headers,
        )
        assert bad.status_code == 400

        zero = client.post(
            f"/finance/retainers/{rid}/apply",
            json={"amount": 0},
            headers=auth_headers,
        )
        assert zero.status_code == 400

    def test_ownership_isolation(
        self, owner, auth_headers, stranger_headers, owned_client
    ):
        created = client.post(
            "/finance/retainers",
            json={"client_id": owned_client.id, "amount": 800, "notes": "privado"},
            headers=auth_headers,
        )
        assert created.status_code == 201
        rid = created.json()["id"]

        denied = client.post(
            f"/finance/retainers/{rid}/apply",
            json={"amount": 100},
            headers=stranger_headers,
        )
        assert denied.status_code == 404

        listed = client.get("/finance/retainers", headers=stranger_headers)
        assert listed.status_code == 200
        assert all(i["id"] != rid for i in listed.json()["items"])

        db = TestingSessionLocal()
        try:
            row = db.query(FeeRetainer).filter(FeeRetainer.id == rid).first()
            assert row is not None
            assert row.user_id == owner.id
            assert row.amount_applied == 0
            assert row.status == "open"
        finally:
            db.close()

    def test_validation_requires_client_and_amount(self, auth_headers):
        missing_client = client.post(
            "/finance/retainers",
            json={"amount": 100},
            headers=auth_headers,
        )
        assert missing_client.status_code == 400

        bad_amt = client.post(
            "/finance/retainers",
            json={"client_id": 1, "amount": -10},
            headers=auth_headers,
        )
        assert bad_amt.status_code == 400
