"""Stress benchmark for legal and accounting professional assistance."""

from __future__ import annotations

import json
import os
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

try:
    from .simulation_auth import create_simulation_access_token
except ImportError:
    from simulation_auth import create_simulation_access_token


API_URL = os.getenv("NEOBUSINESS_API_URL", "http://127.0.0.1:8000")
ROOT_DIR = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT_DIR / "relatorios_melhorias" / "simulacoes"

CASES = [
    {
        "id": "dctfweb_mit",
        "domain": "contabil_fiscal",
        "source_codes": {"RFB_DCTFWEB"},
        "terms": {"dctfweb", "mit", "darf"},
        "question": (
            "Uma empresa percebeu divergencia depois de transmitir o MIT e a "
            "DCTFWeb. Explique um procedimento seguro de diagnostico e retificacao, "
            "efeitos no DARF, conferencias antes de transmitir e pontos que exigem "
            "validacao do contador. Nao invente prazo nem funcionalidade."
        ),
    },
    {
        "id": "esocial_desligamento",
        "domain": "juridico_contabil",
        "source_codes": {"ESOCIAL"},
        "terms": {"esocial", "desligamento", "folha"},
        "question": (
            "Monte um checklist detalhado para revisar desligamento de empregado "
            "no eSocial, reflexos na folha e consistencia com as demais obrigacoes. "
            "Separe dados necessarios, validacoes, riscos e fonte oficial."
        ),
    },
    {
        "id": "escrituracao_simples",
        "domain": "contabil_fiscal",
        "source_codes": {"CFC_ESCRITURACAO", "CFC_NBC"},
        "terms": {"escrituracao", "contabil", "simples nacional"},
        "question": (
            "Uma microempresa do Simples Nacional afirma que nao precisa de "
            "escrituracao contabil. Analise a premissa, diferencie obrigacoes "
            "fiscais de contabilidade regular e indique documentos e controles "
            "que o contador deve conferir."
        ),
    },
    {
        "id": "reforma_tributaria_2026",
        "domain": "contabil_fiscal",
        "source_codes": {"RFB_RTC2026"},
        "terms": {"ibs", "cbs", "2026"},
        "question": (
            "Considerando exclusivamente orientacoes oficiais vigentes em 2026, "
            "como uma empresa deve se preparar para IBS e CBS em documentos "
            "fiscais? Diferencie o que ja esta confirmado, fase de adaptacao, "
            "riscos de parametrizacao e fatos que ainda dependem de regulamentacao."
        ),
    },
    {
        "id": "irpf_2026",
        "domain": "contabil_fiscal",
        "source_codes": {"RFB_IRPF2026"},
        "terms": {"irpf", "dependente", "receita federal"},
        "question": (
            "Com base no Perguntas e Respostas IRPF 2026 da Receita Federal, "
            "estruture uma entrevista de triagem para contribuinte com dependente, "
            "despesas medicas, ganho de capital e rendimentos no exterior. Nao "
            "presuma valores ou enquadramento sem os fatos."
        ),
    },
    {
        "id": "domicilio_cnj",
        "domain": "juridico",
        "source_codes": {"CNJ_DOMICILIO"},
        "terms": {"domicilio judicial", "citacao", "prazo"},
        "question": (
            "Explique como um departamento juridico deve controlar citacoes e "
            "comunicacoes no Domicilio Judicial Eletronico. Crie uma rotina de "
            "governanca, alertas e dupla verificacao sem inventar prazo."
        ),
    },
    {
        "id": "preventiva",
        "domain": "juridico",
        "source_codes": {"CPP"},
        "terms": {"prisao preventiva", "art. 312", "cautelar"},
        "question": (
            "Analise profundamente os requisitos da prisao preventiva, necessidade "
            "de fundamentacao concreta, admissibilidade e medidas cautelares "
            "alternativas. Corrija a ideia de que a gravidade abstrata basta."
        ),
    },
    {
        "id": "cdc_vicio_oculto",
        "domain": "juridico",
        "source_codes": {"CDC"},
        "terms": {"vicio oculto", "90 dias", "art. 26"},
        "question": (
            "Em produto duravel com vicio oculto, diferencie prazo para reclamar, "
            "prazo para o fornecedor sanar o vicio e eventual reparacao por fato "
            "do produto. Inclua riscos probatorios e fatos faltantes."
        ),
    },
    {
        "id": "lgpd_incidente",
        "domain": "juridico",
        "source_codes": {"LGPD", "ANPD"},
        "terms": {"incidente", "dados pessoais", "anpd"},
        "question": (
            "Uma empresa sofreu incidente com dados pessoais. Estruture as "
            "primeiras 24 horas de resposta, preservacao de evidencias, avaliacao "
            "juridica e comunicacao. Nao invente prazo regulatorio nem conclua "
            "automaticamente que todo incidente deve ser comunicado."
        ),
    },
    {
        "id": "justa_causa_esocial",
        "domain": "juridico_contabil",
        "source_codes": {"CLT", "ESOCIAL"},
        "terms": {"justa causa", "prova", "esocial"},
        "question": (
            "Integre a analise juridica de uma possivel justa causa com a rotina "
            "operacional de desligamento no eSocial. Separe fundamento, prova, "
            "decisao do advogado, execucao pela folha e controles contra erro."
        ),
    },
]

