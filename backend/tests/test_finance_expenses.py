"""
Testes: /finance/expenses — despesas reembolsáveis (JWT + ownership).
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_finance_expenses.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, ExpenseClaim, User, get_db  # noqa: E402
from routes.finance_routes import router as finance_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_finance_expenses.db"
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
app.include_router(finance_router)
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
    return _make_user("exp.owner@example.com", "Exp Owner")


@pytest.fixture
def stranger():
    return _make_user("exp.stranger@example.com", "Stranger")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


@pytest.fixture
def stranger_headers(stranger):
    return _headers_for(stranger)


class TestExpenseClaims:
    def test_requires_auth(self):
        resp = client.get("/finance/expenses")
        assert resp.status_code in (401, 403)

    def test_create_list_reimburse(self, auth_headers, owner):
        create = client.post(
            "/finance/expenses",
            headers=auth_headers,
            json={
                "description": "Uber fórum → escritório",
                "amount": 48.5,
                "category": "travel",
            },
        )
        assert create.status_code == 201, create.text
        body = create.json()
        assert body["user_id"] == owner.id
        assert body["status"] == "pending"
        assert body["category"] == "travel"
        eid = body["id"]

        listed = client.get("/finance/expenses", headers=auth_headers)
        assert listed.status_code == 200
        data = listed.json()
        assert data["count"] >= 1
        assert data["pending_total"] >= 48.5

        patched = client.patch(
            f"/finance/expenses/{eid}/status",
            headers=auth_headers,
            json={"status": "reimbursed"},
        )
        assert patched.status_code == 200
        assert patched.json()["status"] == "reimbursed"

    def test_ownership_isolation(self, auth_headers, stranger_headers):
        create = client.post(
            "/finance/expenses",
            headers=auth_headers,
            json={"description": "Cópias", "amount": 12, "category": "copies"},
        )
        assert create.status_code == 201
        eid = create.json()["id"]

        listed = client.get("/finance/expenses", headers=stranger_headers)
        assert listed.status_code == 200
        assert eid not in [x["id"] for x in listed.json()["items"]]

        patch = client.patch(
            f"/finance/expenses/{eid}/status",
            headers=stranger_headers,
            json={"status": "denied"},
        )
        assert patch.status_code == 404
        assert ExpenseClaim is not None
