"""
Rotas de Inteligencia Operacional
================================
Fornece visao executiva, score de maturidade e recomendacoes acionaveis
para o escritorio.
"""

from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from datetime import datetime, timedelta, timezone
from database import ActivityEvent, Deadline, Hearing, MatterDocItem, OfficeTask, PowerOfAttorney, get_db_async
from security import get_current_user
from services.operations_intelligence_service import operations_intelligence_service

router = APIRouter(prefix="/operations", tags=["Operations"])
REPORTS_ROOT = Path(__file__).resolve().parent.parent.parent / "relatorios_melhorias"
TEXT_EXTENSIONS = {".md", ".txt", ".log", ".json", ".csv", ".yml", ".yaml"}
MAX_PREVIEW_CHARS = 1400
MAX_CONTENT_CHARS = 40000


def _read_text_preview(path: Path, max_chars: int = MAX_PREVIEW_CHARS) -> str:
    """Leitura resiliente de artefatos textuais para preview."""
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return ""

    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_chars].strip()
    except OSError:
        return ""


def _artifact_category(path: Path) -> str:
    """Categoria amigavel baseada no diretorio relativo."""
    relative_parent = path.parent.relative_to(REPORTS_ROOT)
    if str(relative_parent) == ".":
        return "estrategia"
    return relative_parent.as_posix()


def _list_report_artifacts(limit: int = 24) -> List[Dict[str, Any]]:
    """Indexa relatorios, simulacoes e logs gerados pelo projeto."""
    if not REPORTS_ROOT.exists():
        return []

    files = [path for path in REPORTS_ROOT.rglob("*") if path.is_file()]
    files.sort(key=lambda item: item.stat().st_mtime, reverse=True)

    artifacts: List[Dict[str, Any]] = []
    for path in files[:limit]:
        stat = path.stat()
        relative_path = path.relative_to(REPORTS_ROOT).as_posix()
        artifacts.append(
            {
                "id": relative_path,
                "name": path.name,
                "relative_path": relative_path,
                "category": _artifact_category(path),
                "extension": path.suffix.lower(),
                "size_bytes": stat.st_size,
                "modified_at": stat.st_mtime,
                "preview": _read_text_preview(path),
            }
        )

    return artifacts


def _resolve_artifact(relative_path: str) -> Path:
    """Resolve artefatos somente dentro da pasta de relatorios."""
    if not relative_path.strip():
        raise HTTPException(status_code=400, detail="relative_path e obrigatorio")

    requested = (REPORTS_ROOT / relative_path).resolve()
    reports_root = REPORTS_ROOT.resolve()

    if requested != reports_root and reports_root not in requested.parents:
        raise HTTPException(status_code=400, detail="Caminho de artefato invalido")

    if not requested.exists() or not requested.is_file():
        raise HTTPException(status_code=404, detail="Artefato nao encontrado")

    return requested


