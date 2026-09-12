"""Persistencia duravel da memoria de chat premium (ChatMessage).

Falha de DB nunca quebra o fluxo: callers devem tratar retorno vazio/False
e continuar com memoria apenas em processo.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from database import ChatMessage

logger = logging.getLogger(__name__)

PREMIUM_CONTEXT_TYPE = "premium_chat"
DEFAULT_HISTORY_LIMIT = 20


def sanitize_conversation_id(raw: Any) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]", "", str(raw or "default"))[:64]
    return cleaned or "default"


def parse_memory_key(memory_key: str) -> Tuple[Optional[int], str]:
    """Extrai (user_id numerico, conversation_id) de chave '{user_id}:{conversation_id}'."""
    if not memory_key:
        return None, "default"

    if ":" in memory_key:
        left, right = memory_key.split(":", 1)
        try:
            return int(left), sanitize_conversation_id(right)
        except (TypeError, ValueError):
            return None, sanitize_conversation_id(memory_key)

    try:
        return int(memory_key), "default"
    except (TypeError, ValueError):
        return None, sanitize_conversation_id(memory_key)


def _row_to_memory_item(row: ChatMessage) -> Dict[str, Any]:
    role = (row.role or row.sender_type or "user").lower()
    if role in {"client", "human"}:
        role = "user"
    if role not in {"user", "assistant", "system"}:
        role = "user"
    content = row.content or row.message or ""
    return {
        "role": role,
        "content": content,
        "timestamp": row.created_at.isoformat() if row.created_at else None,
        "metadata": {
            "persisted_id": row.id,
            "confidence": row.confidence,
            "context_used": row.context_used or {},
        },
    }


def load_conversation_messages(
    db: Session,
    user_id: int,
    conversation_id: str,
    limit: int = DEFAULT_HISTORY_LIMIT,
) -> List[Dict[str, Any]]:
    """Carrega as ultimas N mensagens premium da conversa (ordem cronologica)."""
    try:
        conv_id = sanitize_conversation_id(conversation_id)
        safe_limit = max(1, min(int(limit or DEFAULT_HISTORY_LIMIT), 100))
        rows = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.user_id == int(user_id),
                ChatMessage.conversation_id == conv_id,
                ChatMessage.context_type == PREMIUM_CONTEXT_TYPE,
                ChatMessage.is_from_whatsapp.is_(False),
            )
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
            .limit(safe_limit)
            .all()
        )
        rows.reverse()
        return [_row_to_memory_item(row) for row in rows]
    except Exception as exc:
        logger.warning(
            "Falha ao hidratar memoria premium user=%s conv=%s: %s",
            user_id,
            conversation_id,
            exc,
        )
        try:
            db.rollback()
        except Exception:
            pass
        return []


def persist_turn(
    db: Session,
    user_id: int,
    conversation_id: str,
    user_content: str,
    assistant_content: str,
    *,
    confidence: Optional[float] = None,
    context_used: Optional[Dict[str, Any]] = None,
) -> bool:
    """Persiste par user/assistant apos sucesso do chat premium. Retorna False se DB falhar."""
    try:
        conv_id = sanitize_conversation_id(conversation_id)
        meta = dict(context_used or {})
        meta.setdefault("conversation_id", conv_id)

        user_row = ChatMessage(
            user_id=int(user_id),
            conversation_id=conv_id,
            role="user",
            sender_type="user",
            content=user_content,
            message=user_content,
            context_type=PREMIUM_CONTEXT_TYPE,
            context_used=meta,
            message_type="text",
            is_from_whatsapp=False,
        )
        assistant_row = ChatMessage(
            user_id=int(user_id),
            conversation_id=conv_id,
            role="assistant",
            sender_type="assistant",
            content=assistant_content,
            message=assistant_content,
            context_type=PREMIUM_CONTEXT_TYPE,
            context_used=meta,
            confidence=confidence,
            message_type="text",
            is_from_whatsapp=False,
        )
        db.add(user_row)
        db.add(assistant_row)
        db.commit()
        return True
    except Exception as exc:
        logger.warning(
            "Falha ao persistir turno premium user=%s conv=%s: %s",
            user_id,
            conversation_id,
            exc,
        )
        try:
            db.rollback()
        except Exception:
            pass
        return False


def clear_conversation_messages(
    db: Session,
    user_id: int,
    conversation_id: str,
) -> int:
    """Apaga mensagens premium da conversa. Retorna -1 se DB falhar."""
    try:
        conv_id = sanitize_conversation_id(conversation_id)
        deleted = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.user_id == int(user_id),
                ChatMessage.conversation_id == conv_id,
                ChatMessage.context_type == PREMIUM_CONTEXT_TYPE,
            )
            .delete(synchronize_session=False)
        )
        db.commit()
        return int(deleted or 0)
    except Exception as exc:
        logger.warning(
            "Falha ao limpar memoria premium user=%s conv=%s: %s",
            user_id,
            conversation_id,
            exc,
        )
        try:
            db.rollback()
        except Exception:
            pass
        return -1
