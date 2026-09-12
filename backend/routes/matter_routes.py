"""
Matter / Case Lifecycle — MVP
Casos unificados com status operacional (open|pending|closed).
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import Client, Matter, Organization, User, get_db
from security import get_current_user, rate_limit
from security.xss_protection import sanitize_plain_text
from services.activity_feed_service import log_activity
from services.org_access import require_org_member, user_can_access_resource

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/matters", tags=["Matters"])

VALID_STATUSES = frozenset({"open", "pending", "closed"})


class MatterCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    client_id: Optional[int] = None
    practice_area: Optional[str] = Field(None, max_length=120)
    status: str = Field("open", max_length=50)
    opposing_party: Optional[str] = Field(None, max_length=255)
    court: Optional[str] = Field(None, max_length=255)
    process_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    organization_id: Optional[int] = None


class MatterUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    client_id: Optional[int] = None
    practice_area: Optional[str] = Field(None, max_length=120)
    status: Optional[str] = Field(None, max_length=50)
    opposing_party: Optional[str] = Field(None, max_length=255)
    court: Optional[str] = Field(None, max_length=255)
    process_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


def _sanitize_optional(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = sanitize_plain_text(value)
    return cleaned if cleaned else None


def _validate_status(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"status inválido; use um de: {', '.join(sorted(VALID_STATUSES))}",
        )
    return normalized


def _get_owned_matter(db: Session, matter_id: int, user_id: int) -> Matter:
    matter = (
        db.query(Matter)
        .filter(Matter.id == matter_id, Matter.user_id == user_id)
        .first()
    )
    if not matter:
        raise HTTPException(status_code=404, detail="Matter não encontrado")
    return matter




def _matter_has_organization_id() -> bool:
    return hasattr(Matter, "organization_id")


def _org_matters_filter(db: Session, org_id: int):
    """Matters owned by the org owner, or tagged with organization_id when present."""
    org = db.query(Organization).filter(Organization.id == int(org_id)).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organização não encontrada")
    clauses = [Matter.user_id == org.owner_user_id]
    if _matter_has_organization_id():
        clauses.append(Matter.organization_id == int(org_id))
    return or_(*clauses)

def _validate_client_ownership(
    db: Session, client_id: Optional[int], user_id: int
) -> Optional[int]:
    if client_id is None:
        return None
    client = (
        db.query(Client)
        .filter(Client.id == client_id, Client.user_id == user_id)
        .first()
    )
    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="client_id inválido ou não pertence ao usuário",
        )
    return client_id


@router.get("")
@rate_limit(requests_per_minute=60)
async def list_matters(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    practice_area: Optional[str] = Query(None),
    client_id: Optional[int] = Query(None),
    org_id: Optional[int] = Query(None),
    organization_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista matters do escritorio (dono = user autenticado; opcional filtro org)."""
    resolved_org_id = organization_id if organization_id is not None else org_id
    if resolved_org_id is not None:
        require_org_member(db, current_user.id, resolved_org_id)
        query = db.query(Matter).filter(_org_matters_filter(db, resolved_org_id))
    else:
        query = db.query(Matter).filter(Matter.user_id == current_user.id)

    if status_filter:
        query = query.filter(Matter.status == _validate_status(status_filter))

    if practice_area:
        query = query.filter(Matter.practice_area.ilike(f"%{practice_area.strip()}%"))

    if client_id is not None:
        query = query.filter(Matter.client_id == client_id)

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            (Matter.title.ilike(term))
            | (Matter.process_number.ilike(term))
            | (Matter.opposing_party.ilike(term))
            | (Matter.court.ilike(term))
        )

    total = query.count()
    matters = (
        query.order_by(Matter.updated_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "matters": [m.to_dict() for m in matters],
        "pagination": {
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit if total else 0,
            "limit": limit,
        },
    }


@router.post("", status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=30)
async def create_matter(
    payload: MatterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cria um novo matter / caso."""
    matter_status = _validate_status(payload.status) or "open"
    title = sanitize_plain_text(payload.title)
    if not title:
        raise HTTPException(status_code=400, detail="title é obrigatório")

    client_id = _validate_client_ownership(db, payload.client_id, current_user.id)

    org_id_value = payload.organization_id
    if org_id_value is not None:
        require_org_member(db, current_user.id, org_id_value)

    matter_kwargs = dict(
        user_id=current_user.id,
        client_id=client_id,
        title=title,
        practice_area=_sanitize_optional(payload.practice_area),
        status=matter_status,
        opposing_party=_sanitize_optional(payload.opposing_party),
        court=_sanitize_optional(payload.court),
        process_number=_sanitize_optional(payload.process_number),
        notes=_sanitize_optional(payload.notes),
    )
    if _matter_has_organization_id():
        matter_kwargs["organization_id"] = org_id_value
    matter = Matter(**matter_kwargs)
    db.add(matter)
    db.commit()
    db.refresh(matter)
    try:
        log_activity(
            db,
            current_user.id,
            "matter.create",
            f"Matter criado: {matter.title}",
            entity_type="matter",
            entity_id=matter.id,
        )
    except Exception:
        pass
    logger.info("Matter criado: %s (user=%s)", matter.id, current_user.id)
    return {"message": "Matter criado com sucesso", "matter": matter.to_dict()}


@router.get("/{matter_id}")
@rate_limit(requests_per_minute=60)
async def get_matter(
    matter_id: int,
    org_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna um matter pelo id (ownership ou membro da org via org_id)."""
    if org_id is not None:
        require_org_member(db, current_user.id, org_id)
        matter = (
            db.query(Matter)
            .filter(Matter.id == matter_id, _org_matters_filter(db, org_id))
            .first()
        )
        if not matter:
            raise HTTPException(status_code=404, detail="Matter nao encontrado")
        resource_org = getattr(matter, "organization_id", None) or org_id
        if not user_can_access_resource(
            db,
            current_user.id,
            matter.user_id,
            resource_org_id=resource_org,
        ):
            raise HTTPException(status_code=403, detail="Acesso negado")
        return {"matter": matter.to_dict()}
    matter = _get_owned_matter(db, matter_id, current_user.id)
    return {"matter": matter.to_dict()}


@router.patch("/{matter_id}")
@rate_limit(requests_per_minute=40)
async def update_matter(
    matter_id: int,
    payload: MatterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atualiza campos do matter (status do ciclo de vida, notas, etc.)."""
    matter = _get_owned_matter(db, matter_id, current_user.id)
    data = payload.model_dump(exclude_unset=True)

    if "status" in data:
        data["status"] = _validate_status(data["status"])

    if "client_id" in data:
        data["client_id"] = _validate_client_ownership(
            db, data["client_id"], current_user.id
        )

    if "title" in data and data["title"] is not None:
        cleaned = sanitize_plain_text(data["title"])
        if not cleaned:
            raise HTTPException(status_code=400, detail="title inválido")
        data["title"] = cleaned

    for field in (
        "practice_area",
        "opposing_party",
        "court",
        "process_number",
        "notes",
    ):
        if field in data and data[field] is not None:
            data[field] = _sanitize_optional(data[field])

    for key, value in data.items():
        setattr(matter, key, value)

    matter.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(matter)
    return {"message": "Matter atualizado", "matter": matter.to_dict()}
