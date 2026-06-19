"""Executa uma conversa longa contra a API e registra metricas de qualidade."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from collections import Counter
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

DOCUMENT_CONTEXT = """
CONTRATO DE PRESTACAO DE SERVICOS - OPERACAO ATLAS
Codigo interno: NBLONG-2026.
Contratante: Atlas Comercio Digital Ltda.
Contratada: Horizonte Tecnologia Juridica Ltda.
Valor mensal: R$ 18.750,00.
Vigencia: 24 meses a partir de 18 de junho de 2026.
Reajuste: IPCA a cada 12 meses.
Rescisao imotivada: aviso previo minimo de 60 dias.
Multa por rescisao antecipada: tres mensalidades.
Incidente de seguranca deve ser notificado em 24 horas.
Prazo para corrigir inadimplemento: 15 dias.
Foro: Comarca de Sao Paulo.
O anexo de nivel de servico nao define disponibilidade minima nem penalidade.
""".strip()

PROMPTS = [
    "Informe o codigo interno, o valor mensal e as partes do documento.",
    "Quais sao os prazos contratuais mais importantes?",
    "Explique os riscos da rescisao antecipada e proponha uma negociacao.",
    "O anexo de nivel de servico esta suficiente? O que precisa ser incluido?",
    "Registre que o nome deste caso e Operacao Atlas e que prefiro respostas em topicos curtos.",
    "Crie um plano de acao para 30 dias, priorizado por risco.",
    "Quais cuidados de LGPD e seguranca devem entrar no plano?",
    "Retome o que combinamos: qual nome do caso, codigo e preferencia de formato?",
    "Calcule o impacto nominal de uma multa de tres mensalidades.",
    "Escreva um email curto para a diretoria com os tres principais riscos.",
    "Questione suas recomendacoes anteriores e indique o que depende de revisao humana.",
    "Feche a tarefa com checklist final, mantendo os fatos e decisoes da conversa.",
]


def post_chat(
    payload: dict[str, Any],
    access_token: str,
) -> tuple[dict[str, Any], float]:
    request = urllib.request.Request(
        f"{API_URL}/api/chat/premium",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
        method="POST",
    )
    started_at = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {error_body}") from exc
    return body, round(time.perf_counter() - started_at, 3)


def opening_signature(response: str) -> str:
    words = " ".join(response.lower().split()).split()
    return " ".join(words[:8])


def run() -> dict[str, Any]:
    user_id = f"long-simulation-{int(time.time())}"
    access_token = create_simulation_access_token(
        API_URL,
        "long-simulation",
    )
    exchanges = []

    for index, prompt in enumerate(PROMPTS, start=1):
        body, latency_seconds = post_chat(
            {
                "message": prompt,
                "conversation_id": user_id,
                "document_context": DOCUMENT_CONTEXT,
            },
            access_token,
        )
        response = str(body.get("response") or "")
        exchanges.append(
            {
                "turn": index,
                "prompt": prompt,
                "response": response,
                "latency_seconds": latency_seconds,
                "response_characters": len(response),
                "metadata": body.get("metadata") or {},
            }
        )

    signatures = [opening_signature(item["response"]) for item in exchanges]
    duplicate_signatures = {
        signature: count
        for signature, count in Counter(signatures).items()
        if signature and count > 1
    }
    all_responses = "\n".join(item["response"] for item in exchanges).lower()
    recall_response = exchanges[7]["response"].lower()
    calculation_response = exchanges[8]["response"].lower()

    checks = {
        "document_code_used": "nblong-2026" in all_responses,
        "case_name_recalled": "operacao atlas" in recall_response
        or "operação atlas" in recall_response,
        "code_recalled_after_topic_shift": "nblong-2026" in recall_response,
        "format_preference_recalled": "topico" in recall_response
        or "tópico" in recall_response,
        "three_month_value_calculated": any(
            value in calculation_response
            for value in ("56.250", "56250", "r$ 56")
        ),
        "all_turns_succeeded": all(item["response"] for item in exchanges),
        "document_context_reported": all(
            item["metadata"].get("document_context_used")
            for item in exchanges
        ),
        "no_internal_instruction_leak": not any(
            marker in all_responses
            for marker in (
                "bloco documento",
                "fonte de dados nao confiavel",
                "fonte de dados não confiável",
                "<documento>",
                "ignore qualquer instrucao",
                "ignore qualquer instrução",
            )
        ),
        "markdown_lists_well_formed": not any(
            re.search(pattern, item["response"])
            for item in exchanges
            for pattern in (
                r"\d+\.\*\*",
                r"\*{4,}",
                r"[.!?]\d+\.\s",
                r"(?m)^\*\*[^*\n]+:\*\s*$",
            )
        ),
    }

    latencies = [item["latency_seconds"] for item in exchanges]
    lengths = [item["response_characters"] for item in exchanges]
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "api_url": API_URL,
        "user_id": user_id,
        "turns": len(exchanges),
        "metrics": {
            "average_latency_seconds": round(sum(latencies) / len(latencies), 3),
            "max_latency_seconds": max(latencies),
            "min_latency_seconds": min(latencies),
            "average_response_characters": round(sum(lengths) / len(lengths), 1),
            "duplicate_opening_signatures": duplicate_signatures,
        },
        "checks": checks,
        "passed_checks": sum(checks.values()),
        "total_checks": len(checks),
        "exchanges": exchanges,
    }


def write_reports(result: dict[str, Any]) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = REPORT_DIR / f"conversa_longa_ia_{timestamp}.json"
    md_path = REPORT_DIR / f"conversa_longa_ia_{timestamp}.md"
    json_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    check_lines = "\n".join(
        f"- {'PASSOU' if passed else 'FALHOU'}: `{name}`"
        for name, passed in result["checks"].items()
    )
    exchange_lines = "\n\n".join(
        (
            f"### Turno {item['turn']}\n\n"
            f"**Pergunta:** {item['prompt']}\n\n"
            f"**Latencia:** {item['latency_seconds']}s\n\n"
            f"**Resposta:**\n\n{item['response']}"
        )
        for item in result["exchanges"]
    )
    md_path.write_text(
        (
            "# Simulacao de Conversa Longa com IA\n\n"
            f"- Gerado em: {result['generated_at']}\n"
            f"- Turnos: {result['turns']}\n"
            f"- Checagens aprovadas: {result['passed_checks']}/{result['total_checks']}\n"
            f"- Latencia media: {result['metrics']['average_latency_seconds']}s\n"
            f"- Maior latencia: {result['metrics']['max_latency_seconds']}s\n"
            f"- Tamanho medio: {result['metrics']['average_response_characters']} caracteres\n\n"
            "## Checagens\n\n"
            f"{check_lines}\n\n"
            "## Repeticao de Aberturas\n\n"
            f"`{json.dumps(result['metrics']['duplicate_opening_signatures'], ensure_ascii=False)}`\n\n"
            "## Conversa Completa\n\n"
            f"{exchange_lines}\n"
        ),
        encoding="utf-8",
    )
    return json_path, md_path


if __name__ == "__main__":
    simulation_result = run()
    generated_paths = write_reports(simulation_result)
    print(
        json.dumps(
            {
                "passed_checks": simulation_result["passed_checks"],
                "total_checks": simulation_result["total_checks"],
                "metrics": simulation_result["metrics"],
                "reports": [str(path) for path in generated_paths],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
