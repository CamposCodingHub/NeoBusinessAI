"""Testes de memoria duravel do chat premium (ChatMessage + SQLite)."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from ai.premium_conversational_engine import (
    AdvancedMemorySystem,
    ConversationMemory,
    PremiumConversationalEngine,
)
from database import Base, ChatMessage, User
from services.chat_memory_service import (
    PREMIUM_CONTEXT_TYPE,
    clear_conversation_messages,
    load_conversation_messages,
    parse_memory_key,
    persist_turn,
    sanitize_conversation_id,
)


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        user = User(email="memory@example.com", name="Memory User", plan_tier="starter")
        session.add(user)
        session.commit()
        session.refresh(user)
        yield session, user
    finally:
        session.close()
        engine.dispose()


class TestChatMemoryService:
    def test_sanitize_and_parse_memory_key(self):
        assert sanitize_conversation_id("case!42") == "case42"
        assert parse_memory_key("7:abc-1") == (7, "abc-1")
        assert parse_memory_key("plain")[0] is None

    def test_persist_load_and_clear(self, db_session):
        db, user = db_session
        ok = persist_turn(
            db,
            user.id,
            "conv-a",
            "Ola Lex",
            "Ola, como posso ajudar?",
            confidence=0.91,
        )
        assert ok is True

        loaded = load_conversation_messages(db, user.id, "conv-a", limit=10)
        assert len(loaded) == 2
        assert loaded[0]["role"] == "user"
        assert loaded[0]["content"] == "Ola Lex"
        assert loaded[1]["role"] == "assistant"
        assert "ajudar" in loaded[1]["content"]

        rows = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.user_id == user.id,
                ChatMessage.conversation_id == "conv-a",
                ChatMessage.context_type == PREMIUM_CONTEXT_TYPE,
            )
            .all()
        )
        assert len(rows) == 2

        deleted = clear_conversation_messages(db, user.id, "conv-a")
        assert deleted == 2
        assert load_conversation_messages(db, user.id, "conv-a") == []

    def test_conversations_are_isolated(self, db_session):
        db, user = db_session
        persist_turn(db, user.id, "a", "msg a", "resp a")
        persist_turn(db, user.id, "b", "msg b", "resp b")

        a_msgs = load_conversation_messages(db, user.id, "a")
        b_msgs = load_conversation_messages(db, user.id, "b")
        assert [m["content"] for m in a_msgs] == ["msg a", "resp a"]
        assert [m["content"] for m in b_msgs] == ["msg b", "resp b"]

    def test_persist_failure_returns_false(self, db_session):
        db, user = db_session

        class BrokenSession:
            def add(self, *_args, **_kwargs):
                raise RuntimeError("db down")

            def commit(self):
                raise RuntimeError("db down")

            def rollback(self):
                return None

        ok = persist_turn(BrokenSession(), user.id, "x", "u", "a")
        assert ok is False


class TestMemoryHydration:
    def test_hydrate_when_in_memory_empty(self, db_session):
        db, user = db_session
        persist_turn(db, user.id, "hyd", "Pergunta salva", "Resposta salva")

        memory_system = AdvancedMemorySystem()
        key = f"{user.id}:hyd"
        memory = memory_system.get_or_create_memory(key, db=db)

        assert len(memory.messages) == 2
        assert memory.messages[0]["content"] == "Pergunta salva"
        assert memory.messages[1]["content"] == "Resposta salva"
        assert memory.interaction_count >= 2

    def test_does_not_rehydrate_non_empty_memory(self, db_session):
        db, user = db_session
        persist_turn(db, user.id, "keep", "db user", "db assistant")

        memory_system = AdvancedMemorySystem()
        key = f"{user.id}:keep"
        memory_system.conversations[key] = ConversationMemory(user_id=key)
        memory_system.conversations[key].add_message("user", "ja em processo")

        memory = memory_system.get_or_create_memory(key, db=db)
        assert len(memory.messages) == 1
        assert memory.messages[0]["content"] == "ja em processo"

    def test_db_failure_falls_back_to_empty_memory(self, db_session):
        db, user = db_session

        class BrokenSession:
            def query(self, *_args, **_kwargs):
                raise RuntimeError("db down")

            def rollback(self):
                return None

        memory_system = AdvancedMemorySystem()
        memory = memory_system.get_or_create_memory(
            f"{user.id}:fail",
            db=BrokenSession(),
        )
        assert list(memory.messages) == []

    def test_clear_memory_removes_in_process(self, db_session):
        db, user = db_session
        key = f"{user.id}:clr"
        memory_system = AdvancedMemorySystem()
        memory_system.get_or_create_memory(key, db=db, hydrate=False)
        memory_system.conversations[key].add_message("user", "temp")
        assert memory_system.clear_memory(key) is True
        assert key not in memory_system.conversations


@pytest.mark.asyncio
async def test_generate_premium_response_hydrates_before_reply(db_session, monkeypatch):
    db, user = db_session
    persist_turn(
        db,
        user.id,
        "eng",
        "Contexto previo do usuario",
        "Contexto previo do assistente",
    )

    engine = PremiumConversationalEngine()

    async def fake_base(*args, **kwargs):
        return "Resposta nova com contexto."

    monkeypatch.setattr(engine, "_generate_base_content", fake_base)
    monkeypatch.setattr(
        engine.self_critique,
        "critique_and_improve",
        lambda text, ctx: (text, 90.0),
    )

    key = f"{user.id}:eng"
    result = await engine.generate_premium_response(
        user_message="Nova pergunta",
        user_id=key,
        db=db,
    )

    memory = engine.memory_system.get_or_create_memory(key, hydrate=False)
    # 2 hidratadas + user + assistant da rodada atual
    assert len(memory.messages) >= 4
    assert memory.messages[0]["content"] == "Contexto previo do usuario"
    assert result["response"]
