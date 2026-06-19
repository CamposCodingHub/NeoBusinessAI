"""
Testes da inteligencia operacional
=================================
Valida score, consolidacao e recomendacoes de alto impacto.
"""

import os
from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = "sqlite:///./test_operations.db"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "false"

from database import (  # noqa: E402
    Base,
    Client,
    Deadline,
    Document,
    Invoice,
    LegalDocument,
    User,
    WhatsAppConfig,
)
from services.operations_intelligence_service import (  # noqa: E402
    operations_intelligence_service,
)
from routes.operations_routes import (  # noqa: E402
    REPORTS_ROOT,
    _list_report_artifacts,
    _resolve_artifact,
)


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_operations.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def setup_module(module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


def test_operations_overview_builds_priorities():
    db = TestingSessionLocal()
    try:
        user = User(
            email="ops@example.com",
            password_hash="hash",
            name="Operacoes",
            role="user",
            plan_tier="premium",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        db.add_all(
            [
                Document(
                    user_id=user.id,
                    filename="contrato-1.pdf",
                    original_filename="contrato-1.pdf",
                    status="uploaded",
                    file_type=".pdf",
                ),
                Document(
                    user_id=user.id,
                    filename="contrato-2.pdf",
                    original_filename="contrato-2.pdf",
                    status="completed",
                    file_type=".pdf",
                ),
                Deadline(
                    user_id=user.id,
                    document_id=1,
                    description="Prazo vencido",
                    due_date=datetime.utcnow() - timedelta(days=1),
                    urgency="high",
                    is_completed=False,
                ),
                Deadline(
                    user_id=user.id,
                    document_id=1,
                    description="Prazo proximo",
                    due_date=datetime.utcnow() + timedelta(days=2),
                    urgency="medium",
                    is_completed=False,
                ),
                Client(
                    user_id=user.id,
                    name="Cliente Ativo",
                    email="ativo@example.com",
                    status="active",
                ),
                Client(
                    user_id=user.id,
                    name="Lead Importante",
                    email="lead@example.com",
                    status="prospect",
                ),
                Invoice(
                    user_id=user.id,
                    client_id=1,
                    invoice_number="FAT-TESTE-001",
                    description="Mensalidade",
                    amount_cents=100000,
                    discount_cents=0,
                    total_cents=100000,
                    status="overdue",
                    due_date=datetime.utcnow() - timedelta(days=4),
                ),
                Invoice(
                    user_id=user.id,
                    client_id=1,
                    invoice_number="FAT-TESTE-002",
                    description="Consultoria",
                    amount_cents=200000,
                    discount_cents=0,
                    total_cents=200000,
                    status="pending",
                    due_date=datetime.utcnow() + timedelta(days=8),
                ),
                LegalDocument(
                    user_id=user.id,
                    piece_type="peticao_inicial",
                    jurisdiction="civel",
                    parties="Autor x Reu",
                    facts="Fatos",
                    requests="Pedidos",
                    status="generating",
                ),
                WhatsAppConfig(
                    user_id=user.id,
                    provider="twilio",
                    is_active=False,
                    is_connected=False,
                    auto_notify_deadlines=False,
                    auto_notify_invoices=False,
                ),
            ]
        )
        db.commit()

        overview = operations_intelligence_service.build_overview(db, user.id)
        markdown = operations_intelligence_service.build_markdown_summary(overview)

        assert overview["workspace"]["documents"]["uploaded"] == 1
        assert overview["workspace"]["deadlines"]["overdue"] == 1
        assert overview["workspace"]["clients"]["prospects"] == 1
        assert overview["workspace"]["finance"]["overdue_total"] == 1000.0
        assert overview["maturity_score"] < 90
        assert overview["recommendations"]
        assert "prazos atrasados" in overview["executive_summary"].lower()
        assert "Score de maturidade" in markdown
    finally:
        db.close()


def test_report_artifacts_are_indexed_and_resolved_safely():
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    artifact_path = REPORTS_ROOT / "_test_route_artifact.md"

    try:
        artifact_path.write_text("# Artefato de teste\n\nConteudo operacional", encoding="utf-8")

        artifacts = _list_report_artifacts(limit=200)
        indexed = next(
            (item for item in artifacts if item["relative_path"] == "_test_route_artifact.md"),
            None,
        )

        assert indexed is not None
        assert "Conteudo operacional" in indexed["preview"]

        resolved = _resolve_artifact("_test_route_artifact.md")
        assert resolved == artifact_path.resolve()
    finally:
        if artifact_path.exists():
            artifact_path.unlink()


def test_report_artifact_blocks_path_traversal():
    with pytest.raises(HTTPException):
        _resolve_artifact("../segredo.txt")
