"""
Pragmatic org-scoped RBAC helpers for multi-tenant access.

Daytime polish: membership checks without a full permission matrix.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from database import OrganizationMember


def get_user_org_ids(db: Session, user_id: int) -> List[int]:
    """Return org ids where the user is an active member."""
    rows = (
        db.query(OrganizationMember.org_id)
        .filter(OrganizationMember.user_id == int(user_id))
        .all()
    )
    return [int(row[0]) for row in rows]


def require_org_member(
    db: Session, user_id: int, org_id: int
) -> OrganizationMember:
    """Return membership or raise HTTP 403."""
    member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.org_id == int(org_id),
            OrganizationMember.user_id == int(user_id),
        )
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: usuário não é membro da organização",
        )
    return member


def user_can_access_resource(
    db: Session,
    user_id: int,
    resource_user_id: int,
    resource_org_id: Optional[int] = None,
) -> bool:
    """
    Same owner, or member of the resource's organization when org_id is set.

    Rule: user_id == resource_user_id OR
          (resource_org_id and user is member of that org).
    """
    if int(user_id) == int(resource_user_id):
        return True
    if resource_org_id is None:
        return False
    member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.org_id == int(resource_org_id),
            OrganizationMember.user_id == int(user_id),
        )
        .first()
    )
    return member is not None
