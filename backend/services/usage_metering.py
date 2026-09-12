"""Pragmatic SaaS usage metering and plan limit checks.

Counts documents and today's AI (user) chat messages; maps plan tiers to
simple limits. Unknown tiers fall back to starter. ENVIRONMENT=test skips
strict blocking so local/CI flows do not break.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import ChatMessage, Document, User

# Starter-aligned defaults for free / unknown / null plan_tier
PLAN_LIMITS: Dict[str, Dict[str, int]] = {
    "starter": {
        "max_documents": 10,
        "max_ai_messages_per_day": 100,
        "max_users": 1,
    },
    "professional": {
        "max_documents": 100,
        "max_ai_messages_per_day": 1000,
        "max_users": 5,
    },
    "business": {
        "max_documents": 1000,
        "max_ai_messages_per_day": 10000,
        "max_users": 25,
    },
}

_ALIASES = {
    "free": "starter",
    "basic": "starter",
    "pro": "professional",
    "enterprise": "business",
}


def _environment() -> str:
    return (os.getenv("ENVIRONMENT") or "development").strip().lower()


def enforcement_relaxed() -> bool:
    """True in test env — do not hard-block uploads/chat."""
    return _environment() == "test"


def normalize_plan_tier(plan_tier: Optional[str]) -> str:
    raw = (plan_tier or "").strip().lower()
    if not raw:
        return "starter"
    mapped = _ALIASES.get(raw, raw)
    if mapped in PLAN_LIMITS:
        return mapped
    return "starter"


def get_plan_limits(plan_tier: Optional[str]) -> Dict[str, int]:
    """Return max_documents, max_ai_messages_per_day, max_users for a tier."""
    tier = normalize_plan_tier(plan_tier)
    return dict(PLAN_LIMITS[tier])


def resolve_user_plan_tier(user: Optional[User]) -> str:
    if user is None:
        return "starter"
    return normalize_plan_tier(getattr(user, "plan_tier", None))


def count_user_documents(db: Session, user_id: int) -> int:
    return (
        db.query(Document)
        .filter(Document.user_id == int(user_id))
        .count()
    )


def count_user_ai_messages_today(db: Session, user_id: int) -> int:
    """Count user-role ChatMessage rows created since UTC midnight today."""
    start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    # Compare naively if DB stores naive UTC
    start_naive = start.replace(tzinfo=None)
    end_naive = start_naive + timedelta(days=1)
    return (
        db.query(ChatMessage)
        .filter(
            ChatMessage.user_id == int(user_id),
            ChatMessage.created_at >= start_naive,
            ChatMessage.created_at < end_naive,
            or_(
                ChatMessage.role == "user",
                (
                    (ChatMessage.role.is_(None))
                    & (ChatMessage.sender_type == "user")
                ),
            ),
        )
        .count()
    )


def get_usage_snapshot(db: Session, user_id: int) -> Dict[str, int]:
    return {
        "documents": count_user_documents(db, user_id),
        "ai_messages_today": count_user_ai_messages_today(db, user_id),
    }


def check_can_upload(
    db: Session,
    user_id: int,
    plan_tier: Optional[str] = None,
) -> Dict[str, Any]:
    if plan_tier is None:
        user = db.query(User).filter(User.id == int(user_id)).first()
        plan_tier = resolve_user_plan_tier(user)
    limits = get_plan_limits(plan_tier)
    usage = get_usage_snapshot(db, user_id)
    if enforcement_relaxed():
        return {
            "allowed": True,
            "reason": "test_environment_skip",
            "usage": usage,
            "limits": limits,
        }
    if usage["documents"] >= limits["max_documents"]:
        return {
            "allowed": False,
            "reason": "document_limit_reached",
            "usage": usage,
            "limits": limits,
        }
    return {
        "allowed": True,
        "reason": None,
        "usage": usage,
        "limits": limits,
    }


def check_can_chat(
    db: Session,
    user_id: int,
    plan_tier: Optional[str] = None,
) -> Dict[str, Any]:
    if plan_tier is None:
        user = db.query(User).filter(User.id == int(user_id)).first()
        plan_tier = resolve_user_plan_tier(user)
    limits = get_plan_limits(plan_tier)
    usage = get_usage_snapshot(db, user_id)
    if enforcement_relaxed():
        return {
            "allowed": True,
            "reason": "test_environment_skip",
            "usage": usage,
            "limits": limits,
        }
    if usage["ai_messages_today"] >= limits["max_ai_messages_per_day"]:
        return {
            "allowed": False,
            "reason": "ai_daily_limit_reached",
            "usage": usage,
            "limits": limits,
        }
    return {
        "allowed": True,
        "reason": None,
        "usage": usage,
        "limits": limits,
    }


def usage_limit_http_payload(gate: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "success": False,
        "error": "usage_limit_exceeded",
        "reason": gate.get("reason"),
        "upgrade_required": True,
        "usage": gate.get("usage") or {},
        "limits": gate.get("limits") or {},
    }
