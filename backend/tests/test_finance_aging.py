"""
Testes: GET /finance/aging — buckets de contas a receber (JWT + ownership).
"""

import os
from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_finance_aging.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, Invoice, User, get_db  # noqa: E402
from routes.finance_routes import router as finance_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_finance_aging.db"
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


def _headers_for(user: User) -> dict:
    token = create_access_token(user_id=str(user.id), role=Role.USER)
    return {"Authorization": f"Bearer {token}"}


def _create_invoice(
    user_id: int,
    *,
    status: str = "pending",
    total_cents: int = 10000,
    days_ago: int = 0,
    invoice_number: str = None,
) -> Invoice:
    db = TestingSessionLocal()
    try:
        now = datetime.utcnow()
        due = now - timedelta(days=days_ago)
        inv = Invoice(
            user_id=user_id,
            invoice_number=invoice_number or f"FAT-AGE-{user_id}-{days_ago}-{total_cents}",
            description="Aging test",
            amount_cents=total_cents,
            discount_cents=0,
            total_cents=total_cents,
            status=status,
            due_date=due,
            created_at=due,
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)
        return inv
    finally:
        db.close()


@pytest.fixture
def owner():
    return _make_user("aging.owner@example.com", "Aging Owner")


@pytest.fixture
def stranger():
    return _make_user("aging.stranger@example.com", "Stranger")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


class TestFinanceAging:
    def test_aging_requires_jwt(self):
        resp = client.get("/finance/aging")
        assert resp.status_code in (401, 403)

    def test_aging_buckets_and_total(self, owner, auth_headers):
        # clean prior open invoices for deterministic totals
        db = TestingSessionLocal()
        try:
            db.query(Invoice).filter(Invoice.user_id == owner.id).delete()
            db.commit()
        finally:
            db.close()

        _create_invoice(owner.id, total_cents=10000, days_ago=10, invoice_number="A-CUR")
        _create_invoice(owner.id, total_cents=20000, days_ago=45, invoice_number="A-3160")
        _create_invoice(owner.id, total_cents=30000, days_ago=75, invoice_number="A-6190")
        _create_invoice(owner.id, total_cents=40000, days_ago=120, invoice_number="A-90P")
        _create_invoice(
            owner.id,
            status="paid",
            total_cents=99900,
            days_ago=200,
            invoice_number="A-PAID",
        )

        resp = client.get("/finance/aging", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["currency"] == "BRL"
        assert data["total_open"] == 1000.0
        assert data["buckets"]["current"] == 100.0
        assert data["buckets"]["d31_60"] == 200.0
        assert data["buckets"]["d61_90"] == 300.0
        assert data["buckets"]["d90_plus"] == 400.0

    def test_aging_isolates_users(self, owner, stranger, auth_headers):
        db = TestingSessionLocal()
        try:
            db.query(Invoice).filter(Invoice.user_id == owner.id).delete()
            db.commit()
        finally:
            db.close()

        _create_invoice(owner.id, total_cents=5000, days_ago=5, invoice_number="OWN-1")
        _create_invoice(stranger.id, total_cents=80000, days_ago=5, invoice_number="STR-1")

        resp = client.get("/finance/aging", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_open"] == 50.0
        assert data["buckets"]["current"] == 50.0

    def test_aging_empty_open(self, owner, auth_headers):
        db = TestingSessionLocal()
        try:
            db.query(Invoice).filter(Invoice.user_id == owner.id).delete()
            db.commit()
        finally:
            db.close()

        resp = client.get("/finance/aging", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_open"] == 0.0
        assert data["buckets"] == {
            "current": 0.0,
            "d31_60": 0.0,
            "d61_90": 0.0,
            "d90_plus": 0.0,
        }
