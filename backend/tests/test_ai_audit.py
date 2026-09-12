"""
Testes da trilha de auditoria Lex (AIAuditEvent + GET /ai/audit).
App minimo com TestClient — sem importar main.
"""

import os
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_ai_audit.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import AIAuditEvent, Base, User, get_db  # noqa: E402
from routes.ai_audit_routes import router as ai_audit_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402
from services.ai_audit_service import persist_lex_audit  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ai_audit.db"
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
app.include_router(ai_audit_router)
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


def _seed_event(user_id: int, **kwargs) -> AIAuditEvent:
    db = TestingSessionLocal()
    try:
        defaults = {
            "user_id": user_id,
            "conversation_id": "default",
            "message_preview": "Pergunta juridica",
            "response_preview": "Resposta Lex",
            "model": "llama-3.1-8b-instant",
            "provider": "groq",
            "legal_area": "trabalhista",
            "grounding_status": "partial",
            "requires_human_review": False,
        }
        defaults.update(kwargs)
        event = AIAuditEvent(**defaults)
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    finally:
        db.close()


@pytest.fixture
def owner():
    return _make_user("audit.owner@example.com", "Audit Owner")


@pytest.fixture
def other():
    return _make_user("audit.other@example.com", "Other Firm")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def other_auth_headers(other):
    return _headers_for(other)


class TestAIAuditRoutes:
    def test_list_requires_auth(self):
        response = client.get("/ai/audit")
        assert response.status_code in {401, 403}

    def test_persist_and_list_own_events(self, owner, auth_headers):
        db = TestingSessionLocal()
        try:
            event = persist_lex_audit(
                db,
                user_id=owner.id,
                conversation_id="conv-1",
                message="A" * 250,
                response="B" * 400,
                model="test-model",
                provider="local",
                legal_area="civil",
                grounding_status="verified",
                requires_human_review=True,
            )
            assert event is not None
            assert len(event.message_preview) == 200
            assert len(event.response_preview) == 300
            assert event.requires_human_review is True
        finally:
            db.close()

        listed = client.get("/ai/audit", headers=auth_headers)
        assert listed.status_code == 200, listed.text
        body = listed.json()
        assert body["count"] >= 1
        previews = [e["message_preview"] for e in body["events"]]
        assert any(p and len(p) == 200 for p in previews)
        assert any(e.get("requires_human_review") for e in body["events"])

    def test_idor_hides_other_user_events(
        self, owner, other, auth_headers, other_auth_headers
    ):
        _seed_event(
            owner.id,
            message_preview="Segredo do owner",
            conversation_id="owner-only",
        )
        _seed_event(
            other.id,
            message_preview="Segredo do other",
            conversation_id="other-only",
        )

        mine = client.get("/ai/audit", headers=auth_headers)
        assert mine.status_code == 200
        mine_msgs = [e["message_preview"] for e in mine.json()["events"]]
        assert "Segredo do owner" in mine_msgs
        assert "Segredo do other" not in mine_msgs

        theirs = client.get("/ai/audit", headers=other_auth_headers)
        assert theirs.status_code == 200
        their_msgs = [e["message_preview"] for e in theirs.json()["events"]]
        assert "Segredo do other" in their_msgs
        assert "Segredo do owner" not in their_msgs

    def test_limit_caps_at_fifty(self, owner, auth_headers):
        for i in range(3):
            _seed_event(owner.id, message_preview=f"evt-{i}")

        response = client.get("/ai/audit?limit=50", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["count"] <= 50

        too_high = client.get("/ai/audit?limit=100", headers=auth_headers)
        assert too_high.status_code == 422

    def test_persist_best_effort_never_raises(self):
        bad_db = MagicMock()
        bad_db.add.side_effect = RuntimeError("db down")
        result = persist_lex_audit(
            bad_db,
            user_id=1,
            conversation_id="x",
            message="oi",
            response="ola",
        )
        assert result is None
        bad_db.rollback.assert_called()
