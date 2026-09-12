"""
Ethical collection plan (régua de cobrança) — stub for lawyers.

Generates suggested steps from invoice aging. Does NOT send messages.
Includes EOAB-oriented disclaimer: no aggressive / harassing collection.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

EOAB_DISCLAIMER = (
    "Régua ética (stub). Cobrança deve observar o Código de Ética e Disciplina da OAB: "
    "comunicação profissional, sem constrangimento, ameaça ou exposição do cliente. "
    "Não constitui cobrança agressiva nem envio automático de mensagens."
)

# Relative offsets from due date
STEP_SPECS = (
    {
        "code": "D-3",
        "offset_days": -3,
        "label": "Lembrete pré-vencimento",
        "tone": "reminder",
        "channel_hint": "e-mail ou WhatsApp com consentimento",
        "suggested_copy": (
            "Lembrete cordial: honorários com vencimento em breve. "
            "Segue boleto/PIX e canal para dúvidas."
        ),
    },
    {
        "code": "D0",
        "offset_days": 0,
        "label": "Vencimento",
        "tone": "due",
        "channel_hint": "e-mail",
        "suggested_copy": (
            "Hoje vence a fatura de honorários. "
            "Quando puder, confirme o pagamento ou avise se precisar de prazo."
        ),
    },
    {
        "code": "D+3",
        "offset_days": 3,
        "label": "Cobrança gentil",
        "tone": "gentle",
        "channel_hint": "e-mail",
        "suggested_copy": (
            "Notamos pendência de poucos dias. "
            "Estamos à disposição para renegociar de forma transparente."
        ),
    },
    {
        "code": "D+7",
        "offset_days": 7,
        "label": "Notificação formal",
        "tone": "formal_notice",
        "channel_hint": "e-mail formal / carta",
        "suggested_copy": (
            "Notificação formal de inadimplência de honorários (sem exposição pública). "
            "Solicitamos regularização ou agendamento de conversa profissional."
        ),
    },
)


def _naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if getattr(dt, "tzinfo", None) is not None:
        return dt.replace(tzinfo=None)
    return dt


def _days_relative_to_due(due_date: Optional[datetime], now: Optional[datetime] = None) -> int:
    """Positive = days past due; negative = days until due."""
    now = _naive_utc(now) or datetime.utcnow()
    due = _naive_utc(due_date) or now
    return (now.date() - due.date()).days


def _recommended_step_code(days_from_due: int) -> str:
    if days_from_due < 0:
        return "D-3" if days_from_due <= -3 else "D0"
    if days_from_due == 0:
        return "D0"
    if days_from_due <= 3:
        return "D+3"
    return "D+7"


def build_steps_for_due(
    due_date: Optional[datetime],
    *,
    now: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Return the four ethical steps with due-relative scheduling metadata."""
    now = _naive_utc(now) or datetime.utcnow()
    due = _naive_utc(due_date) or now
    days_from_due = _days_relative_to_due(due, now)
    current = _recommended_step_code(days_from_due)
    steps: List[Dict[str, Any]] = []
    for spec in STEP_SPECS:
        steps.append(
            {
                **spec,
                "days_from_due_target": spec["offset_days"],
                "is_current": spec["code"] == current,
                "is_due_or_past": days_from_due >= spec["offset_days"],
            }
        )
    return steps


def build_collection_plan_for_invoice(
    invoice: Any,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Build one plan dict from an Invoice-like object."""
    now = _naive_utc(now) or datetime.utcnow()
    due = getattr(invoice, "due_date", None) or getattr(invoice, "created_at", None)
    due = _naive_utc(due) or now
    days_from_due = _days_relative_to_due(due, now)
    total_cents = getattr(invoice, "total_cents", None)
    if total_cents is not None:
        amount = float(total_cents) / 100.0
    else:
        amount = float(getattr(invoice, "total", 0) or getattr(invoice, "amount", 0) or 0)

    return {
        "invoice_id": getattr(invoice, "id", None),
        "invoice_number": getattr(invoice, "invoice_number", None),
        "client_id": getattr(invoice, "client_id", None),
        "status": getattr(invoice, "status", None),
        "due_date": due.isoformat() if due else None,
        "amount": round(amount, 2),
        "days_from_due": days_from_due,
        "recommended_step": _recommended_step_code(days_from_due),
        "steps": build_steps_for_due(due, now=now),
        "disclaimer": EOAB_DISCLAIMER,
    }


def build_collection_plans(
    invoices: Sequence[Any],
    *,
    now: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    return [build_collection_plan_for_invoice(inv, now=now) for inv in invoices]
