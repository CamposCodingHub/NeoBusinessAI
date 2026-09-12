"""
Testes: GET /finance/profitability — estimativa operacional por cliente (JWT).
"""

import os
from datetime import date, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_finance_profitability.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import (  # noqa: E402
    Base,
    Client,
    CostAdvance,
    Invoice,
    TimeEntry,
    User,
    get_db,
)
from routes.finance_routes import router as finance_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_finance_profitability.db"
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


def _create_invoice(
    user_id: int,
    client_id: int | None,
    *,
    status: str = "pending",
    total_cents: int = 10000,
    invoice_number: str,
) -> Invoice:
    db = TestingSessionLocal()
    try:
        inv = Invoice(
            user_id=user_id,
            client_id=client_id,
            invoice_number=invoice_number,
            description="Profit test",
            amount_cents=total_cents,
            discount_cents=0,
            total_cents=total_cents,
            status=status,
            due_date=datetime.utcnow(),
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)
        return inv
    finally:
        db.close()


def _create_time(
    user_id: int,
    client_id: int | None,
    *,
    minutes: int,
    hourly_rate: float,
    billable: bool = True,
) -> TimeEntry:
    db = TestingSessionLocal()
    try:
        entry = TimeEntry(
            user_id=user_id,
            client_id=client_id,
            description="Work",
            minutes=minutes,
            hourly_rate=hourly_rate,
            billable=billable,
            work_date=date.today(),
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
    finally:
        db.close()


def _create_cost(
    user_id: int,
    client_id: int | None,
    *,
    amount: float,
    status: str = "advanced",
) -> CostAdvance:
    db = TestingSessionLocal()
    try:
        row = CostAdvance(
            user_id=user_id,
            client_id=client_id,
            description="Custas",
            amount=amount,
            status=status,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row
    finally:
        db.close()


@pytest.fixture
def owner():
    return _make_user("profit.owner@example.com", "Profit Owner")


@pytest.fixture
def stranger():
    return _make_user("profit.stranger@example.com", "Stranger")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


class TestFinanceProfitability:
    def test_profitability_requires_jwt(self):
        resp = client.get("/finance/profitability")
        assert resp.status_code in (401, 403)

    def test_profitability_aggregates_per_client(self, owner, auth_headers):
        db = TestingSessionLocal()
        try:
            db.query(Invoice).filter(Invoice.user_id == owner.id).delete()
            db.query(TimeEntry).filter(TimeEntry.user_id == owner.id).delete()
            db.query(CostAdvance).filter(CostAdvance.user_id == owner.id).delete()
            db.commit()
        finally:
            db.close()

        c1 = _make_client(owner.id, "Alpha Adv")
        c2 = _make_client(owner.id, "Beta Ltda")

        _create_invoice(
            owner.id, c1.id, status="paid", total_cents=100000, invoice_number="P-ALPHA-1"
        )
        _create_invoice(
            owner.id, c1.id, status="pending", total_cents=50000, invoice_number="P-ALPHA-2"
        )
        _create_invoice(
            owner.id, c2.id, status="pending", total_cents=20000, invoice_number="P-BETA-1"
        )
        # cancelled ignored
        _create_invoice(
            owner.id, c1.id, status="cancelled", total_cents=99900, invoice_number="P-SKIP"
        )

        _create_time(owner.id, c1.id, minutes=60, hourly_rate=300.0)  # 300
        _create_time(owner.id, c2.id, minutes=120, hourly_rate=200.0)  # 400
        _create_time(owner.id, c1.id, minutes=60, hourly_rate=100.0, billable=False)

        _create_cost(owner.id, c1.id, amount=150.0, status="advanced")
        _create_cost(owner.id, c1.id, amount=50.0, status="reimbursed")  # ignored
        _create_cost(owner.id, c2.id, amount=25.0, status="advanced")

        resp = client.get("/finance/profitability?limit=10", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "note" in data
        assert "estimativa" in data["note"].lower()
        assert "clients" in data

        by_name = {c["client_name"]: c for c in data["clients"]}
        assert "Alpha Adv" in by_name
        assert "Beta Ltda" in by_name

        alpha = by_name["Alpha Adv"]
        assert alpha["invoiced"] == 1500.0
        assert alpha["time_value"] == 300.0
        assert alpha["costs_open"] == 150.0
        assert alpha["rough_margin"] == 1350.0  # invoiced - costs

        beta = by_name["Beta Ltda"]
        assert beta["invoiced"] == 200.0
        assert beta["time_value"] == 400.0
        assert beta["costs_open"] == 25.0
        assert beta["rough_margin"] == 175.0

    def test_profitability_isolates_users(self, owner, stranger, auth_headers):
        db = TestingSessionLocal()
        try:
            db.query(Invoice).filter(Invoice.user_id == owner.id).delete()
            db.query(TimeEntry).filter(TimeEntry.user_id == owner.id).delete()
            db.query(CostAdvance).filter(CostAdvance.user_id == owner.id).delete()
            db.commit()
        finally:
            db.close()

        own = _make_client(owner.id, "Own Client")
        other = _make_client(stranger.id, "Other Client")
        _create_invoice(
            owner.id, own.id, status="paid", total_cents=10000, invoice_number="OWN-P1"
        )
        _create_invoice(
            stranger.id, other.id, status="paid", total_cents=500000, invoice_number="STR-P1"
        )
        _create_cost(stranger.id, other.id, amount=999.0)

        resp = client.get("/finance/profitability", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        names = {c["client_name"] for c in data["clients"]}
        assert "Own Client" in names
        assert "Other Client" not in names
        own_row = next(c for c in data["clients"] if c["client_name"] == "Own Client")
        assert own_row["invoiced"] == 100.0

    def test_profitability_empty_activity(self, owner, auth_headers):
        db = TestingSessionLocal()
        try:
            db.query(Invoice).filter(Invoice.user_id == owner.id).delete()
            db.query(TimeEntry).filter(TimeEntry.user_id == owner.id).delete()
            db.query(CostAdvance).filter(CostAdvance.user_id == owner.id).delete()
            db.commit()
        finally:
            db.close()

        resp = client.get("/finance/profitability", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["clients"] == []
        assert "estimativa operacional" in data["note"]
