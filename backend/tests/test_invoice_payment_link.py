"""
Testes: POST /finance/invoices/{id}/payment-link (stub path).
Ownership JWT + persistência de payment_url.
"""

import os
from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_invoice_payment_link.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")
# Garante caminho stub (sem Stripe real nos testes)
os.environ.pop("STRIPE_SECRET_KEY", None)

from database import Base, Client, Invoice, User, get_db  # noqa: E402
from routes.finance_routes import router as finance_router  # noqa: E402
from routes.portal_client_routes import router as portal_router  # noqa: E402
from models.portal_client import PortalClient  # noqa: E402
from security import create_access_token, get_password_hash  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_invoice_payment_link.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(finance_router)
app.include_router(portal_router)


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
    client_id: int = None,
    status: str = "pending",
    total_cents: int = 15000,
) -> Invoice:
    db = TestingSessionLocal()
    try:
        inv = Invoice(
            user_id=user_id,
            client_id=client_id,
            invoice_number=f"FAT-TEST-{user_id}-{datetime.utcnow().timestamp()}",
            description="Honorários teste",
            amount_cents=total_cents,
            discount_cents=0,
            total_cents=total_cents,
            due_date=datetime.utcnow() + timedelta(days=7),
            status=status,
            invoice_type="service",
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)
        return inv
    finally:
        db.close()


@pytest.fixture
def owner():
    return _make_user("paylink.owner@example.com", "Pay Owner")


@pytest.fixture
def other():
    return _make_user("paylink.other@example.com", "Other Firm")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def other_auth_headers(other):
    return _headers_for(other)


class TestInvoicePaymentLink:
    def test_stub_payment_link_persists(self, owner, auth_headers):
        inv = _create_invoice(owner.id)
        resp = client.post(
            f"/finance/invoices/{inv.id}/payment-link",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["provider"] == "stub"
        assert body["invoice_id"] == inv.id
        assert body["payment_url"].startswith(
            f"https://pay.lexscan.local/i/{inv.id}?token="
        )
        assert "token=" in body["payment_url"]

        db = TestingSessionLocal()
        try:
            stored = db.query(Invoice).filter(Invoice.id == inv.id).first()
            assert stored.payment_url == body["payment_url"]
            assert stored.payment_reference  # token assinado persistido
        finally:
            db.close()

    def test_idor_other_user_gets_404(self, owner, other_auth_headers):
        inv = _create_invoice(owner.id)
        resp = client.post(
            f"/finance/invoices/{inv.id}/payment-link",
            headers=other_auth_headers,
        )
        assert resp.status_code == 404

        db = TestingSessionLocal()
        try:
            stored = db.query(Invoice).filter(Invoice.id == inv.id).first()
            assert stored.payment_url is None
        finally:
            db.close()

    def test_auth_required(self, owner):
        inv = _create_invoice(owner.id)
        resp = client.post(f"/finance/invoices/{inv.id}/payment-link")
        assert resp.status_code in (401, 403)

    def test_cancelled_invoice_rejected(self, owner, auth_headers):
        inv = _create_invoice(owner.id, status="cancelled")
        resp = client.post(
            f"/finance/invoices/{inv.id}/payment-link",
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_portal_list_includes_payment_url(self, owner):
        db = TestingSessionLocal()
        try:
            firm_client = Client(
                user_id=owner.id,
                name="Cliente Portal Pay",
                email="cliente.pay@example.com",
            )
            db.add(firm_client)
            db.flush()

            inv = Invoice(
                user_id=owner.id,
                client_id=firm_client.id,
                invoice_number="FAT-PORTAL-PAY-1",
                description="Portal pay",
                amount_cents=20000,
                discount_cents=0,
                total_cents=20000,
                due_date=datetime.utcnow() + timedelta(days=5),
                status="pending",
                payment_url="https://pay.lexscan.local/i/99?token=abc",
            )
            db.add(inv)

            portal = PortalClient(
                client_id=firm_client.id,
                email="cliente.pay@example.com",
                password_hash=get_password_hash("secret123"),
                is_active=True,
            )
            db.add(portal)
            db.commit()
            db.refresh(portal)
            portal_id = portal.id
        finally:
            db.close()

        token = create_access_token(
            user_id=str(portal_id),
            role=Role.USER,
            permissions=["portal"],
        )
        resp = client.get(
            "/portal/invoices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, resp.text
        invoices = resp.json()["invoices"]
        assert len(invoices) >= 1
        match = next(i for i in invoices if i["invoice_number"] == "FAT-PORTAL-PAY-1")
        assert match["payment_url"] == "https://pay.lexscan.local/i/99?token=abc"
