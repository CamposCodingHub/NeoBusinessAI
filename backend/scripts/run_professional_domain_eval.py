"""Eval offline dos dominios profissionais da Lex (sem chamar LLM).

Valida detectores + fragmentos de addenda/disclaimer no system prompt.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence


BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from ai.professional_domains import (  # noqa: E402
    SAFE_FISCAL_RULES,
    build_domain_system_addenda,
    detect_professional_domains,
    looks_like_accounting_tax_query,
)


DEFAULT_DATASET = BACKEND_ROOT / "evals" / "professional_domains_v1.json"


def _contains_all(haystack: str, needles: Sequence[str]) -> List[str]:
    missing = []
    lowered = haystack.lower()
    for needle in needles:
        if needle and needle.lower() not in lowered:
            missing.append(needle)
    return missing


def _contains_any(haystack: str, needles: Sequence[str]) -> List[str]:
    found = []
    lowered = haystack.lower()
    for needle in needles:
        if needle and needle.lower() in lowered:
            found.append(needle)
    return found


def score_case(case: Dict[str, Any]) -> Dict[str, Any]:
    prompt = str(case.get("prompt") or "")
    expected = list(case.get("expected_domains") or [])
    detected = detect_professional_domains(prompt)
    addenda = build_domain_system_addenda(detected)

    # Espelha o orquestrador: bloco contabil legado + regras seguras.
    system_fragment = addenda
    if looks_like_accounting_tax_query(prompt) and SAFE_FISCAL_RULES not in system_fragment:
        system_fragment = f"{system_fragment}\n\n{SAFE_FISCAL_RULES}".strip()

    missing_domains = [d for d in expected if d not in detected]
    # Para casos negativos, qualquer dominio e falha se expected vazio.
    negative_domain_fail = (not expected) and bool(detected) and "negativo" in str(
        case.get("id") or ""
    )

    missing_addenda = _contains_all(
        system_fragment,
        list(case.get("required_addenda_terms") or []),
    )
    missing_disclaimer = _contains_all(
        system_fragment,
        list(case.get("required_disclaimer_terms") or []),
    )
    forbidden_hits = _contains_any(
        system_fragment,
        list(case.get("forbidden_addenda_terms") or []),
    )

    passed = not (
        missing_domains
        or negative_domain_fail
        or missing_addenda
        or missing_disclaimer
        or forbidden_hits
    )

    return {
        "id": case.get("id"),
        "passed": passed,
        "prompt": prompt,
        "expected_domains": expected,
        "detected_domains": detected,
        "missing_domains": missing_domains,
        "negative_domain_fail": negative_domain_fail,
        "missing_addenda_terms": missing_addenda,
        "missing_disclaimer_terms": missing_disclaimer,
        "forbidden_addenda_hits": forbidden_hits,
        "accounting_intent": looks_like_accounting_tax_query(prompt),
        "addenda_preview": system_fragment[:500],
    }


def run_dataset(dataset_path: Path) -> Dict[str, Any]:
    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    cases = list(payload.get("cases") or [])
    results = [score_case(case) for case in cases]
    passed = sum(1 for item in results if item["passed"])
    total = len(results)
    return {
        "name": payload.get("name"),
        "version": payload.get("version"),
        "dataset": str(dataset_path),
        "passed": passed,
        "failed": total - passed,
        "total": total,
        "pass_rate": round((passed / total) if total else 0.0, 4),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET,
        help="Caminho do JSON de casos",
    )
    parser.add_argument(
        "--fail-under",
        type=float,
        default=1.0,
        help="Taxa minima de aprovacao (0-1). Default 1.0",
    )
    args = parser.parse_args()

    report = run_dataset(args.dataset)
    print(json.dumps(report, indent=2, ensure_ascii=False))

    if report["total"] == 0:
        return 2
    if report["pass_rate"] < args.fail_under:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