LONG_DIALOGUE = [
    (
        "Registre o caso Aurora: empregado Marcos, salario de R$ 8.400,00, "
        "admissao em 12/03/2022 e possivel desligamento em 30/06/2026. A empresa "
        "ainda nao decidiu entre acordo e dispensa sem justa causa. Quais fatos "
        "faltam antes de calcular ou orientar?"
    ),
    "Agora organize um checklist juridico para comparar acordo e dispensa.",
    "Conecte esse checklist ao desligamento no eSocial e indique validacoes da folha.",
    "Depois do fechamento da folha, quais conciliacoes com DCTFWeb e DARF devem ser investigadas?",
    "Proponha lancamentos e documentos de suporte sem inventar contas contabeis da empresa.",
    "Mude de assunto: quais impactos de IBS e CBS em 2026 nao devem ser confundidos com esse desligamento?",
    "Retome o caso Aurora. Qual era o empregado, salario, data de admissao e as duas alternativas ainda abertas?",
    "Feche com uma matriz RACI entre advogado, contador, RH e diretoria, incluindo revisao humana e fontes.",
]


def normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    ).lower()


def call_chat(
    token: str,
    message: str,
    conversation_id: str,
    response_mode: str = "deep",
) -> tuple[dict[str, Any], float]:
    started_at = time.perf_counter()
    response = requests.post(
        f"{API_URL}/api/chat/premium",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": message,
            "conversation_id": conversation_id,
            "response_mode": response_mode,
            "jurisdiction": "Brasil - federal",
        },
        timeout=300,
    )
    latency = round(time.perf_counter() - started_at, 3)
    response.raise_for_status()
    return response.json(), latency


def evaluate(case: dict[str, Any], body: dict[str, Any], latency: float) -> dict:
    answer = str(body.get("response") or "")
    normalized_answer = normalize(answer)
    metadata = body.get("metadata") or {}
    source_codes = {
        source.get("code") for source in metadata.get("sources", [])
    }
    expected_terms = {
        term for term in case["terms"] if normalize(term) in normalized_answer
    }
    checks = {
        "success": bool(body.get("success")),
        "detailed_answer": len(answer) >= 800,
        "expected_terms": len(expected_terms) >= 2,
        "expected_source": bool(source_codes & case["source_codes"]),
        "official_grounding": metadata.get("grounding_status")
        in {"official_sources", "official_links"},
        "professional_domain": metadata.get("professional_domain")
        == case["domain"],
        "human_review": bool(metadata.get("requires_human_review")),
        "review_role": metadata.get("review_role")
        in {
            "contador_responsavel",
            "advogado_responsavel",
            "advogado_e_contador_responsaveis",
        },
        "robust_model": metadata.get("model")
        in {"llama-3.3-70b-versatile", "openai/gpt-oss-120b"},
        "model_not_degraded": not bool(metadata.get("model_degraded")),
        "source_index": "fontes oficiais consultadas" in normalized_answer,
        "no_unverified_articles": not metadata.get(
            "unverified_article_references"
        ),
    }
    return {
        "id": case["id"],
        "domain": case["domain"],
        "source_codes_expected": sorted(case["source_codes"]),
        "terms_expected": sorted(case["terms"]),
        "question": case["question"],
        "latency_seconds": latency,
        "response_characters": len(answer),
        "source_codes": sorted(code for code in source_codes if code),
        "expected_terms_found": sorted(expected_terms),
        "metadata": metadata,
        "checks": checks,
        "passed_checks": sum(checks.values()),
        "total_checks": len(checks),
        "response": answer,
    }


