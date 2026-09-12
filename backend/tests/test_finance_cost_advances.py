"""
Testes: CRUD /finance/cost-advances — custas / adiantamentos (JWT + ownership).
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_finance_cost_advances.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, CostAdvance, User, get_db  # noqa: E402
from routes.finance_routes import router as finance_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_finance_cost_advances.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(finance_router)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


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
    return _make_user("custas.owner@example.com", "Custas Owner")


@pytest.fixture
def stranger():
    return _make_user("custas.stranger@example.com", "Stranger")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def stranger_headers(stranger):
    return _headers_for(stranger)


class TestCostAdvances:
    def test_requires_jwt(self):
        resp = client.get("/finance/cost-advances")
        assert resp.status_code in (401, 403)

    def test_create_list_and_update(self, owner, auth_headers):
        created = client.post(
            "/finance/cost-advances",
            json={
                "description": "Guia inicial TRT",
                "amount": 350.5,
                "client_id": None,
                "matter_id": None,
            },
            headers=auth_headers,
        )
        assert created.status_code == 201, created.text
        body = created.json()
        assert body["description"] == "Guia inicial TRT"
        assert body["amount"] == 350.5
        assert body["status"] == "advanced"
        advance_id = body["id"]

        listed = client.get("/finance/cost-advances", headers=auth_headers)
        assert listed.status_code == 200
        assert listed.json()["count"] >= 1
        assert any(i["id"] == advance_id for i in listed.json()["items"])

        patched = client.patch(
            f"/finance/cost-advances/{advance_id}",
            json={"status": "reimbursed"},
            headers=auth_headers,
        )
        assert patched.status_code == 200
        assert patched.json()["status"] == "reimbursed"

        got = client.get(f"/finance/cost-advances/{advance_id}", headers=auth_headers)
        assert got.status_code == 200
        assert got.json()["status"] == "reimbursed"

    def test_ownership_isolation(self, owner, auth_headers, stranger_headers):
        created = client.post(
            "/finance/cost-advances",
            json={"description": "Perícia", "amount": 1200},
            headers=auth_headers,
        )
        assert created.status_code == 201
        advance_id = created.json()["id"]

        denied = client.get(
            f"/finance/cost-advances/{advance_id}",
            headers=stranger_headers,
        )
        assert denied.status_code == 404

        denied_patch = client.patch(
            f"/finance/cost-advances/{advance_id}",
            json={"status": "written_off"},
            headers=stranger_headers,
        )
        assert denied_patch.status_code == 404

        # owner still sees advanced
        db = TestingSessionLocal()
        try:
            row = db.query(CostAdvance).filter(CostAdvance.id == advance_id).first()
            assert row is not None
            assert row.user_id == owner.id
            assert row.status == "advanced"
        finally:
            db.close()

    def test_validation_and_delete(self, auth_headers):
        bad = client.post(
            "/finance/cost-advances",
            json={"description": "", "amount": 10},
            headers=auth_headers,
        )
        assert bad.status_code == 400

        bad_amt = client.post(
            "/finance/cost-advances",
            json={"description": "X", "amount": -1},
            headers=auth_headers,
        )
        assert bad_amt.status_code == 400

        created = client.post(
            "/finance/cost-advances",
            json={"description": "Diligência", "amount": 80},
            headers=auth_headers,
        )
        assert created.status_code == 201
        advance_id = created.json()["id"]

        deleted = client.delete(
            f"/finance/cost-advances/{advance_id}",
            headers=auth_headers,
        )
        assert deleted.status_code == 200
        assert deleted.json()["ok"] is True

        missing = client.get(
            f"/finance/cost-advances/{advance_id}",
            headers=auth_headers,
        )
        assert missing.status_code == 404
