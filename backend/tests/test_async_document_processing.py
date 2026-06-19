from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, Document
from routes import document_routes
from services import document_processing_service


@pytest.fixture
def document_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'async-documents.db'}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def create_document(session, tmp_path: Path, status: str = "uploaded") -> Document:
    file_path = tmp_path / "contrato.txt"
    file_path.write_text("Contrato Atlas. Prazo de 15 dias.", encoding="utf-8")
    document = Document(
        user_id=77,
        filename="contrato.txt",
        original_filename="contrato.txt",
        file_path=str(file_path),
        file_size=file_path.stat().st_size,
        file_type=".txt",
        title="Contrato",
        status=status,
        custom_data={"sha256": "abc"},
    )
    session.add(document)
    session.commit()
    session.refresh(document)
    return document


def test_processing_service_persists_progress_and_result(
    document_session,
    tmp_path,
    monkeypatch,
):
    document = create_document(document_session, tmp_path)
    progress_updates = []
    monkeypatch.setattr(
        document_processing_service,
        "process_uploaded_path",
        lambda *args: {
            "success": True,
            "text": "Contrato Atlas. Prazo de 15 dias. Valor R$ 5.000,00.",
            "pages": 2,
            "method": "test_extractor",
            "truncated": False,
        },
    )
    monkeypatch.setattr(
        document_processing_service.lexscan_engine,
        "process_document",
        lambda text: {
            "success": True,
            "summary": "Resumo Atlas",
            "analysis": "Analise profissional completa.",
            "document_type": "contrato",
            "process_number": "",
            "court": "",
            "parties": {"autor": "Atlas"},
            "deadlines": [{"days": "15"}],
            "values": [{"value": "5.000,00"}],
            "analysis_mode": "remote_ai",
            "ai_analysis_used": True,
            "ai_error": "",
        },
    )

    processed = document_processing_service.process_document_record(
        document_session,
        document,
        lambda progress, stage, message: progress_updates.append(
            (progress, stage, message)
        ),
    )

    assert processed.status == "completed"
    assert processed.custom_data["progress"] == 100
    assert processed.custom_data["processing_stage"] == "completed"
    assert processed.custom_data["pages"] == 2
    assert processed.content["document_type"] == "contrato"
    assert [update[0] for update in progress_updates] == [10, 25, 55, 85, 100]


def test_processing_service_persists_recoverable_error(
    document_session,
    tmp_path,
    monkeypatch,
):
    document = create_document(document_session, tmp_path)
    monkeypatch.setattr(
        document_processing_service,
        "process_uploaded_path",
        lambda *args: {
            "success": False,
            "text": "",
            "error": "PDF corrompido",
        },
    )

    with pytest.raises(document_processing_service.DocumentProcessingError):
        document_processing_service.process_document_record(
            document_session,
            document,
        )

    document_session.refresh(document)
    assert document.status == "error"
    assert "PDF corrompido" in document.error_message
    assert document.custom_data["processing_stage"] == "error"
    assert document.custom_data["progress"] == 100


@pytest.mark.asyncio
async def test_analyze_route_queues_once_and_exposes_status(
    document_session,
    tmp_path,
    monkeypatch,
):
    document = create_document(document_session, tmp_path)
    user = SimpleNamespace(user_id="77")
    monkeypatch.setattr(document_routes, "DOCUMENT_QUEUE_AVAILABLE", True)
    monkeypatch.setattr(
        document_routes,
        "queue_document_path_processing",
        lambda document_id, user_id: "task-123",
    )
    monkeypatch.setattr(
        document_routes,
        "get_task_status",
        lambda task_id: {
            "task_id": task_id,
            "status": "PENDING",
            "ready": False,
            "meta": None,
        },
    )

    result = await document_routes.analyze_document(
        document.id,
        current_user=user,
        db=document_session,
    )

    assert result["status"] == "queued"
    assert result["task_id"] == "task-123"
    document_session.refresh(document)
    assert document.status == "queued"
    assert document.custom_data["progress"] == 5

    status = await document_routes.document_processing_status(
        document.id,
        current_user=user,
        db=document_session,
    )
    assert status["status"] == "queued"
    assert status["task"]["status"] == "PENDING"

    with pytest.raises(HTTPException) as duplicate_error:
        await document_routes.analyze_document(
            document.id,
            current_user=user,
            db=document_session,
        )
    assert duplicate_error.value.status_code == 409

    with pytest.raises(HTTPException) as delete_error:
        await document_routes.delete_document(
            document.id,
            current_user=user,
            db=document_session,
        )
    assert delete_error.value.status_code == 409
