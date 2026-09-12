"""Unit tests for pragmatic usage metering (no main import)."""

from __future__ import annotations

import os
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Config/Settings exige ENVIRONMENT=test para SQLite; enforcement e
# controlado via monkeypatch nos testes de bloqueio.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_usage_metering.db")
os.environ["ENVIRONMENT"] = "test"
os.environ.setdefault("DEBUG", "false")

from database import Base, ChatMessage, Document, User  # noqa: E402
from services import usage_metering as metering  # noqa: E402


@pytest.fixture()
def db_session(monkeypatch):
    # Bloqueio estrito nos testes de gate (service le getenv a cada chamada)
    monkeypatch.setenv("ENVIRONMENT", "development")
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        user = User(
            email="usage@example.com",
            name="Usage User",
            plan_tier="starter",
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        yield session, user
    finally:
        session.close()
        engine.dispose()


class TestPlanLimits:
    def test_get_plan_limits_known_tiers(self):
        starter = metering.get_plan_limits("starter")
        assert starter["max_documents"] == 10
        assert starter["max_ai_messages_per_day"] == 100
        assert starter["max_users"] == 1

        pro = metering.get_plan_limits("professional")
        assert pro["max_documents"] == 100
        assert pro["max_users"] == 5

        biz = metering.get_plan_limits("business")
        assert biz["max_documents"] == 1000
        assert biz["max_ai_messages_per_day"] == 10000

    def test_unknown_plan_falls_back_to_starter(self):
        assert metering.get_plan_limits(None) == metering.get_plan_limits("starter")
        assert metering.get_plan_limits("free") == metering.get_plan_limits("starter")
        assert metering.get_plan_limits("mystery") == metering.get_plan_limits("starter")
        assert metering.normalize_plan_tier("PRO") == "professional"


class TestCounters:
    def test_count_user_documents(self, db_session):
        db, user = db_session
        assert metering.count_user_documents(db, user.id) == 0
        db.add(
            Document(
                user_id=user.id,
                filename="a.pdf",
                original_filename="a.pdf",
            )
        )
        db.add(
            Document(
                user_id=user.id,
                filename="b.pdf",
                original_filename="b.pdf",
            )
        )
        db.commit()
        assert metering.count_user_documents(db, user.id) == 2

    def test_count_user_ai_messages_today(self, db_session):
        db, user = db_session
        now = datetime.utcnow()
        db.add(
            ChatMessage(
                user_id=user.id,
                role="user",
                content="hoje",
                created_at=now,
            )
        )
        db.add(
            ChatMessage(
                user_id=user.id,
                role="assistant",
                content="resposta",
                created_at=now,
            )
        )
        db.add(
            ChatMessage(
                user_id=user.id,
                role="user",
                content="ontem",
                created_at=now - timedelta(days=2),
            )
        )
        db.commit()
        assert metering.count_user_ai_messages_today(db, user.id) == 1


class TestGates:
    def test_check_can_upload_blocks_at_limit(self, db_session, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "development")
        db, user = db_session
        limits = metering.get_plan_limits("starter")
        for i in range(limits["max_documents"]):
            db.add(
                Document(
                    user_id=user.id,
                    filename=f"d{i}.pdf",
                    original_filename=f"d{i}.pdf",
                )
            )
        db.commit()

        result = metering.check_can_upload(db, user.id, plan_tier="starter")
        assert result["allowed"] is False
        assert result["reason"] == "document_limit_reached"
        assert result["usage"]["documents"] == limits["max_documents"]
        assert "limits" in result

    def test_check_can_chat_blocks_at_daily_limit(self, db_session, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "development")
        db, user = db_session
        limits = metering.get_plan_limits("starter")
        now = datetime.utcnow()
        for i in range(limits["max_ai_messages_per_day"]):
            db.add(
                ChatMessage(
                    user_id=user.id,
                    role="user",
                    content=f"msg-{i}",
                    created_at=now,
                )
            )
        db.commit()

        result = metering.check_can_chat(db, user.id, plan_tier="starter")
        assert result["allowed"] is False
        assert result["reason"] == "ai_daily_limit_reached"
        assert result["usage"]["ai_messages_today"] == limits["max_ai_messages_per_day"]

    def test_test_environment_skips_strict_block(self, db_session, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "test")
        db, user = db_session
        limits = metering.get_plan_limits("starter")
        for i in range(limits["max_documents"] + 3):
            db.add(
                Document(
                    user_id=user.id,
                    filename=f"x{i}.pdf",
                    original_filename=f"x{i}.pdf",
                )
            )
        db.commit()

        result = metering.check_can_upload(db, user.id, plan_tier="starter")
        assert result["allowed"] is True
        assert result["reason"] == "test_environment_skip"
        assert result["usage"]["documents"] > limits["max_documents"]

    def test_usage_limit_http_payload_shape(self, db_session, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "development")
        db, user = db_session
        for i in range(10):
            db.add(
                Document(
                    user_id=user.id,
                    filename=f"p{i}.pdf",
                    original_filename=f"p{i}.pdf",
                )
            )
        db.commit()
        gate = metering.check_can_upload(db, user.id, plan_tier="starter")
        payload = metering.usage_limit_http_payload(gate)
        assert payload["success"] is False
        assert payload["error"] == "usage_limit_exceeded"
        assert payload["upgrade_required"] is True
        assert "usage" in payload and "limits" in payload
