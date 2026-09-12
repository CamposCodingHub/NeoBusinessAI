"""
Rotas de Geração de Peças Jurídicas
=======================================
Geração de documentos jurídicos com IA + stub de contrato de honorários.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Literal, Optional
import logging

from database import Client, Matter, User, Document, LegalDocument, get_db, get_db_async
from security import get_current_user, rate_limit
from middleware.tenant_middleware import get_tenant_db
from security.xss_protection import sanitize_plain_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/legal", tags=["Jurídico"])


# Schemas Pydantic
from pydantic import BaseModel, Field, field_validator


FEE_TYPE_LABELS = {
    "hourly": "Honorários por hora",
    "flat": "Honorários fixos (valor fechado)",
    "contingency": "Honorários de êxito (ad exitum)",
}


class EngagementLetterRequest(BaseModel):
    """Body para rascunho de contrato de honorários (sem LLM)."""

    client_id: int = Field(..., description="Cliente contratante (ownership obrigatório)")
    matter_id: Optional[int] = Field(None, description="Caso/matter opcional")
    fee_type: Literal["hourly", "flat", "contingency"] = Field(
        ..., description="Modalidade de honorários"
    )
    amount: Optional[float] = Field(None, ge=0, description="Valor fixo ou % / base de êxito")
    hourly_rate: Optional[float] = Field(None, ge=0, description="Taxa horária (fee_type=hourly)")
    scope: str = Field(..., min_length=1, description="Objeto / escopo dos serviços")

    @field_validator("scope")
    @classmethod
    def sanitize_scope(cls, value: str) -> str:
        cleaned = sanitize_plain_text(value).strip()
        if not cleaned:
            raise ValueError("scope é obrigatório")
        return cleaned


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


def _format_brl(value: Optional[float]) -> str:
    if value is None:
        return "[a definir]"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fee_clause(fee_type: str, amount: Optional[float], hourly_rate: Optional[float]) -> str:
    if fee_type == "hourly":
        return (
            f"Os honorários serão cobrados por hora trabalhada, à razão de "
            f"**{_format_brl(hourly_rate)}** por hora, conforme relatório de tempos."
        )
    if fee_type == "flat":
        return (
            f"Os honorários são fixos no valor total de **{_format_brl(amount)}**, "
            f"pelos serviços descritos no objeto deste contrato."
        )
    # contingency
    if amount is not None and amount <= 100:
        return (
            f"Os honorários de êxito equivalem a **{amount:.2f}%** do proveito "
            f"econômico obtido em favor do CONTRATANTE, exigíveis somente em caso de êxito."
        )
    return (
        f"Os honorários de êxito serão de **{_format_brl(amount)}**, "
        f"exigíveis somente em caso de êxito na demanda/objeto contratado."
    )


def build_engagement_letter_markdown(
    *,
    client_name: str,
    attorney_name: str,
    scope: str,
    fee_type: str,
    amount: Optional[float],
    hourly_rate: Optional[float],
    matter_title: Optional[str] = None,
) -> str:
    """Template Python de contrato de honorários (rascunho, sem LLM)."""
    today = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    fee_label = FEE_TYPE_LABELS.get(fee_type, fee_type)
    matter_line = (
        f"\n**Caso / Matter:** {matter_title}\n" if matter_title else "\n"
    )
    return f"""# CONTRATO DE HONORÁRIOS ADVOCATÍCIOS

**Data do rascunho:** {today}

## Partes

**CONTRATANTE:** {client_name}

**CONTRATADO:** {attorney_name} (ou escritório por ele representado)
{matter_line}
## Objeto / Escopo

{scope}

## Modalidade de Honorários

**Tipo:** {fee_label}

{_fee_clause(fee_type, amount, hourly_rate)}

## Disposições Gerais (stub)

1. O presente instrumento é um **rascunho gerado automaticamente** e não produz
   efeitos jurídicos até revisão, complementação e assinatura das partes.
2. Despesas processuais, custas e encargos de terceiros correrão por conta do
   CONTRATANTE, salvo pacto em contrário.
3. O CONTRATADO atuará com independência técnica, observados o Estatuto da
   Advocacia e o Código de Ética da OAB.

## Assinaturas

_______________________________  
CONTRATANTE — {client_name}

_______________________________  
CONTRATADO — {attorney_name}

---
*Documento gerado pela NeoBusiness AI — revisar com advogado antes de uso.*
"""


@router.post("/engagement-letter", response_model=dict)
@rate_limit(requests_per_minute=30)
async def create_engagement_letter_draft(
    payload: EngagementLetterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Gera rascunho markdown de contrato de honorários (template Python, sem LLM).

    Não persiste Document — retorna apenas o draft para revisão humana.
    """
    user_id = int(current_user.id)
    client = (
        db.query(Client)
        .filter(Client.id == payload.client_id, Client.user_id == user_id)
        .first()
    )
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado",
        )

    matter_title: Optional[str] = None
    if payload.matter_id is not None:
        matter = (
            db.query(Matter)
            .filter(Matter.id == payload.matter_id, Matter.user_id == user_id)
            .first()
        )
        if not matter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Matter não encontrado",
            )
        if matter.client_id is not None and matter.client_id != client.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="matter_id não pertence ao client_id informado",
            )
        matter_title = matter.title

    attorney = db.query(User).filter(User.id == user_id).first()
    attorney_name = (attorney.name if attorney and attorney.name else None) or (
        attorney.email if attorney else f"Usuário {user_id}"
    )

    warnings: List[str] = ["revisar com advogado"]
    if payload.fee_type == "hourly" and payload.hourly_rate is None:
        warnings.append("hourly_rate não informado — preencher taxa horária antes de assinar")
    if payload.fee_type in ("flat", "contingency") and payload.amount is None:
        warnings.append("amount não informado — preencher valor/percentual antes de assinar")

    draft_markdown = build_engagement_letter_markdown(
        client_name=client.name,
        attorney_name=attorney_name,
        scope=payload.scope,
        fee_type=payload.fee_type,
        amount=payload.amount,
        hourly_rate=payload.hourly_rate,
        matter_title=matter_title,
    )

    logger.info(
        "Engagement letter draft gerado client_id=%s fee_type=%s user=%s",
        payload.client_id,
        payload.fee_type,
        user_id,
    )

    return {
        "draft_markdown": draft_markdown,
        "warnings": warnings,
        "client_id": client.id,
        "matter_id": payload.matter_id,
        "fee_type": payload.fee_type,
    }


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
