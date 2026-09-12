"""Tests: WhatsApp LGPD consent stub + soft gate on approvals approve."""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_whatsapp_consent.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, User, get_db  # noqa: E402
from routes.approvals_routes import router as approvals_router  # noqa: E402
from routes.compliance_routes import router as compliance_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402
from services.outbound_approval_service import queue_whatsapp_for_approval  # noqa: E402
from services.whatsapp_consent_service import (  # noqa: E402
    CONSENT_REQUIRED_CODE,
    hash_phone,
)

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_whatsapp_consent.db"
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
app.include_router(compliance_router)
app.include_router(approvals_router)
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
    return _make_user("wa.consent.owner@example.com", "WA Owner")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


class TestWhatsAppConsent:
    def test_create_list_and_revoke(self, owner, auth_headers):
        phone = "+55 11 98888-7777"
        created = client.post(
            "/compliance/whatsapp-consent",
            json={"phone": phone, "source": "manual"},
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        body = created.json()["consent"]
        assert body["channel"] == "whatsapp"
        assert body["source"] == "manual"
        assert body["active"] is True
        assert body["phone_hash"] == hash_phone(phone)

        listed = client.get(
            "/compliance/whatsapp-consent",
            headers=auth_headers,
        )
        assert listed.status_code == 200
        assert listed.json()["count"] >= 1

        revoked = client.post(
            "/compliance/whatsapp-consent/revoke",
            json={"consent_id": body["id"]},
            headers=auth_headers,
        )
        assert revoked.status_code == 200, revoked.text
        assert revoked.json()["count"] == 1
        assert revoked.json()["revoked"][0]["active"] is False

    def test_get_filter_by_client_id(self, owner, auth_headers):
        created = client.post(
            "/compliance/whatsapp-consent",
            json={"client_id": 42, "phone": "11999990000", "source": "intake"},
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text

        filtered = client.get(
            "/compliance/whatsapp-consent",
            params={"client_id": 42},
            headers=auth_headers,
        )
        assert filtered.status_code == 200
        items = filtered.json()["consents"]
        assert any(c["client_id"] == 42 for c in items)

        empty = client.get(
            "/compliance/whatsapp-consent",
            params={"client_id": 99999},
            headers=auth_headers,
        )
        assert empty.status_code == 200
        assert empty.json()["count"] == 0

    def test_approve_without_consent_returns_403(self, owner, auth_headers):
        db = TestingSessionLocal()
        try:
            row = queue_whatsapp_for_approval(
                db,
                owner.id,
                recipient="5511977776666",
                body="Ola, teste LGPD",
                source="manual",
            )
            db.commit()
            approval_id = row.id
        finally:
            db.close()

        resp = client.post(
            f"/approvals/outbound/{approval_id}/approve",
            headers=auth_headers,
        )
        assert resp.status_code == 403, resp.text
        detail = resp.json()["detail"]
        assert detail["code"] == CONSENT_REQUIRED_CODE

    def test_approve_with_consent_allowed(self, owner, auth_headers):
        phone = "5511966665555"
        granted = client.post(
            "/compliance/whatsapp-consent",
            json={"phone": phone, "source": "manual"},
            headers=auth_headers,
        )
        assert granted.status_code == 201, granted.text

        db = TestingSessionLocal()
        try:
            row = queue_whatsapp_for_approval(
                db,
                owner.id,
                recipient=phone,
                body="Mensagem com consentimento",
                source="manual",
            )
            db.commit()
            approval_id = row.id
        finally:
            db.close()

        resp = client.post(
            f"/approvals/outbound/{approval_id}/approve",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["approval"]["status"] in {"approved", "sent"}
