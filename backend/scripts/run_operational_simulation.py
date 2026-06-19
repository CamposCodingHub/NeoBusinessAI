"""
Simulador operacional automatizado
==================================
Cria uma base representativa de operacao, roda a inteligencia operacional
e salva relatorios em disco.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./simulation_ops.db"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "false"

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import (  # noqa: E402
    Base,
    Client,
    Deadline,
    Document,
    Invoice,
    LegalDocument,
    SessionLocal,
    User,
    WhatsAppConfig,
    engine,
)
from services.operations_intelligence_service import (  # noqa: E402
    operations_intelligence_service,
)


def seed_simulation_data():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        user = User(
            email="simulacao@neobusiness.ai",
            password_hash="hash",
            name="Simulacao NeoBusiness",
            role="premium",
            plan_tier="premium",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        documents = [
            Document(
                user_id=user.id,
                filename="inicial-caso-tributario.pdf",
                original_filename="inicial-caso-tributario.pdf",
                title="Caso Tributario",
                file_type=".pdf",
                status="completed",
            ),
            Document(
                user_id=user.id,
                filename="contrato-societario.pdf",
                original_filename="contrato-societario.pdf",
                title="Contrato Societario",
                file_type=".pdf",
                status="uploaded",
            ),
            Document(
                user_id=user.id,
                filename="audiencia-trabalhista.pdf",
                original_filename="audiencia-trabalhista.pdf",
                title="Audiencia Trabalhista",
                file_type=".pdf",
                status="processing",
            ),
        ]

        clients = [
            Client(
                user_id=user.id,
                name="Industria Aurora",
                email="juridico@aurora.com",
                status="active",
            ),
            Client(
                user_id=user.id,
                name="Grupo Vale Verde",
                email="contato@valeverde.com",
                status="prospect",
            ),
            Client(
                user_id=user.id,
                name="Cliente Inativo",
                email="inativo@example.com",
                status="inactive",
            ),
        ]

        db.add_all(documents + clients)
        db.commit()

        deadlines = [
            Deadline(
                user_id=user.id,
                document_id=documents[0].id,
                description="Impugnacao fiscal",
                due_date=datetime.utcnow() - timedelta(days=2),
                urgency="high",
                is_completed=False,
            ),
            Deadline(
                user_id=user.id,
                document_id=documents[2].id,
                description="Audiencia conciliacao",
                due_date=datetime.utcnow() + timedelta(days=3),
                urgency="high",
                is_completed=False,
            ),
        ]

        invoices = [
            Invoice(
                user_id=user.id,
                client_id=clients[0].id,
                invoice_number="SIM-001",
                description="Mensalidade consultiva",
                amount_cents=450000,
                discount_cents=0,
                total_cents=450000,
                status="paid",
                due_date=datetime.utcnow() - timedelta(days=20),
                paid_at=datetime.utcnow() - timedelta(days=12),
            ),
            Invoice(
                user_id=user.id,
                client_id=clients[0].id,
                invoice_number="SIM-002",
                description="Exito contratual",
                amount_cents=180000,
                discount_cents=0,
                total_cents=180000,
                status="pending",
                due_date=datetime.utcnow() + timedelta(days=10),
            ),
            Invoice(
                user_id=user.id,
                client_id=clients[2].id,
                invoice_number="SIM-003",
                description="Parcela em atraso",
                amount_cents=95000,
                discount_cents=0,
                total_cents=95000,
                status="overdue",
                due_date=datetime.utcnow() - timedelta(days=9),
            ),
        ]

        legal_documents = [
            LegalDocument(
                user_id=user.id,
                document_id=documents[0].id,
                piece_type="peticao_inicial",
                jurisdiction="tributario",
                parties="Empresa x Fazenda",
                facts="Auto de infracao e defesa administrativa previa.",
                requests="Anulacao do auto e tutela.",
                status="completed",
                content="Peca final pronta para revisao.",
                generated_at=datetime.utcnow() - timedelta(days=1),
            ),
            LegalDocument(
                user_id=user.id,
                document_id=documents[2].id,
                piece_type="contestacao",
                jurisdiction="trabalhista",
                parties="Reclamante x Reclamada",
                facts="Contestacao em andamento.",
                requests="Improcedencia dos pedidos.",
                status="generating",
            ),
        ]

        whatsapp = WhatsAppConfig(
            user_id=user.id,
            provider="twilio",
            twilio_phone_number="+5511999999999",
            is_active=True,
            is_connected=False,
            auto_notify_deadlines=False,
            auto_notify_invoices=True,
        )

        db.add_all(deadlines + invoices + legal_documents + [whatsapp])
        db.commit()

        overview = operations_intelligence_service.build_overview(db, user.id)
        markdown = operations_intelligence_service.build_markdown_summary(overview)
        return overview, markdown
    finally:
        db.close()


def save_reports(overview, markdown):
    reports_dir = Path(__file__).resolve().parents[2] / "relatorios_melhorias" / "simulacoes"
    reports_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    json_path = reports_dir / f"simulacao_operacional_{timestamp}.json"
    md_path = reports_dir / f"simulacao_operacional_{timestamp}.md"

    json_path.write_text(
        json.dumps(overview, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    md_path.write_text(markdown, encoding="utf-8")
    return json_path, md_path


if __name__ == "__main__":
    overview, markdown = seed_simulation_data()
    json_path, md_path = save_reports(overview, markdown)
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    print(f"Score de maturidade: {overview['maturity_score']}")
    print(f"Resumo: {overview['executive_summary']}")