def run() -> dict[str, Any]:
    token = create_simulation_access_token(API_URL, "professional-benchmark")
    run_id = f"professional-{int(time.time())}"
    results = []
    for index, case in enumerate(CASES, start=1):
        try:
            body, latency = call_chat(
                token,
                case["question"],
                f"{run_id}-case-{index}",
                "deep",
            )
            results.append(evaluate(case, body, latency))
        except Exception as exc:
            results.append(
                {
                    "id": case["id"],
                    "domain": case["domain"],
                    "source_codes_expected": sorted(case["source_codes"]),
                    "terms_expected": sorted(case["terms"]),
                    "question": case["question"],
                    "latency_seconds": None,
                    "response_characters": 0,
                    "source_codes": [],
                    "expected_terms_found": [],
                    "metadata": {},
                    "checks": {"success": False},
                    "passed_checks": 0,
                    "total_checks": 1,
                    "response": "",
                    "error": str(exc),
                }
            )

    dialogue = []
    dialogue_id = f"{run_id}-dialogue"
    for turn, message in enumerate(LONG_DIALOGUE, start=1):
        try:
            body, latency = call_chat(
                token,
                message,
                dialogue_id,
                "balanced",
            )
            dialogue.append(
                {
                    "turn": turn,
                    "message": message,
                    "response": str(body.get("response") or ""),
                    "latency_seconds": latency,
                    "metadata": body.get("metadata") or {},
                }
            )
        except Exception as exc:
            dialogue.append(
                {
                    "turn": turn,
                    "message": message,
                    "response": "",
                    "latency_seconds": None,
                    "metadata": {},
                    "error": str(exc),
                }
            )

    recall = normalize(dialogue[6]["response"] if len(dialogue) > 6 else "")
    final_answer = normalize(dialogue[-1]["response"] if dialogue else "")
    dialogue_checks = {
        "all_turns_answered": all(item["response"] for item in dialogue),
        "marcos_recalled": "marcos" in recall,
        "salary_recalled": "8.400" in recall or "8400" in recall,
        "admission_recalled": "12/03/2022" in recall or "12 de marco de 2022" in recall,
        "alternatives_recalled": "acordo" in recall and "sem justa causa" in recall,
        "raci_roles_present": all(
            term in final_answer
            for term in ("advogado", "contador", "rh", "diretoria")
        ),
        "no_prompt_leak": "ordem de prioridade:" not in final_answer,
    }

    all_checks = [
        check
        for result in results
        for check in result["checks"].values()
    ] + list(dialogue_checks.values())
    return {
        "generated_at": datetime.now().isoformat(),
        "api_url": API_URL,
        "cases": len(results),
        "dialogue_turns": len(dialogue),
        "passed_checks": sum(all_checks),
        "total_checks": len(all_checks),
        "perfect_cases": sum(
            result["passed_checks"] == result["total_checks"]
            for result in results
        ),
        "average_response_characters": round(
            sum(result["response_characters"] for result in results)
            / max(len(results), 1),
            1,
        ),
        "results": results,
        "dialogue_checks": dialogue_checks,
        "dialogue": dialogue,
    }


def write_reports(payload: dict[str, Any]) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = REPORT_DIR / f"benchmark_ia_profissional_{timestamp}.json"
    md_path = REPORT_DIR / f"benchmark_ia_profissional_{timestamp}.md"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# Benchmark extremo da IA profissional",
        "",
        f"- Checagens: {payload['passed_checks']}/{payload['total_checks']}",
        f"- Casos perfeitos: {payload['perfect_cases']}/{payload['cases']}",
        f"- Media de caracteres: {payload['average_response_characters']}",
        "",
        "| Caso | Dominio | Tamanho | Fontes | Checagens |",
        "|---|---|---:|---|---:|",
    ]
    for result in payload["results"]:
        lines.append(
            f"| {result['id']} | {result['domain']} | "
            f"{result['response_characters']} | "
            f"{', '.join(result['source_codes']) or '-'} | "
            f"{result['passed_checks']}/{result['total_checks']} |"
        )
    lines.extend(["", "## Conversa longa", ""])
    lines.extend(
        f"- {'PASSOU' if passed else 'FALHOU'}: `{name}`"
        for name, passed in payload["dialogue_checks"].items()
    )
    for item in payload["dialogue"]:
        lines.extend(
            [
                "",
                f"### Turno {item['turn']}",
                "",
                f"**Pergunta:** {item['message']}",
                "",
                f"**Resposta:** {item['response']}",
            ]
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


if __name__ == "__main__":
    result = run()
    reports = write_reports(result)
    print(
        json.dumps(
            {
                "passed_checks": result["passed_checks"],
                "total_checks": result["total_checks"],
                "perfect_cases": result["perfect_cases"],
                "reports": [str(path) for path in reports],
            },
            ensure_ascii=True,
            indent=2,
        )
    )
