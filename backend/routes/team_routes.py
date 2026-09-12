"""
Gestão de Equipe e Tarefas
Módulo 2 - Implementação Simplificada + stub de convites multi-usuário
"""

import logging
import secrets
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from database import TeamInvite, User, get_db
from security import get_current_user, rate_limit, require_role, Role
from security.xss_protection import sanitize_plain_text
from services.activity_feed_service import log_activity

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/team", tags=["Gestão de Equipe"])

VALID_INVITE_ROLES = frozenset({"user", "admin"})
VALID_INVITE_STATUSES = frozenset({"pending", "accepted", "revoked"})


class TeamInviteCreate(BaseModel):
    email: EmailStr
    role: str = Field("user", max_length=50)


class TeamInviteAccept(BaseModel):
    token: str = Field(..., min_length=8, max_length=128)


def _owner_id(current_user) -> int:
    return int(current_user.id)


def _validate_invite_role(value: str) -> str:
    normalized = (value or "user").strip().lower()
    if normalized not in VALID_INVITE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"role inválido; use um de: {', '.join(sorted(VALID_INVITE_ROLES))}",
        )
    return normalized


def _get_owned_invite(db: Session, invite_id: int, owner_user_id: int) -> TeamInvite:
    invite = (
        db.query(TeamInvite)
        .filter(
            TeamInvite.id == invite_id,
            TeamInvite.owner_user_id == owner_user_id,
        )
        .first()
    )
    if not invite:
        raise HTTPException(status_code=404, detail="Convite não encontrado")
    return invite


def _serialize_invite(invite: TeamInvite, *, include_token: bool = False) -> dict:
    return invite.to_dict(include_token=include_token)


# --- Membros / tarefas (legado) ---

@router.get("/members")
async def list_team_members(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista membros da equipe do escritório"""
    # Retorna usuários do mesmo "tenant" (simplificado)
    members = db.query(User).filter(
        User.id != current_user.id,
        User.is_active == True,  # noqa: E712
    ).all()

    return {
        "members": [{
            "id": m.id,
            "name": m.name,
            "email": m.email,
            "role": m.role,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        } for m in members],
        "count": len(members),
    }


@router.get("/tasks")
async def list_team_tasks(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista tarefas da equipe"""
    # Placeholder - integrar com sistema de tarefas quando implementado
    return {
        "tasks": [],
        "message": "Módulo de tarefas em desenvolvimento",
        "status": "placeholder",
    }


@router.get("/productivity")
async def team_productivity(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """Dashboard de produtividade da equipe (apenas admin)"""
    return {
        "period_days": days,
        "metrics": {
            "total_clients": 0,
            "documents_processed": 0,
            "invoices_generated": 0,
            "deadlines_met": 0,
        },
        "members": [],
        "message": "Módulo de produtividade em desenvolvimento",
    }


# --- Convites (stub multi-usuário) ---

@router.post("/invites", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=30)
async def create_team_invite(
    payload: TeamInviteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cria convite pendente (somente o owner autenticado)."""
    owner_id = _owner_id(current_user)
    email = sanitize_plain_text(str(payload.email)).strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="email inválido")
    role = _validate_invite_role(payload.role)

    # Evita duplicata pendente do mesmo owner + email
    existing = (
        db.query(TeamInvite)
        .filter(
            TeamInvite.owner_user_id == owner_id,
            TeamInvite.email == email,
            TeamInvite.status == "pending",
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Já existe convite pendente para este e-mail",
        )

    invite = TeamInvite(
        owner_user_id=owner_id,
        email=email,
        role=role,
        status="pending",
        token=secrets.token_urlsafe(32),
        created_at=datetime.utcnow(),
    )
    db.add(invite)
    db.flush()
    db.refresh(invite)
    try:
        log_activity(
            db,
            owner_id,
            "team.invite",
            f"Convite enviado para {email} ({role})",
            entity_type="team_invite",
            entity_id=invite.id,
        )
    except Exception:
        pass
    logger.info("TeamInvite %s criado por user %s para %s", invite.id, owner_id, email)
    return {"invite": _serialize_invite(invite, include_token=True)}


@router.get("/invites")
@rate_limit(requests_per_minute=60)
async def list_team_invites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista convites do escritório do usuário autenticado (IDOR-safe)."""
    owner_id = _owner_id(current_user)
    invites = (
        db.query(TeamInvite)
        .filter(TeamInvite.owner_user_id == owner_id)
        .order_by(TeamInvite.created_at.desc())
        .all()
    )
    return {
        "invites": [_serialize_invite(i) for i in invites],
        "count": len(invites),
    }


@router.post("/invites/accept")
@rate_limit(requests_per_minute=20)
async def accept_team_invite(
    payload: TeamInviteAccept,
    db: Session = Depends(get_db),
):
    """
    Aceita convite via token (sem JWT).
    Se já existir User com o e-mail, marca aceito e anexa nota de vínculo.
    Caso contrário, cria stub de User e marca aceito.
    """
    token = (payload.token or "").strip()
    if not token:
        raise HTTPException(status_code=400, detail="token obrigatório")

    invite = db.query(TeamInvite).filter(TeamInvite.token == token).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Convite não encontrado")
    if invite.status == "revoked":
        raise HTTPException(status_code=400, detail="Convite revogado")
    if invite.status == "accepted":
        raise HTTPException(status_code=400, detail="Convite já aceito")

    email = invite.email.strip().lower()
    existing_user = db.query(User).filter(User.email == email).first()
    note = None
    linked_user_id = None

    if existing_user:
        linked_user_id = existing_user.id
        note = (
            f"Usuário existente (id={existing_user.id}) vinculado ao convite "
            f"do escritório owner_user_id={invite.owner_user_id}"
        )
        # Anexa nota leve no company se vazio (stub; sem schema extra)
        if not existing_user.company:
            existing_user.company = f"team:{invite.owner_user_id}"
    else:
        stub = User(
            email=email,
            name=email.split("@")[0],
            password_hash=None,
            role="admin" if invite.role == "admin" else "user",
            company=f"team:{invite.owner_user_id}",
            is_active=True,
        )
        db.add(stub)
        db.flush()
        db.refresh(stub)
        linked_user_id = stub.id
        note = f"Stub de usuário criado (id={stub.id}) para aceite de convite"

    invite.status = "accepted"
    invite.accepted_at = datetime.utcnow()
    db.flush()
    db.refresh(invite)

    return {
        "invite": _serialize_invite(invite),
        "linked_user_id": linked_user_id,
        "note": note,
        "created_stub": existing_user is None,
    }


@router.post("/invites/{invite_id}/revoke")
@rate_limit(requests_per_minute=30)
async def revoke_team_invite(
    invite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoga convite pendente (somente owner; 404 se IDOR)."""
    owner_id = _owner_id(current_user)
    invite = _get_owned_invite(db, invite_id, owner_id)

    if invite.status == "revoked":
        return {"invite": _serialize_invite(invite), "message": "Já estava revogado"}
    if invite.status == "accepted":
        raise HTTPException(
            status_code=400,
            detail="Não é possível revogar convite já aceito",
        )

    invite.status = "revoked"
    db.flush()
    db.refresh(invite)
    return {"invite": _serialize_invite(invite)}
