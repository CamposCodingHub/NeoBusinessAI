"""Secure document upload, extraction, analysis and lifecycle routes."""

import hashlib
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config import settings
from database import Client, Document, Matter, User, get_db_async
from security import UPLOAD_RATE_LIMIT, get_current_user, rate_limit
from security.file_validation import (
    ALLOWED_TYPES,
    sanitize_filename,
    validate_file_signature,
    validate_filename,
)

try:
    from tasks import get_task_status, queue_document_path_processing

    DOCUMENT_QUEUE_AVAILABLE = True
except ImportError:
    DOCUMENT_QUEUE_AVAILABLE = False


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["Documentos"])

UPLOAD_DIR = Path(
    os.getenv(
        "UPLOAD_DIR",
        Path(__file__).resolve().parents[1] / "runtime" / "uploads",
    )
).resolve()
ALLOWED_EXTENSIONS = frozenset(ALLOWED_TYPES)
MAX_FILE_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024
UPLOAD_CHUNK_SIZE = 1024 * 1024
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class SharePortalRequest(BaseModel):
    """Compartilha documento com cliente do portal via custom_data.client_id."""

    client_id: int = Field(..., gt=0)
    matter_id: Optional[int] = Field(None, gt=0)


def _user_id(current_user) -> int:
    return int(current_user.user_id)


def _owned_document(db: Session, document_id: int, user_id: int) -> Optional[Document]:
    return (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == user_id)
        .first()
    )


def _owned_client(db: Session, client_id: int, user_id: int) -> Client:
    client = (
        db.query(Client)
        .filter(Client.id == client_id, Client.user_id == user_id)
        .first()
    )
    if not client:
        raise HTTPException(
            status_code=400,
            detail="client_id inválido ou não pertence ao usuário",
        )
    return client


def _owned_matter(db: Session, matter_id: int, user_id: int) -> Matter:
    matter = (
        db.query(Matter)
        .filter(Matter.id == matter_id, Matter.user_id == user_id)
        .first()
    )
    if not matter:
        raise HTTPException(
            status_code=400,
            detail="matter_id inválido ou não pertence ao usuário",
        )
    return matter


def _processing_fields(document: Document) -> Dict[str, Any]:
    metadata = document.custom_data or {}
    return {
        "progress": int(metadata.get("progress") or 0),
        "processing_stage": metadata.get("processing_stage") or document.status,
        "processing_message": metadata.get("processing_message") or "",
        "task_id": metadata.get("task_id"),
        "error_message": document.error_message,
        "processing_time_ms": document.processing_time_ms,
    }


@router.post("/upload", response_model=dict)
@rate_limit(requests_per_minute=UPLOAD_RATE_LIMIT.requests_per_minute)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_async),
):
    """Stream and validate a document without loading it entirely into memory."""
    original_filename = sanitize_filename(file.filename or "")
    file_ext = validate_filename(original_filename)
    user_id = _user_id(current_user)

    try:
        from services.usage_metering import (
            check_can_upload,
            usage_limit_http_payload,
        )

        gate = check_can_upload(db, user_id)
        if not gate.get("allowed"):
            raise HTTPException(
                status_code=402,
                detail=usage_limit_http_payload(gate),
            )
    except HTTPException:
        raise
    except Exception:
        # Fallback legado se metering falhar
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.documents_limit:
            document_count = (
                db.query(Document).filter(Document.user_id == user_id).count()
            )
            if document_count >= user.documents_limit:
                raise HTTPException(
                    status_code=403,
                    detail="Limite de documentos do plano atingido",
                )

    safe_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / safe_filename
    partial_path = file_path.with_suffix(f"{file_path.suffix}.part")
    file_size = 0
    header = bytearray()
    digest = hashlib.sha256()
    mime_type = ""

    try:
        async with aiofiles.open(partial_path, "wb") as destination:
            while chunk := await file.read(UPLOAD_CHUNK_SIZE):
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "Arquivo muito grande. Maximo: "
                            f"{settings.MAX_FILE_SIZE_MB}MB"
                        ),
                    )
                if len(header) < 8192:
                    header.extend(chunk[: 8192 - len(header)])
                digest.update(chunk)
                await destination.write(chunk)

        if not file_size:
            raise HTTPException(status_code=400, detail="Arquivo vazio")

        mime_type = validate_file_signature(
            original_filename,
            bytes(header),
            str(partial_path),
        )
        os.replace(partial_path, file_path)

        document = Document(
            user_id=user_id,
            filename=original_filename,
            original_filename=original_filename,
            file_path=str(file_path),
            file_size=file_size,
            file_type=file_ext,
            title=(title or original_filename)[:255],
            status="uploaded",
            custom_data={
                "sha256": digest.hexdigest(),
                "mime_type": mime_type,
                "upload_mode": "streamed",
            },
            created_at=datetime.utcnow(),
        )
        db.add(document)
        db.commit()
        db.refresh(document)
    except HTTPException:
        db.rollback()
        partial_path.unlink(missing_ok=True)
        file_path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        db.rollback()
        partial_path.unlink(missing_ok=True)
        file_path.unlink(missing_ok=True)
        logger.exception("Falha ao persistir upload")
        raise HTTPException(
            status_code=500,
            detail="Nao foi possivel armazenar o documento com seguranca",
        ) from exc
    finally:
        await file.close()

    logger.info(
        "Documento upload: %s (%s bytes, user=%s)",
        original_filename,
        file_size,
        user_id,
    )
    return {
        "message": "Documento uploadado com sucesso",
        "document_id": document.id,
        "filename": document.filename,
        "status": document.status,
        "file_size": file_size,
        "mime_type": mime_type,
        "sha256": digest.hexdigest(),
    }