# Atalhos estaticos dos modulos operacionais do dashboard (Lex / UI).
# Limites de uso tambem existem em GET /usage/me; o atalho aponta para planos.
OPERATIONS_SHORTCUTS: List[Dict[str, str]] = [
    {
        "label": "Hoje",
        "path": "/dashboard/hoje",
        "description": "Prazos, audiencias e procuracoes do dia",
    },
    {
        "label": "Tarefas",
        "path": "/dashboard/tarefas",
        "description": "Checklist operacional do escritorio",
    },
    {
        "label": "Atendimentos",
        "path": "/dashboard/atendimentos",
        "description": "Historico de contatos com clientes",
    },
    {
        "label": "Docs do caso",
        "path": "/dashboard/docs-caso",
        "description": "Checklist do que falta do cliente",
    },
    {
        "label": "Agenda",
        "path": "/dashboard/agenda",
        "description": "Audiencias e compromissos",
    },
    {
        "label": "Procuracoes",
        "path": "/dashboard/poa",
        "description": "Validade operacional de mandatos",
    },
    {
        "label": "Prazos",
        "path": "/dashboard/deadlines",
        "description": "Controle de prazos e alertas do escritorio",
    },
    {
        "label": "Matters",
        "path": "/dashboard/matters",
        "description": "Casos e pastas do cliente",
    },
    {
        "label": "Intake / COI",
        "path": "/dashboard/intake",
        "description": "Leads, intake e checagem de conflito de interesses",
    },
    {
        "label": "Time entries",
        "path": "/dashboard/time",
        "description": "Lancamentos de tempo e honorarios",
    },
    {
        "label": "Aprovacoes WhatsApp",
        "path": "/dashboard/approvals",
        "description": "Fila de aprovacao antes de envio ao cliente",
    },
    {
        "label": "Documentos",
        "path": "/dashboard/documents",
        "description": "Upload e busca no acervo do usuario",
    },
    {
        "label": "Engagement / Activity",
        "path": "/dashboard/activity",
        "description": "Feed operacional e engagement do escritorio",
    },
    {
        "label": "Organizacoes",
        "path": "/dashboard/orgs",
        "description": "Orgs multi-tenant e membros",
    },
    {
        "label": "Trust",
        "path": "/dashboard/trust",
        "description": "Contas de custodia e reconciliacao",
    },
    {
        "label": "E-Sign",
        "path": "/dashboard/esign",
        "description": "Envelopes e assinatura eletronica",
    },
    {
        "label": "Monitor",
        "path": "/dashboard/monitor",
        "description": "Monitoramento de processos e intimacoes",
    },
    {
        "label": "Financeiro",
        "path": "/dashboard/finance",
        "description": "Caixa, aging de recebiveis e NFS-e",
    },
    {
        "label": "Limites de uso",
        "path": "/pricing",
        "description": "Planos e limites; detalhe atual em GET /usage/me",
    },
]


@router.get("/shortcuts")
async def get_operations_shortcuts(
    current_user=Depends(get_current_user),
):
    """Lista atalhos dos modulos operacionais do dashboard (JWT)."""
    _ = current_user
    return {"shortcuts": OPERATIONS_SHORTCUTS}




@router.get("/today")
async def get_operations_today(
    days_ahead: int = Query(7, ge=1, le=30),
    poa_days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db_async),
    current_user=Depends(get_current_user),
):
    """Painel do dia: prazos, audiencias e procuracoes a vencer (JWT)."""
    user_id = int(current_user.user_id)
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=days_ahead + 1)
    today_end = start + timedelta(days=1)

    deadlines = (
        db.query(Deadline)
        .filter(
            Deadline.user_id == user_id,
            Deadline.is_completed.is_(False),
            Deadline.due_date.isnot(None),
            Deadline.due_date < end,
        )
        .order_by(Deadline.due_date.asc())
        .limit(50)
        .all()
    )
    overdue = []
    due_today = []
    upcoming = []
    for d in deadlines:
        due = d.due_date
        if due is None:
            continue
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        item = d.to_dict()
        if due < start:
            overdue.append(item)
        elif due < today_end:
            due_today.append(item)
        else:
            upcoming.append(item)

    hearings = (
        db.query(Hearing)
        .filter(
            Hearing.user_id == user_id,
            Hearing.status == "scheduled",
            Hearing.hearing_at >= start,
            Hearing.hearing_at < end,
        )
        .order_by(Hearing.hearing_at.asc())
        .limit(50)
        .all()
    )

    poa_horizon = now + timedelta(days=poa_days)
    powers = (
        db.query(PowerOfAttorney)
        .filter(
            PowerOfAttorney.user_id == user_id,
            PowerOfAttorney.status == "active",
            PowerOfAttorney.expires_at.isnot(None),
            PowerOfAttorney.expires_at >= now,
            PowerOfAttorney.expires_at <= poa_horizon,
        )
        .order_by(PowerOfAttorney.expires_at.asc())
        .limit(50)
        .all()
    )


    open_tasks = (
        db.query(OfficeTask)
        .filter(
            OfficeTask.user_id == user_id,
            OfficeTask.status == "open",
        )
        .order_by(OfficeTask.due_at.asc(), OfficeTask.id.desc())
        .limit(50)
        .all()
    )
    due_soon_tasks = []
    undated_tasks = []
    for t in open_tasks:
        if t.due_at is None:
            undated_tasks.append(t.to_dict())
            continue
        due = t.due_at if t.due_at.tzinfo else t.due_at.replace(tzinfo=timezone.utc)
        if due < end:
            due_soon_tasks.append(t.to_dict())


    pending_docs = (
        db.query(MatterDocItem)
        .filter(
            MatterDocItem.user_id == user_id,
            MatterDocItem.status == "pending",
        )
        .order_by(MatterDocItem.id.desc())
        .limit(30)
        .all()
    )

    return {
        "success": True,
        "generated_at": now.isoformat(),
        "window": {
            "days_ahead": days_ahead,
            "poa_days": poa_days,
            "from": start.isoformat(),
            "to": end.isoformat(),
        },
        "deadlines": {
            "overdue": overdue,
            "due_today": due_today,
            "upcoming": upcoming,
            "counts": {
                "overdue": len(overdue),
                "due_today": len(due_today),
                "upcoming": len(upcoming),
            },
        },
        "hearings": [h.to_dict() for h in hearings],
        "hearings_count": len(hearings),
        "powers_expiring": [p.to_dict() for p in powers],
        "powers_expiring_count": len(powers),
        "tasks": {
            "due_soon": due_soon_tasks,
            "undated": undated_tasks[:20],
            "counts": {
                "due_soon": len(due_soon_tasks),
                "undated": len(undated_tasks),
                "open": len(open_tasks),
            },
        },
        "docs_pending": [d.to_dict() for d in pending_docs],
        "docs_pending_count": len(pending_docs),
    }

