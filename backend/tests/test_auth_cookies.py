"""
Testes: cookie HttpOnly access_token + auth via cookie.
App mínimo — evita import pesado de main.
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_auth_cookies.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import Base, User, get_db, get_db_async  # noqa: E402
from routes.auth_routes import router as auth_router  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth_cookies.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

TEST_PASSWORD = "SenhaForte123!"


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    finally:
        db.close()


app = FastAPI()
app.include_router(auth_router)
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_db_async] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup():
    yield
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


class TestAuthCookies:
    def test_login_sets_httponly_cookie_and_json_token(self):
        reg = client.post(
            "/auth/register",
            json={
                "email": "cookie-login@example.com",
                "password": TEST_PASSWORD,
                "name": "Cookie Login",
            },
        )
        assert reg.status_code == 201
        assert "access_token" in reg.json()
        assert "access_token" in reg.cookies

        login = client.post(
            "/auth/login",
            json={
                "email": "cookie-login@example.com",
                "password": TEST_PASSWORD,
            },
        )
        assert login.status_code == 200
        body = login.json()
        assert body["token_type"] == "bearer"
        assert body["access_token"]
        assert "access_token" in login.cookies

        # Set-Cookie flags (httponly; secure off in ENVIRONMENT=test)
        set_cookie = login.headers.get("set-cookie", "")
        assert "access_token=" in set_cookie
        assert "HttpOnly" in set_cookie or "httponly" in set_cookie.lower()
        assert "Path=/" in set_cookie or "path=/" in set_cookie.lower()

    def test_protected_endpoint_accepts_cookie_without_bearer(self):
        client.post(
            "/auth/register",
            json={
                "email": "cookie-me@example.com",
                "password": TEST_PASSWORD,
                "name": "Cookie Me",
            },
        )
        login = client.post(
            "/auth/login",
            json={
                "email": "cookie-me@example.com",
                "password": TEST_PASSWORD,
            },
        )
        assert login.status_code == 200
        assert "access_token" in login.cookies

        # Sem Authorization — TestClient reenvia cookies da sessão
        me = client.get("/auth/me")
        assert me.status_code == 200
        assert me.json()["email"] == "cookie-me@example.com"

        logout = client.post("/auth/logout")
        assert logout.status_code == 200
        assert logout.json()["token_invalidated"] is True
