"""Authenticated usage / plan limit snapshot for the current user."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import User, get_db
from security import get_current_user
from services.usage_metering import (
    check_can_chat,
    check_can_upload,
    get_plan_limits,
    get_usage_snapshot,
    resolve_user_plan_tier,
)

router = APIRouter(prefix="/usage", tags=["Usage"])


@router.get("/me")
async def usage_me(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return current plan, usage counters, limits, and can_upload / can_chat."""
    user_id = int(current_user.user_id)
    user = db.query(User).filter(User.id == user_id).first()
    plan_tier = resolve_user_plan_tier(user)
    limits = get_plan_limits(plan_tier)
    usage = get_usage_snapshot(db, user_id)
    upload = check_can_upload(db, user_id, plan_tier=plan_tier)
    chat = check_can_chat(db, user_id, plan_tier=plan_tier)

    return {
        "success": True,
        "plan_tier": plan_tier,
        "usage": usage,
        "limits": limits,
        "can_upload": bool(upload.get("allowed")),
        "can_chat": bool(chat.get("allowed")),
        "upload_reason": upload.get("reason"),
        "chat_reason": chat.get("reason"),
    }
