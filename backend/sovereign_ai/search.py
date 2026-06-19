"""Busca juridica hibrida local com citacoes verificaveis."""

from __future__ import annotations

import asyncio
import hashlib
import math
import re
import unicodedata
from collections import Counter
from datetime import datetime
from typing import Any, Dict, Iterable, List, Sequence

import httpx
from sqlalchemy import or_
from sqlalchemy.orm import Session

from config import settings
from database import (
    Document,
    LegalKnowledgeChunk,
    LegalKnowledgeSource,
    SessionLocal,
)
from services.official_legal_sources_service import (
    LEGAL_SOURCES,
    official_legal_sources,
)


LEGAL_SYNONYMS = {
    "prisao": {"custodia", "cautelar", "preventiva", "liberdade"},
    "contrato": {"obrigacao", "inadimplemento", "clausula", "rescisao"},
    "consumidor": {"fornecedor", "produto", "servico", "vicio", "defeito"},
    "trabalhista": {"empregado", "empregador", "clt", "rescisao"},
    "tributario": {"tributo", "imposto", "credito", "fiscal"},
    "dados": {"lgpd", "privacidade", "tratamento", "titular"},
    "recurso": {"apelacao", "agravo", "embargos", "recorrente"},
    "jurisprudencia": {"precedente", "acordao", "sumula", "tema"},
}

PORTUGUESE_STOPWORDS = {
    "a", "ao", "aos", "aquela", "aquele", "as", "com", "como", "da", "das",
    "de", "do", "dos", "e", "em", "entre", "essa", "esse", "esta", "este",
    "foi", "ha", "isso", "na", "nas", "no", "nos", "o", "os", "ou", "para",
    "pela", "pelas", "pelo", "pelos", "por", "qual", "quais", "que", "sao",
    "se", "sem", "ser", "seu", "sua", "um", "uma", "previsto", "previstos",
}


def normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value or "")
    without_accents = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return re.sub(r"\s+", " ", without_accents.lower()).strip()


def tokenize(value: str) -> List[str]:
    return re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?", normalize_text(value))


def expand_terms(query: str) -> List[str]:
    terms = list(
        dict.fromkeys(
            term
            for term in tokenize(query)
            if term not in PORTUGUESE_STOPWORDS and len(term) > 1
        )
    )
    expanded = list(terms)
    for term in terms:
        expanded.extend(sorted(LEGAL_SYNONYMS.get(term, set())))
    return list(dict.fromkeys(term for term in expanded if len(term) > 1))


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return max(-1.0, min(1.0, dot / (left_norm * right_norm)))


class OllamaEmbeddingClient:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: int = 180,
    ):
        openai_base = (base_url or settings.LOCAL_AI_BASE_URL).rstrip("/")
        self.base_url = openai_base.removesuffix("/v1")
        self.model = model or settings.LOCAL_AI_EMBEDDING_MODEL
        self.timeout_seconds = timeout_seconds

    async def embed(self, texts: Sequence[str]) -> List[List[float]]:
        if not texts:
            return []
        timeout = httpx.Timeout(self.timeout_seconds, connect=10)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/embed",
                json={
                    "model": self.model,
                    "input": list(texts),
                    "truncate": True,
                    "keep_alive": settings.LOCAL_AI_KEEP_ALIVE,
                },
            )
        response.raise_for_status()
        payload = response.json()
        embeddings = payload.get("embeddings") or []
        if len(embeddings) != len(texts):
            raise RuntimeError("Ollama retornou quantidade invalida de embeddings")
        return [[float(value) for value in vector] for vector in embeddings]

    async def safe_embed(self, texts: Sequence[str]) -> List[List[float] | None]:
        try:
            return list(await self.embed(texts))
        except Exception:
            return [None for _ in texts]


