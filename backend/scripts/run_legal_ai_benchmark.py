"""Benchmark factual da IA em multiplas areas do Direito brasileiro."""

from __future__ import annotations

import json
import os
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from .simulation_auth import create_simulation_access_token
except ImportError:
    from simulation_auth import create_simulation_access_token


API_URL = os.getenv("NEOBUSINESS_API_URL", "http://127.0.0.1:8000")
ROOT_DIR = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT_DIR / "relatorios_melhorias" / "simulacoes"

QUESTIONS = [
    {
        "id": "penal_dolo",
        "area": "penal",
        "question": (
            "Faca uma pesquisa profunda sobre a diferenca entre dolo eventual e "
            "culpa consciente no direito penal brasileiro. Parta do artigo 18 do "
            "Codigo Penal, explique criterios praticos, controversias e quais fatos "
            "precisariam ser provados em um caso concreto."
        ),
        "expected_terms": ["dolo eventual", "culpa consciente", "art. 18"],
        "required_fact_groups": [
            ["art. 18", "artigo 18"],
            ["assumiu o risco"],
            ["previu", "preve", "previsao"],
        ],
        "forbidden_claims": [
            "culpa consciente e uma forma de dolo eventual",
        ],
    },
    {
        "id": "processo_penal_prisao",
        "area": "processual_penal",
        "question": (
            "Quais sao os requisitos juridicos para decretacao de prisao preventiva "
            "no processo penal brasileiro? Diferencie pressupostos, fundamentos, "
            "necessidade concreta e medidas cautelares alternativas."
        ),
        "expected_terms": ["prisao preventiva", "processo penal", "cautelar"],
        "required_fact_groups": [
            ["art. 312", "artigo 312"],
            ["art. 313", "artigo 313"],
            ["art. 315", "artigo 315"],
            ["art. 319", "artigo 319"],
            ["prova da existencia do crime", "materialidade"],
            ["indicio suficiente de autoria", "indicios de autoria"],
            ["conveniencia da instrucao criminal"],
        ],
        "forbidden_claims": [
            "gravidade do crime e um fator importante para a decretacao",
            "seguranca das testemunhas ou a aplicacao da lei penal",
            "impossibilidade de substituicao por outra medida cautelar (art. 312",
        ],
    },
    {
        "id": "cpc_tutelas",
        "area": "processual_civil",
        "question": (
            "Compare tutela de urgencia antecipada, tutela cautelar e tutela da "
            "evidencia no CPC. Inclua requisitos, momento processual, riscos e um "
            "quadro pratico de escolha."
        ),
        "expected_terms": ["tutela", "urgencia", "evidencia"],
        "required_fact_groups": [
            ["art. 300", "artigo 300"],
            ["art. 311", "artigo 311"],
            ["probabilidade do direito"],
            ["perigo de dano", "risco ao resultado util"],
        ],
        "forbidden_claims": [
            "artigos 311 a 314",
            "decisao final nao pode ser objeto de recurso",
            "cautelar requer apenas urgencia",
            "jurisprudencia do stj tem exigido",
        ],
    },
    {
        "id": "civil_inadimplemento",
        "area": "civil",
        "question": (
            "Em um contrato empresarial, quais consequencias podem decorrer do "
            "inadimplemento e como analisar perdas e danos, clausula penal, "
            "resolucao e cumprimento especifico?"
        ),
        "expected_terms": ["inadimplemento", "perdas e danos", "clausula penal"],
        "required_fact_groups": [
            ["art. 389", "artigo 389"],
            ["art. 475", "artigo 475"],
            ["art. 402", "artigo 402"],
            ["art. 408", "artigo 408"],
            ["art. 412", "artigo 412"],
        ],
        "forbidden_claims": [
            "artigo 461",
            "clausula penal punitiva",
        ],
    },
    {
        "id": "consumidor_vicio",
        "area": "consumidor",
        "question": (
            "Explique a diferenca entre vicio e fato do produto no Codigo de Defesa "
            "do Consumidor, com prazos, responsaveis e consequencias praticas."
        ),
        "expected_terms": ["vicio", "produto", "consumidor"],
        "required_fact_groups": [
            ["30 dias"],
            ["90 dias"],
            ["art. 26", "artigo 26"],
            ["art. 12", "artigo 12"],
            ["art. 18", "artigo 18"],
            ["art. 27", "artigo 27"],
        ],
        "forbidden_claims": [
            "90 dias para produtos nao duraveis",
            "30 dias para produtos duraveis",
            "independentemente de qualquer falha ou defeito",
            "artigo 26: o consumidor pode exigir a reparacao de danos",
            "30 dias para sanar produto nao duravel e 90 dias para sanar produto duravel",
        ],
    },
    {
        "id": "trabalhista_justa_causa",
        "area": "trabalhista",
        "question": (
            "Quais cuidados probatorios e procedimentais uma empresa deve observar "
            "antes de aplicar justa causa a um empregado? Estruture riscos e "
            "checklist de revisao."
        ),
        "expected_terms": ["justa causa", "prova", "empregado"],
        "required_fact_groups": [
            ["art. 482", "artigo 482"],
            ["imediatidade"],
            ["proporcionalidade"],
            ["onus da prova", "art. 818", "artigo 818"],
        ],
        "forbidden_claims": [
            "artigo 493: a empresa deve realizar uma investigacao previa",
            "artigo 494: a empresa deve garantir os direitos do empregado",
        ],
    },
    {
        "id": "lgpd_bases",
        "area": "protecao_de_dados",
        "question": (
            "Compare consentimento, execucao de contrato, obrigacao legal e legitimo "
            "interesse como bases legais da LGPD. Explique quando cada uma e "
            "adequada e os principais riscos de uso indevido."
        ),
        "expected_terms": ["consentimento", "legitimo interesse", "lgpd"],
        "required_fact_groups": [
            ["art. 7", "artigo 7"],
            ["art. 10", "artigo 10"],
            ["legitimo interesse"],
            ["necessidade"],
            ["transparencia"],
        ],
    },
    {
        "id": "geral_produtividade",
        "area": "geral",
        "question": (
            "Ajude a organizar uma rotina semanal de atendimento, estudo e revisao "
            "de tarefas para um profissional autonomo."
        ),
        "expected_terms": ["semana", "tarefas"],
        "response_mode": "balanced",
    },
]


def normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    ).lower()


def call_api(
    payload: dict[str, Any],
    access_token: str,
) -> tuple[dict[str, Any], float]:
    request = urllib.request.Request(
        f"{API_URL}/api/chat/premium",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {access_token}",
        },
        method="POST",
    )
    started_at = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {error_body}") from exc
    return body, round(time.perf_counter() - started_at, 3)


def evaluate_answer(
    item: dict[str, Any],
    response: str,
    metadata: dict[str, Any],
) -> tuple[dict[str, bool], list[str], list[list[str]], list[str]]:
    normalized_response = normalize(response)
    expected_found = [
        term
        for term in item["expected_terms"]
        if normalize(term) in normalized_response
    ]
    required_fact_groups = item.get("required_fact_groups", [])
    fact_groups_found = [
        group
        for group in required_fact_groups
        if any(normalize(option) in normalized_response for option in group)
    ]
    forbidden_claims_found = [
        claim
        for claim in item.get("forbidden_claims", [])
        if normalize(claim) in normalized_response
    ]
    legal_question = item["area"] != "geral"
    checks = {
        "response_generated": len(response) > 200,
        "expected_terms_present": len(expected_found)
        >= max(1, len(item["expected_terms"]) - 1),
        "detailed_when_legal": len(response) >= 900 if legal_question else True,
        "official_sources_present": bool(metadata.get("sources"))
        if legal_question
        else True,
        "large_model_used": metadata.get("model")
        in {"llama-3.3-70b-versatile", "openai/gpt-oss-120b"}
        if legal_question
        else metadata.get("model") == "llama-3.1-8b-instant",
        "human_review_flag": bool(metadata.get("requires_human_review"))
        if legal_question
        else not bool(metadata.get("requires_human_review")),
        "citation_marker_present": "[fonte" in normalized_response
        if legal_question
        else True,
        "claim_level_citations": int(metadata.get("inline_citations") or 0) >= 2
        if legal_question
        else True,
        "robust_model_completed": not bool(metadata.get("model_degraded"))
        if legal_question
        else True,
        "article_references_grounded": not bool(
            metadata.get("unverified_article_references")
        )
        if legal_question
        else True,
        "response_completed": bool(metadata.get("response_complete", True)),
        "required_legal_facts_present": (
            len(fact_groups_found) == len(required_fact_groups)
        ),
        "known_false_claims_absent": not forbidden_claims_found,
    }
    return checks, expected_found, fact_groups_found, forbidden_claims_found