@router.get("/", response_model=Dict[str, Any])
@router.get("", response_model=Dict[str, Any])
async def list_documents(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_async),
):
    query = db.query(Document).filter(Document.user_id == _user_id(current_user))
    if status:
        query = query.filter(Document.status == status)

    total = query.count()
    documents = (
        query.order_by(Document.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return {
        "documents": [
            {
                "id": document.id,
                "filename": document.filename,
                "title": document.title,
                "file_type": document.file_type,
                "file_size": document.file_size,
                "status": document.status,
                **_processing_fields(document),
                "created_at": (
                    document.created_at.isoformat()
                    if document.created_at
                    else None
                ),
                "processed_at": (
                    document.processed_at.isoformat()
                    if document.processed_at
                    else None
                ),
            }
            for document in documents
        ],
        "pagination": {
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit,
            "limit": limit,
        },
    }


@router.get("/search", response_model=Dict[str, Any])
async def search_documents(
    q: str = Query(..., min_length=1, max_length=300, description="Termo de busca"),
    limit: int = Query(10, ge=1, le=50),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_async),
):
    """Busca autenticada nos documentos do usuario atual."""
    from services.internal_document_search import search_user_documents

    query = (q or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Parametro q e obrigatorio")

    results = search_user_documents(
        db,
        _user_id(current_user),
        query,
        top_k=limit,
    )
    return {
        "query": query,
        "count": len(results),
        "results": results,
    }


@router.get("/stats", response_model=dict)
async def get_document_stats(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_async),
):
    documents = (
        db.query(Document)
        .filter(Document.user_id == _user_id(current_user))
        .all()
    )
    by_status: Dict[str, int] = {}
    by_type: Dict[str, int] = {}
    for document in documents:
        by_status[document.status] = by_status.get(document.status, 0) + 1
        by_type[document.file_type] = by_type.get(document.file_type, 0) + 1
    return {
        "total_documents": len(documents),
        "by_status": by_status,
        "by_type": by_type,
        "total_size": sum(document.file_size or 0 for document in documents),
        "limits": {
            "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
            "max_pdf_pages": settings.MAX_PDF_PAGES,
            "max_ocr_pages": settings.MAX_OCR_PAGES,
        },
    }


@router.get("/{document_id}", response_model=dict)
async def get_document(
    document_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_async),
):
    document = _owned_document(db, document_id, _user_id(current_user))
    if not document:
        raise HTTPException(status_code=404, detail="Documento nao encontrado")

    return {
        "id": document.id,
        "filename": document.filename,
        "title": document.title,
        "file_type": document.file_type,
        "file_size": document.file_size,
        "status": document.status,
        **_processing_fields(document),
        "content": document.content,
        "metadata": document.custom_data,
        "summary": document.summary,
        "analysis": document.analysis,
        "error_message": document.error_message,
        "created_at": (
            document.created_at.isoformat() if document.created_at else None
        ),
        "processed_at": (
            document.processed_at.isoformat() if document.processed_at else None
        ),
    }


@router.delete("/{document_id}", response_model=dict)
async def delete_document(
    document_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_async),
):
    document = _owned_document(db, document_id, _user_id(current_user))
    if not document:
        raise HTTPException(status_code=404, detail="Documento nao encontrado")
    if document.status in {"queued", "processing"}:
        raise HTTPException(
            status_code=409,
            detail="Aguarde a analise terminar antes de excluir o documento",
        )

    file_path = Path(document.file_path) if document.file_path else None
    db.delete(document)
    db.commit()
    if file_path:
        file_path.unlink(missing_ok=True)
    return {"message": "Documento deletado com sucesso"}


