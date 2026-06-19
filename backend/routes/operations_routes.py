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

from database import get_db_async
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