def run() -> dict[str, Any]:
    results = []
    user_id = f"legal-benchmark-{int(time.time())}"
    access_token = create_simulation_access_token(
        API_URL,
        "legal-benchmark",
    )

    for item in QUESTIONS:
        response_mode = item.get("response_mode", "deep")
        body, latency = call_api(
            {
                "message": item["question"],
                "conversation_id": user_id,
                "response_mode": response_mode,
                "jurisdiction": "Brasil - federal",
            },
            access_token,
        )
        response = str(body.get("response") or "")
        metadata = body.get("metadata") or {}
        (
            checks,
            expected_found,
            fact_groups_found,
            forbidden_claims_found,
        ) = evaluate_answer(item, response, metadata)
        results.append(
            {
                **item,
                "response_mode": response_mode,
                "latency_seconds": latency,
                "response_characters": len(response),
                "expected_terms_found": expected_found,
                "required_fact_groups_found": fact_groups_found,
                "forbidden_claims_found": forbidden_claims_found,
                "metadata": metadata,
                "checks": checks,
                "passed_checks": sum(checks.values()),
                "total_checks": len(checks),
                "response": response,
            }
        )

    all_checks = [
        value
        for result in results
        for value in result["checks"].values()
    ]
    legal_results = [result for result in results if result["area"] != "geral"]
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "api_url": API_URL,
        "questions": len(results),
        "summary": {
            "passed_checks": sum(all_checks),
            "total_checks": len(all_checks),
            "average_latency_seconds": round(
                sum(result["latency_seconds"] for result in results) / len(results),
                3,
            ),
            "average_legal_response_characters": round(
                sum(result["response_characters"] for result in legal_results)
                / len(legal_results),
                1,
            ),
            "legal_questions_with_sources": sum(
                bool(result["metadata"].get("sources"))
                for result in legal_results
            ),
            "legal_questions_using_large_model": sum(
                result["metadata"].get("model")
                in {"llama-3.3-70b-versatile", "openai/gpt-oss-120b"}
                for result in legal_results
            ),
            "questions_passing_every_check": sum(
                result["passed_checks"] == result["total_checks"]
                for result in results
            ),
        },
        "results": results,
    }


def write_reports(result: dict[str, Any]) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = REPORT_DIR / f"benchmark_ia_juridica_{timestamp}.json"
    md_path = REPORT_DIR / f"benchmark_ia_juridica_{timestamp}.md"
    json_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    sections = []
    for item in result["results"]:
        check_lines = "\n".join(
            f"- {'PASSOU' if value else 'FALHOU'}: `{name}`"
            for name, value in item["checks"].items()
        )
        source_lines = "\n".join(
            f"- [{source['title']}]({source['url']})"
            for source in item["metadata"].get("sources", [])
        ) or "- Nenhuma fonte"
        forbidden_lines = ", ".join(item["forbidden_claims_found"]) or "Nenhuma"
        sections.append(
            f"""## {item['id']}

**Area esperada:** {item['area']}

**Pergunta:** {item['question']}

**Latencia:** {item['latency_seconds']}s

**Tamanho:** {item['response_characters']} caracteres

**Modelo:** {item['metadata'].get('model')}

**Checagens:** {item['passed_checks']}/{item['total_checks']}

**Alegacoes falsas detectadas:** {forbidden_lines}

{check_lines}

### Fontes

{source_lines}

### Resposta

{item['response']}
"""
        )

    summary = result["summary"]
    md_path.write_text(
        f"""# Benchmark da IA Juridica

- Gerado em: {result['generated_at']}
- Perguntas: {result['questions']}
- Checagens: {summary['passed_checks']}/{summary['total_checks']}
- Perguntas com aprovacao total: {summary['questions_passing_every_check']}/{result['questions']}
- Latencia media: {summary['average_latency_seconds']}s
- Tamanho medio das respostas juridicas: {summary['average_legal_response_characters']} caracteres
- Perguntas juridicas com fontes: {summary['legal_questions_with_sources']}/7
- Perguntas juridicas com modelo 70B: {summary['legal_questions_using_large_model']}/7

{''.join(sections)}
""",
        encoding="utf-8",
    )
    return json_path, md_path


if __name__ == "__main__":
    benchmark = run()
    paths = write_reports(benchmark)
    print(
        json.dumps(
            {
                "summary": benchmark["summary"],
                "reports": [str(path) for path in paths],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