@router.get("/activity")
async def get_operations_activity(
    db: Session = Depends(get_db_async),
    current_user=Depends(get_current_user),
):
    """Últimos 50 eventos do feed operacional do usuário (JWT)."""
    user_id = int(current_user.user_id)
    events = (
        db.query(ActivityEvent)
        .filter(ActivityEvent.user_id == user_id)
        .order_by(ActivityEvent.created_at.desc(), ActivityEvent.id.desc())
        .limit(50)
        .all()
    )
    return {
        "events": [e.to_dict() for e in events],
        "count": len(events),
    }


@router.get("/overview")
async def get_operations_overview(
    db: Session = Depends(get_db_async),
    current_user=Depends(get_current_user),
):
    """Retorna um panorama operacional consolidado do usuario atual."""
    return operations_intelligence_service.build_overview(
        db=db,
        user_id=int(current_user.user_id),
    )


@router.get("/summary")
async def get_operations_summary(
    db: Session = Depends(get_db_async),
    current_user=Depends(get_current_user),
):
    """Retorna um resumo executivo em Markdown para relatórios e copilotos."""
    overview = operations_intelligence_service.build_overview(
        db=db,
        user_id=int(current_user.user_id),
    )
    return {
        "markdown": operations_intelligence_service.build_markdown_summary(overview),
        "overview": overview,
    }


@router.get("/reports-center")
async def get_reports_center(
    limit: int = Query(24, ge=1, le=100),
    db: Session = Depends(get_db_async),
    current_user=Depends(get_current_user),
):
    """Retorna uma central consolidada de relatorios e artefatos do workspace."""
    overview = operations_intelligence_service.build_overview(
        db=db,
        user_id=int(current_user.user_id),
    )
    artifacts = _list_report_artifacts(limit=limit)

    return {
        "generated_at": overview["generated_at"],
        "overview": overview,
        "summary_markdown": operations_intelligence_service.build_markdown_summary(overview),
        "artifacts": artifacts,
        "artifact_count": len(artifacts),
        "reports_root_exists": REPORTS_ROOT.exists(),
        "reports_root": REPORTS_ROOT.as_posix(),
    }


@router.get("/report-artifact")
async def get_report_artifact(
    relative_path: str = Query(..., min_length=1),
    current_user=Depends(get_current_user),
):
    """Retorna conteudo textual de um artefato salvo em relatorios_melhorias."""
    artifact_path = _resolve_artifact(relative_path)
    stat = artifact_path.stat()
    content = _read_text_preview(artifact_path, max_chars=MAX_CONTENT_CHARS)

    return {
        "name": artifact_path.name,
        "relative_path": artifact_path.relative_to(REPORTS_ROOT).as_posix(),
        "category": _artifact_category(artifact_path),
        "extension": artifact_path.suffix.lower(),
        "size_bytes": stat.st_size,
        "modified_at": stat.st_mtime,
        "content": content,
        "truncated": len(content) >= MAX_CONTENT_CHARS,
    }
