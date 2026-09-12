"""
Testes: GET /finance/tax-calendar — lembretes metodológicos (stub, não API RFB).
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_finance_tax_calendar.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, User, get_db  # noqa: E402
from routes.finance_routes import router as finance_router  # noqa: E402
from security import create_access_token  # noqa: E402
from security.auth import Role  # noqa: E402
from services.tax_calendar_service import (  # noqa: E402
    DUE_HINT_CONFIRM,
    TAX_CALENDAR_DISCLAIMER,
    build_tax_calendar,
    parse_month,
)

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_finance_tax_calendar.db"
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
    return _make_user("taxcal.owner@example.com", "Tax Calendar Owner")


@pytest.fixture
def auth_headers(owner):
    return _headers_for(owner)


class TestTaxCalendar:
    def test_tax_calendar_requires_jwt(self):
        resp = client.get("/finance/tax-calendar?month=2026-09")
        assert resp.status_code in (401, 403)

    def test_tax_calendar_methodological_items(self, auth_headers):
        resp = client.get(
            "/finance/tax-calendar?month=2026-09",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["month"] == "2026-09"
        assert data["stub"] is True
        assert data["count"] >= 3
        assert TAX_CALENDAR_DISCLAIMER[:30] in data["disclaimer"]
        codes = [i["code"] for i in data["items"]]
        assert "SIMPLES_DAS" in codes
        assert "ISS_MUNICIPAL" in codes
        assert "DCTFWEB_ESOCIAL" in codes
        for item in data["items"]:
            assert set(item.keys()) >= {"code", "title", "due_hint", "disclaimer"}
            assert DUE_HINT_CONFIRM in item["due_hint"]
            # No invented fixed rates / exact day claims
            assert "%" not in item["due_hint"]
            assert "dia 20" not in item["due_hint"].lower()

    def test_tax_calendar_invalid_month(self, auth_headers):
        resp = client.get(
            "/finance/tax-calendar?month=2026-13",
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_service_parse_and_build(self):
        assert parse_month("2026-09") == "2026-09"
        with pytest.raises(ValueError):
            parse_month("09-2026")
        built = build_tax_calendar("2026-09")
        assert built["count"] == 3
        assert built["source"] == "methodological_stub_not_rfb_api"