class SovereignLegalSearch:
    def __init__(self, embedding_client: OllamaEmbeddingClient | None = None):
        self.embedding_client = embedding_client or OllamaEmbeddingClient()

    @staticmethod
    def chunk_text(
        text: str,
        *,
        max_chars: int = 1800,
        overlap_chars: int = 220,
    ) -> List[str]:
        cleaned = re.sub(r"\r\n?", "\n", text or "")
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
        if not cleaned:
            return []

        structural_text = "".join(
            char
            for char in unicodedata.normalize("NFKD", cleaned)
            if not unicodedata.combining(char)
        ).lower()
        boundaries = [
            match.start()
            for match in re.finditer(
                r"(?im)(?=^\s*(?:art\.?\s*\d+|capitulo\b|titulo\b|secao\b))",
                structural_text,
            )
        ]
        if not boundaries:
            boundaries = [0]
        boundaries.append(len(cleaned))
        sections = [
            cleaned[boundaries[index] : boundaries[index + 1]].strip()
            for index in range(len(boundaries) - 1)
        ]

        chunks: List[str] = []
        for section in sections:
            cursor = 0
            while cursor < len(section):
                end = min(cursor + max_chars, len(section))
                if end < len(section):
                    preferred = max(
                        section.rfind("\n\n", cursor, end),
                        section.rfind(". ", cursor, end),
                        section.rfind("; ", cursor, end),
                    )
                    if preferred > cursor + max_chars // 2:
                        end = preferred + 1
                chunk = section[cursor:end].strip()
                if len(chunk) >= 40:
                    chunks.append(chunk)
                if end >= len(section):
                    break
                cursor = max(end - overlap_chars, cursor + 1)
        return chunks

    async def index_text(
        self,
        db: Session,
        *,
        source_key: str,
        title: str,
        content: str,
        source_type: str,
        authority: str = "",
        jurisdiction: str = "Brasil",
        legal_area: str = "geral",
        url: str = "",
        citation_prefix: str = "",
        custom_data: Dict[str, Any] | None = None,
        force: bool = False,
        generate_embeddings: bool = True,
    ) -> Dict[str, Any]:
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        source = (
            db.query(LegalKnowledgeSource)
            .filter(LegalKnowledgeSource.source_key == source_key)
            .first()
        )
        if source and source.content_hash == content_hash and not force:
            count = (
                db.query(LegalKnowledgeChunk)
                .filter(LegalKnowledgeChunk.source_id == source.id)
                .count()
            )
            return {
                "source_id": source.id,
                "source_key": source_key,
                "chunks": count,
                "unchanged": True,
            }

        if not source:
            source = LegalKnowledgeSource(
                source_key=source_key,
                title=title,
                source_type=source_type,
                authority=authority,
                jurisdiction=jurisdiction,
                legal_area=legal_area,
                url=url,
                status="active",
                content_hash=content_hash,
                custom_data=custom_data or {},
                last_collected_at=datetime.utcnow(),
            )
            db.add(source)
            db.flush()
        else:
            db.query(LegalKnowledgeChunk).filter(
                LegalKnowledgeChunk.source_id == source.id
            ).delete(synchronize_session=False)

        source.title = title
        source.source_type = source_type
        source.authority = authority
        source.jurisdiction = jurisdiction
        source.legal_area = legal_area
        source.url = url
        source.status = "active"
        source.content_hash = content_hash
        source.custom_data = custom_data or {}
        source.last_collected_at = datetime.utcnow()

        chunks = self.chunk_text(content)
        embeddings: List[List[float] | None] = []
        if generate_embeddings:
            for start in range(0, len(chunks), 24):
                embeddings.extend(
                    await self.embedding_client.safe_embed(
                        chunks[start : start + 24]
                    )
                )
        else:
            embeddings = [None for _ in chunks]

        for ordinal, chunk in enumerate(chunks):
            article = re.search(
                r"(?i)\bart\.?\s*(\d+[a-z]?(?:-[a-z])?)",
                chunk,
            )
            citation = citation_prefix or title
            if article:
                citation = f"{citation}, art. {article.group(1)}"
            db.add(
                LegalKnowledgeChunk(
                    source_id=source.id,
                    external_id=f"{source_key}:{ordinal}",
                    ordinal=ordinal,
                    title=title,
                    content=chunk,
                    normalized_content=normalize_text(chunk),
                    embedding=embeddings[ordinal] if embeddings else None,
                    embedding_model=(
                        self.embedding_client.model
                        if embeddings and embeddings[ordinal]
                        else None
                    ),
                    token_count=max(1, len(chunk) // 4),
                    citation=citation,
                    legal_area=legal_area,
                    custom_data=custom_data or {},
                )
            )
        db.commit()
        return {
            "source_id": source.id,
            "source_key": source_key,
            "chunks": len(chunks),
            "embedded": sum(bool(item) for item in embeddings),
            "unchanged": False,
        }

    async def index_user_document(
        self,
        db: Session,
        document: Document,
    ) -> Dict[str, Any]:
        raw_content = document.content
        if isinstance(raw_content, dict):
            content = str(
                raw_content.get("extracted_text")
                or raw_content.get("text")
                or raw_content.get("content")
                or raw_content
            )
        else:
            content = str(raw_content or "")
        if not content.strip():
            raise ValueError("Documento nao possui conteudo extraido")
        return await self.index_text(
            db,
            source_key=f"user-document:{document.user_id}:{document.id}",
            title=document.title or document.original_filename or document.filename,
            content=content,
            source_type="user_document",
            authority="Documento do usuario",
            jurisdiction="privado",
            legal_area=str((document.custom_data or {}).get("legal_area") or "geral"),
            citation_prefix=document.original_filename or document.filename,
            custom_data={
                "user_id": document.user_id,
                "document_id": document.id,
                "private": True,
            },
            generate_embeddings=False,
        )

    async def bootstrap_official_sources(
        self,
        db: Session,
        *,
        source_codes: Sequence[str],
        force: bool = False,
        generate_embeddings: bool = False,
    ) -> List[Dict[str, Any]]:
        selected = [
            source for source in LEGAL_SOURCES if source.code in source_codes
        ]
        results = []
        for source in selected:
            try:
                content = await asyncio.to_thread(
                    official_legal_sources._fetch_text,
                    source.url,
                )
                results.append(
                    await self.index_text(
                        db,
                        source_key=f"official:{source.code}",
                        title=source.title,
                        content=content,
                        source_type=source.source_type,
                        authority=self._authority_for(source.url),
                        jurisdiction="Brasil",
                        legal_area=source.legal_area,
                        url=source.url,
                        citation_prefix=source.title,
                        custom_data={"official_code": source.code},
                        force=force,
                        generate_embeddings=generate_embeddings,
                    )
                )
            except Exception as exc:
                results.append(
                    {
                        "source_key": f"official:{source.code}",
                        "error": str(exc),
                    }
                )
        return results

    async def search(
        self,
        db: Session,
        *,
        query: str,
        top_k: int | None = None,
        legal_area: str | None = None,
        court: str | None = None,
        user_id: int | None = None,
        include_private: bool = True,
    ) -> Dict[str, Any]:
        top_k = top_k or settings.AI_KNOWLEDGE_TOP_K
        terms = expand_terms(query)
        query_embedding = (
            await self.embedding_client.safe_embed([query])
        )[0]

        chunks_query = db.query(LegalKnowledgeChunk).join(
            LegalKnowledgeSource,
            LegalKnowledgeSource.id == LegalKnowledgeChunk.source_id,
        ).filter(LegalKnowledgeSource.status == "active")
        if legal_area:
            chunks_query = chunks_query.filter(
                LegalKnowledgeChunk.legal_area == legal_area
            )
        if court:
            chunks_query = chunks_query.filter(
                LegalKnowledgeChunk.court == court
            )
        if terms:
            chunks_query = chunks_query.filter(
                or_(
                    *[
                        LegalKnowledgeChunk.normalized_content.ilike(
                            f"%{term}%"
                        )
                        for term in terms[:12]
                    ]
                )
            )
        article_numbers = re.findall(
            r"\bart(?:igo)?\.?\s*(\d+[a-z]?(?:-[a-z])?)",
            normalize_text(query),
        )
        priority_candidates = []
        if article_numbers:
            priority_candidates = chunks_query.filter(
                or_(
                    *[
                        LegalKnowledgeChunk.normalized_content.ilike(
                            f"%art%{article}%"
                        )
                        for article in article_numbers
                    ]
                )
            ).limit(60).all()
        general_candidates = chunks_query.limit(600).all()
        candidates = list(
            {
                chunk.id: chunk
                for chunk in [*priority_candidates, *general_candidates]
            }.values()
        )

        # O corpus oficial entra imediatamente por busca lexical. Embeddings
        # dos candidatos relevantes sao materializados de forma incremental.
        missing_embeddings = [
            chunk for chunk in candidates if not chunk.embedding
        ][: settings.AI_LAZY_EMBED_BATCH]
        if missing_embeddings:
            generated = await self.embedding_client.safe_embed(
                [chunk.content for chunk in missing_embeddings]
            )
            changed = False
            for chunk, vector in zip(missing_embeddings, generated):
                if vector:
                    chunk.embedding = vector
                    chunk.embedding_model = self.embedding_client.model
                    changed = True
            if changed:
                db.commit()

        document_frequency = Counter()
        candidate_tokens = {}
        for chunk in candidates:
            tokens = set(tokenize(chunk.normalized_content))
            candidate_tokens[chunk.id] = tokens
            for term in terms:
                if term in tokens:
                    document_frequency[term] += 1

        scored = []
        query_normalized = normalize_text(query)
        for chunk in candidates:
            metadata = chunk.custom_data or {}
            if metadata.get("private"):
                if not include_private:
                    continue
                if user_id is None or int(metadata.get("user_id") or -1) != int(user_id):
                    continue
            tokens = candidate_tokens[chunk.id]
            lexical = 0.0
            for term in terms:
                if term not in tokens:
                    continue
                inverse = math.log(
                    (len(candidates) + 1)
                    / (document_frequency[term] + 0.5)
                )
                lexical += max(0.1, inverse)
            lexical = min(1.0, lexical / max(2.5, len(terms) * 0.45))
            if query_normalized in chunk.normalized_content:
                lexical = min(1.0, lexical + 0.25)
            referenced_article_match = any(
                re.search(
                    rf"\bart\.?\s*{re.escape(article)}(?:\D|$)",
                    chunk.normalized_content,
                )
                for article in article_numbers
            )
            citation_normalized = normalize_text(chunk.citation or "")
            exact_article_match = any(
                re.search(
                    rf"\bart\.?\s*{re.escape(article)}(?:\D|$)",
                    citation_normalized,
                )
                for article in article_numbers
            )
            if exact_article_match:
                lexical = 1.0
            elif referenced_article_match:
                lexical = min(0.82, lexical + 0.12)
            semantic = max(
                0.0,
                cosine_similarity(query_embedding or [], chunk.embedding or []),
            )
            authority_bonus = (
                0.08
                if chunk.source.source_key.startswith("official:")
                else 0.04
            )
            article_bonus = (
                0.25 if exact_article_match else
                0.04 if referenced_article_match else
                0.0
            )
            score = min(
                1.0,
                semantic * 0.52
                + lexical * 0.34
                + authority_bonus
                + article_bonus,
            )
            if score < settings.AI_KNOWLEDGE_MIN_SCORE:
                continue
            scored.append(
                {
                    "chunk_id": chunk.id,
                    "source_id": chunk.source_id,
                    "source_key": chunk.source.source_key,
                    "title": chunk.title or chunk.source.title,
                    "citation": chunk.citation,
                    "url": chunk.source.url,
                    "authority": chunk.source.authority,
                    "source_type": chunk.source.source_type,
                    "legal_area": chunk.legal_area,
                    "court": chunk.court,
                    "excerpt": chunk.content,
                    "score": round(score, 6),
                    "semantic_score": round(semantic, 6),
                    "lexical_score": round(lexical, 6),
                    "private": bool(metadata.get("private")),
                }
            )
        scored.sort(key=lambda item: item["score"], reverse=True)
        diversified = []
        citation_counts = Counter()
        for item in scored:
            citation_key = normalize_text(item["citation"] or item["title"])
            if citation_counts[citation_key] >= 1:
                continue
            diversified.append(item)
            citation_counts[citation_key] += 1
            if len(diversified) >= top_k:
                break
        return {
            "query": query,
            "results": diversified,
            "total_candidates": len(candidates),
            "embedding_model": self.embedding_client.model,
            "hybrid_search": True,
        }

    @staticmethod
    def build_context(
        results: Iterable[Dict[str, Any]],
        *,
        max_excerpt_chars: int = 1200,
    ) -> str:
        blocks = []
        for index, item in enumerate(results, start=1):
            blocks.append(
                "\n".join(
                    [
                        f"[Base Local {index}] {item['citation']}",
                        f"Autoridade: {item.get('authority') or 'nao informada'}",
                        f"URL: {item.get('url') or 'documento privado'}",
                        f"Trecho:\n{item['excerpt'][:max_excerpt_chars]}",
                    ]
                )
            )
        return "\n\n".join(blocks)

    @staticmethod
    def stats(db: Session) -> Dict[str, Any]:
        return {
            "sources": db.query(LegalKnowledgeSource).count(),
            "chunks": db.query(LegalKnowledgeChunk).count(),
            "embedded_chunks": db.query(LegalKnowledgeChunk)
            .filter(LegalKnowledgeChunk.embedding_model.isnot(None))
            .count(),
        }

    @staticmethod
    def _authority_for(url: str) -> str:
        if "planalto.gov.br" in url:
            return "Presidencia da Republica"
        if "stj.jus.br" in url:
            return "Superior Tribunal de Justica"
        if "stf.jus.br" in url:
            return "Supremo Tribunal Federal"
        if "cnj.jus.br" in url:
            return "Conselho Nacional de Justica"
        if "receita" in url:
            return "Receita Federal"
        return "Fonte oficial"


sovereign_legal_search = SovereignLegalSearch()


async def search_local_knowledge(
    query: str,
    *,
    user_id: int | None = None,
    legal_area: str | None = None,
    top_k: int | None = None,
) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        return await sovereign_legal_search.search(
            db,
            query=query,
            user_id=user_id,
            legal_area=legal_area,
            top_k=top_k,
        )
    finally:
        db.close()
