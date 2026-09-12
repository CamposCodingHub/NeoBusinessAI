"""
Organization multi-tenant MVP
CRUD mínimo: criar org, listar, detalhe, adicionar membro por e-mail.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import Organization, OrganizationMember, User, get_db
from security import get_current_user, rate_limit
from security.xss_protection import sanitize_plain_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orgs", tags=["Organizations"])

VALID_MEMBER_ROLES = frozenset({"member", "admin"})
VALID_ALL_ROLES = frozenset({"owner", "admin", "member"})


class OrgCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: Optional[str] = Field(None, min_length=2, max_length=120)
    plan_tier: str = Field("free", max_length=50)


class OrgMemberAdd(BaseModel):
    email: EmailStr
    role: str = Field("member", max_length=50)


def _uid(current_user) -> int:
    return int(current_user.id)


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_only).strip("-").lower()
    return slug[:120] or "org"


def _unique_slug(db: Session, base: str) -> str:
    candidate = base
    n = 2
    while db.query(Organization).filter(Organization.slug == candidate).first():
        suffix = f"-{n}"
        candidate = f"{base[: 120 - len(suffix)]}{suffix}"
        n += 1
    return candidate


def _membership(
    db: Session, org_id: int, user_id: int
) -> Optional[OrganizationMember]:
    return (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.org_id == org_id,
            OrganizationMember.user_id == user_id,
        )
        .first()
    )


def _require_membership(
    db: Session, org_id: int, user_id: int
) -> OrganizationMember:
    member = _membership(db, org_id, user_id)
    if not member:
        raise HTTPException(status_code=404, detail="Organização não encontrada")
    return member


def _require_adminish(
    db: Session, org_id: int, user_id: int
) -> OrganizationMember:
    member = _require_membership(db, org_id, user_id)
    if member.role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas owner ou admin podem gerenciar membros",
        )
    return member


def _serialize_org(
    org: Organization, *, role: Optional[str] = None, members: Optional[list] = None
) -> dict:
    data = org.to_dict()
    if role is not None:
        data["my_role"] = role
    if members is not None:
        data["members"] = members
    return data


@router.post("", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=30)
async def create_org(
    payload: OrgCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Cria organização; o caller vira owner."""
    user_id = _uid(current_user)
    name = sanitize_plain_text(payload.name) or ""
    if len(name) < 2:
        raise HTTPException(status_code=400, detail="name inválido")

    plan_tier = (sanitize_plain_text(payload.plan_tier) or "free").strip().lower()[
        :50
    ] or "free"
    raw_slug = payload.slug.strip() if payload.slug else name
    base_slug = _slugify(sanitize_plain_text(raw_slug) or name)
    slug = _unique_slug(db, base_slug)

    org = Organization(
        name=name,
        slug=slug,
        owner_user_id=user_id,
        plan_tier=plan_tier,
    )
    db.add(org)
    db.flush()

    membership = OrganizationMember(
        org_id=org.id,
        user_id=user_id,
        role="owner",
    )
    db.add(membership)

    # Soft-link home org if user has none yet
    user = db.query(User).filter(User.id == user_id).first()
    if user is not None and getattr(user, "organization_id", None) is None:
        user.organization_id = org.id

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Não foi possível criar a organização")
    db.refresh(org)

    logger.info("Org criada id=%s owner=%s slug=%s", org.id, user_id, org.slug)
    return {"organization": _serialize_org(org, role="owner")}


@router.get("")
@rate_limit(requests_per_minute=60)
async def list_orgs(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Lista organizações em que o usuário é membro."""
    user_id = _uid(current_user)
    rows = (
        db.query(Organization, OrganizationMember.role)
        .join(
            OrganizationMember,
            OrganizationMember.org_id == Organization.id,
        )
        .filter(OrganizationMember.user_id == user_id)
        .order_by(Organization.id.desc())
        .all()
    )
    orgs = [_serialize_org(org, role=role) for org, role in rows]
    return {"organizations": orgs, "count": len(orgs)}


@router.get("/{org_id}")
@rate_limit(requests_per_minute=60)
async def get_org(
    org_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Detalhe da org se o caller for membro."""
    user_id = _uid(current_user)
    membership = _require_membership(db, org_id, user_id)
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organização não encontrada")

    members = (
        db.query(OrganizationMember, User)
        .outerjoin(User, User.id == OrganizationMember.user_id)
        .filter(OrganizationMember.org_id == org_id)
        .order_by(OrganizationMember.id.asc())
        .all()
    )
    member_payload = []
    for m, u in members:
        item = m.to_dict()
        item["email"] = u.email if u else None
        item["name"] = u.name if u else None
        member_payload.append(item)

    return {
        "organization": _serialize_org(
            org, role=membership.role, members=member_payload
        )
    }


@router.post("/{org_id}/members", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=30)
async def add_org_member(
    org_id: int,
    payload: OrgMemberAdd,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Adiciona membro existente por e-mail (role member|admin)."""
    caller_id = _uid(current_user)
    _require_adminish(db, org_id, caller_id)

    role = (payload.role or "member").strip().lower()
    if role not in VALID_MEMBER_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"role inválido; use um de: {', '.join(sorted(VALID_MEMBER_ROLES))}",
        )

    email = str(payload.email).strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuário com este e-mail não existe",
        )

    if _membership(db, org_id, user.id):
        raise HTTPException(
            status_code=400,
            detail="Usuário já é membro desta organização",
        )

    member = OrganizationMember(org_id=org_id, user_id=user.id, role=role)
    db.add(member)
    if getattr(user, "organization_id", None) is None:
        user.organization_id = org_id

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Não foi possível adicionar o membro")
    db.refresh(member)

    data = member.to_dict()
    data["email"] = user.email
    data["name"] = user.name
    return {"member": data}
