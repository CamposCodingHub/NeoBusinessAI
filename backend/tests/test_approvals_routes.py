"""
Testes do gate de aprovação outbound WhatsApp.
App mínimo com TestClient (sem importar main) — JWT obrigatório.
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_approvals.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, OutboundMessageApproval, User, get_db  # noqa: E402
from routes.approvals_routes import router as approvals_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402
from services.outbound_approval_service import queue_whatsapp_for_approval  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_approvals.db"
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
    return _make_user("approvals.owner@example.com", "Approvals Owner")


@pytest.fixture
def other():
    return _make_user("approvals.other@example.com", "Other Firm")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def other_auth_headers(other):
    return _headers_for(other)


class TestApprovalsRoutes:
    def test_create_and_list_pending(self, auth_headers):
        created = client.post(
            "/approvals/outbound",
            json={
                "recipient": "11999998888",
                "body": "Olá, lembrete de prazo amanhã.",
                "source": "deadline",
            },
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        body = created.json()["approval"]
        assert body["status"] == "pending"
        assert body["channel"] == "whatsapp"
        assert body["source"] == "deadline"
        assert body["recipient"].startswith("55")

        listed = client.get(
            "/approvals/outbound?status=pending", headers=auth_headers
        )
        assert listed.status_code == 200
        data = listed.json()
        assert data["pagination"]["total"] >= 1
        assert any(a["id"] == body["id"] for a in data["approvals"])

    def test_approve_without_whatsapp_is_simulated(self, auth_headers):
        created = client.post(
            "/approvals/outbound",
            json={
                "recipient": "+5511988776655",
                "body": "Cobrança amigável — fatura #42",
                "source": "finance",
            },
            headers=auth_headers,
        )
        approval_id = created.json()["approval"]["id"]

        approved = client.post(
            f"/approvals/outbound/{approval_id}/approve",
            headers=auth_headers,
        )
        assert approved.status_code == 200, approved.text
        payload = approved.json()
        assert payload["approval"]["status"] == "approved"
        assert payload["approval"]["decided_at"] is not None
        assert payload["send"]["simulated"] is True
        assert payload["send"]["sent"] is False

    def test_reject_pending(self, auth_headers):
        created = client.post(
            "/approvals/outbound",
            json={
                "recipient": "11911112222",
                "body": "Rascunho Lex — não enviar",
                "source": "lex",
            },
            headers=auth_headers,
        )
        approval_id = created.json()["approval"]["id"]

        rejected = client.post(
            f"/approvals/outbound/{approval_id}/reject",
            headers=auth_headers,
        )
        assert rejected.status_code == 200, rejected.text
        assert rejected.json()["approval"]["status"] == "rejected"

        listed = client.get(
            "/approvals/outbound?status=pending", headers=auth_headers
        )
        assert all(a["id"] != approval_id for a in listed.json()["approvals"])

    def test_cannot_approve_twice(self, auth_headers):
        created = client.post(
            "/approvals/outbound",
            json={"recipient": "11900001111", "body": "Dupla aprovação", "source": "manual"},
            headers=auth_headers,
        )
        approval_id = created.json()["approval"]["id"]
        first = client.post(
            f"/approvals/outbound/{approval_id}/approve", headers=auth_headers
        )
        assert first.status_code == 200
        second = client.post(
            f"/approvals/outbound/{approval_id}/approve", headers=auth_headers
        )
        assert second.status_code == 409

    def test_idor_other_user_404(self, auth_headers, other_auth_headers):
        created = client.post(
            "/approvals/outbound",
            json={"recipient": "11933334444", "body": "Privado", "source": "manual"},
            headers=auth_headers,
        )
        approval_id = created.json()["approval"]["id"]

        listed = client.get(
            "/approvals/outbound?status=pending", headers=other_auth_headers
        )
        assert listed.status_code == 200
        assert all(a["id"] != approval_id for a in listed.json()["approvals"])

        bad = client.post(
            f"/approvals/outbound/{approval_id}/approve",
            headers=other_auth_headers,
        )
        assert bad.status_code == 404

    def test_auth_required(self):
        res = client.get("/approvals/outbound?status=pending")
        assert res.status_code in (401, 403)

    def test_queue_helper_creates_pending(self, owner):
        db = TestingSessionLocal()
        try:
            row = queue_whatsapp_for_approval(
                db,
                user_id=owner.id,
                recipient="11955556666",
                body="Helper enqueue",
                source="deadline",
                commit=True,
            )
            assert row.id is not None
            assert row.status == "pending"
            assert row.channel == "whatsapp"
            fetched = (
                db.query(OutboundMessageApproval)
                .filter(OutboundMessageApproval.id == row.id)
                .first()
            )
            assert fetched is not None
            assert fetched.body == "Helper enqueue"
        finally:
            db.close()

    def test_invalid_source_rejected(self, auth_headers):
        bad = client.post(
            "/approvals/outbound",
            json={
                "recipient": "11922223333",
                "body": "Fonte inválida",
                "source": "telegram_bot",
            },
            headers=auth_headers,
        )
        assert bad.status_code == 400
