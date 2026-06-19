"""Rotas operacionais da infraestrutura soberana de IA."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import (
    AIInferenceEvent,
    AIResearchJob,
    Document,
    FineTuningExample,
    User,
    get_db,
)
from security import get_current_user
from sovereign_ai.gateway import sovereign_ai_gateway
from sovereign_ai.search import sovereign_legal_search
from sovereign_ai.evaluation import legal_model_evaluator
from sovereign_ai.training import training_dataset_service
from services.official_realtime_research_service import (
    official_realtime_research,
)

router = APIRouter(prefix="/ai/sovereign", tags=["Sovereign AI"])


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=4000)
    top_k: int = Field(6, ge=1, le=20)
    legal_area: Optional[str] = None
    court: Optional[str] = None
    include_private: bool = True


class RealtimeSearchRequest(BaseModel):
    query: str = Field(min_length=4, max_length=4000)
    max_results: int = Field(5, ge=1, le=10)


class BootstrapRequest(BaseModel):
    source_codes: List[str] = Field(
        default_factory=lambda: ["CF88", "CP", "CPP", "CC", "CPC"]
    )
    force: bool = False
    generate_embeddings: bool = False


class TrainingExampleRequest(BaseModel):
    source_type: str = Field(min_length=2, max_length=80)
    domain: str = Field(min_length=2, max_length=120)
    instruction: str = Field(min_length=10, max_length=12000)
    input_text: str = Field("", max_length=40000)
    output_text: str = Field(min_length=20, max_length=40000)
    citations: List[dict | str] = Field(default_factory=list)


class TrainingReviewRequest(BaseModel):
    approved: bool
    quality_score: float = Field(ge=0, le=1)
    notes: str = Field("", max_length=4000)


class EvaluationRequest(BaseModel):
    candidate_model: Optional[str] = None


class ResearchJobRequest(BaseModel):
    query: str = Field(min_length=20, max_length=12000)
    document_context: str = Field("", max_length=40000)
    conversation_id: str = Field("research", max_length=64)
    jurisdiction: str = Field("Brasil - federal", max_length=160)
    legal_area: Optional[str] = Field(None, max_length=120)


@router.get("/status")
async def sovereign_ai_status(db: Session = Depends(get_db)):
    return {
        **(await sovereign_ai_gateway.health()),
        "knowledge": sovereign_legal_search.stats(db),
    }


@router.post("/search")
async def sovereign_search(
    request: SearchRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await sovereign_legal_search.search(
        db,
        query=request.query,
        top_k=request.top_k,
        legal_area=request.legal_area,
        court=request.court,
        user_id=int(current_user.user_id),
        include_private=request.include_private,
    )


@router.post("/realtime-search")
async def realtime_official_search(
    request: RealtimeSearchRequest,
    current_user=Depends(get_current_user),
):
    del current_user
    return await asyncio.to_thread(
        official_realtime_research.search,
        request.query,
        request.max_results,
    )


@router.post("/knowledge/bootstrap")
async def bootstrap_knowledge(
    request: BootstrapRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    del current_user
    results = await sovereign_legal_search.bootstrap_official_sources(
        db,
        source_codes=request.source_codes,
        force=request.force,
        generate_embeddings=request.generate_embeddings,
    )
    return {
        "success": not any("error" in item for item in results),
        "results": results,
        "stats": sovereign_legal_search.stats(db),
    }


@router.post("/knowledge/documents/{document_id}")
async def index_user_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == int(current_user.user_id),
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Documento nao encontrado")
    result = await sovereign_legal_search.index_user_document(db, document)
    return {"success": True, **result}


@router.get("/inference-events")
async def inference_events(
    hours: int = Query(24, ge=1, le=720),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    del current_user
    since = datetime.utcnow() - timedelta(hours=hours)
    events = (
        db.query(AIInferenceEvent)
        .filter(AIInferenceEvent.created_at >= since)
        .order_by(AIInferenceEvent.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "events": [
            {
                "request_id": event.request_id,
                "provider": event.provider,
                "route": event.route,
                "requested_model": event.requested_model,
                "actual_model": event.actual_model,
                "status": event.status,
                "latency_ms": event.latency_ms,
                "tokens": event.total_tokens,
                "fallback_used": event.fallback_used,
                "error_code": event.error_code,
                "created_at": event.created_at.isoformat(),
            }
            for event in events
        ]
    }


@router.post("/training/examples")
async def create_training_example(
    request: TrainingExampleRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    example = training_dataset_service.create_example(
        db,
        source_type=request.source_type,
        domain=request.domain,
        instruction=request.instruction,
        input_text=request.input_text,
        output_text=request.output_text,
        citations=request.citations,
        custom_data={"submitted_by": int(current_user.user_id)},
    )
    return {
        "id": example.id,
        "review_status": example.review_status,
        "dataset_split": example.dataset_split,
    }


@router.patch("/training/examples/{example_id}/review")
async def review_training_example(
    example_id: int,
    request: TrainingReviewRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    reviewer = db.query(User).filter(
        User.id == int(current_user.user_id)
    ).first()
    if not reviewer or reviewer.role not in {"admin", "premium", "enterprise"}:
        raise HTTPException(
            status_code=403,
            detail="Revisao exige perfil profissional autorizado",
        )
    try:
        example = training_dataset_service.review_example(
            db,
            example_id=example_id,
            reviewer_id=reviewer.id,
            approved=request.approved,
            quality_score=request.quality_score,
            notes=request.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "id": example.id,
        "review_status": example.review_status,
        "quality_score": example.quality_score,
    }


@router.get("/training/stats")
async def training_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    del current_user
    return training_dataset_service.stats(db)


@router.post("/training/export")
async def export_training_dataset(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    reviewer = db.query(User).filter(
        User.id == int(current_user.user_id)
    ).first()
    if not reviewer or reviewer.role not in {"admin", "enterprise"}:
        raise HTTPException(status_code=403, detail="Exportacao restrita")
    output_dir = (
        Path(__file__).resolve().parent.parent
        / "runtime"
        / "training"
        / "legal-v1"
    )
    return training_dataset_service.export_jsonl(
        db,
        output_dir=output_dir,
    )


@router.post("/evaluations/run")
async def run_evaluation(
    request: EvaluationRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    del current_user
    from config import settings

    dataset_path = (
        Path(__file__).resolve().parent.parent
        / "evals"
        / "legal_sovereign_v1.json"
    )
    return await legal_model_evaluator.run(
        db,
        dataset_path=dataset_path,
        candidate_model=(
            request.candidate_model or settings.LOCAL_AI_BALANCED_MODEL
        ),
    )


@router.post("/research-jobs", status_code=202)
async def create_research_job(
    request: ResearchJobRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        from tasks import queue_deep_research
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="Fila de pesquisa indisponivel",
        ) from exc

    user_id = int(current_user.user_id)
    job = AIResearchJob(
        user_id=user_id,
        conversation_id=request.conversation_id,
        query=request.query,
        document_context=request.document_context,
        jurisdiction=request.jurisdiction,
        legal_area=request.legal_area,
        status="queued",
        progress=5,
        stage="queued",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    try:
        job.task_id = queue_deep_research(job.id, user_id)
        db.commit()
    except Exception as exc:
        job.status = "error"
        job.stage = "queue_error"
        job.progress = 100
        job.error_message = str(exc)[:1000]
        db.commit()
        raise HTTPException(
            status_code=503,
            detail="Nao foi possivel enfileirar a pesquisa",
        ) from exc
    return {
        "job_id": job.id,
        "task_id": job.task_id,
        "status": job.status,
        "progress": job.progress,
    }


@router.get("/research-jobs/{job_id}")
async def get_research_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    job = db.query(AIResearchJob).filter(
        AIResearchJob.id == job_id,
        AIResearchJob.user_id == int(current_user.user_id),
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Pesquisa nao encontrada")
    return {
        "job_id": job.id,
        "task_id": job.task_id,
        "status": job.status,
        "progress": job.progress,
        "stage": job.stage,
        "result": job.result if job.status == "completed" else None,
        "metadata": job.result_metadata if job.status == "completed" else {},
        "error": job.error_message if job.status == "error" else None,
        "provider": job.provider,
        "model": job.actual_model,
        "created_at": job.created_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": (
            job.completed_at.isoformat() if job.completed_at else None
        ),
    }


@router.get("/research-jobs")
async def list_research_jobs(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    jobs = (
        db.query(AIResearchJob)
        .filter(AIResearchJob.user_id == int(current_user.user_id))
        .order_by(AIResearchJob.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "jobs": [
            {
                "job_id": job.id,
                "status": job.status,
                "progress": job.progress,
                "stage": job.stage,
                "query": job.query[:240],
                "provider": job.provider,
                "model": job.actual_model,
                "created_at": job.created_at.isoformat(),
            }
            for job in jobs
        ]
    }
