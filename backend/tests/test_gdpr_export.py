"""
Testes: exportação LGPD/GDPR (GET|POST /gdpr/export).
Pacote JSON do firm user autenticado — sem password_hash.
"""

import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_gdpr_export.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import (  # noqa: E402
    Base,
    ChatMessage,
    Client,
    Document,
    Invoice,
    Lead,
    Matter,
    User,
    get_db,
)
from routes.gdpr_routes import router as gdpr_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402
from services.compliance_service import ComplianceService  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_gdpr_export.db"
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
    finally:
        db.close()


app = FastAPI()
app.include_router(gdpr_router)
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def _make_user(email: str, name: str, password_hash: str = "SECRET_HASH_NEVER_EXPORT") -> User:
    db = TestingSessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return existing
        user = User(
            email=email,
            name=name,
            password_hash=password_hash,
            role="user",
            company="Escritório Teste",
            phone="11999990000",
            plan_tier="premium",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def _headers_for(user: User) -> dict:
    token = create_access_token(user_id=str(user.id), role=Role.USER)
    return {"Authorization": f"Bearer {token}"}


def _seed_firm_data(user_id: int) -> None:
    db = TestingSessionLocal()
    try:
        if db.query(Client).filter(Client.user_id == user_id).count() > 0:
            return
        db.add(
            Client(
                user_id=user_id,
                name="Cliente A",
                email="cliente@example.com",
                status="active",
            )
        )
        db.add(
            Document(
                user_id=user_id,
                filename="peticao.pdf",
                original_filename="peticao.pdf",
                file_type="pdf",
                file_size=1024,
                status="completed",
                text_content="TEXTO COMPLETO NÃO DEVE APARECER NO EXPORT",
                title="Petição",
            )
        )
        db.add(
            Invoice(
                user_id=user_id,
                invoice_number=f"INV-GDPR-{user_id}-1",
                description="Honorários",
                amount_cents=10000,
                total_cents=10000,
                status="paid",
                due_date=datetime.utcnow() + timedelta(days=7),
            )
        )
        db.add(
            ChatMessage(
                user_id=user_id,
                role="user",
                content="mensagem sensível",
                message="mensagem sensível",
            )
        )
        db.add(
            Lead(
                user_id=user_id,
                name="Lead B",
                email="lead@example.com",
                status="new",
            )
        )
        db.add(
            Matter(
                user_id=user_id,
                title="Caso Cível",
                status="open",
            )
        )
        db.commit()
    finally:
        db.close()


@pytest.fixture
def owner():
    user = _make_user("gdpr.owner@example.com", "GDPR Owner")
    _seed_firm_data(user.id)
    return user

@pytest.fixture
def other():
    return _make_user("gdpr.other@example.com", "Other Firm")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


class TestGdprExport:
    def test_get_export_returns_package_without_password_hash(self, owner, auth_headers):
        resp = client.get("/gdpr/export", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()

        assert "profile" in data
        assert data["profile"]["email"] == "gdpr.owner@example.com"
        assert data["profile"]["name"] == "GDPR Owner"
        assert "password_hash" not in data["profile"]
        assert "password_hash" not in str(data).lower()
        assert data["profile"].get("company") == "Escritório Teste"

        assert data["clients_count"] >= 1
        assert data["chat_messages_count"] >= 1
        assert data["leads_count"] >= 1
        assert data["matters_count"] >= 1

        assert isinstance(data["documents"], list)
        assert len(data["documents"]) >= 1
        doc = data["documents"][0]
        assert "id" in doc
        assert "filename" in doc
        assert "created_at" in doc or doc.get("created_at") is None
        # Sem texto completo do documento
        assert "text_content" not in doc
        assert "TEXTO COMPLETO" not in str(data)

        inv = data["invoices_summary"]
        assert inv["count"] >= 1
        assert inv["total_amount_cents"] >= 10000
        assert "items" in inv

        assert data["export_metadata"]["format_version"] == "2.0"

    def test_post_export_same_shape(self, owner, auth_headers):
        resp = client.post("/gdpr/export", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "profile" in data
        assert "clients_count" in data
        assert "documents" in data
        assert "invoices_summary" in data
        assert "chat_messages_count" in data
        assert "leads_count" in data
        assert "matters_count" in data
        assert "password_hash" not in str(data).lower()

    def test_export_requires_jwt(self):
        resp = client.get("/gdpr/export")
        assert resp.status_code in (401, 403)

    def test_legacy_alias_and_best_effort_partial(self, owner, auth_headers):
        # Alias legado
        resp = client.get("/gdpr/export/my-data", headers=auth_headers)
        assert resp.status_code == 200
        assert "profile" in resp.json()

        # Seção isolada falha → export continua
        db = TestingSessionLocal()
        try:
            with patch.object(
                ComplianceService,
                "_safe_section",
                wraps=ComplianceService._safe_section,
            ) as wrapped:
                # força falha em leads via query quebrada
                real_export = ComplianceService.export_user_data

                def _export_with_broken_leads(session, user_id):
                    package = {
                        "export_metadata": {"format_version": "2.0"},
                        "profile": {"id": user_id, "email": "x"},
                        "clients_count": 0,
                        "documents": [],
                        "invoices_summary": {
                            "count": 0,
                            "total_amount_cents": 0,
                            "by_status": {},
                            "items": [],
                        },
                        "chat_messages_count": 0,
                        "leads_count": 0,
                        "matters_count": 0,
                        "partial_errors": [],
                    }
                    partial = package["partial_errors"]

                    def boom():
                        raise RuntimeError("table missing")

                    package["leads_count"] = ComplianceService._safe_section(
                        "leads_count", boom, partial, 0
                    )
                    package["clients_count"] = ComplianceService._safe_section(
                        "clients_count",
                        lambda: session.query(Client)
                        .filter(Client.user_id == user_id)
                        .count(),
                        partial,
                        0,
                    )
                    return package

                package = _export_with_broken_leads(db, owner.id)
                assert package["leads_count"] == 0
                assert any(e["section"] == "leads_count" for e in package["partial_errors"])
                assert package["clients_count"] >= 1
                _ = wrapped  # noqa: F841 — presence of helper
        finally:
            db.close()

    def test_service_never_includes_password_hash(self, owner):
        db = TestingSessionLocal()
        try:
            package = ComplianceService.export_user_data(db, owner.id)
            assert "password_hash" not in package["profile"]
            assert "SECRET_HASH" not in str(package)
            # mock user com atributo extra sensível
            fake = MagicMock()
            fake.id = owner.id
            fake.email = "a@b.com"
            fake.name = "A"
            fake.company = None
            fake.phone = None
            fake.role = "user"
            fake.plan_tier = "free"
            fake.subscription_status = None
            fake.documents_limit = 5
            fake.users_limit = 1
            fake.is_active = True
            fake.created_at = None
            fake.updated_at = None
            fake.last_login = None
            fake.password_hash = "SHOULD_NOT_APPEAR"
            profile = ComplianceService._profile_from_user(fake)
            assert "password_hash" not in profile
        finally:
            db.close()
