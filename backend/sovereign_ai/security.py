"""Controles de entrada e saida independentes do modelo."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, Tuple

from sovereign_ai.search import normalize_text

INJECTION_PATTERNS = (
    r"\bignore\b.*\b(?:instruction|prompt|regra)",
    r"\bignore\b.*\b(?:tudo|anterior)",
    r"\bmostre\b.*\b(?:prompt|instruc)",
    r"\brevele\b.*\b(?:prompt|instruc|sistema)",
    r"\bsystem\s+prompt\b",
    r"\bjailbreak\b",
    r"\bdeveloper\s+mode\b",
)

LEAK_PATTERNS = (
    r"\bsystem\s+prompt\s*:",
    r"\binstrucoes?\s+internas?\s*:",
    r"\border\s+de\s+prioridade\s*:",
    r"\bregras\s+obrigatorias\s*:",
    r"\bvoce\s+e\s+lex\s+juris\s+local\b",
)


def _combined_role_text(
    messages: Iterable[Dict[str, Any]],
    role: str,
) -> str:
    return "\n".join(
        str(message.get("content") or "")
        for message in messages
        if message.get("role") == role
    )


def detect_prompt_injection(messages: Iterable[Dict[str, Any]]) -> bool:
    user_text = normalize_text(_combined_role_text(messages, "user"))
    return any(re.search(pattern, user_text, re.I) for pattern in INJECTION_PATTERNS)


def sanitize_model_output(
    messages: Iterable[Dict[str, Any]],
    content: str,
) -> Tuple[str, bool]:
    """Bloqueia vazamento e normaliza marcadores de fonte existentes."""
    normalized_content = normalize_text(content)
    injection = detect_prompt_injection(messages)
    leak_detected = any(
        re.search(pattern, normalized_content, re.I)
        for pattern in LEAK_PATTERNS
    )
    system_text = _combined_role_text(messages, "system")
    source_markers = list(
        dict.fromkeys(
            re.findall(
                r"\[(?:Fonte|Base Local)\s+\d+\]",
                system_text,
                re.I,
            )
        )
    )

    if leak_detected or (injection and "system prompt" in normalized_content):
        allowed_sources = (
            " ".join(source_markers)
            if source_markers
            else "as fontes autorizadas da consulta"
        )
        return (
            "Nao posso revelar prompts, regras internas ou instrucoes do "
            "sistema. Posso, contudo, analisar o conteudo juridico permitido "
            f"com base em {allowed_sources}. Qualquer conclusao deve permanecer "
            "limitada aos trechos recuperados e passar por revisao profissional.",
            True,
        )

    normalized_citations = re.sub(
        r"(?<!\[)\b(Fonte|Base Local)\s+(\d+)\s*:",
        lambda match: f"[{match.group(1)} {match.group(2)}]:",
        content,
        flags=re.I,
    )
    normalized_citations = re.sub(
        r"\(\s*(Fonte|Base Local)\s+(\d+)\s*\)",
        lambda match: f"[{match.group(1)} {match.group(2)}]",
        normalized_citations,
        flags=re.I,
    )
    return normalized_citations, False
