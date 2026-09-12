"""
Testes: Organization multi-tenant MVP (create/list/detail/members) — JWT + membership.
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_org_routes.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import (  # noqa: E402
    Base,
    Organization,
    OrganizationMember,
    User,
    get_db,
)
from routes.org_routes import router as org_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_org_routes.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    finally:
        db.close()


app = FastAPI()
app.include_router(org_router)
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def _make_user(email: str, name: str) -> User:
    db = TestingSessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return existing
        user = User(email=email, name=name, password_hash="x", role="user")
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def _headers_for(user: User) -> dict:
    token = create_access_token(user_id=str(user.id), role=Role.USER)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def owner():
    return _make_user("org.owner@example.com", "Org Owner")


@pytest.fixture
def colleague():
    return _make_user("org.colleague@example.com", "Colleague")


@pytest.fixture
def stranger():
    return _make_user("org.stranger@example.com", "Stranger")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def colleague_headers(colleague):
    return _headers_for(colleague)


@pytest.fixture
def stranger_headers(stranger):
    return _headers_for(stranger)


class TestOrgRoutes:
    def test_create_and_list_orgs(self, owner, auth_headers):
        created = client.post(
            "/orgs",
            json={"name": "Escritório Alpha", "slug": "escritorio-alpha"},
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        body = created.json()["organization"]
        assert body["name"] == "Escritório Alpha"
        assert body["slug"] == "escritorio-alpha"
        assert body["owner_user_id"] == owner.id
        assert body["my_role"] == "owner"
        assert body["plan_tier"] == "free"

        listed = client.get("/orgs", headers=auth_headers)
        assert listed.status_code == 200, listed.text
        data = listed.json()
        assert data["count"] >= 1
        assert any(o["id"] == body["id"] for o in data["organizations"])

        db = TestingSessionLocal()
        try:
            membership = (
                db.query(OrganizationMember)
                .filter(
                    OrganizationMember.org_id == body["id"],
                    OrganizationMember.user_id == owner.id,
                )
                .first()
            )
            assert membership is not None
            assert membership.role == "owner"
            u = db.query(User).filter(User.id == owner.id).first()
            assert u.organization_id == body["id"]
        finally:
            db.close()

    def test_get_org_detail_as_member(self, auth_headers):
        created = client.post(
            "/orgs",
            json={"name": "Detail Org", "slug": "detail-org"},
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        org_id = created.json()["organization"]["id"]

        detail = client.get(f"/orgs/{org_id}", headers=auth_headers)
        assert detail.status_code == 200, detail.text
        org = detail.json()["organization"]
        assert org["id"] == org_id
        assert org["my_role"] == "owner"
        assert isinstance(org["members"], list)
        assert any(m["role"] == "owner" for m in org["members"])

    def test_idor_non_member_gets_404(self, auth_headers, stranger_headers):
        created = client.post(
            "/orgs",
            json={"name": "Private Org", "slug": "private-org"},
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        org_id = created.json()["organization"]["id"]

        denied = client.get(f"/orgs/{org_id}", headers=stranger_headers)
        assert denied.status_code == 404

        stranger_list = client.get("/orgs", headers=stranger_headers)
        assert stranger_list.status_code == 200
        assert all(o["id"] != org_id for o in stranger_list.json()["organizations"])

    def test_add_member_by_email(self, owner, colleague, auth_headers, colleague_headers):
        created = client.post(
            "/orgs",
            json={"name": "Team Org", "slug": "team-org"},
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        org_id = created.json()["organization"]["id"]

        added = client.post(
            f"/orgs/{org_id}/members",
            json={"email": colleague.email, "role": "admin"},
            headers=auth_headers,
        )
        assert added.status_code == 201, added.text
        member = added.json()["member"]
        assert member["user_id"] == colleague.id
        assert member["role"] == "admin"
        assert member["email"] == colleague.email

        # Colleague now sees the org
        listed = client.get("/orgs", headers=colleague_headers)
        assert listed.status_code == 200
        assert any(o["id"] == org_id for o in listed.json()["organizations"])

        # Duplicate rejected
        dup = client.post(
            f"/orgs/{org_id}/members",
            json={"email": colleague.email, "role": "member"},
            headers=auth_headers,
        )
        assert dup.status_code == 400

        # Missing email
        missing = client.post(
            f"/orgs/{org_id}/members",
            json={"email": "nobody@example.com", "role": "member"},
            headers=auth_headers,
        )
        assert missing.status_code == 404

    def test_auth_required(self):
        assert client.get("/orgs").status_code in (401, 403)
        assert client.post(
            "/orgs",
            json={"name": "X"},
        ).status_code in (401, 403)
        assert client.get("/orgs/1").status_code in (401, 403)
        assert client.post(
            "/orgs/1/members",
            json={"email": "a@b.com", "role": "member"},
        ).status_code in (401, 403)

    def test_member_cannot_add_members(
        self, owner, colleague, stranger, auth_headers, colleague_headers
    ):
        created = client.post(
            "/orgs",
            json={"name": "Guard Org", "slug": "guard-org"},
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        org_id = created.json()["organization"]["id"]

        # Add colleague as plain member
        added = client.post(
            f"/orgs/{org_id}/members",
            json={"email": colleague.email, "role": "member"},
            headers=auth_headers,
        )
        assert added.status_code == 201, added.text

        forbidden = client.post(
            f"/orgs/{org_id}/members",
            json={"email": stranger.email, "role": "member"},
            headers=colleague_headers,
        )
        assert forbidden.status_code == 403
