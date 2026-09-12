"""
Testes: POST /documents/{id}/share-portal — compartilhar doc com portal (IDOR-safe).
"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_document_portal_share.db")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from database import (  # noqa: E402
    Base,
    Client,
    Document,
    Matter,
    User,
    get_db,
    get_db_async,
)
from models.portal_client import PortalClient  # noqa: E402
from routes.document_routes import router as document_router  # noqa: E402
from routes.portal_client_routes import router as portal_router  # noqa: E402
from security import create_access_token, get_password_hash  # noqa: E402
from security.auth import Role  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_document_portal_share.db"
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


async def override_get_db_async():
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    finally:
        db.close()


app = FastAPI()
app.include_router(document_router)
app.include_router(portal_router)
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_db_async] = override_get_db_async
client = TestClient(app)


def _firm_headers(user_id: int) -> dict:
    token = create_access_token(user_id=str(user_id), role=Role.USER)
    return {"Authorization": f"Bearer {token}"}


def _portal_headers(portal_id: int) -> dict:
    token = create_access_token(
        user_id=str(portal_id),
        role=Role.USER,
        permissions=["portal"],
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def seed():
    db = TestingSessionLocal()
    try:
        db.query(Document).delete()
        db.query(Matter).delete()
        db.query(PortalClient).delete()
        db.query(Client).delete()
        db.query(User).delete()
        db.commit()

        firm = User(
            email="share.firm@example.com",
            name="Share Firm",
            password_hash="x",
            role="user",
        )
        other_firm = User(
            email="share.other@example.com",
            name="Other Firm",
            password_hash="x",
            role="user",
        )
        db.add_all([firm, other_firm])
        db.flush()

        firm_client = Client(
            user_id=firm.id,
            name="Cliente Firm",
            email="cliente.share@example.com",
            status="active",
        )
        other_client = Client(
            user_id=other_firm.id,
            name="Cliente Outro",
            email="outro.share@example.com",
            status="active",
        )
        db.add_all([firm_client, other_client])
        db.flush()

        portal = PortalClient(
            client_id=firm_client.id,
            email="cliente.share@example.com",
            password_hash=get_password_hash("senha-portal"),
            is_active=True,
        )
        db.add(portal)
        db.flush()

        matter = Matter(
            user_id=firm.id,
            client_id=firm_client.id,
            title="Caso Share",
            status="open",
        )
        db.add(matter)
        db.flush()

        doc = Document(
            user_id=firm.id,
            filename="interno.pdf",
            title="Doc Interno",
            file_type="pdf",
            status="completed",
            custom_data={"progress": 100},
        )
        foreign_doc = Document(
            user_id=other_firm.id,
            filename="alheio.pdf",
            title="Doc Alheio",
            file_type="pdf",
            status="completed",
            custom_data={},
        )
        db.add_all([doc, foreign_doc])
        db.commit()

        return {
            "firm_id": firm.id,
            "other_firm_id": other_firm.id,
            "client_id": firm_client.id,
            "other_client_id": other_client.id,
            "portal_id": portal.id,
            "matter_id": matter.id,
            "doc_id": doc.id,
            "foreign_doc_id": foreign_doc.id,
        }
    finally:
        db.close()


class TestDocumentPortalShare:
    def test_share_sets_custom_data_client_id(self, seed):
        res = client.post(
            f"/documents/{seed['doc_id']}/share-portal",
            json={"client_id": seed["client_id"]},
            headers=_firm_headers(seed["firm_id"]),
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["success"] is True
        assert body["client_id"] == seed["client_id"]
        assert body["custom_data"]["client_id"] == seed["client_id"]

        db = TestingSessionLocal()
        try:
            doc = db.query(Document).filter(Document.id == seed["doc_id"]).first()
            assert doc.custom_data.get("client_id") == seed["client_id"]
            assert doc.custom_data.get("progress") == 100
        finally:
            db.close()

    def test_share_with_matter_id(self, seed):
        res = client.post(
            f"/documents/{seed['doc_id']}/share-portal",
            json={
                "client_id": seed["client_id"],
                "matter_id": seed["matter_id"],
            },
            headers=_firm_headers(seed["firm_id"]),
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["matter_id"] == seed["matter_id"]
        assert body["custom_data"]["matter_id"] == seed["matter_id"]

        db = TestingSessionLocal()
        try:
            doc = db.query(Document).filter(Document.id == seed["doc_id"]).first()
            assert doc.matter_id == seed["matter_id"]
            assert doc.custom_data.get("client_id") == seed["client_id"]
        finally:
            db.close()

    def test_idor_foreign_document(self, seed):
        res = client.post(
            f"/documents/{seed['foreign_doc_id']}/share-portal",
            json={"client_id": seed["client_id"]},
            headers=_firm_headers(seed["firm_id"]),
        )
        assert res.status_code == 404

    def test_idor_foreign_client(self, seed):
        res = client.post(
            f"/documents/{seed['doc_id']}/share-portal",
            json={"client_id": seed["other_client_id"]},
            headers=_firm_headers(seed["firm_id"]),
        )
        assert res.status_code == 400
        assert "client_id" in res.json()["detail"].lower()

    def test_requires_auth(self, seed):
        res = client.post(
            f"/documents/{seed['doc_id']}/share-portal",
            json={"client_id": seed["client_id"]},
        )
        assert res.status_code == 401

    def test_portal_lists_shared_document(self, seed):
        share = client.post(
            f"/documents/{seed['doc_id']}/share-portal",
            json={"client_id": seed["client_id"]},
            headers=_firm_headers(seed["firm_id"]),
        )
        assert share.status_code == 200, share.text

        portal = client.get(
            "/portal/documents",
            headers=_portal_headers(seed["portal_id"]),
        )
        assert portal.status_code == 200, portal.text
        ids = [d["id"] for d in portal.json()["documents"]]
        assert seed["doc_id"] in ids
        assert seed["foreign_doc_id"] not in ids
