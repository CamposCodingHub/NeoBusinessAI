"""
Rotas de Geração de Peças Jurídicas
=======================================
Geração de documentos jurídicos com IA.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
import logging

from database import get_db_async, User, Document, LegalDocument
from security import get_current_user, rate_limit
from middleware.tenant_middleware import get_tenant_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/legal", tags=["Jurídico"])


# Schemas Pydantic
from pydantic import BaseModel, Field, field_validator


class GeneratePieceRequest(BaseModel):
    """Schema para geração de peças jurídicas"""
    document_id: Optional[int] = Field(None, description="ID do documento base")
    piece_type: str = Field(..., description="Tipo de peça (petição, contestação, recurso, etc)")
    jurisdiction: str = Field(..., description="Jurisdição (cível, trabalhista, tributário, etc)")
    parties: str = Field(..., description="Partes envolvidas")
    facts: str = Field(..., description="Fatos relevantes")
    requests: str = Field(..., description="Pedidos")
    additional_context: Optional[str] = Field(None, description="Contexto adicional")

    @field_validator("document_id", mode="before")
    @classmethod
    def normalize_empty_document_id(cls, value):
        if value in ("", None):
            return None
        return value
    
    @field_validator("piece_type")
    @classmethod
    def validate_piece_type(cls, value: str) -> str:
        valid_types = [
            'peticao_inicial', 'contestacao', 'recurso_apelacao',
            'embargos_declaracao', 'agravo', 'habeas_corpus',
            'acao_cautelar', 'contrato', 'parecer'
        ]
        if value not in valid_types:
            raise ValueError(f"Tipo inválido. Use: {', '.join(valid_types)}")
        return value


@router.post("/generate-piece", response_model=dict)
async def generate_legal_piece(
    request_data: GeneratePieceRequest,
    tenant_db = Depends(get_tenant_db),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db_async)
):
    """
    Gera peça jurídica com IA
    
    - **document_id**: Documento base (opcional)
    - **piece_type**: Tipo de peça
    - **jurisdiction**: Jurisdição
    - **parties**: Partes envolvidas
    - **facts**: Fatos relevantes
    - **requests**: Pedidos
    """
    # Se documento informado, verificar que pertence ao usuário
    if request_data.document_id:
        document = tenant_db.get_by_id(Document, request_data.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    # Criar registro da peça jurídica
    legal_doc = LegalDocument(
        user_id=int(current_user.user_id),
        document_id=request_data.document_id,
        piece_type=request_data.piece_type,
        jurisdiction=request_data.jurisdiction,
        parties=request_data.parties,
        facts=request_data.facts,
        requests=request_data.requests,
        additional_context=request_data.additional_context,
        status="generating",
        created_at=datetime.utcnow()
    )
    
    db.add(legal_doc)
    db.commit()
    db.refresh(legal_doc)
    
    # TODO: Integrar com motor de IA para geração real
    # Por enquanto, simula geração
    legal_doc.status = "completed"
    legal_doc.content = f"""
# {request_data.piece_type.replace('_', ' ').title()}

**Jurisdição:** {request_data.jurisdiction}

**Partes:**
{request_data.parties}

**Fatos:**
{request_data.facts}

**Pedidos:**
{request_data.requests}

---

**Documento gerado em {datetime.utcnow().strftime('%d/%m/%Y às %H:%M')}**

*Este documento foi gerado pela NeoBusiness AI e deve ser revisado por um advogado antes de ser protocolado.*
"""
    legal_doc.generated_at = datetime.utcnow()
    db.commit()
    
    logger.info(f"Peça jurídica gerada: {request_data.piece_type} (User: {current_user.user_id})")
    
    return {
        "message": "Peça jurídica gerada com sucesso",
        "document_id": legal_doc.id,
        "piece_type": legal_doc.piece_type,
        "status": legal_doc.status,
        "content": legal_doc.content
    }


@router.get("/pieces", response_model=List[dict])
async def list_legal_pieces(
    tenant_db = Depends(get_tenant_db),
    current_user = Depends(get_current_user)
):
    """
    Lista todas as peças jurídicas do usuário
    """
    pieces = tenant_db.filter_by_tenant(LegalDocument).order_by(LegalDocument.created_at.desc()).all()
    
    return [
        {
            "id": piece.id,
            "piece_type": piece.piece_type,
            "jurisdiction": piece.jurisdiction,
            "status": piece.status,
            "content": piece.content,
            "created_at": piece.created_at.isoformat() if piece.created_at else None,
            "generated_at": piece.generated_at.isoformat() if piece.generated_at else None
        }
        for piece in pieces
    ]


@router.get("/pieces/{piece_id}", response_model=dict)
async def get_legal_piece(
    piece_id: int,
    tenant_db = Depends(get_tenant_db),
    current_user = Depends(get_current_user)
):
    """
    Obtém uma peça jurídica específica
    """
    piece = tenant_db.get_by_id(LegalDocument, piece_id)
    
    if not piece:
        raise HTTPException(status_code=404, detail="Peça não encontrada")
    
    return {
        "id": piece.id,
        "piece_type": piece.piece_type,
        "jurisdiction": piece.jurisdiction,
        "parties": piece.parties,
        "facts": piece.facts,
        "requests": piece.requests,
        "additional_context": piece.additional_context,
        "content": piece.content,
        "status": piece.status,
        "created_at": piece.created_at.isoformat() if piece.created_at else None,
        "generated_at": piece.generated_at.isoformat() if piece.generated_at else None
    }


@router.delete("/pieces/{piece_id}", response_model=dict)
async def delete_legal_piece(
    piece_id: int,
    tenant_db = Depends(get_tenant_db),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db_async)
):
    """
    Deleta uma peça jurídica
    """
    piece = tenant_db.get_by_id(LegalDocument, piece_id)
    
    if not piece:
        raise HTTPException(status_code=404, detail="Peça não encontrada")
    
    db.delete(piece)
    db.commit()
    
    logger.info(f"Peça jurídica deletada: {piece.piece_type} (User: {current_user.user_id})")
    
    return {"message": "Peça deletada com sucesso"}


@router.get("/templates", response_model=List[dict])
async def list_templates(
    current_user = Depends(get_current_user)
):
    """
    Lista templates disponíveis para geração
    """
    templates = [
        {
            "id": "peticao_inicial",
            "name": "Petição Inicial",
            "description": "Petição inicial para ação judicial",
            "jurisdictions": ["civel", "trabalhista", "tributario"]
        },
        {
            "id": "contestacao",
            "name": "Contestação",
            "description": "Contestação de ação judicial",
            "jurisdictions": ["civel", "trabalhista"]
        },
        {
            "id": "recurso_apelacao",
            "name": "Recurso de Apelação",
            "description": "Recurso contra sentença",
            "jurisdictions": ["civel", "trabalhista", "tributario"]
        },
        {
            "id": "habeas_corpus",
            "name": "Habeas Corpus",
            "description": "Medida cautelar de liberdade",
            "jurisdictions": ["civel", "criminal"]
        },
        {
            "id": "contrato",
            "name": "Contrato",
            "description": "Contrato jurídico",
            "jurisdictions": ["civel", "empresarial"]
        },
        {
            "id": "parecer",
            "name": "Parecer Jurídico",
            "description": "Parecer sobre questão jurídica",
            "jurisdictions": ["civel", "trabalhista", "tributario", "empresarial"]
        }
    ]
    
    return templates
