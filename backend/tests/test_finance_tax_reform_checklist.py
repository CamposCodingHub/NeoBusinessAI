"""
Testes: GET /finance/tax-reform-checklist — ajuda metodológica estática.
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_finance_tax_reform.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, User, get_db  # noqa: E402
from routes.finance_routes import router as finance_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402
from services.tax_reform_checklist_service import (  # noqa: E402
    TAX_REFORM_DISCLAIMER,
    build_tax_reform_checklist,
)

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_finance_tax_reform.db"
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
    return _make_user("taxreform.owner@example.com", "Tax Reform Owner")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


class TestTaxReformChecklist:
    def test_requires_jwt(self):
        resp = client.get("/finance/tax-reform-checklist")
        assert resp.status_code in (401, 403)

    def test_static_methodological_items(self, auth_headers):
        resp = client.get("/finance/tax-reform-checklist", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["stub"] is True
        assert data["count"] >= 3
        assert TAX_REFORM_DISCLAIMER[:40] in data["disclaimer"]
        ids = [i["id"] for i in data["items"]]
        assert "esocial_reinf_dctfweb" in ids
        assert "reforma_ibs_cbs" in ids
        assert "disclaimer_crc" in ids
        blob = str(data).lower()
        # No invented fixed rates / exact day claims as facts
        assert "%" not in blob
        assert "dia 20" not in blob
        assert "art." not in blob  # no invented article numbers as certainty

    def test_service_build(self):
        built = build_tax_reform_checklist()
        assert built["source"] == "methodological_help_not_legal_advice"
        assert built["count"] == len(built["items"])
