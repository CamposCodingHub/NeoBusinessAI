"""Testes da busca interna de documentos do usuario."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, List
from unittest.mock import MagicMock

import pytest

from services.internal_document_search import (
    build_document_context,
    looks_like_accounting_tax_query,
    looks_like_user_document_query,
    search_user_documents,
)


def _doc(
    *,
    doc_id: int,
    user_id: int = 1,
    filename: str,
    summary: str = "",
    text: str = "",
    document_type: str = "contrato",
    parties: Any = None,
    status: str = "completed",
    analysis: str = "",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=doc_id,
        user_id=user_id,
        filename=filename,
        original_filename=filename,
        title=filename,
        summary=summary,
        text_content=text,
        document_type=document_type,
        # Legacy content JSON still present as fallback for older rows.
        content={
            "extracted_text": text,
            "document_type": document_type,
            "text_content": text,
        },
        parties=parties or {},
        analysis=analysis,
        status=status,
        updated_at=None,
    )


class _FakeQuery:
    def __init__(self, documents: List[Any]):
        self._documents = documents
        self._filters = []

    def filter(self, *args, **kwargs):
        self._filters.extend(args)
        return self

    def order_by(self, *args, **kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def all(self):
        # Mock session returns all documents for the user; scoring does ranking.
        return list(self._documents)


class _FakeSession:
    def __init__(self, documents: List[Any]):
        self._documents = documents

    def query(self, *_args, **_kwargs):
        return _FakeQuery(self._documents)


def test_search_ranks_filename_and_text_hits():
    docs = [
        _doc(
            doc_id=1,
            filename="proposta-comercial.pdf",
            summary="Proposta comercial generica",
            text="Objeto generico sem clausulas relevantes",
            document_type="proposta",
        ),
        _doc(
            doc_id=2,
            filename="contrato-locacao-loja.pdf",
            summary="Contrato de locacao comercial",
            text=(
                "Clausula 5. O locatario pagara aluguel mensal. "
                "Multa por atraso de 2% ao mes."
            ),
            document_type="contrato",
            parties={"locador": "Alpha Ltda", "locatario": "Beta ME"},
        ),
        _doc(
            doc_id=3,
            filename="peticao-inicial.pdf",
            summary="Peticao civel",
            text="Pedido de indenizacao por danos materiais",
            document_type="peticao",
        ),
    ]
    session = _FakeSession(docs)

    results = search_user_documents(
        session,
        user_id=1,
        query="meu contrato locacao multa",
        top_k=3,
    )

    assert results
    assert results[0]["document_id"] == 2
    assert results[0]["filename"] == "contrato-locacao-loja.pdf"
    assert results[0]["score"] > 0
    assert "multa" in results[0]["excerpt"].lower() or "locacao" in results[0][
        "excerpt"
    ].lower()


def test_search_isolates_by_user_id_via_query_filter():
    docs = [
        _doc(doc_id=10, user_id=1, filename="meu-contrato.pdf", text="clausula confidencial"),
        _doc(doc_id=11, user_id=2, filename="outro-contrato.pdf", text="clausula confidencial"),
    ]
    # Fake session does not re-filter by user_id; simulate owned docs only.
    session = _FakeSession([docs[0]])
    results = search_user_documents(session, user_id=1, query="contrato confidencial")
    assert all(item["document_id"] == 10 for item in results)


def test_search_uses_live_text_content_column():
    """Ranking deve ler Document.text_content, nao so content JSON."""
    docs = [
        SimpleNamespace(
            id=1,
            user_id=1,
            filename="arquivo.pdf",
            original_filename="arquivo.pdf",
            title=None,
            summary="Resumo curto",
            text_content="Clausula unica sobre multa contratual de locacao",
            document_type="contrato",
            content={},  # sem extracted_text ficticio
            parties={"locador": "Alpha"},
            analysis="Analise menciona risco de multa",
            status="completed",
            updated_at=None,
        )
    ]
    results = search_user_documents(
        _FakeSession(docs),
        user_id=1,
        query="multa locacao",
        top_k=1,
    )
    assert results
    assert results[0]["document_id"] == 1
    assert results[0]["document_type"] == "contrato"
    assert "multa" in results[0]["excerpt"].lower()


def test_search_falls_back_to_content_extracted_text():
    """Linhas antigas so com content.extracted_text continuam pesquisaveis."""
    docs = [
        SimpleNamespace(
            id=2,
            user_id=1,
            filename="legado.pdf",
            original_filename="legado.pdf",
            title=None,
            summary="",
            text_content=None,
            document_type=None,
            content={
                "extracted_text": "Texto legado com clausula de rescisao",
                "document_type": "peticao",
            },
            parties={},
            analysis="",
            status="completed",
            updated_at=None,
        )
    ]
    results = search_user_documents(
        _FakeSession(docs),
        user_id=1,
        query="rescisao",
        top_k=1,
    )
    assert results
    assert results[0]["document_type"] == "peticao"
    assert "rescisao" in results[0]["excerpt"].lower()


def test_build_document_context_includes_ranked_snippets():
    context = build_document_context(
        [
            {
                "document_id": 7,
                "filename": "contrato.pdf",
                "document_type": "contrato",
                "score": 9.5,
                "excerpt": "Clausula de rescisao antecipada.",
            }
        ]
    )
    assert "DOCUMENTOS INTERNOS DO USUARIO" in context
    assert "contrato.pdf" in context
    assert "Clausula de rescisao antecipada" in context


@pytest.mark.parametrize(
    "message,expected",
    [
        ("O que diz o PDF do meu contrato sobre multa?", True),
        ("Liste meus documentos sobre locacao", True),
        ("Qual a diferenca entre dolo eventual e culpa?", False),
        ("Como classificar despesa de software no plano de contas?", False),
    ],
)
def test_looks_like_user_document_query(message, expected):
    assert looks_like_user_document_query(message) is expected


@pytest.mark.parametrize(
    "message,expected",
    [
        ("Como funciona o ISS para servicos de advocacia?", True),
        ("Classificacao de despesas com cartorio no Simples Nacional", True),
        ("Quais obrigacoes acessorias da DCTFWeb?", True),
        ("Resuma o artigo 121 do Codigo Penal", False),
    ],
)
def test_looks_like_accounting_tax_query(message, expected):
    assert looks_like_accounting_tax_query(message) is expected


@pytest.mark.asyncio
async def test_orchestrator_injects_internal_document_context(monkeypatch):
    from services.legal_ai_orchestrator import LegalAIOrchestrator

    captured = {}

    class Engine:
        async def generate_premium_response(self, **kwargs):
            captured.update(kwargs)
            return {
                "response": "Com base no contrato recuperado [Fonte 1].",
                "quality_score": 88,
                "metadata": {"model": kwargs.get("model_name"), "actual_model": kwargs.get("model_name")},
            }

    orchestrator = LegalAIOrchestrator(Engine())

    monkeypatch.setattr(
        "services.legal_ai_orchestrator.official_legal_sources.retrieve",
        lambda query: {
            "is_legal_query": False,
            "legal_area": "geral",
            "article": None,
            "grounding_status": "unverified",
            "sources": [],
            "guardrails": [],
        },
    )
    monkeypatch.setattr(
        "services.legal_ai_orchestrator.official_legal_sources.build_context",
        lambda retrieval: "",
    )
    monkeypatch.setattr(
        "services.legal_ai_orchestrator.search_user_documents",
        lambda db, user_id, query, top_k=5: [
            {
                "document_id": 42,
                "filename": "contrato-servicos.pdf",
                "document_type": "contrato",
                "score": 11.0,
                "excerpt": "Clausula 3. Remuneracao mensal de R$ 5.000,00.",
            }
        ],
    )
    fake_db = MagicMock()
    monkeypatch.setattr(
        "database.SessionLocal",
        lambda: fake_db,
    )

    result = await orchestrator.answer(
        user_message="O que diz o meu contrato de servicos sobre remuneracao?",
        user_id="9:default",
        document_context="",
        response_mode="balanced",
    )

    assert "contrato-servicos.pdf" in captured.get("document_context", "")
    assert result["legal_metadata"]["internal_document_search_used"] is True
    assert result["legal_metadata"]["internal_document_hits"][0]["document_id"] == 42
    fake_db.close.assert_called()


@pytest.mark.asyncio
async def test_orchestrator_marks_accounting_intent(monkeypatch):
    from services.legal_ai_orchestrator import LegalAIOrchestrator

    captured = {}

    class Engine:
        async def generate_premium_response(self, **kwargs):
            captured.update(kwargs)
            return {
                "response": (
                    "Orientacao operacional sem aliquota inventada. "
                    "Nao e parecer vinculante."
                ),
                "metadata": {
                    "model": kwargs.get("model_name"),
                    "actual_model": kwargs.get("model_name"),
                },
            }

    orchestrator = LegalAIOrchestrator(Engine())
    monkeypatch.setattr(
        "services.legal_ai_orchestrator.official_legal_sources.retrieve",
        lambda query: {
            "is_legal_query": False,
            "legal_area": "geral",
            "article": None,
            "grounding_status": "unverified",
            "sources": [],
            "guardrails": [],
        },
    )
    monkeypatch.setattr(
        "services.legal_ai_orchestrator.official_legal_sources.build_context",
        lambda retrieval: "",
    )

    result = await orchestrator.answer(
        user_message="Como classificar despesa de ISS no Simples Nacional?",
        user_id="3:default",
        response_mode="balanced",
    )

    assert result["legal_metadata"]["accounting_intent"] is True
    assert result["legal_metadata"]["professional_domain"] == "contabil_fiscal"
    assert "parecer vinculante" in (captured.get("system_context") or "").lower()
