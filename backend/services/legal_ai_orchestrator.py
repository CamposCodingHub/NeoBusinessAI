"""Orquestracao de respostas juridicas fundamentadas e verificaveis."""

from __future__ import annotations

import asyncio
import re
import time
import unicodedata
from typing import Any, Dict, Optional

from config import settings
from services.official_legal_sources_service import official_legal_sources
from services.official_realtime_research_service import (
    official_realtime_research,
)


RESPONSE_MODES = {
    "quick": {
        "label": "Consulta profissional rapida",
        "model": "llama-3.3-70b-versatile",
        "max_tokens": 700,
        "instruction": (
            "Responda em no maximo 450 palavras, mas inclua regra juridica, "
            "aplicacao, limite da resposta e fontes."
        ),
    },
    "balanced": {
        "label": "Analise profissional",
        "model": "llama-3.3-70b-versatile",
        "max_tokens": 1200,
        "instruction": (
            "Produza analise de no maximo 900 palavras, distinguindo texto legal, "
            "interpretacao, aplicacao pratica, riscos, teses alternativas e "
            "proximos passos. Evite repetir a mesma regra."
        ),
    },
    "deep": {
        "label": "Pesquisa profissional profunda",
        "model": "llama-3.3-70b-versatile",
        "max_tokens": 2600,
        "instruction": (
            "Atue como pesquisador senior juridico-contabil. Estruture a resposta em: "
            "questao apresentada, resposta executiva, fundamento normativo, "
            "analise detalhada, possiveis interpretacoes, riscos e controvesias, "
            "informacoes faltantes, estrategia de verificacao e conclusao. "
            "Nao trate hipotese como fato e nao invente jurisprudencia. Limite a "
            "resposta a 1.400 palavras e elimine repeticoes."
        ),
    },
}

CURATED_CLAIM_ARTICLE_RULES = (
    (
        (
            "prova da existencia do crime",
            "indicio suficiente de autoria",
            "perigo gerado pela liberdade",
            "perigo gerado pelo estado de liberdade",
        ),
        {"312"},
    ),
    (
        (
            "fatos novos ou contemporaneos",
            "decisao sempre motivada e fundamentada",
        ),
        {"315"},
    ),
    (
        ("probabilidade do direito", "perigo de dano"),
        {"300"},
    ),
    (
        ("30 dias para sanar o vicio",),
        {"18"},
    ),
    (
        ("30 dias para produto nao duravel", "90 dias para produto duravel"),
        {"26"},
    ),
    (
        ("cinco anos para reparacao",),
        {"27"},
    ),
)


