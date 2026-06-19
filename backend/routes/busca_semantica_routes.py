"""Busca semantica local em documentos e fontes juridicas."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import Document, User, get_db
from security import get_current_user
from sovereign_ai.search import sovereign_legal_search

router = APIRouter(prefix="/busca", tags=["Busca Semantica"])


@router.post("/semantic")
async def semantic_search(
    query: str,
    document_type: Optional[str] = None,
    top_k: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Combina embeddings locais, termos juridicos e autoridade da fonte."""
    return await sovereign_legal_search.search(
        db,
        query=query,
        top_k=max(1, min(top_k, 20)),
        legal_area=document_type,
        user_id=int(current_user.user_id),
        include_private=True,
    )


@router.post("/index-document/{document_id}")
async def index_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Indexa o texto extraido de um documento privado do usuario."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == int(current_user.user_id),
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Documento nao encontrado")

    result = await sovereign_legal_search.index_user_document(db, document)
    return {
        "success": True,
        "document_id": document_id,
        "indexed": True,
        **result,
    }
