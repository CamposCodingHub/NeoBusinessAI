"""Busca interna de documentos do usuario (lexical / semantic-ish)."""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Any, Dict, List, Sequence

from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session

from database import Document


DEFAULT_TOP_K = 5
DEFAULT_CANDIDATE_LIMIT = 80
EXCERPT_RADIUS = 140
MAX_EXCERPT_CHARS = 420


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", ascii_text).strip().lower()


def _tokenize(query: str) -> List[str]:
    tokens = re.findall(r"[a-z0-9]{2,}", _normalize(query))
    stopwords = {
        "de",
        "da",
        "do",
        "das",
        "dos",
        "em",
        "no",
        "na",
        "nos",
        "nas",
        "um",
        "uma",
        "os",
        "as",
        "ao",
        "aos",
        "que",
        "qual",
        "quais",
        "meu",
        "minha",
        "meus",
        "minhas",
        "o",
        "a",
        "e",
        "ou",
        "para",
        "por",
        "com",
        "sobre",
        "diz",
        "pdf",
        "documento",
        "documentos",
        "arquivo",
        "arquivos",
        "contrato",
        "contratos",
    }
    return [token for token in tokens if token not in stopwords]


def _parties_text(parties: Any) -> str:
    if parties is None:
        return ""
    if isinstance(parties, str):
        return parties
    try:
        return json.dumps(parties, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(parties)


def _content_dict(document: Document) -> Dict[str, Any]:
    """JSON legado em Document.content (ainda preenchido pelo pipeline)."""
    content = getattr(document, "content", None)
    return content if isinstance(content, dict) else {}


def _document_type(document: Document) -> str:
    """Tipo: coluna live Document.document_type; fallback content JSON legado."""
    explicit = getattr(document, "document_type", None)
    if explicit:
        return str(explicit)
    return str(_content_dict(document).get("document_type") or "")


def _analysis_text(document: Document) -> str:
    analysis = getattr(document, "analysis", None)
    if isinstance(analysis, str) and analysis.strip():
        return analysis
    if isinstance(analysis, dict):
        try:
            return json.dumps(analysis, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(analysis)
    return ""


def _text_content(document: Document) -> str:
    """Texto: coluna live Document.text_content; fallbacks content/analysis."""
    column_value = getattr(document, "text_content", None)
    if isinstance(column_value, str) and column_value.strip():
        return column_value

    content = _content_dict(document)
    for key in ("extracted_text", "text_content", "text", "raw_text"):
        value = content.get(key)
        if value:
            return str(value)

    return _analysis_text(document)


def _haystacks(document: Document) -> Dict[str, str]:
    """Campos reais usados no ranking (alinhados a document_to_dict)."""
    filename = " ".join(
        filter(
            None,
            [
                getattr(document, "filename", None) or "",
                getattr(document, "original_filename", None) or "",
                getattr(document, "title", None) or "",
            ],
        )
    )
    return {
        "filename": filename,
        "summary": str(getattr(document, "summary", None) or ""),
        "document_type": _document_type(document),
        "parties": _parties_text(getattr(document, "parties", None)),
        "analysis": _analysis_text(document),
        "text_content": _text_content(document),
    }


def _score_document(document: Document, tokens: Sequence[str], query: str) -> float:
    fields = _haystacks(document)
    normalized_fields = {key: _normalize(value) for key, value in fields.items()}
    query_norm = _normalize(query)
    score = 0.0
    weights = {
        "filename": 4.0,
        "document_type": 3.0,
        "parties": 2.5,
        "summary": 2.0,
        "analysis": 1.5,
        "text_content": 1.0,
    }

    if query_norm and query_norm in normalized_fields["filename"]:
        score += 12.0
    if query_norm and query_norm in normalized_fields["summary"]:
        score += 6.0
    if query_norm and query_norm in normalized_fields["analysis"]:
        score += 4.0

    for token in tokens:
        for field, weight in weights.items():
            haystack = normalized_fields[field]
            if not haystack or token not in haystack:
                continue
            occurrences = haystack.count(token)
            score += weight * min(occurrences, 4)
            if field == "filename" and haystack.startswith(token):
                score += 2.0

    # Prefer completed / analyzed documents slightly.
    status = str(getattr(document, "status", "") or "").lower()
    if status in {"completed", "processed"}:
        score += 0.5
    return score


def _excerpt_for(document: Document, tokens: Sequence[str], query: str) -> str:
    fields = _haystacks(document)
    preferred = [
        fields["summary"],
        fields["text_content"],
        fields["analysis"],
        fields["parties"],
        fields["filename"],
    ]
    query_norm = _normalize(query)
    for source in preferred:
        if not source:
            continue
        lowered = source.lower()
        idx = -1
        needle = ""
        if query_norm and query_norm in _normalize(source):
            # Approximate position using first token present.
            for token in tokens or [query_norm]:
                pos = lowered.find(token)
                if pos >= 0:
                    idx = pos
                    needle = token
                    break
        if idx < 0:
            for token in tokens:
                pos = lowered.find(token)
                if pos >= 0:
                    idx = pos
                    needle = token
                    break
        if idx < 0 and not tokens:
            excerpt = re.sub(r"\s+", " ", source).strip()
            return excerpt[:MAX_EXCERPT_CHARS]
        if idx >= 0:
            start = max(0, idx - EXCERPT_RADIUS)
            end = min(len(source), idx + len(needle) + EXCERPT_RADIUS)
            snippet = re.sub(r"\s+", " ", source[start:end]).strip()
            prefix = "..." if start > 0 else ""
            suffix = "..." if end < len(source) else ""
            return f"{prefix}{snippet}{suffix}"[:MAX_EXCERPT_CHARS]

    fallback = fields["summary"] or fields["filename"] or "Sem trecho disponivel"
    return re.sub(r"\s+", " ", fallback).strip()[:MAX_EXCERPT_CHARS]


def _append_ilike(patterns: List[Any], column: Any, like: str) -> None:
    if column is None:
        return
    try:
        patterns.append(column.ilike(like))
    except Exception:
        pass


def _sql_candidates(
    db: Session,
    user_id: int,
    query: str,
    tokens: Sequence[str],
    limit: int,
) -> List[Document]:
    """Filtra candidatos via ILIKE nas colunas live do Document.

    Colunas primarias: filename, summary, text_content, document_type,
    parties, analysis. content JSON e fallback legado (extracted_text).
    """
    base = db.query(Document).filter(Document.user_id == user_id)
    patterns: List[Any] = []
    raw_terms = [query.strip()] + list(tokens[:6])
    for term in raw_terms:
        cleaned = term.strip()
        if len(cleaned) < 2:
            continue
        like = f"%{cleaned}%"
        _append_ilike(patterns, Document.filename, like)
        _append_ilike(patterns, getattr(Document, "original_filename", None), like)
        _append_ilike(patterns, getattr(Document, "title", None), like)
        _append_ilike(patterns, Document.summary, like)
        _append_ilike(patterns, Document.text_content, like)
        _append_ilike(patterns, Document.document_type, like)
        _append_ilike(patterns, Document.analysis, like)
        # JSON cast: parties (live) + content (legado extracted_text / tipo).
        try:
            patterns.append(cast(Document.parties, String).ilike(like))
        except Exception:
            pass
        try:
            patterns.append(cast(Document.content, String).ilike(like))
        except Exception:
            pass

    if patterns:
        filtered = (
            base.filter(or_(*patterns))
            .order_by(Document.updated_at.desc(), Document.id.desc())
            .limit(limit)
            .all()
        )
        if filtered:
            return filtered

    return (
        base.order_by(Document.updated_at.desc(), Document.id.desc())
        .limit(limit)
        .all()
    )


def search_user_documents(
    db: Session,
    user_id: int,
    query: str,
    *,
    top_k: int = DEFAULT_TOP_K,
    candidate_limit: int = DEFAULT_CANDIDATE_LIMIT,
) -> List[Dict[str, Any]]:
    """Busca documentos do usuario por palavra-chave com ranking simples.

    Retorna lista ordenada com document_id, filename, score e excerpt.
    """
    cleaned_query = (query or "").strip()
    if not cleaned_query or not user_id:
        return []

    tokens = _tokenize(cleaned_query)
    candidates = _sql_candidates(
        db,
        int(user_id),
        cleaned_query,
        tokens,
        max(candidate_limit, top_k),
    )

    ranked: List[Dict[str, Any]] = []
    for document in candidates:
        score = _score_document(document, tokens, cleaned_query)
        if score <= 0 and tokens:
            continue
        if score <= 0 and not tokens:
            score = 0.1
        ranked.append(
            {
                "document_id": document.id,
                "filename": (
                    document.original_filename
                    or document.filename
                    or f"documento-{document.id}"
                ),
                "document_type": _document_type(document) or None,
                "score": round(float(score), 3),
                "excerpt": _excerpt_for(document, tokens, cleaned_query),
                "status": getattr(document, "status", None),
            }
        )

    ranked.sort(key=lambda item: (-item["score"], item["document_id"]))
    return ranked[: max(1, int(top_k))]


def build_document_context(
    results: Sequence[Dict[str, Any]],
    *,
    max_chars: int = 8000,
) -> str:
    """Monta bloco de contexto para injecao no Lex."""
    if not results:
        return ""

    blocks: List[str] = []
    used = 0
    for index, item in enumerate(results, start=1):
        block = (
            f"[Doc {index}] id={item.get('document_id')} "
            f"arquivo={item.get('filename')} "
            f"tipo={item.get('document_type') or 'n/d'} "
            f"score={item.get('score')}\n"
            f"Trecho: {item.get('excerpt') or ''}"
        )
        if used + len(block) > max_chars and blocks:
            break
        blocks.append(block)
        used += len(block) + 5
    header = (
        "DOCUMENTOS INTERNOS DO USUARIO (busca no produto):\n"
        "Use apenas estes trechos como evidencia factual do acervo do usuario. "
        "Se o trecho for insuficiente, diga isso explicitamente.\n\n"
    )
    return header + "\n\n--- PROXIMO ARQUIVO ---\n\n".join(blocks)


def looks_like_user_document_query(message: str) -> bool:
    """Heuristica para perguntas sobre documentos do usuario no produto."""
    normalized = _normalize(message)
    markers = (
        "meu contrato",
        "minha peticao",
        "meus documentos",
        "meus arquivos",
        "documento anexado",
        "no documento",
        "do documento",
        "no pdf",
        "o que diz o pdf",
        "o que diz o contrato",
        "procure no documento",
        "busque no documento",
        "encontre no contrato",
        "no meu acervo",
        "arquivo que enviei",
        "pdf que enviei",
        "contrato que enviei",
        "nos meus documentos",
        "entre meus documentos",
    )
    if any(marker in normalized for marker in markers):
        return True
    # Generic "documento X" / "contrato X" with a specific name-ish token.
    if re.search(
        r"\b(documento|contrato|peticao|arquivo|pdf)\b.{0,40}\b",
        normalized,
    ) and any(
        token in normalized
        for token in ("meu", "minha", "meus", "minhas", "anex", "enviad", "uplo")
    ):
        return True
    return False


def looks_like_accounting_tax_query(message: str) -> bool:
    """Detecta intents contabeis / fiscais BR operacionais."""
    from ai.professional_domains import (
        looks_like_accounting_tax_query as _domain_accounting_query,
    )

    return _domain_accounting_query(message)


class InternalDocumentSearch:
    """Facade usada pelo orquestrador e pelas rotas."""

    def search(
        self,
        db: Session,
        user_id: int,
        query: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> List[Dict[str, Any]]:
        return search_user_documents(db, user_id, query, top_k=top_k)

    def build_context(
        self,
        results: Sequence[Dict[str, Any]],
        max_chars: int = 8000,
    ) -> str:
        return build_document_context(results, max_chars=max_chars)


internal_document_search = InternalDocumentSearch()