class LegalAIOrchestrator:
    def __init__(self, conversational_engine, local_search=None):
        self.engine = conversational_engine
        self.local_search = local_search
        self._contingency_history: Dict[str, list[str]] = {}

    async def answer(
        self,
        user_message: str,
        user_id: str,
        document_context: str = "",
        response_mode: str = "balanced",
        jurisdiction: str = "Brasil - federal",
        legal_area: Optional[str] = None,
    ) -> Dict[str, Any]:
        started_at = time.perf_counter()
        contingency_history = self._remember_for_contingency(
            user_id,
            user_message,
        )
        mode = RESPONSE_MODES.get(response_mode, RESPONSE_MODES["balanced"])
        quick_document_evidence = (
            response_mode == "quick"
            and bool(document_context)
            and self._is_document_evidence_request(user_message)
        )
        retrieval = official_legal_sources.retrieve(user_message)
        if (
            document_context
            and not quick_document_evidence
            and self._should_use_document_for_retrieval(user_message, retrieval)
        ):
            contextual_retrieval = official_legal_sources.retrieve(
                f"{user_message}\nContexto tematico do documento:\n"
                f"{document_context[:4000]}"
            )
            if contextual_retrieval["sources"]:
                retrieval = contextual_retrieval
        if (
            legal_area
            and legal_area != "geral"
            and not retrieval["is_legal_query"]
            and self._is_legal_follow_up(user_message)
        ):
            retrieval = official_legal_sources.retrieve(
                f"{user_message}\nArea juridica em continuidade: {legal_area}"
            )
        detected_area = (
            str(retrieval["legal_area"])
            if retrieval["is_legal_query"]
            else legal_area or "geral"
        )
        context_budgets = {
            "quick": {
                "official_chars": 3200,
                "local_top_k": 3,
                "local_excerpt_chars": 600,
            },
            "balanced": {
                "official_chars": 4500,
                "local_top_k": 3,
                "local_excerpt_chars": 650,
            },
            "deep": {
                "official_chars": 7500,
                "local_top_k": 5,
                "local_excerpt_chars": 900,
            },
        }
        context_budget = context_budgets.get(
            response_mode,
            context_budgets["balanced"],
        )
        official_context = official_legal_sources.build_context(retrieval)[
            : context_budget["official_chars"]
        ]
        official_excerpt_text = "\n".join(
            str(source.get("excerpt") or "")
            for source in retrieval.get("sources", [])
        )
        requested_articles = list(
            self._extract_article_numbers_ordered(user_message)
        )
        related_articles = self._extract_article_headings_ordered(
            official_excerpt_text
        )
        local_article_order = list(
            dict.fromkeys([*requested_articles, *related_articles])
        )
        local_search_query = user_message
        if local_article_order:
            local_search_query += "\nDispositivos recuperados: " + " ".join(
                f"Art. {article}" for article in local_article_order
            )
        sovereign_results = []
        sovereign_context = ""
        if (
            self.local_search
            and response_mode != "quick"
            and not quick_document_evidence
        ):
            try:
                from database import SessionLocal

                db = SessionLocal()
                try:
                    numeric_user_id = int(str(user_id).split(":", 1)[0])
                    sovereign_search = await self.local_search.search(
                        db,
                        query=local_search_query,
                        top_k=max(
                            context_budget["local_top_k"] * 2,
                            len(local_article_order) + 2,
                        ),
                        legal_area=(
                            str(retrieval["legal_area"])
                            if retrieval["is_legal_query"]
                            else None
                        ),
                        user_id=numeric_user_id,
                        include_private=True,
                    )
                    sovereign_results = self._prioritize_local_articles(
                        sovereign_search["results"],
                        local_article_order,
                    )[: context_budget["local_top_k"]]
                    sovereign_context = self.local_search.build_context(
                        sovereign_results,
                        max_excerpt_chars=context_budget[
                            "local_excerpt_chars"
                        ],
                    )
                finally:
                    db.close()
            except Exception:
                sovereign_results = []
                sovereign_context = ""
        legal_query = bool(retrieval["is_legal_query"])
        accounting_areas = {
            "contabil",
            "contabil_fiscal",
            "trabalhista_previdenciario",
            "tributario_reforma_consumo",
        }
        selected_areas = {
            str(source.get("legal_area") or "")
            for source in retrieval.get("sources", [])
        }
        has_accounting_area = bool(selected_areas & accounting_areas)
        has_legal_area = bool(
            selected_areas
            and any(area not in accounting_areas for area in selected_areas)
        )
        professional_domain = (
            "juridico_contabil"
            if has_accounting_area and has_legal_area
            else "contabil_fiscal"
            if detected_area in accounting_areas
            else "juridico"
            if legal_query
            else "geral"
        )
        realtime_research = {
            "used": False,
            "status": "not_requested",
            "results": [],
            "retrieved_at": None,
            "latency_ms": 0,
            "cache_hit": False,
            "errors": [],
        }
        if (
            settings.AI_REALTIME_OFFICIAL_SEARCH_ENABLED
            and legal_query
            and official_realtime_research.should_research(user_message)
        ):
            try:
                realtime_research = await asyncio.to_thread(
                    official_realtime_research.search,
                    user_message,
                    settings.AI_REALTIME_OFFICIAL_SEARCH_MAX_RESULTS,
                )
            except Exception as exc:
                realtime_research = {
                    **realtime_research,
                    "status": "error",
                    "errors": [str(exc)[:300]],
                }
        realtime_results = list(realtime_research.get("results") or [])
        realtime_context = self._build_realtime_context(realtime_results)

        system_context = ""
        if legal_query:
            system_context = f"""
MODO DE TRABALHO PROFISSIONAL: {mode['label']}
JURISDICAO INFORMADA: {jurisdiction}
AREA DETECTADA: {detected_area}
DOMINIO PROFISSIONAL: {professional_domain}
DATA DE REFERENCIA: use somente o texto e as fontes fornecidas nesta execucao.

{mode['instruction']}

REGRAS DE CONFIABILIDADE:
- As REGRAS FACTUAIS CURADAS prevalecem sobre qualquer memoria do modelo.
- Comece pela regra curada aplicavel e nao a contradiga na analise posterior.
- Cite as fontes fornecidas usando [Fonte 1], [Fonte 2] etc.
- Nao invente numero de processo, sumula, precedente, artigo ou teor de decisao.
- So associe paragrafo a artigo quando essa associacao aparecer literalmente no trecho fornecido.
- Se uma conclusao depender de jurisprudencia nao recuperada, diga isso claramente.
- Diferencie texto legal ou normativo, orientacao oficial, interpretacao e recomendacao estrategica.
- Indique fatos faltantes que podem mudar a conclusao.
- Em materia contabil ou fiscal, nao invente aliquota, prazo, leiaute ou obrigacao.
- Informe que a resposta auxilia o trabalho profissional e requer revisao do advogado ou contador responsavel.

FONTES OFICIAIS DISPONIVEIS:
{official_context or 'Nenhuma fonte oficial foi recuperada. Assuma postura conservadora e solicite pesquisa complementar.'}

BASE JURIDICA SOBERANA LOCAL:
{sovereign_context or 'Nenhum trecho adicional foi recuperado da base local.'}

PESQUISA OFICIAL CONSULTADA AGORA:
{realtime_context or 'Pesquisa em tempo real nao solicitada ou sem resultado oficial verificavel.'}
""".strip()

        guardrails = retrieval.get("guardrails", [])
        selected_model = (
            mode["model"] if legal_query else "llama-3.1-8b-instant"
        )
        max_tokens = mode["max_tokens"] if legal_query else 1400
        if response_mode == "quick" and realtime_results:
            result = self._build_verified_realtime_result(
                realtime_results=realtime_results,
                document_context=document_context,
                latency_ms=int(
                    (time.perf_counter() - started_at) * 1000
                ),
            )
        elif quick_document_evidence:
            result = self._build_verified_document_result(
                user_message=user_message,
                document_context=document_context,
                latency_ms=int(
                    (time.perf_counter() - started_at) * 1000
                ),
            )
        elif (
            response_mode == "quick"
            and legal_query
            and guardrails
        ):
            result = self._build_verified_quick_result(
                document_context=document_context,
                latency_ms=int(
                    (time.perf_counter() - started_at) * 1000
                ),
            )
        else:
            result = await self.engine.generate_premium_response(
                user_message=user_message,
                user_id=user_id,
                document_context=document_context,
                response_mode=response_mode,
                model_name=selected_model,
                max_tokens=max_tokens,
                system_context=system_context,
                preserve_structure=legal_query,
            )

        full_official_text = "\n".join(
            str(source.get("excerpt") or "")
            for source in retrieval["sources"]
        )
        sources = [
            {
                "code": source["code"],
                "title": source["title"],
                "url": source["url"],
                "status": source["status"],
                "excerpt": str(source.get("excerpt") or "")[:1800],
            }
            for source in retrieval["sources"]
        ]
        response_before_source_index = str(result.get("response") or "")
        engine_metadata = result.get("metadata") or {}
        actual_model = engine_metadata.get("actual_model", selected_model)
        actual_provider = engine_metadata.get("provider", "unknown")
        guardrails = retrieval.get("guardrails", [])
        contingency_mode = legal_query and actual_model == "unavailable"
        if contingency_mode:
            response_before_source_index = self._build_grounded_contingency_response(
                user_message=user_message,
                retrieval=retrieval,
                detected_area=detected_area,
                professional_domain=professional_domain,
                recent_history=contingency_history,
                document_context=document_context,
            )
        prompt_leak_blocked = self._contains_internal_instruction_leak(
            response_before_source_index
        )
        if prompt_leak_blocked:
            response_before_source_index = self._build_safe_leak_response(
                guardrails,
                sources,
            )
        (
            response_before_source_index,
            suppressed_jurisprudence_lines,
        ) = self._suppress_unverified_jurisprudence_claims(
            response_before_source_index,
            retrieval,
        )
        (
            response_before_source_index,
            suppressed_paragraph_lines,
        ) = self._suppress_mismatched_paragraph_claims(
            response_before_source_index,
            full_official_text,
        )
        (
            response_before_source_index,
            suppressed_curated_claim_lines,
        ) = self._suppress_mismatched_curated_claims(
            response_before_source_index,
        )
        if legal_query and guardrails and actual_model != "unavailable":
            response_before_source_index = (
                "## Base normativa verificada\n\n"
                + "\n".join(
                    f"- {guardrail} [Fonte 1]"
                    for guardrail in guardrails
                )
                + "\n\n## Analise complementar\n\n"
                + response_before_source_index.lstrip()
            )
        if suppressed_paragraph_lines:
            response_before_source_index = (
                f"{response_before_source_index.rstrip()}\n\n"
                "## Auditoria de dispositivos\n\n"
                f"A Lex suprimiu {suppressed_paragraph_lines} trecho(s) que "
                "associavam paragrafo a artigo sem suporte literal nos textos "
                "recuperados."
            )
        if suppressed_curated_claim_lines:
            response_before_source_index = (
                f"{response_before_source_index.rstrip()}\n\n"
                "## Auditoria de associacoes normativas\n\n"
                f"A Lex suprimiu {suppressed_curated_claim_lines} trecho(s) "
                "que atribuiam conceito juridico curado ao artigo incorreto."
            )
        (
            response_before_source_index,
            suppressed_invalid_realtime_lines,
        ) = self._suppress_invalid_realtime_markers(
            response_before_source_index,
            source_count=len(realtime_results),
        )
        if suppressed_invalid_realtime_lines:
            response_before_source_index = (
                f"{response_before_source_index.rstrip()}\n\n"
                "## Auditoria de pesquisa atual\n\n"
                f"A Lex suprimiu {suppressed_invalid_realtime_lines} trecho(s) "
                "com marcador de atualizacao inexistente."
            )
        (
            response_before_source_index,
            suppressed_invalid_source_lines,
        ) = self._suppress_invalid_source_markers(
            response_before_source_index,
            source_count=len(sources),
        )
        if suppressed_invalid_source_lines:
            response_before_source_index = (
                f"{response_before_source_index.rstrip()}\n\n"
                "## Auditoria de fontes\n\n"
                f"A Lex suprimiu {suppressed_invalid_source_lines} trecho(s) "
                "com marcador de fonte inexistente no indice desta resposta."
            )
        response_articles = self._extract_article_numbers(
            response_before_source_index
        )
        verified_articles = self._extract_article_headings(
            full_official_text
        )
        detected_unverified_references = sorted(
            response_articles - verified_articles,
            key=lambda value: int(re.match(r"\d+", value).group()),
        )
        suppressed_line_count = 0
        if legal_query and detected_unverified_references:
            (
                response_before_source_index,
                suppressed_line_count,
            ) = self._suppress_unverified_article_lines(
                response_before_source_index,
                detected_unverified_references,
            )
            references = ", ".join(
                detected_unverified_references
            )
            response_before_source_index = (
                f"{response_before_source_index.rstrip()}\n\n"
                "## Auditoria automatica de fundamentacao\n\n"
                f"A Lex suprimiu {suppressed_line_count} trecho(s) que mencionavam "
                f"referencias numericas nao recuperadas ({references}). Consulte o "
                "texto integral antes de reintroduzir essas afirmacoes."
            )
        source_markers = len(
            re.findall(
                r"(?:\[|\()?Fonte\s+\d+(?:\]|\))?",
                response_before_source_index,
                re.IGNORECASE,
            )
        )
        realtime_markers = len(
            re.findall(
                r"(?:\[|\()?Atual\s+\d+(?:\]|\))?",
                response_before_source_index,
                re.IGNORECASE,
            )
        )
        response_articles = self._extract_article_numbers(
            response_before_source_index
        )
        verified_article_citations = response_articles & verified_articles
        inline_citations = (
            source_markers
            + realtime_markers
            + len(verified_article_citations)
        )
        unverified_article_references = sorted(
            response_articles - verified_articles,
            key=lambda value: int(re.match(r"\d+", value).group()),
        )
        result["response"] = response_before_source_index
        if legal_query and sources:
            result["response"] = self._ensure_official_source_index(
                response_before_source_index,
                sources,
            )
        if realtime_results:
            result["response"] = self._ensure_realtime_source_index(
                result["response"],
                realtime_results,
                realtime_research.get("retrieved_at"),
            )
        response_complete = bool(
            engine_metadata.get("response_complete", True)
        )
        local_legal_models = {
            settings.LOCAL_AI_FAST_MODEL,
            settings.LOCAL_AI_QUICK_MODEL,
            settings.LOCAL_AI_BALANCED_MODEL,
            settings.LOCAL_AI_DEEP_MODEL,
            "lex-retrieval-verificada",
            "lex-document-retrieval",
            "lex-realtime-verificada",
        }
        approved_legal_models = {
            selected_model,
            "openai/gpt-oss-120b",
            *local_legal_models,
        }
        model_degraded = (
            legal_query and actual_model not in approved_legal_models
        )
        model_fallback_used = (
            legal_query
            and actual_model in approved_legal_models
            and actual_model != selected_model
            and actual_model not in local_legal_models
        )
        confidence_level = (
            "alto_para_texto_normativo"
            if (
                retrieval["grounding_status"] == "official_sources"
                and inline_citations >= 2
                and not model_degraded
                and response_complete
            )
            else "moderado_requer_verificacao"
            if legal_query
            else "geral"
        )
        result["legal_metadata"] = {
            "is_legal_query": legal_query,
            "is_professional_query": legal_query,
            "legal_area": detected_area,
            "professional_domain": professional_domain,
            "jurisdiction": jurisdiction,
            "response_mode": response_mode,
            "model": actual_model,
            "requested_model": selected_model,
            "provider": actual_provider,
            "route": engine_metadata.get("route", ""),
            "usage": engine_metadata.get("usage", {}),
            "latency_ms": engine_metadata.get("latency_ms", 0),
            "provider_fallback_used": engine_metadata.get(
                "provider_fallback_used",
                False,
            ),
            "model_degraded": model_degraded,
            "model_fallback_used": model_fallback_used,
            "grounding_status": retrieval["grounding_status"],
            "sources": sources,
            "sovereign_sources": sovereign_results,
            "sovereign_search_used": bool(sovereign_results),
            "realtime_web_used": bool(realtime_results),
            "realtime_web_status": realtime_research.get("status"),
            "realtime_retrieved_at": realtime_research.get("retrieved_at"),
            "realtime_latency_ms": realtime_research.get("latency_ms", 0),
            "realtime_cache_hit": bool(realtime_research.get("cache_hit")),
            "realtime_sources": realtime_results,
            "realtime_errors": realtime_research.get("errors") or [],
            "inline_citations": inline_citations,
            "source_markers": source_markers,
            "realtime_markers": realtime_markers,
            "verified_article_citations": sorted(
                verified_article_citations,
                key=lambda value: int(re.match(r"\d+", value).group()),
            ),
            "verified_articles": sorted(
                verified_articles,
                key=lambda value: int(re.match(r"\d+", value).group()),
            ),
            "unverified_article_references": unverified_article_references,
            "suppressed_article_references": detected_unverified_references,
            "suppressed_unsupported_lines": suppressed_line_count,
            "suppressed_unsupported_jurisprudence_lines": (
                suppressed_jurisprudence_lines
            ),
            "suppressed_mismatched_paragraph_lines": (
                suppressed_paragraph_lines
            ),
            "suppressed_mismatched_curated_claim_lines": (
                suppressed_curated_claim_lines
            ),
            "suppressed_invalid_source_lines": (
                suppressed_invalid_source_lines
            ),
            "suppressed_invalid_realtime_lines": (
                suppressed_invalid_realtime_lines
            ),
            "prompt_leak_blocked": prompt_leak_blocked,
            "citation_quality": (
                "claim_level"
                if inline_citations >= 2
                else "source_index_only"
                if sources
                else "none"
            ),
            "confidence_level": confidence_level,
            "response_complete": response_complete,
            "finish_reason": engine_metadata.get("finish_reason", "stop"),
            "requires_human_review": legal_query,
            "review_role": (
                "advogado_e_contador_responsaveis"
                if professional_domain == "juridico_contabil"
                else
                "contador_responsavel"
                if professional_domain == "contabil_fiscal"
                else "advogado_responsavel"
                if professional_domain == "juridico"
                else "usuario"
            ),
            "answer_scope": (
                "fundamentada_em_fontes_oficiais"
                if retrieval["grounding_status"] == "official_sources"
                else "orientacao_geral_com_links_oficiais"
                if legal_query
                else "assistencia_geral"
            ),
            "contingency_mode": contingency_mode,
        }
        return result

    @staticmethod
    def _build_verified_quick_result(
        *,
        document_context: str,
        latency_ms: int,
    ) -> Dict[str, Any]:
        document_note = (
            "O documento selecionado deve ser confrontado com a regra acima; "
            "nenhuma afirmacao do arquivo substitui o texto oficial."
            if document_context
            else (
                "A aplicacao ao caso concreto depende da cronologia, das provas "
                "e dos fatos ainda nao informados."
            )
        )
        return {
            "response": (
                "## Aplicacao objetiva\n\n"
                f"{document_note}\n\n"
                "## Limites da resposta\n\n"
                "Esta consulta rapida usa somente regras curadas e trechos "
                "oficiais recuperados. Nao confirma jurisprudencia, estrategia "
                "processual especifica nem fatos do caso. Submeta prazo, medida "
                "e conclusao ao profissional responsavel."
            ),
            "quality_score": 100,
            "style": "verified_retrieval",
            "detected_intent": "legal_research",
            "emotional_state": "neutral",
            "context_summary": "Resposta juridica rapida verificada por recuperacao.",
            "metadata": {
                "interaction_count": 1,
                "response_length": 0,
                "response_mode": "quick",
                "model": "lex-retrieval-verificada",
                "actual_model": "lex-retrieval-verificada",
                "model_degraded": False,
                "finish_reason": "stop",
                "response_complete": True,
                "preserve_structure": True,
                "provider": "local-knowledge-engine",
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
                "route": "quick_verified",
                "provider_fallback_used": False,
                "latency_ms": latency_ms,
            },
        }

    @classmethod
    def _build_verified_document_result(
        cls,
        *,
        user_message: str,
        document_context: str,
        latency_ms: int,
    ) -> Dict[str, Any]:
        sections = [
            section.strip()
            for section in document_context.split("--- PROXIMO ARQUIVO ---")
            if section.strip()
        ]
        normalized_query = cls._normalize_for_guard(user_message)
        requested_fields = []
        if any(term in normalized_query for term in ("resum", "sintese", "visao geral")):
            requested_fields.append("RESUMO")
        if any(term in normalized_query for term in ("parte", "contratante", "contratada")):
            requested_fields.append("PARTES")
        if any(term in normalized_query for term in ("prazo", "venc", "vigencia")):
            requested_fields.append("PRAZOS")
        if any(term in normalized_query for term in ("valor", "multa", "financeir")):
            requested_fields.append("VALORES")
        if any(term in normalized_query for term in ("risco", "problema", "atencao")):
            requested_fields.append("ANALISE")
        if not requested_fields:
            requested_fields = ["RESUMO", "ANALISE", "PRAZOS", "VALORES"]

        document_blocks = []
        for section in sections:
            name_match = re.search(r"(?m)^ARQUIVO:\s*(.+)$", section)
            name = name_match.group(1).strip() if name_match else "Documento"
            lines = [f"### {name}"]
            for field in requested_fields:
                match = re.search(
                    rf"(?ms)^{re.escape(field)}:\s*(.*?)(?=^[A-Z ]+:|\Z)",
                    section,
                )
                if not match:
                    continue
                value = match.group(1).strip()
                if value and value not in {"{}", "[]", "Nao informado", "Nao informada"}:
                    lines.append(f"**{field.title()}:** {value[:1800]}")
            if len(lines) == 1:
                lines.append(
                    "Nenhuma evidencia estruturada correspondente foi encontrada."
                )
            document_blocks.append("\n\n".join(lines))

        response = (
            "## Evidencias dos documentos selecionados\n\n"
            + "\n\n".join(document_blocks)
            + "\n\n## Limites\n\n"
            "A resposta acima reproduz somente dados extraidos e persistidos dos "
            "arquivos selecionados. Interpretacoes juridicas, calculos e conclusoes "
            "devem ser solicitados separadamente e revisados pelo profissional."
        )
        return cls._retrieval_result(
            response=response,
            model="lex-document-retrieval",
            provider="local-document-engine",
            route="quick_document_verified",
            style="verified_document_retrieval",
            latency_ms=latency_ms,
        )

    @classmethod
    def _build_verified_realtime_result(
        cls,
        *,
        realtime_results: list[Dict[str, Any]],
        document_context: str,
        latency_ms: int,
    ) -> Dict[str, Any]:
        blocks = []
        for index, source in enumerate(realtime_results, start=1):
            date = source.get("updated_at") or source.get("published_at")
            excerpt = re.sub(
                r"\s+",
                " ",
                str(source.get("excerpt") or ""),
            ).strip()
            blocks.append(
                "\n".join(
                    [
                        f"### {source.get('title')} [Atual {index}]",
                        f"- Autoridade: {source.get('authority')}",
                        f"- Data oficial encontrada: {date or 'nao informada'}",
                        f"- Evidencia: {excerpt[:700]}",
                    ]
                )
            )
        context_note = (
            "\n\nOs documentos privados selecionados nao foram enviados a nenhum "
            "servico externo; permanecem apenas no processamento local."
            if document_context
            else ""
        )
        response = (
            "## Atualizacoes oficiais recuperadas em tempo real\n\n"
            + "\n\n".join(blocks)
            + context_note
            + "\n\n## Limites\n\n"
            "Os itens acima registram o conteudo recuperado agora nas paginas "
            "oficiais. Antes de adotar uma medida, confira a vigencia, o texto "
            "integral e a aplicacao ao caso concreto."
        )
        return cls._retrieval_result(
            response=response,
            model="lex-realtime-verificada",
            provider="official-web-local-synthesis",
            route="quick_realtime_verified",
            style="verified_realtime_retrieval",
            latency_ms=latency_ms,
        )

    @staticmethod
    def _retrieval_result(
        *,
        response: str,
        model: str,
        provider: str,
        route: str,
        style: str,
        latency_ms: int,
    ) -> Dict[str, Any]:
        return {
            "response": response,
            "quality_score": 100,
            "style": style,
            "detected_intent": "evidence_retrieval",
            "emotional_state": "neutral",
            "context_summary": "Resposta verificavel produzida por recuperacao local.",
            "metadata": {
                "interaction_count": 1,
                "response_length": len(response),
                "response_mode": "quick",
                "model": model,
                "actual_model": model,
                "model_degraded": False,
                "finish_reason": "stop",
                "response_complete": True,
                "preserve_structure": True,
                "provider": provider,
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
                "route": route,
                "provider_fallback_used": False,
                "latency_ms": latency_ms,
            },
        }

    @staticmethod
    def _build_realtime_context(
        sources: list[Dict[str, Any]],
    ) -> str:
        blocks = []
        for index, source in enumerate(sources, start=1):
            blocks.append(
                "\n".join(
                    [
                        f"[Atual {index}] {source.get('title')}",
                        f"Autoridade: {source.get('authority')}",
                        f"URL oficial: {source.get('url')}",
                        (
                            "Publicado/atualizado: "
                            f"{source.get('updated_at') or source.get('published_at') or 'nao informado'}"
                        ),
                        f"Trecho consultado agora:\n{source.get('excerpt') or ''}",
                    ]
                )
            )
        return "\n\n".join(blocks)

    def _remember_for_contingency(
        self,
        user_id: str,
        message: str,
    ) -> list[str]:
        history = self._contingency_history.setdefault(user_id, [])
        history.append(message[:3000])
        if len(history) > 8:
            del history[:-8]
        return list(history)

    @staticmethod
    def _build_grounded_contingency_response(
        user_message: str,
        retrieval: Dict[str, Any],
        detected_area: str,
        professional_domain: str,
        recent_history: list[str],
        document_context: str,
    ) -> str:
        sources = retrieval.get("sources", [])
        source_sections = []
        for index, source in enumerate(sources[:4], start=1):
            excerpt = re.sub(
                r"\s+",
                " ",
                str(source.get("excerpt") or ""),
            ).strip()
            if excerpt:
                source_sections.append(
                    f"### Evidencia oficial {index} [Fonte {index}]\n\n"
                    f"{excerpt[:1600]}"
                )
            else:
                source_sections.append(
                    f"### Referencia oficial {index} [Fonte {index}]\n\n"
                    "O texto nao foi recuperado nesta execucao. A verificacao "
                    "deve ser feita diretamente no link oficial."
                )

        guardrails = retrieval.get("guardrails", [])
        guardrail_lines = (
            "\n".join(f"- {item}" for item in guardrails)
            if guardrails
            else (
                "- Nao transformar hipotese em fato.\n"
                "- Nao inventar prazo, aliquota, artigo, obrigacao ou precedente.\n"
                "- Conferir o texto integral e a vigencia na fonte oficial."
            )
        )

        recent_context = (
            [recent_history[0], *recent_history[-5:]]
            if len(recent_history) > 6
            else recent_history
        )
        context_lines = "\n".join(
            f"- {message[:700]}" for message in recent_context
        )
        if document_context:
            context_lines += (
                "\n- Contexto documental conectado: "
                + re.sub(r"\s+", " ", document_context[:1200]).strip()
            )

        normalized_question = LegalAIOrchestrator._normalize_for_guard(
            user_message
        )
        if "raci" in normalized_question:
            checklist = (
                "| Atividade | Advogado | Contador | RH | Diretoria |\n"
                "|---|---|---|---|---|\n"
                "| Definir fundamento e risco juridico | R/A | C | C | I |\n"
                "| Validar reflexos contabeis e fiscais | C | R/A | C | I |\n"
                "| Conferir cadastro, eventos e documentos | C | C | R/A | I |\n"
                "| Aprovar alternativa e risco residual | C | C | C | R/A |\n"
                "| Executar dupla verificacao final | A | A | R | I |\n\n"
                "Legenda: R responsavel pela execucao; A aprovador; C consultado; "
                "I informado."
            )
        elif professional_domain == "contabil_fiscal":
            checklist = (
                "- Confirmar CNPJ/CPF, periodo de apuracao, regime tributario e "
                "estabelecimento afetado.\n"
                "- Conferir recibos, eventos transmitidos, totalizadores, guias, "
                "livros e conciliacoes antes de retificar.\n"
                "- Comparar origem contabil, folha, documento fiscal e declaracao "
                "para localizar a primeira divergencia.\n"
                "- Registrar evidencia, responsavel, data, versao do leiaute e "
                "efeito financeiro de cada ajuste.\n"
                "- Submeter enquadramento, prazo e transmissao ao contador responsavel."
            )
        elif professional_domain == "juridico_contabil":
            checklist = (
                "- Advogado: delimitar fundamento, risco, prova e decisao juridica.\n"
                "- Contador: validar reflexos contabeis, fiscais, previdenciarios e guias.\n"
                "- RH/operacao: conferir cadastro, datas, eventos e documentos de suporte.\n"
                "- Diretoria: aprovar alternativa, risco residual e alocacao de responsavel.\n"
                "- Manter uma unica linha do tempo e dupla verificacao antes da execucao."
            )
        else:
            checklist = (
                "- Delimitar fatos incontroversos, fatos alegados e fatos ainda sem prova.\n"
                "- Confirmar competencia, procedimento, datas de ciencia e forma de contagem.\n"
                "- Separar texto normativo, interpretacao e estrategia do caso concreto.\n"
                "- Pesquisar jurisprudencia somente em resultado oficial recuperado.\n"
                "- Submeter tese, prazo e medida ao advogado responsavel."
            )

        return (
            "## Contingencia profissional fundamentada\n\n"
            "O modelo generativo especializado esta temporariamente indisponivel. "
            "Para nao entregar uma resposta curta ou inventada, a Lex montou abaixo "
            "um dossie deterministico a partir das fontes oficiais recuperadas. "
            "Nenhuma conclusao individualizada foi presumida.\n\n"
            f"**Area detectada:** {detected_area}\n\n"
            f"**Dominio:** {professional_domain}\n\n"
            f"**Pergunta atual:** {user_message}\n\n"
            "## Contexto recente informado pelo usuario\n\n"
            f"{context_lines or '- Nenhum contexto anterior disponivel.'}\n\n"
            "## Controles factuais\n\n"
            f"{guardrail_lines}\n\n"
            + "\n\n".join(source_sections)
            + "\n\n## Checklist de verificacao e execucao\n\n"
            f"{checklist}\n\n"
            "## Informacoes que podem mudar a orientacao\n\n"
            "- Datas exatas, recibos, documentos integrais e versoes transmitidas.\n"
            "- Regime aplicavel, jurisdicao, periodo, partes e eventos posteriores.\n"
            "- Existencia de decisao, regulamentacao ou orientacao oficial mais recente.\n"
            "- Divergencias entre o relato, o sistema oficial e a documentacao suporte.\n\n"
            "## Proximo passo seguro\n\n"
            "Use os trechos e links oficiais abaixo para validar cada premissa. "
            "Depois, o advogado ou contador responsavel deve registrar a conclusao, "
            "o fundamento, a evidencia usada e o responsavel pela execucao."
        )

    @staticmethod
    def _normalize_for_guard(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value or "")
        return "".join(
            character
            for character in normalized
            if not unicodedata.combining(character)
        ).lower()

    @classmethod
    def _contains_internal_instruction_leak(cls, response: str) -> bool:
        normalized = cls._normalize_for_guard(response)
        markers = (
            "ordem de prioridade:",
            "regras obrigatorias:",
            "instrucoes especializadas desta execucao",
            "regras e fontes oficiais desta execucao",
            "dados do documento do usuario:",
        )
        return any(marker in normalized for marker in markers)

    @staticmethod
    def _build_safe_leak_response(
        guardrails: list[str],
        sources: list[Dict[str, Any]],
    ) -> str:
        grounded_points = "\n".join(
            f"- {guardrail} [Fonte 1]"
            for guardrail in guardrails
        )
        if not grounded_points:
            grounded_points = (
                "- A consulta deve ser respondida somente a partir das fontes "
                "oficiais recuperadas, sem expor configuracoes internas."
            )
        source_scope = (
            f"Foram recuperadas {len(sources)} fonte(s) oficial(is) para "
            "verificacao."
            if sources
            else "Nenhuma fonte oficial suficiente foi recuperada."
        )
        return (
            "## Protecao de seguranca\n\n"
            "Nao forneco configuracoes internas, instrucoes reservadas ou "
            "detalhes operacionais do sistema. O pedido de extracao foi bloqueado "
            "e nao altera a analise juridica.\n\n"
            "## Resposta juridica segura\n\n"
            f"{grounded_points}\n\n"
            "A aplicacao ao caso concreto depende dos fatos, das provas e da "
            "jurisprudencia efetivamente pesquisada. Nao se deve transformar "
            "hipotese em conclusao nem atribuir a tribunais entendimentos que nao "
            "tenham sido recuperados nesta consulta.\n\n"
            "## Verificacao recomendada\n\n"
            f"{source_scope} Confira o texto integral, delimite a pergunta "
            "juridica e submeta a conclusao a revisao do advogado responsavel."
        )

    @classmethod
    def _suppress_unverified_jurisprudence_claims(
        cls,
        response: str,
        retrieval: Dict[str, Any],
    ) -> tuple[str, int]:
        sources = retrieval.get("sources", [])
        has_unverified_jurisprudence = any(
            source.get("source_type") == "jurisprudence_portal"
            and source.get("status") != "official_text"
            for source in sources
        )
        if not has_unverified_jurisprudence:
            return response, 0

        claim_patterns = (
            r"\bjurisprudencia\s+(?:do|da|de)\s+\w+.*\b"
            r"(?:estabelece|decidiu|entende|firmou|tem decidido)\b",
            r"\b(?:stj|stf|tst)\s+.*\b"
            r"(?:estabelece|decidiu|entende|firmou|tem decidido)\b",
        )
        safe_markers = (
            "nao verificado",
            "nao e possivel confirmar",
            "nao foi localizado",
            "parece ser ficticio",
        )
        retained_lines = []
        suppressed = 0
        for line in response.splitlines():
            normalized = cls._normalize_for_guard(line)
            unsupported_claim = any(
                re.search(pattern, normalized)
                for pattern in claim_patterns
            )
            explicitly_cautious = any(
                marker in normalized for marker in safe_markers
            )
            if unsupported_claim and not explicitly_cautious:
                suppressed += 1
                continue
            retained_lines.append(line)

        if not suppressed:
            return response, 0

        audited_response = "\n".join(retained_lines).strip()
        audited_response += (
            "\n\n## Auditoria de jurisprudencia\n\n"
            f"A Lex suprimiu {suppressed} trecho(s) que atribuiam entendimento "
            "a tribunal sem decisao ou ementa recuperada. Consulte a pesquisa "
            "oficial antes de formular a tese."
        )
        return audited_response, suppressed

    @staticmethod
    def _should_use_document_for_retrieval(
        user_message: str,
        retrieval: Dict[str, Any],
    ) -> bool:
        source_codes = {
            source.get("code")
            for source in retrieval.get("sources", [])
        }
        normalized_message = user_message.lower()
        document_reference = any(
            term in normalized_message
            for term in (
                "documento",
                "contrato anexado",
                "texto anexado",
                "arquivo",
            )
        )
        generic_sources = source_codes.issubset({"CF88", "CPC", "STJ"})
        return not source_codes or (document_reference and generic_sources)

    @staticmethod
    def _is_document_evidence_request(message: str) -> bool:
        normalized = LegalAIOrchestrator._normalize_for_guard(message)
        return any(
            marker in normalized
            for marker in (
                "documento",
                "arquivo",
                "contrato selecionado",
                "resuma",
                "resumo",
                "sintese",
                "partes",
                "prazos",
                "valores",
                "riscos dos arquivos",
            )
        )

    @staticmethod
    def _extract_article_numbers(text: str) -> set[str]:
        return {
            match.group(1).lower()
            for match in re.finditer(
                r"\bart(?:igo)?\.?\s*(\d+[a-z]?(?:-[a-z])?)",
                text,
                re.IGNORECASE,
            )
        }

    @staticmethod
    def _extract_article_headings(text: str) -> set[str]:
        return {
            match.group(1).lower()
            for match in re.finditer(
                r"(?im)^[ \t]*Art\.?[ \t]*"
                r"(\d+[a-z]?(?:-[a-z])?)"
                r"(?=[ \t]*(?:[.\-–—ºo]|$))",
                text,
            )
        }

    @staticmethod
    def _extract_article_numbers_ordered(text: str) -> list[str]:
        return list(
            dict.fromkeys(
                match.group(1).lower()
                for match in re.finditer(
                    r"\bart(?:igo)?\.?\s*(\d+[a-z]?(?:-[a-z])?)",
                    text,
                    re.IGNORECASE,
                )
            )
        )

    @staticmethod
    def _extract_article_headings_ordered(text: str) -> list[str]:
        return list(
            dict.fromkeys(
                match.group(1).lower()
                for match in re.finditer(
                    r"(?im)^[ \t]*Art\.?[ \t]*"
                    r"(\d+[a-z]?(?:-[a-z])?)"
                    r"(?=[ \t]*(?:[.\-–—ºo]|$))",
                    text,
                )
            )
        )

    @classmethod
    def _prioritize_local_articles(
        cls,
        results: list[Dict[str, Any]],
        article_order: list[str],
    ) -> list[Dict[str, Any]]:
        priorities = {
            article: index for index, article in enumerate(article_order)
        }

        def priority(item: Dict[str, Any]):
            citation_articles = cls._extract_article_numbers_ordered(
                str(item.get("citation") or "")
            )
            rank = min(
                (
                    priorities[article]
                    for article in citation_articles
                    if article in priorities
                ),
                default=len(priorities) + 1,
            )
            return rank, -float(item.get("score") or 0)

        return sorted(results, key=priority)

    @staticmethod
    def _is_legal_follow_up(message: str) -> bool:
        normalized = message.lower()
        return any(
            re.search(pattern, normalized)
            for pattern in (
                r"\bart(?:igo)?\.?\s*\d*",
                r"\bprazo\b",
                r"\blei\b",
                r"\bcodigo\b",
                r"\brequisit\w*",
                r"\bresponsabil\w*",
                r"\bprescri\w*",
                r"\bdecaden\w*",
                r"\brecurso\b",
                r"\bpena\b",
                r"\bprisao\b",
                r"\btutela\b",
                r"\bvicio\b",
                r"\bcontrato\b",
                r"\bclausula\b",
                r"\bdctfweb\b",
                r"\besocial\b",
                r"\bcontab\w*",
                r"\bfiscal\w*",
                r"\btribut\w*",
                r"\bdeclar\w*",
                r"\bescritur\w*",
                r"\bibs\b",
                r"\bcbs\b",
            )
        )

    @staticmethod
    def _suppress_unverified_article_lines(
        response: str,
        article_references: list[str],
    ) -> tuple[str, int]:
        patterns = [
            re.compile(
                rf"\bart(?:igo)?\.?\s*{re.escape(article)}(?:\D|$)",
                re.IGNORECASE,
            )
            for article in article_references
        ]
        retained_lines = []
        suppressed = 0
        for line in response.splitlines():
            if any(pattern.search(line) for pattern in patterns):
                suppressed += 1
                continue
            retained_lines.append(line)
        return "\n".join(retained_lines).strip(), suppressed

    @classmethod
    def _suppress_mismatched_paragraph_claims(
        cls,
        response: str,
        official_text: str,
    ) -> tuple[str, int]:
        article_blocks = list(
            re.finditer(
                r"(?im)^[ \t]*Art\.?[ \t]*"
                r"(?P<article>\d+[a-z]?(?:-[a-z])?)"
                r"(?=[ \t]*(?:[.\-–—ºo]|$))",
                official_text,
            )
        )
        verified: Dict[str, set[str]] = {}
        for index, match in enumerate(article_blocks):
            end = (
                article_blocks[index + 1].start()
                if index + 1 < len(article_blocks)
                else len(official_text)
            )
            block = official_text[match.start() : end]
            verified[match.group("article").lower()] = set(
                re.findall(r"§{1,2}\s*(\d+)", block)
            )

        if not verified:
            return response, 0

        retained_lines = []
        suppressed = 0
        last_article = ""
        for line in response.splitlines():
            explicit_articles = list(
                re.finditer(
                    r"\bart(?:igo)?\.?\s*(\d+[a-z]?(?:-[a-z])?)",
                    line,
                    re.IGNORECASE,
                )
            )
            target_article = (
                explicit_articles[-1].group(1).lower()
                if explicit_articles
                else last_article
                if re.search(r"\bmesmo artigo\b", line, re.IGNORECASE)
                else ""
            )
            paragraph_segment = (
                line[: explicit_articles[-1].start()]
                if explicit_articles
                else line
            )
            paragraph_numbers = set(
                re.findall(r"§{1,2}\s*(\d+)", paragraph_segment)
            )
            if "§§" in paragraph_segment:
                paragraph_numbers.update(
                    re.findall(r"\b(\d+)\s*[ºo]?", paragraph_segment)
                )

            invalid_association = (
                target_article in verified
                and paragraph_numbers
                and not paragraph_numbers.issubset(verified[target_article])
            )
            if invalid_association:
                suppressed += 1
            else:
                retained_lines.append(line)

            if explicit_articles:
                last_article = explicit_articles[-1].group(1).lower()

        return "\n".join(retained_lines).strip(), suppressed

    @staticmethod
    def _suppress_invalid_source_markers(
        response: str,
        *,
        source_count: int,
    ) -> tuple[str, int]:
        retained_lines = []
        suppressed = 0
        for line in response.splitlines():
            markers = {
                int(value)
                for value in re.findall(
                    r"(?:\[|\()?Fonte\s+(\d+)(?:\]|\))?",
                    line,
                    re.IGNORECASE,
                )
            }
            if any(marker < 1 or marker > source_count for marker in markers):
                suppressed += 1
                continue
            retained_lines.append(line)
        return "\n".join(retained_lines).strip(), suppressed

    @classmethod
    def _suppress_mismatched_curated_claims(
        cls,
        response: str,
    ) -> tuple[str, int]:
        retained_lines = []
        suppressed = 0
        for line in response.splitlines():
            normalized = cls._normalize_for_guard(line)
            articles = cls._extract_article_numbers(line)
            invalid = False
            if articles:
                for triggers, allowed_articles in CURATED_CLAIM_ARTICLE_RULES:
                    if any(trigger in normalized for trigger in triggers):
                        if not articles.intersection(allowed_articles):
                            invalid = True
                            break
            if invalid:
                suppressed += 1
                continue
            retained_lines.append(line)
        return "\n".join(retained_lines).strip(), suppressed

    @staticmethod
    def _suppress_invalid_realtime_markers(
        response: str,
        *,
        source_count: int,
    ) -> tuple[str, int]:
        retained_lines = []
        suppressed = 0
        for line in response.splitlines():
            markers = {
                int(value)
                for value in re.findall(
                    r"(?:\[|\()?Atual\s+(\d+)(?:\]|\))?",
                    line,
                    re.IGNORECASE,
                )
            }
            if any(marker < 1 or marker > source_count for marker in markers):
                suppressed += 1
                continue
            retained_lines.append(line)
        return "\n".join(retained_lines).strip(), suppressed

    @staticmethod
    def _ensure_official_source_index(
        response: str,
        sources: list[Dict[str, Any]],
    ) -> str:
        if "## Fontes oficiais consultadas" in response:
            return response

        source_lines = [
            f"- [Fonte {index}] [{source['title']}]({source['url']})"
            for index, source in enumerate(sources, start=1)
        ]
        return (
            f"{response.rstrip()}\n\n"
            "## Fontes oficiais consultadas\n\n"
            + "\n".join(source_lines)
        ).strip()

    @staticmethod
    def _ensure_realtime_source_index(
        response: str,
        sources: list[Dict[str, Any]],
        retrieved_at: str | None,
    ) -> str:
        if "## Fontes oficiais consultadas agora" in response:
            return response
        lines = [
            (
                f"- [Atual {index}] [{source.get('title')}]"
                f"({source.get('url')}) - {source.get('authority')}"
            )
            for index, source in enumerate(sources, start=1)
        ]
        return (
            f"{response.rstrip()}\n\n"
            "## Fontes oficiais consultadas agora\n\n"
            f"Consulta realizada em: {retrieved_at or 'horario nao informado'}\n\n"
            + "\n".join(lines)
        ).strip()
