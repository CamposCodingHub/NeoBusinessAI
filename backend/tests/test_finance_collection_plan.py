"""
Testes: GET /finance/collection-plan — régua ética EOAB (JWT + ownership).
"""

import os
from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_finance_collection.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, Invoice, User, get_db  # noqa: E402
from routes.finance_routes import router as finance_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402
from services.collection_plan_service import (  # noqa: E402
    EOAB_DISCLAIMER,
    build_steps_for_due,
)

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_finance_collection.db"
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
    total_cents: int = 15000,
    days_from_due: int = 0,
    invoice_number: str = None,
) -> Invoice:
    """days_from_due: positive = overdue, negative = not yet due."""
    db = TestingSessionLocal()
    try:
        now = datetime.utcnow()
        due = now - timedelta(days=days_from_due)
        inv = Invoice(
            user_id=user_id,
            invoice_number=invoice_number
            or f"FAT-COL-{user_id}-{days_from_due}-{total_cents}-{os.urandom(2).hex()}",
            description="Collection plan test",
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
    return _make_user("collection.owner@example.com", "Collection Owner")


@pytest.fixture
def stranger():
    return _make_user("collection.stranger@example.com", "Stranger")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


class TestCollectionPlan:
    def test_collection_plan_requires_jwt(self):
        resp = client.get("/finance/collection-plan")
        assert resp.status_code in (401, 403)

    def test_plan_steps_and_disclaimer(self, owner, auth_headers):
        # clean open invoices for this owner
        db = TestingSessionLocal()
        try:
            db.query(Invoice).filter(
                Invoice.user_id == owner.id,
                Invoice.status.in_(["pending", "overdue"]),
            ).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()

        inv = _create_invoice(owner.id, days_from_due=5, total_cents=20000)
        resp = client.get("/finance/collection-plan", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["count"] >= 1
        assert EOAB_DISCLAIMER[:20] in data["disclaimer"]
        plan = next(p for p in data["plans"] if p["invoice_id"] == inv.id)
        codes = [s["code"] for s in plan["steps"]]
        assert codes == ["D-3", "D0", "D+3", "D+7"]
        assert plan["recommended_step"] == "D+7"
        assert any(s.get("is_current") for s in plan["steps"])

    def test_plan_by_invoice_id_and_ownership(self, owner, stranger, auth_headers):
        inv = _create_invoice(owner.id, days_from_due=-3, total_cents=10000)
        ok = client.get(
            f"/finance/collection-plan?invoice_id={inv.id}",
            headers=auth_headers,
        )
        assert ok.status_code == 200
        assert ok.json()["count"] == 1
        assert ok.json()["plans"][0]["recommended_step"] == "D-3"

        stranger_headers = _headers_for(stranger)
        denied = client.get(
            f"/finance/collection-plan?invoice_id={inv.id}",
            headers=stranger_headers,
        )
        assert denied.status_code == 404

    def test_service_step_ordering(self):
        steps = build_steps_for_due(datetime.utcnow() - timedelta(days=1))
        assert len(steps) == 4
        assert steps[0]["code"] == "D-3"
        assert steps[-1]["code"] == "D+7"
