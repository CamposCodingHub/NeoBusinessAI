"""
Monthly tax obligations reminder — methodological stub for accountants.

NOT a real RFB / municipal calendar API. No invented due days or tax rates.
Always confirm the official calendar with the accountant and RFB/prefeitura.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

TAX_CALENDAR_DISCLAIMER = (
    "Lembretes metodológicos (stub). Não constitui calendário oficial da RFB "
    "nem de prefeituras. Sem alíquotas nem dias de vencimento inventados — "
    "confirmar calendário RFB/prefeitura vigente com o contador responsável."
)

DUE_HINT_CONFIRM = "confirmar calendário RFB/prefeitura vigente"

# Method-only reminders (no fake fixed rates / exact statutory due days).
REMINDER_SPECS = (
    {
        "code": "SIMPLES_DAS",
        "title": "Simples Nacional / DAS",
        "due_hint": (
            f"Apuração e DAS da competência — checar competência com o contador; "
            f"{DUE_HINT_CONFIRM}"
        ),
        "disclaimer": (
            "Metodologia apenas. Regime e vencimento dependem do enquadramento "
            f"e do calendário oficial; {DUE_HINT_CONFIRM}."
        ),
    },
    {
        "code": "ISS_MUNICIPAL",
        "title": "ISS municipal",
        "due_hint": (
            f"Recolhimento / declaração municipal conforme município do estabelecimento; "
            f"{DUE_HINT_CONFIRM}"
        ),
        "disclaimer": (
            "ISS é municipal — prazos e forma variam por prefeitura; "
            f"{DUE_HINT_CONFIRM}."
        ),
    },
    {
        "code": "DCTFWEB_ESOCIAL",
        "title": "DCTFWeb / eSocial (eventos)",
        "due_hint": (
            f"Revisar eventos eSocial e transmissão DCTFWeb do período (método); "
            f"{DUE_HINT_CONFIRM}"
        ),
        "disclaimer": (
            "Lembrete de processo, não checklist normativo fechado; "
            f"{DUE_HINT_CONFIRM}."
        ),
    },
)


def parse_month(month: Optional[str]) -> str:
    """Validate YYYY-MM or default to current UTC month."""
    if month is None or not str(month).strip():
        from datetime import datetime

        return datetime.utcnow().strftime("%Y-%m")
    value = str(month).strip()
    if not MONTH_RE.match(value):
        raise ValueError("month must be YYYY-MM")
    return value


def build_tax_calendar_items(month: str) -> List[Dict[str, str]]:
    """Return methodological reminder items for the given competence month."""
    items: List[Dict[str, str]] = []
    for spec in REMINDER_SPECS:
        items.append(
            {
                "code": spec["code"],
                "title": spec["title"],
                "due_hint": f"{month}: {spec['due_hint']}",
                "disclaimer": spec["disclaimer"],
            }
        )
    return items


def build_tax_calendar(month: Optional[str] = None) -> Dict[str, Any]:
    resolved = parse_month(month)
    return {
        "month": resolved,
        "items": build_tax_calendar_items(resolved),
        "count": len(REMINDER_SPECS),
        "disclaimer": TAX_CALENDAR_DISCLAIMER,
        "stub": True,
        "source": "methodological_stub_not_rfb_api",
    }
