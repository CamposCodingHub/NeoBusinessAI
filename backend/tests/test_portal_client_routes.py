"""
Testes do Portal do Cliente (MVP transacional read-only).
App mínimo com TestClient — evita import pesado de main.
"""

import os
from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_portal.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import (  # noqa: E402
    Base,
    Client,
    Document,
    Invoice,
    Matter,
    User,
    get_db,
)
from models.portal_client import PortalClient  # noqa: E402
from routes.portal_client_routes import router as portal_router  # noqa: E402
from security import create_access_token, get_password_hash  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_portal.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(portal_router)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def _seed():
    db = TestingSessionLocal()
    try:
        db.query(Invoice).delete()
        db.query(Document).delete()
        db.query(Matter).delete()
        db.query(PortalClient).delete()
        db.query(Client).delete()
        db.query(User).delete()
        db.commit()

        firm = User(
            email="firm.portal@example.com",
            name="Firm Owner",
            password_hash="x",
            role="user",
        )
        db.add(firm)
        db.flush()

        owned = Client(
            user_id=firm.id,
            name="Cliente Portal",
            email="cliente.portal@example.com",
            status="active",
        )
        other = Client(
            user_id=firm.id,
            name="Outro Cliente",
            email="outro@example.com",
            status="active",
        )
        db.add_all([owned, other])
        db.flush()

        portal = PortalClient(
            client_id=owned.id,
            email="cliente.portal@example.com",
            password_hash=get_password_hash("senha-segura"),
            is_active=True,
        )
        db.add(portal)
        db.flush()

        matter = Matter(
            user_id=firm.id,
            client_id=owned.id,
            title="Caso do Cliente",
            status="open",
        )
        db.add(matter)
        db.flush()

        doc_ok = Document(
            user_id=firm.id,
            filename="contrato.pdf",
            title="Contrato Compartilhado",
            file_type="pdf",
            status="completed",
            matter_id=matter.id,
            custom_data={"client_id": owned.id},
        )
        doc_other = Document(
            user_id=firm.id,
            filename="segredo.pdf",
            title="Doc de Outro",
            file_type="pdf",
            status="completed",
            custom_data={"client_id": other.id},
        )
        db.add_all([doc_ok, doc_other])

        inv_ok = Invoice(
            user_id=firm.id,
            client_id=owned.id,
            invoice_number="INV-PORTAL-1",
            description="Honorários",
            amount_cents=150000,
            total_cents=150000,
            status="pending",
            due_date=datetime.utcnow() + timedelta(days=15),
        )
        inv_other = Invoice(
            user_id=firm.id,
            client_id=other.id,
            invoice_number="INV-OTHER-1",
            description="Não deve aparecer",
            amount_cents=9900,
            total_cents=9900,
            status="pending",
            due_date=datetime.utcnow() + timedelta(days=10),
        )
        db.add_all([inv_ok, inv_other])
        db.commit()

        return {
            "portal_id": portal.id,
            "client_id": owned.id,
            "other_client_id": other.id,
            "doc_ok_id": doc_ok.id,
            "doc_other_id": doc_other.id,
            "inv_ok_id": inv_ok.id,
            "inv_other_id": inv_other.id,
        }
    finally:
        db.close()


@pytest.fixture
def seed():
    return _seed()


def _portal_headers(portal_id: int) -> dict:
    token = create_access_token(
        user_id=str(portal_id),
        role=Role.USER,
        permissions=["portal"],
    )
    return {"Authorization": f"Bearer {token}"}


class TestPortalClientRoutes:
    def test_login_success(self, seed):
        res = client.post(
            "/portal/login",
            json={"email": "cliente.portal@example.com", "password": "senha-segura"},
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["access_token"]
        assert body["client_name"] == "Cliente Portal"
        assert body["client_id"] == seed["client_id"]

    def test_login_invalid(self, seed):
        res = client.post(
            "/portal/login",
            json={"email": "cliente.portal@example.com", "password": "errada"},
        )
        assert res.status_code == 401

    def test_requires_auth(self):
        assert client.get("/portal/documents").status_code == 401
        assert client.get("/portal/invoices").status_code == 401

    def test_staff_token_without_portal_claim_rejected(self, seed):
        token = create_access_token(
            user_id=str(seed["portal_id"]),
            role=Role.USER,
            permissions=[],
        )
        res = client.get(
            "/portal/documents",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 401

    def test_list_own_documents_only(self, seed):
        headers = _portal_headers(seed["portal_id"])
        res = client.get("/portal/documents", headers=headers)
        assert res.status_code == 200, res.text
        docs = res.json()["documents"]
        ids = {d["id"] for d in docs}
        assert seed["doc_ok_id"] in ids
        assert seed["doc_other_id"] not in ids

    def test_list_own_invoices_only(self, seed):
        headers = _portal_headers(seed["portal_id"])
        res = client.get("/portal/invoices", headers=headers)
        assert res.status_code == 200, res.text
        invs = res.json()["invoices"]
        ids = {i["id"] for i in invs}
        assert seed["inv_ok_id"] in ids
        assert seed["inv_other_id"] not in ids
        assert invs[0]["total_amount"] == 1500.0

    def test_invoice_idor(self, seed):
        headers = _portal_headers(seed["portal_id"])
        denied = client.get(
            f"/portal/invoices/{seed['inv_other_id']}",
            headers=headers,
        )
        assert denied.status_code == 404

        ok = client.get(
            f"/portal/invoices/{seed['inv_ok_id']}",
            headers=headers,
        )
        assert ok.status_code == 200
        assert ok.json()["invoice"]["id"] == seed["inv_ok_id"]

    def test_document_idor(self, seed):
        headers = _portal_headers(seed["portal_id"])
        denied = client.get(
            f"/portal/documents/{seed['doc_other_id']}",
            headers=headers,
        )
        assert denied.status_code == 404

    def test_timeline_and_me(self, seed):
        headers = _portal_headers(seed["portal_id"])
        me = client.get("/portal/me", headers=headers)
        assert me.status_code == 200
        assert me.json()["client_name"] == "Cliente Portal"

        tl = client.get("/portal/timeline", headers=headers)
        assert tl.status_code == 200
        assert "events" in tl.json()
