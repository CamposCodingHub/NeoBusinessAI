"""Transactional document processing shared by API and Celery workers."""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from sqlalchemy.orm import Session

from ai.lexscan_engine import lexscan_engine
from config import settings
from database import Document
from tools.ocr_real import process_uploaded_path


ProgressCallback = Callable[[int, str, str], None]


class DocumentProcessingError(RuntimeError):
    """Raised after a document failure has been persisted."""


def _update_metadata(
    document: Document,
    progress: int,
    stage: str,
    message: str,
) -> None:
    document.custom_data = {
        **(document.custom_data or {}),
        "progress": progress,
        "processing_stage": stage,
        "processing_message": message,
    }


def process_document_record(
    db: Session,
    document: Document,
    progress_callback: Optional[ProgressCallback] = None,
) -> Document:
    """Extract, analyze and persist one document with bounded resources."""
    started_at = time.perf_counter()

    def report(progress: int, stage: str, message: str) -> None:
        _update_metadata(document, progress, stage, message)
        db.commit()
        if progress_callback:
            progress_callback(progress, stage, message)

    document.status = "processing"
    document.error_message = None
    report(10, "validating", "Validando arquivo e disponibilidade")

    try:
        if not document.file_path or not Path(document.file_path).exists():
            raise ValueError("Arquivo fisico do documento nao foi encontrado")

        report(25, "extracting", "Extraindo texto e estrutura do documento")
        extraction = process_uploaded_path(
            document.file_path,
            document.original_filename or document.filename,
        )
        extracted_text = str(extraction.get("text") or "").strip()
        if not extraction.get("success") or not extracted_text:
            raise ValueError(
                extraction.get("error")
                or "Nao foi possivel extrair texto utilizavel do documento"
            )

        report(55, "analyzing", "Analisando riscos, partes, prazos e valores")
        analysis = lexscan_engine.process_document(extracted_text)
        if not analysis.get("success"):
            raise ValueError(
                analysis.get("error") or "Falha na analise profissional"
            )

        report(85, "persisting", "Consolidando resultados e trilha de auditoria")
        document.status = "completed"
        document.processed_at = datetime.utcnow()
        document.processing_time_ms = int(
            (time.perf_counter() - started_at) * 1000
        )
        document.summary = analysis.get("summary") or ""
        document.parties = analysis.get("parties") or {}
        document.deadlines = analysis.get("deadlines") or []
        document.values = analysis.get("values") or []
        document.analysis = analysis.get("analysis") or ""
        document.content = {
            "extracted_text": extracted_text[:100000],
            "summary": analysis.get("summary") or "",
            "analysis": analysis.get("analysis") or "",
            "document_type": analysis.get("document_type") or "unknown",
            "process_number": analysis.get("process_number") or "",
            "court": analysis.get("court") or "",
            "parties": analysis.get("parties") or {},
            "deadlines": analysis.get("deadlines") or [],
            "values": analysis.get("values") or [],
            "analysis_mode": analysis.get("analysis_mode", "unknown"),
            "ai_analysis_used": bool(analysis.get("ai_analysis_used")),
        }
        document.custom_data = {
            **(document.custom_data or {}),
            "pages": extraction.get("pages", 1),
            "language": "pt-BR",
            "extraction_method": extraction.get("method", "unknown"),
            "text_characters": len(extracted_text),
            "text_truncated": bool(extraction.get("truncated")),
            "max_text_characters": settings.MAX_EXTRACTED_TEXT_CHARS,
            "analysis_mode": analysis.get("analysis_mode", "unknown"),
            "ai_analysis_used": bool(analysis.get("ai_analysis_used")),
            "ai_error": str(analysis.get("ai_error") or "")[:500],
            "progress": 100,
            "processing_stage": "completed",
            "processing_message": "Analise concluida",
        }
        db.commit()
        db.refresh(document)
        if progress_callback:
            progress_callback(100, "completed", "Analise concluida")
        return document
    except Exception as exc:
        document.status = "error"
        document.error_message = str(exc)[:1000]
        document.processed_at = datetime.utcnow()
        document.processing_time_ms = int(
            (time.perf_counter() - started_at) * 1000
        )
        _update_metadata(
            document,
            100,
            "error",
            "A analise falhou e pode ser tentada novamente",
        )
        db.commit()
        if progress_callback:
            progress_callback(
                100,
                "error",
                "A analise falhou e pode ser tentada novamente",
            )
        raise DocumentProcessingError(str(exc)) from exc
