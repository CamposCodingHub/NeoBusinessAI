"""
Testes básicos do Matter / Case MVP
CRUD JWT (app mínimo — evita import pesado de main).
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_matters.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import (  # noqa: E402
    Base,
    Client,
    Matter,
    Organization,
    OrganizationMember,
    User,
    get_db,
)
from routes.matter_routes import router as matter_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_matters.db"
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
    finally:
        db.close()


app = FastAPI()
app.include_router(matter_router)
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



def _make_org(owner: User, name: str = "Firm Matter", slug: str = "firm-matter") -> Organization:
    db = TestingSessionLocal()
    try:
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
        db.refresh(org)
        return org
    finally:
        db.close()


def _headers_for(user: User) -> dict:
    token = create_access_token(user_id=str(user.id), role=Role.USER)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def owner():
    return _make_user("matter.owner@example.com", "Matter Owner")


@pytest.fixture
def other():
    return _make_user("matter.other@example.com", "Other Firm")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def other_auth_headers(other):
    return _headers_for(other)


@pytest.fixture
def owned_client(owner):
    db = TestingSessionLocal()
    try:
        row = Client(user_id=owner.id, name="Cliente Matter", email="cli@example.com")
        db.add(row)
        db.commit()
        db.refresh(row)
        return row
    finally:
        db.close()


class TestMatterRoutes:
    def test_create_and_list_matters(self, auth_headers):
        created = client.post(
            "/matters",
            json={
                "title": "Ação Trabalhista Silva",
                "practice_area": "Trabalhista",
                "opposing_party": "Empresa XYZ",
                "court": "TRT-2",
                "process_number": "1000123-45.2024.5.02.0001",
                "notes": "Primeira audiência marcada",
            },
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        body = created.json()
        assert body["matter"]["title"] == "Ação Trabalhista Silva"
        assert body["matter"]["status"] == "open"
        assert body["matter"]["process_number"] == "1000123-45.2024.5.02.0001"

        listed = client.get("/matters", headers=auth_headers)
        assert listed.status_code == 200
        data = listed.json()
        assert data["pagination"]["total"] >= 1
        assert any(m["title"] == "Ação Trabalhista Silva" for m in data["matters"])

    def test_get_matter_by_id(self, auth_headers):
        created = client.post(
            "/matters",
            json={"title": "Consulta Cível", "practice_area": "Cível"},
            headers=auth_headers,
        )
        matter_id = created.json()["matter"]["id"]

        fetched = client.get(f"/matters/{matter_id}", headers=auth_headers)
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["matter"]["id"] == matter_id
        assert fetched.json()["matter"]["title"] == "Consulta Cível"

    def test_patch_status_and_fields(self, auth_headers):
        created = client.post(
            "/matters",
            json={"title": "Caso Pendente", "practice_area": "Família"},
            headers=auth_headers,
        )
        matter_id = created.json()["matter"]["id"]

        patched = client.patch(
            f"/matters/{matter_id}",
            json={"status": "pending", "notes": "Aguardando documentos"},
            headers=auth_headers,
        )
        assert patched.status_code == 200, patched.text
        assert patched.json()["matter"]["status"] == "pending"
        assert "documentos" in patched.json()["matter"]["notes"]

    def test_invalid_status_rejected(self, auth_headers):
        created = client.post(
            "/matters",
            json={"title": "Status Inválido"},
            headers=auth_headers,
        )
        matter_id = created.json()["matter"]["id"]
        bad = client.patch(
            f"/matters/{matter_id}",
            json={"status": "archived_xyz"},
            headers=auth_headers,
        )
        assert bad.status_code == 400

    def test_create_with_owned_client(self, auth_headers, owned_client):
        created = client.post(
            "/matters",
            json={
                "title": "Caso com Cliente",
                "client_id": owned_client.id,
                "practice_area": "Tributário",
            },
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        assert created.json()["matter"]["client_id"] == owned_client.id

    def test_idor_other_user_cannot_get(self, auth_headers, other_auth_headers):
        created = client.post(
            "/matters",
            json={"title": "Caso Privado"},
            headers=auth_headers,
        )
        matter_id = created.json()["matter"]["id"]

        denied = client.get(f"/matters/{matter_id}", headers=other_auth_headers)
        assert denied.status_code == 404

        denied_patch = client.patch(
            f"/matters/{matter_id}",
            json={"status": "closed"},
            headers=other_auth_headers,
        )
        assert denied_patch.status_code == 404


    def test_create_with_organization_id(self, auth_headers, owner):
        org = _make_org(owner, "Org Matter OK", "org-matter-ok")
        created = client.post(
            "/matters",
            json={
                "title": "Caso com Org",
                "organization_id": org.id,
                "practice_area": "Civel",
            },
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        body = created.json()["matter"]
        assert body["organization_id"] == org.id
        assert body["title"] == "Caso com Org"

        listed = client.get(
            f"/matters?organization_id={org.id}",
            headers=auth_headers,
        )
        assert listed.status_code == 200, listed.text
        assert any(m["id"] == body["id"] for m in listed.json()["matters"])

    def test_create_organization_id_forbids_non_member(
        self, auth_headers, other_auth_headers, owner, other
    ):
        org = _make_org(owner, "Org Matter Forbid", "org-matter-forbid")
        denied = client.post(
            "/matters",
            json={
                "title": "Caso Intruso",
                "organization_id": org.id,
            },
            headers=other_auth_headers,
        )
        assert denied.status_code == 403, denied.text

    def test_requires_auth(self):
        response = client.get("/matters")
        assert response.status_code in (401, 403)