@router.post("/{document_id}/share-portal", response_model=dict)
async def share_document_with_portal(
    document_id: int,
    body: SharePortalRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_async),
):
    """
    Marca documento para o portal do cliente (custom_data.client_id).
    IDOR-safe: documento e cliente devem pertencer ao usuário autenticado.
    Opcionalmente vincula matter_id (também owned).
    """
    user_id = _user_id(current_user)
    document = _owned_document(db, document_id, user_id)
    if not document:
        raise HTTPException(status_code=404, detail="Documento nao encontrado")

    client = _owned_client(db, body.client_id, user_id)

    if body.matter_id is not None:
        matter = _owned_matter(db, body.matter_id, user_id)
        if matter.client_id is not None and matter.client_id != client.id:
            raise HTTPException(
                status_code=400,
                detail="matter_id não pertence ao client_id informado",
            )
        document.matter_id = matter.id

    metadata = dict(document.custom_data or {})
    metadata["client_id"] = int(client.id)
    if body.matter_id is not None:
        metadata["matter_id"] = int(body.matter_id)
    document.custom_data = metadata
    db.commit()
    db.refresh(document)

    return {
        "success": True,
        "message": "Documento compartilhado com o portal do cliente",
        "document_id": document.id,
        "client_id": client.id,
        "matter_id": document.matter_id,
        "custom_data": {
            "client_id": metadata.get("client_id"),
            "matter_id": metadata.get("matter_id"),
        },
    }


@router.get("/{document_id}/processing-status", response_model=dict)
async def document_processing_status(
    document_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_async),
):
    document = _owned_document(db, document_id, _user_id(current_user))
    if not document:
        raise HTTPException(status_code=404, detail="Documento nao encontrado")

    fields = _processing_fields(document)
    task_status = None
    if fields["task_id"] and DOCUMENT_QUEUE_AVAILABLE:
        try:
            task_status = get_task_status(str(fields["task_id"]))
        except Exception as exc:
            task_status = {
                "status": "UNKNOWN",
                "ready": False,
                "error": str(exc),
            }

    if (
        task_status
        and task_status.get("status") == "FAILURE"
        and document.status in {"queued", "processing"}
    ):
        document.status = "error"
        document.error_message = str(
            task_status.get("error") or "Worker encerrou a tarefa com erro"
        )[:1000]
        document.custom_data = {
            **(document.custom_data or {}),
            "progress": 100,
            "processing_stage": "error",
            "processing_message": "A tarefa falhou e pode ser tentada novamente",
        }
        db.commit()
        db.refresh(document)
        fields = _processing_fields(document)

    return {
        "document_id": document.id,
        "status": document.status,
        **fields,
        "task": task_status,
        "completed": document.status == "completed",
        "failed": document.status == "error",
    }


@router.post("/{document_id}/analyze", response_model=dict, status_code=202)
async def analyze_document(
    document_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_async),
):
    user_id = _user_id(current_user)
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == user_id)
        .with_for_update()
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Documento nao encontrado")
    if document.status in {"queued", "processing"}:
        raise HTTPException(status_code=409, detail="Documento ja esta em processamento")
    if not DOCUMENT_QUEUE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Fila de processamento temporariamente indisponivel",
        )

    document.status = "queued"
    document.error_message = None
    document.custom_data = {
        **(document.custom_data or {}),
        "progress": 5,
        "processing_stage": "queued",
        "processing_message": "Documento aguardando worker disponivel",
    }
    db.commit()

    try:
        task_id = queue_document_path_processing(document.id, user_id)
        document.custom_data = {
            **(document.custom_data or {}),
            "task_id": task_id,
        }
        db.commit()
    except Exception as exc:
        document.status = "uploaded"
        document.custom_data = {
            **(document.custom_data or {}),
            "progress": 0,
            "processing_stage": "queue_unavailable",
            "processing_message": "Nao foi possivel enviar para a fila",
        }
        db.commit()
        raise HTTPException(
            status_code=503,
            detail="Nao foi possivel enviar o documento para processamento",
        ) from exc

    return {
        "message": "Documento enviado para analise",
        "document_id": document.id,
        "status": document.status,
        "task_id": task_id,
        "progress": 5,
        "check_status_url": f"/documents/{document.id}/processing-status",
    }
