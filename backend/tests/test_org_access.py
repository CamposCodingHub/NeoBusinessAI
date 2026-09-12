"""
Unit tests for org-scoped RBAC helpers (no full main import).
"""

import os

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_org_access.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import (  # noqa: E402
    Base,
    Organization,
    OrganizationMember,
    User,
)
from services.org_access import (  # noqa: E402
    get_user_org_ids,
    require_org_member,
    user_can_access_resource,
)

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_org_access.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        # Isolate each test
        session.query(OrganizationMember).delete()
        session.query(Organization).delete()
        session.query(User).delete()
        session.commit()
        yield session
    finally:
        session.close()


def _user(db, email: str, name: str) -> User:
    user = User(email=email, name=name, password_hash="x", role="user")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _org(db, owner: User, name: str = "Firm", slug: str = "firm") -> Organization:
    org = Organization(
        name=name, slug=slug, owner_user_id=owner.id, plan_tier="free"
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    db.add(
        OrganizationMember(org_id=org.id, user_id=owner.id, role="owner")
    )
    db.commit()
    return org


def test_get_user_org_ids_returns_memberships(db):
    owner = _user(db, "owner@example.com", "Owner")
    colleague = _user(db, "col@example.com", "Colleague")
    outsider = _user(db, "out@example.com", "Outsider")
    org_a = _org(db, owner, "A", "org-a")
    org_b = _org(db, owner, "B", "org-b")
    db.add(OrganizationMember(org_id=org_a.id, user_id=colleague.id, role="member"))
    db.commit()

    assert sorted(get_user_org_ids(db, owner.id)) == sorted([org_a.id, org_b.id])
    assert get_user_org_ids(db, colleague.id) == [org_a.id]
    assert get_user_org_ids(db, outsider.id) == []


def test_require_org_member_ok_and_forbidden(db):
    owner = _user(db, "owner2@example.com", "Owner")
    outsider = _user(db, "out2@example.com", "Outsider")
    org = _org(db, owner, "C", "org-c")

    member = require_org_member(db, owner.id, org.id)
    assert member.user_id == owner.id
    assert member.org_id == org.id

    with pytest.raises(HTTPException) as exc:
        require_org_member(db, outsider.id, org.id)
    assert exc.value.status_code == 403


def test_user_can_access_resource_same_user(db):
    user = _user(db, "same@example.com", "Same")
    assert user_can_access_resource(db, user.id, user.id) is True
    assert user_can_access_resource(db, user.id, user.id + 99) is False


def test_user_can_access_resource_via_org_membership(db):
    owner = _user(db, "owner3@example.com", "Owner")
    member = _user(db, "mem@example.com", "Member")
    outsider = _user(db, "out3@example.com", "Outsider")
    org = _org(db, owner, "D", "org-d")
    db.add(OrganizationMember(org_id=org.id, user_id=member.id, role="member"))
    db.commit()

    # Resource owned by owner, scoped to org → member can access
    assert (
        user_can_access_resource(
            db, member.id, resource_user_id=owner.id, resource_org_id=org.id
        )
        is True
    )
    assert (
        user_can_access_resource(
            db, outsider.id, resource_user_id=owner.id, resource_org_id=org.id
        )
        is False
    )
    # No org on resource → only same user
    assert (
        user_can_access_resource(
            db, member.id, resource_user_id=owner.id, resource_org_id=None
        )
        is False
    )
