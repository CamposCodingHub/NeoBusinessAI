"""Pesquisa jurisprudencial sobre a base soberana local."""

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from security import get_current_user
from sovereign_ai.search import sovereign_legal_search

router = APIRouter(prefix="/jurisprudencia", tags=["Pesquisa Jurisprudencial"])


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=4000)
    court: Optional[str] = None
    subject: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    page: int = Field(1, ge=1)


@router.post("/search")
async def search_jurisprudencia(
    request: SearchRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Pesquisa decisoes e precedentes que ja foram coletados e indexados."""
    search = await sovereign_legal_search.search(
        db,
        query=request.query,
        top_k=10,
        legal_area=request.subject,
        court=request.court,
        user_id=int(current_user.user_id),
        include_private=False,
    )
    return {
        "query": request.query,
        "results": search["results"],
        "total": len(search["results"]),
        "hybrid_search": True,
        "embedding_model": search["embedding_model"],
        "ai_summary": None,
    }


@router.get("/courts")
async def list_available_courts():
    return {
        "courts": [
            {"code": "STF", "name": "Supremo Tribunal Federal", "status": "indexable"},
            {"code": "STJ", "name": "Superior Tribunal de Justica", "status": "indexable"},
            {"code": "TST", "name": "Tribunal Superior do Trabalho", "status": "indexable"},
            {"code": "TJSP", "name": "Tribunal de Justica de SP", "status": "planned"},
            {"code": "TJRJ", "name": "Tribunal de Justica do RJ", "status": "planned"},
        ]
    }


@router.post("/analyze")
async def analyze_case_with_precedents(
    case_description: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    search = await sovereign_legal_search.search(
        db,
        query=case_description,
        top_k=8,
        user_id=int(current_user.user_id),
        include_private=False,
    )
    return {
        "analysis": "Precedentes recuperados para analise pelo copiloto.",
        "suggested_precedents": search["results"],
        "confidence": (
            search["results"][0]["score"] if search["results"] else 0
        ),
        "legal_basis": [
            result["citation"] for result in search["results"]
        ],
    }
