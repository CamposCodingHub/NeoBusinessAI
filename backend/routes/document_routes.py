"""
Rotas de Documentos
===================
Upload, processamento, OCR e gerenciamento de documentos.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import os
import uuid
from typing import List, Optional, Dict, Any
import aiofiles

from database import get_db_async, User, Document
from security import (
    get_current_user, require_role, Role,
    rate_limit, UPLOAD_RATE_LIMIT,
    validate_schema, DocumentUploadSchema
)
from middleware.tenant_middleware import get_tenant_db, check_resource_ownership

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["Documentos"])
security = HTTPBearer()

# Configurações
UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".rtf"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Criar diretório de uploads
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=dict)
@rate_limit(requests_per_minute=UPLOAD_RATE_LIMIT.requests_per_minute)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db_async)
):
    """
    Upload de documento com processamento
    
    - **file**: Arquivo (PDF, DOC, DOCX, TXT, RTF)
    - **title**: Título opcional do documento
    """
    # Validar extensão
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extensão não permitida. Use: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Validar tamanho
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Arquivo muito grande. Máximo: 50MB"
        )
    
    # Gerar nome único
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    # Salvar arquivo
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(file_content)
    
    # Criar registro no banco
    document = Document(
        user_id=int(current_user.user_id),
        filename=file.filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=len(file_content),
        file_type=file_ext,
        title=title or file.filename,
        status="uploaded",
        created_at=datetime.utcnow()
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    logger.info(f"Documento upload: {file.filename} (User: {current_user.user_id})")
    
    return {
        "message": "Documento uploadado com sucesso",
        "document_id": document.id,
        "filename": document.filename,
        "status": document.status
    }


@router.get("/", response_model=Dict[str, Any])
@router.get("", response_model=Dict[str, Any])
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    tenant_db = Depends(get_tenant_db),
    current_user = Depends(get_current_user)
):
    """
    Lista todos os documentos do usuário (paginado)
    """
    query = tenant_db.filter_by_tenant(Document)
    
    if status:
        query = query.filter(Document.status == status)
    
    # Total count for pagination
    total = query.count()
    
    # Apply pagination
    documents = query.order_by(Document.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    return {
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "title": doc.title,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "status": doc.status,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "processed_at": doc.processed_at.isoformat() if doc.processed_at else None
            }
            for doc in documents
        ],
        "pagination": {
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit,
            "limit": limit
        }
    }


@router.get("/{document_id}", response_model=dict)
async def get_document(
    document_id: int,
    tenant_db = Depends(get_tenant_db),
    current_user = Depends(get_current_user)
):
    """
    Obtém detalhes de um documento específico
    """
    document = tenant_db.get_by_id(Document, document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    return {
        "id": document.id,
        "filename": document.filename,
        "title": document.title,
        "file_type": document.file_type,
        "file_size": document.file_size,
        "status": document.status,
        "content": document.content,
        "metadata": document.metadata,
        "created_at": document.created_at.isoformat() if document.created_at else None,
        "processed_at": document.processed_at.isoformat() if document.processed_at else None
    }


@router.delete("/{document_id}", response_model=dict)
async def delete_document(
    document_id: int,
    tenant_db = Depends(get_tenant_db),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db_async)
):
    """
    Deleta um documento
    """
    document = tenant_db.get_by_id(Document, document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    # Deletar arquivo físico
    if document.file_path and os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # Deletar registro
    db.delete(document)
    db.commit()
    
    logger.info(f"Documento deletado: {document.filename} (User: {current_user.user_id})")
    
    return {"message": "Documento deletado com sucesso"}


@router.post("/{document_id}/analyze", response_model=dict)
async def analyze_document(
    document_id: int,
    tenant_db = Depends(get_tenant_db),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db_async)
):
    """
    Inicia análise de documento com IA
    """
    document = tenant_db.get_by_id(Document, document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    # Atualizar status
    document.status = "processing"
    document.processed_at = datetime.utcnow()
    db.commit()
    
    # TODO: Integrar com motor de IA para análise real
    # Por enquanto, simula análise
    document.status = "completed"
    document.content = {
        "summary": "Documento analisado com sucesso",
        "key_points": ["Ponto 1", "Ponto 2", "Ponto 3"],
        "entities": ["Entidade A", "Entidade B"]
    }
    document.metadata = {
        "pages": 10,
        "language": "pt-BR",
        "confidence": 0.95
    }
    db.commit()
    
    logger.info(f"Documento analisado: {document.filename} (User: {current_user.user_id})")
    
    return {
        "message": "Análise concluída",
        "document_id": document.id,
        "status": document.status,
        "content": document.content
    }


@router.get("/stats", response_model=dict)
async def get_document_stats(
    tenant_db = Depends(get_tenant_db),
    current_user = Depends(get_current_user)
):
    """
    Estatísticas de documentos do usuário
    """
    documents = tenant_db.filter_by_tenant(Document).all()
    
    total = len(documents)
    by_status = {}
    by_type = {}
    
    for doc in documents:
        by_status[doc.status] = by_status.get(doc.status, 0) + 1
        by_type[doc.file_type] = by_type.get(doc.file_type, 0) + 1
    
    return {
        "total_documents": total,
        "by_status": by_status,
        "by_type": by_type,
        "total_size": sum(doc.file_size for doc in documents)
    }
